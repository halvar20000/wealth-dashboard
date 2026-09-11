"""ETF ideas — "high growth, low TER" and "high yield, low TER".

The two fund boards of Share Ideas. They rank a curated UCITS universe on
what actually separates one index fund from another:

    growth (past total return, in EUR)  ·  cost (TER)
    ·  risk (volatility and worst drawdown)  ·  size (fund survivability)

and, for the dividend board, the income the fund actually paid.

Why this is a separate module and not a third profile of `screener.py`
----------------------------------------------------------------------
The value and income boards are two profiles over one table because they
ask different questions of the *same* facts. An ETF shares almost none of
those facts: it has no ROE, no payout ratio, no P/E and no 52-week
narrative worth ranking. It has a TER, which no share has, and its growth
has to be *computed from a price series* rather than read from a field.
Different inputs, different fetch, different table.

Growth is computed, not read
----------------------------
Yahoo's `threeYearAverageReturn` / `fiveYearAverageReturn` are populated
for US mutual funds and reliably EMPTY for the European UCITS listings
this board is made of — which are exactly the ETFs that can be bought
here. A board whose headline column is blank for every row it cares about
is not a board. So the return comes from the price history instead, via
the same anonymous Yahoo chart endpoint `prices.py` uses.

Two things about that series matter enormously and are easy to get wrong:

1. **The closes must be ADJUSTED.** The raw close of a *distributing* ETF
   drops by the dividend on every ex-date, so its price CAGR understates
   its real return by roughly its yield every year — which on this board
   would rank every accumulating share class above the distributing share
   class of the very same fund, for a reason that does not exist. Yahoo's
   `adjclose` reinvests distributions and makes the two comparable.
2. **The series is converted to EUR before anything is measured.**
   `IWDA.AS` and `CSPX.AS` are quoted in USD even though they trade on
   Euronext; `EUNL.DE` quotes the same fund in EUR. Comparing their raw
   CAGRs ranks the dollar, not the fund. One FX series per currency per
   run fixes it, and the FX series is fetched once and reused.

What the growth column is NOT
-----------------------------
It is the past five years, in EUR, after the fund's costs. It is not a
forecast, and over a window that contained one of the strongest US equity
runs on record it will rank concentration highly — the Nasdaq and
semiconductor funds are at the top of this board because of what already
happened, not because of what will. The cost pillar is the only column
here that is a fact about the *future*: a TER is charged every year
whatever the market does. That asymmetry is the reason cost carries 30%
of a board whose headline is growth.
"""

from __future__ import annotations

import json
import math
import time
from datetime import date, datetime, timezone

from . import i18n
from .settings import DATA_DIR
from .screener import _blend, _ramp, held_symbols, owned_symbols
from .screener_etf_universe import DEFAULT_ETF_UNIVERSE

CONFIG_FILE = DATA_DIR / "screener.json"          # shared with screener.py
UNIVERSE_FILE = DATA_DIR / "screener_etf_universe.json"

_t, _f = i18n.t, i18n.f

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULTS = {
    "weights": {
        "growth": 0.40,   # past total return in EUR
        "cost": 0.30,     # TER — the only column that is a fact about the future
        "risk": 0.20,     # volatility and worst drawdown
        "size": 0.10,     # fund survivability and spread
    },
    "gates": {
        # A TER is the whole point of the board. Unknown is not "assume
        # cheap" and not "silently drop" — it is a visible gate with a
        # reason, which is the nudge to put the KID figure into the
        # override file.
        "require_ter": True,
        "max_ter": 0.0075,           # 0.75% — above this it is active management
        "min_history_years": 3.0,    # under 3y a CAGR is a momentum reading
        "min_total_assets": 50_000_000,   # only fires when the figure is known
        "exclude_leveraged": True,
    },
    "ramps": {
        # [poor, good]; good < poor means lower is better.
        "cagr": [0.02, 0.15],
        "ter": [0.0060, 0.0005],
        "sharpe": [0.20, 1.20],      # CAGR / volatility, no risk-free rate
        "max_drawdown": [0.55, 0.15],
        "total_assets": [50_000_000, 1_000_000_000],
    },
    "growth_mix": {"cagr_5y": 0.60, "cagr_3y": 0.40},
    "risk_mix": {"sharpe": 0.60, "max_drawdown": 0.40},
    "max_age_hours": 20,
    # Bars past which a curated TER and Yahoo's reported one are treated as
    # a disagreement worth flagging (5 bp absolute).
    "ter_disagreement_bp": 5.0,
}

# Bumped whenever `fetch_one()` starts storing a field it did not store
# before. A cached row is only "fresh" if it was written by code at least
# this revision — see `_fresh_symbols()`. Age alone cannot answer "is this
# row current" after a column is added: the row is recent, valid, and
# has a hole in it, and the hole looks like missing data rather than a
# stale cache.
FETCH_REV = 1

# Name fragments that mean "this fund's multi-year CAGR does not mean what
# the column header says". A 3x daily product compounds volatility drag,
# so a five-year figure is an artefact of the path, not of the index.
_LEVERAGE_MARKERS = (
    "2x", "3x", "-1x", "leveraged", "levered", "daily short", "inverse",
    "bear", "ultrashort", "double long", "triple",
)

# How much history the chart is asked for. Six years covers a five-year
# CAGR with a margin for the "nearest observation" tolerance, and six
# rolling distribution years for the worst-cut figure.
HISTORY_YEARS = 6.0
REQUEST_PAUSE = 0.4


# --------------------------------------------------------------------------
# Dividend profile — "high yield, low TER"
# --------------------------------------------------------------------------
# A second question asked of the SAME `screener_etfs` rows, exactly as the
# income board is a second question asked of `screener_fundamentals`.
# Nothing is refetched and nothing is duplicated, so the two ETF boards
# can never disagree about a fund's TER or its yield — they read one row.
#
# Why yield is only 35% when "high yield" is the request
# ------------------------------------------------------
# The same reason it is 35% on the share income board, and it bites harder
# here. An index that selects on yield mechanically buys whatever has just
# fallen, so the highest-yielding dividend ETF on any given day is often
# the one holding the companies about to cut. The difference is that an
# ETF has no payout ratio and no balance sheet to interrogate — you cannot
# ask a fund whether it can afford its distribution. The only evidence
# that a distribution is durable is whether it has ever collapsed, which
# is what `div_worst_cut` measures and what the stability pillar spends
# most of its weight on.
#
# Why cost is 25% on a board whose headline is yield
# --------------------------------------------------
# Because a TER is charged out of the same cash the distribution comes
# from. At a 3.5% yield, a 0.45% TER is not "half a percent" — it is 13%
# of the income, taken every year, guaranteed, before the fund has picked
# a single stock. The `net_yield` column makes that subtraction visible;
# the pillars stay separate so a high net yield can still be read as
# either "it pays a lot" or "it costs little", which are different
# investments.

