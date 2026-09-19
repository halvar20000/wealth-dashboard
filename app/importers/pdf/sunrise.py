"""Sunrise (Austria) — the Fondsabrechnung: one line with the kind, the
fund, the amount, the price and the units; the ISIN and price date below."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^(?P<type>Kauf|Verkauf|Aussch.ttung|Wiederanlage|Sparplan) (?P<name>.+?) (?P<amount>" + NUM + r") € (?P<price>" + NUM + r") € (?P<shares>" + NUM + r")$\n" + ISIN + r" (?P<date>" + DATE + r")"],
    "amount": [r"^Abrechnungsbetrag: (?P<amount>" + NUM + r") (?P<currency>€)"],
    "fees": [r"^Ausgabeaufschlag/Provision: (?P<fee>" + NUM + r") (?P<currency>€)"],
    "ref": [r"^Auftrags-Nummer: (?P<ref>\d+)"],
}

PAYOUT_FIELDS = {
    "security": [r"^Fondsname: (?P<name>.+)\nWKN/ISIN: " + ISIN],
    "shares": [r"^Anteile: (?P<shares>" + NUM + r")"],
    "date": [r"Datum des Ertrags: (?P<date>" + DATE + r")"],
    "amount": [r"^Aussch.ttung gesamt: (?P<amount>" + NUM + r")"],
}

SPEC = Spec(
    slug="sunrise_pdf",
    label="Sunrise — Fondsabrechnung PDF",
    corpus="sunrise",
    marks=[r"meetsunrise\.com", r"Sunrise Securities"],
    number="auto",
    docs=[
        Doc(kind="trade", when=r"Fondsabrechnung", sell=r"^Verkauf ", fields=FIELDS),
        # A distribution taxed away entirely: the income, and the tax on it.
        Doc(kind="dividend", when=r"^Aussch.ttung gesamt: ", fields=PAYOUT_FIELDS),
        Doc(kind="tax", when=r"^Kapitalertragsteuer \(KESt\) gesamt: ", fields={**PAYOUT_FIELDS,
            "amount": [r"^Kapitalertragsteuer \(KESt\) gesamt: (?P<amount>" + NUM + r")"]}, also=True),
    ],
)
