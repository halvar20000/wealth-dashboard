"""Trade Republic, through the interface its own web app uses.

**Unofficial, and may stop working any day.** Trade Republic publishes
no API. Its web app logs in with the phone number and PIN, confirms
the login in the mobile app (or with a code), and then talks to
`wss://api.traderepublic.com` — a WebSocket with a small protocol of
its own: `connect`, then `sub N {"type": …}` for each thing wanted,
answered by `N A {json}`. This module speaks exactly that, the way
the pytr project and Sure do. Trade Republic has changed it several
times and will again; when it breaks, the statement PDFs still read.

What is needed: the phone number and the PIN, kept 0600 beside the
other keys. The PIN is used to log in; a login lasts until Trade
Republic ends it (weeks, usually), and the session cookies are kept so
the daily sync needs nothing from you until then. Log in again from
the account page when it lapses.

What is read, and what it becomes
---------------------------------
  * **timelineTransactions** — every event, newest first, page by
    page: order and savings-plan executions, dividends, interest,
    deposits, withdrawals, card payments, tax refunds. The event says
    the money; for a trade or a dividend, `timelineDetailV2` says the
    units, the price, the fee and the tax.
  * **compactPortfolioByType** — the positions, checked against what
    the rows add up to.
  * **cash** — the balance reading.

The ids are Trade Republic's event ids (`trtl:`), so a re-sync never
doubles a row, and a sync stops paging as soon as it reaches an event
it has. An account that already holds its history from the CSV export,
the statement PDFs or a move-in gets no second copy: a booking the
account has by day, security, units and money is the same booking —
see `brokers.dedupe_against_account`.
"""

from __future__ import annotations

import base64
import json
import os
import re
import socket
import ssl
import struct
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .. import settings
from ..db import get_conn
from ..importers import ParsedTxn, ParseResult, store
from ..importers.base import find_isin

API = "https://api.traderepublic.com"
WS_HOST = "api.traderepublic.com"
PHONE_FILE = "traderepublic_phone"
PIN_FILE = "traderepublic_pin"
SESSION_FILE = "traderepublic_session.json"
PENDING_FILE = "traderepublic_pending.json"
TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
APP_VERSION = "2.2631.13"
CONNECT = {"locale": "en", "platformId": "webtrading", "platformVersion": "chrome - 151.0.0",
           "clientId": "app.traderepublic.com", "clientVersion": "5582"}
MAX_PAGES = 60
MAX_DETAILS = 300

# Which events matter, and what they are. Anything else is left out
# and counted (an app notice, a document, a card order).
TRADES = {"TRADING_TRADE_EXECUTED", "TRADE_INVOICE", "ORDER_EXECUTED", "SAVINGS_PLAN_EXECUTED",
          "TRADING_SAVINGSPLAN_EXECUTED", "CRYPTO_INVOICE", "IPO_TRADE_EXECUTED", "PRIVATE_MARKET_FUND_TRADE_EXECUTED",
          "trading_savingsplan_executed", "benefits_saveback_execution", "benefits_spare_change_execution"}
DIVIDENDS = {"CREDIT", "DIVIDEND", "SSP_CORPORATE_ACTION_CASH", "ssp_corporate_action_invoice_cash"}
INTEREST = {"INTEREST_PAYOUT", "INTEREST_PAYOUT_CREATED"}
CASH_IN = {"PAYMENT_INBOUND", "INCOMING_TRANSFER", "INCOMING_TRANSFER_DELEGATION", "BANK_TRANSACTION_INCOMING",
           "PAYMENT_INBOUND_SEPA_DIRECT_DEBIT", "PAYMENT_INBOUND_APPLE_PAY", "card_refund", "CARD_REFUND",
           "SSP_CORPORATE_ACTION_CASH_NON_DIVIDEND"}
