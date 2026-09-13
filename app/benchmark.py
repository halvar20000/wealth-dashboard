"""Against a benchmark: the same money in an index instead.

"Up 12 %" means one thing beside "the world index did 15 %" and
another beside "it did 4 %". So the portfolio's time-weighted return
is drawn day by day against an index over the same span, both
starting at 100 — the one comparison a time-weighted return exists
to make, because the timing of your own money is already taken out.

The index is a Yahoo symbol: a handful are offered by name — the
world, Europe, the S&P 500, the DAX, the SMI, emerging markets,
bitcoin — and any other can be typed. Broad indices are quoted in
their own currency and, where Yahoo has no clean index in euros, an
accumulating ETF stands in; the series is turned into the currency of
what it is compared to, at each day's ECB rate, so a Swiss reader
comparing a franc portfolio to the S&P sees the franc return of the
S&P, which is the honest one.

The benchmark's daily closes are kept in the `prices` table under a
pseudo-ISIN `BENCH:<symbol>`, fetched once back to the first trade
and topped up when a day is missing — so the second look is free.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import prices
from .db import get_conn

PREFIX = "BENCH:"

# Name, symbol, currency the symbol is quoted in. A proxy ETF where the
# index itself has no usable quote on Yahoo.
BENCHMARKS = {
    "world": ("MSCI World", "EUNL.DE", "EUR"),
    "all_world": ("FTSE All-World", "VWCE.DE", "EUR"),
    "sp500": ("S&P 500", "^GSPC", "USD"),
    "nasdaq": ("Nasdaq 100", "^NDX", "USD"),
    "europe": ("Euro Stoxx 50", "^STOXX50E", "EUR"),
    "dax": ("DAX", "^GDAXI", "EUR"),
    "smi": ("SMI", "^SSMI", "CHF"),
    "emerging": ("MSCI Emerging Markets", "IS3N.DE", "EUR"),
    "bonds_eur": ("Euro government bonds", "VETY.DE", "EUR"),
    "gold": ("Gold", "GC=F", "USD"),
    "bitcoin": ("Bitcoin", "BTC-EUR", "EUR"),
}


def resolve(key_or_symbol: str) -> tuple[str, str]:
    """(label, symbol) for a known key or a symbol typed in."""
    k = (key_or_symbol or "world").strip()
    if k in BENCHMARKS:
        return BENCHMARKS[k][0], BENCHMARKS[k][1]
    sym = k.upper()
    return sym, sym


def closes(symbol: str, since: str, get=None, today: date | None = None) -> list[tuple[str, float, str]]:
    """The benchmark's daily closes from `since`, from the table, fetched
    or topped up from Yahoo when the table is short."""
    today = today or date.today()
    key = PREFIX + symbol.upper()
    with get_conn() as conn:
        rows = [(r["as_of"], r["price"], r["currency"]) for r in conn.execute(
            "SELECT as_of, price, currency FROM prices WHERE isin = ? ORDER BY as_of", (key,))]
    have_from = rows[0][0] if rows else None
    have_to = rows[-1][0] if rows else None
    need_from = None
    if not rows or have_from > since:
        need_from = since
    elif have_to < (today - timedelta(days=2)).isoformat():
        need_from = have_to
    if need_from:
        try:
            fresh = prices.history(symbol, need_from, get)
        except prices.PriceError:
            fresh = []
        if fresh:
            with get_conn() as conn:
                for day, close, ccy in fresh:
                    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) "
                                 "VALUES (?, ?, ?, ?)", (key, day, close, ccy))
                rows = [(r["as_of"], r["price"], r["currency"]) for r in conn.execute(
                    "SELECT as_of, price, currency FROM prices WHERE isin = ? ORDER BY as_of", (key,))]
    return [r for r in rows if r[0] >= since]


def indexed(values: list[tuple[str, float | None]], flows: dict[str, float]) -> list[tuple[str, float]]:
    """The time-weighted growth as an index: 100 on the first day with
    a value, chain-linked over each day's return with the day's flows
    taken out — the same arithmetic as performance.twr(), kept as a
    line instead of one number."""
    out = []
    growth = 100.0
    prev = None
    for day, value in values:
        if value is None:
            prev = None
            continue
        if prev is not None:
            base = prev + flows.get(day, 0.0)
            if base > 1e-9:
                growth *= value / base
        prev = value
        out.append((day, growth))
    return out


def compare(portfolio: list[tuple[str, float]], bench: list[tuple[str, float, str]],
            currency: str) -> dict:
    """Both lines over the portfolio's days, at 100 on the first day both
    exist, the benchmark in the portfolio's currency. Weekends and
    holidays carry the benchmark's last close forward."""
    if not portfolio:
        return {"points": [], "portfolio": None, "benchmark": None}
    convert = prices.in_currency(currency)
    bench_c = []
    for day, px, ccy in bench:
        v = convert(px, ccy, day)
        if v is not None:
            bench_c.append((day, v))
    if not bench_c:
        return {"points": [], "portfolio": None, "benchmark": None}
    from bisect import bisect_right
    bdays = [d for d, _ in bench_c]
    first = next((d for d, _ in portfolio if bisect_right(bdays, d)), None)
    if first is None:
        return {"points": [], "portfolio": None, "benchmark": None}
    p0 = next(v for d, v in portfolio if d == first)
    b0 = bench_c[bisect_right(bdays, first) - 1][1]
    points = []
    for d, v in portfolio:
        if d < first:
            continue
        i = bisect_right(bdays, d)
        points.append({"date": d, "portfolio": v / p0 * 100.0, "benchmark": bench_c[i - 1][1] / b0 * 100.0})
    last = points[-1]
    return {"points": points, "portfolio": last["portfolio"] - 100.0, "benchmark": last["benchmark"] - 100.0,
            "since": first}
