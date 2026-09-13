"""The dividend calendar: what was paid out, and what is due.

Two halves. *Received*: every dividend and interest row on a
security, month by month, turned into the base currency at its day's
rate — the trailing twelve months, the years, the payers. *Expected*:
what each holding paid per share over the last twelve months, as
Yahoo lists it by ex-date, times the units held today, each payment
projected forward a year on its own date — so a quarterly payer shows
four times in the coming twelve months, in the months it actually
pays. That is a calendar, not a forecast: it assumes every payer
keeps paying what it paid, which is the assumption a dividend
investor lives by and knows the limits of.

Per-share history is fetched from Yahoo at most once a day per
symbol and kept in `dividend_events`; a symbol Yahoo has no
distribution data for is simply absent from the expected half.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from . import prices, yahoo
from .db import get_conn, get_state, set_state

FETCHED = "dividends_fetched:"
FRESH_HOURS = 24


def refresh(get=None, isins: list[str] | None = None, force: bool = False) -> dict:
    """Per-share distributions of every held security with a symbol,
    fetched when older than a day."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    isins = prices.held_isins() if isins is None else isins
    with get_conn() as conn:
        symbols = {r["isin"]: r["symbol"] for r in conn.execute(
            "SELECT isin, symbol FROM securities WHERE symbol IS NOT NULL").fetchall()}
    done, failed = 0, []
    for isin in isins:
        symbol = symbols.get(isin)
        if not symbol or isin.startswith(prices.CRYPTO_PREFIX):
            continue
        last = get_state(FETCHED + isin)
        if last and not force:
            try:
                age = (now - datetime.fromisoformat(last)).total_seconds() / 3600
                if age < FRESH_HOURS:
                    continue
            except ValueError:
                pass
        try:
            hist = yahoo.history(symbol, years=2.2, interval="1mo", get=get)
        except Exception as exc:                        # noqa: BLE001
            failed.append({"isin": isin, "error": str(exc)})
            set_state(FETCHED + isin, now.isoformat(timespec="seconds"))
            continue
        with get_conn() as conn:
            for day, amount in hist.get("dividends") or []:
                conn.execute("INSERT OR REPLACE INTO dividend_events (isin, ex_date, amount, currency) VALUES (?, ?, ?, ?)",
                             (isin, day, amount, hist.get("currency")))
        set_state(FETCHED + isin, now.isoformat(timespec="seconds"))
        done += 1
    return {"fetched": done, "failed": failed}


