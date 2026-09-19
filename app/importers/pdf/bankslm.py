"""Bank SLM (Spar + Leihkasse Münsingen) — Börsenabrechnung and
Dividende, Swiss paper with mangled umlauts."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?:Anteile )?(?P<name>.+)\n(?P<name2>.+)\nValor: (?P<ref>\d+)",
                 r"^(?P<shares>" + NUM + r") (?:Anteile )?(?P<name>.+)\n(?:[^\n]*\n)?[^\n]*\nValor: (?P<ref>\d+)", r"^ISIN: " + ISIN],
    "price": [r"^Menge/Nominal Preis\n" + NUM + r" (?P<price>" + NUM + r")", r"^Menge Ausf.hrung Preis Wrg Betrag\n" + NUM + r" \S+ (?P<price>" + NUM + r") "],
    "date": [r"^Wir haben f.r Sie am (?P<date>" + DATE + r")", r"Valuta: (?P<date>" + DATE + r")"],
    "amount": [r"^Netto (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "fees": [r"^(?:Eigene Courtage|Courtage|B.rsengeb.hr|Fremde Spesen)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Umsatzabgabe|\d+% Verrechnungssteuer|Verrechnungssteuer|Quellensteuer)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Change (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
DIVIDEND_FIELDS = {
    "security": [r"^ISIN: " + ISIN, r"^Valor: (?P<ref>\d+)"],
    "shares": [r"^Bestand: (?P<shares>" + NUM + r") zu "],
    "date": [r"^Am (?P<date>" + DATE + r") wurde", r"per (?P<date>" + DATE + r")"],
    "amount": [r"^Netto (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "taxes": [r"^(?:\d+% )?(?:Verrechnungssteuer|Quellensteuer)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="bankslm_pdf",
    label="Bank SLM — Abrechnung PDF",
    corpus="bankslm",
    marks=[r"Bank SLM", r"Spar \+ Leihkasse M.nsingen", r"M.nsingen"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^B.rsenabrechnung - (?:Kauf|Verkauf|Zeichnung|R.cknahme|Emission)", sell=r"^B.rsenabrechnung - (?:R.cknahme|Verkauf)|f.r Sie am \S+ verkauft", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Dividende\s*$", fields=DIVIDEND_FIELDS),
    ],
)

# The same Finnova paper under other letterheads.
SPECS = [
    SPEC,
    Spec(slug="radicant_pdf", label="radicant / Basellandschaftliche Kantonalbank — Abrechnung PDF", corpus="basellandschaftlichekantonalbank",
         marks=[r"radicant", r"Basellandschaftliche Kantonalbank", r"BLKB"], number="ch", docs=SPEC.docs),
    Spec(slug="fkb_pdf", label="Freiburger Kantonalbank — Abrechnung PDF", corpus="freiburgerkantonalbank",
         marks=[r"fkb\.ch", r"Freiburger Kantonalbank", r"BCF / FKB"], number="ch", docs=SPEC.docs),
]
