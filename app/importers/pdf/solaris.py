"""Solaris (Solarisbank) — the Girokonto and reference account
statements it prints for the fintechs it banks."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"-?[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"
GIRO_ROW = r"^" + DATE + r" " + DATE + r" \S.* " + NUM + r" EUR$"
GIRO_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") " + DATE + r" "],
    "amount": [r"^" + DATE + r" " + DATE + r" (?P<type>.+?) (?P<amount>" + NUM + r") (?P<currency>EUR)$"],
    "type": [r"^" + DATE + r" " + DATE + r" (?P<type>.+?) " + NUM + r" EUR$"],
}
REF_ROW = r"^\S.* " + DATE + r" " + DATE + r" " + NUM + r"€$"
REF_FIELDS = {
    "date": [r"^.* (?P<date>" + DATE + r") " + DATE + r" " + NUM + r"€$"],
    "amount": [r"^(?P<type>.+?) " + DATE + r" " + DATE + r" (?P<amount>" + NUM + r")(?P<currency>€)$"],
    "type": [r"^(?P<type>.+?) " + DATE + r" " + DATE + r" " + NUM + r"€$"],
}

SPEC = Spec(
    slug="solaris_pdf",
    label="Solaris — Kontoauszug PDF",
    corpus="solarisbank",
    marks=[r"Solarisbank", r"Solaris SE", r"SOBKDEB2"],
    number="auto",
    docs=[
        Doc(kind="rows", when=r"^Buchung Wertstellung Typ Beschreibung Betrag", block=GIRO_ROW, fields=GIRO_FIELDS,
            kinds={r"Zins": "interest", r"Geb.hr|Entgelt": "fee"}),
        Doc(kind="rows", when=r"^Transaktionen Buchungsdatum Valutadatum", block=REF_ROW, fields=REF_FIELDS,
            kinds={r"Zins": "interest", r"Geb.hr|Entgelt": "fee"}),
    ],
)
