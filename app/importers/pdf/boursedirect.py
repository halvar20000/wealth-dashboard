"""Bourse Direct — the relevé d'opérations: a row per booking with the
date, the kind, the ISIN and name, and the amount in the débit or
crédit column; quantity, price and brokerage on the lines below."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}/\d{2}/\d{4}"
ROW = r"^" + DATE + r" [A-Z]"
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?P<type>[A-Z][A-Z0-9' ]+?)(?: [A-Z]{2}[A-Z0-9]{9}\d| VIRT| " + NUM + r"$)"],
    "security": [r"^" + DATE + r" [A-Z ]+? " + ISIN + r" (?P<name>.+?) " + NUM + r"$"],
    "amount": [r"^" + DATE + r" .* (?P<amount>" + NUM + r")$"],
    "shares": [r"^QUANTITE : [-+]?(?P<shares>" + NUM + r")"],
    "price": [r"^COURS : [-+]?(?P<price>" + NUM + r") "],
    "fees": [r"^COURTAGE : \+?(?P<fee>" + NUM + r") TVA : \+?(?P<fee2>" + NUM + r")", r"TVA : \+?(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:TAXE TRANSACT|TTF)[^\n]*? (?P<tax>" + NUM + r")$"],
}


def tidy(text: str) -> str:
    return re.sub(r"(\d) (\d{3},\d{2})\b", r"\1\2", text)


SPEC = Spec(
    slug="boursedirect_pdf",
    label="Bourse Direct — relevé d'opérations PDF",
    corpus="boursedirect",
    marks=[r"Bourse Direct"],
    number="de",
    preprocess=tidy,
    docs=[
        Doc(kind="rows", when=r"^Date D.signation D.bit", block=ROW, fields=FIELDS,
            kinds={r"^ACHAT": "buy", r"^VENTE": "sell", r"^COUPONS": "dividend", r"^TAXE": "tax", r"^DROITS|^FRAIS": "fee",
                   r"^INVESTISSEMENT|^VIREMENT ESPECES|^VERSEMENT": "deposit", r"^RETRAIT": "withdrawal"}),
    ],
)
