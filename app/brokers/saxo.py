"""Saxo Bank, through its OpenAPI with an application of your own.

Saxo is OAuth2 — the same shape as connecting a bank, with one twist
that decides the whole design: **the tokens are short-lived**. An access
token lasts twenty minutes; the refresh token that renews it lasts about
an hour, is single-use, and every renewal hands back a new one and
kills the old. A sync once a day cannot keep itself logged in. So:

  * a **keep-alive thread** renews the chain every five minutes for as
    long as the app runs (`keepalive()` — main.py starts it);
  * a sync uses whatever access token the chain has, renewing first if
    it is about to expire;
  * when the chain has lapsed — the app was down for more than an hour,
    Saxo had a bad day — the account page says so, and connecting again
    is one click and a Saxo login. Nothing is lost: the history is in
    the database, the connection is the only thing that expired.

Setting up, once
----------------
1. At <https://www.developer.saxo/openapi/appmanagement> create an app:
   environment **Live** (or **Simulation** to try it against Saxo's demo
   account first — the toggle under Settings selects which), grant type
   **Authorization Code**, redirect URL exactly the one Settings shows —
   the dashboard's own address plus `/saxo/callback`.
2. Paste the **AppKey** and **AppSecret** under Settings. The secret is
   kept 0600 beside the bank key and never shown again.
3. On an account, press **Connect Saxo**: Saxo's login, then back here.
   A client with several Saxo accounts gets one dashboard account each,
   because two balances added together is not a balance.

What is read
------------
  * `/port/v1/balances` — the cash, per account, as the balance reading.
  * `/cs/v1/reports/trades` — every fill of the last 400 days: a buy
    or a sale with quantity, price and the booked amount in the account
    currency, net of costs.
  * `/cs/v1/reports/bookings` — dividends, interest, fees, taxes,
    deposits and withdrawals.
  * `/port/v1/positions` — what Saxo says is held, against what the
    trades add up to. A position that was transferred in has no
    purchase in Saxo's history, so the difference is recorded as a
    transfer with the quantity and Saxo's average open price — then the
    holding is right, and the next sync finds no difference.

Saxo does not hand out ISINs (they are licensed market data), so a
Saxo instrument is keyed `SAXO:<uic>` and given the Yahoo ticker its
symbol and exchange imply — `IWDA:xams` is `IWDA.AS` — which is what
the price feed then quotes. The ticker can be corrected under Settings
like any other, and a security bought at Saxo and at another broker is
two holdings rather than one, which the page shows as such.
"""

from __future__ import annotations

import base64
import json
import secrets as _secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from .. import settings
from ..db import get_conn, get_state, set_state
from ..importers import ParsedTxn, ParseResult, store

ENVIRONMENTS = {
    "live": {"auth": "https://live.logonvalidation.net",
             "api": "https://gateway.saxobank.com/openapi"},
    "sim": {"auth": "https://sim.logonvalidation.net",
            "api": "https://gateway.saxobank.com/sim/openapi"},
}
APP_FILE = "saxo_app.json"
STATE_FILE = "saxo_state.json"
TIMEOUT = 30
HISTORY_DAYS = 400
# Renew when the access token has less than this left, and renew the
# chain this often whatever its state, because the refresh token itself
# is the thing that must not be allowed to age past an hour.
ACCESS_MARGIN_S = 120
KEEPALIVE_S = 300
PENDING_STATE_KEY = "saxo_pending_state"

# Saxo's exchange codes (MICs, lower case) → the Yahoo ticker suffix.
_YAHOO_SUFFIX = {
    "xpar": ".PA", "xams": ".AS", "xbru": ".BR", "xlis": ".LS", "xetr": ".DE",
    "fsx": ".F", "xmil": ".MI", "xswx": ".SW", "xvtx": ".SW", "xlon": ".L",
    "xmad": ".MC", "xsto": ".ST", "xcse": ".CO", "xhel": ".HE", "xosl": ".OL",
    "xwbo": ".VI", "xtse": ".TO", "xasx": ".AX", "xtks": ".T", "xhkg": ".HK",
    "xnas": "", "xnys": "", "arcx": "", "bats": "", "xase": "",
}


