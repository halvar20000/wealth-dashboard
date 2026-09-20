"""Interactive Brokers, through the Flex Web Service with a token of
your own.

No OAuth, no app registration: in Account Management you create an
Activity Flex Query (Reports → Flex Queries) with Trades, Cash
Transactions, Open Positions and the Cash Report ticked and a period
such as "Last 365 Days"; then under Reports → Settings → Flex Web
Service you switch the service on and get a token. The query's id
and the token are what this needs. The token can only run Flex
queries — it cannot see your login, place an order or move money.

The service works in two steps, which is why a sync takes a little
while: `SendRequest` asks IBKR to generate the statement and answers
with a reference code; `GetStatement` with that code hands the XML
over once it is ready, or says "still generating" (error 1004/1019)
for a few seconds first. The XML is then read by the Flex importer
(`importers/ibkr_flex.py`) exactly as a downloaded one would be.

IBKR keeps Flex history for a year or so. For what came before, run
the query once with a custom period and drop the XML on the import
page — same reader, same ids, nothing doubled.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .. import settings
from ..db import get_conn
from ..importers import ibkr_flex, store

BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
TOKEN_FILE = "ibkr_token"
QUERY_FILE = "ibkr_query"
TIMEOUT = 60
POLL_SECONDS = 4
MAX_POLLS = 20
PENDING_CODES = ("1004", "1019")           # statement still generating / in progress


class IbkrError(Exception):
    pass


class HoldingsDrift(IbkrError):
    """Synced, but IBKR's positions and the rows do not agree."""


# ─── Credentials ─────────────────────────────────────────────────────

def credentials_present() -> bool:
    return ((settings.SECRETS_DIR / TOKEN_FILE).exists()
            and (settings.SECRETS_DIR / QUERY_FILE).exists())


def save_credentials(token: str, query_id: str) -> None:
    settings.ensure_dirs()
    token, query_id = (token or "").strip(), (query_id or "").strip()
    if not token or not query_id:
        raise ValueError("Both the Flex token and the query id are needed.")
    if not query_id.isdigit():
        raise ValueError("The query id is the number IBKR shows beside the Flex Query, such as 987654.")
    if not re.fullmatch(r"\d{10,}", token):
        raise ValueError("The token does not look like the one Flex Web Service shows — a long number.")
    for name, value in ((TOKEN_FILE, token), (QUERY_FILE, query_id)):
        path = settings.SECRETS_DIR / name
        path.write_text(value)
        try:
            path.chmod(0o600)
        except OSError:
            pass


def forget_credentials() -> None:
    for name in (TOKEN_FILE, QUERY_FILE):
        try:
            (settings.SECRETS_DIR / name).unlink()
        except FileNotFoundError:
            pass


def _credentials() -> tuple[str, str]:
    try:
        return ((settings.SECRETS_DIR / TOKEN_FILE).read_text().strip(),
                (settings.SECRETS_DIR / QUERY_FILE).read_text().strip())
    except OSError:
        raise IbkrError("Interactive Brokers is not set up — add the Flex token under Settings.") from None


# ─── The client ──────────────────────────────────────────────────────

def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise IbkrError(f"Could not reach Interactive Brokers: {exc}") from exc


