"""Crédit Mutuel Alliance Fédérale / Suravenir (Linxea) — the
Confirmation de versement on an assurance-vie contract."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d ]*\d,\d+"
ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"

FIELDS = {
    "security": [r"^(?P<name>.+?) " + ISIN + r" \d{2}/\d{2}/\d{4} (?P<price>" + NUM + r") (?P<shares>" + NUM + r") (?P<amount>" + NUM + r")$"],
    "date": [r"^.?\s?Date du versement : (?P<date>\d{2}/\d{2}/\d{4})"],
    "amount": [r"^Montant brut \(frais inclus\) : (?P<amount>" + NUM + r") (?P<currency>€)"],
    "fees": [r"^Frais de Versement : (?P<fee>" + NUM + r") €"],
}

SPEC = Spec(
    slug="creditmutuel_pdf",
    label="Crédit Mutuel / Suravenir — Confirmation de versement PDF",
    corpus="creditmutuelalliancefederale",
    marks=[r"Suravenir", r"Cr.dit Mutuel"],
    number="de",
    docs=[
        Doc(kind="trade", when=r"^Objet : Confirmation de versement", fields=FIELDS),
    ],
)
