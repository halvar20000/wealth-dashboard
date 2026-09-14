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

**Securities are valued at a market price that names its day** — see
prices.py — and where there is none, at the last price you traded at,
which is labelled as such wherever it appears. The two are never mixed
without saying so: the page says how many holdings are at market and how
many are at their last trade.
"""

from __future__ import annotations

from . import fx, people, prices
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


# Accounts whose balance is an asset but not cash: a pension fund, the
# notes on a lending platform, a house. They count in the net worth
# and get a pile of their own — a pension in the cash tile would say
# there is money to spend that cannot be touched for twenty years.
ASSET_TYPES = {"pension": "Pension", "p2p": "P2P lending", "property": "Property"}

# The four groups the accounts table is laid out in — the way a
# balance sheet reads: what is money, what is invested, what is put
# away for later, what is owed.
GROUPS = (("cash", "Cash & banks", ("bank", "savings", "card", "other")),
          ("investments", "Investments", ("broker", "p2p", "property")),
          ("pension", "Pension", ("pension",)),
          ("liabilities", "Liabilities", ("loan",)))
GROUP_OF = {t: g for g, _, types in GROUPS for t in types}


def summary(base_currency: str = "EUR", account_ids: list[int] | None = None) -> dict:
    """Everything, or one person's share of it — see people.scope()."""
    only, params = people.sql_in(account_ids, "id")
    only_t, params_t = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        accounts = [dict(r) for r in conn.execute(
            f"SELECT * FROM accounts WHERE 1=1{only} ORDER BY name", params).fetchall()]
        balances = _latest_balances(conn)
        counts = {r["account_id"]: r["n"] for r in conn.execute(
            "SELECT account_id, COUNT(*) AS n FROM transactions "
            "GROUP BY account_id").fetchall()}
        banks = {r["account_id"]: r["aspsp_name"] for r in conn.execute(
            "SELECT account_id, aspsp_name FROM bank_links").fetchall()}
        owners = people.by_account(conn)
        recent = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id WHERE 1=1{only_t} "
            f"ORDER BY t.txn_date DESC, t.id DESC LIMIT 12", params_t).fetchall()]
        # How many accounts the lens leaves out, so the accounts page
        # can say so instead of looking like the others were deleted.
        hidden = 0 if account_ids is None else conn.execute(
            "SELECT COUNT(*) AS n FROM accounts").fetchone()["n"] - len(accounts)

    # ── Cash, per account ────────────────────────────────────────
    # What one euro is worth in each currency on the newest day the ECB
    # has published. Read once: a portfolio of forty holdings would
    # otherwise ask the same question forty times.
    fx_as_of, fx_rates = fx.rates_on()

    def between(amount: float | None, frm: str | None, to: str | None):
        """From one currency into another, or None when no rate says how.

        None is not zero and not the original number. Every caller here
        treats it as "cannot say", which is what puts the amount beside
        the total instead of inside it.
        """
        if amount is None:
            return None
        frm = (frm or base_currency).upper()
        to = (to or base_currency).upper()
        if frm == to:
            return amount
        if frm not in fx_rates or to not in fx_rates:
            return None
        return amount / fx_rates[frm] * fx_rates[to]

    def to_base(amount: float | None, currency: str | None):
        return between(amount, currency, base_currency)

    cash_by_currency: dict[str, float] = {}
    debt_by_currency: dict[str, float] = {}
    assets_by_currency: dict[str, float] = {}
    assets_by_type: dict[str, float] = {}
    rows = []
    for acct in accounts:
        bal = balances.get(acct["id"])
        amount = bal["amount"] if bal else None
        currency = (bal["currency"] if bal else None) or acct["currency"]
        if amount is not None:
            # A loan's reading is negative — money owed — and is debt,
            # not cash: the net worth subtracts it, the cash tile does not.
            # A pension, a P2P book or a house is an asset, not cash.
            if acct["type"] == "loan":
                pile = debt_by_currency
            elif acct["type"] in ASSET_TYPES:
                pile = assets_by_currency
            else:
                pile = cash_by_currency
            pile[currency] = pile.get(currency, 0.0) + amount
        rows.append({
            **acct,
            "balance": amount,
            "balance_base": to_base(amount, currency),
            "balance_currency": currency,
            "balance_as_of": bal["as_of"] if bal else None,
            "transactions": counts.get(acct["id"], 0),
            "bank": banks.get(acct["id"]),
            "people": owners.get(acct["id"], []),
        })

    # ── Securities, across every account ─────────────────────────
    # Aggregated by ISIN, because the same fund held at two brokers is
    # one position from where the owner is standing.
    holdings: dict[str, dict] = {}
    securities_by_currency: dict[str, float] = {}
    # Per account too, so the accounts table can say what each broker
    # is worth, not only what the household holds of each security.
    per_account: dict[int, list[tuple[str, float]]] = {}
    for acct in accounts:
        for pos in positions(acct["id"]):
            key = pos["isin"]
            per_account.setdefault(acct["id"], []).append((key, pos["quantity"]))
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

    # A market price where there is one, in the holding's own currency
    # so that it sits beside net_invested; the last trade where there is
    # not. Which one it was is on the item, because the page says it.
    market = prices.latest()
    prices_as_of: str | None = None
    for item in holdings.values():
        ccy = item["currency"] or base_currency
        item["price"], item["price_kind"] = None, None
        item["price_as_of"], item["symbol"] = None, None
        quote = market.get(item["isin"])
        if quote:
            in_own = between(quote["price"], quote["currency"], ccy)
            if in_own is not None:
                item["price"], item["price_kind"] = in_own, "market"
                item["price_as_of"], item["symbol"] = quote["as_of"], quote["symbol"]
                if prices_as_of is None or quote["as_of"] > prices_as_of:
                    prices_as_of = quote["as_of"]
        if item["price"] is None and item["last_price"] is not None:
            item["price"], item["price_kind"] = item["last_price"], "trade"
        if item["price"] is not None:
            item["value"] = item["quantity"] * item["price"]
            item["value_base"] = to_base(item["value"], ccy)
            securities_by_currency[ccy] = (
                securities_by_currency.get(ccy, 0.0) + item["value"])
        else:
            item["value_base"] = None

    holdings_list = sorted(holdings.values(),
                           key=lambda h: -(h["value"] or 0))

    # Each account: its cash, its securities at the prices above, the
    # two together — and the figure in the account's own currency when
    # everything in it is in that currency, as a statement would show.
    for r in rows:
        sec_base = 0.0
        own = True
        sec_native = 0.0
        for key, qty in per_account.get(r["id"], []):
            item = holdings[key]
            if item["price"] is None:
                continue
            v = qty * item["price"]
            vb = to_base(v, item["currency"] or base_currency)
            sec_base += vb or 0.0
            if (item["currency"] or base_currency).upper() == r["currency"].upper():
                sec_native += v
            else:
                own = False
        r["securities_base"] = sec_base
        r["total_base"] = (r["balance_base"] or 0.0) + sec_base
        native_cash = r["balance"] if r["balance"] is not None and r["balance_currency"].upper() == r["currency"].upper() else None
        if r["balance"] is not None and r["balance_currency"].upper() != r["currency"].upper():
            own = False
        r["total_native"] = ((native_cash or 0.0) + sec_native) if own and (native_cash is not None or sec_native) else None
        r["group"] = GROUP_OF.get(r["type"], "cash")
    groups = []
    for key, label, _types in GROUPS:
        members = [r for r in rows if r["group"] == key]
        if members:
            members.sort(key=lambda r: -abs(r["total_base"]))
            groups.append({"key": key, "label": label, "accounts": members,
                           "total_base": sum(r["total_base"] for r in members)})

    # ── Totals ───────────────────────────────────────────────────
    totals_by_currency: dict[str, float] = {}
    for source in (cash_by_currency, securities_by_currency, assets_by_currency, debt_by_currency):
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
    debt_base = -sum(v for v in (to_base(a, c)
                                 for c, a in debt_by_currency.items())
                     if v is not None)
    assets_base = 0.0
    for r in rows:
        if r["type"] in ASSET_TYPES and r["balance_base"]:
            assets_base += r["balance_base"]
            assets_by_type[r["type"]] = assets_by_type.get(r["type"], 0.0) + r["balance_base"]
    if cash_base:
        by_class.append({"name": "Cash", "value": cash_base})
    if sec_base:
        by_class.append({"name": "Securities", "value": sec_base})
    for t, v in sorted(assets_by_type.items(), key=lambda kv: -kv[1]):
        by_class.append({"name": ASSET_TYPES[t], "value": v})

    return {
        "base_currency": base_currency,
        "net_worth": cash_base + sec_base + assets_base - debt_base,
        "cash": cash_base,
        "securities": sec_base,
        # The pension, P2P and property balances: an asset, not cash.
        "assets": assets_base,
        "assets_by_type": assets_by_type,
        "debt": debt_base,
        "unconverted": unconverted,
        "converted": converted,
        # The date of the rates used, so the total can name it. None
        # when nothing needed converting.
        "fx_as_of": fx_as_of if converted else None,
        "accounts": rows,
        "groups": groups,
        "account_count": len(rows),
        "connected_count": sum(1 for r in rows if r["bank"]),
        "holdings": holdings_list,
        "transaction_count": sum(counts.get(a["id"], 0) for a in accounts),
        "hidden_accounts": hidden,
        "by_account": by_account[:10],
        "by_class": by_class,
        "recent": recent,
        # True when at least one holding has no price at all, so the page
        # can say the securities figure is partial rather than implying a
        # complete valuation.
        "holdings_unpriced": sum(1 for h in holdings_list
                                 if h["price"] is None),
        # How the securities figure was reached: how many holdings are
        # at a market price, how many at their last trade, and the day
        # of the newest market price — so the total can name it.
        "holdings_at_market": sum(1 for h in holdings_list
                                  if h["price_kind"] == "market"),
        "holdings_at_trade": sum(1 for h in holdings_list
                                 if h["price_kind"] == "trade"),
        "prices_as_of": prices_as_of,
    }
