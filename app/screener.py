"""Share Ideas — "cheap, beaten-down, quality, pays a dividend".

Answers the standing question *"which shares are worth a look right
now?"* against four criteria:

    value dropped  ·  P/E low  ·  quality share  ·  pays dividends

Two boards, one cache
---------------------
The same `screener_fundamentals` rows are scored through two PROFILES:

  * **value** — the board above.
  * **income** — "highest dividend that is still growing": yield 35%,
    growth 30% (dividend, revenue, earnings), safety 20% (payout, free
    cash flow cover, leverage), quality 15%.

They are profiles rather than two modules because nothing needs to be
refetched to answer the second question, and because two boards reading
one row can never disagree about a company's yield. ETFs are the
exception and live in `screener_etf.py`: an ETF has no ROE, no payout
ratio and no P/E, and the one number that matters for it — the TER —
does not exist in this table at all.

There is no API key for this and none is needed. Yahoo's `quoteSummary`
carries every field the four criteria need (trailing/forward P/E,
dividend yield and payout ratio, ROE / margins / debt-to-equity /
current ratio, 52-week high and low); `yahoo.py` does the cookie-and-
crumb handshake it wants. No new dependency, no new secret.

Why a nightly cache rather than live fetching
---------------------------------------------
One Yahoo request per symbol at ~360 symbols is minutes, not
milliseconds, and Yahoo rate-limits. So `refresh()` writes into
`screener_fundamentals` from a background thread and the page only ever
reads it. A failed symbol keeps its previous row (with `last_error` set)
instead of vanishing from the board.

Scoring is deliberately transparent
-----------------------------------
Every pillar is a documented linear ramp over one or two published
figures, blended with fixed weights, and the API hands the browser both
the score AND the inputs that produced it. A screener you cannot audit
is a horoscope. Missing inputs are not silently treated as zero: the
weights are renormalised over the fields that are actually present, and
the row carries a `coverage` fraction so a thin row can be distrusted on
sight.

Hard gates run BEFORE scoring and are recorded, not hidden — a name that
fails "pays a dividend" stays in the table with `gate_failed` set,
because knowing *why* something is absent is worth as much as the
ranking.

PEA eligibility is surfaced because for a French reader it decides
where a share can sit: only EU/EEA-seated companies qualify. It is
derived from the reported country of incorporation and flagged as
indicative — Yahoo's `country` is occasionally the HQ rather than the
registered seat, so it is a filter for the shortlist, never a substitute
for checking with the broker.

Thresholds live in `screener.json` in the data folder, so they can be
tuned without a deploy; the page re-reads the file on every request.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone

from . import i18n
from .settings import DATA_DIR
from .screener_universe import DEFAULT_UNIVERSE

CONFIG_FILE = DATA_DIR / "screener.json"
UNIVERSE_FILE = DATA_DIR / "screener_universe.json"

# The sentences a gate or a flag produces are read on the page, so they
# go through the catalogue like everything else the page says.
_t, _f = i18n.t, i18n.f

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# Thresholds are the ends of the scoring ramps, not cliff edges: a name at
# the "good" end scores 100 on that pillar, at the "poor" end 0, linear in
# between. They live in a JSON file so they can be tuned without a deploy
# (the page re-reads on every request), but the defaults below are what the
# board actually runs on.

DEFAULTS = {
    # Composite weights — must be meaningful relative to each other, they
    # are renormalised so they need not sum to 1.
    "weights": {
        "value": 0.25,      # how far below its own 52-week high
        "cheap": 0.25,      # P/E / price-to-book
        "quality": 0.30,    # ROE, margins, leverage, liquidity
        "dividend": 0.20,   # yield, and whether it is covered
    },
    # Hard gates. A name failing any of these is stored but not ranked.
    "gates": {
        "min_market_cap": 1_000_000_000,   # reporting currency, ~1bn floor
        "require_dividend": True,
        "min_dividend_yield": 0.005,       # 0.5% — a token dividend is not one
        "require_positive_earnings": True,
        "max_payout_ratio": 1.50,          # >150% is a dividend being borrowed
        "max_pe": 60.0,                    # above this "low P/E" is meaningless
    },
    # Ramp endpoints: [poor, good].
    "ramps": {
        "drawdown": [0.05, 0.40],          # 5% off the high = nothing, 40% = full
        "pe": [25.0, 8.0],                 # inverted: lower is better
        "pb": [4.0, 1.0],                  # inverted
        "roe": [0.08, 0.25],
        "operating_margin": [0.05, 0.25],
        "debt_to_equity": [2.0, 0.30],     # inverted, as a ratio not a percent
        "current_ratio": [0.80, 2.00],
        "dividend_yield": [0.015, 0.055],
        "payout_sweet_spot": [0.25, 0.60], # full marks inside, decaying outside
    },
    # Sub-weights inside the composite pillars.
    "cheap_mix": {"pe": 0.75, "pb": 0.25},
    "quality_mix": {
        "roe": 0.35,
        "operating_margin": 0.25,
        "debt_to_equity": 0.25,
        "current_ratio": 0.15,
    },
    "dividend_mix": {"yield": 0.60, "payout": 0.40},
    # A row older than this is refetched by `refresh`; below it, skipped.
    "max_age_hours": 20,
}

# --------------------------------------------------------------------------
# Income profile
# --------------------------------------------------------------------------
# The second board answers a DIFFERENT question over the SAME cache:
# "highest dividend that is still growing". It is a scoring profile, not a
# second screener — nothing is refetched, because every input it needs is
# already a column. Adding it as a profile rather than a module is what
# keeps the two boards permanently consistent: they cannot disagree about
# a company's yield, because they read the same row.
#
# Why the weights are not simply "yield, then growth"
# ---------------------------------------------------
# A pure yield ranking is a yield-trap generator: the highest yields on
# any given day belong to the companies the market has just decided will
# cut. Yield and growth carry 65% between them — but a SAFETY pillar
# (payout, free-cash-flow cover, leverage) and the usual quality pillar
# hold the other 35%, and the gates below refuse to rank a yield that is
# already a distress signal. A board that ranked purely on yield would
# put the next dividend cut at the top of it, every time.

INCOME_DEFAULTS = {
    "weights": {
        "yield": 0.35,     # what it pays today
        "growth": 0.30,    # dividend, revenue and earnings growth
        "safety": 0.20,    # can it keep paying — payout, FCF cover, leverage
        "quality": 0.15,   # does the business earn its money
    },
    "gates": {
        "min_market_cap": 1_000_000_000,
        "min_dividend_yield": 0.025,       # below 2.5% it is not an income idea
        # A double-digit yield on a large cap is the market pricing a cut,
        # not an opportunity. Gated rather than merely flagged, because on
        # a board sorted by yield those names would otherwise own the top
        # of the list permanently.
        "max_dividend_yield": 0.12,
        "require_positive_earnings": True,
        "max_payout_ratio": 0.90,          # stricter than the value board
        "max_pe": 40.0,
        # Only fires when the figure is actually present — a company with
        # no reported revenue growth is unknown, not shrinking.
        "min_revenue_growth": -0.02,
    },
    "ramps": {
        "dividend_yield": [0.020, 0.070],
        "dividend_growth": [0.00, 0.08],   # forward vs trailing dividend
        "revenue_growth": [0.00, 0.08],
        "earnings_growth": [0.00, 0.12],
        "payout": [0.90, 0.35],            # inverted: headroom is the point
        "fcf_payout": [1.20, 0.45],        # inverted
        "debt_to_equity": [2.0, 0.30],     # inverted
        "current_ratio": [0.80, 2.00],
        "roe": [0.08, 0.25],
        "operating_margin": [0.05, 0.25],
        "profit_margin": [0.03, 0.20],
    },
    "growth_mix": {"dividend": 0.45, "revenue": 0.30, "earnings": 0.25},
    "safety_mix": {
        "payout": 0.35,
        "fcf_payout": 0.25,
        "debt_to_equity": 0.25,
        "current_ratio": 0.15,
    },
    "quality_mix": {"roe": 0.40, "operating_margin": 0.35, "profit_margin": 0.25},
    "max_age_hours": 20,
}

PROFILES = {"value": DEFAULTS, "income": INCOME_DEFAULTS}

# EU/EEA seats — the PEA eligibility test. Switzerland and the UK are
# deliberately absent: neither is in the EEA, so neither is PEA-eligible,
# however European they feel.
EEA_COUNTRIES = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany",
    "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Latvia",
    "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Norway", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
    "Spain", "Sweden",
}

# Seconds between Yahoo requests during a refresh. Yahoo rate-limits,
# and a screener refreshed once a night is in no hurry.
REQUEST_PAUSE = 0.4


def load_config(profile: str = "value") -> dict:
    """Config file merged over the profile's defaults, one level per section.

    The value board reads the TOP LEVEL of `screener.json`; the income
    board reads the nested `"income"` section, so the two can be tuned
    independently without either one inheriting thresholds meant for the
    other (a 60x max_pe is sane on a "what has fallen" board and absurd
    on an income one).
    """
    base = PROFILES.get(profile, DEFAULTS)
    cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    if not CONFIG_FILE.exists():
        return cfg
    try:
        user = json.loads(CONFIG_FILE.read_text())
    except Exception:
        return cfg
    if profile != "value":
        user = user.get(profile) or {}
        if not isinstance(user, dict):
            return cfg
    for key, val in user.items():
        if key in PROFILES or key in ("etf", "etf_dividend"):
            continue          # a sibling board's section, not ours
        if isinstance(val, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(val)
        else:
            cfg[key] = val
    return cfg


# --------------------------------------------------------------------------
# Holdings — what the reader already owns
# --------------------------------------------------------------------------

def held_symbols(conn) -> dict[str, dict]:
    """{symbol: {name, quote_type}} for every open position with a ticker.

    A holding sold down to nothing is not a holding. The ticker and the
    instrument type come from `securities`, which the price feed fills
    in; a holding the feed has not priced yet has no ticker and cannot
    be screened until it does.
    """
    try:
        rows = conn.execute(
            "SELECT s.symbol, s.quote_type, COALESCE(s.name, MAX(t.security_name)) AS name "
            "  FROM securities s JOIN transactions t ON t.isin = s.isin "
            " WHERE s.symbol IS NOT NULL AND s.symbol <> '' "
            "   AND t.kind IN ('buy', 'sell') AND t.quantity IS NOT NULL "
            " GROUP BY s.symbol HAVING ABS(SUM(t.quantity)) > 1e-9").fetchall()
    except Exception:
        return {}
    return {str(r["symbol"]).strip().upper():
            {"name": r["name"], "quote_type": (r["quote_type"] or "").upper() or None}
            for r in rows if r["symbol"]}


def owned_symbols(conn) -> set[str]:
    return set(held_symbols(conn))


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------

def load_universe(conn=None) -> list[str]:
    """Symbols to screen: the shipped list, the user's file, and own holdings.

    Own holdings are folded in automatically so the page always scores
    what the reader already owns alongside the candidates — the most
    useful comparison on the screen is "is this cheaper than what I
    hold?", and it costs one query. Only what Yahoo calls an equity
    qualifies (or what it has not classified yet): an ETF has no P/E or
    ROE and would score as an all-gates-failed row for no reason. It goes
    to the ETF board instead.
    """
    symbols: list[str] = []
    seen: set[str] = set()

    def _add(sym) -> None:
        if not sym:
            return
        s = str(sym).strip().upper()
        if s and s not in seen:
            seen.add(s)
            symbols.append(s)

    data: dict = {}
    if UNIVERSE_FILE.exists():
        try:
            data = json.loads(UNIVERSE_FILE.read_text()) or {}
            for s in data.get("symbols", []):
                _add(s)
        except Exception:
            data = {}
    else:
        try:
            UNIVERSE_FILE.write_text(json.dumps(
                {"symbols": [], "exclude": [],
                 "_help": "Symbols to screen besides the shipped list, and "
                          "shipped symbols to leave out."}, indent=2))
        except OSError:
            pass

    for s in DEFAULT_UNIVERSE:
        _add(s)

    if conn is not None:
        for sym, meta in held_symbols(conn).items():
            if meta["quote_type"] in (None, "EQUITY"):
                _add(sym)

    exclude = {str(s).strip().upper() for s in data.get("exclude", [])}
    return [s for s in symbols if s not in exclude]


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

_NUMERIC_COLS = [
    "price", "market_cap", "trailing_pe", "forward_pe", "price_to_book",
    "dividend_yield", "payout_ratio", "div_yield_5y_avg", "return_on_equity",
    "operating_margin", "profit_margin", "debt_to_equity", "current_ratio",
    "revenue_growth", "earnings_growth", "beta", "week52_high", "week52_low",
    "dividend_rate", "trailing_dividend_rate", "free_cashflow",
    "shares_outstanding",
]
_TEXT_COLS = [
    "name", "sector", "industry", "country", "exchange", "currency", "quote_type",
]
_ALL_COLS = _TEXT_COLS + _NUMERIC_COLS


def upsert(conn, symbol: str, fields: dict, error: str | None = None) -> None:
    """Write one row. On error, keep the old values and only stamp the error.

    Never blanking a row on a failed fetch is the point: a transient Yahoo
    hiccup should not make a name disappear from the board, it should make
    it visibly stale.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if error is not None and not fields:
        conn.execute(
            "INSERT INTO screener_fundamentals (symbol, last_error, fetched_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(symbol) DO UPDATE SET last_error = excluded.last_error",
            (symbol, error, now),
        )
        return
    cols = ["symbol"] + _ALL_COLS + ["fetched_at", "last_error"]
    vals = [symbol] + [fields.get(c) for c in _ALL_COLS] + [now, error]
    placeholders = ", ".join("?" for _ in cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in cols[1:])
    conn.execute(
        f"INSERT INTO screener_fundamentals ({', '.join(cols)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT(symbol) DO UPDATE SET {updates}",
        vals,
    )


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def _num(v):
    """Yahoo returns None, NaN, 'Infinity' and strings interchangeably."""
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _as_fraction(v, cap: float = 1.0):
    """Normalise a rate that Yahoo may report as a fraction OR a percent.

    `dividendYield` has been reported as 0.031 AND as 3.1 across Yahoo's
    own endpoints and the libraries over them; `debtToEquity` has always
    been a percent (150.4 meaning 1.504x). Rather than trust a source,
    decide per value: anything above `cap` is read as a percent. A 100%+
    genuine dividend yield does not exist, and a genuine payout ratio
    above 1.0 is caught by the max_payout_ratio gate either way.
    """
    f = _num(v)
    if f is None:
        return None
    return f / 100.0 if abs(f) > cap else f