def is_stale() -> bool:
    """Any held symbol without a fetch in the last day."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        symbols = {r["isin"] for r in conn.execute("SELECT isin FROM securities WHERE symbol IS NOT NULL")}
    for isin in prices.held_isins():
        if isin not in symbols or isin.startswith(prices.CRYPTO_PREFIX):
            continue
        last = get_state(FETCHED + isin)
        if not last:
            return True
        try:
            if (now - datetime.fromisoformat(last)).total_seconds() / 3600 >= FRESH_HOURS:
                return True
        except ValueError:
            return True
    return False


def _shift_year(d: date) -> date:
    return date(d.year + 1, d.month, min(d.day, monthrange(d.year + 1, d.month)[1]))


def calendar(base_currency: str, account_ids: list[int] | None, summary: dict,
             today: date | None = None) -> dict:
    """Received and expected, by month and by security, in the base
    currency. `summary` is overview.summary(), for the holdings."""
    from . import people
    today = today or date.today()
    convert = prices.in_currency(base_currency)
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.txn_date, t.amount, t.currency, t.isin, t.kind, MAX(t.security_name) AS name "
            f"FROM transactions t WHERE t.isin IS NOT NULL AND t.kind IN ('dividend', 'interest'){only} "
            f"GROUP BY t.id ORDER BY t.txn_date", params)]
        events = [dict(r) for r in conn.execute("SELECT * FROM dividend_events ORDER BY isin, ex_date")]
    # Received.
    by_month: dict[str, float] = {}
    by_year: dict[str, float] = {}
    by_isin: dict[str, dict] = {}
    since_12m = (today - timedelta(days=365)).isoformat()
    last_12m = 0.0
    for r in rows:
        amt = convert(r["amount"], r["currency"], r["txn_date"])
        if amt is None:
            continue
        m, y = r["txn_date"][:7], r["txn_date"][:4]
        by_month[m] = by_month.get(m, 0.0) + amt
        by_year[y] = by_year.get(y, 0.0) + amt
        d = by_isin.setdefault(r["isin"], {"isin": r["isin"], "name": r["name"] or r["isin"], "received_12m": 0.0,
                                             "received_all": 0.0, "count": 0, "last": None})
        d["received_all"] += amt
        d["count"] += 1
        d["last"] = r["txn_date"]
        if r["txn_date"] >= since_12m:
            d["received_12m"] += amt
            last_12m += amt
    # Expected: last year's per-share payments, times the units held, a year on.
    held = {h["isin"]: h for h in summary["holdings"] if h.get("quantity")}
    names = {h["isin"]: h.get("name") for h in summary["holdings"]}
    expected_by_month: dict[str, float] = {}
    expected_by_isin: dict[str, dict] = {}
    upcoming = []
    horizon = (today + timedelta(days=365)).isoformat()
    for ev in events:
        h = held.get(ev["isin"])
        if not h or ev["ex_date"] < since_12m or ev["ex_date"] > today.isoformat():
            continue
        nxt = _shift_year(date.fromisoformat(ev["ex_date"]))
        if nxt.isoformat() > horizon or nxt < today:
            continue
        per_share = convert(ev["amount"], ev["currency"], today.isoformat())
        if per_share is None:
            continue
        amount = per_share * h["quantity"]
        m = nxt.isoformat()[:7]
        expected_by_month[m] = expected_by_month.get(m, 0.0) + amount
        d = expected_by_isin.setdefault(ev["isin"], {"isin": ev["isin"], "name": names.get(ev["isin"]) or ev["isin"],
                                                     "expected_12m": 0.0, "payments": 0, "per_share": 0.0,
                                                     "next": None, "currency": ev["currency"]})
        d["expected_12m"] += amount
        d["payments"] += 1
        d["per_share"] += ev["amount"]
        if d["next"] is None or nxt.isoformat() < d["next"]:
            d["next"] = nxt.isoformat()
        upcoming.append({"date": nxt.isoformat(), "isin": ev["isin"], "name": names.get(ev["isin"]) or ev["isin"],
                         "amount": amount, "per_share": ev["amount"], "currency": ev["currency"]})
    upcoming.sort(key=lambda u: u["date"])
    expected_12m = sum(expected_by_month.values())
    value = sum(h["value_base"] or 0.0 for h in summary["holdings"] if h.get("value_base"))
    # The calendar: twelve months back, twelve ahead.
    months = []
    first = date(today.year, today.month, 1)
    for k in range(-11, 13):
        y, m = first.year + (first.month - 1 + k) // 12, (first.month - 1 + k) % 12 + 1
        key = f"{y:04d}-{m:02d}"
        months.append({"month": key, "received": by_month.get(key, 0.0) if k <= 0 else 0.0,
                       "expected": expected_by_month.get(key, 0.0) if k >= 0 else 0.0, "ahead": k > 0})
    # Every security: the received and the expected side by side.
    securities = {}
    for isin, d in by_isin.items():
        securities[isin] = {**d, "expected_12m": 0.0, "payments": 0, "per_share": 0.0, "next": None, "held": isin in held}
    for isin, d in expected_by_isin.items():
        securities.setdefault(isin, {"isin": isin, "name": d["name"], "received_12m": 0.0, "received_all": 0.0,
                                     "count": 0, "last": None, "held": True}).update(
            {k: d[k] for k in ("expected_12m", "payments", "per_share", "next", "currency")})
    sec_list = sorted(securities.values(), key=lambda d: -(d["expected_12m"] + d["received_12m"]))
    return {"received_12m": last_12m, "expected_12m": expected_12m,
            "yield_on_value": (expected_12m / value) if value > 0 else None, "value": value,
            "by_year": [{"year": y, "amount": v} for y, v in sorted(by_year.items(), reverse=True)],
            "months": months, "securities": sec_list, "upcoming": upcoming[:40],
            "received_all": sum(by_year.values()), "payers": len([s for s in sec_list if s["expected_12m"] > 0])}
