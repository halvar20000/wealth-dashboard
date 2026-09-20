"""Trading 212, through its public API with a key of your own.

Trading 212 → Settings → API (Beta) → Generate key: give it only the
read scopes — Account data, Portfolio, History — and paste the key and
the secret here. Every request carries them as HTTP Basic auth; the
key can be revoked in the app at any time. The API is for Invest and
Stocks ISA accounts (not CFD), and works against the live account or
the practice one.

What is read, and what it becomes
---------------------------------
  * **History → orders** — every filled order: quantity, fill price,
    and what it did to the wallet (`walletImpact.netValue`, in the
    account's currency, with the currency-conversion fee and stamp
    duty listed as taxes). A buy is money out, a sale money in.
  * **History → dividends** — the cash that arrived per instrument,
    net; the gross per share is printed too, so the tax is the gap.
  * **History → transactions** — deposits, withdrawals, fees,
    interest on free cash and share lending.
  * **Positions** — what the account holds, checked against what the
    rows add up to; and the **summary**, whose free cash is the
    balance reading.

The rate limits are per account and tight — the history endpoints
allow six calls a minute — so a first sync of a long history takes a
few minutes; the client waits when it must, guided by the
`x-ratelimit-*` headers, rather than failing.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .. import settings
from ..db import get_conn
from ..importers import ParsedTxn, ParseResult, store

LIVE = "https://live.trading212.com/api/v0"
DEMO = "https://demo.trading212.com/api/v0"
KEY_FILE = "trading212_key"
SECRET_FILE = "trading212_secret"
TIMEOUT = 30
PAGE = 50
MAX_PAGES = 400


class Trading212Error(Exception):
    pass


class HoldingsDrift(Trading212Error):
    """Synced, but the positions and the rows do not agree."""


# ─── Credentials ─────────────────────────────────────────────────────

def credentials_present() -> bool:
    return ((settings.SECRETS_DIR / KEY_FILE).exists()
            and (settings.SECRETS_DIR / SECRET_FILE).exists())


def save_credentials(key: str, secret: str, environment: str = "live") -> None:
    settings.ensure_dirs()
    key, secret = (key or "").strip(), (secret or "").strip()
    if not key or not secret:
        raise ValueError("Both the API key and the secret are needed.")
    if environment not in ("live", "demo"):
        raise ValueError("The environment is live or demo.")
    for name, value in ((KEY_FILE, key), (SECRET_FILE, secret)):
        path = settings.SECRETS_DIR / name
        path.write_text(value)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    cfg = settings.load()
    cfg["trading212_environment"] = environment
    settings.save(cfg)


def forget_credentials() -> None:
    for name in (KEY_FILE, SECRET_FILE):
        try:
            (settings.SECRETS_DIR / name).unlink()
        except FileNotFoundError:
            pass


def environment() -> str:
    return settings.get("trading212_environment", "live") or "live"


def _credentials() -> tuple[str, str]:
    try:
        return ((settings.SECRETS_DIR / KEY_FILE).read_text().strip(),
                (settings.SECRETS_DIR / SECRET_FILE).read_text().strip())
    except OSError:
        raise Trading212Error("Trading 212 is not set up — add the API key under Settings.") from None


# ─── The client ──────────────────────────────────────────────────────

def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise Trading212Error(f"Could not reach Trading 212: {exc}") from exc


class Client:
    def __init__(self, key: str, secret: str, environment: str = "live", transport=None, sleep=time.sleep):
        self.base = DEMO if environment == "demo" else LIVE
        self.auth = "Basic " + base64.b64encode(f"{key}:{secret}".encode()).decode()
        self.transport = transport or _urllib_transport
        self.sleep = sleep

    def get(self, path: str, **query) -> dict | list:
        url = self.base + (path if path.startswith("/") else "/" + path)
        if query:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        headers = {"Authorization": self.auth, "Accept": "application/json", "User-Agent": "wealth-dashboard"}
        for attempt in range(6):
            status, body, resp_headers = self.transport("GET", url, headers, None)
            low = {k.lower(): v for k, v in (resp_headers or {}).items()}
            if status == 429:
                # The reset header is a Unix time; otherwise the period.
                wait = 10.0
                try:
                    reset = float(low.get("x-ratelimit-reset", 0))
                    wait = max(1.0, min(reset - time.time() + 0.5, 70.0)) if reset > 1e9 else float(low.get("x-ratelimit-period", 10))
                except ValueError:
                    pass
                self.sleep(wait)
                continue
            if status in (401, 403):
                raise Trading212Error("Trading 212 refused the key — check it under Settings, and that it has the read scopes.")
            if status != 200:
                raise Trading212Error(f"Trading 212 answered {status} for {path}.")
            try:
                return json.loads(body.decode("utf-8"))
            except ValueError:
                raise Trading212Error("Trading 212 returned something that is not JSON.") from None
        raise Trading212Error("Trading 212 kept rate-limiting the request — try again later.")

    def pages(self, path: str) -> list[dict]:
        """Every item of a cursor-paginated list, following nextPagePath."""
        items: list[dict] = []
        next_path: str | None = None
        for _ in range(MAX_PAGES):
            data = self.get(next_path) if next_path else self.get(path, limit=PAGE)
            if not isinstance(data, dict):
                break
            items.extend(data.get("items") or [])
            next_path = data.get("nextPagePath")
            if not next_path:
                break
            next_path = next_path.replace("/api/v0", "", 1)
        return items

    def summary(self) -> dict:
        return self.get("/equity/account/summary")

    def positions(self) -> list[dict]:
        data = self.get("/equity/positions")
        return data if isinstance(data, list) else data.get("items", [])

    def orders(self) -> list[dict]:
        return self.pages("/equity/history/orders")

    def dividends(self) -> list[dict]:
        return self.pages("/equity/history/dividends")

    def transactions(self) -> list[dict]:
        return self.pages("/equity/history/transactions")


def client(transport=None, sleep=time.sleep) -> Client:
    key, secret = _credentials()
    return Client(key, secret, environment(), transport, sleep)


# ─── What the API says → rows ────────────────────────────────────────

def _day(iso: str | None) -> str | None:
    if not iso:
        return None
    return iso[:10]


def _f(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def normalise(orders: list[dict], dividends: list[dict], transactions: list[dict],
              account_currency: str) -> ParseResult:
    result = ParseResult()
    ccy = account_currency.upper()[:3]
    for item in orders:
        order = item.get("order") or item
        fill = item.get("fill") or {}
        if (order.get("status") or "").upper() != "FILLED" and not fill:
            continue
        if fill.get("type") and fill["type"] != "TRADE":
            result.skipped += 1                       # a split, a spin-off: units without money
            continue
        inst = order.get("instrument") or {}
        qty = _f(fill.get("quantity")) or _f(order.get("filledQuantity")) or _f(order.get("quantity"))
        price = _f(fill.get("price"))
        impact = fill.get("walletImpact") or {}
        net = _f(impact.get("netValue"))
        if net is None:
            net = _f(order.get("filledValue")) or ((qty or 0.0) * (price or 0.0))
        date = _day(fill.get("filledAt") or order.get("createdAt"))
        if not qty or not date:
            result.problems.append(f"an order without quantity or date was left out ({order.get('ticker')})")
            continue
        side = (order.get("side") or "").upper() or ("BUY" if qty > 0 else "SELL")
        kind = "buy" if side == "BUY" else "sell"
        taxes = impact.get("taxes") or []
        fee = sum(abs(_f(t.get("quantity")) or 0.0) for t in taxes if (t.get("name") or "").upper() in ("CURRENCY_CONVERSION_FEE", "TRANSACTION_FEE", "COMMISSION_TURNOVER"))
        tax = sum(abs(_f(t.get("quantity")) or 0.0) for t in taxes if (t.get("name") or "").upper() not in ("CURRENCY_CONVERSION_FEE", "TRANSACTION_FEE", "COMMISSION_TURNOVER"))
        ref = fill.get("id") or order.get("id")
        name = inst.get("name") or order.get("ticker") or ""
        result.rows.append(ParsedTxn(
            txn_date=date, description=f"{'Kauf' if kind == 'buy' else 'Verkauf'} {name}"[:500],
            amount=round(-abs(net) if kind == "buy" else abs(net), 2),
            currency=(impact.get("currency") or ccy).upper(), kind=kind,
            external_id=f"t212:order:{ref}" if ref else None,
            isin=inst.get("isin") or None, security_name=name or None,
            quantity=abs(qty) if kind == "buy" else -abs(qty), price=abs(price) if price else None,
            fee=round(fee, 2) or None, tax=round(tax, 2) or None,
        ))
    for d in dividends:
        inst = d.get("instrument") or {}
        amount = _f(d.get("amount"))
        date = _day(d.get("paidOn"))
        if amount is None or not date:
            continue
        gross = (_f(d.get("grossAmountPerShare")) or 0.0) * (_f(d.get("quantity")) or 0.0)
        tax = round(gross - amount, 2) if gross and gross > amount and (d.get("currency") or ccy).upper() == (inst.get("currency") or d.get("tickerCurrency") or "").upper() else None
        kind = "interest" if (d.get("type") or "").upper() == "INTEREST" else "dividend"
        result.rows.append(ParsedTxn(
            txn_date=date, description=f"{'Zinsen' if kind == 'interest' else 'Dividende'} {inst.get('name') or d.get('ticker') or ''}"[:500],
            amount=round(amount, 2), currency=(d.get("currency") or ccy).upper(), kind=kind,
            external_id=f"t212:div:{d.get('reference')}" if d.get("reference") else None,
            isin=inst.get("isin") or None, security_name=inst.get("name") or d.get("ticker"),
            quantity=None, tax=tax if tax and tax > 0 else None,
        ))
    for t in transactions:
        amount = _f(t.get("amount"))
        date = _day(t.get("dateTime"))
        ttype = (t.get("type") or "").upper()
        if amount is None or not date:
            continue
        kind = {"DEPOSIT": "deposit", "WITHDRAW": "withdrawal", "FEE": "fee",
                "INTEREST_ON_FREE_CASH": "interest", "LENDING_INTEREST": "interest", "TRANSFER": "transfer"}.get(ttype, "other")
        if kind == "transfer":
            kind = "deposit" if amount > 0 else "withdrawal"
        result.rows.append(ParsedTxn(
            txn_date=date, description={"deposit": "Einzahlung", "withdrawal": "Auszahlung", "fee": "Gebühr", "interest": "Zinsen"}.get(kind, ttype.title())[:500],
            amount=round(amount, 2), currency=(t.get("currency") or ccy).upper(), kind=kind,
            external_id=f"t212:cash:{t.get('reference')}" if t.get("reference") else None,
        ))
    return result


# ─── Sync ────────────────────────────────────────────────────────────

def sync_link(link: dict, api: Client | None = None) -> int:
    api = api or client()
    parsed = normalise(api.orders(), api.dividends(), api.transactions(), link["account_currency"])
    summary = api.summary()
    cash = (summary.get("cash") or {})
    free = _f(cash.get("availableToTrade"))
    if free is not None:
        parsed.closing_balance = {"amount": round(free + (_f(cash.get("reservedForOrders")) or 0.0), 2),
                                  "currency": (summary.get("currency") or link["account_currency"]).upper(),
                                  "as_of": datetime.now(timezone.utc).date().isoformat()}
    report = store(link["account_id"], parsed, "trading212")
    with get_conn() as conn:
        held = {r["isin"]: r["q"] for r in conn.execute(
            "SELECT isin, SUM(quantity) AS q FROM transactions WHERE account_id = ? "
            "AND isin IS NOT NULL AND quantity IS NOT NULL GROUP BY isin", (link["account_id"],))}
    drift = []
    for p in api.positions():
        inst = p.get("instrument") or {}
        isin, qty = inst.get("isin"), _f(p.get("quantity")) or 0.0
        if not isin:
            continue
        have = held.get(isin, 0.0)
        if abs(have - qty) > 1e-6:
            drift.append(f"{inst.get('name') or p.get('ticker')}: Trading 212 says {qty:g}, the rows add up to {have:g}")
    if drift:
        raise HoldingsDrift("Synced, but the holdings do not add up — " + "; ".join(drift)
                            + ". A split or a transfer in is units without an order; add it by hand.")
    return report["inserted"]


def describe() -> dict:
    return {"configured": credentials_present(), "environment": environment()}


def check(transport=None, sleep=time.sleep) -> dict:
    api = client(transport, sleep)
    s = api.summary()
    return {"ok": True, "currency": s.get("currency"), "cash": (s.get("cash") or {}).get("availableToTrade"),
            "invested": (s.get("investments") or {}).get("currentValue"), "total": s.get("totalValue")}
