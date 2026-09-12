"""Enable Banking — PSD2 account access for European banks.

Enable Banking is an aggregator: one API in front of a few thousand banks
across the EEA. You register your own application with them, which is the
only arrangement that is honest for a self-hosted app — the credentials
are yours, the consent is yours, and nothing passes through a server
belonging to whoever wrote this.

What you need, once
-------------------
1. An account at https://enablebanking.com and an application in their
   Control Panel. Note its **Application ID** (a UUID).
2. An RSA key pair. Keep the private key; upload the public half to the
   Control Panel:

       openssl genrsa -out enablebanking_private.key 4096
       openssl rsa -in enablebanking_private.key -pubout -out enablebanking_public.pem

3. Register your **redirect URL** in the Control Panel. It must match
   what this app sends, character for character.

Authentication is not OAuth
---------------------------
There is no token endpoint and nothing to refresh. Every request carries
a JWT you mint yourself and sign with that private key: `kid` is the
application id, `iss` is "enablebanking.com", `aud` is
"api.enablebanking.com". So the private key IS the credential — it never
leaves this machine, and there is no secret to rotate on their side.

The flow, end to end
--------------------
    GET  /aspsps?country=DE      which banks are available
    POST /auth                   -> {url, authorization_id}; send the user to url
    (the user authenticates at their bank and is redirected back with ?code)
    POST /sessions {code}        -> {session_id, accounts: [...]}
    GET  /accounts/{uid}/balances
    GET  /accounts/{uid}/transactions

The consent behind a session expires — 90 days is the PSD2 maximum and
what most banks grant. When it does, every call fails until the user
walks through /auth again. That is not a bug to work around; it is the
regulation, and the UI's job is to say so before the failure rather than
after.

Testing
-------
Every network call goes through the `transport` argument, so the test
suite drives the whole flow against a fake without a credential, a
network, or a bank. Nothing here imports `requests`; the standard
library is enough and one less dependency is one less thing to install
on a NAS.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

BASE_URL = "https://api.enablebanking.com"
JWT_TTL_S = 3600

# Transport signature: (method, url, headers, body|None) -> (status, bytes)
Transport = Callable[[str, str, dict, bytes | None], tuple[int, bytes]]


class EnableBankingError(RuntimeError):
    """An API call failed. Carries the status and the body, because
    Enable Banking's error bodies name the actual problem (an unknown
    ASPSP, an unregistered redirect URL) and a bare status code does
    not."""

    def __init__(self, method: str, path: str, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"{method} {path} -> {status}: {body[:400]}")


def _urllib_transport(method: str, url: str, headers: dict,
                      body: bytes | None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ─── JWT ─────────────────────────────────────────────────────────────

def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def mint_jwt(app_id: str, private_key_pem: bytes, ttl: int = JWT_TTL_S) -> str:
    """A self-signed RS256 JWT. `cryptography` is imported here rather
    than at module level so the rest of this module — and the app that
    imports it — still loads on a machine where the dependency is
    missing, and can say so."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:                      # pragma: no cover
        raise EnableBankingError(
            "JWT", "sign", 0,
            "the 'cryptography' package is required to sign requests "
            "(pip install cryptography)") from exc

    key = serialization.load_pem_private_key(private_key_pem, password=None)
    now = int(time.time())
    header = {"typ": "JWT", "alg": "RS256", "kid": app_id}
    payload = {"iss": "enablebanking.com", "aud": "api.enablebanking.com",
               "iat": now, "exp": now + ttl}
    signing_input = (
        f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    ).encode("ascii")
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input.decode()}.{_b64url(sig)}"


# ─── Client ──────────────────────────────────────────────────────────

