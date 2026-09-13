"""Exchange rates, from the European Central Bank.

The ECB publishes euro reference rates every TARGET business day, free,
without a key, without a rate limit and without an account — which is
the whole reason they are the source here. A dashboard that needs an API
key before it can add a dollar to a euro is a dashboard that stops
working the day somebody's free tier ends.

Three things worth knowing about them:

**They are reference rates, not tradeable ones.** Published around 16:00
CET against the euro. Your bank did not give you this rate and your
broker will not either. For "what is my net worth", that is the right
kind of number; for "what will I get if I sell", it is not, and nothing
here pretends otherwise.

**They are euro-based.** Everything else is a cross rate through the
euro, which is exactly how this module computes it — USD to CHF is USD
to EUR to CHF. That introduces no error the ECB has not already made.

**There is no rate at the weekend.** No publication on a Saturday means
Sunday uses Friday's, which is correct rather than a gap: nothing traded
in between. Every conversion therefore carries the date of the rate it
used, and the pages say it.

Ninety days of history are fetched, not just today, because it is one
file either way and the history is what a balance chart will want. The
ECB's full series back to 1999 is an eight-megabyte download; if a page
ever needs 2014, that is the day to fetch it, not before.
"""

from __future__ import annotations

import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone

from .db import get_conn, get_state, set_state

# Ninety days in one file, about 70 KB. The daily file is smaller and
# would need a second endpoint for the history, which is a second thing
# to break for no gain.
ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"

# The euro is the unit these rates are quoted in, so it is never a row.
BASE = "EUR"

# Refreshed at most this often. The ECB publishes once a day; asking
# more often is asking a public service for something it did not change.
FRESH_HOURS = 20

# When we last asked, which is not the same question as how old the
# newest rate is. On a Monday morning the freshest rate in existence is
# Friday's, and calling that stale sends somebody looking for a bug in a
# weekend.
FETCHED_AT = "fx_fetched_at"

# Long enough to survive a NAS on a slow link, short enough that a
# hanging request does not hold a thread for the afternoon.
TIMEOUT = 20


class FxError(RuntimeError):
    """Something went wrong fetching or reading the rates, in a sentence
    meant for the person who clicked the button."""


# ─── Fetching ────────────────────────────────────────────────────────

