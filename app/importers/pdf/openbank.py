"""Openbank (Santander, Spain) — the fund transaction note in its
German translation, letter-spaced labels and all."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"

FIELDS = {
    "security": [r"^D ?A ?T ?U ?M ?: \d{2}-\d{2}-\d{4} (?P<name>.+?) W ?E ?C ?H", r"^I ?S ?I ?N ?: " + ISIN],
    "shares": [r"^BETEILIGUNGEN (?P<shares>" + NUM + r")"],
    "price": [r"^NETTOINVENTARWERT (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^DATUM NETTOINVENTARWERT (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^NETTOBETRAG (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "fees": [r"^GESAMTKOSTEN (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})"],
}

SPEC = Spec(
    slug="openbank_pdf",
    label="Openbank — Transaktionsabrechnung PDF",
    corpus="openbanksa",
    marks=[r"OPEN BANK", r"Openbank", r"TRANSAKTIONSABRECHNUNG"],
    docs=[
        Doc(kind="trade", when=r"^TRANSAKTION (?:ZEICHNUNG|R.CKERSTATTUNG|MAXIMAL VERF.GBARE ERSTATTUNG|KAUF|VERKAUF)", sell=r"^TRANSAKTION (?:R.CKERSTATTUNG|MAXIMAL VERF.GBARE ERSTATTUNG|VERKAUF)", fields=FIELDS),
    ],
)