CASH_OUT = {"PAYMENT_OUTBOUND", "OUTGOING_TRANSFER", "OUTGOING_TRANSFER_DELEGATION", "BANK_TRANSACTION_OUTGOING",
            "BANK_TRANSACTION_OUTGOING_DIRECT_DEBIT", "BANK_TRANSACTION_OUTGOING_SCHEDULED", "CARD_TRANSACTION",
            "card_successful_transaction", "CARD_CASH_BACK", "CARD_ATM_WITHDRAWAL", "SPARE_CHANGE_AGGREGATE",
            "SAVEBACK_AGGREGATE"}
TAX_REFUNDS = {"TAX_REFUND", "ssp_tax_correction_invoice", "SSP_TAX_CORRECTION"}
FEES = {"CARD_ORDER_FEE"}


class TradeRepublicError(Exception):
    pass


class SessionExpired(TradeRepublicError):
    """The login lapsed: log in again from the account page."""


class HoldingsDrift(TradeRepublicError):
    """Synced, but the positions and the rows do not agree."""


# ─── Credentials and session ─────────────────────────────────────────

def _path(name: str):
    return settings.SECRETS_DIR / name


def _write(name: str, text: str) -> None:
    settings.ensure_dirs()
    p = _path(name)
    p.write_text(text)
    try:
        p.chmod(0o600)
    except OSError:
        pass


def credentials_present() -> bool:
    return _path(PHONE_FILE).exists() and _path(PIN_FILE).exists()


def session_present() -> bool:
    return _path(SESSION_FILE).exists()


def save_credentials(phone: str, pin: str) -> None:
    phone, pin = re.sub(r"[\s-]", "", phone or ""), (pin or "").strip()
    if not re.fullmatch(r"\+\d{8,15}", phone):
        raise ValueError("The phone number is the one Trade Republic knows, with the country code: +49… or +41….")
    if not re.fullmatch(r"\d{4}", pin):
        raise ValueError("The PIN is the four digits you unlock the app with.")
    _write(PHONE_FILE, phone)
    _write(PIN_FILE, pin)


def forget() -> None:
    for name in (PHONE_FILE, PIN_FILE, SESSION_FILE, PENDING_FILE):
        try:
            _path(name).unlink()
        except FileNotFoundError:
            pass


def _credentials() -> tuple[str, str]:
    try:
        return _path(PHONE_FILE).read_text().strip(), _path(PIN_FILE).read_text().strip()
    except OSError:
        raise TradeRepublicError("Trade Republic is not set up — add the phone number and PIN under Settings.") from None


def _cookies() -> dict:
    try:
        return json.loads(_path(SESSION_FILE).read_text())
    except (OSError, ValueError):
        return {}


def _save_cookies(cookies: dict) -> None:
    _write(SESSION_FILE, json.dumps(cookies))


def _pending() -> dict | None:
    try:
        return json.loads(_path(PENDING_FILE).read_text())
    except (OSError, ValueError):
        return None


# ─── HTTP with cookies ───────────────────────────────────────────────

def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(), resp.headers.get_all("Set-Cookie") or []
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get_all("Set-Cookie") or []
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise TradeRepublicError(f"Could not reach Trade Republic: {exc}") from exc


def _device_info() -> str:
    ident = base64.b64encode(json.dumps({
        "stableDeviceId": __import__("hashlib").sha512((socket.gethostname() + "|wealth-dashboard").encode()).hexdigest(),
        "browser": "Chrome", "browserVersion": "151.0.0.0", "device": "Desktop", "deviceType": "desktop",
        "os": "Linux", "osVersion": "", "timezone": "Europe/Berlin", "timezoneOffset": -60,
        "screen": "1920x1080x24", "preferredLanguages": ["en"], "numberOfCores": os.cpu_count() or 4,
    }).encode()).decode()
    return ident


