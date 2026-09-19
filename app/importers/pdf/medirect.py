"""MeDirect Bank (Belgium) — the Transactiebevestiging."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d+"
ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"


def quantity(text: str) -> str:
    """The quantity is printed English-style ("38.879") beside Belgian
    prices ("€ 17,49"): one notation for the row."""
    return re.sub(r"^((?:Koop|Verkoop) \S+ [A-Z]{2}[A-Z0-9]{9}\d .+? )(\d+)\.(\d+)( €)", r"\1\2,\3\4", text, flags=re.M)


FIELDS = {
    "security": [r"^(?:Koop|Verkoop) (?P<ref>\S+) " + ISIN + r" (?P<name>.+?) (?P<shares>" + NUM + r"|\d+) € (?P<price>" + NUM + r") €"],
    "date": [r"^(?P<date>\d{2}-\d{2}-\d{4}) - \d{2}:\d{2}"],
    "amount": [r"^Totaal (?P<currency>€) (?P<amount>" + NUM + r")"],
    "fees": [r"^MeDirect Commissie € (?P<fee>" + NUM + r")", r"^Wisselkosten en belastingen € (?P<fee>" + NUM + r")"],
}

SPEC = Spec(
    slug="medirect_pdf",
    label="MeDirect — Transactiebevestiging PDF",
    corpus="medirectbankplc",
    marks=[r"MeDirect"],
    number="de",
    preprocess=quantity,
    docs=[
        Doc(kind="trade", when=r"^Transactiebevestiging", sell=r"^Verkoop ", fields=FIELDS),
    ],
)
