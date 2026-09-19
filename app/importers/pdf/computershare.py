"""Computershare — the Employee Plan Statement (ESPP purchases)."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d+"
DATE = r"\d{2} [A-Z][a-z]{2} \d{4}"
ROW = r"^" + DATE + r" Purchase " + NUM

FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") Purchase "],
    "amount": [r"^" + DATE + r" Purchase (?P<amount>" + NUM + r") "],
    "fees": [r"^" + DATE + r" Purchase " + NUM + r" (?P<fee>" + NUM + r") " + NUM + r" " + DATE],
    "shares": [r" (?P<price>" + NUM + r") (?P<shares>" + NUM + r") " + NUM + r"$"],
    "security": [r"^(?P<name>[A-Z][A-Za-z ]+?) - Employee Plan Statement$"],
}

SPEC = Spec(
    slug="computershare_pdf",
    label="Computershare — Employee Plan Statement PDF",
    corpus="computershare",
    marks=[r"Computershare"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"Employee Plan Statement", block=ROW, fields=FIELDS),
    ],
)