class Http:
    """Requests against api.traderepublic.com carrying the session's
    cookies, and keeping the ones it hands back."""

    def __init__(self, cookies: dict | None = None, transport=None):
        self.cookies = dict(cookies or {})
        self.transport = transport or _urllib_transport
        self._refreshed = 0.0

    def _headers(self, login: bool = False) -> dict:
        h = {"User-Agent": USER_AGENT, "Origin": API, "Referer": API + "/", "Accept": "application/json",
             "Accept-Language": "en-US,en;q=0.9", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
             "Sec-Fetch-Site": "same-site"}
        if self.cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if login:
            h.update({"X-TR-Device-Info": _device_info(), "X-TR-App-Version": APP_VERSION, "X-Tr-Platform": "web-pro"})
        return h

    def request(self, method: str, path: str, body: dict | None = None, login: bool = False) -> tuple[int, dict | list | None]:
        headers = self._headers(login)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, raw, set_cookies = self.transport(method, API + path, headers, data)
        for sc in set_cookies:
            pair = sc.split(";", 1)[0]
            if "=" in pair:
                k, v = pair.split("=", 1)
                if k.strip() and v.strip():
                    self.cookies[k.strip()] = v.strip()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw and raw.strip() else None
        except ValueError:
            parsed = None
        return status, parsed

    def refresh(self) -> None:
        """The web app pings the session every few minutes; so do we."""
        if time.time() - self._refreshed < 280:
            return
        status, _ = self.request("GET", "/api/v1/auth/web/session")
        if status in (401, 403):
            raise SessionExpired("The Trade Republic login has lapsed — log in again from the account page.")
        self._refreshed = time.time()


# ─── Login ───────────────────────────────────────────────────────────

