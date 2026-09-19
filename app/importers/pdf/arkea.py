"""Arkéa Direct Bank / Fortuneo (France) — Avis d'opérations: the
security on its own line, then the row with Quantité and Cours."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}-\d{2}-\d{4})"

TRADE_FIELDS = {
    "security": [r"^. (?:ACTION|ETF|OPCVM|OBLIGATION|TRACKER|FONDS) : (?P<name>.+?) \(" + ISIN + r"\)"],
    "shares": [r"^Quantit. (?P<shares>" + NUM + r") Cours (?P<price>" + NUM + r") (?P<price_currency>€|[A-Z]{3})"],
    "date": [r"^" + DATE + r" R.f.rence"],
    "amount": [r"^Montant NET (?P<amount>" + NUM + r") €"],
    "ref": [r"R.f.rence (?P<ref>\S+)"],
    "fees": [r"^(?:Courtage et Commission|Courtage|Commission|Frais) (?P<fee>" + NUM + r") €"],
    "taxes": [r"^(?:Taxe sur les Transactions Financi.res|TTF|Imp.t|Pr.l.vements) (?P<tax>" + NUM + r") €"],
}

SPEC = Spec(
    slug="arkea_pdf",
    label="Arkéa Direct Bank / Fortuneo — avis d'opérations PDF",
    corpus="arkeadirectbank",
    marks=[r"ARKEA", r"Ark.a", r"Fortuneo", r"AVIS D'OP.RATIONS"],
    docs=[
        Doc(kind="trade", when=r"^\d{2}:\d{2}:\d{2} Sens (?:Achat|Vente)", sell=r"Sens Vente", block=r"^. (?:ACTION|ETF|OPCVM|OBLIGATION|TRACKER|FONDS) : ", fields=TRADE_FIELDS),
    ],
)
