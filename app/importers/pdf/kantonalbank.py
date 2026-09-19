"""The cantonal banks on the Avaloq printer — St.Galler Kantonalbank,
Thurgauer Kantonalbank: "Abrechnung: Ihr Kauf", the position on the
line under "gekauft", Courtage and Stempelsteuer, Total, and the
settlement "Zu Ihren Lasten Valuta …" in the account's currency."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}|\d{1,2}\. [A-Za-zä]+ \d{4}"

TRADE_FIELDS = {
    "security": [r"^(?:(?P<notation>[A-Z]{3}) )?(?P<shares>" + NUM + r") (?P<name>.+?) Valoren-Nr\.:? \d+\n(?:[^\n]*\n)??[^\n]*?ISIN:? " + ISIN,
                 r"ISIN:? " + ISIN],
    "price": [r"^Kurs (?:(?P<price_currency>[A-Z]{3}) )?(?P<price>" + NUM + r")%? "],
    "date": [r"^Wir haben f.r Sie am (?P<date>" + DATE + r")", r"Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Zu Ihren (?:Lasten|Gunsten) Valuta (?:" + DATE + r") (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Referenznummer (?P<ref>\d+)"],
    "fees": [r"^(?:Courtage|Fremde Courtage|Geb.hren Gegenpartei|B.rsengeb.hr|Spesen)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Stempelsteuer|Umsatzabgabe|Quellensteuer|Verrechnungssteuer)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Wechselkurs (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
DIVIDEND_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?P<name>.+)\n(?:[^\n]*Valoren-Nr\.:? \d+, )?ISIN:? " + ISIN],
    "date": [r"^Zu Ihren (?:Gunsten|Lasten) Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Zu Ihren (?:Gunsten|Lasten) Valuta (?:" + DATE + r") (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Referenznummer (?P<ref>\d+)"],
    "taxes": [r"^(?:Quellensteuer|Verrechnungssteuer|Steuerr.ckbehalt)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}
DOCS = [
    Doc(kind="trade", when=r"^Abrechnung: Ihr (?:Kauf|Verkauf)", sell=r"^Abrechnung: Ihr Verkauf", fields=TRADE_FIELDS),
    Doc(kind="dividend", when=r"^(?:Baraussch.ttung|Dividende|Aussch.ttung|Ertragsabrechnung)\s*$", fields=DIVIDEND_FIELDS),
]

SPECS = [
    Spec(slug="sgkb_pdf", label="St.Galler Kantonalbank — Abrechnung PDF", corpus="stgallerkantonalbank",
         marks=[r"St\.Galler Kantonalbank", r"sgkb\.ch", r"KBSGCH22"], number="ch", docs=DOCS),
    Spec(slug="tkb_pdf", label="Thurgauer Kantonalbank — Abrechnung PDF", corpus="thurgauerkantonalbank",
         marks=[r"Thurgauer Kantonalbank", r"tkb\.ch", r"KBTGCH22"], number="ch", docs=DOCS),
]
