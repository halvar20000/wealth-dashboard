"""findependent — ETF-Kauf, ETF-Verkauf, Ertragsausschüttung,
Einzahlung, the quarterly Verwaltungsgebühren and their refund."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^ETF-Name (?P<name>.+)\nISIN " + ISIN],
    "shares": [r"^Anzahl Anteile (?P<shares>" + NUM + r")"],
    "price": [r"^Preis pro Anteil (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Valuta (?P<date>" + DATE + r")", r"^Lenzburg, (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Verrechneter Betrag|Gutgeschriebener Betrag|Ertrag total CHF|Betrag|Verwaltungsgeb.hren|Depotgeb.hren|R.ckerstattung[^\n]*?|Gutschrift[^\n]*?) (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")$"],
    "fees": [r"^(?:B.rsenabgaben|Courtage|Kommission|Geb.hren) (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Stempelabgaben|Verrechnungssteuer[^\n]*?|Quellensteuer[^\n]*?) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="findependent_pdf",
    label="findependent — Abrechnung PDF",
    corpus="findependentag",
    marks=[r"findependent"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^ETF-(?:Kauf|Verkauf)", sell=r"^ETF-Verkauf", fields=FIELDS),
        Doc(kind="dividend", when=r"^Ertragsaussch.ttung", fields=FIELDS),
        Doc(kind="deposit", when=r"^(?:Einzahlung|Willkommensbonus)", fields=FIELDS),
        Doc(kind="withdrawal", when=r"^Auszahlung", fields=FIELDS),
        Doc(kind="fee", when=r"^(?:Verwaltungsgeb.hren|Depotgeb.hren|Geb.hrenerstattung|R.ckerstattung)", fields=FIELDS),
    ],
)
