"""Market prices, from Yahoo Finance.

Until this existed a holding was valued at the price you last traded it
at — honest, labelled as such everywhere, and useless after a month. An
ETF bought at 70 that trades at 90 today is worth 90; a dashboard that
says 70 is a dashboard that is wrong by exactly the amount you were
hoping to see.

Yahoo is the source because it needs no key, no account and no
registration: the same reason the ECB is the source for exchange rates.
Two endpoints, both public and both used by Yahoo's own pages:

  * search — takes an ISIN and answers with tickers. This is the hard
    half. A broker export gives an ISIN, which is the same everywhere,
    and every price source wants a ticker, which is per exchange: the
    same fund is IWDA.AS in Amsterdam and IWDA.L in London, in euros in
    one place and dollars in the other. The answer is kept in
    `securities`, so it is asked once per security ever — and it can be
    typed in, for the security the search gets wrong or cannot find.
  * chart — takes a ticker and answers with the last price, the
    currency it is quoted in, and when. The currency matters: a London
    quote comes back in dollars or in pence, and a price in pence added
    to a value in pounds is off by a hundred.

Two rules run through the rest of the app. **Every price names its
day**, and the pages say it, because a Friday price on a Monday is the
newest there is and a March price in September is a problem. And **a
price the source could not give is not a price of zero**: the holding
falls back to the last trade, labelled, so the total is still a total
and the page says which part of it is old.

Nothing here reaches the network on import. Refreshing happens on a
thread started by main() and from a button under Settings, and a page
renders whether or not the prices arrived.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .db import get_conn, get_state, set_state

SEARCH_URL = ("https://query2.finance.yahoo.com/v1/finance/search"
              "?q={q}&quotesCount=10&newsCount=0")
QUOTE_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
             "?range=5d&interval=1d")

# Yahoo answers urllib's own user agent with a 429 — and, oddly, a full
# browser string too. The shortest thing that looks like a browser is
# what gets through, and it was checked against both endpoints.
USER_AGENT = "Mozilla/5.0"
TIMEOUT = 20

# Refreshed at most this often. Prices move all day; a net worth does
# not need to. Six hours means a server that runs all day sees the
# close, and one started in the morning sees yesterday's.
FRESH_HOURS = 6
FETCHED_AT = "prices_fetched_at"

# Where a fund is most likely to be listed in each currency — used only
# to prefer one of several search results, so that a euro portfolio is
# priced in euros where it can be. The quote's own currency is what is
# stored either way, so a wrong guess here costs a conversion, never a
# wrong number.
_EXCHANGE_SUFFIX = {
    "EUR": (".AS", ".DE", ".PA", ".MI", ".F", ".BR", ".MC", ".VI", ".IR",
            ".LS", ".HE", ".AT"),
    "CHF": (".SW",), "GBP": (".L",), "USD": ("",), "SEK": (".ST",),
    "DKK": (".CO",), "NOK": (".OL",), "PLN": (".WA",), "CZK": (".PR",),
    "JPY": (".T",), "CAD": (".TO",), "AUD": (".AX",), "HKD": (".HK",),
}
_PRICEABLE = {"ETF", "EQUITY", "MUTUALFUND", "INDEX", "CRYPTOCURRENCY"}

# A Yahoo ticker: letters, digits, and the punctuation exchanges use.
_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-=^]{0,19}$")


class PriceError(RuntimeError):
    """Something went wrong fetching a price, in a sentence meant for
    the person reading the page."""


# ─── Fetching ────────────────────────────────────────────────────────

def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PriceError(f"Yahoo refused the request ({exc.code}).") from exc
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        raise PriceError(f"Could not reach Yahoo: {exc}") from exc


def pick_symbol(quotes: list[dict], base_currency: str = "EUR") -> str | None:
    """The best ticker among what the search returned, or None.

    Prefer something priceable over a news hit, and a listing in the
    base currency over one abroad. Ties keep Yahoo's own order, which
    is its relevance ranking.
    """
    suffixes = _EXCHANGE_SUFFIX.get(base_currency.upper(), ())
    best, best_score = None, -1
    for q in quotes:
        symbol = (q.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        score = 0
        if (q.get("quoteType") or "").upper() in _PRICEABLE:
            score += 1
        if any(symbol.endswith(sfx) if sfx else "." not in symbol
               for sfx in suffixes):
            score += 2
        if score > best_score:
            best, best_score = symbol, score
    return best


def resolve(isin: str, base_currency: str = "EUR", get=None) -> dict:
    """ISIN → {symbol, name}, from the search endpoint. Raises PriceError."""
    data = (get or _get_json)(SEARCH_URL.format(q=urllib.parse.quote(isin)))
    quotes = data.get("quotes") or []
    symbol = pick_symbol(quotes, base_currency)
    if not symbol:
        raise PriceError("Yahoo does not know this ISIN. Type its ticker in "
                         "under Settings — the one Yahoo uses, like IWDA.AS.")
    match = next((q for q in quotes if (q.get("symbol") or "").upper() == symbol), {})
    return {"symbol": symbol,
            "name": match.get("longname") or match.get("shortname") or None}


def quote(symbol: str, get=None) -> dict:
    """Ticker → {price, currency, as_of, quote_type}. Raises PriceError.

    The chart endpoint's `meta` has the last price and the currency it
    is in. London quotes in pence come back as "GBp" — a lower-case
    last letter is Yahoo's way of saying hundredths of the currency,
    and it is turned into the currency itself here so that nothing
    downstream has to know.

    `quote_type` is Yahoo's `instrumentType` — EQUITY, ETF, MUTUALFUND
    — which comes free with the price and is what the Share Ideas
    boards use to put a held fund beside the funds and a held share
    beside the shares.
    """
    data = (get or _get_json)(QUOTE_URL.format(symbol=urllib.parse.quote(symbol)))
    chart = data.get("chart") or {}
    if chart.get("error"):
        desc = chart["error"].get("description") or chart["error"].get("code")
        raise PriceError(f"Yahoo has no price for {symbol}: {desc}")
    results = chart.get("result") or []
    meta = (results[0] if results else {}).get("meta") or {}
    price = meta.get("regularMarketPrice")
    currency = (meta.get("currency") or "").strip()
    stamp = meta.get("regularMarketTime")
    if price is None or not currency:
        raise PriceError(f"Yahoo answered for {symbol} without a price.")
    if len(currency) == 3 and currency[-1].islower():
        price, currency = float(price) / 100.0, currency.upper()
    when = (datetime.fromtimestamp(int(stamp), tz=timezone.utc).date().isoformat()
            if stamp else datetime.now(timezone.utc).date().isoformat())
    return {"price": float(price), "currency": currency.upper(), "as_of": when,
            "quote_type": (meta.get("instrumentType") or "").upper() or None}


# ─── What to price ───────────────────────────────────────────────────

def held_isins() -> list[str]:
    """Every ISIN with an open position somewhere. A holding sold down
    to nothing is not priced: nobody is waiting on that number."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT isin FROM transactions "
            " WHERE isin IS NOT NULL AND kind IN ('buy', 'sell') "
            "   AND quantity IS NOT NULL "
            " GROUP BY isin HAVING ABS(SUM(quantity)) > 1e-9 "
            " ORDER BY isin").fetchall()
    return [r["isin"] for r in rows]


