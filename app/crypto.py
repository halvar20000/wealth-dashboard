"""The crypto page: every coin held, its price, and what the wallet is worth.

A coin is a holding like any other — keyed `CRYPTO:BTC`, units from the
rows that moved them, priced by the feed as Yahoo's `BTC-EUR` — so the
page is a view, not a second ledger. What it adds is the chart people
actually open a bitcoin page for: the price over a range, or the wallet's
value over it, with the change over the range in money and in percent.

The price series comes from Yahoo per request and is kept an hour: the
ranges reach back years, further than the backfilled daily prices go,
and a page opened twice in an hour should not ask twice. The wallet
series is the price series times the units held on each day, from the
same rows the security page lists.
"""

from __future__ import annotations

import time
from bisect import bisect_right
from datetime import date, timedelta

from . import people, prices
from .db import get_conn
from .importers import positions
from .prices import CRYPTO_PREFIX

RANGES = {"1m": 31, "3m": 92, "1y": 366, "5y": 5 * 366, "max": None}
_cache: dict[tuple, tuple[float, list]] = {}
CACHE_S = 3600


def coins(base_currency: str = "EUR", account_ids: list[int] | None = None) -> list[dict]:
    """Every coin held under the current view, with the figures the KPI
    strip shows. Aggregated across accounts the way the portfolio is."""
    only, params = people.sql_in(account_ids, "id")
    with get_conn() as conn:
        accounts = [dict(r) for r in conn.execute(
            f"SELECT id, name FROM accounts WHERE 1=1{only}", params).fetchall()]
    market = prices.latest()
    out: dict[str, dict] = {}
    for acct in accounts:
        for pos in positions(acct["id"]):
            if not pos["isin"].startswith(CRYPTO_PREFIX):
                continue
            c = out.setdefault(pos["isin"], {
                "isin": pos["isin"], "code": pos["isin"][len(CRYPTO_PREFIX):],
                "name": pos["name"], "quantity": 0.0, "net_invested": 0.0,
                "accounts": [], "currency": pos["currency"] or base_currency})
            c["quantity"] += pos["quantity"]
            c["net_invested"] += pos["net_invested"] or 0.0
            c["accounts"].append(acct["name"])
    for c in out.values():
        m = market.get(c["isin"])
        c["price"] = m["price"] if m else None
        c["price_as_of"] = m["as_of"] if m else None
        c["price_currency"] = m["currency"] if m else None
        c["symbol"] = (m or {}).get("symbol") or f"{c['code']}-{base_currency}"
        c["value"] = c["quantity"] * m["price"] if m else None
        c["avg_cost"] = (c["net_invested"] / c["quantity"]) if c["quantity"] > 1e-12 and c["net_invested"] > 0 else None
        c["gain"] = (c["value"] - c["net_invested"]) if c["value"] is not None else None
        c["gain_pct"] = (c["gain"] / c["net_invested"] * 100) if c["gain"] is not None and c["net_invested"] > 0 else None
    return sorted(out.values(), key=lambda c: -(c["value"] or 0))


def price_series(symbol: str, range_key: str, get=None, today: date | None = None) -> list[tuple[str, float, str]]:
    """Daily closes over the range, from Yahoo, cached for an hour."""
    today = today or date.today()
    days = RANGES.get(range_key, 31)
    since = (today - timedelta(days=days)).isoformat() if days else "2010-01-01"
    key = (symbol, range_key, since)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_S:
        return hit[1]
    rows = prices.history(symbol, since, get)
    _cache[key] = (time.time(), rows)
    return rows


def chart(isin: str, range_key: str, mode: str, base_currency: str = "EUR",
          account_ids: list[int] | None = None, get=None, today: date | None = None) -> dict:
    """{points: [{date, value}], currency, change, change_pct, units}."""
    with get_conn() as conn:
        sec = conn.execute("SELECT symbol FROM securities WHERE isin = ?", (isin,)).fetchone()
    symbol = (sec["symbol"] if sec and sec["symbol"] else None) \
        or f"{isin[len(CRYPTO_PREFIX):]}-{base_currency}"
    series = price_series(symbol, range_key, get, today)
    if not series:
        return {"points": [], "currency": None, "change": None, "change_pct": None}
    currency = series[-1][2]
    if mode == "wallet":
        only, params = people.sql_in(account_ids, "account_id")
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT txn_date, quantity FROM transactions WHERE isin = ? AND quantity IS NOT NULL"
                f"{only} ORDER BY txn_date, id", [isin, *params]).fetchall()
        days, qty, q = [], [], 0.0
        for r in rows:
            q += r["quantity"] or 0.0
            days.append(r["txn_date"]); qty.append(q)
        points = []
        for day, price, _ in series:
            i = bisect_right(days, day)
            held = qty[i - 1] if i else 0.0
            points.append({"date": day, "value": held * price, "units": held})
    else:
        points = [{"date": day, "value": price} for day, price, _ in series]
    first = next((p["value"] for p in points if p["value"]), None)
    last = points[-1]["value"]
    change = (last - first) if first is not None and last is not None else None
    return {"points": points, "currency": currency, "symbol": symbol,
            "change": change,
            "change_pct": (change / first * 100) if change is not None and first else None,
            "from": points[0]["date"], "to": points[-1]["date"]}


def recent(isin: str, account_ids: list[int] | None = None, limit: int = 25) -> list[dict]:
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t JOIN accounts a ON a.id = t.account_id "
            f"WHERE t.isin = ?{only} ORDER BY t.txn_date DESC, t.id DESC LIMIT ?",
            [isin, *params, limit]).fetchall()]
