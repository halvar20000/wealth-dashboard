"""GoCardless Bank Account Data — the aggregator that used to be Nordigen.

The second way into a bank, beside Enable Banking. Same idea, other
company: an API that talks PSD2 to two and a half thousand banks in
Europe and, unlike Enable Banking, the United Kingdom, and hands back
Berlin-Group-shaped JSON. It has no private key to manage — a secret
id and a secret key from the portal become a short-lived access
token — and it registers no redirect URLs at all, which is one thing
fewer to get wrong.

The flow, in their words:

    token/new        secret id + key → access token (a day)
    institutions     the banks of a country
    requisitions     "connect this bank, send them back here" → a link
    …the user goes to the bank and comes back with ?ref=…
    requisitions/id  status LN (linked) and the account ids
    accounts/id/…    details, balances, transactions

An end-user agreement sets how long the access lasts (90 days is the
PSD2 default and the bank's ceiling); the requisition carries it. The
`reference` on the requisition is this app's state, so the callback
knows what it was doing — see sync.py.

Like the Enable Banking client this one goes through one `transport`
callable, so a test drives the whole code path against a fake.
"""

from __future__ import annotations

import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Iterator

BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"
TIMEOUT = 30
DEFAULT_ACCESS_DAYS = 90
DEFAULT_HISTORY_DAYS = 730

Transport = Callable[[str, str, dict, bytes | None], tuple[int, bytes]]


class GoCardlessError(Exception):
    def __init__(self, method: str, path: str, status: int, body: str):
        self.method, self.path, self.status, self.body = method, path, status, body
        super().__init__(f"{method} {path} -> {status}: {body[:300]}")


