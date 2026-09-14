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


class Valuer:
    """Everything needed to say what a set of accounts was worth on any
    day, loaded once: the balance readings, the trades with their
    running quantities, the prices, the ECB rates. `value_on(day)` is
    then a handful of bisects — cheap enough to call for every day of
    a decade, which the performance figures do.

    Built once per request for one set of accounts, because the
    loading is the expensive half and the same facts answer both "what
    was the net worth on the 3rd" and "on the 4th".
    """

    def __init__(self, base_currency: str = "EUR", account_ids: list[int] | None = None):
        self.base = base_currency.upper()
        only, params = people.sql_in(account_ids)
        only_t, params_t = people.sql_in(account_ids, "t.account_id")
        with get_conn() as conn:
            self.balances: dict[int, tuple[list[str], list[tuple[float, str]]]] = {}
            for r in conn.execute(
                    f"SELECT account_id, as_of, amount, currency FROM balances "
                    f"WHERE 1=1{only} ORDER BY account_id, as_of, id", params):
                days, vals = self.balances.setdefault(r["account_id"], ([], []))
                if days and days[-1] == r["as_of"]:
                    vals[-1] = (r["amount"], r["currency"])   # newest reading of a day
                else:
                    days.append(r["as_of"])
                    vals.append((r["amount"], r["currency"]))

            # Per holding: the trades in date order, with the running
            # quantity and the price paid, so "held on day d" is one bisect.
            self.trades: dict[str, tuple[list[str], list[float], list[tuple[float, str]]]] = {}
            per_isin: dict[str, list] = {}
            for r in conn.execute(
                    f"SELECT t.isin, t.txn_date, t.kind, t.quantity, t.price, t.currency "
                    f"FROM transactions t WHERE t.isin IS NOT NULL AND t.quantity IS NOT NULL"
                    f"{only_t} ORDER BY t.txn_date, t.id",
                    params_t):
                per_isin.setdefault(r["isin"], []).append(dict(r))
            # Units in today's terms: a market price is split-adjusted,
            # so the units held before a split are scaled to match — see
            # splits.factors(). The last price paid is in the units of
            # its day and is kept with a factor of its own.
            from . import splits
            for isin, rows in per_isin.items():
                days, qty, paid = self.trades.setdefault(isin, ([], [], []))
                factor = splits.factors(rows)
                running = 0.0
                for r, f in zip(rows, factor):
                    running += r["quantity"] or 0.0
                    last_paid = (r["price"] / f, r["currency"]) if r["price"] else (
                        paid[-1] if paid else (None, None))
                    days.append(r["txn_date"]); qty.append(running * f); paid.append(last_paid)

            self.prices: dict[str, tuple[list[str], list[tuple[float, str]]]] = {}
            if self.trades:
                marks = ",".join("?" * len(self.trades))
                for r in conn.execute(
                        f"SELECT isin, as_of, price, currency FROM prices "
                        f"WHERE isin IN ({marks}) ORDER BY isin, as_of", list(self.trades)):
                    days, vals = self.prices.setdefault(r["isin"], ([], []))
                    days.append(r["as_of"]); vals.append((r["price"], r["currency"]))

        from . import fx
        self.fx_days, self.fx = fx.table()
        firsts = [d[0] for d, _ in self.balances.values() if d] + \
                 [d[0] for d, _, _ in self.trades.values() if d]
        self.first_date: str | None = min(firsts) if firsts else None

    def rates_at(self, day: str) -> dict[str, float]:
        i = bisect_right(self.fx_days, day)
        return self.fx[self.fx_days[i - 1]] if i else {"EUR": 1.0}

    def to_base(self, amount: float, ccy: str, day: str,
                rates: dict[str, float] | None = None) -> float | None:
        ccy = (ccy or self.base).upper()
        if ccy == self.base:
            return amount
        rates = rates or self.rates_at(day)
        if ccy in rates and self.base in rates:
            return amount / rates[ccy] * rates[self.base]
        return None

    def value_on(self, day: str) -> tuple[float | None, float | None]:
        """(cash, securities) in the base currency on `day`; None where
        nothing is known yet. A holding with no market price on the day
        is valued at the last price it was traded at."""
        rates = self.rates_at(day)
        cash = sec = 0.0
        known_cash = known_sec = False
        for days, vals in self.balances.values():
            i = bisect_right(days, day)
            if not i:
                continue
            v = self.to_base(vals[i - 1][0], vals[i - 1][1], day, rates)
            if v is not None:
                cash += v; known_cash = True
        for isin, (days, qty, paid) in self.trades.items():
            i = bisect_right(days, day)
            if not i or abs(qty[i - 1]) < 1e-9:
                continue
            pdays, pvals = self.prices.get(isin, ([], []))
            j = bisect_right(pdays, day)
            price, ccy = pvals[j - 1] if j else paid[i - 1]
            if price is None:
                continue
            v = self.to_base(qty[i - 1] * price, ccy, day, rates)
            if v is not None:
                sec += v; known_sec = True
        return (cash if known_cash else None), (sec if known_sec else None)


def series(base_currency: str = "EUR", account_ids: list[int] | None = None,
           period: str = "ytd", today: date | None = None) -> dict:
    """The net worth on a set of days across the period.

    {points: [{date, net_worth, cash, securities}], first_date, ...}
    A point whose day predates every record is None rather than zero:
    the money existed, the app just has no reading of it.
    """
    today = today or date.today()
    v = Valuer(base_currency, account_ids)
    first_date = v.first_date
    start = period_start(period, today)
    if start is None:
        start = date.fromisoformat(first_date) if first_date else today
    if first_date and date.fromisoformat(first_date) > start:
        # No point drawing months of nothing before the first record.
        start = date.fromisoformat(first_date)

    points = []
    for day in _sample_dates(start, today):
        d = day.isoformat()
        cash, sec = v.value_on(d)
        known = cash is not None or sec is not None
        points.append({"date": d, "net_worth": ((cash or 0.0) + (sec or 0.0)) if known else None,
                       "cash": (cash or 0.0) if known else None,
                       "securities": (sec or 0.0) if known else None})

    firsts = [p for p in points if p["net_worth"] is not None]
    return {
        "period": period,
        "points": points,
        "first_date": first_date,
        "start": firsts[0] if firsts else None,
        "base_currency": v.base,
    }
