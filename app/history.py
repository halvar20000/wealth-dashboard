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
            # Which pile an account's balance belongs in: a pension, a P2P
            # book, a house is wealth but not cash — see overview.ASSET_TYPES
            # — and the page can leave a pile out of the line.
            only_a, params_a = people.sql_in(account_ids, "id")
            self.types: dict[int, str] = {r["id"]: r["type"] for r in
                                          conn.execute(f"SELECT id, type FROM accounts WHERE 1=1{only_a}", params_a)}
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
        is valued at the last price it was traded at. "Cash" here is
        every balance — a pension's, a loan's — so the two add up to the
        net worth; assets_on() says how much of it is which."""
        cash, sec, _ = self._on(day)
        return cash, sec

    def assets_on(self, day: str) -> dict[str, float]:
        """The balance-only assets on `day`, by type — what the line can
        be drawn without."""
        return self._on(day)[2]

    def _on(self, day: str) -> tuple[float | None, float | None, dict[str, float]]:
        from .overview import ASSET_TYPES
        rates = self.rates_at(day)
        cash = sec = 0.0
        known_cash = known_sec = False
        assets: dict[str, float] = {}
        for account_id, (days, vals) in self.balances.items():
            i = bisect_right(days, day)
            if not i:
                continue
            v = self.to_base(vals[i - 1][0], vals[i - 1][1], day, rates)
            if v is not None:
                cash += v; known_cash = True
                t = self.types.get(account_id)
                if t in ASSET_TYPES:
                    assets[t] = assets.get(t, 0.0) + v
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
        return (cash if known_cash else None), (sec if known_sec else None), assets


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
    # Net worth as another app recorded it, for the days before this
    # app's own records reach — see net_worth_readings in db.py. Used
    # only up to the day the records take over, so the two never mix.
    recorded = _recorded(v.base, account_ids)
    takeover = _records_from(account_ids)
    if recorded:
        # The other app's total is the first complete picture; what
        # this app can work out for the days before it — the trades of
        # a broker or two, no cash — is a fraction that would draw a
        # step up to the real number. The line starts where the whole
        # is known.
        first_date = min(recorded)
    start = period_start(period, today)
    if start is None:
        start = date.fromisoformat(first_date) if first_date else today
    if first_date and date.fromisoformat(first_date) > start:
        # No point drawing months of nothing before the first record.
        start = date.fromisoformat(first_date)

    rec_days = sorted(recorded)
    points = [_point(v, recorded, rec_days, takeover, day)
              for day in _sample_dates(start, today)]

    firsts = [p for p in points if p["net_worth"] is not None]
    return {
        "period": period,
        "points": points,
        "first_date": first_date,
        "start": firsts[0] if firsts else None,
        "base_currency": v.base,
    }


def _point(v: Valuer, recorded: dict[str, float], rec_days: list[str],
           takeover: str | None, day: date) -> dict:
    """The net worth on one day, from this app's records or — before
    they reach — from another app's recorded totals."""
    d = day.isoformat()
    if rec_days and (takeover is None or d < takeover):
        # The newest recorded day at or before this one, as a balance
        # reading is carried forward — but not across a gap of more
        # than a month, which would draw a flat line over days nobody
        # recorded.
        i = bisect_right(rec_days, d)
        if i and (day - date.fromisoformat(rec_days[i - 1])).days <= 31:
            return {"date": d, "net_worth": recorded[rec_days[i - 1]], "cash": None,
                    "securities": None, "assets": {}, "recorded": True}
    if rec_days and d < rec_days[0]:
        return {"date": d, "net_worth": None, "cash": None, "securities": None, "assets": {}}
    cash, sec, assets = v._on(d)
    known = cash is not None or sec is not None
    return {"date": d, "net_worth": ((cash or 0.0) + (sec or 0.0)) if known else None,
            "cash": (cash or 0.0) if known else None,
            "securities": (sec or 0.0) if known else None,
            "assets": assets if known else {}}


def changes(now: float | None, base_currency: str = "EUR",
            account_ids: list[int] | None = None, today: date | None = None) -> dict:
    """How far the net worth `now` is from a month ago and from the
    start of the year: the two tiles under the hero.

    {month: {since, from, diff, pct}, ytd: {...}} — `from` is None where
    no reading covers the earlier day, and then there is no diff either:
    a change measured from nothing is not a change. `since` is the day
    actually compared against, which for the year is 1 January unless
    the records start later, in which case it says so.
    """
    today = today or date.today()
    v = Valuer(base_currency, account_ids)
    recorded = _recorded(v.base, account_ids)
    rec_days = sorted(recorded)
    takeover = _records_from(account_ids)
    # As series() does: where another app's totals exist, the line —
    # and so the comparison — starts where the whole is known.
    first = rec_days[0] if rec_days else v.first_date
    out = {}
    for key, since in (("month", today - timedelta(days=30)), ("ytd", date(today.year, 1, 1))):
        if first and date.fromisoformat(first) > since:
            since = date.fromisoformat(first)
        earlier = _point(v, recorded, rec_days, takeover, since)["net_worth"] \
            if since < today else None
        if earlier is None or now is None:
            out[key] = {"since": since.isoformat(), "from": None, "diff": None, "pct": None}
            continue
        diff = now - earlier
        out[key] = {"since": since.isoformat(), "from": earlier, "diff": diff,
                    "pct": (diff / abs(earlier) * 100) if earlier else None}
    return out


def _recorded(base: str, account_ids: list[int] | None) -> dict[str, float]:
    """Net worth readings brought over from another app, in the base
    currency. Only for the whole household: another app's total cannot
    be cut down to one person's accounts."""
    if account_ids is not None:
        return {}
    with get_conn() as conn:
        return {r["as_of"]: r["amount"] for r in conn.execute(
            "SELECT as_of, amount FROM net_worth_readings WHERE currency = ? ORDER BY as_of", (base.upper(),))}


def _records_from(account_ids: list[int] | None) -> str | None:
    """The first day the readings moved in from another app cover every
    account — from there on this app's own arithmetic draws the line.
    The move writes it down (a stray reading dated earlier, a fund's
    last update, would otherwise hand the line over months too soon);
    an older move without it falls back to the first such reading."""
    from .db import get_state
    day = get_state("records_from")
    if day:
        return day
    only, params = people.sql_in(account_ids)
    with get_conn() as conn:
        row = conn.execute(f"SELECT MIN(as_of) AS d FROM balances WHERE balance_type = 'financial_planner'{only}",
                           params).fetchone()
    return row["d"] if row and row["d"] else None