class SaxoError(RuntimeError):
    """A Saxo call that failed, in a sentence for the page."""


class NotConnected(SaxoError):
    """The token chain is not there or has lapsed: log in again."""


# ─── Credentials and state ───────────────────────────────────────────

def _read_json(name: str) -> dict:
    try:
        return json.loads((settings.SECRETS_DIR / name).read_text())
    except (OSError, ValueError):
        return {}


def _write_json(name: str, data: dict) -> None:
    settings.ensure_dirs()
    path = settings.SECRETS_DIR / name
    path.write_text(json.dumps(data, indent=2))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def app_config() -> dict:
    return _read_json(APP_FILE)


def credentials_present() -> bool:
    cfg = app_config()
    return bool(cfg.get("app_key") and cfg.get("app_secret"))


def save_credentials(app_key: str, app_secret: str, environment: str = "live") -> None:
    app_key, app_secret = (app_key or "").strip(), (app_secret or "").strip()
    if not app_key or not app_secret:
        raise ValueError("Both the AppKey and the AppSecret are needed.")
    if environment not in ENVIRONMENTS:
        environment = "live"
    _write_json(APP_FILE, {"app_key": app_key, "app_secret": app_secret,
                           "environment": environment})


def forget() -> None:
    for name in (APP_FILE, STATE_FILE):
        try:
            (settings.SECRETS_DIR / name).unlink()
        except FileNotFoundError:
            pass


def environment() -> str:
    return app_config().get("environment") or "live"


def _urls() -> dict:
    return ENVIRONMENTS[environment()]


def state() -> dict:
    return _read_json(STATE_FILE)


def _save_state(st: dict) -> None:
    _write_json(STATE_FILE, st)


def redirect_uri() -> str:
    """The dashboard's own address plus /saxo/callback — derived from the
    redirect URL the user already registered for the bank, so both
    point at the same host."""
    bank = settings.get("redirect_url", "http://localhost:8000/connect/callback")
    parts = urllib.parse.urlsplit(bank)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/saxo/callback", "", ""))


# ─── HTTP ────────────────────────────────────────────────────────────

def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SaxoError(f"Could not reach Saxo: {exc}") from exc


transport = _urllib_transport          # swapped by the tests


def _http(method: str, url: str, headers: dict, body: bytes | None = None):
    status, data = transport(method, url, headers, body)
    text = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
    if status >= 400:
        raise SaxoError(f"Saxo {method} {url.split('?')[0].split('/openapi')[-1]} "
                        f"-> {status}: {text[:300]}")
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        raise SaxoError("Saxo answered with something that is not JSON.") from None


# ─── OAuth ───────────────────────────────────────────────────────────

def _token_request(form: dict) -> dict:
    cfg = app_config()
    if not (cfg.get("app_key") and cfg.get("app_secret")):
        raise NotConnected("Saxo is not set up — add the AppKey and AppSecret under Settings.")
    basic = base64.b64encode(f"{cfg['app_key']}:{cfg['app_secret']}".encode()).decode()
    return _http("POST", f"{_urls()['auth']}/token",
                 {"Authorization": f"Basic {basic}",
                  "Content-Type": "application/x-www-form-urlencoded",
                  "Accept": "application/json"},
                 urllib.parse.urlencode(form).encode())


def _apply_tokens(st: dict, resp: dict) -> None:
    now = datetime.now(timezone.utc)
    st["access_token"] = resp["access_token"]
    st["access_expires_at"] = (now + timedelta(seconds=int(resp.get("expires_in") or 1200))
                               ).isoformat(timespec="seconds")
    if resp.get("refresh_token"):
        st["refresh_token"] = resp["refresh_token"]
        st["refresh_expires_at"] = (
            now + timedelta(seconds=int(resp.get("refresh_token_expires_in") or 3600))
        ).isoformat(timespec="seconds")
    st["last_refresh_at"] = now.isoformat(timespec="seconds")
    st.pop("lapsed", None)