DIVIDEND_DEFAULTS = {
    "weights": {
        "yield": 0.35,      # what it actually paid over the last 12 months
        "cost": 0.25,       # TER — charged out of that same income
        "growth": 0.20,     # is the distribution rising or shrinking
        "stability": 0.20,  # has it ever been cut, how deep did the fund fall
    },
    "gates": {
        # An accumulating share class pays nothing. It is not a bad income
        # fund, it is not an income fund — and it must be told apart from a
        # fund whose distribution data simply failed to fetch, which is why
        # `dividend_metrics()` returns 0.0 for the first and None for the
        # second.
        "require_distributing": True,
        "min_yield": 0.020,          # under 2% this is a growth fund with a coupon
        # A double-digit yield on a diversified fund is a special
        # distribution, a stale price or a return of capital — never an
        # opportunity that survived everyone else noticing it. Gated, not
        # flagged, because on a board sorted by yield it would otherwise
        # own the top permanently.
        "max_yield": 0.120,
        "require_ter": True,
        "max_ter": 0.0075,
        "min_history_years": 3.0,
        # Two full distribution years, or there is no year-on-year change
        # to judge and the growth pillar would be scoring noise.
        "min_div_years": 2.0,
        "min_total_assets": 50_000_000,
        "exclude_leveraged": True,
        # See check_dividend_gates(): a US mutual fund's payout conflates
        # income with the realised capital gains it is required to
        # distribute, so its "yield" is not one.
        "exclude_mutual_funds": True,
    },
    "ramps": {
        "div_yield_ttm": [0.020, 0.060],
        "ter": [0.0060, 0.0010],
        "div_growth": [-0.03, 0.08],
        # Inverted: 0 means it has never cut across the years on record,
        # -35% means it once lost a third of its income in a year.
        "div_worst_cut": [-0.35, 0.0],
        "max_drawdown": [0.55, 0.20],
        "cagr_5y": [0.0, 0.10],
    },
    # Distribution growth leads; the price series is the check on it. A
    # fund can raise its distribution while its NAV shrinks — that is
    # capital being handed back and called income, and the price leg is
    # the only thing on this board that notices.
    "growth_mix": {"dividend": 0.65, "price": 0.35},
    "stability_mix": {"worst_cut": 0.60, "max_drawdown": 0.40},
    "max_age_hours": 20,
    "ter_disagreement_bp": 5.0,
    # Yahoo's own yield field, where present, versus the one computed from
    # distributions. Past this gap the row says so rather than picking.
    "yield_disagreement_pct": 0.25,
}

PROFILES = {"growth": DEFAULTS, "dividend": DIVIDEND_DEFAULTS}

# `screener.json` section per profile.
_CONFIG_SECTION = {"growth": "etf", "dividend": "etf_dividend"}


