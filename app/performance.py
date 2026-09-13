"""Time-weighted and money-weighted return — the two numbers that
answer "how did it do", and answer it differently on purpose.

**TWR** (time-weighted, chain-linked daily) is the return of the
*investment*, with the timing of your own money taken out: every day's
return is measured after the day's cash flows are added, and the days
are multiplied together. It is what compares a fund to a benchmark, or
one holding to another, regardless of when each was bought.

**MWR** (money-weighted, the internal rate of return) is the return of
*your money*: the annual rate at which every amount you put in and took
out, plus what is left, comes to zero. A well-timed buy raises it; a
badly timed one lowers it. It is what your statement's "performance"
usually means, and what a deposit account would have had to pay.

Both are computed on the same facts the pages already show — the
daily value from `history.Valuer` or `prices.series_for`, and the
rows that moved money — and neither is stored, so a corrected row or
a backfilled price changes the figure on the next page load.

Sign conventions, once. A flow is money crossing the boundary of what
is measured. For a holding that is a buy (money in, +), a sale or a
dividend (money out, −); the cash effect a row carries is the
investor's side, so the flow is minus the amount. For MWR the investor
side is used as is — a buy is money gone, a sale or dividend money
back — with what is still held counted as money back at the end.

The maths follows Portfolio Performance's "true time-weighted rate of
return" and its IRR: daily sub-periods, flows at the start of the day,
365.25-day years for annualising.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta

from . import history, prices
from .db import get_conn

YEAR = 365.25


def twr(values: list[tuple[str, float | None]], flows: dict[str, float]) -> float | None:
    """Chain-linked daily return over the whole series, as a fraction.

    `values` is [(day, value)] on consecutive days, `flows` money added
    (+) or taken out (−) on a day, taken to happen before that day's
    valuation. A day on which the value is unknown breaks the chain
    for that day only; a day on which the position was empty before
    the flow (the first buy) has no return to measure.
    """
    growth = 1.0
    prev = None
    counted = False
    for day, value in values:
        if value is None:
            prev = None
            continue
        if prev is not None:
            base = prev + flows.get(day, 0.0)
            if base > 1e-9:
                growth *= value / base
                counted = True
        prev = value
    return (growth - 1.0) if counted else None


def annualise(total: float | None, days: int) -> float | None:
    if total is None or days <= 0:
        return None
    if days < 30:
        return None                              # a fortnight annualised is a joke
    return (1.0 + total) ** (YEAR / days) - 1.0


def mwr(cashflows: list[tuple[str, float]], end_day: str, end_value: float | None) -> float | None:
    """The annual internal rate of return of the investor's cash flows.

    `cashflows` are (day, amount) from the investor's side — money put
    in negative, money received positive — and `end_value` is what is
    still held, counted as received on `end_day`. Solved by bisection
    on the sign of the net present value, which is monotonic in the
    rate for a series that starts with money going in; None when there
    is no such series or the rate would be absurd.
    """
    if end_value is None:
        return None
    flows = [(date.fromisoformat(d), a) for d, a in cashflows if abs(a) > 1e-9]
    if end_value > 1e-9:
        flows.append((date.fromisoformat(end_day), end_value))
    if not flows or not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        return None
    t0 = min(d for d, _ in flows)
    span = (max(d for d, _ in flows) - t0).days
    if span < 1:
        return None

    def npv(rate: float) -> float:
        return sum(a / (1.0 + rate) ** ((d - t0).days / YEAR) for d, a in flows)

    lo, hi = -0.9999, 100.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-7:
            break
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    rate = (lo + hi) / 2
    return rate if -0.999 < rate < 99 else None


# ─── One security ────────────────────────────────────────────────────

def for_security(isin: str, account_ids: list[int] | None = None,
                 today: date | None = None, currency: str | None = None) -> dict:
    """Since the first row: TWR (total and annualised), MWR (annual),
    and the span they cover — in the currency the shares were paid in,
    or the one asked for, flows turned at their own day's rate."""
    today = today or date.today()
    series = prices.series_for(isin, account_ids, today, currency)
    pts = series.get("points") or []
    if not pts:
        return {"twr": None, "twr_annual": None, "mwr": None, "days": 0}
    from . import people
    only, params = people.sql_in(account_ids, "account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT txn_date, kind, amount, currency FROM transactions WHERE isin = ? "
            f"AND kind IN ('buy', 'sell', 'dividend', 'interest'){only} ORDER BY txn_date",
            [isin, *params]).fetchall()
    convert = prices.in_currency(series["currency"])
    flows: dict[str, float] = defaultdict(float)
    cashflows = []
    for r in rows:
        amount = convert(r["amount"], r["currency"], r["txn_date"])
        if amount is None:
            continue
        flows[r["txn_date"]] += -amount
        cashflows.append((r["txn_date"], amount))
    values = [(p["date"], p["value"]) for p in pts]
    # The chain starts at the first day's closing value, which already
    # holds the first buy: the return of the first day itself is not
    # measured, which is how every tool does it.
    total = twr(values, flows)
    days = (today - date.fromisoformat(pts[0]["date"])).days
    last = pts[-1]
    return {"twr": total, "twr_annual": annualise(total, days),
            "mwr": mwr(cashflows, last["date"], last["value"]),
            "days": days, "since": pts[0]["date"]}