def _default_fetcher(symbol: str) -> dict:
    """Raw Yahoo fundamentals for one symbol. Imported here, not at the
    top, so importing this module costs nothing on the network side."""
    from . import yahoo
    return yahoo.fundamentals(symbol, yahoo.SHARE_MODULES)


def normalise(info: dict) -> dict:
    """Yahoo's flattened summary → this module's column names and units.

    Everything that is a rate comes out as a FRACTION and everything that
    is a ratio comes out as a RATIO, so the scoring functions never have to
    ask what unit they were handed.
    """
    price = _num(info.get("currentPrice"))
    if price is None:
        price = _num(info.get("regularMarketPrice"))
    if price is None:
        price = _num(info.get("previousClose"))

    div_yield = _as_fraction(info.get("dividendYield"), cap=1.0)
    if not div_yield:
        # Fall back to rate/price — present when dividendYield is absent,
        # and a useful cross-check when the unit is ambiguous.
        rate = _num(info.get("trailingAnnualDividendRate")) or _num(info.get("dividendRate"))
        if rate and price:
            div_yield = rate / price
    if div_yield is not None and (div_yield <= 0 or div_yield > 0.30):
        # >30% is a data error or a liquidating special, not an income stock.
        div_yield = None

    d2e = _num(info.get("debtToEquity"))
    if d2e is not None:
        d2e = d2e / 100.0 if abs(d2e) > 5 else d2e

    return {
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "currency": info.get("currency"),
        "quote_type": info.get("quoteType"),
        "price": price,
        "market_cap": _num(info.get("marketCap")),
        "trailing_pe": _num(info.get("trailingPE")),
        "forward_pe": _num(info.get("forwardPE")),
        "price_to_book": _num(info.get("priceToBook")),
        "dividend_yield": div_yield,
        "payout_ratio": _as_fraction(info.get("payoutRatio"), cap=3.0),
        # fiveYearAvgDividendYield has always been a percent (3.4 = 3.4%).
        "div_yield_5y_avg": (lambda v: v / 100.0 if v else None)(
            _num(info.get("fiveYearAvgDividendYield"))
        ),
        "return_on_equity": _as_fraction(info.get("returnOnEquity"), cap=3.0),
        "operating_margin": _as_fraction(info.get("operatingMargins"), cap=3.0),
        "profit_margin": _as_fraction(info.get("profitMargins"), cap=3.0),
        "debt_to_equity": d2e,
        "current_ratio": _num(info.get("currentRatio")),
        "revenue_growth": _as_fraction(info.get("revenueGrowth"), cap=3.0),
        "earnings_growth": _as_fraction(info.get("earningsGrowth"), cap=5.0),
        "beta": _num(info.get("beta")),
        "week52_high": _num(info.get("fiftyTwoWeekHigh")),
        "week52_low": _num(info.get("fiftyTwoWeekLow")),
        # Both dividend rates are per-share amounts in the reporting
        # currency, NOT rates — so no _as_fraction here, and the pair is
        # only ever used as a ratio, which makes the currency cancel.
        "dividend_rate": _num(info.get("dividendRate")),
        "trailing_dividend_rate": _num(info.get("trailingAnnualDividendRate")),
        "free_cashflow": _num(info.get("freeCashflow")),
        "shares_outstanding": _num(info.get("sharesOutstanding")),
    }


