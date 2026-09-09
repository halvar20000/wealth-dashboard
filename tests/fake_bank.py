"""A fake Enable Banking, and a DKB-shaped payload to drive it.

The whole client goes through one `transport` callable, so the tests
exercise the real code path — URL building, JWT header, pagination,
error handling — against this instead of the network. Nothing here is
recorded from anyone's real account; the numbers are invented and the
IBAN is in the documentation range.
"""

from __future__ import annotations

import json
import urllib.parse

APP_ID = "11111111-2222-3333-4444-555555555555"

# openssl genrsa 2048, generated for this test file and used nowhere else.
# A test that skips signing does not test signing.
TEST_KEY_BITS = 2048

ASPSPS_DE = {
    "aspsps": [
        {"name": "DKB", "country": "DE", "psu_types": ["personal", "business"],
         "logo": "https://example.invalid/dkb.png"},
        {"name": "Deutsche Bank", "country": "DE", "psu_types": ["personal"]},
        {"name": "Sparkasse", "country": "DE", "psu_types": ["personal"]},
        {"name": "N26", "country": "DE", "psu_types": ["personal"]},
        # Enable Banking flags its test banks. They sort to the top of the
        # picker: a sandbox and a real bank are indistinguishable in a
        # table of names, and picking the wrong one spends a consent.
        {"name": "Mock ASPSP", "country": "DE", "psu_types": ["personal"],
         "sandbox": True},
    ]
}

AUTH_RESPONSE = {
    "url": "https://banking.dkb.invalid/psd2/authorize?request=abc123",
    "authorization_id": "auth-9f8e7d",
    "psu_id_hash": "hash-psu",
}

SESSION_RESPONSE = {
    "session_id": "sess-abcdef123456",
    "access": {"valid_until": "2027-01-01T00:00:00+00:00"},
    "aspsp": {"name": "DKB", "country": "DE"},
    "accounts": [
        {
            "uid": "acct-uid-0001",
            "identification_hash": "idhash0001",
            "account_id": {"iban": "DE02120300000000202051"},
            "name": "Girokonto",
            "product": "DKB Cash",
            "currency": "EUR",
            "cash_account_type": "CACC",
        }
    ],
}

BALANCES_RESPONSE = {
    "balances": [
        # Deliberately out of preference order, and with the "wrong" one
        # first: a picker that takes balances[0] passes a naive test and
        # shows a different number every sync in real life.
        {"balance_type": "CLBD", "balance_amount": {"amount": "1500.00", "currency": "EUR"},
         "reference_date": "2026-09-08"},
        {"balance_type": "ITAV", "balance_amount": {"amount": "1428.55", "currency": "EUR"},
         "reference_date": "2026-09-08"},
    ]
}

# Two pages, to exercise the continuation key.
TRANSACTIONS_PAGE_1 = {
    "transactions": [
        {
            "entry_reference": "DKB-2026-09-08-0001",
            "booking_date": "2026-09-08",
            "value_date": "2026-09-08",
            "status": "BOOK",
            "credit_debit_indicator": "DBIT",
            "transaction_amount": {"amount": "42.90", "currency": "EUR"},
            "creditor": {"name": "REWE Markt GmbH"},
            "remittance_information": ["REWE SAGT DANKE", "  25873946  "],
        },
        {
            "entry_reference": "DKB-2026-09-05-0002",
            "booking_date": "2026-09-05",
            "status": "BOOK",
            "credit_debit_indicator": "CRDT",
            "transaction_amount": {"amount": "3200.00", "currency": "EUR"},
            "debtor": {"name": "Arbeitgeber GmbH"},
            "remittance_information": ["GEHALT 09/2026"],
        },
        {
            # Pending. Must not be stored: it can still change or vanish,
            # and storing it means a duplicate when it books.
            "entry_reference": "DKB-2026-09-09-0003",
            "booking_date": "2026-09-09",
            "status": "PDNG",
            "credit_debit_indicator": "DBIT",
            "transaction_amount": {"amount": "12.00", "currency": "EUR"},
        },
    ],
    "continuation_key": "page-2",
}

TRANSACTIONS_PAGE_2 = {
    "transactions": [
        {
            # No entry_reference: the id has to be hashed from content.
            "booking_date": "2026-08-30",
            "status": "BOOK",
            "credit_debit_indicator": "DBIT",
            "transaction_amount": {"amount": "9.99", "currency": "XXX"},
            "creditor": {"name": "Streaming Dienst"},
            "remittance_information": ["ABO AUGUST"],
        },
        {
            # No direction field at all. A few banks sign the amount
            # themselves; trusting the indicator alone would drop this.
            "entry_reference": "DKB-2026-08-28-0005",
            "booking_date": "2026-08-28",
            "status": "BOOK",
            "transaction_amount": {"amount": "-25.00", "currency": "EUR"},
            "remittance_information": ["BARGELDAUSZAHLUNG"],
        },
    ],
}

APPLICATION_RESPONSE = {
    "name": "wealth-dashboard-test",
    "redirect_urls": ["http://localhost:8000/connect/callback"],
    "active": True,
}


class FakeBank:
    """Records every call so the tests can assert on what was sent, not
    only on what came back."""

    def __init__(self):
        self.calls: list[dict] = []
        self.fail_next: tuple[int, str] | None = None

    def transport(self, method: str, url: str, headers: dict,
                  body: bytes | None) -> tuple[int, bytes]:
        parsed = urllib.parse.urlparse(url)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.calls.append({"method": method, "path": parsed.path,
                           "params": params, "headers": headers,
                           "body": json.loads(body) if body else None})

        if self.fail_next is not None:
            status, message = self.fail_next
            self.fail_next = None
            return status, json.dumps({"message": message}).encode()

        path = parsed.path
        if path == "/application":
            return 200, json.dumps(APPLICATION_RESPONSE).encode()
        if path == "/aspsps":
            if params.get("country") != "DE":
                return 200, json.dumps({"aspsps": []}).encode()
            return 200, json.dumps(ASPSPS_DE).encode()
        if path == "/auth":
            return 200, json.dumps(AUTH_RESPONSE).encode()
        if path == "/sessions":
            return 200, json.dumps(SESSION_RESPONSE).encode()
        if path.endswith("/balances"):
            return 200, json.dumps(BALANCES_RESPONSE).encode()
        if path.endswith("/transactions"):
            if params.get("continuation_key") == "page-2":
                return 200, json.dumps(TRANSACTIONS_PAGE_2).encode()
            return 200, json.dumps(TRANSACTIONS_PAGE_1).encode()
        return 404, b'{"message": "no such endpoint"}'
