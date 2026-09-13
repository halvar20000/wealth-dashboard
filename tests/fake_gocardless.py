"""A fake GoCardless Bank Account Data API, driven through the client's
transport hook. Invented numbers; the IBAN is in the documentation
range. Records every call so a test can say what was asked."""

from __future__ import annotations

import json
import urllib.parse

INSTITUTIONS_GB = [
    {"id": "MONZO_MONZGB2L", "name": "Monzo", "bic": "MONZGB2L", "transaction_total_days": "730",
     "countries": ["GB"], "logo": "https://example.invalid/monzo.png", "max_access_valid_for_days": "90"},
    {"id": "SANDBOXFINANCE_SFIN0000", "name": "Sandbox Finance", "bic": "SFIN0000",
     "transaction_total_days": "90", "countries": ["GB", "DE"], "max_access_valid_for_days": "90"},
]
AGREEMENT = {"id": "agr-1", "created": "2026-09-13T10:00:00Z", "max_historical_days": 730,
             "access_valid_for_days": 90, "access_scope": ["balances", "details", "transactions"],
             "accepted": "2026-09-13T10:05:00Z", "institution_id": "MONZO_MONZGB2L"}
REQUISITION_NEW = {"id": "req-1", "created": "2026-09-13T10:00:00Z", "status": "CR", "agreement": "agr-1",
                   "accounts": [], "link": "https://ob.gocardless.com/psd2/start/req-1/MONZO_MONZGB2L"}
REQUISITION_LINKED = {**REQUISITION_NEW, "status": "LN", "accounts": ["acc-11", "acc-22"]}
DETAILS = {"acc-11": {"account": {"iban": "GB33BUKB20201555555555", "currency": "GBP", "name": "Current Account", "ownerName": "Jane Roe"}},
           "acc-22": {"account": {"iban": "GB94BARC10201530093459", "currency": "GBP", "product": "Savings Pot"}}}
BALANCES = {"balances": [
    {"balanceAmount": {"amount": "1250.40", "currency": "GBP"}, "balanceType": "interimAvailable", "referenceDate": "2026-09-13"},
    {"balanceAmount": {"amount": "1300.00", "currency": "GBP"}, "balanceType": "closingBooked", "referenceDate": "2026-09-12"},
]}
TRANSACTIONS = {"transactions": {
    "booked": [
        {"transactionId": "tx-1", "bookingDate": "2026-09-10", "valueDate": "2026-09-10",
         "transactionAmount": {"amount": "-42.50", "currency": "GBP"}, "creditorName": "Tesco Stores",
         "remittanceInformationUnstructured": "TESCO STORES 3141 LONDON"},
        {"transactionId": "tx-2", "bookingDate": "2026-09-01",
         "transactionAmount": {"amount": "2500.00", "currency": "GBP"}, "debtorName": "ACME LTD",
         "remittanceInformationUnstructuredArray": ["SALARY", "SEPTEMBER"]},
        {"internalTransactionId": "int-3", "bookingDate": "2026-09-05",
         "transactionAmount": {"amount": "-9.99", "currency": "GBP"},
         "remittanceInformationUnstructured": "Netflix"},
    ],
    "pending": [
        {"bookingDate": "2026-09-13", "transactionAmount": {"amount": "-15.00", "currency": "GBP"},
         "remittanceInformationUnstructured": "PENDING CARD AUTH"},
    ],
}}


class FakeGoCardless:
    def __init__(self):
        self.calls = []
        self.linked = False
        self.fail_next = None
        self.tokens = 0

    def transport(self, method, url, headers, body):
        parsed = urllib.parse.urlparse(url)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.calls.append({"method": method, "path": parsed.path, "params": params,
                           "headers": headers, "body": json.loads(body) if body else None})
        path = parsed.path.replace("/api/v2", "", 1)
        if self.fail_next is not None:
            status, message = self.fail_next
            self.fail_next = None
            return status, json.dumps({"summary": message, "detail": message}).encode()
        if path == "/token/new/":
            self.tokens += 1
            return 200, json.dumps({"access": f"tok-{self.tokens}", "access_expires": 86400,
                                    "refresh": "ref", "refresh_expires": 2592000}).encode()
        if headers.get("Authorization") != f"Bearer tok-{self.tokens}":
            return 401, b'{"summary": "Invalid token"}'
        if path == "/institutions/":
            return 200, json.dumps(INSTITUTIONS_GB if params.get("country") == "GB" else []).encode()
        if path == "/agreements/enduser/" and method == "POST":
            return 201, json.dumps(AGREEMENT).encode()
        if path == "/agreements/enduser/agr-1/":
            return 200, json.dumps(AGREEMENT).encode()
        if path == "/requisitions/" and method == "POST":
            return 201, json.dumps(REQUISITION_NEW).encode()
        if path == "/requisitions/req-1/":
            return 200, json.dumps(REQUISITION_LINKED if self.linked else REQUISITION_NEW).encode()
        if path.startswith("/accounts/") and path.endswith("/details/"):
            acc = path.split("/")[2]
            return 200, json.dumps(DETAILS.get(acc, {"account": {}})).encode()
        if path.endswith("/balances/"):
            return 200, json.dumps(BALANCES).encode()
        if path.endswith("/transactions/"):
            return 200, json.dumps(TRANSACTIONS).encode()
        return 404, b'{"summary": "no such endpoint"}'