def begin_connect(account_id: int) -> str:
    """The URL to send the browser to. The state is remembered so the
    callback can tell a genuine return from a replay."""
    cfg = app_config()
    if not credentials_present():
        raise NotConnected("Saxo is not set up — add the AppKey and AppSecret under Settings.")
    token = _secrets.token_urlsafe(24)
    set_state(PENDING_STATE_KEY, json.dumps({"state": token, "account_id": account_id,
                                             "at": time.time()}))
    query = urllib.parse.urlencode({"response_type": "code", "client_id": cfg["app_key"],
                                    "redirect_uri": redirect_uri(), "state": token})
    return f"{_urls()['auth']}/authorize?{query}"


def complete_connect(code: str, state_token: str) -> dict:
    """Exchange the code, find out who we are, link the accounts.

    Returns {account_id, linked: [names]}. The first Saxo account is
    linked to the account the user started from; the rest are created
    beside it, named after Saxo's account id.
    """
    pending = json.loads(get_state(PENDING_STATE_KEY) or "{}")
    if not pending or pending.get("state") != state_token:
        raise SaxoError("That code is not from a connection this app started.")
    if time.time() - float(pending.get("at") or 0) > 3600:
        raise SaxoError("That login took more than an hour; start again.")
    resp = _token_request({"grant_type": "authorization_code", "code": code,
                           "redirect_uri": redirect_uri()})
    st = state()
    _apply_tokens(st, resp)
    _save_state(st)
    set_state(PENDING_STATE_KEY, "")

    me = _api("/port/v1/clients/me")
    st["client_key"] = me.get("ClientKey")
    st["client_id"] = me.get("ClientId")
    st["default_currency"] = me.get("DefaultCurrency")
    accounts = _collection("/port/v1/accounts/me")
    st["accounts"] = [{"key": a.get("AccountKey"), "id": a.get("AccountId"),
                       "currency": a.get("Currency"), "type": a.get("AccountType")}
                      for a in accounts if a.get("AccountKey")]
    _save_state(st)

    from . import add_link
    linked = []
    first = pending.get("account_id")
    with get_conn() as conn:
        base = conn.execute("SELECT * FROM accounts WHERE id = ?", (first,)).fetchone()
    for i, a in enumerate(st["accounts"]):
        if i == 0 and base is not None:
            account_id = base["id"]
            if a["currency"] and a["currency"] != base["currency"]:
                with get_conn() as conn:
                    conn.execute("UPDATE accounts SET currency = ? WHERE id = ?",
                                 (a["currency"], account_id))
        else:
            with get_conn() as conn:
                row = conn.execute("SELECT account_id FROM broker_links WHERE provider = 'saxo' "
                                   "AND remote_id = ?", (a["key"],)).fetchone()
                if row:
                    account_id = row["account_id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO accounts (name, type, currency) VALUES (?, 'broker', ?)",
                        (f"Saxo {a['id']}", a["currency"] or "EUR"))
                    account_id = int(cur.lastrowid)
        add_link(account_id, "saxo", remote_id=a["key"], remote_label=str(a["id"]),
                 currency=a["currency"])
        with get_conn() as conn:
            linked.append(conn.execute("SELECT name FROM accounts WHERE id = ?",
                                       (account_id,)).fetchone()["name"])
    return {"account_id": base["id"] if base is not None else None, "linked": linked}


