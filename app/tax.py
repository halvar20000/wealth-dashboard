"""What would be left after tax if everything were sold today.

A portfolio page shows what the shares are worth. What they are worth
*to you* is less: the gain in them has not been taxed yet, and in most
places it will be the day you sell. A plan built on the gross figure
plans with money the tax office is holding a claim on.

The arithmetic is the easy half:

  * the gain in a holding is today's value less what the open lots
    cost — the same lots `gains.py` walks for a realised sale, under
    the same FIFO-or-average rule, so the figure here and the figure
    after a real sale agree;
  * losses count against gains, because every regime that taxes the
    gain lets the loss of the same kind reduce it;
  * an allowance comes off what is left (Germany's Sparerpauschbetrag,
    Britain's CGT allowance);
  * a fraction may be exempt before the rate applies (Germany's
    Teilfreistellung of 30 % on an equity fund);
  * the rate finishes it.

The hard half is that the rule is different in every country and for
every person, which is why nothing here is guessed: an account with no
profile is counted at zero and said to be at zero. The presets below
are starting points to be checked against your own situation, not
advice — this is an estimate, not a tax return.

Two limits worth naming. The cost of a lot is taken in the currency it
was paid in and converted at today's rate, not at the rate of its own
day, so for a foreign holding the currency's own gain is not separated
out. And an exemption that depends on what a fund holds is set per
account here, not per fund.
"""

from __future__ import annotations

from collections import defaultdict

from . import fx, gains, overview, people, settings
from .db import get_conn

# Starting points, with the figures as of 2026. A preset is copied into
# an account's profile and edited there; nothing reads them afterwards.
PRESETS = {
    "de": {"label": "Deutschland — Abgeltungsteuer + Soli",
           "rate": 26.375, "allowance": 1000.0, "exempt": 0.0},
    "de_church": {"label": "Deutschland — mit Kirchensteuer (9 %)",
                  "rate": 27.99, "allowance": 1000.0, "exempt": 0.0},
    "de_fund": {"label": "Deutschland — Aktienfonds (30 % Teilfreistellung)",
                "rate": 26.375, "allowance": 1000.0, "exempt": 30.0},
    "at": {"label": "Österreich — KESt", "rate": 27.5, "allowance": 0.0, "exempt": 0.0},
    "ch": {"label": "Schweiz — Privatvermögen, steuerfrei",
           "rate": 0.0, "allowance": 0.0, "exempt": 0.0},
    "fr": {"label": "France — PFU (flat tax)", "rate": 30.0, "allowance": 0.0, "exempt": 0.0},
    "uk": {"label": "United Kingdom — CGT, higher rate",
           "rate": 24.0, "allowance": 3000.0, "exempt": 0.0},
    "none": {"label": "Steuerfrei / nicht gerechnet", "rate": 0.0, "allowance": 0.0, "exempt": 0.0},
}


def profiles() -> dict[int, dict]:
    """account_id → {rate, allowance, exempt, label}."""
    with get_conn() as conn:
        return {r["account_id"]: dict(r) for r in conn.execute("SELECT * FROM tax_profiles")}


def profile_for(account_id: int) -> dict | None:
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM tax_profiles WHERE account_id = ?", (account_id,)).fetchone()
    return dict(r) if r else None


def set_profile(account_id: int, rate, allowance=0.0, exempt=0.0, label: str = "") -> None:
    """A rate of nothing and no label means: forget it, this account is
    not counted — which is different from a rate of zero that somebody
    chose, and the page says which it is."""
    def _num(v, lo, hi):
        if v in (None, ""):
            return None
        n = float(str(v).replace(",", "."))
        if not lo <= n <= hi:
            raise ValueError(f"A figure between {lo:g} and {hi:g}, not {n:g}.")
        return n
    rate = _num(rate, 0, 100)
    with get_conn() as conn:
        conn.execute("DELETE FROM tax_profiles WHERE account_id = ?", (account_id,))
        if rate is None:
            return
        conn.execute("INSERT INTO tax_profiles (account_id, rate, allowance, exempt, label) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (account_id, rate, _num(allowance, 0, 1e9) or 0.0,
                      _num(exempt, 0, 100) or 0.0, (label or "").strip()[:60]))


