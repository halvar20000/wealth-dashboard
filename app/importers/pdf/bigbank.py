"""Bigbank (Tagesgeld) — the monthly Kontoauszug."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[+-]?[\d ]*\d,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?:[A-Z]{2}\d{2}[A-Z0-9]+ )?(?P<type>\S+)"],
    "amount": [r" (?P<amount>" + NUM + r")$"],
}

SPEC = Spec(
    slug="bigbank_pdf",
    label="Bigbank — Kontoauszug PDF",
    corpus="bigbank",
    marks=[r"BIGBANK AS", r"bigbank\.at", r"bigbank\.de"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^Datum Gegenkonto Buchung Name Betrag in EUR", block=r"^" + DATE + r" .*" + NUM + r"$", fields=FIELDS,
            kinds={r"^Einzahlung": "deposit", r"^Auszahlung": "withdrawal", r"^Zins": "interest"}),
    ],
)