def start_login(transport=None) -> dict:
    """Phone and PIN in; Trade Republic asks the app (or a code). What
    comes back says which, and is kept until `finish_login`."""
    phone, pin = _credentials()
    http = Http({}, transport)
    status, body = http.request("POST", "/api/v2/auth/web/login", {"phoneNumber": phone, "pin": pin}, login=True)
    if status in (401, 403) or (isinstance(body, dict) and body.get("errors")):
        detail = ""
        if isinstance(body, dict):
            errs = body.get("errors") or []
            detail = "; ".join(str(e.get("errorCode") or e.get("message") or e) for e in errs) if isinstance(errs, list) else str(errs)
        raise TradeRepublicError(f"Trade Republic refused the login ({detail or status}). Wrong PIN or phone number, or too many tries.")
    if status != 200 or not isinstance(body, dict) or not body.get("processId"):
        raise TradeRepublicError(f"Trade Republic answered {status} to the login without a process id.")
    process_id = str(body["processId"])
    status, process = http.request("GET", f"/api/v2/auth/web/login/processes/{process_id}", login=True)
    action = (process or {}).get("requiredAction") if isinstance(process, dict) else None
    pending = {"process_id": process_id, "required_action": action or "", "cookies": http.cookies,
               "countdown": int(body.get("countdownInSeconds") or 120),
               "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _write(PENDING_FILE, json.dumps(pending))
    return {"method": "code" if action == "AUTHENTICATOR_VERIFICATION" else "app", "countdown": pending["countdown"]}


_DONE = {"CONFIRMED", "COMPLETED", "APPROVED", "SUCCESS", "OK", "DONE"}


def finish_login(code: str | None = None, transport=None) -> dict:
    """The second step: the code typed, or the app's approval looked
    for. On success the session is saved and the account described."""
    pending = _pending()
    if not pending:
        raise TradeRepublicError("No login is under way — start one first.")
    http = Http(pending.get("cookies"), transport)
    pid = pending["process_id"]
    if pending.get("required_action") == "AUTHENTICATOR_VERIFICATION" and not pending.get("verified"):
        if not (code or "").strip():
            raise TradeRepublicError("Trade Republic wants the code from the app.")
        status, body = http.request("POST", f"/api/v2/auth/web/login/processes/{pid}/authenticator-verification",
                                    {"code": code.strip()}, login=True)
        if status not in (200, 201, 204):
            raise TradeRepublicError(f"Trade Republic did not accept the code ({status}).")
        pending["verified"] = True
        pending["cookies"] = http.cookies
        _write(PENDING_FILE, json.dumps(pending))
    status, process = http.request("GET", f"/api/v2/auth/web/login/processes/{pid}", login=True)
    if status in (401, 403, 404):
        raise TradeRepublicError("The login attempt has expired — start again.")
    state = " ".join(str((process or {}).get(k, "")) for k in ("state", "status", "statusCode", "result")).upper() if isinstance(process, dict) else ""
    if not any(s in state.split() for s in _DONE):
        pending["cookies"] = http.cookies
        _write(PENDING_FILE, json.dumps(pending))
        return {"done": False}
    status, account = http.request("GET", "/api/v2/auth/account", login=True)
    if status != 200 or not isinstance(account, dict) or not account.get("securitiesAccountNumber"):
        raise TradeRepublicError("Logged in, but Trade Republic did not name the securities account.")
    _save_cookies(http.cookies)
    try:
        _path(PENDING_FILE).unlink()
    except FileNotFoundError:
        pass
    return {"done": True, "account": str(account["securitiesAccountNumber"]), "currency": account.get("currency") or "EUR"}


# ─── The WebSocket, in the standard library ──────────────────────────

class WebSocket:
    """Just enough of RFC 6455 for one client: text frames out (masked,
    as a client must), text and control frames in."""

    def __init__(self, host: str, headers: dict, timeout: float = TIMEOUT):
        raw = socket.create_connection((host, 443), timeout=timeout)
        self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        key = base64.b64encode(os.urandom(16)).decode()
        lines = [f"GET / HTTP/1.1", f"Host: {host}", "Upgrade: websocket", "Connection: Upgrade",
                 f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13"]
        lines += [f"{k}: {v}" for k, v in headers.items()]
        self.sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
        reply = b""
        while b"\r\n\r\n" not in reply:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise TradeRepublicError("Trade Republic closed the connection during the WebSocket handshake.")
            reply += chunk
        head, _, rest = reply.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise TradeRepublicError("Trade Republic refused the WebSocket: " + head.split(b"\r\n", 1)[0].decode("latin-1"))
        self.buffer = rest

    def _read(self, n: int) -> bytes:
        while len(self.buffer) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise TradeRepublicError("Trade Republic closed the WebSocket.")
            self.buffer += chunk
        out, self.buffer = self.buffer[:n], self.buffer[n:]
        return out

    def _send(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        head = bytes([0x80 | opcode])
        n = len(payload)
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def send_text(self, text: str) -> None:
        self._send(0x1, text.encode())

    def receive(self) -> str:
        message = b""
        while True:
            b1, b2 = self._read(2)
            fin, opcode = b1 & 0x80, b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if b2 & 0x80 else None
            data = self._read(n)
            if mask:
                data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
            if opcode == 0x9:                       # ping
                self._send(0xA, data)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                raise TradeRepublicError("Trade Republic closed the WebSocket.")
            message += data
            if fin:
                return message.decode("utf-8", "replace")

    def close(self) -> None:
        try:
            self._send(0x8, struct.pack(">H", 1000))
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


def _open_ws(cookies: dict):
    return WebSocket(WS_HOST, {"Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()), "Origin": API,
                               "User-Agent": USER_AGENT})


class Session:
    """A connected WebSocket speaking Trade Republic's protocol."""

    def __init__(self, ws):
        self.ws = ws
        self.n = 0
        ws.send_text("connect 31 " + json.dumps(CONNECT))
        if ws.receive().strip() != "connected":
            raise TradeRepublicError("Trade Republic did not accept the WebSocket connection — log in again.")

    def sub(self, **payload):
        self.n += 1
        n = self.n
        self.ws.send_text(f"sub {n} " + json.dumps(payload))
        previous = None
        try:
            while True:
                msg = self.ws.receive()
                parts = msg.split(" ", 2)
                if len(parts) < 2 or parts[0] != str(n):
                    continue
                code = parts[1]
                body = parts[2] if len(parts) > 2 else ""
                if code == "A":
                    return json.loads(body or "{}")
                if code == "D":
                    previous = _delta(previous or "", body)
                    return json.loads(previous or "{}")
                if code == "E":
                    err = body
                    try:
                        errs = json.loads(body).get("errors") or []
                        err = "; ".join(str(e.get("errorCode") or e.get("message") or e) for e in errs) or body
                    except ValueError:
                        pass
                    if "AUTHENTICATION" in err.upper() or "UNAUTHORIZED" in err.upper():
                        raise SessionExpired("The Trade Republic login has lapsed — log in again from the account page.")
                    raise TradeRepublicError(f"Trade Republic refused {payload.get('type')}: {err}")
                if code == "C":
                    raise TradeRepublicError(f"Trade Republic closed {payload.get('type')}.")
        finally:
            try:
                self.ws.send_text(f"unsub {n}")
            except Exception:                        # noqa: BLE001
                pass


def _delta(previous: str, delta: str) -> str:
    """Trade Republic's diff format: tab-separated ops, `=n` keep n
    chars, `-n` drop n, `+text` insert."""
    out, i = [], 0
    for op in delta.split("\t"):
        if not op:
            continue
        if op[0] == "=":
            n = int(op[1:]); out.append(previous[i:i + n]); i += n
        elif op[0] == "-":
            i += int(op[1:])
        elif op[0] == "+":
            out.append(op[1:])
    return "".join(out)


# ─── Timeline → rows ─────────────────────────────────────────────────

def _money(node) -> tuple[float | None, str | None]:
    if isinstance(node, list):
        node = node[0] if node else None
    if not isinstance(node, dict):
        return None, None
    v = node.get("value", node.get("amount"))
    try:
        v = float(v) if v is not None else None
    except (TypeError, ValueError):
        v = None
    return v, (node.get("currency") or node.get("currencyId") or None)


def _num(text) -> float | None:
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    s = re.sub(r"[^\d,.\-]", "", str(text))
    if not s or s in ("-", ".", ","):
        return None
    if s.count(",") == 1 and (s.rfind(",") > s.rfind(".")):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _rows_of_detail(detail) -> list[dict]:
    rows: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("data"), list):
                rows.extend(r for r in node["data"] if isinstance(r, dict))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(detail)
    return rows


def _row_text(rows: list[dict], titles: tuple) -> str | None:
    for r in rows:
        if str(r.get("title") or "").strip().lower() in titles:
            d = r.get("detail") or {}
            return d.get("text") or (d.get("value") or {}).get("text") if isinstance(d, dict) else None
    return None


def _isin_of(item: dict, detail) -> str | None:
    icon = str(item.get("icon") or "")
    m = re.search(r"logos/([A-Z]{2}[A-Z0-9]{9}\d)", icon)
    if m:
        return m.group(1)
    for text in _strings(detail):
        isin = find_isin(text) if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", text.strip()) else None
        if isin:
            return isin
    for text in _strings(detail):
        m = re.search(r"logos/([A-Z]{2}[A-Z0-9]{9}\d)", text)
        if m:
            return m.group(1)
    return None


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def normalise(events: list[tuple[dict, dict | None]], account_currency: str) -> ParseResult:
    """(event, detail or None) pairs → rows."""
    result = ParseResult()
    ccy0 = account_currency.upper()[:3]
    for item, detail in events:
        etype = str(item.get("eventType") or "")
        amount, ccy = _money(item.get("amount"))
        date = str(item.get("timestamp") or "")[:10]
        ext = f"trtl:{item.get('id')}" if item.get("id") else None
        title = str(item.get("title") or "").strip()
        subtitle = str(item.get("subtitle") or "").strip()
        ccy = (ccy or ccy0).upper()
        if not date or amount is None:
            result.skipped += 1
            continue
        rows = _rows_of_detail(detail) if detail else []
        if etype in TRADES:
            shares = _num(_row_text(rows, ("shares", "aktien", "anteile", "stück", "shares added", "shares received")))
            price = _num(_row_text(rows, ("share price", "aktienkurs", "kurs", "price", "preis")))
            fee = _num(_row_text(rows, ("fee", "gebühr", "gebühren", "fees")))
            tax = _num(_row_text(rows, ("tax", "taxes", "steuer", "steuern")))
            isin = _isin_of(item, detail)
            sell = amount > 0 or any(w in subtitle.lower() for w in ("sell", "verkauf", "sale"))
            kind = "sell" if sell else "buy"
            if shares is None and price:
                shares = abs(amount) / price
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"{'Verkauf' if sell else 'Kauf'} {title}"[:500], amount=round(amount, 2),
                currency=ccy, kind=kind, external_id=ext, isin=isin, security_name=title or None,
                quantity=(abs(shares) if kind == "buy" else -abs(shares)) if shares else None,
                price=abs(price) if price else None, fee=abs(fee) if fee else None, tax=abs(tax) if tax else None))
        elif etype in DIVIDENDS:
            tax = _num(_row_text(rows, ("tax", "taxes", "steuer", "steuern", "withholding tax", "quellensteuer")))
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"Dividende {title}"[:500], amount=round(amount, 2), currency=ccy,
                kind="dividend", external_id=ext, isin=_isin_of(item, detail), security_name=title or None,
                tax=abs(tax) if tax else None))
        elif etype in INTEREST:
            result.rows.append(ParsedTxn(txn_date=date, description=f"Zinsen {title}"[:500], amount=round(amount, 2),
                                         currency=ccy, kind="interest", external_id=ext))
        elif etype in TAX_REFUNDS:
            result.rows.append(ParsedTxn(txn_date=date, description=f"Steuererstattung {title}"[:500], amount=round(abs(amount), 2),
                                         currency=ccy, kind="tax", external_id=ext))
        elif etype in FEES:
            result.rows.append(ParsedTxn(txn_date=date, description=f"Gebühr {title}"[:500], amount=round(-abs(amount), 2),
                                         currency=ccy, kind="fee", external_id=ext))
        elif etype in CASH_IN or etype in CASH_OUT:
            kind = "deposit" if amount > 0 else "withdrawal"
            result.rows.append(ParsedTxn(txn_date=date, description=" ".join(x for x in (title, subtitle) if x)[:500] or kind,
                                         amount=round(amount, 2), currency=ccy, kind=kind, external_id=ext,
                                         counterparty=title if etype in CASH_OUT and "card" in etype.lower() else None))
        else:
            result.skipped += 1
    return result