class Client:
    def __init__(self, token: str, query_id: str, transport=None, sleep=time.sleep):
        self.token, self.query_id = token, query_id
        self.transport = transport or _urllib_transport
        self.sleep = sleep

    def _get(self, path: str, **query) -> str:
        url = f"{BASE}/{path}?" + urllib.parse.urlencode({"t": self.token, "v": 3, **query})
        status, body = self.transport("GET", url, {"User-Agent": "wealth-dashboard"}, None)
        if status != 200:
            raise IbkrError(f"Interactive Brokers answered {status}.")
        return body.decode("utf-8", "replace")

    @staticmethod
    def _error(xml: str) -> tuple[str, str] | None:
        code = re.search(r"<ErrorCode>\s*(\d+)\s*</ErrorCode>", xml)
        msg = re.search(r"<ErrorMessage>\s*(.*?)\s*</ErrorMessage>", xml, re.S)
        return (code.group(1), msg.group(1) if msg else "") if code else None

    def statement(self) -> str:
        """The Flex XML: ask for it, then fetch it once it is ready."""
        first = self._get("SendRequest", q=self.query_id)
        err = self._error(first)
        if err:
            raise IbkrError(_explain(*err))
        ref = re.search(r"<ReferenceCode>\s*(\S+?)\s*</ReferenceCode>", first)
        if not ref:
            raise IbkrError("Interactive Brokers did not return a reference code for the query.")
        for attempt in range(MAX_POLLS):
            xml = self._get("GetStatement", q=ref.group(1))
            if "<FlexQueryResponse" in xml:
                return xml
            err = self._error(xml)
            if err and err[0] in PENDING_CODES:
                self.sleep(POLL_SECONDS)
                continue
            raise IbkrError(_explain(*err) if err else "Interactive Brokers returned an unexpected answer.")
        raise IbkrError("Interactive Brokers is still generating the statement — try again in a minute.")


def _explain(code: str, msg: str) -> str:
    if code in ("1012", "1015"):
        return f"Interactive Brokers refused the token ({msg or 'invalid or expired'}). Make a new one under Flex Web Service."
    if code == "1014":
        return f"Interactive Brokers does not know the query id ({msg or 'invalid query'})."
    return f"Interactive Brokers: {msg or 'error ' + code} (code {code})."


def client(transport=None, sleep=time.sleep) -> Client:
    token, query_id = _credentials()
    return Client(token, query_id, transport, sleep)


# ─── Sync ────────────────────────────────────────────────────────────

def sync_link(link: dict, api: Client | None = None) -> int:
    """Pull the statement, store it, take the cash balance, check the
    positions. Returns how many rows were new."""
    api = api or client()
    xml = api.statement()
    statements = ibkr_flex.read(xml)
    if not statements:
        raise IbkrError("The Flex query returned no statement — does it include Trades and Cash Transactions?")
    wanted = link.get("remote_id")
    chosen = next((s for s in statements if not wanted or s.account_id == wanted), statements[0])
    parsed = ibkr_flex.parse(xml, account_currency=link["account_currency"])
    parsed.rows = [r for r in parsed.rows if (r.external_id or "").startswith(f"ibkr:{chosen.account_id}:")] if len(statements) > 1 else parsed.rows
    if chosen.cash.get(link["account_currency"].upper()) is not None:
        parsed.closing_balance = {"amount": round(chosen.cash[link["account_currency"].upper()], 2),
                                  "currency": link["account_currency"].upper(), "as_of": chosen.to_date}
    report = store(link["account_id"], parsed, "ibkr")
    # IBKR's positions against what the rows add up to: a gap is a
    # trade older than the query's period, said so, never patched.
    with get_conn() as conn:
        held = {r["isin"]: r["q"] for r in conn.execute(
            "SELECT isin, SUM(quantity) AS q FROM transactions WHERE account_id = ? "
            "AND isin IS NOT NULL AND quantity IS NOT NULL GROUP BY isin", (link["account_id"],))}
    drift = []
    for key, (qty, name) in chosen.positions.items():
        have = held.get(key, 0.0)
        if abs(have - qty) > 1e-6:
            drift.append(f"{name}: IBKR says {qty:g}, the rows add up to {have:g}")
    if drift:
        raise HoldingsDrift("Synced, but the holdings do not add up — " + "; ".join(drift)
                            + ". A Flex query covers a year at most; drop an older statement's XML on the import page.")
    return report["inserted"]


def describe() -> dict:
    return {"configured": credentials_present()}


def check(transport=None, sleep=time.sleep) -> dict:
    """A live look: the token works, and what the statement covers."""
    api = client(transport, sleep)
    statements = ibkr_flex.read(api.statement())
    s = statements[0] if statements else None
    return {"ok": True,
            "accounts": [x.account_id for x in statements],
            "period": (s.from_date, s.to_date) if s else None,
            "trades": sum(1 for x in statements for r in x.rows if r.kind in ("buy", "sell")),
            "cash": s.cash if s else {}}