def load_config(profile: str = "growth") -> dict:
    """`screener.json`'s section for this profile, merged over its defaults.

    One file tunes the whole screener and each board reads its own
    section — the value board the top level, income `"income"`, the ETF
    growth board `"etf"`, the ETF dividend board `"etf_dividend"`. Nothing
    leaks between them: `max_ter` 0.75% is reasonable on a growth board
    and a different judgement on an income one, and neither should inherit
    the other's.
    """
    base = PROFILES.get(profile, DEFAULTS)
    section = _CONFIG_SECTION.get(profile, "etf")
    cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    if not CONFIG_FILE.exists():
        return cfg
    try:
        user = (json.loads(CONFIG_FILE.read_text()) or {}).get(section) or {}
    except Exception:
        return cfg
    if not isinstance(user, dict):
        return cfg
    for key, val in user.items():
        if isinstance(val, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(val)
        else:
            cfg[key] = val
    return cfg


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------

_META_FIELDS = ("name", "ter", "dist", "pea", "region")


def load_universe(conn=None) -> dict[str, dict]:
    """{symbol: curated metadata} — shipped list, override file, own holdings.

    Merge order is shipped → override → holdings, and the override merges
    FIELD BY FIELD rather than replacing the entry: correcting one TER
    should not require restating the fund's name, distribution policy and
    PEA status, because a half-restated entry is how a "dist" fund quietly
    becomes an "acc" one on the page.
    """
    uni: dict[str, dict] = {}

    def _merge(entry: dict) -> None:
        sym = str(entry.get("symbol") or "").strip().upper()
        if not sym:
            return
        cur = uni.setdefault(sym, {"symbol": sym})
        for f in _META_FIELDS:
            if f in entry and entry[f] is not None:
                cur[f] = entry[f]
        cur.setdefault("ter", None)

    for e in DEFAULT_ETF_UNIVERSE:
        _merge(e)

    data: dict = {}
    if UNIVERSE_FILE.exists():
        try:
            data = json.loads(UNIVERSE_FILE.read_text()) or {}
        except Exception:
            data = {}
        for e in data.get("etfs", []):
            if isinstance(e, dict):
                _merge(e)
    else:
        try:
            UNIVERSE_FILE.write_text(json.dumps(
                {"etfs": [], "exclude": [],
                 "_help": "Field-by-field overrides for the shipped ETF list. "
                          "Example: {\"symbol\": \"IWDA.AS\", \"ter\": 0.002}"},
                indent=2))
        except OSError:
            pass

    # Own ETF holdings, so a fund the reader actually owns is always on
    # the board next to the candidates — the share board does the same
    # with its equities. No curated fields: it will say its TER is
    # unknown until someone supplies one, which is the honest state.
    if conn is not None:
        for sym, meta in held_symbols(conn).items():
            if meta["quote_type"] in ("ETF", "MUTUALFUND"):
                _merge({"symbol": sym, "name": meta["name"]})

    for sym in {str(s).strip().upper() for s in data.get("exclude", [])}:
        uni.pop(sym, None)
    return uni


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

_NUMERIC_COLS = [
    "price", "total_assets", "yahoo_ter", "dividend_yield",
    "cagr_1y", "cagr_3y", "cagr_5y", "volatility_1y", "max_drawdown",
    "history_years", "week52_high", "week52_low",
    "div_ttm", "div_prior", "div_yield_ttm", "div_growth", "div_worst_cut",
    "div_events_12m", "div_events_prior", "div_years",
]
_TEXT_COLS = [
    "name", "category", "family", "currency", "exchange", "quote_type",
    "history_start", "history_end", "div_last_date",
]
_ALL_COLS = _TEXT_COLS + _NUMERIC_COLS


def upsert(conn, symbol: str, fields: dict, error: str | None = None) -> None:
    """Write one row; on error keep the old values and stamp the error only."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if error is not None and not fields:
        conn.execute(
            "INSERT INTO screener_etfs (symbol, last_error, fetched_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(symbol) DO UPDATE SET last_error = excluded.last_error",
            (symbol, error, now),
        )
        return
    cols = ["symbol"] + _ALL_COLS + ["fetched_at", "last_error", "fetch_rev"]
    vals = [symbol] + [fields.get(c) for c in _ALL_COLS] + [now, error, FETCH_REV]
    conn.execute(
        f"INSERT INTO screener_etfs ({', '.join(cols)}) "
        f"VALUES ({', '.join('?' for _ in cols)}) "
        f"ON CONFLICT(symbol) DO UPDATE SET "
        f"{', '.join(f'{c} = excluded.{c}' for c in cols[1:])}",
        vals,
    )


# --------------------------------------------------------------------------
# Series maths — stdlib only. The fetchers hand this layer plain
# [(date, close)] lists, so the test suite needs no network.
# --------------------------------------------------------------------------

def _num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if (math.isnan(f) or math.isinf(f)) else f


def _d(s) -> date | None:
    if isinstance(s, date):
        return s
    try:
        return date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def to_eur(series, fx_series, pence: bool = False):
    """Convert [(date, close)] into EUR using [(date, units_per_eur)].

    `fx_series` is Yahoo's `EUR{CCY}=X`, i.e. how many units of the quote
    currency one euro buys, so the conversion is a division. Rates are
    matched with the most recent rate at or before each price date rather
    than requiring equal dates — weekly equity bars and daily FX bars do
    not land on the same calendar, and dropping the mismatches would
    silently shorten the history and with it the 5-year CAGR.

    A price date earlier than the first known rate is dropped: inventing a
    rate by extrapolating backwards would put a made-up number into the
    one column the board ranks on.
    """
    div = 100.0 if pence else 1.0
    if not fx_series:
        return [(d, c / div) for d, c in series]
    fx = sorted((_d(d), _num(r)) for d, r in fx_series)
    fx = [(d, r) for d, r in fx if d and r and r > 0]
    if not fx:
        return [(d, c / div) for d, c in series]

    out, i, rate = [], 0, None
    for d0, close in sorted(series):
        dd = _d(d0)
        if dd is None or close is None:
            continue
        while i < len(fx) and fx[i][0] <= dd:
            rate = fx[i][1]
            i += 1
        if rate is None:
            continue
        out.append((dd, (close / div) / rate))
    return out


def cagr(series, years: float, tolerance_days: int = 60) -> float | None:
    """Compound annual growth over the last `years` of the series.

    The start point is the observation nearest to `end - years`, accepted
    only if it is within `tolerance_days`. Anchoring on "nearest" rather
    than "first available" is what stops a fund with four years of history
    reporting a five-year CAGR that is really a four-year one — which
    would flatter exactly the young, concentrated funds this board is most
    at risk of over-rewarding.
    """
    pts = [(_d(d), _num(c)) for d, c in series]
    pts = sorted((d, c) for d, c in pts if d and c and c > 0)
    if len(pts) < 2:
        return None
    end_d, end_v = pts[-1]
    target = date.fromordinal(max(1, end_d.toordinal() - int(round(years * 365.25))))
    best = min(pts[:-1], key=lambda p: abs((p[0] - target).days))
    if abs((best[0] - target).days) > tolerance_days:
        return None
    span = (end_d - best[0]).days / 365.25
    if span <= 0.05 or best[1] <= 0:
        return None
    return (end_v / best[1]) ** (1.0 / span) - 1.0


def volatility(series, weeks: int = 52) -> float | None:
    """Annualised standard deviation of the last `weeks` weekly log returns."""
    pts = sorted((_d(d), _num(c)) for d, c in series)
    vals = [c for d, c in pts if d and c and c > 0][-(weeks + 1):]
    if len(vals) < 12:
        return None
    rets = [math.log(vals[i] / vals[i - 1]) for i in range(1, len(vals))]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(52.0)


def max_drawdown(series) -> float | None:
    """Worst peak-to-trough fall over the whole series, as a fraction.

    Measured on weekly closes, so it is a floor on the true intra-week
    drawdown, not the exact figure. Understating it slightly is the safe
    direction for a number used to penalise risk — it can only make a
    fund look worse than the column claims, never better.
    """
    pts = sorted((_d(d), _num(c)) for d, c in series)
    vals = [c for d, c in pts if d and c and c > 0]
    if len(vals) < 3:
        return None
    peak, worst = vals[0], 0.0
    for v in vals:
        peak = max(peak, v)
        worst = max(worst, (peak - v) / peak)
    return worst


def series_metrics(series) -> dict:
    """Every derived figure for one EUR total-return series."""
    pts = sorted((_d(d), _num(c)) for d, c in series)
    pts = [(d, c) for d, c in pts if d and c and c > 0]
    if len(pts) < 2:
        return {}
    span = (pts[-1][0] - pts[0][0]).days / 365.25
    closes = [c for _, c in pts]
    return {
        "cagr_1y": cagr(pts, 1.0, tolerance_days=30),
        "cagr_3y": cagr(pts, 3.0),
        "cagr_5y": cagr(pts, 5.0),
        "volatility_1y": volatility(pts),
        "max_drawdown": max_drawdown(pts),
        "history_years": round(span, 2),
        "history_start": pts[0][0].isoformat(),
        "history_end": pts[-1][0].isoformat(),
        "price": closes[-1],
        # From weekly closes, so these are the highest and lowest weekly
        # CLOSE of the last year in EUR, not the intraday extremes Yahoo
        # would report in the listing currency. Stored for context only —
        # nothing on this board ranks on them.
        "week52_high": max(closes[-53:]),
        "week52_low": min(closes[-53:]),
    }


# --------------------------------------------------------------------------
# Distribution maths — the dividend board's inputs
# --------------------------------------------------------------------------
# Yahoo's own `yield` / `dividendYield` field is filled in for US mutual
# funds and empty for precisely the European UCITS listings this board is
# made of — the SAME failure the module docstring records for
# `threeYearAverageReturn`. A dividend board ranked on it would be blank
# for five names in six.
#
# So the yield is computed from the distributions actually paid, exactly
# as the growth column is computed from the price series actually
# observed. Yahoo's figure is still stored, and `_dividend_flags()`
# surfaces a large disagreement rather than either one silently winning.
#
# No FX conversion happens here, and that is not an oversight: a yield is
# a RATIO of two amounts in the same listing currency, so it is
# dimensionless and identical in every currency. Converting both legs
# would multiply and divide by the same rate. Distribution *growth* is a
# ratio too, and measuring it in the fund's own currency is the more
# honest reading anyway — it is the fund raising its payout, not the euro
# falling.

def _bucket_sums(divs, today: date, years: int = 6) -> list[float]:
    """Distributions summed into rolling 365-day buckets, newest first.

    Rolling windows anchored on today rather than calendar years, because
    a calendar-year bucket splits a December-ex/January-pay distribution
    across two years and invents a cut that never happened.
    """
    out = []
    for i in range(years):
        hi = today.toordinal() - 365 * i
        lo = hi - 365
        out.append(sum(a for d, a in divs if lo < d.toordinal() <= hi))
    return out


def dividend_metrics(dividends, price, today: date | None = None) -> dict:
    """Trailing distribution figures for one fund.

    `dividends` is [(YYYY-MM-DD, amount)] in the LISTING currency, and
    `price` must be in that same currency — see the note above. Callers
    must therefore pass the pre-conversion price, not the EUR one that
    `series_metrics()` produces.
    """
    today = today or date.today()
    divs = sorted((_d(d), _num(a)) for d, a in (dividends or []))
    # Yahoo returns an ANNOUNCED upcoming ex-date alongside the paid
    # history. A dividend that has not been paid yet is not trailing
    # income, and counting it would inflate both the yield and the
    # payment frequency of exactly the funds that announce earliest.
    # Dropped here, once, so every figure below shares one definition of
    # "has been paid".
    divs = [(d, a) for d, a in divs if d and a and a > 0 and d <= today]
    px = _num(price)

    if not divs:
        # Zero distributions is a FACT, not missing data — it is what an
        # accumulating share class looks like from the outside, and the
        # gate below relies on being able to tell the two apart. An
        # accumulating fund reports 0.0; a fund we failed to fetch
        # reports None, and only the second one is a data problem.
        return {"div_ttm": 0.0, "div_yield_ttm": 0.0, "div_events_12m": 0,
                "div_years": 0.0}

    buckets = _bucket_sums(divs, today)
    ttm, prior = buckets[0], buckets[1]
    span_years = (today - divs[0][0]).days / 365.25

    growth = None
    if prior > 0 and ttm > 0:
        growth = ttm / prior - 1.0

    # Worst year-on-year fall over the complete buckets we have. This is
    # the ETF analogue of the share board's payout ratio: an index fund
    # has no payout ratio to interrogate, so the only evidence that a
    # distribution is durable is whether it has ever collapsed. Buckets
    # before the fund's first distribution are not "a cut to zero", so
    # only pairs where BOTH years are inside the fund's own history
    # count.
    complete = int(min(len(buckets) - 1, max(0, span_years - 1)))
    worst = None
    for i in range(complete):
        newer, older = buckets[i], buckets[i + 1]
        if older > 0:
            change = newer / older - 1.0
            worst = change if worst is None else min(worst, change)

    return {
        "div_ttm": round(ttm, 6),
        "div_prior": round(prior, 6),
        "div_yield_ttm": round(ttm / px, 6) if (px and px > 0) else None,
        "div_growth": round(growth, 4) if growth is not None else None,
        "div_worst_cut": round(worst, 4) if worst is not None else None,
        # Payment frequency, used to spot a fund that changed schedule —
        # a switch from annual to quarterly triples the event count and
        # can make one year look like a huge rise for no economic reason.
        # Counted over the SAME windows the sums use.
        "div_events_12m": sum(1 for d, _ in divs
                              if today.toordinal() - 365 < d.toordinal()
                              <= today.toordinal()),
        "div_events_prior": sum(1 for d, _ in divs
                                if today.toordinal() - 730 < d.toordinal()
                                <= today.toordinal() - 365),
        "div_years": round(span_years, 2),
        "div_last_date": divs[-1][0].isoformat(),
    }


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def _yahoo_ter(info: dict) -> float | None:
    """Yahoo's expense ratio as a FRACTION, whichever field carries it.

    The same unit trap as `screener.normalise()`, in a place where it is
    worse: `annualReportExpenseRatio` is a fraction (0.0020) and
    `netExpenseRatio` is a percent (0.20), and both mean 0.20% a year.
    Read either as the other and a cheap fund becomes a hundred times
    dearer, or an expensive one becomes free — on the pillar that carries
    30% of the score. Anything above 5% is read as a percent; no UCITS
    tracker charges 5%, and an active fund charging 20 basis points is not
    a thing either, so the split is unambiguous in both directions.
    """
    for key in ("annualReportExpenseRatio", "netExpenseRatio", "netExpRatio",
                "expenseRatio", "grossExpenseRatio", "grossExpRatio"):
        v = _num(info.get(key))
        if v is None or v <= 0:
            continue
        return v / 100.0 if v > 0.05 else v
    return None


def normalise_info(info: dict) -> dict:
    """Yahoo's flattened summary → this module's column names and units."""
    price = (_num(info.get("regularMarketPrice"))
             or _num(info.get("currentPrice"))
             or _num(info.get("previousClose")))
    dy = _num(info.get("yield"))
    if dy is None:
        dy = _num(info.get("dividendYield"))
    if dy is not None and dy > 1.0:      # percent form
        dy = dy / 100.0
    if dy is not None and (dy <= 0 or dy > 0.30):
        dy = None
    return {
        "name": info.get("longName") or info.get("shortName"),
        "category": info.get("category"),
        "family": info.get("fundFamily"),
        "currency": info.get("currency"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "quote_type": info.get("quoteType"),
        "price": price,
        "total_assets": _num(info.get("totalAssets")),
        "yahoo_ter": _yahoo_ter(info),
        "dividend_yield": dy,
    }


def _default_info_fetcher(symbol: str) -> dict:
    from . import yahoo
    return yahoo.fundamentals(symbol, yahoo.FUND_MODULES)


def _default_history_fetcher(symbol: str) -> dict:
    """{closes, dividends, currency, quote_type} — one chart call.

    Adjusted closes and the discrete distributions come from the same
    reply, so the growth column (which needs them folded in) and the
    dividend board (which needs them as events) cannot disagree about
    what was paid.
    """
    from . import yahoo
    return yahoo.history(symbol, years=HISTORY_YEARS)


def fetch_one(symbol: str, info_fetcher, history_fetcher, fx_cache: dict) -> dict:
    """All stored fields for one ETF: Yahoo info + EUR series metrics +
    trailing distributions."""
    info = info_fetcher(symbol) or {}
    fields = normalise_info(info)

    hist = history_fetcher(symbol) or {}
    series = hist.get("closes") or []
    if not series:
        raise ValueError("no price history in Yahoo response")
    # The chart reply knows the listing currency and the instrument type
    # even when the summary is thin; the summary wins where it answers.
    fields["currency"] = fields.get("currency") or hist.get("currency")
    fields["quote_type"] = fields.get("quote_type") or hist.get("quote_type")

    # Captured BEFORE the EUR series overwrites `price` below. The yield
    # is distributions over price and both must be in the same currency;
    # dividing a listing-currency distribution by a EUR price is a silent
    # FX error on the one number the dividend board ranks on.
    listing_price = _num(fields.get("price")) or series[-1][1]

    ccy = (fields.get("currency") or "EUR").upper()
    pence = ccy == "GBP" and (fields.get("exchange") or "").upper().startswith("LSE")
    if hist.get("currency") == "GBp" or info.get("currency") == "GBp":
        pence, ccy = True, "GBP"
    fx = _fx_series(ccy, history_fetcher, fx_cache)
    eur = to_eur(series, fx, pence=pence)
    if len(eur) < 12:
        raise ValueError(f"history too short after FX alignment ({len(eur)} points)")

    metrics = series_metrics(eur)
    # Yahoo's own price is in the listing currency; the EUR series has just
    # produced a consistent one. Prefer the EUR figure so the price, the
    # 52-week band and the CAGR on the page are all the same currency —
    # a price in USD beside a return in EUR is how a reader concludes the
    # numbers are wrong.
    fields.update(metrics)
    # If the FX fetch failed, the series is still in the listing currency
    # and every figure derived from it is a return in THAT currency. Say
    # so in the column rather than stamping "EUR" on it: an unconverted
    # USD return sitting on a EUR board is the one error this whole
    # conversion step exists to prevent, and it must not be invisible.
    fields["currency"] = "EUR" if (fx or ccy == "EUR") else ccy

    # Distributions come with the same reply. A fund with no dividend
    # history is a perfectly good growth-board row: an empty list is
    # "accumulating", and only a missing list is "unknown".
    if "dividends" in hist:
        fields.update(dividend_metrics(hist.get("dividends") or [], listing_price))
    return fields


def _fx_series(ccy: str, history_fetcher, cache: dict):
    """Weekly `EUR{ccy}=X` closes, fetched at most once per run."""
    ccy = (ccy or "EUR").upper()
    if ccy == "EUR":
        return []
    if ccy in cache:
        return cache[ccy]
    try:
        cache[ccy] = (history_fetcher(f"EUR{ccy}=X") or {}).get("closes") or []
    except Exception:
        cache[ccy] = []
    return cache[ccy]


def refresh(conn, symbols=None, info_fetcher=None, history_fetcher=None,
            limit=None, force=False, sleep_s=0.0, log=None, stop=None) -> dict:
    """Fetch and store every ETF. Returns {ok, failed, skipped, attempted}."""
    cfg = load_config()
    info_fetcher = info_fetcher or _default_info_fetcher
    history_fetcher = history_fetcher or _default_history_fetcher

    uni = load_universe(conn)
    syms = list(symbols) if symbols else list(uni)

    if not force:
        fresh = _fresh_symbols(conn, cfg["max_age_hours"])
        kept = [s for s in syms if s not in fresh]
        skipped = len(syms) - len(kept)
        syms = kept
    else:
        skipped = 0
    if limit:
        syms = syms[:limit]

    fx_cache: dict = {}
    ok = failed = 0
    for sym in syms:
        if stop and stop():
            break
        try:
            fields = fetch_one(sym, info_fetcher, history_fetcher, fx_cache)
            upsert(conn, sym, fields, error=None)
            ok += 1
        except Exception as e:
            failed += 1
            upsert(conn, sym, {}, error=f"{type(e).__name__}: {e}"[:300])
            if log:
                log(f"{sym}: {type(e).__name__}: {e}")
            if "429" in str(e):
                time.sleep(15)
        conn.commit()
        if sleep_s:
            time.sleep(sleep_s)
    return {"ok": ok, "failed": failed, "skipped": skipped, "attempted": len(syms)}


def _fresh_symbols(conn, max_age_hours: float) -> set[str]:
    """Symbols a refresh may skip: recent, error-free AND written by code
    of the current `FETCH_REV`."""
    rows = conn.execute(
        "SELECT symbol FROM screener_etfs "
        "WHERE last_error IS NULL AND fetched_at IS NOT NULL "
        "AND fetched_at > datetime('now', ?) "
        "AND COALESCE(fetch_rev, 0) >= ?",
        (f"-{float(max_age_hours)} hours", FETCH_REV),
    ).fetchall()
    return {r[0] for r in rows}


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
# `_ramp` and `_blend` are imported from screener.py rather than copied:
# the boards must renormalise missing data the same way, and two copies
# of that rule would drift the first time one of them was tuned.

def _pct(v, digits=1) -> str:
    return i18n.group(f"{v * 100:.{digits}f}", i18n.active())


def _n(v, digits=1) -> str:
    return i18n.group(f"{v:,.{digits}f}", i18n.active())


def effective_ter(row) -> tuple[float | None, str | None]:
    """(TER, source) — the curated figure first, Yahoo's only as a fallback.

    Curated wins because it is the KID number for the exact share class,
    whereas Yahoo's is frequently the US-domiciled sibling's or simply
    absent for European listings. Yahoo's is still stored, because the two
    disagreeing is a useful signal that the entry points at the wrong
    share class — `_flags()` surfaces that rather than this function
    quietly picking a winner.
    """
    ter = _num(row.get("ter"))
    if ter is not None and ter > 0:
        return ter, "curated"
    yt = _num(row.get("yahoo_ter"))
    if yt is not None and yt > 0:
        return yt, "yahoo"
    return None, None


def check_gates(row, cfg) -> list[str]:
    g = cfg["gates"]
    fails: list[str] = []

    qt = (row.get("quote_type") or "").upper()
    if qt and qt not in ("ETF", "MUTUALFUND"):
        fails.append(_f("not a fund ({type})", type=qt.lower()))

    name = f"{row.get('name') or ''} {row.get('category') or ''}".lower()
    if g.get("exclude_leveraged") and any(m in name for m in _LEVERAGE_MARKERS):
        fails.append(_t("leveraged or inverse — a multi-year CAGR is meaningless"))

    ter, _src = effective_ter(row)
    if ter is None:
        if g.get("require_ter"):
            fails.append(_t("no TER known — add it to screener_etf_universe.json"))
    elif g.get("max_ter") and ter > g["max_ter"]:
        fails.append(_f("too expensive ({pct}% a year)", pct=_pct(ter, 2)))

    hy = _num(row.get("history_years"))
    floor = g.get("min_history_years")
    if floor:
        if hy is None:
            fails.append(_t("no price history"))
        elif hy < floor:
            fails.append(_f("only {years} years of history", years=_n(hy, 1)))

    # Unknown size is NOT small. Yahoo leaves `totalAssets` empty for
    # plenty of European listings, and gating on the gap would empty the
    # board of exactly the funds it exists to surface.
    ta = _num(row.get("total_assets"))
    if g.get("min_total_assets") and ta is not None and ta < g["min_total_assets"]:
        fails.append(_f("fund too small ({m}m)", m=_n(ta / 1e6, 0)))

    return fails


def _finish(r: dict, pillars: dict, sub_cov: dict, cfg: dict) -> None:
    composite, _ = _blend(pillars, cfg["weights"])
    w_total = sum(w for w in cfg["weights"].values() if w > 0)
    coverage = (sum(cfg["weights"].get(k, 0) * v for k, v in sub_cov.items())
                / w_total) if w_total > 0 else 0.0
    r["pillars"] = {k: (round(v, 1) if v is not None else None)
                    for k, v in pillars.items()}
    r["score"] = round(composite, 1) if composite is not None else None
    r["coverage"] = round(coverage, 2)
    r["pillar_coverage"] = {k: round(v, 2) for k, v in sub_cov.items()}
    # `pea` is curated, never inferred. Yahoo cannot answer it: PEA
    # eligibility is a French rule about the fund's holdings and wrapper,
    # and a synthetic MSCI World qualifies where a physical one does not.
    r["pea_eligible"] = bool(r.get("pea")) if r.get("pea") is not None else None


def score_row(row, cfg=None) -> dict:
    """Score one ETF on growth · cost · risk · size."""
    cfg = cfg or load_config()
    r = dict(row)
    ramps = cfg["ramps"]

    ter, ter_src = effective_ter(r)
    r["ter"] = ter
    r["ter_source"] = ter_src

    c3, c5 = _num(r.get("cagr_3y")), _num(r.get("cagr_5y"))
    vol = _num(r.get("volatility_1y"))
    mdd = _num(r.get("max_drawdown"))
    ta = _num(r.get("total_assets"))

    growth, growth_cov = _blend(
        {"cagr_5y": _ramp(c5, *ramps["cagr"]),
         "cagr_3y": _ramp(c3, *ramps["cagr"])},
        cfg["growth_mix"],
    )
    cost = _ramp(ter, *ramps["ter"])

    # Return per unit of volatility, with no risk-free rate subtracted —
    # so it is not a Sharpe ratio and is not labelled one. Adding a
    # risk-free rate would mean picking a currency and a maturity for it,
    # and the ranking is unchanged by a constant subtracted from every row.
    sharpe = (c3 / vol) if (c3 is not None and vol and vol > 0) else None
    risk, risk_cov = _blend(
        {"sharpe": _ramp(sharpe, *ramps["sharpe"]),
         "max_drawdown": _ramp(mdd, *ramps["max_drawdown"])},
        cfg["risk_mix"],
    )
    size = _ramp(ta, *ramps["total_assets"])

    _finish(r, {"growth": growth, "cost": cost, "risk": risk, "size": size},
            {"growth": growth_cov, "cost": 1.0 if cost is not None else 0.0,
             "risk": risk_cov, "size": 1.0 if size is not None else 0.0}, cfg)
    r["return_per_vol"] = round(sharpe, 2) if sharpe is not None else None

    gates = check_gates(r, cfg)
    r["gate_failed"] = gates or None
    if gates:
        r["score"] = None
    r["flags"] = _flags(r, cfg)
    return r


def _flags(r, cfg) -> list[str]:
    out: list[str] = []

    ter = _num(r.get("ter"))
    yt = _num(r.get("yahoo_ter"))
    bp = cfg.get("ter_disagreement_bp", 5.0)
    if (r.get("ter_source") == "curated" and ter is not None and yt
            and abs(ter - yt) * 10_000 > bp):
        out.append(_f("our TER {ours}% vs Yahoo's {theirs}% — likely a different "
                      "share class; check the ISIN", ours=_pct(ter, 2), theirs=_pct(yt, 2)))
    if r.get("ter_source") == "yahoo":
        out.append(_t("TER is Yahoo's, not the KID's — verify before ranking on it"))

    ccy = (r.get("currency") or "EUR").upper()
    if ccy != "EUR":
        out.append(_f("returns are in {ccy}, not EUR — the FX series could not be "
                      "fetched, so this row is not comparable with the rest", ccy=ccy))

    if _num(r.get("cagr_5y")) is None and _num(r.get("cagr_3y")) is not None:
        out.append(_t("under 5 years of history — growth is the 3-year figure alone"))

    if (r.get("dist") or "").lower() == "dist":
        out.append(_t("distributing — outside a tax wrapper each distribution is "
                      "taxed in the year it is paid, so it compounds slower"))

    mdd = _num(r.get("max_drawdown"))
    if mdd is not None and mdd > 0.45:
        out.append(_f("fell {pct}% peak to trough within this window", pct=_pct(mdd, 0)))

    vol = _num(r.get("volatility_1y"))
    if vol is not None and vol > 0.28:
        out.append(_f("volatile ({pct}% a year)", pct=_pct(vol, 0)))

    if (r.get("region") or "") in ("Theme", "Sector"):
        out.append(_t("single theme or sector — a concentrated bet, not a core holding"))

    ta = _num(r.get("total_assets"))
    if ta is None:
        out.append(_t("fund size unknown — Yahoo reports none for this listing"))

    if r.get("coverage", 1.0) < 0.6:
        out.append(_t("thin data — score built on few figures"))
    return out


# --------------------------------------------------------------------------
# Dividend profile — gates, scoring, flags
# --------------------------------------------------------------------------

def is_accumulating(row) -> bool | None:
    """True / False / None — pays nothing, pays something, or we do not know.

    Three states, not two, and the distinction is the whole reason the
    dividend board can be trusted. `div_ttm == 0.0` is a MEASUREMENT: the
    fetch succeeded and found no distributions, which is what an
    accumulating share class looks like from outside. `div_ttm is None`
    means the fetch failed and we know nothing. Collapsing those two into
    "no dividend" would quietly drop every fund whose dividend call
    happened to time out, and the board would look shorter rather than
    broken.

    The curated `dist` field is used only as a cross-check, never as the
    answer: it is hand-maintained and therefore the thing most likely to
    be stale, and `_dividend_flags()` reports a disagreement instead of
    letting either side win silently.
    """
    ttm = _num(row.get("div_ttm"))
    events = row.get("div_events_12m")
    if ttm is None and events is None:
        return None
    return not ((ttm or 0) > 0 or (events or 0) > 0)


def net_yield(row) -> float | None:
    """Trailing yield minus the TER — the income that reaches you.

    Displayed, never ranked on. Ranking on the difference would hide which
    half produced it, and "pays 5% and costs 0.6%" is a different fund
    from "pays 4.6% and costs 0.05%" even though the subtraction agrees.
    """
    dy = _num(row.get("div_yield_ttm"))
    ter, _src = effective_ter(row)
    if dy is None:
        return None
    return dy - (ter or 0.0)


def check_dividend_gates(row, cfg) -> list[str]:
    """Reasons this fund is not an income candidate. Empty list = it is."""
    g = cfg["gates"]
    fails: list[str] = []

    qt = (row.get("quote_type") or "").upper()
    if qt and qt not in ("ETF", "MUTUALFUND"):
        fails.append(_f("not a fund ({type})", type=qt.lower()))

    # US mutual funds are allowed on the growth board — a total-return
    # CAGR means the same thing for them as for an ETF. They are NOT
    # allowed here, because their annual distribution is mostly REALISED
    # CAPITAL GAINS, which US funds are obliged to pay out and European
    # ETFs are not. Treating that as income is not a rounding error: it
    # puts a target-date fund at the top of the board with a "6% yield",
    # a 46% "increase" and a 75% "cut" in adjacent years — three figures
    # that are all the same artefact. The tell is in the data (one or
    # two lumpy payments a year), but the type is the honest thing to
    # gate on.
    if qt == "MUTUALFUND" and g.get("exclude_mutual_funds", True):
        fails.append(_t("US mutual fund — its annual distribution is mostly "
                        "realised capital gains, not income"))

    name = f"{row.get('name') or ''} {row.get('category') or ''}".lower()
    if g.get("exclude_leveraged") and any(m in name for m in _LEVERAGE_MARKERS):
        fails.append(_t("leveraged or inverse — not an income holding"))

    acc = is_accumulating(row)
    if acc is None:
        fails.append(_t("no distribution data — the fetch has not run yet"))
    elif acc and g.get("require_distributing"):
        fails.append(_t("accumulating — reinvests internally and pays no income"))

    dy = _num(row.get("div_yield_ttm"))
    if dy is not None and acc is False:
        lo, hi = g.get("min_yield"), g.get("max_yield")
        if lo and dy < lo:
            fails.append(_f("yield too low for an income holding ({pct}%)",
                            pct=_pct(dy, 2)))
        elif hi and dy > hi:
            fails.append(_f("implausible yield ({pct}%) — a special distribution, "
                            "a return of capital, or a stale price", pct=_pct(dy, 1)))

    ter, _src = effective_ter(row)
    if ter is None:
        if g.get("require_ter"):
            fails.append(_t("no TER known — add it to screener_etf_universe.json"))
    elif g.get("max_ter") and ter > g["max_ter"]:
        fails.append(_f("too expensive ({pct}% a year)", pct=_pct(ter, 2)))

    hy = _num(row.get("history_years"))
    if g.get("min_history_years"):
        if hy is None:
            fails.append(_t("no price history"))
        elif hy < g["min_history_years"]:
            fails.append(_f("only {years} years of price history", years=_n(hy, 1)))

    dvy = _num(row.get("div_years"))
    floor = g.get("min_div_years")
    if floor and acc is False and dvy is not None and dvy < floor:
        fails.append(_f("only {years} years of distributions — too short to tell "
                        "a rising payout from a lucky one", years=_n(dvy, 1)))

    ta = _num(row.get("total_assets"))
    if g.get("min_total_assets") and ta is not None and ta < g["min_total_assets"]:
        fails.append(_f("fund too small ({m}m)", m=_n(ta / 1e6, 0)))

    return fails


def score_dividend_row(row, cfg=None) -> dict:
    """Score one ETF on yield · cost · growth · stability."""
    cfg = cfg or load_config("dividend")
    r = dict(row)
    ramps = cfg["ramps"]

    ter, ter_src = effective_ter(r)
    r["ter"] = ter
    r["ter_source"] = ter_src

    dy = _num(r.get("div_yield_ttm"))
    dg = _num(r.get("div_growth"))
    cut = _num(r.get("div_worst_cut"))
    mdd = _num(r.get("max_drawdown"))
    c5 = _num(r.get("cagr_5y"))

    yield_p = _ramp(dy, *ramps["div_yield_ttm"])
    cost = _ramp(ter, *ramps["ter"])
    growth, growth_cov = _blend(
        {"dividend": _ramp(dg, *ramps["div_growth"]),
         "price": _ramp(c5, *ramps["cagr_5y"])},
        cfg["growth_mix"],
    )
    # A fund with enough history and no cut on record scores full marks
    # here; one with too little history to have a `worst_cut` scores on
    # drawdown alone, and `_blend` renormalises rather than treating the
    # gap as a zero.
    stability, stab_cov = _blend(
        {"worst_cut": _ramp(cut, *ramps["div_worst_cut"]),
         "max_drawdown": _ramp(mdd, *ramps["max_drawdown"])},
        cfg["stability_mix"],
    )

    _finish(r, {"yield": yield_p, "cost": cost, "growth": growth, "stability": stability},
            {"yield": 1.0 if yield_p is not None else 0.0,
             "cost": 1.0 if cost is not None else 0.0,
             "growth": growth_cov, "stability": stab_cov}, cfg)
    ny = net_yield(r)
    r["net_yield"] = round(ny, 6) if ny is not None else None
    r["accumulating"] = is_accumulating(r)

    gates = check_dividend_gates(r, cfg)
    r["gate_failed"] = gates or None
    if gates:
        r["score"] = None
    r["flags"] = _dividend_flags(r, cfg)
    return r


def _dividend_flags(r, cfg) -> list[str]:
    """Caveats an income candidate still deserves once it has ranked."""
    out: list[str] = []

    # The curated policy versus what the distributions actually show. A
    # disagreement usually means the universe entry points at the sibling
    # share class — the same failure the TER cross-check exists to catch,
    # and worth as much here, because acc/dist decides whether the fund
    # belongs on this board at all.
    curated = (r.get("dist") or "").lower()
    acc = r.get("accumulating")
    if curated == "acc" and acc is False:
        out.append(_t("listed as accumulating but has paid distributions — the "
                      "universe entry is probably the wrong share class"))
    elif curated == "dist" and acc is True:
        out.append(_t("listed as distributing but has paid nothing in 12 months — "
                      "probably the accumulating share class of the same fund"))

    # Computed yield versus Yahoo's own field, where Yahoo has one at all.
    dy, yy = _num(r.get("div_yield_ttm")), _num(r.get("dividend_yield"))
    tol = cfg.get("yield_disagreement_pct", 0.25)
    if dy and yy and yy > 0 and abs(dy - yy) / yy > tol:
        out.append(_f("our trailing yield {ours}% vs Yahoo's {theirs}% — check for "
                      "a special distribution", ours=_pct(dy, 2), theirs=_pct(yy, 2)))

    # A frequency change makes one year's total incomparable with the
    # next for a reason that has nothing to do with the payout rising.
    now, before = r.get("div_events_12m"), r.get("div_events_prior")
    if now and before and now != before:
        out.append(_f("paid {now} times this year vs {before} last — a schedule "
                      "change, so the growth figure is not like-for-like",
                      now=now, before=before))

    cut = _num(r.get("div_worst_cut"))
    if cut is not None and cut < -0.15:
        out.append(_f("has cut before — worst year was {pct}%", pct=_pct(cut, 0)))

    dg = _num(r.get("div_growth"))
    if dg is not None and dg < -0.05:
        out.append(_f("distribution is shrinking ({pct}% year on year)", pct=_pct(dg, 0)))

    ter = _num(r.get("ter"))
    dy_ = _num(r.get("div_yield_ttm"))
    if ter and dy_ and dy_ > 0 and ter / dy_ > 0.12:
        out.append(_f("the TER eats {pct}% of the income", pct=_pct(ter / dy_, 0)))

    if r.get("ter_source") == "yahoo":
        out.append(_t("TER is Yahoo's, not the KID's — verify before ranking on it"))

    ccy = (r.get("currency") or "EUR").upper()
    if ccy != "EUR":
        out.append(_f("returns are in {ccy}, not EUR — the FX series could not be "
                      "fetched, so this row is not comparable with the rest", ccy=ccy))

    if r.get("pea_eligible"):
        out.append(_t("PEA-eligible — distributions inside a PEA are not taxed in "
                      "the year they are paid, which matters more on an income "
                      "holding than on an accumulating one"))
    elif r.get("pea_eligible") is False:
        out.append(_t("not PEA-eligible — in a plain broker account each "
                      "distribution is taxed the year it is paid, so the headline "
                      "yield is not the net one"))

    if (r.get("region") or "") in ("Theme", "Sector", "Property"):
        out.append(_t("single sector — a concentrated bet, not a core income holding"))

    mdd = _num(r.get("max_drawdown"))
    if mdd is not None and mdd > 0.45:
        out.append(_f("fell {pct}% peak to trough within this window", pct=_pct(mdd, 0)))

    if _num(r.get("total_assets")) is None:
        out.append(_t("fund size unknown — Yahoo reports none for this listing"))

    if r.get("coverage", 1.0) < 0.6:
        out.append(_t("thin data — score built on few figures"))
    return out


# --------------------------------------------------------------------------
# Query
# --------------------------------------------------------------------------

PILLAR_ORDER = {
    "growth": ["growth", "cost", "risk", "size"],
    "dividend": ["yield", "cost", "growth", "stability"],
}

# What the payload calls itself, so the page can tell four boards apart.
_PAYLOAD_NAME = {"growth": "etf", "dividend": "etf_dividend"}


def results(conn, top=None, pea_only=False, include_failed=False,
            regions=None, min_score=None, profile="growth") -> dict:
    """The payload an ETF tab of Share Ideas consumes, for one profile.

    `profile` selects which question is asked of the same cached rows:
    "growth" = high past total return for a low TER; "dividend" = high
    trailing yield for a low TER, that is still growing and has not been
    cut. One table, two questions — so the two tabs can never disagree
    about a fund's TER, its size or its drawdown.

    Curated metadata is merged in HERE rather than stored, so correcting a
    TER in the override file lands on the next page load instead of the
    next nightly refresh — the same reason scoring is not stored either.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown ETF profile {profile!r}; "
                         f"expected one of {sorted(PROFILES)}")
    cfg = load_config(profile)
    scorer = score_dividend_row if profile == "dividend" else score_row
    uni = load_universe(conn)
    rows = [dict(r) for r in conn.execute("SELECT * FROM screener_etfs").fetchall()]

    held = owned_symbols(conn)
    # The watchlist table is keyed on a bare symbol, so it is shared with
    # the share boards rather than duplicated. Starring an ETF and starring
    # a share are the same act, and one list is what makes "watchlist only"
    # mean the same thing on every tab.
    watch = {r["symbol"]: dict(r) for r in conn.execute(
        "SELECT * FROM screener_watchlist").fetchall()}

    scored, rejected = [], []
    for raw in rows:
        meta = uni.get(raw["symbol"], {})
        merged = dict(raw)
        for f in _META_FIELDS:
            if f == "name" and raw.get("name"):
                continue          # Yahoo's full legal name beats our short one
            if meta.get(f) is not None:
                merged[f] = meta[f]
        r = scorer(merged, cfg)
        r["held"] = r["symbol"] in held
        r["in_universe"] = r["symbol"] in uni
        wl = watch.get(r["symbol"])
        r["watch_status"] = wl["status"] if wl else None
        r["note"] = wl.get("note") if wl else None
        (rejected if r["gate_failed"] else scored).append(r)

    if profile == "dividend":
        _flag_duplicate_listings(scored)

    scored.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0)))
    if pea_only:
        scored = [r for r in scored if r.get("pea_eligible")]
    if regions:
        want = {s.lower() for s in regions}
        scored = [r for r in scored if (r.get("region") or "").lower() in want]
    if min_score is not None:
        scored = [r for r in scored if (r["score"] or 0) >= min_score]
    if top:
        scored = scored[:top]

    fetched = [r["fetched_at"] for r in rows if r.get("fetched_at")]
    all_regions = sorted({(uni.get(r["symbol"], {}) or {}).get("region")
                          for r in rows} - {None})
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "profile": _PAYLOAD_NAME[profile],
        "pillar_order": PILLAR_ORDER[profile],
        "universe_size": len(rows),
        "ranked": scored,
        "rejected": sorted(rejected, key=lambda x: x["symbol"]) if include_failed else [],
        "rejected_count": len(rejected),
        "regions": all_regions,
        "last_refresh": max(fetched) if fetched else None,
        "oldest_row": min(fetched) if fetched else None,
        "errors": sum(1 for r in rows if r.get("last_error")),
        "config": cfg,
    }