# ─── Sync ────────────────────────────────────────────────────────────

def fetch(cookies: dict, known_ids: set, http: Http | None = None, ws_factory=_open_ws) -> dict:
    """Everything the web app would show: positions, cash, and the
    timeline back to the newest event already known."""
    http = http or Http(cookies)
    http.refresh()
    status, account = http.request("GET", "/api/v2/auth/account")
    if status in (401, 403):
        raise SessionExpired("The Trade Republic login has lapsed — log in again from the account page.")
    if status != 200 or not isinstance(account, dict):
        raise TradeRepublicError(f"Trade Republic answered {status} for the account.")
    sec_no = account.get("securitiesAccountNumber")
    ws = ws_factory(http.cookies)
    try:
        s = Session(ws)
        cash_raw = s.sub(type="cash")
        cash, cash_ccy = _money(cash_raw)
        positions = {}
        try:
            portfolio = s.sub(type="compactPortfolioByType", secAccNo=sec_no)
            for cat in (portfolio.get("categories") or []):
                for p in (cat.get("positions") or []):
                    isin = p.get("instrumentId") or p.get("isin")
                    size = _num(p.get("netSize") or p.get("size"))
                    if isin and size:
                        positions[isin] = (positions.get(isin, (0.0, ""))[0] + size, p.get("name") or isin)
        except TradeRepublicError as e:
            if isinstance(e, SessionExpired):
                raise
        events: list[dict] = []
        after = None
        stop = False
        for _ in range(MAX_PAGES):
            page = s.sub(type="timelineTransactions", **({"after": after} if after else {}))
            items = page.get("items") or []
            if not items:
                break
            for it in items:
                if it.get("id") in known_ids:
                    stop = True
                    break
                events.append(it)
            after = (page.get("cursors") or {}).get("after")
            if stop or not after:
                break
        pairs = []
        fetched = 0
        for it in events:
            detail = None
            if (it.get("eventType") in TRADES or it.get("eventType") in DIVIDENDS) and it.get("id") and fetched < MAX_DETAILS:
                try:
                    detail = s.sub(type="timelineDetailV2", id=it["id"])
                    fetched += 1
                except TradeRepublicError as e:
                    if isinstance(e, SessionExpired):
                        raise
            pairs.append((it, detail))
    finally:
        ws.close()
    return {"account": str(sec_no or ""), "currency": account.get("currency") or "EUR", "cash": cash, "cash_currency": cash_ccy,
            "positions": positions, "events": pairs, "cookies": http.cookies}


