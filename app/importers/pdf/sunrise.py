"""Sunrise (Austria) — the Fondsabrechnung: one line with the kind, the
fund, the amount, the price and the units; the ISIN and price date below."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^(?P<type>Kauf|Verkauf|Aussch.ttung|Wiederanlage|Sparplan) (?P<name>.+?) (?P<amount>" + NUM + r") € (?P<price>" + NUM + r") € (?P<shares>" + NUM + r")$\n" + ISIN + r" (?P<date>" + DATE + r")"],
    "date": [r"^(?:Wien|Berlin), (?P<date>" + DATE + r")"],
    "amount": [r"^Abrechnungsbetrag: (?P<amount>" + NUM + r") (?P<currency>€)"],
    "fees": [r"^Ausgabeaufschlag/Provision: (?P<fee>" + NUM + r") (?P<currency>€)"],
    "ref": [r"^Auftrags-Nummer: (?P<ref>\d+)"],
}

PAYOUT_FIELDS = {
    "security": [r"^Fondsname: (?P<name>.+)\nWKN/ISIN: " + ISIN],
    "shares": [r"^Anteile: (?P<shares>" + NUM + r")"],
    "date": [r"Datum des Ertrags: (?P<date>" + DATE + r")"],
    "amount": [r"^Zur Wieder(?:veranlagung|anlage)(?:/Auszahlung)? zur Verf.gung stehend: (?P<amount>" + NUM + r")", r"^Aussch.ttung gesamt: (?P<amount>" + NUM + r")"],
    "taxes": [r"^Kapitalertragss?teuer \(KESt\) gesamt: (?P<tax>" + NUM + r")"],
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
        # Taxed away entirely: the income, and the tax on it as a row of its own.
        Doc(kind="tax", when=r"^Zur Auszahlung kommender Betrag: 0[.,]00", fields={**PAYOUT_FIELDS, "taxes": [],
            "amount": [r"^Kapitalertragss?teuer \(KESt\) gesamt: (?P<amount>" + NUM + r")"]}, also=True),
    ],
)

# Simpel (own360) prints the same paper from Vienna.
SIMPEL = Spec(slug="simpel_pdf", label="Simpel / own360 — Fondsabrechnung PDF", corpus="simpel",
              marks=[r"Simpel S\.A\.", r"own360"], number="auto", docs=SPEC.docs)
SPECS = [SPEC, SIMPEL]