class Client:
    """One configured connection to Enable Banking.

    The JWT is minted once per client and reused until it is close to
    expiry: signing is cheap but not free, and a sync walking a year of
    transactions makes a lot of calls.
    """

    def __init__(self, app_id: str, private_key_pem: bytes,
                 base_url: str = BASE_URL,
                 transport: Transport | None = None):
        self.app_id = app_id
        self.private_key_pem = private_key_pem
        self.base_url = base_url.rstrip("/")
        self.transport = transport or _urllib_transport
        self._jwt: str | None = None
        self._jwt_expires_at = 0.0

    # -- plumbing ----------------------------------------------------
    def jwt(self) -> str:
        if self._jwt is None or time.time() > self._jwt_expires_at - 60:
            self._jwt = mint_jwt(self.app_id, self.private_key_pem)
            self._jwt_expires_at = time.time() + JWT_TTL_S
        return self._jwt

    def request(self, method: str, path: str, *,
                params: dict | None = None,
                body: dict | None = None) -> Any:
        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        headers = {"Accept": "application/json",
                   "Authorization": f"Bearer {self.jwt()}"}
        raw = None
        if body is not None:
            raw = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"

        status, data = self.transport(method, url, headers, raw)
        if status >= 400:
            raise EnableBankingError(method, path, status,
                                     data.decode("utf-8", "replace"))
        return json.loads(data) if data else None

    # -- API ---------------------------------------------------------
    def application(self) -> dict:
        """The registered application. Used as a credential check: it is
        the cheapest call that proves the app id and the key agree, and
        it returns the redirect URLs actually registered — which is the
        setting people get wrong."""
        return self.request("GET", "/application")

    def aspsps(self, country: str) -> list[dict]:
        """Banks available in one country. `country` is an ISO-3166 alpha-2
        code — DE for Germany."""
        resp = self.request("GET", "/aspsps", params={"country": country})
        if isinstance(resp, dict):
            return resp.get("aspsps", []) or []
        return resp or []

    def start_auth(self, *, aspsp_name: str, aspsp_country: str,
                   redirect_url: str, state: str,
                   valid_until: str | None = None,
                   psu_type: str = "personal") -> dict:
        """Begin authorisation. Returns {url, authorization_id}; send the
        user to `url`.

        `state` is round-tripped by the bank and is how the callback
        knows which of possibly several pending connections came back.
        Treat it as required even though the API tolerates its absence.
        """
        if valid_until is None:
            valid_until = (datetime.now(timezone.utc)
                           + timedelta(days=90)).replace(microsecond=0).isoformat()
        return self.request("POST", "/auth", body={
            "access": {"valid_until": valid_until},
            "aspsp": {"name": aspsp_name, "country": aspsp_country},
            "redirect_url": redirect_url,
            "psu_type": psu_type,
            "state": state,
        })

    def create_session(self, code: str) -> dict:
        """Exchange the ?code from the redirect for a session. The
        response carries the accounts the user consented to share — this
        is the only moment they are enumerated."""
        return self.request("POST", "/sessions", body={"code": code})

    def session(self, session_id: str) -> dict:
        return self.request("GET", f"/sessions/{session_id}")

    def balances(self, account_uid: str) -> dict:
        return self.request("GET", f"/accounts/{account_uid}/balances")

    def transactions(self, account_uid: str, *,
                     date_from: str | None = None,
                     date_to: str | None = None,
                     continuation_key: str | None = None,
                     strategy: str = "longest",
                     transaction_status: str = "BOOK") -> dict:
        # strategy="longest" asks the bank for the most history it will
        # serve. "default" can be a very short recent window — short
        # enough to return nothing for an account with real activity —
        # and since every row is deduplicated on a stable id, asking for
        # too much is free and asking for too little is silent data loss.
        return self.request("GET", f"/accounts/{account_uid}/transactions",
                            params={"date_from": date_from,
                                    "date_to": date_to,
                                    "continuation_key": continuation_key,
                                    "strategy": strategy,
                                    "transaction_status": transaction_status})

    def all_transactions(self, account_uid: str, **kwargs) -> Iterator[dict]:
        """Walk the paginated response. The bank decides the page size.

        A continuation key is only valid with the parameters of the
        request that produced it, and the follow-up request repeats them
        — the documented rule, and right for most banks. Not for all:
        the Trade Republic connector hands back a key stamped with a
        transaction status other than the `BOOK` it was asked for, then
        rejects the identical repeat with a 422 naming the continuation
        key. The key is bound to the rest (asked for alone it is "wrong"),
        so on exactly that error the page is asked for again with the
        same parameters and the status the connector will accept: none,
        then BOTH. Pending rows that come back are dropped on
        normalisation as they always were. A 422 for any other reason
        is still an error, and a bank that accepts the repeat is never
        asked twice.
        """
        cont = None
        seen_keys: set[str] = set()
        while True:
            try:
                page = self.transactions(account_uid, continuation_key=cont, **kwargs)
            except EnableBankingError as exc:
                if cont is None or not _refuses_continuation(exc):
                    raise
                page = self._continue_anyway(account_uid, cont, kwargs, exc)
            for txn in (page.get("transactions") or []):
                yield txn
            cont = page.get("continuation_key")
            if not cont:
                return
            # A bank repeating a continuation key would spin here for
            # ever, fetching the same page. Seen once is a bug; seen
            # twice is an infinite loop with a real HTTP request in it.
            if cont in seen_keys:
                return
            seen_keys.add(cont)


    def _continue_anyway(self, account_uid: str, cont: str, kwargs: dict,
                         first: EnableBankingError) -> dict:
        """The next page from a connector that refused the repeat."""
        last = first
        for status in (None, "BOTH"):
            try:
                return self.transactions(account_uid, continuation_key=cont,
                                         **{**kwargs, "transaction_status": status})
            except EnableBankingError as exc:
                if not _refuses_continuation(exc):
                    raise
                last = exc
        raise last