def refresh_tokens(st: dict | None = None) -> dict:
    st = st if st is not None else state()
    if not st.get("refresh_token"):
        raise NotConnected("Saxo is not connected.")
    exp = _parse(st.get("refresh_expires_at"))
    if exp and exp < datetime.now(timezone.utc):
        st["lapsed"] = True
        _save_state(st)
        raise NotConnected("The Saxo login has lapsed — connect again from the account page.")
    try:
        resp = _token_request({"grant_type": "refresh_token",
                               "refresh_token": st["refresh_token"],
                               "redirect_uri": redirect_uri()})
    except SaxoError as exc:
        if "400" in str(exc) or "401" in str(exc):
            st["lapsed"] = True
            _save_state(st)
            raise NotConnected("Saxo refused the refresh token — connect again from "
                               "the account page.") from exc
        raise
    _apply_tokens(st, resp)
    _save_state(st)
    return st


def access_token() -> str:
    st = state()
    exp = _parse(st.get("access_expires_at"))
    if st.get("access_token") and exp and \
            exp > datetime.now(timezone.utc) + timedelta(seconds=ACCESS_MARGIN_S):
        return st["access_token"]
    return refresh_tokens(st)["access_token"]


def keepalive() -> dict:
    """One tick of the chain. Never raises: the thread logs and goes on."""
    st = state()
    if not st.get("refresh_token") or st.get("lapsed"):
        return {"status": "idle"}
    try:
        refresh_tokens(st)
        return {"status": "ok", "access_expires_at": st.get("access_expires_at")}
    except SaxoError as exc:
        return {"status": "error", "message": str(exc)}


def _parse(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ─── API ─────────────────────────────────────────────────────────────

def _api(path: str, params: dict | None = None):
    url = _urls()["api"] + path
    if params:
        q = {k: v for k, v in params.items() if v not in (None, "")}
        if q:
            url += "?" + urllib.parse.urlencode(q)
    return _http("GET", url, {"Authorization": f"Bearer {access_token()}",
                              "Accept": "application/json"})


def _collection(path: str, params: dict | None = None) -> list[dict]:
    out: list[dict] = []
    url = _urls()["api"] + path
    if params:
        q = {k: v for k, v in params.items() if v not in (None, "")}
        if q:
            url += "?" + urllib.parse.urlencode(q)
    token = access_token()
    while url:
        resp = _http("GET", url, {"Authorization": f"Bearer {token}",
                                  "Accept": "application/json"})
        if not isinstance(resp, dict):
            break
        out.extend(resp.get("Data") or [])
        url = resp.get("__next") or ""
    return out


# ─── What the API says → rows ────────────────────────────────────────

def instrument_key(uic) -> str:
    return f"SAXO:{uic}"


def yahoo_symbol(symbol: str | None) -> str | None:
    """`IWDA:xams` → `IWDA.AS`; None for an exchange this table lacks."""
    base, _, exch = (symbol or "").partition(":")
    base = base.strip().upper()
    if not base or exch.strip().lower() not in _YAHOO_SUFFIX:
        return None
    return base + _YAHOO_SUFFIX[exch.strip().lower()]


def _remember_symbol(uic, symbol: str | None, name: str | None) -> None:
    """The Yahoo ticker for a Saxo instrument, into `securities`, so the
    price feed quotes it without a search it could not do (a search
    wants an ISIN). Never over a ticker the user typed."""
    ysym = yahoo_symbol(symbol)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO securities (isin, symbol, name, symbol_source, resolved_at) "
            "VALUES (?, ?, ?, 'saxo', datetime('now')) ON CONFLICT(isin) DO UPDATE SET "
            " symbol = CASE WHEN securities.symbol_source = 'manual' THEN securities.symbol "
            "               ELSE COALESCE(excluded.symbol, securities.symbol) END, "
            " name = COALESCE(excluded.name, securities.name)",
            (instrument_key(uic), ysym, name))