def refresh(conn, symbols=None, fetcher=None, limit=None, force=False,
            sleep_s=0.0, log=None, stop=None) -> dict:
    """Fetch and store fundamentals. Returns {ok, failed, skipped, attempted}.

    Each row is committed on its own: a refresh is minutes long, and a
    transaction held open that long would block the bank sync that
    happens to run at the same time. `stop` is a callable the thread can
    use to bow out early.
    """
    cfg = load_config()
    fetcher = fetcher or _default_fetcher
    syms = list(symbols) if symbols else load_universe(conn)

    if not force:
        # Count what THIS run dropped, not every fresh row in the table.
        fresh = _fresh_symbols(conn, cfg["max_age_hours"])
        kept = [s for s in syms if s not in fresh]
        skipped = len(syms) - len(kept)
        syms = kept
    else:
        skipped = 0

    if limit:
        syms = syms[:limit]

    ok = failed = 0
    for i, sym in enumerate(syms, 1):
        if stop and stop():
            break
        try:
            info = fetcher(sym)
            fields = normalise(info) if info else {}
            if not fields.get("price"):
                raise ValueError("no price in Yahoo response")
            upsert(conn, sym, fields, error=None)
            ok += 1
        except Exception as e:
            failed += 1
            upsert(conn, sym, {}, error=f"{type(e).__name__}: {e}"[:300])
            if log:
                log(f"{sym}: {type(e).__name__}: {e}")
            if "429" in str(e):
                # Rate-limited. Waiting is the only thing that helps.
                time.sleep(15)
        conn.commit()
        if sleep_s:
            time.sleep(sleep_s)
    return {"ok": ok, "failed": failed, "skipped": skipped, "attempted": len(syms)}