def _refuses_continuation(exc: EnableBankingError) -> bool:
    """A 422 whose complaint is the continuation key — the connector's
    idea of what the key is bound to differs from ours."""
    return exc.status == 422 and "continuation" in exc.body.replace("_", "").lower()


# ─── Normalisation ───────────────────────────────────────────────────
# Turning one bank's JSON into a row. Every rule below exists because
# some bank does the awkward thing.

_BALANCE_PREFERENCE = ["ITAV", "CLBD", "XPCD", "ITBD", "OPBD", "CLAV"]


def pick_balance(payload: dict) -> dict | None:
    """Choose one balance from the several a bank reports.

    A single account commonly returns four: booked, available, and two
    provisional variants. They differ by pending card authorisations, so
    picking arbitrarily makes the number wobble between syncs for no
    visible reason. Preference order is interim-available first —
    "what could I spend now" is the number a person means by "my
    balance".
    """
    balances = payload.get("balances") or []
    by_type = {}
    for b in balances:
        t = (b.get("balance_type") or "").upper()
        if t:
            by_type.setdefault(t, b)

    for wanted in _BALANCE_PREFERENCE:
        if wanted in by_type:
            chosen = by_type[wanted]
            break
    else:
        if not balances:
            return None
        chosen = balances[0]

    amount = (chosen.get("balance_amount") or {})
    try:
        value = float(amount.get("amount"))
    except (TypeError, ValueError):
        return None
    return {"amount": value,
            "currency": amount.get("currency"),
            "balance_type": (chosen.get("balance_type") or "").upper() or None,
            "as_of": chosen.get("reference_date") or
                     datetime.now(timezone.utc).date().isoformat()}


def _description(txn: dict) -> str:
    """Banks put the human-readable text in whichever field they feel
    like. Take the first that has content, then collapse whitespace —
    several return the text as fixed-width lines padded with spaces."""
    parts: list[str] = []
    raw = txn.get("remittance_information")
    if isinstance(raw, list):
        parts.extend(str(x) for x in raw if x)
    elif raw:
        parts.append(str(raw))
    for key in ("remittance_information_unstructured",
                "additional_information", "bank_transaction_code",
                "merchant_category_code"):
        val = txn.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
            break
    text = " ".join(parts)
    return " ".join(text.split())[:500]


