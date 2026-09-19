"""KBC (Belgium) — Overzicht transacties: "Uw Aankoop Online van 15
PROSUS N.V. (AS) aan 57,2 EUR 858,00 EUR", Waardecode on a later line."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}/\d{2}/\d{4})"

ROW = r"^Uw (?:Aankoop|Verkoop)\b"
TRADE_FIELDS = {
    "security": [r"^Uw (?:Aankoop|Verkoop) \S+ van (?P<shares>" + NUM + r") (?P<name>.+?) (?:aan|tegen) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$[\s\S]*?Waardecode " + ISIN],
    "date": [r"^" + DATE + r" [\d:]+ Valuta"],
    "amount": [r"^Netto (?:debit|credit) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"^Borderel (?P<ref>\d+)"],
    "fees": [r"^(?:Makelaarsloon|Kosten|Beurskosten) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Beurstaks|Roerende voorheffing|Taks) (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="kbc_pdf",
    label="KBC — transactieoverzicht PDF",
    corpus="kbcgroupnv",
    marks=[r"KBC BANK", r"KREDBEBB", r"KBC Bank"],
    docs=[
        Doc(kind="trade", when=ROW, sell=r"^Uw Verkoop", block=r"^Borderel \d+", fields=TRADE_FIELDS),
    ],
)