def trades_to_rows(trades: list[dict], account_currency: str) -> list[ParsedTxn]:
    rows = []
    for t in trades:
        tid = t.get("TradeId")
        if not tid:
            continue
        event = (t.get("TradeEventType") or "").strip().lower()
        if event.startswith("b"):
            kind = "buy"
        elif event.startswith("s"):
            kind = "sell"
        else:
            continue
        qty, price = t.get("Amount"), t.get("Price")
        date = (t.get("TradeExecutionTime") or t.get("TradeDate")
                or t.get("AdjustedTradeDate") or "")[:10]
        if not date or qty is None:
            continue
        ccy = (t.get("AccountCurrency") or t.get("ClientCurrency") or account_currency).upper()
        booked = t.get("BookedAmountAccountCurrency")
        if booked is None:
            gross = (price or 0) * qty
            booked = -gross if kind == "buy" else gross
        name = t.get("InstrumentDescription") or t.get("InstrumentSymbol")
        rows.append(ParsedTxn(
            txn_date=date, description=f"{'Bought' if kind == 'buy' else 'Sold'} {qty:g} "
                                       f"{t.get('InstrumentSymbol') or name or ''}".strip(),
            amount=round(float(booked), 2), currency=ccy, kind=kind,
            external_id=f"saxo:trade:{tid}", isin=instrument_key(t.get("Uic")),
            security_name=name, quantity=abs(qty) if kind == "buy" else -abs(qty),
            price=price))
        _remember_symbol(t.get("Uic"), t.get("InstrumentSymbol"), name)
    return rows


def bookings_to_rows(bookings: list[dict], account_currency: str) -> list[ParsedTxn]:
    rows = []
    for b in bookings:
        bid = b.get("BkAmountId") or b.get("BookingId") or b.get("Id")
        amount = b.get("Amount")
        if not bid or amount is None:
            continue
        date = (b.get("Date") or b.get("ValueDate") or "")[:10]
        if not date:
            continue
        kind_text = (b.get("BkAmountType") or b.get("AmountTypeName") or "").lower()
        symbol = b.get("InstrumentSymbol") or ""
        if "dividend" in kind_text:
            kind = "dividend"
        elif "interest" in kind_text:
            kind = "interest"
        elif "tax" in kind_text or "withhold" in kind_text:
            kind = "tax"
        elif "fee" in kind_text or "commission" in kind_text or "cost" in kind_text:
            kind = "fee"
        elif "transfer" in kind_text and symbol:
            kind = "transfer"
        else:
            kind = "deposit" if amount > 0 else "withdrawal"
        rows.append(ParsedTxn(
            txn_date=date, description=" ".join(filter(None, [b.get("BkAmountType") or "Booking", symbol])),
            amount=round(float(amount), 2), currency=(b.get("Currency") or account_currency).upper(),
            kind=kind, external_id=f"saxo:booking:{bid}",
            isin=instrument_key(b.get("Uic")) if b.get("Uic") and kind == "dividend" else None,
            security_name=b.get("InstrumentDescription") if b.get("Uic") and kind == "dividend" else None))
    return rows