def _counterparty(txn: dict, indicator: str) -> str | None:
    """Whoever is at the other end. Which side that is depends on the
    direction: on money going out it is the creditor, on money coming in
    it is the debtor. Reading one field regardless gets it right half
    the time."""
    key = "creditor" if indicator == "DBIT" else "debtor"
    party = txn.get(key) or {}
    name = party.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()[:200]
    other = txn.get("debtor" if key == "creditor" else "creditor") or {}
    name = other.get("name")
    return name.strip()[:200] if isinstance(name, str) and name.strip() else None


def external_id(txn: dict, identification_hash: str) -> str:
    """A stable id, so re-importing an overlapping window is harmless.

    Most banks supply `entry_reference` and it is genuinely unique per
    account. Some supply nothing at all, and for those the id is a hash
    of the fields that identify the entry: date, amount, currency and
    description. Both are namespaced by the ACCOUNT's identification
    hash — without that, two accounts at the same bank with the same
    €4.20 coffee on the same day would collide and one would silently
    vanish.
    """
    ref = txn.get("entry_reference")
    if isinstance(ref, str) and ref.strip():
        return f"eb:{identification_hash}:{ref.strip()}"
    amount = txn.get("transaction_amount") or {}
    seed = "|".join([
        identification_hash,
        str(txn.get("booking_date") or txn.get("value_date") or ""),
        str(amount.get("amount", "")),
        str(amount.get("currency", "")),
        _description(txn),
    ])
    return f"eb:{identification_hash}:h:{hashlib.sha1(seed.encode()).hexdigest()[:20]}"


def normalise_transaction(txn: dict, identification_hash: str,
                          default_currency: str = "EUR") -> dict | None:
    """One bank transaction → one row, or None if it is not one yet.

    Returns None for a pending entry: an amount that has not settled can
    still change or disappear, and storing it means either a duplicate
    when it books or a phantom when it does not.
    """
    status = (txn.get("status") or "").upper()
    if status not in ("BOOK", ""):
        return None

    amount_obj = txn.get("transaction_amount") or {}
    try:
        magnitude = float(amount_obj.get("amount"))
    except (TypeError, ValueError):
        return None

    # The amount is reported unsigned, with the direction in a separate
    # field. Trusting the sign of the number instead would make every
    # withdrawal look like income.
    indicator = (txn.get("credit_debit_indicator") or "").upper()
    if indicator == "DBIT":
        amount = -abs(magnitude)
    elif indicator == "CRDT":
        amount = abs(magnitude)
    else:
        amount = magnitude          # a few banks omit it and do sign it

    currency = amount_obj.get("currency")
    # XXX is ISO 4217 for "no currency" and some banks send it as a
    # placeholder rather than omitting the field.
    if not currency or currency == "XXX":
        currency = default_currency

    date = (txn.get("booking_date") or txn.get("value_date")
            or txn.get("transaction_date"))
    if not date:
        return None

    return {
        "txn_date": str(date)[:10],
        "description": _description(txn),
        "counterparty": _counterparty(txn, indicator),
        "amount": amount,
        "currency": currency,
        "external_id": external_id(txn, identification_hash),
    }


def account_label(account: dict) -> str:
    """A name a person will recognise in a list. Banks fill in different
    subsets of these, so fall back rather than showing a UUID."""
    for key in ("name", "product", "cash_account_type"):
        val = account.get(key)
        if isinstance(val, str) and val.strip():
            base = val.strip()
            break
    else:
        base = "Account"
    iban = (account.get("account_id") or {}).get("iban")
    if iban:
        return f"{base} ···{str(iban)[-4:]}"
    return base


def new_state() -> str:
    return uuid.uuid4().hex


def load_private_key(path: Path) -> bytes:
    if not path.exists():
        raise EnableBankingError(
            "config", str(path), 0,
            "No private key found. Generate one with "
            "`openssl genrsa -out enablebanking_private.key 4096` and upload "
            "the public half in the Enable Banking Control Panel.")
    return path.read_bytes()