def parse(xml_text: str) -> dict[str, dict[str, float]]:
    """`{"2026-09-09": {"USD": 1.1652, …}, …}` from the ECB's XML.

    Read by attribute rather than by path: the document is namespaced
    twice over, and a namespace URL that changes would break a path
    lookup while the attributes stay exactly where they are.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise FxError(f"The ECB sent something that is not XML: {exc}") from exc

    days: dict[str, dict[str, float]] = {}
    for node in root.iter():
        when = node.get("time")
        if not when:
            continue
        rates: dict[str, float] = {}
        for child in node:
            ccy, rate = child.get("currency"), child.get("rate")
            if not ccy or not rate or ccy == BASE:
                continue
            try:
                value = float(rate)
            except ValueError:
                continue                  # one bad cell is not a bad day
            if value > 0:
                rates[ccy.upper()] = value
        if rates:
            days[when] = rates
    if not days:
        raise FxError("The ECB's file had no rates in it.")
    return days


def fetch(url: str = ECB_URL) -> str:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise FxError(f"The ECB refused the request ({exc.code}). "
                      f"Try again later.") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise FxError(f"Could not reach the ECB: {exc}. This machine may "
                      f"have no way out to the internet, which is fine — "
                      f"amounts in other currencies stay unconverted.") from exc


def store(days: dict[str, dict[str, float]]) -> int:
    """Upsert. Re-fetching an overlapping window is the normal case."""
    written = 0
    with get_conn() as conn:
        for when, rates in days.items():
            for ccy, per_eur in rates.items():
                conn.execute(
                    "INSERT INTO fx_rates (as_of, currency, per_eur) "
                    "VALUES (?, ?, ?) ON CONFLICT(as_of, currency) "
                    "DO UPDATE SET per_eur = excluded.per_eur",
                    (when, ccy, per_eur))
                written += 1
    return written


def refresh(url: str = ECB_URL) -> dict:
    """Fetch, parse, store. Raises FxError with something readable."""
    days = parse(fetch(url))
    store(days)
    set_state(FETCHED_AT, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    newest = max(days)
    return {"days": len(days), "currencies": len(days[newest]),
            "latest": newest}


# The whole history since 1999, one file of a few megabytes, fetched
# once — and only when a row in the books predates the ninety days:
# a share bought in 2022 and quoted in dollars needs 2022's rate to
# say what it cost in dollars.
ECB_HIST_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
BACKFILLED = "fx_backfilled"


def needs_backfill() -> bool:
    """A transaction or a price older than the oldest rate on record,
    and the whole history not fetched yet."""
    if get_state(BACKFILLED):
        return False
    with get_conn() as conn:
        oldest_rate = conn.execute("SELECT MIN(as_of) AS d FROM fx_rates").fetchone()["d"]
        oldest_row = conn.execute(
            "SELECT MIN(d) AS d FROM (SELECT MIN(txn_date) AS d FROM transactions "
            "UNION ALL SELECT MIN(as_of) FROM prices)").fetchone()["d"]
    return bool(oldest_rate and oldest_row and oldest_row < oldest_rate)


def backfill(url: str = ECB_HIST_URL) -> dict:
    """Fetch and store every rate the ECB has ever published."""
    days = parse(fetch(url))
    store(days)
    set_state(BACKFILLED, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"days": len(days), "oldest": min(days)}


# ─── Reading ─────────────────────────────────────────────────────────

def latest_date() -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT MAX(as_of) AS d FROM fx_rates").fetchone()
    return row["d"] if row and row["d"] else None


def rates_on(when: str | None = None) -> tuple[str | None, dict[str, float]]:
    """The rates of the newest publication day at or before `when`.

    One day, not a mixture: taking USD from Tuesday and CHF from Friday
    because that is what happens to be stored would produce a cross rate
    that never existed.
    """
    with get_conn() as conn:
        if when:
            row = conn.execute(
                "SELECT MAX(as_of) AS d FROM fx_rates WHERE as_of <= ?",
                (str(when)[:10],)).fetchone()
        else:
            row = conn.execute("SELECT MAX(as_of) AS d FROM fx_rates").fetchone()
        as_of = row["d"] if row else None
        if not as_of:
            return None, {}
        rates = {r["currency"]: r["per_eur"] for r in conn.execute(
            "SELECT currency, per_eur FROM fx_rates WHERE as_of = ?",
            (as_of,)).fetchall()}
    rates[BASE] = 1.0
    return as_of, rates


def convert(amount: float | None, frm: str, to: str,
            when: str | None = None) -> tuple[float | None, str | None]:
    """`(converted, the date of the rate)`, or `(None, None)`.

    None rather than a guess, in both directions: an unknown currency and
    an empty rate table both mean "this app cannot tell you", and the
    pages are built to say that instead of showing a number.
    """
    if amount is None:
        return None, None
    frm, to = (frm or BASE).upper(), (to or BASE).upper()
    if frm == to:
        return amount, None
    as_of, rates = rates_on(when)
    if frm not in rates or to not in rates:
        return None, None
    return amount / rates[frm] * rates[to], as_of


def known_currencies() -> set[str]:
    _as_of, rates = rates_on()
    return set(rates)


def fetched_hours_ago() -> float | None:
    """How long since we last asked the ECB. None when we never have."""
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
    """Whether it is worth asking again — not whether the rate is old.

    The freshest rate that exists on a Monday morning is Friday's, and
    there is nothing to fix about that.
    """
    since = fetched_hours_ago()
    return since is None or since > hours


def status() -> dict:
    """What the Settings page shows about the rates."""
    as_of, rates = rates_on()
    return {"as_of": as_of,
            "currencies": sorted(c for c in rates if c != BASE),
            "count": max(len(rates) - 1, 0),
            "stale": is_stale(),
            "fetched_hours_ago": fetched_hours_ago(),
            # Shown so that "Friday's rate" on a Monday reads as the
            # ECB's schedule rather than as something not working.
            "weekend": date.today().weekday() >= 5}