def refresh(base_currency: str = "EUR", get=None,
            isins: list[str] | None = None) -> dict:
    """Resolve what needs resolving, quote everything held, store it.

    One security failing must not stop the rest: the error is written
    on its row for the Settings page to show, and the loop goes on. So
    this never raises for one bad ISIN — only the summary says how many
    it could not price.
    """
    # Resolved here, not in the signature: the tests swap the module's
    # fetcher for a canned one, and a default bound at import time would
    # keep the real one — and reach Yahoo from a test.
    get = get or _get_json
    isins = held_isins() if isins is None else isins
    priced, failed = 0, []
    with get_conn() as conn:
        known = {r["isin"]: dict(r) for r in conn.execute(
            "SELECT * FROM securities").fetchall()}
    for isin in isins:
        row = known.get(isin) or {"isin": isin}
        try:
            if not row.get("symbol"):
                found = resolve(isin, base_currency, get)
                row.update(symbol=found["symbol"], name=found["name"],
                           symbol_source="yahoo")
                with get_conn() as conn:
                    conn.execute(
                        "INSERT INTO securities (isin, symbol, name, symbol_source, "
                        " resolved_at, last_error) VALUES (?, ?, ?, 'yahoo', "
                        " datetime('now'), NULL) ON CONFLICT(isin) DO UPDATE SET "
                        " symbol = excluded.symbol, name = excluded.name, "
                        " symbol_source = 'yahoo', resolved_at = excluded.resolved_at, "
                        " last_error = NULL",
                        (isin, row["symbol"], row["name"]))
            q = quote(row["symbol"], get)
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO prices (isin, as_of, price, currency, fetched_at) "
                    "VALUES (?, ?, ?, ?, datetime('now')) ON CONFLICT(isin, as_of) "
                    "DO UPDATE SET price = excluded.price, currency = excluded.currency, "
                    " fetched_at = excluded.fetched_at",
                    (isin, q["as_of"], q["price"], q["currency"]))
                conn.execute("UPDATE securities SET last_error = NULL, "
                             "quote_type = COALESCE(?, quote_type) WHERE isin = ?",
                             (q["quote_type"], isin))
            priced += 1
        except PriceError as exc:
            failed.append({"isin": isin, "error": str(exc)})
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO securities (isin, last_error) VALUES (?, ?) "
                    "ON CONFLICT(isin) DO UPDATE SET last_error = excluded.last_error",
                    (isin, str(exc)))
    set_state(FETCHED_AT, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"priced": priced, "failed": failed, "held": len(isins)}