# ─── The securities of a set of accounts ─────────────────────────────

def for_accounts(base_currency: str = "EUR", account_ids: list[int] | None = None,
                 start: date | None = None, today: date | None = None) -> dict:
    """The securities held in these accounts, as one investment: TWR and
    MWR from `start` (or the first trade) to today, in the base currency.

    Cash is left out on purpose. Idle cash earns nothing and a deposit
    that sits unspent for a year would drag the figure to say nothing
    about the investments; and a broker account whose cash is not
    recorded would make every deposit look like a loss. So the boundary
    is the securities: a buy is money crossing in, a sale or a dividend
    money crossing out.
    """
    today = today or date.today()
    v = history.Valuer(base_currency, account_ids)
    if not v.trades:
        return {"twr": None, "twr_annual": None, "mwr": None, "days": 0, "since": None}
    first = min(d[0] for d, _, _ in v.trades.values() if d)
    begin = max(start, date.fromisoformat(first)) if start else date.fromisoformat(first)
    from . import people
    only, params = people.sql_in(account_ids, "account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT txn_date, amount, currency FROM transactions WHERE isin IS NOT NULL "
            f"AND kind IN ('buy', 'sell', 'dividend', 'interest') AND txn_date >= ?{only} "
            f"ORDER BY txn_date", [begin.isoformat(), *params]).fetchall()
    flows: dict[str, float] = defaultdict(float)
    cashflows = []
    for r in rows:
        amount = v.to_base(r["amount"], r["currency"], r["txn_date"])
        if amount is None:
            continue
        flows[r["txn_date"]] += -amount
        cashflows.append((r["txn_date"], amount))
    values = []
    d = begin
    while d <= today:
        ds = d.isoformat()
        _, sec = v.value_on(ds)
        values.append((ds, sec))
        d += timedelta(days=1)
    # Starting from a day the securities were already held: what was
    # held before that day's flows is the money put in, for the MWR.
    if start and values and values[0][1] is not None:
        opening = values[0][1] - flows.get(values[0][0], 0.0)
        if opening > 1e-9:
            cashflows = [(values[0][0], -opening)] + cashflows
    total = twr(values, flows)
    days = (today - begin).days
    last_day, last_value = values[-1] if values else (today.isoformat(), None)
    return {"twr": total, "twr_annual": annualise(total, days),
            "mwr": mwr(cashflows, last_day, last_value), "days": days,
            "since": begin.isoformat()}