def reconcile_positions(account_id: int, positions: list[dict], account_currency: str) -> list[ParsedTxn]:
    """Rows for what Saxo holds that the trades do not explain.

    A position transferred in from another broker has no buy in Saxo's
    history. Its quantity is recorded as a transfer dated when Saxo
    opened it, at Saxo's average open price, so the holding is right
    and the cost is known even though no money moved here.
    """
    with get_conn() as conn:
        have = {r["isin"]: r["q"] for r in conn.execute(
            "SELECT isin, SUM(quantity) AS q FROM transactions WHERE account_id = ? "
            "AND isin LIKE 'SAXO:%' AND quantity IS NOT NULL GROUP BY isin", (account_id,))}
    rows = []
    seen: dict[str, float] = {}
    for p in positions:
        base = p.get("PositionBase") or {}
        disp = p.get("DisplayAndFormat") or {}
        uic, qty = base.get("Uic"), base.get("Amount")
        if uic is None or qty is None:
            continue
        key = instrument_key(uic)
        seen[key] = seen.get(key, 0.0) + float(qty)
        _remember_symbol(uic, disp.get("Symbol"), disp.get("Description"))
    for key, qty in seen.items():
        diff = qty - have.get(key, 0.0)
        if abs(diff) < 1e-9:
            continue
        p = next(p for p in positions if instrument_key((p.get("PositionBase") or {}).get("Uic")) == key)
        base, disp = p.get("PositionBase") or {}, p.get("DisplayAndFormat") or {}
        opened = (base.get("ExecutionTimeOpen") or "")[:10] or datetime.now(timezone.utc).date().isoformat()
        rows.append(ParsedTxn(
            txn_date=opened,
            description=f"Position at Saxo not explained by its trades: {diff:+g} "
                        f"{disp.get('Symbol') or key}",
            amount=0.0, currency=account_currency, kind="transfer",
            external_id=f"saxo:adjust:{key}:{opened}:{diff:+g}",
            isin=key, security_name=disp.get("Description"), quantity=diff,
            price=base.get("OpenPrice")))
    return rows


def sync_link(link: dict) -> int:
    st = state()
    client_key = st.get("client_key")
    if not client_key:
        raise NotConnected("Saxo is not connected.")
    ccy = (link.get("currency") or link["account_currency"]).upper()
    today = datetime.now(timezone.utc).date()
    frm = (today - timedelta(days=HISTORY_DAYS)).isoformat()
    to = today.isoformat()

    trades = _collection(f"/cs/v1/reports/trades/{client_key}",
                         {"FromDate": frm, "ToDate": to, "$top": 1000})
    bookings = _collection(f"/cs/v1/reports/bookings/{client_key}",
                           {"FromDate": frm, "ToDate": to, "$top": 1000})
    # The reports are per client; keep what belongs to this account when
    # the rows say which, and everything when they do not.
    mine = str(link.get("remote_label") or "")
    def own(row):
        aid = row.get("AccountId")
        return not aid or not mine or str(aid) == mine
    parsed = ParseResult()
    parsed.rows.extend(trades_to_rows([t for t in trades if own(t)], ccy))
    parsed.rows.extend(bookings_to_rows([b for b in bookings if own(b)], ccy))
    report = store(link["account_id"], parsed, "saxo")

    positions = _collection("/port/v1/positions", {
        "ClientKey": client_key, "AccountKey": link.get("remote_id"),
        "FieldGroups": "PositionBase,PositionView,DisplayAndFormat"})
    extra = ParseResult()
    extra.rows = reconcile_positions(link["account_id"], positions, ccy)
    bal = _api("/port/v1/balances", {"ClientKey": client_key, "AccountKey": link.get("remote_id")})
    if isinstance(bal, dict) and bal.get("CashBalance") is not None:
        cash = float(bal["CashBalance"]) + float(bal.get("TransactionsNotBooked") or 0)
        extra.closing_balance = {"amount": round(cash, 2), "currency": (bal.get("Currency") or ccy).upper(),
                                 "as_of": to}
    report2 = store(link["account_id"], extra, "saxo")
    return report["inserted"] + report2["inserted"]


def describe() -> dict:
    """For the Settings page and the account page."""
    st = state()
    cfg = app_config()
    exp = _parse(st.get("refresh_expires_at"))
    alive = bool(st.get("refresh_token")) and not st.get("lapsed") and \
        (exp is None or exp > datetime.now(timezone.utc))
    return {"configured": credentials_present(), "environment": cfg.get("environment") or "live",
            "app_key": cfg.get("app_key"), "connected": bool(st.get("client_key")),
            "alive": alive, "lapsed": bool(st.get("client_key")) and not alive,
            "client_id": st.get("client_id"), "accounts": st.get("accounts") or [],
            "last_refresh_at": st.get("last_refresh_at"),
            "redirect_uri": redirect_uri()}