def _normalise_fund_name(name: str | None) -> str:
    """A fund name reduced to what identifies the FUND rather than the
    share class or the listing venue."""
    s = (name or "").lower()
    for noise in ("ucits etf", "ucits", "etf", "(de)", "(dist)", "(acc)",
                  "dist", "acc", "distributing", "accumulating", "inc",
                  "eur", "usd", "gbp", "chf", "hedged", "1d", "1c"):
        s = s.replace(noise, " ")
    return " ".join(s.split())


def _flag_duplicate_listings(rows) -> None:
    """Mark funds that appear more than once under different symbols.

    `IQQA.DE` and `IDVY.AS` are one fund on two exchanges; so are
    `VHYL.AS` / `VGWD.DE` and `IPRP.AS` / `IQQP.DE`. On the growth board
    that is harmless — you are comparing funds, and a duplicate is one
    extra row. On an income board it is worse than harmless, because the
    output is a SHORTLIST: three of the top five slots being the same two
    funds is a shortlist that has quietly lost most of its choices.

    Flagged rather than deduplicated. Which listing you can actually buy,
    and in which currency, depends on your broker — that is the reader's
    decision, and silently dropping the sibling would make it for them
    while hiding that it happened.
    """
    groups: dict[str, list] = {}
    for r in rows:
        key = _normalise_fund_name(r.get("name"))
        if key:
            groups.setdefault(key, []).append(r)
    for members in groups.values():
        if len(members) < 2:
            continue
        for r in members:
            others = ", ".join(sorted(o["symbol"] for o in members
                                      if o["symbol"] != r["symbol"]))
            r.setdefault("flags", []).append(
                _f("the same fund is also listed as {others} — pick the listing "
                   "your broker offers, they are not separate holdings", others=others))
            r["duplicate_of"] = others


def last_refresh(conn) -> str | None:
    row = conn.execute(
        "SELECT MAX(fetched_at) AS t FROM screener_etfs WHERE last_error IS NULL"
    ).fetchone()
    return row["t"] if row else None