def _urllib_transport(method: str, url: str, headers: dict,
                      body: bytes | None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


class Client:
    def __init__(self, secret_id: str, secret_key: str, base_url: str = BASE_URL,
                 transport: Transport | None = None):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport or _urllib_transport
        self._access: str | None = None
        self._access_expires_at = 0.0

    # -- plumbing ----------------------------------------------------
    def token(self) -> str:
        if self._access is None or time.time() > self._access_expires_at - 60:
            data = self._call("POST", "/token/new/", body={"secret_id": self.secret_id,
                                                           "secret_key": self.secret_key}, auth=False)
            self._access = data["access"]
            self._access_expires_at = time.time() + int(data.get("access_expires") or 86400)
        return self._access

    def _call(self, method: str, path: str, *, params: dict | None = None,
              body: dict | None = None, auth: bool = True) -> Any:
        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        headers = {"Accept": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self.token()}"
        raw = None
        if body is not None:
            raw = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, data = self.transport(method, url, headers, raw)
        if status >= 400:
            raise GoCardlessError(method, path, status, data.decode("utf-8", "replace"))
        return json.loads(data) if data else None

    def request(self, method: str, path: str, **kw) -> Any:
        return self._call(method, path, **kw)

    # -- API ---------------------------------------------------------
    def institutions(self, country: str) -> list[dict]:
        resp = self._call("GET", "/institutions/", params={"country": country.upper()})
        return resp if isinstance(resp, list) else []

    def create_agreement(self, institution_id: str, access_days: int = DEFAULT_ACCESS_DAYS,
                         history_days: int = DEFAULT_HISTORY_DAYS) -> dict:
        return self._call("POST", "/agreements/enduser/", body={
            "institution_id": institution_id,
            "max_historical_days": history_days,
            "access_valid_for_days": access_days,
            "access_scope": ["balances", "details", "transactions"]})

    def create_requisition(self, institution_id: str, redirect: str, reference: str,
                           agreement_id: str | None = None, language: str = "EN") -> dict:
        body = {"redirect": redirect, "institution_id": institution_id,
                "reference": reference, "user_language": language.upper()[:2]}
        if agreement_id:
            body["agreement"] = agreement_id
        return self._call("POST", "/requisitions/", body=body)

    def requisition(self, requisition_id: str) -> dict:
        return self._call("GET", f"/requisitions/{requisition_id}/")

    def agreement(self, agreement_id: str) -> dict:
        return self._call("GET", f"/agreements/enduser/{agreement_id}/")

    def account_details(self, account_id: str) -> dict:
        resp = self._call("GET", f"/accounts/{account_id}/details/")
        return (resp or {}).get("account") or {}

    def account(self, account_id: str) -> dict:
        return self._call("GET", f"/accounts/{account_id}/") or {}

    def balances(self, account_id: str) -> dict:
        return self._call("GET", f"/accounts/{account_id}/balances/") or {}

    def transactions(self, account_id: str, date_from: str | None = None,
                     date_to: str | None = None) -> dict:
        return self._call("GET", f"/accounts/{account_id}/transactions/",
                          params={"date_from": date_from, "date_to": date_to}) or {}

    def all_transactions(self, account_id: str, date_from: str | None = None) -> Iterator[dict]:
        """The booked ones. GoCardless does not page; a whole window
        comes at once, and pending entries are listed apart and left
        out here for the same reason as everywhere in this app: an
        amount that has not settled can still change or vanish."""
        payload = self.transactions(account_id, date_from)
        for txn in (payload.get("transactions") or {}).get("booked") or []:
            yield txn


# ─── Interpreting what came back ─────────────────────────────────────

# Which of a bank's several balances is "the" balance — see the Enable
# Banking client for why one is chosen and why this order.
_BALANCE_PREFERENCE = ("interimAvailable", "expected", "closingBooked",
                       "interimBooked", "openingBooked", "authorised", "forwardAvailable")


def pick_balance(payload: dict) -> dict | None:
    balances = payload.get("balances") or []
    by_type = {}
    for b in balances:
        t = b.get("balanceType") or ""
        if t:
            by_type.setdefault(t, b)
    chosen = next((by_type[w] for w in _BALANCE_PREFERENCE if w in by_type), None)
    if chosen is None:
        if not balances:
            return None
        chosen = balances[0]
    amount = chosen.get("balanceAmount") or {}
    try:
        value = float(amount.get("amount"))
    except (TypeError, ValueError):
        return None
    return {"amount": value, "currency": amount.get("currency"),
            "balance_type": (chosen.get("balanceType") or "").upper() or None,
            "as_of": chosen.get("referenceDate") or datetime.now(timezone.utc).date().isoformat()}


def _description(txn: dict) -> str:
    parts: list[str] = []
    arr = txn.get("remittanceInformationUnstructuredArray")
    if isinstance(arr, list):
        parts.extend(str(x) for x in arr if x)
    for key in ("remittanceInformationUnstructured", "remittanceInformationStructured",
                "additionalInformation", "proprietaryBankTransactionCode"):
        val = txn.get(key)
        if isinstance(val, str) and val.strip() and val.strip() not in parts:
            parts.append(val.strip())
            break
    return " ".join(" ".join(parts).split())[:500]


def normalise_transaction(txn: dict, default_currency: str = "EUR") -> dict | None:
    """One booked transaction → one row, the shape sync.py stores.

    The amount is signed by the bank here — a debit is negative — which
    is the one place this feed differs from Enable Banking's unsigned
    amount with a direction beside it. The id is the bank's
    transactionId, or its internalTransactionId, or a hash of what the
    row says when the bank sends neither.
    """
    amount_obj = txn.get("transactionAmount") or {}
    try:
        amount = float(amount_obj.get("amount"))
    except (TypeError, ValueError):
        return None
    currency = amount_obj.get("currency") or default_currency
    day = txn.get("bookingDate") or txn.get("valueDate") or (txn.get("bookingDateTime") or "")[:10]
    if not day:
        return None
    counterparty = txn.get("creditorName") if amount < 0 else txn.get("debtorName")
    counterparty = " ".join(str(counterparty).split())[:200] if counterparty else None
    ref = txn.get("transactionId") or txn.get("internalTransactionId") or txn.get("entryReference")
    if ref:
        external_id = f"gc:{str(ref).strip()[:120]}"
    else:
        import hashlib
        seed = "|".join([str(day)[:10], f"{amount:.2f}", currency, _description(txn), counterparty or ""])
        external_id = "gc:" + hashlib.sha1(seed.encode()).hexdigest()[:24]
    return {"txn_date": str(day)[:10], "description": _description(txn) or (counterparty or "—"),
            "counterparty": counterparty, "amount": amount, "currency": currency,
            "external_id": external_id}


def account_label(details: dict, fallback: str = "") -> str:
    for key in ("name", "displayName", "product", "ownerName"):
        val = details.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:80]
    iban = details.get("iban")
    if isinstance(iban, str) and len(iban) > 4:
        return f"…{iban[-4:]}"
    return fallback or "Account"


def new_state() -> str:
    return secrets.token_urlsafe(24)


def valid_until(agreement: dict | None, requisition: dict | None = None) -> str | None:
    """When the access ends: the agreement's accepted date plus its
    days, or the requisition's creation plus ninety if there is none."""
    days = DEFAULT_ACCESS_DAYS
    start = None
    if agreement:
        try:
            days = int(agreement.get("access_valid_for_days") or days)
        except (TypeError, ValueError):
            pass
        start = agreement.get("accepted")
    if not start and requisition:
        start = requisition.get("created")
    try:
        when = datetime.fromisoformat(str(start).replace("Z", "+00:00")) if start else datetime.now(timezone.utc)
    except ValueError:
        when = datetime.now(timezone.utc)
    return (when + timedelta(days=days)).isoformat(timespec="seconds")
