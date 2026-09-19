"""BoursoBank (Boursorama) — the avis d'opération de bourse (achat,
vente) and the coupons statement, French numbers with a space for
thousands."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}/\d{2}/\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?P<date>" + DATE + r") (?P<shares>" + NUM + r") (?P<name>.+?)(?: R.f.rence : \d+)?$"],
    "shares": [r"^" + DATE + r" (?P<shares>" + NUM + r") "],
    "price": [r"Cours ex.cut. : (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^(?P<date>" + DATE + r") " + NUM + r" "],
    "amount": [r"^Montant net au (?:d.bit|cr.dit) de votre compte\n(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})",
               r"^(?:" + NUM + r" [A-Z]{3} ){2,3}(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$\nSous r.serve"],
    "ref": [r"R.f.rence : (?P<ref>\d+)"],
    "fees": [r"^Montant brut Commission Frais[^\n]*\n" + NUM + r" [A-Z]{3} (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3}) ",
             r"^Montant brut Commission Frais[^\n]*\n" + NUM + r" [A-Z]{3} " + NUM + r" [A-Z]{3} (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$",
             r"^Commission Frais divers Montant total des frais\n" + NUM + r" [A-Z]{3} " + NUM + r" [A-Z]{3} (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "isin_line": [r"Code ISIN : " + ISIN],
}
TRADE_FIELDS["security"].append(r"Code ISIN : " + ISIN)

COUPON_ROW = r"^" + DATE + r" " + NUM + r" .+ \([A-Z]{2}[A-Z0-9]{9}\d\) " + NUM
COUPON_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "security": [r"^" + DATE + r" (?P<shares>" + NUM + r") (?P<name>.+?) \(" + ISIN + r"\)"],
    "amount": [r"\([A-Z]{2}[A-Z0-9]{9}\d\) (?P<gross>" + NUM + r")(?: " + NUM + r")* (?P<amount>" + NUM + r")$"],
    "gross": [r"\([A-Z]{2}[A-Z0-9]{9}\d\) (?P<gross>" + NUM + r") "],
    "type": [r"^(?P<type>" + DATE + r")"],
}
OPC_FIELDS = {
    "security": [r"^(?P<date>" + DATE + r") (?P<shares>" + NUM + r") (?P<name>.+)$", r"Code ISIN : " + ISIN],
    "date": [r"^(?P<date>" + DATE + r") " + NUM + r" "],
    "price": [r"Valeur liquidative : (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "amount": [r"^Montant brut[^\n]*Montant net au (?:d.bit|cr.dit) de votre compte\n(?:" + NUM + r" [A-Z]{3} ){3}(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "fees": [r"^Montant brut Droits[^\n]*\n" + NUM + r" [A-Z]{3} (?P<fee>" + NUM + r") [A-Z]{3} (?P<fee2>" + NUM + r") (?P<currency>[A-Z]{3}) "],
    "ref": [r"R.f.rence : (?P<ref>\d+)"],
}


def tidy(text: str) -> str:
    """"2 008,64" → "2008,64", and the ISIN line joined for the coupon rows."""
    text = re.sub(r"(\d) (\d{3},\d{2})\b", r"\1\2", text)
    return text


SPEC = Spec(
    slug="boursobank_pdf",
    label="BoursoBank — avis d'opération PDF",
    corpus="boursobank",
    marks=[r"boursobank\.com", r"Boursorama", r"BoursoBank", r"boursorama\.com", r"^OPERATION DE BOURSE\n", r"Sous r.serve de bonne fin"],
    number="de",
    preprocess=tidy,
    docs=[
        Doc(kind="trade", when=r"^OPERATION DE BOURSE", sell=r"^VENTE|au cr.dit de votre compte", fields=TRADE_FIELDS),
        Doc(kind="trade", when=r"^OPERATION SUR OPC", sell=r"^RACHAT|au cr.dit de votre compte", fields=OPC_FIELDS),
        Doc(kind="rows", when=r"^COUPONS REMBOURSEMENTS", block=COUPON_ROW, fields=COUPON_FIELDS, kinds={r".": "dividend"}),
    ],
)