def set_symbol(isin: str, symbol: str | None) -> None:
    """Type the ticker in, or clear it so the next refresh looks it up.

    The override survives every refresh: a lookup never replaces what
    a person typed. Clearing it forgets the lookup too, so the next
    refresh starts from the ISIN.
    """
    symbol = (symbol or "").strip().upper()
    with get_conn() as conn:
        if not symbol:
            conn.execute("UPDATE securities SET symbol = NULL, symbol_source = NULL, "
                         "last_error = NULL WHERE isin = ?", (isin,))
            return
        if not _SYMBOL_RE.match(symbol):
            raise ValueError(f"{symbol!r} does not look like a ticker. Yahoo's "
                             f"look like IWDA.AS or AAPL.")
        conn.execute(
            "INSERT INTO securities (isin, symbol, symbol_source, resolved_at, "
            " last_error) VALUES (?, ?, 'manual', datetime('now'), NULL) "
            "ON CONFLICT(isin) DO UPDATE SET symbol = excluded.symbol, "
            " symbol_source = 'manual', resolved_at = excluded.resolved_at, "
            " last_error = NULL", (isin, symbol))


# ─── Reading ─────────────────────────────────────────────────────────

def latest() -> dict[str, dict]:
    """The newest price per ISIN: {isin: {price, currency, as_of, symbol}}."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.isin, p.price, p.currency, p.as_of, s.symbol, s.name
              FROM prices p
              JOIN (SELECT isin, MAX(as_of) AS as_of FROM prices GROUP BY isin) n
                ON n.isin = p.isin AND n.as_of = p.as_of
              LEFT JOIN securities s ON s.isin = p.isin
            """).fetchall()
    return {r["isin"]: dict(r) for r in rows}


def fetched_hours_ago() -> float | None:
    stamp = get_state(FETCHED_AT)
    if not stamp:
        return None
    try:
        when = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - when).total_seconds() / 3600


def is_stale(hours: float = FRESH_HOURS) -> bool:
    since = fetched_hours_ago()
    return since is None or since > hours


def status() -> list[dict]:
    """One row per held security, for the Settings page: its ticker,
    where the ticker came from, its newest price, and what went wrong
    if something did."""
    held = held_isins()
    prices = latest()
    with get_conn() as conn:
        securities = {r["isin"]: dict(r) for r in conn.execute(
            "SELECT * FROM securities").fetchall()}
        names = {r["isin"]: r["name"] for r in conn.execute(
            "SELECT isin, MAX(security_name) AS name FROM transactions "
            " WHERE isin IS NOT NULL GROUP BY isin").fetchall()}
    out = []
    for isin in held:
        sec = securities.get(isin, {})
        price = prices.get(isin)
        out.append({
            "isin": isin,
            "name": names.get(isin) or sec.get("name") or isin,
            "symbol": sec.get("symbol"),
            "manual": sec.get("symbol_source") == "manual",
            "price": price["price"] if price else None,
            "currency": price["currency"] if price else None,
            "as_of": price["as_of"] if price else None,
            "error": sec.get("last_error"),
        })
    return out