def _fresh_symbols(conn, max_age_hours: float) -> set[str]:
    rows = conn.execute(
        "SELECT symbol FROM screener_fundamentals "
        "WHERE last_error IS NULL AND fetched_at IS NOT NULL "
        "AND fetched_at > datetime('now', ?)",
        (f"-{float(max_age_hours)} hours",),
    ).fetchall()
    return {r[0] for r in rows}


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def _ramp(x, poor, good):
    """Linear 0..100 from `poor` to `good`; works in either direction.

    `good < poor` gives an inverted ramp (lower is better), which is what
    P/E, price-to-book and debt-to-equity want.
    """
    if x is None or poor == good:
        return None
    t = (x - poor) / (good - poor)
    return max(0.0, min(1.0, t)) * 100.0


def _plateau(x, lo, hi, tolerance=None):
    """100 inside [lo, hi], decaying linearly outside over `tolerance`.

    The payout ratio is the one figure here where more is not better and
    less is not better: too low and the dividend is an afterthought, too
    high and it is not covered by earnings.
    """
    if x is None:
        return None
    if tolerance is None:
        tolerance = (hi - lo) * 1.5
    if lo <= x <= hi:
        return 100.0
    d = (lo - x) if x < lo else (x - hi)
    return max(0.0, 100.0 * (1.0 - d / tolerance))