def _open_lots(account_ids: list[int] | None, how: str) -> dict[tuple[int, str], dict]:
    """Per account and security: the units still held and what they
    cost, from the same walk a sale would make."""
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id "
            f"WHERE t.isin IS NOT NULL AND t.quantity IS NOT NULL{only} "
            f"ORDER BY t.txn_date, t.id", params).fetchall()]
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for r in rows:
        grouped[(r["account_id"], r["isin"])].append(r)
    out = {}
    for key, rs in grouped.items():
        res = gains._run(rs, how)
        if res["open_quantity"] > 1e-9:
            out[key] = {"quantity": res["open_quantity"], "cost": res["open_cost"],
                        "currency": rs[-1]["currency"] or "EUR",
                        "account": rs[-1]["account_name"]}
    return out


def if_sold(account_ids: list[int] | None = None, how: str | None = None) -> dict:
    """Everything sold today: what it is worth, what the gain is, what
    the tax would be, and what would be left — per holding, per account
    and in total, in the dashboard's base currency."""
    base = settings.get("base_currency", "EUR")
    how = how or gains.method()
    held = _open_lots(account_ids, how)
    prices = {h["isin"]: h for h in overview.summary(base, account_ids=account_ids)["holdings"]}
    rules = profiles()
    with get_conn() as conn:
        names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM accounts")}

    rows, by_account = [], defaultdict(lambda: {"value": 0.0, "gain": 0.0, "rows": []})
    for (account_id, isin), lot in held.items():
        price = (prices.get(isin) or {}).get("price")
        if price is None:
            continue
        value_local = lot["quantity"] * price
        value, _ = fx.convert(value_local, lot["currency"], base)
        cost, _ = fx.convert(lot["cost"], lot["currency"], base)
        if value is None or cost is None:
            continue                       # no rate: say nothing rather than guess
        row = {"isin": isin, "name": (prices.get(isin) or {}).get("name") or isin,
               "account_id": account_id, "account": names.get(account_id, ""),
               "quantity": lot["quantity"], "value": round(value, 2),
               "cost": round(cost, 2), "gain": round(value - cost, 2)}
        rows.append(row)
        acc = by_account[account_id]
        acc["value"] += value
        acc["gain"] += value - cost
        acc["rows"].append(row)

    accounts, total_tax, total_value, total_gain, unknown = [], 0.0, 0.0, 0.0, []
    for account_id, acc in sorted(by_account.items(), key=lambda kv: -kv[1]["value"]):
        rule = rules.get(account_id)
        taxable = max(0.0, acc["gain"])
        tax = 0.0
        if rule:
            taxable = max(0.0, taxable * (1 - (rule["exempt"] or 0) / 100.0) - (rule["allowance"] or 0))
            tax = taxable * (rule["rate"] or 0) / 100.0
        else:
            unknown.append(names.get(account_id, ""))
        accounts.append({"account_id": account_id, "account": names.get(account_id, ""),
                         "value": round(acc["value"], 2), "gain": round(acc["gain"], 2),
                         "taxable": round(taxable, 2), "tax": round(tax, 2),
                         "net": round(acc["value"] - tax, 2),
                         "rule": rule, "counted": bool(rule)})
        total_tax += tax
        total_value += acc["value"]
        total_gain += acc["gain"]
    rows.sort(key=lambda r: -r["gain"])
    return {"base_currency": base, "method": how,
            "value": round(total_value, 2), "gain": round(total_gain, 2),
            "tax": round(total_tax, 2), "net": round(total_value - total_tax, 2),
            "accounts": accounts, "holdings": rows,
            # Accounts nobody has given a rule: their gain is in the
            # total, their tax is not, and the page says so rather than
            # printing a net figure that quietly assumes zero.
            "accounts_without_a_rule": unknown}
