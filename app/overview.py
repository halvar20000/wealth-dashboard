"""What everything adds up to.

The one page that answers "how am I doing" rather than "what happened in
this account". Everything here is derived at request time from the rows
the importers and the bank sync wrote — nothing is stored, so there is no
cached total that can quietly disagree with the accounts it came from.

Two honesty rules run through it.

**Currencies are converted at a rate the page names, or not at all.**
ECB reference rates, with the publication date shown beside the total.
An amount whose currency the ECB does not publish — or any amount at all
before the rates have ever been fetched — is still reported beside the
total rather than inside it. A single number that silently treats 100
CHF as 100 EUR is worse than two numbers, because it is wrong in a way
nobody can see; a number converted at a rate nobody can see is the same
failure one step later.

**Securities are valued at the last price you traded at.** That is not a
market price. It is the only price this app knows, it is labelled as such
everywhere it appears, and it is why a price feed is the next thing to
build.
"""

from __future__ import annotations

from . import fx
from .db import get_conn
from .importers import positions


def _latest_balances(conn) -> dict[int, dict]:
    """The most recent balance reading per account."""
    rows = conn.execute(
        """
        SELECT b.account_id, b.amount, b.currency, b.as_of, b.balance_type
          FROM balances b
          JOIN (SELECT account_id, MAX(as_of) AS as_of, MAX(id) AS id
                  FROM balances GROUP BY account_id) latest
            ON latest.account_id = b.account_id AND latest.id = b.id
        """).fetchall()
    return {r["account_id"]: dict(r) for r in rows}


