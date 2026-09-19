"""Crowdestor (Flex) — the account statement."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" \S+ (?P<type>\S+)"],
    "amount": [r" (?P<amount>[+-]" + NUM + r") " + NUM + r"w?$"],
    "ref": [r"^" + DATE + r" (?P<ref>\S+) "],
}

SPEC = Spec(
    slug="crowdestor_pdf",
    label="Crowdestor — Flex statement PDF",
    corpus="crowdestor",
    marks=[r"FLEX STATEMENT - CR-", r"Crowdestor"],
    number="en",
    docs=[
        Doc(kind="rows", when=r"^Date Goal Type Amount \((?P<currency>€)\)", block=r"^" + DATE + r" \S+ ", fields=FIELDS,
            kinds={r"^Profit": "interest", r"^Deposit": "deposit", r"^Automatic|withdrawal": "withdrawal"}),
    ],
)
