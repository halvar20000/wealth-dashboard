"""Ginmon — the monthly Gebührenabrechnung / fee invoice."""

from __future__ import annotations

from ..statement import Doc, Spec

FIELDS = {
    "date": [r"^Rechnungsdatum / Invoice date: (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^Rechnungsbetrag (?P<amount>[\d.,]+) (?P<currency>€)"],
    "ref": [r"^Rechnungsnummer ?/ ?Invoice no: (?P<ref>\d+)"],
}

SPEC = Spec(
    slug="ginmon_pdf",
    label="Ginmon — Gebührenabrechnung PDF",
    corpus="ginmon",
    marks=[r"Ginmon"],
    number="en",
    docs=[
        Doc(kind="fee", when=r"^Geb.hrenabrechnung", fields=FIELDS),
    ],
)
