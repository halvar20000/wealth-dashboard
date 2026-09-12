"""Net worth over time, rebuilt from what was recorded.

Nothing is snapshotted. The history is worked out on request from the
same facts every other page uses — the balance readings each account
has accumulated, the trades that make up each holding, the prices and
the ECB rates, each taken *as of the day being drawn*. A chart derived
that way cannot disagree with the pages beside it, and it goes back
exactly as far as the records do: a bank account's line starts with
its first reading, a holding's with its first trade.

That last point is the honest limit of this. An account connected last
week has one week of history however long it has existed, and the
chart says nothing about the time before. What makes the line fill in
is the daily sync: one reading a day, and after a month there is a
month.

Two rules from the overview carry over unchanged. An amount whose
currency has no rate on the day is left out of the total rather than
counted at face value; and a holding with no market price on the day
is valued at the last price it was traded at.
"""

from __future__ import annotations

from bisect import bisect_right
from datetime import date, timedelta

from . import people
from .db import get_conn

# Enough points to draw a smooth line, few enough that a decade is still
# cheap: each point is a walk over every account and holding.
MAX_POINTS = 130

PERIODS = {"1m": 31, "3m": 92, "6m": 183, "1y": 366, "ytd": None, "all": None}


def period_start(period: str, today: date | None = None) -> date | None:
    """The first day a period covers; None for 'all'."""
    today = today or date.today()
    if period == "ytd":
        return date(today.year, 1, 1)
    days = PERIODS.get(period)
    return None if days is None else today - timedelta(days=days)


def _sample_dates(start: date, end: date) -> list[date]:
    span = (end - start).days
    if span <= 0:
        return [end]
    step = max(1, -(-span // (MAX_POINTS - 1)))         # ceil
    out = [start + timedelta(days=i) for i in range(0, span, step)]
    if out[-1] != end:
        out.append(end)
    return out


def series(base_currency: str = "EUR", account_ids: list[int] | None = None,
           period: str = "ytd", today: date | None = None) -> dict:
    """The net worth on a set of days across the period.

    {points: [{date, net_worth, cash, securities}], first_date, ...}
    A point whose day predates every record is None rather than zero:
    the money existed, the app just has no reading of it.
    """
    base = base_currency.upper()
    today = today or date.today()
    only, params = people.sql_in(account_ids)
    only_t, params_t = people.sql_in(account_ids, "t.account_id")

    with get_conn() as conn:
        balances: dict[int, tuple[list[str], list[tuple[float, str]]]] = {}
        for r in conn.execute(
                f"SELECT account_id, as_of, amount, currency FROM balances "
                f"WHERE 1=1{only} ORDER BY account_id, as_of, id", params):
            days, vals = balances.setdefault(r["account_id"], ([], []))
            if days and days[-1] == r["as_of"]:
                vals[-1] = (r["amount"], r["currency"])   # newest reading of a day
            else:
                days.append(r["as_of"])
                vals.append((r["amount"], r["currency"]))

        # Per holding: the trades in date order, with the running quantity
        # and the price paid, so "held on day d" is one bisect.
        trades: dict[str, tuple[list[str], list[float], list[tuple[float, str]]]] = {}
        for r in conn.execute(
                f"SELECT t.isin, t.txn_date, t.quantity, t.price, t.currency "
                f"FROM transactions t WHERE t.isin IS NOT NULL AND t.quantity IS NOT NULL"
                f"{only_t} ORDER BY t.txn_date, t.id",
                params_t):
            days, qty, paid = trades.setdefault(r["isin"], ([], [], []))
            running = (qty[-1] if qty else 0.0) + (r["quantity"] or 0.0)
            last_paid = (r["price"], r["currency"]) if r["price"] else (
                paid[-1] if paid else (None, None))
            days.append(r["txn_date"]); qty.append(running); paid.append(last_paid)

        prices: dict[str, tuple[list[str], list[tuple[float, str]]]] = {}
        if trades:
            marks = ",".join("?" * len(trades))
            for r in conn.execute(
                    f"SELECT isin, as_of, price, currency FROM prices "
                    f"WHERE isin IN ({marks}) ORDER BY isin, as_of", list(trades)):
                days, vals = prices.setdefault(r["isin"], ([], []))
                days.append(r["as_of"]); vals.append((r["price"], r["currency"]))

        fx_days: list[str] = [r["as_of"] for r in conn.execute(
            "SELECT DISTINCT as_of FROM fx_rates ORDER BY as_of")]
        fx_rows = conn.execute(
            "SELECT as_of, currency, per_eur FROM fx_rates").fetchall()

    fx: dict[str, dict[str, float]] = {}
    for r in fx_rows:
        fx.setdefault(r["as_of"], {"EUR": 1.0})[r["currency"]] = r["per_eur"]

    def rates_at(day: str) -> dict[str, float]:
        i = bisect_right(fx_days, day)
        return fx[fx_days[i - 1]] if i else {"EUR": 1.0}

    def to_base(amount: float, ccy: str, rates: dict[str, float]) -> float | None:
        ccy = (ccy or base).upper()
        if ccy == base:
            return amount
        if ccy in rates and base in rates:
            return amount / rates[ccy] * rates[base]
        return None

    first_candidates = [d[0] for d, _ in balances.values() if d] + \
                       [d[0] for d, _, _ in trades.values() if d]
    first_date = min(first_candidates) if first_candidates else None
    start = period_start(period, today)
    if start is None:
        start = date.fromisoformat(first_date) if first_date else today
    if first_date and date.fromisoformat(first_date) > start:
        # No point drawing months of nothing before the first record.
        start = date.fromisoformat(first_date)

    points = []
    for day in _sample_dates(start, today):
        d = day.isoformat()
        rates = rates_at(d)
        cash = sec = 0.0
        known = False
        for days, vals in balances.values():
            i = bisect_right(days, d)
            if not i:
                continue
            v = to_base(vals[i - 1][0], vals[i - 1][1], rates)
            if v is not None:
                cash += v; known = True
        for isin, (days, qty, paid) in trades.items():
            i = bisect_right(days, d)
            if not i or abs(qty[i - 1]) < 1e-9:
                continue
            pdays, pvals = prices.get(isin, ([], []))
            j = bisect_right(pdays, d)
            price, ccy = pvals[j - 1] if j else paid[i - 1]
            if price is None:
                continue
            v = to_base(qty[i - 1] * price, ccy, rates)
            if v is not None:
                sec += v; known = True
        points.append({"date": d, "net_worth": (cash + sec) if known else None,
                       "cash": cash if known else None,
                       "securities": sec if known else None})

    firsts = [p for p in points if p["net_worth"] is not None]
    return {
        "period": period,
        "points": points,
        "first_date": first_date,
        "start": firsts[0] if firsts else None,
        "base_currency": base,
    }
