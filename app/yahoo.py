"""Yahoo Finance, the two endpoints the Share Ideas boards need.

`prices.py` already talks to Yahoo for a last price, keylessly, through
the *chart* endpoint. The screener needs two more things, and neither
costs a key, an account or a dependency:

  * **fundamentals** — `quoteSummary`, where the P/E, the yield, the
    payout ratio, the margins and the fund's expense ratio live. It is
    the one Yahoo endpoint that refuses an anonymous request: it wants a
    session cookie and a "crumb" that goes with it. The handshake is two
    requests (one for the cookie, one for the crumb), done once and kept
    for the run. This is precisely what the yfinance library does; the
    library is not used because it drags pandas and numpy into an image
    whose selling point is four requirements, and because a NAS that
    lost `/usr` on reboot cannot import it anyway.
  * **history** — the chart endpoint again, asked for six years of weekly
    bars with `events=div`. One reply carries the *adjusted* closes (the
    ETF board's growth column, which must be total return), the
    distributions actually paid (the dividend ETF board's yield), the
    listing currency and the instrument type.

Every value in a `quoteSummary` reply is wrapped — `{"raw": 0.034,
"fmt": "3.40%"}` — and an absent one is an empty `{}`. `_flatten()`
unwraps the first and drops the second, so the screener sees a flat
dict with the same keys the yfinance library exposes and its unit
handling (`screener.normalise()`) applies unchanged. That matters: the
raw `dividendYield` is a fraction, `debtToEquity` a percent,
`fiveYearAvgDividendYield` a percent, and the screener decides per value
rather than trusting any of it.

Nothing here reaches the network on import; the refresh thread and the
Settings button are the only callers, and every function takes an
injectable `get` so the test suite runs with canned replies.
"""

from __future__ import annotations

import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .prices import PriceError, TIMEOUT, USER_AGENT

COOKIE_URL = "https://fc.yahoo.com"
CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"
CONSENT_URL = "https://guce.yahoo.com/consent"
SUMMARY_URL = ("https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
               "?modules={modules}&crumb={crumb}")
CHART_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
             "?period1={p1}&period2={p2}&interval={interval}&events=div")

SHARE_MODULES = "price,summaryDetail,defaultKeyStatistics,financialData,assetProfile"
FUND_MODULES = "price,summaryDetail,defaultKeyStatistics,fundProfile"

# A cookie jar lasts a while; Yahoo's `A3` cookie is good for a year.
# Re-done when the crumb is refused, which is the only signal there is.
_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))
_crumb: str | None = None


class YahooError(PriceError):
    """A fetch that failed, in a sentence for the row's `last_error`."""


# ─── Plumbing ────────────────────────────────────────────────────────

