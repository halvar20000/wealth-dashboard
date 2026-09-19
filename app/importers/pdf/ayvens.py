"""Ayvens Bank (Online-Sparkonto) — the Kontoauszug."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"-?[\d.]+,\d{2}"
DATE = r"\d{2}-\d{2}-\d{4}"
ROW = r"^" + DATE + r" .*?(?:dazu|Ab) " + NUM + r" €$"

FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?P<type>.+?) " + NUM + r" €$"],
    "amount": [r" (?P<amount>" + NUM + r") (?P<currency>€)$"],
}

SPEC = Spec(
    slug="ayvens_pdf",
    label="Ayvens Bank — Kontoauszug PDF",
    corpus="ayvensbank",
    marks=[r"Ayvens Bank", r"ayvensbank\.de"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^Datum Referenzkonto Beschreibung Betrag", block=ROW, fields=FIELDS,
            kinds={r"^Zinsen dazu": "interest"}),
    ],
)
