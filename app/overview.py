"""What everything adds up to.

The one page that answers "how am I doing" rather than "what happened in
this account". Everything here is derived at request time from the rows
the importers and the bank sync wrote — nothing is stored, so there is no
cached total that can quietly disagree with the accounts it came from.

Two honesty rules run through it.

**Currencies are not added together.** There is no exchange-rate source
yet, so an amount in CHF is reported beside the base-currency total, not
inside it. A single number that silently treats 100 CHF as 100 EUR is
worse than two numbers, because it is wrong in a way nobody can see.

**Securities are valued at the last price you traded at.** That is not a
market price. It is the only price this app knows, it is labelled as such
everywhere it appears, and it is why a price feed is the next thing to
build.
"""

from __future__ import annotations

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
            securities_by_currency[ccy] = (
                securities_by_currency.get(ccy, 0.0) + item["value"])

    holdings_list = sorted(holdings.values(),
                           key=lambda h: -(h["value"] or 0))

    # ── Totals ───────────────────────────────────────────────────
    totals_by_currency: dict[str, float] = {}
    for source in (cash_by_currency, securities_by_currency):
        for ccy, amount in source.items():
            totals_by_currency[ccy] = totals_by_currency.get(ccy, 0.0) + amount

    # The headline is the base currency only. Everything else is listed
    # beside it, unconverted and saying so.
    unconverted = sorted(
        ({"currency": c, "amount": a} for c, a in totals_by_currency.items()
         if c != base_currency and abs(a) > 0.005),
        key=lambda x: -abs(x["amount"]))

    # ── Breakdowns for the charts ────────────────────────────────
    by_account = sorted(
        [{"name": r["name"], "value": r["balance"]}
         for r in rows
         if r["balance"] and r["balance_currency"] == base_currency
         and r["balance"] > 0],
        key=lambda x: -x["value"])
    for h in holdings_list:
        if h["value"] and (h["currency"] or base_currency) == base_currency:
            label = ", ".join(sorted(set(h["accounts"])))
            existing = next((b for b in by_account if b["name"] == label), None)
            if existing:
                existing["value"] += h["value"]
            else:
                by_account.append({"name": label, "value": h["value"]})
    by_account.sort(key=lambda x: -x["value"])

    by_class = []
    cash_base = cash_by_currency.get(base_currency, 0.0)
    sec_base = securities_by_currency.get(base_currency, 0.0)
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
