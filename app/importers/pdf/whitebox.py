"""Whitebox — the monthly fee statement, one line per account."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
ROW = r"^\d{6,} (?:€ " + NUM + r" |[\d,]+% )?(?:€ " + NUM + r" )?€ " + NUM + r"$"
FIELDS = {
    "date": [r"^(?P<date>\d{1,2}\. [A-Za-zä]+ \d{4})$"],
    "type": [r"^(?P<type>\d{6,}) "],
    "amount": [r"^\d{6,} .*€ (?P<amount>" + NUM + r")$"],
}

SPEC = Spec(
    slug="whitebox_pdf",
    label="Whitebox — Gebührenabrechnung PDF",
    corpus="withebankgmbh",
    marks=[r"Whitebox"],
    docs=[
        Doc(kind="rows", when=r"^Geb.hrenabrechnung f.r", block=ROW, fields=FIELDS, kinds={r".": "fee"}),
    ],
)