def _blend(parts: dict, weights: dict):
    """Weighted mean over the components that are present.

    Returns (score, coverage) where coverage is the share of the intended
    weight that had data. Renormalising rather than defaulting a missing
    field to zero is what stops a thinly-covered name from being punished
    for Yahoo's gaps — but the coverage number keeps that honest, because
    a score built from one field out of four should not be trusted like
    one built from four.
    """
    tot_w = sum(w for w in weights.values() if w > 0)
    if tot_w <= 0:
        return None, 0.0
    acc = used = 0.0
    for key, w in weights.items():
        v = parts.get(key)
        if v is None or w <= 0:
            continue
        acc += v * w
        used += w
    if used <= 0:
        return None, 0.0
    return acc / used, used / tot_w


def effective_pe(row) -> float | None:
    """Trailing P/E when positive, else forward P/E when positive.

    Trailing first, because it is a fact and the forward figure is an
    analyst consensus. But a company with a loss-making trailing year and
    a credible forward number is exactly the "value dropped" case, so the
    forward figure is used rather than discarding the name.
    """
    tpe = _num(row.get("trailing_pe"))
    if tpe is not None and tpe > 0:
        return tpe
    fpe = _num(row.get("forward_pe"))
    if fpe is not None and fpe > 0:
        return fpe
    return None


def drawdown(row) -> float | None:
    """Fraction below the 52-week high, e.g. 0.28 = 28% off."""
    price = _num(row.get("price"))
    high = _num(row.get("week52_high"))
    if not price or not high or high <= 0:
        return None
    return max(0.0, (high - price) / high)


def off_low(row) -> float | None:
    """Fraction above the 52-week low — the falling-knife check."""
    price = _num(row.get("price"))
    low = _num(row.get("week52_low"))
    if not price or not low or low <= 0:
        return None
    return (price - low) / low


def _pct(v, digits=1) -> str:
    """A fraction as a percentage figure, in the language of the page."""
    return i18n.group(f"{v * 100:.{digits}f}", i18n.active())


def _n(v, digits=1) -> str:
    return i18n.group(f"{v:,.{digits}f}", i18n.active())


def check_gates(row, cfg) -> list[str]:
    """Reasons this name is not rankable. Empty list = it is."""
    g = cfg["gates"]
    fails: list[str] = []

    qt = (row.get("quote_type") or "").upper()
    if qt and qt != "EQUITY":
        fails.append(_f("not a share ({type})", type=qt.lower()))

    mc = _num(row.get("market_cap"))
    if g.get("min_market_cap"):
        if mc is None:
            fails.append(_t("no market cap"))
        elif mc < g["min_market_cap"]:
            fails.append(_f("too small ({bn}bn)", bn=_n(mc / 1e9, 2)))

    pe = effective_pe(row)
    if g.get("require_positive_earnings") and pe is None:
        fails.append(_t("no positive earnings"))
    if pe is not None and g.get("max_pe") and pe > g["max_pe"]:
        fails.append(_f("P/E too high ({pe})", pe=_n(pe, 0)))

    dy = _num(row.get("dividend_yield"))
    if g.get("require_dividend"):
        if not dy:
            fails.append(_t("pays no dividend"))
        elif dy < g.get("min_dividend_yield", 0):
            fails.append(_f("token dividend ({pct}%)", pct=_pct(dy, 2)))

    payout = _num(row.get("payout_ratio"))
    if payout is not None and g.get("max_payout_ratio") and payout > g["max_payout_ratio"]:
        fails.append(_f("dividend not covered ({pct}% payout)", pct=_pct(payout, 0)))

    return fails


def _finish(r: dict, pillars: dict, sub_cov: dict, cfg: dict) -> None:
    """The fields every scorer adds: rounded pillars, the composite, and
    the nested coverage.

    Coverage is nested, not flat. A pillar that exists but was built
    from one of its two inputs is not fully covered, and reporting it as
    such would hide exactly the rows that deserve distrust — a name
    scored on price-and-yield alone must not look as solid as one scored
    on twelve figures.
    """
    composite, _ = _blend(pillars, cfg["weights"])
    w_total = sum(w for w in cfg["weights"].values() if w > 0)
    coverage = (sum(cfg["weights"].get(k, 0) * v for k, v in sub_cov.items()) / w_total
                if w_total > 0 else 0.0)
    r["pillars"] = {k: (round(v, 1) if v is not None else None)
                    for k, v in pillars.items()}
    r["score"] = round(composite, 1) if composite is not None else None
    r["coverage"] = round(coverage, 2)
    r["pillar_coverage"] = {k: round(v, 2) for k, v in sub_cov.items()}


def _derived(r: dict) -> None:
    """The figures both share boards show beside the score."""
    dd, ol, pe = drawdown(r), off_low(r), effective_pe(r)
    r["drawdown"] = round(dd, 4) if dd is not None else None
    r["off_52w_low"] = round(ol, 4) if ol is not None else None
    r["effective_pe"] = round(pe, 2) if pe is not None else None
    r["pe_basis"] = (
        "trailing" if (_num(r.get("trailing_pe")) or 0) > 0
        else ("forward" if pe is not None else None)
    )
    r["pea_eligible"] = (r.get("country") in EEA_COUNTRIES) if r.get("country") else None


