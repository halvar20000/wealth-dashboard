"""Advanzia Bank (Advanziakonto) — the Kontoauszug."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"-?[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "date": [r"^" + DATE + r" (?P<date>" + DATE + r") ", r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?:" + DATE + r" )?(?P<type>.+?) " + NUM + r"$"],
    "amount": [r"^" + DATE + r" .+? (?P<amount>" + NUM + r")$"],
}

SPEC = Spec(
    slug="advanzia_pdf",
    label="Advanzia Bank — Kontoauszug PDF",
    corpus="advanziabank",
    marks=[r"Advanzia"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^(?:Datum|Valutadatum Buchungstag) Beschreibung Betrag \((?P<currency>[A-Z]{3})\)", block=r"^" + DATE + r" .+? " + NUM + r"$", fields=FIELDS,
            kinds={r"ZINS": "interest", r"SALDO": "skip"}),
    ],
)