def summary(base_currency: str = "EUR") -> dict:
    with get_conn() as conn:
        accounts = [dict(r) for r in conn.execute(
            "SELECT * FROM accounts ORDER BY name").fetchall()]
        balances = _latest_balances(conn)
        counts = {r["account_id"]: r["n"] for r in conn.execute(
            "SELECT account_id, COUNT(*) AS n FROM transactions "
            "GROUP BY account_id").fetchall()}
        banks = {r["account_id"]: r["aspsp_name"] for r in conn.execute(
            "SELECT account_id, aspsp_name FROM bank_links").fetchall()}
        recent = [dict(r) for r in conn.execute(
            "SELECT t.*, a.name AS account_name FROM transactions t "
            "JOIN accounts a ON a.id = t.account_id "
            "ORDER BY t.txn_date DESC, t.id DESC LIMIT 12").fetchall()]

    # ── Cash, per account ────────────────────────────────────────
    # What one euro is worth in each currency on the newest day the ECB
    # has published. Read once: a portfolio of forty holdings would
    # otherwise ask the same question forty times.
    fx_as_of, fx_rates = fx.rates_on()

    def to_base(amount: float | None, currency: str | None):
        """Into the base currency, or None when no rate says how.

        None is not zero and not the original number. Every caller here
        treats it as "cannot say", which is what puts the amount beside
        the total instead of inside it.
        """
        if amount is None:
            return None
        ccy = (currency or base_currency).upper()
        if ccy == base_currency.upper():
            return amount
        if ccy not in fx_rates or base_currency.upper() not in fx_rates:
            return None
        return amount / fx_rates[ccy] * fx_rates[base_currency.upper()]

    cash_by_currency: dict[str, float] = {}
    rows = []
    for acct in accounts:
        bal = balances.get(acct["id"])
        amount = bal["amount"] if bal else None
        currency = (bal["currency"] if bal else None) or acct["currency"]
        if amount is not None:
            cash_by_currency[currency] = cash_by_currency.get(currency, 0.0) + amount
        rows.append({
            **acct,
            "balance": amount,
            "balance_base": to_base(amount, currency),
            "balance_currency": currency,
            "balance_as_of": bal["as_of"] if bal else None,
            "transactions": counts.get(acct["id"], 0),
            "bank": banks.get(acct["id"]),
        })

    # ── Securities, across every account ─────────────────────────
    # Aggregated by ISIN, because the same fund held at two brokers is
    # one position from where the owner is standing.
    holdings: dict[str, dict] = {}
    securities_by_currency: dict[str, float] = {}
    for acct in accounts:
        for pos in positions(acct["id"]):
            key = pos["isin"]
            item = holdings.setdefault(key, {
                "isin": key, "name": pos["name"], "quantity": 0.0,
                "net_invested": 0.0, "currency": pos["currency"],
                "last_price": pos["last_price"], "value": 0.0,
                "accounts": [], "incomplete_history": False,
                "last_trade": pos["last_trade"],
            })
            item["quantity"] += pos["quantity"]
            item["net_invested"] += pos["net_invested"] or 0.0
            item["accounts"].append(acct["name"])
            item["incomplete_history"] |= bool(pos["incomplete_history"])
            if pos["last_trade"] and pos["last_trade"] > (item["last_trade"] or ""):
                item["last_trade"] = pos["last_trade"]
                item["last_price"] = pos["last_price"]
            if not item["name"] and pos["name"]:
                item["name"] = pos["name"]

    for item in holdings.values():
        if item["last_price"] is not None:
            item["value"] = item["quantity"] * item["last_price"]
            ccy = item["currency"] or base_currency
            item["value_base"] = to_base(item["value"], ccy)
            securities_by_currency[ccy] = (
                securities_by_currency.get(ccy, 0.0) + item["value"])
        else:
            item["value_base"] = None

    holdings_list = sorted(holdings.values(),
                           key=lambda h: -(h["value"] or 0))

    # ── Totals ───────────────────────────────────────────────────
    totals_by_currency: dict[str, float] = {}
    for source in (cash_by_currency, securities_by_currency):
        for ccy, amount in source.items():
            totals_by_currency[ccy] = totals_by_currency.get(ccy, 0.0) + amount

    # Three piles: the base currency, what a rate could convert, and
    # what nothing could. The last one is still shown beside the total
    # rather than dropped, because an amount the app cannot value is not
    # an amount that stopped existing.
    converted, unconverted = [], []
    for ccy, amount in totals_by_currency.items():
        if ccy == base_currency or abs(amount) <= 0.005:
            continue
        in_base = to_base(amount, ccy)
        if in_base is None:
            unconverted.append({"currency": ccy, "amount": amount})
        else:
            converted.append({"currency": ccy, "amount": amount,
                              "in_base": in_base})
    converted.sort(key=lambda x: -abs(x["in_base"]))
    unconverted.sort(key=lambda x: -abs(x["amount"]))

    # ── Breakdowns for the charts ────────────────────────────────
    # The charts are in the base currency, and now include anything a
    # rate could bring into it — a chart that quietly omits the dollar
    # account is a chart that disagrees with the total above it.
    by_account = sorted(
        [{"name": r["name"], "value": r["balance_base"]}
         for r in rows
         if r["balance_base"] and r["balance_base"] > 0],
        key=lambda x: -x["value"])
    for h in holdings_list:
        if h["value_base"]:
            label = ", ".join(sorted(set(h["accounts"])))
            existing = next((b for b in by_account if b["name"] == label), None)
            if existing:
                existing["value"] += h["value_base"]
            else:
                by_account.append({"name": label, "value": h["value_base"]})
    by_account.sort(key=lambda x: -x["value"])

    by_class = []
    # The totals are everything a rate could express in the base
    # currency, which on a single-currency install is exactly what it
    # was before.
    cash_base = sum(v for v in (to_base(a, c)
                                for c, a in cash_by_currency.items())
                    if v is not None)
    sec_base = sum(v for v in (to_base(a, c)
                               for c, a in securities_by_currency.items())
                   if v is not None)
    if cash_base:
        by_class.append({"name": "Cash", "value": cash_base})
    if sec_base:
        by_class.append({"name": "Securities", "value": sec_base})

    return {
        "base_currency": base_currency,
        "net_worth": cash_base + sec_base,
        "cash": cash_base,
        "securities": sec_base,
        "unconverted": unconverted,
        "converted": converted,
        # The date of the rates used, so the total can name it. None
        # when nothing needed converting.
        "fx_as_of": fx_as_of if converted else None,
        "accounts": rows,
        "account_count": len(rows),
        "connected_count": sum(1 for r in rows if r["bank"]),
        "holdings": holdings_list,
        "transaction_count": sum(counts.values()),
        "by_account": by_account[:10],
        "by_class": by_class,
        "recent": recent,
        # True when at least one holding has no price at all, so the page
        # can say the securities figure is partial rather than implying a
        # complete valuation.
        "holdings_unpriced": sum(1 for h in holdings_list
                                 if h["last_price"] is None),
    }
