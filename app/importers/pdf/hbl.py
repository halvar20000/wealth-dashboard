"""Hypothekarbank Lenzburg — the paper behind neon: Börse / Kauf,
Börse / Verkauf, Ertragsausschüttung. Swiss francs, apostrophes for
thousands, a foreign dividend changed at the rate on the page."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?P<name>.+?) Depotstelle:? ?\d*\n(?:[^\n]*\n)??Valor: \d+ / " + ISIN, r"Valor: \d+ / " + ISIN],
    "shares": [r"^Menge (?P<shares>" + NUM + r") Kurs (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Wir haben am (?P<date>" + DATE + r")", r"Zahlbar Datum: (?P<date>" + DATE + r")", r"Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Belastung|Gutschrift) [\d.]+ Valuta " + DATE + r" (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Transaktion (?P<ref>\S+)"],
    "fees": [r"^(?:Eigene Kommission[^\n]*?|Courtage[^\n]*?|B.rsengeb.hr[^\n]*?|Fremde Spesen|Spesen) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Umsatzabgabe|Verrechnungssteuer[^\n]*?|Quellensteuer[^\n]*?|Steuerr.ckbehalt[^\n]*?) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Devisenkurs (?P<fx_rate>" + NUM + r") CHF", r"(?P<fx_pair>[A-Z]{3}/CHF) (?P<fx_rate>" + NUM + r") CHF"],
}

SPEC = Spec(
    slug="hbl_pdf",
    label="Hypothekarbank Lenzburg / neon — Abrechnung PDF",
    corpus="hypothekarbanklenzburgag",
    marks=[r"Hypothekarbank Lenzburg", r"hbl\.ch", r"HYPLCH22"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^B.rse / (?:Kauf|Verkauf|Zeichnung|R.cknahme)|^Titelr.ckzahlung", sell=r"^B.rse / (?:Verkauf|R.cknahme)|^Titelr.ckzahlung|f.r Sie verkauft", fields=FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsaussch.ttung|Dividende|Kapitalr.ckzahlung)", fields=FIELDS),
    ],
)
