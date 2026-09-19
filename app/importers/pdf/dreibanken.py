"""3 Banken (Oberbank, BKS, BTV — 3-Banken-EDV) — the Wertpapier-
Abrechnung for a Kauf, Verkauf or Ausschüttung, Austrian paper with
KESt on the line."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^" + ISIN + r" (?P<name>.+?) (?:Zugang|Abgang)? ?Stk ?\. (?P<shares>" + NUM + r")"],
    "price": [r"^Kurs (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) "],
    "date": [r"^Schlusstag (?P<date>" + DATE + r")", r"Wert (?P<date>" + DATE + r") ", r"^Extag (?P<date>" + DATE + r")"],
    "amount": [r"^Wertpapierrechnung Wert " + DATE + r" (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")", r"^Summe (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Auftrags-Nr\. (?P<ref>\S+)"],
    "fees": [r"^(?:Dritt- und B.rsengeb.hr|Provision|Spesen|Geb.hr)[^\n]*? (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")$"],
    "taxes": [r"KESt(?:-Neu|-Alt)? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")"],
}

SPEC = Spec(
    slug="dreibanken_pdf",
    label="3 Banken (Oberbank, BKS, BTV) — Wertpapier-Abrechnung PDF",
    corpus="dreibankenedv",
    marks=[r"Oberbank", r"BKS Bank", r"BTV", r"Klagenfurt", r"3 ?Banken"],
    docs=[
        Doc(kind="trade", when=r"^Wertpapier-Abrechnu ?n ?g +(?:Kauf|Verkauf)", sell=r"^Wertpapier-Abrechnu ?n ?g +Verkauf|Abgang Stk", fields=FIELDS),
        Doc(kind="dividend", when=r"^Wertpapier-Abrechnu ?n ?g +(?:Aussch.ttung|Dividende|Ertrag)", fields=FIELDS),
    ],
)