def score_row(row, cfg=None) -> dict:
    """Score one fundamentals row against the four criteria.

    Returns the row's own fields plus `pillars`, `score`, `coverage`,
    `gate_failed` and `flags`. Deliberately returns the inputs alongside
    the outputs so the page can show its working.
    """
    cfg = cfg or load_config()
    r = dict(row)
    ramps = cfg["ramps"]

    dd = drawdown(r)
    pe = effective_pe(r)
    pb = _num(r.get("price_to_book"))
    dy = _num(r.get("dividend_yield"))
    payout = _num(r.get("payout_ratio"))

    # --- value: how far it has fallen from its own 52-week high ---
    value = _ramp(dd, *ramps["drawdown"])

    # --- cheap: P/E, with price-to-book as the minority partner ---
    cheap, cheap_cov = _blend(
        {"pe": _ramp(pe, *ramps["pe"]),
         "pb": _ramp(pb, *ramps["pb"]) if (pb and pb > 0) else None},
        cfg["cheap_mix"],
    )

    # --- quality: earns well, is not over-levered, can pay its bills ---
    quality, quality_cov = _blend(
        {
            "roe": _ramp(_num(r.get("return_on_equity")), *ramps["roe"]),
            "operating_margin": _ramp(_num(r.get("operating_margin")),
                                      *ramps["operating_margin"]),
            "debt_to_equity": _ramp(_num(r.get("debt_to_equity")),
                                    *ramps["debt_to_equity"]),
            "current_ratio": _ramp(_num(r.get("current_ratio")),
                                   *ramps["current_ratio"]),
        },
        cfg["quality_mix"],
    )

    # --- dividend: pays, and can keep paying ---
    dividend, div_cov = _blend(
        {"yield": _ramp(dy, *ramps["dividend_yield"]),
         "payout": _plateau(payout, *ramps["payout_sweet_spot"])},
        cfg["dividend_mix"],
    )

    _finish(r,
            {"value": value, "cheap": cheap, "quality": quality, "dividend": dividend},
            {"value": 1.0 if value is not None else 0.0, "cheap": cheap_cov,
             "quality": quality_cov, "dividend": div_cov},
            cfg)
    _derived(r)

    gates = check_gates(r, cfg)
    r["gate_failed"] = gates or None
    if gates:
        r["score"] = None

    r["flags"] = _flags(r, cfg)
    return r


def _flags(r, cfg) -> list[str]:
    """Short human warnings a ranked name still deserves.

    These do not change the score — they are the caveats a screener owes
    you once it has told you something looks cheap. The falling-knife one
    matters most: "40% off the high" and "sitting on its 52-week low" are
    the same fact seen from two ends, and only the second tells you the
    market has not yet stopped selling.
    """
    out: list[str] = []
    ol = off_low(r)
    if ol is not None and ol < 0.08:
        out.append(_t("near its 52-week low — still falling?"))
    payout = _num(r.get("payout_ratio"))
    if payout is not None and 0.90 <= payout <= cfg["gates"].get("max_payout_ratio", 1.5):
        out.append(_t("payout ratio above 90% — dividend barely covered"))
    dy = _num(r.get("dividend_yield"))
    avg = _num(r.get("div_yield_5y_avg"))
    if dy and avg and dy > avg * 1.8:
        out.append(_t("yield far above its own 5-year average — possible yield trap"))
    pe = effective_pe(r)
    if pe is not None and (_num(r.get("trailing_pe")) or 0) <= 0:
        out.append(_t("no trailing profit — P/E is the forward estimate"))
    eg = _num(r.get("earnings_growth"))
    if eg is not None and eg < -0.20:
        out.append(_f("earnings down {pct}% year on year", pct=_pct(abs(eg), 0)))
    d2e = _num(r.get("debt_to_equity"))
    if d2e is not None and d2e > 2.0:
        out.append(_f("leveraged ({ratio}x debt/equity)", ratio=_n(d2e, 1)))
    if r.get("coverage", 1.0) < 0.6:
        out.append(_t("thin data — score built on few figures"))
    return out


# --------------------------------------------------------------------------
# Income scoring — "highest dividend that is still growing"
# --------------------------------------------------------------------------

def dividend_growth(row) -> float | None:
    """Forward annual dividend vs the trailing twelve months, as a fraction.

    Yahoo publishes both `dividendRate` (the forward-looking annual rate
    implied by the most recent declaration) and `trailingAnnualDividendRate`
    (what was actually paid over the last year). Their ratio is the only
    dividend-growth signal available without a second request per symbol —
    and it is a *forward* one, so it sees a cut at the moment it is
    declared rather than a year later.

    It is noisy for irregular payers: a company that moved from four
    quarterly payments to one annual one, or paid a special, can show
    ±50% growth that means nothing. `_income_flags()` marks that rather
    than the ramp hiding it, because the alternative — silently discarding
    large moves — would also discard genuine cuts, which are the single
    most important thing this board must not miss.
    """
    fwd = _num(row.get("dividend_rate"))
    trl = _num(row.get("trailing_dividend_rate"))
    if not fwd or not trl or trl <= 0 or fwd <= 0:
        return None
    return fwd / trl - 1.0


