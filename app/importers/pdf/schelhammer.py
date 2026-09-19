"""Schelhammer Capital Bank / die plattform (Austria) — the Abrechnung
Handel and the Ertrag, with the fund's name letter-spaced."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+(?:-{2})?"
DATE = r"\d{1,2}\.\d{1,2}\.\d{4}"

FIELDS = {
    "security": [r"^Titel: " + ISIN + r" (?P<name>.+)$"],
    "shares": [r"^(?:Zugang|Abgang): (?P<shares>" + NUM + r") Stk", r"^(?P<shares>" + NUM + r") Stk$"],
    "price": [r"^Kurs: (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^Schlusstag: (?P<date>" + DATE + r")", r"^Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Zu (?:Lasten|Gunsten) IBAN [^\n]*? (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"^Auftrags-Nr\.: (?P<ref>\S+)"],
    "fees": [r"^(?:Spesen|Provision|Geb.hr|Fremde Spesen)[^\n]*?: (?P<sign>-?)(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Kapitalertragsteuer|KESt|Quellensteuer)[^\n]*?: (?P<sign>-?)(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}


def unspace(text: str) -> str:
    """"X t r . ( I E ) - i B oxx" → the letters back together on the Titel line."""
    return re.sub(r"^(Titel: [A-Z]{2}[A-Z0-9]{9}\d) (.+)$",
                  lambda m: m.group(1) + " " + re.sub(r"(?<=\S) (?=\S(?: |$))", "", m.group(2)).strip(), text, flags=re.M)


SPEC = Spec(
    slug="schelhammer_pdf",
    label="Schelhammer Capital Bank / die plattform — Abrechnung PDF",
    corpus="schelhammercapitalbankag",
    marks=[r"Schelhammer", r"dieplattform\.at"],
    preprocess=unspace,
    docs=[
        Doc(kind="trade", when=r"^Gesch.ftsart: (?:Kauf|Verkauf|Ausgabe|R.cknahme|Ausgabe Fonds)", sell=r"^Gesch.ftsart: (?:Verkauf|R.cknahme)|^Abgang:", fields=FIELDS),
        Doc(kind="dividend", when=r"^Gesch.ftsart: (?:Ertrag|Aussch.ttung|Dividende)", fields=FIELDS),
    ],
)