def sync_link(link: dict, fetched: dict | None = None) -> int:
    cookies = _cookies()
    if not cookies and fetched is None:
        raise SessionExpired("Trade Republic is not logged in — log in from the account page.")
    with get_conn() as conn:
        known = {r["external_id"].split(":", 1)[1] for r in conn.execute(
            "SELECT external_id FROM transactions WHERE account_id = ? AND (external_id LIKE 'trtl:%' OR external_id LIKE 'tr:%')",
            (link["account_id"],))}
    data = fetched or fetch(cookies, known)
    if data.get("cookies"):
        _save_cookies(data["cookies"])
    parsed = normalise(data["events"], link["account_currency"])
    if data.get("cash") is not None:
        parsed.closing_balance = {"amount": round(data["cash"], 2), "currency": (data.get("cash_currency") or link["account_currency"]).upper(),
                                  "as_of": datetime.now(timezone.utc).date().isoformat()}
    from . import dedupe_against_account
    dedupe_against_account(link["account_id"], "traderepublic", parsed)
    report = store(link["account_id"], parsed, "traderepublic")
    with get_conn() as conn:
        held = {r["isin"]: r["q"] for r in conn.execute(
            "SELECT isin, SUM(quantity) AS q FROM transactions WHERE account_id = ? "
            "AND isin IS NOT NULL AND quantity IS NOT NULL GROUP BY isin", (link["account_id"],))}
    drift = []
    for isin, (qty, name) in (data.get("positions") or {}).items():
        have = held.get(isin, 0.0)
        if abs(have - qty) > 1e-4:
            drift.append(f"{name}: Trade Republic says {qty:g}, the rows add up to {have:g}")
    if drift:
        raise HoldingsDrift("Synced, but the holdings do not add up — " + "; ".join(drift)
                            + ". The timeline shows a year or two; import the older Abrechnung PDFs for the rest.")
    return report["inserted"]


def describe() -> dict:
    pending = _pending()
    with get_conn() as conn:
        linked = conn.execute("SELECT a.name FROM broker_links bl JOIN accounts a ON a.id = bl.account_id "
                              "WHERE bl.provider = 'traderepublic' LIMIT 1").fetchone()
    return {"configured": credentials_present(), "logged_in": session_present(),
            "pending": {"method": "code" if (pending or {}).get("required_action") == "AUTHENTICATOR_VERIFICATION" else "app"} if pending else None,
            "linked": linked["name"] if linked else None}