def fcf_payout(row) -> float | None:
    """Dividends as a share of free cash flow.

    The earnings payout ratio is the headline number and the weaker one:
    earnings are an accounting result and can be flattered by non-cash
    items, whereas a dividend is paid in cash. A utility at a 70% earnings
    payout but a 130% cash payout is funding its dividend from the balance
    sheet, and only this figure says so. Missing for plenty of names, which
    is exactly why the safety pillar renormalises rather than defaults.
    """
    rate = _num(row.get("dividend_rate")) or _num(row.get("trailing_dividend_rate"))
    shares = _num(row.get("shares_outstanding"))
    fcf = _num(row.get("free_cashflow"))
    if not rate or not shares or not fcf or fcf <= 0:
        return None
    return (rate * shares) / fcf


def check_income_gates(row, cfg) -> list[str]:
    """Reasons this name is not an income candidate. Empty list = it is."""
    g = cfg["gates"]
    fails: list[str] = []

    qt = (row.get("quote_type") or "").upper()
    if qt and qt != "EQUITY":
        fails.append(_f("not a share ({type})", type=qt.lower()))

    mc = _num(row.get("market_cap"))
    if g.get("min_market_cap"):
        if mc is None:
            fails.append(_t("no market cap"))
        elif mc < g["min_market_cap"]:
            fails.append(_f("too small ({bn}bn)", bn=_n(mc / 1e9, 2)))

    dy = _num(row.get("dividend_yield"))
    if not dy:
        fails.append(_t("pays no dividend"))
    else:
        if dy < g.get("min_dividend_yield", 0):
            fails.append(_f("yield too low for income ({pct}%)", pct=_pct(dy, 2)))
        elif g.get("max_dividend_yield") and dy > g["max_dividend_yield"]:
            fails.append(_f("yield says distress ({pct}%)", pct=_pct(dy, 1)))

    pe = effective_pe(row)
    if g.get("require_positive_earnings") and pe is None:
        fails.append(_t("no positive earnings"))
    if pe is not None and g.get("max_pe") and pe > g["max_pe"]:
        fails.append(_f("P/E too high ({pe})", pe=_n(pe, 0)))

    payout = _num(row.get("payout_ratio"))
    if payout is not None and g.get("max_payout_ratio") and payout > g["max_payout_ratio"]:
        fails.append(_f("payout leaves no headroom ({pct}%)", pct=_pct(payout, 0)))

    # Growth gate. Fires only on a figure that is PRESENT — an unreported
    # revenue growth means unknown, and gating on unknown would quietly
    # empty the board of every company Yahoo happens to cover thinly.
    floor = g.get("min_revenue_growth")
    rg = _num(row.get("revenue_growth"))
    if floor is not None and rg is not None and rg < floor:
        fails.append(_f("revenue shrinking ({pct}%)", pct=_pct(rg, 1)))

    return fails


def score_income_row(row, cfg=None) -> dict:
    """Score one fundamentals row as an income candidate.

    Same contract as `score_row()` — the row's own fields plus `pillars`,
    `score`, `coverage`, `gate_failed` and `flags` — so the page can render
    both boards through one code path, and so a row can be handed to either
    scorer without conversion.
    """
    cfg = cfg or load_config("income")
    r = dict(row)
    ramps = cfg["ramps"]

    dy = _num(r.get("dividend_yield"))
    dg = dividend_growth(r)
    rg = _num(r.get("revenue_growth"))
    eg = _num(r.get("earnings_growth"))
    payout = _num(r.get("payout_ratio"))
    fcfp = fcf_payout(r)

    # --- yield: what it pays today ---
    yield_score = _ramp(dy, *ramps["dividend_yield"])

    # --- growth: "still a certain growth" ---
    growth, growth_cov = _blend(
        {
            "dividend": _ramp(dg, *ramps["dividend_growth"]),
            "revenue": _ramp(rg, *ramps["revenue_growth"]),
            "earnings": _ramp(eg, *ramps["earnings_growth"]),
        },
        cfg["growth_mix"],
    )

    # --- safety: can it keep paying ---
    safety, safety_cov = _blend(
        {
            "payout": _ramp(payout, *ramps["payout"]),
            "fcf_payout": _ramp(fcfp, *ramps["fcf_payout"]),
            "debt_to_equity": _ramp(_num(r.get("debt_to_equity")),
                                    *ramps["debt_to_equity"]),
            "current_ratio": _ramp(_num(r.get("current_ratio")),
                                   *ramps["current_ratio"]),
        },
        cfg["safety_mix"],
    )

    # --- quality: does the business earn its money ---
    quality, quality_cov = _blend(
        {
            "roe": _ramp(_num(r.get("return_on_equity")), *ramps["roe"]),
            "operating_margin": _ramp(_num(r.get("operating_margin")),
                                      *ramps["operating_margin"]),
            "profit_margin": _ramp(_num(r.get("profit_margin")),
                                   *ramps["profit_margin"]),
        },
        cfg["quality_mix"],
    )

    _finish(r,
            {"yield": yield_score, "growth": growth, "safety": safety, "quality": quality},
            {"yield": 1.0 if yield_score is not None else 0.0, "growth": growth_cov,
             "safety": safety_cov, "quality": quality_cov},
            cfg)
    r["dividend_growth"] = round(dg, 4) if dg is not None else None
    r["fcf_payout"] = round(fcfp, 4) if fcfp is not None else None
    _derived(r)

    gates = check_income_gates(r, cfg)
    r["gate_failed"] = gates or None
    if gates:
        r["score"] = None

    r["flags"] = _income_flags(r, cfg)
    return r