def _open(url: str, data: bytes | None = None) -> bytes:
    request = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with _opener.open(request, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # The cookie request answers 404 by design; that is not a failure.
        if exc.code == 404 and url == COOKIE_URL:
            return b""
        raise YahooError(f"Yahoo refused the request ({exc.code}).") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise YahooError(f"Could not reach Yahoo: {exc}") from exc


def _get_json(url: str) -> dict:
    try:
        return json.loads(_open(url).decode("utf-8"))
    except ValueError as exc:
        raise YahooError("Yahoo answered with something that is not JSON.") from exc


def _handshake() -> str:
    """Cookie, then crumb. Two strategies, tried in order.

    The plain one — a request to fc.yahoo.com sets the cookie, and the
    crumb endpoint answers with a short token — is what works from most
    places. From some EU addresses Yahoo instead wants the GDPR consent
    page agreed to first; that form is filled in and posted, and the
    crumb asked for again. The consent path is the yfinance library's,
    transcribed; it is a fallback, not the expectation.
    """
    global _crumb
    _jar.clear()
    _open(COOKIE_URL)
    crumb = _open(CRUMB_URL).decode("utf-8", "replace").strip()
    if not crumb or "<" in crumb or len(crumb) > 40:
        page = _open(CONSENT_URL).decode("utf-8", "replace")
        token = re.search(r'name="csrfToken"\s+value="([^"]+)"', page)
        sid = re.search(r'name="sessionId"\s+value="([^"]+)"', page)
        if not (token and sid):
            raise YahooError("Yahoo wants a consent form this app cannot find "
                             "its way through.")
        form = urllib.parse.urlencode(
            [("agree", "agree"), ("agree", "agree"), ("consentUUID", "default"),
             ("sessionId", sid.group(1)), ("csrfToken", token.group(1)),
             ("originalDoneUrl", "https://finance.yahoo.com/"),
             ("namespace", "yahoo")]).encode()
        _open(f"https://consent.yahoo.com/v2/collectConsent?sessionId={sid.group(1)}",
              form)
        _open(f"https://guce.yahoo.com/copyConsent?sessionId={sid.group(1)}")
        crumb = _open(CRUMB_URL).decode("utf-8", "replace").strip()
    if not crumb or "<" in crumb:
        raise YahooError("Yahoo did not hand out a session crumb.")
    _crumb = crumb
    return crumb


def _flatten(modules: dict) -> dict:
    """quoteSummary's per-module, `{raw, fmt}`-wrapped reply → one flat
    dict of plain values, under the names the screener expects.

    A nested block such as `feesExpensesInvestment` is flattened one
    level so its expense ratio lands beside the others. Later modules
    do not overwrite earlier ones: `price` comes first and its market
    cap is the one to keep.
    """
    def unwrap(v):
        if isinstance(v, dict):
            if "raw" in v:
                return v["raw"]
            if not v:
                return None
        return v

    out: dict = {}
    for _name, block in (modules or {}).items():
        if not isinstance(block, dict):
            continue
        for key, value in block.items():
            v = unwrap(value)
            if isinstance(v, dict):                # a nested block
                for k2, v2 in v.items():
                    v2 = unwrap(v2)
                    if v2 is not None and not isinstance(v2, (dict, list)):
                        out.setdefault(k2, v2)
                continue
            if v is not None and not isinstance(v, list):
                out.setdefault(key, v)
    # The names the screener (and the yfinance library) use for these.
    if "exchangeName" in out:
        out.setdefault("fullExchangeName", out["exchangeName"])
    if "family" in out:
        out.setdefault("fundFamily", out["family"])
    if "categoryName" in out:
        out.setdefault("category", out["categoryName"])
    return out


# ─── The two calls ───────────────────────────────────────────────────

def fundamentals(symbol: str, modules: str = SHARE_MODULES) -> dict:
    """Everything `quoteSummary` knows about one symbol, flattened.

    A refused crumb — Yahoo rotates them — is answered by one fresh
    handshake and one retry; a second refusal is the row's error.
    """
    crumb = _crumb or _handshake()
    for attempt in (1, 2):
        url = SUMMARY_URL.format(symbol=urllib.parse.quote(symbol),
                                 modules=modules, crumb=urllib.parse.quote(crumb))
        try:
            data = _get_json(url)
        except YahooError as exc:
            if attempt == 1 and ("401" in str(exc) or "403" in str(exc)):
                crumb = _handshake()
                continue
            raise
        summary = data.get("quoteSummary") or {}
        if summary.get("error"):
            desc = summary["error"].get("description") or summary["error"].get("code")
            raise YahooError(f"Yahoo has nothing for {symbol}: {desc}")
        results = summary.get("result") or []
        if not results:
            raise YahooError(f"Yahoo has nothing for {symbol}.")
        return _flatten(results[0])
    raise YahooError(f"Yahoo refused {symbol} twice.")     # pragma: no cover


def history(symbol: str, years: float = 6.0, interval: str = "1wk",
            get=None) -> dict:
    """Adjusted weekly closes and paid distributions for one symbol.

    Returns {closes: [(YYYY-MM-DD, adjclose)], dividends: [(YYYY-MM-DD,
    amount)], currency, quote_type}. The closes are Yahoo's `adjclose`
    — distributions reinvested — which is the only series on which an
    accumulating and a distributing class of the same fund compare
    equal. The dividends are the discrete payments, in the listing
    currency, ex-date stamped; Yahoo lists the next declared one too,
    and the screener drops anything dated after today.
    """
    now = int(time.time())
    url = CHART_URL.format(symbol=urllib.parse.quote(symbol),
                           p1=now - int(years * 365.25 * 86400), p2=now,
                           interval=interval)
    data = (get or _get_json)(url)
    chart = data.get("chart") or {}
    if chart.get("error"):
        desc = chart["error"].get("description") or chart["error"].get("code")
        raise YahooError(f"Yahoo has no history for {symbol}: {desc}")
    results = chart.get("result") or []
    if not results:
        raise YahooError(f"Yahoo has no history for {symbol}.")
    r = results[0]
    meta = r.get("meta") or {}
    stamps = r.get("timestamp") or []
    ind = r.get("indicators") or {}
    adj = ((ind.get("adjclose") or [{}])[0].get("adjclose")
           or (ind.get("quote") or [{}])[0].get("close") or [])

    def day(ts) -> str:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()

    closes = [(day(ts), float(c)) for ts, c in zip(stamps, adj)
              if c is not None and c == c and c > 0]
    divs = []
    for ev in ((r.get("events") or {}).get("dividends") or {}).values():
        amount, ts = ev.get("amount"), ev.get("date")
        if amount and ts and amount > 0:
            divs.append((day(ts), float(amount)))
    divs.sort()
    return {"closes": closes, "dividends": divs,
            "currency": (meta.get("currency") or "").strip() or None,
            "quote_type": (meta.get("instrumentType") or "").upper() or None}