def _income_flags(r, cfg) -> list[str]:
    """Caveats an income candidate still deserves once it has ranked."""
    out: list[str] = []

    dg = r.get("dividend_growth")
    if dg is not None:
        if dg < -0.02:
            out.append(_f("forward dividend {pct}% BELOW the trailing one — "
                          "a cut is already declared", pct=_pct(abs(dg), 0)))
        elif abs(dg) > 0.50:
            out.append(_t("dividend rate moved more than 50% — likely a special, "
                          "or a change of payment frequency, not real growth"))

    dy = _num(r.get("dividend_yield"))
    avg = _num(r.get("div_yield_5y_avg"))
    if dy and avg and dy > avg * 1.5:
        out.append(_t("yield well above its own 5-year average — the price fell, "
                      "the dividend did not rise"))

    fcfp = r.get("fcf_payout")
    if fcfp is not None and fcfp > 1.0:
        out.append(_f("dividend costs {pct}% of free cash flow — paid out of the "
                      "balance sheet, not out of the business", pct=_pct(fcfp, 0)))

    payout = _num(r.get("payout_ratio"))
    if payout is not None and payout > 0.75:
        out.append(_f("payout ratio {pct}% — little room for a bad year",
                      pct=_pct(payout, 0)))

    eg = _num(r.get("earnings_growth"))
    if eg is not None and eg < -0.15:
        out.append(_f("earnings down {pct}% year on year", pct=_pct(abs(eg), 0)))

    d2e = _num(r.get("debt_to_equity"))
    if d2e is not None and d2e > 2.0:
        out.append(_f("leveraged ({ratio}x debt/equity)", ratio=_n(d2e, 1)))

    ol = off_low(r)
    if ol is not None and ol < 0.08:
        out.append(_t("near its 52-week low — the market is still selling"))

    if r.get("coverage", 1.0) < 0.6:
        out.append(_t("thin data — score built on few figures"))
    return out


# --------------------------------------------------------------------------
# Query
# --------------------------------------------------------------------------

PILLAR_ORDER = {
    "value": ["value", "cheap", "quality", "dividend"],
    "income": ["yield", "growth", "safety", "quality"],
}


def results(conn, top=None, pea_only=False, include_failed=False,
            sectors=None, min_score=None, profile="value") -> dict:
    """The payload the Share Ideas page consumes, for one scoring profile.

    `profile` selects which question is being asked of the same cache:
    "value" = cheap, beaten-down, quality, pays a dividend; "income" =
    highest dividend that is still growing. The payload shape is identical
    either way — only `pillars` (and therefore `pillar_order`) differ — so
    the page renders both through one code path.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    cfg = load_config(profile)
    scorer = score_income_row if profile == "income" else score_row
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM screener_fundamentals"
    ).fetchall()]

    held = owned_symbols(conn)
    watch = {r["symbol"]: dict(r) for r in conn.execute(
        "SELECT * FROM screener_watchlist"
    ).fetchall()}

    scored, rejected = [], []
    for raw in rows:
        r = scorer(raw, cfg)
        r["held"] = r["symbol"] in held
        wl = watch.get(r["symbol"])
        r["watch_status"] = wl["status"] if wl else None
        r["note"] = wl.get("note") if wl else None
        (rejected if r["gate_failed"] else scored).append(r)

    scored.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0)))

    if pea_only:
        scored = [r for r in scored if r.get("pea_eligible")]
    if sectors:
        want = {s.lower() for s in sectors}
        scored = [r for r in scored if (r.get("sector") or "").lower() in want]
    if min_score is not None:
        scored = [r for r in scored if (r["score"] or 0) >= min_score]
    if top:
        scored = scored[:top]

    all_sectors = sorted({r["sector"] for r in rows if r.get("sector")})
    fetched = [r["fetched_at"] for r in rows if r.get("fetched_at")]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "profile": profile,
        "pillar_order": PILLAR_ORDER[profile],
        "universe_size": len(rows),
        "ranked": scored,
        "rejected": sorted(rejected, key=lambda x: x["symbol"]) if include_failed else [],
        "rejected_count": len(rejected),
        "sectors": all_sectors,
        "last_refresh": max(fetched) if fetched else None,
        "oldest_row": min(fetched) if fetched else None,
        "errors": sum(1 for r in rows if r.get("last_error")),
        "config": cfg,
    }


def set_watch(conn, symbol: str, status: str | None, note: str | None = None) -> dict:
    symbol = symbol.strip().upper()
    if status is None:
        conn.execute("DELETE FROM screener_watchlist WHERE symbol = ?", (symbol,))
        return {"symbol": symbol, "status": None}
    if status not in ("watch", "dismissed"):
        raise ValueError(f"unknown status {status!r}")
    conn.execute(
        "INSERT INTO screener_watchlist (symbol, status, note) VALUES (?, ?, ?) "
        "ON CONFLICT(symbol) DO UPDATE SET status = excluded.status, "
        "note = COALESCE(excluded.note, screener_watchlist.note)",
        (symbol, status, note),
    )
    return {"symbol": symbol, "status": status, "note": note}


def last_refresh(conn) -> str | None:
    """When the newest share row was fetched, for the Settings page."""
    row = conn.execute(
        "SELECT MAX(fetched_at) AS t FROM screener_fundamentals "
        "WHERE last_error IS NULL").fetchone()
    return row["t"] if row else None
