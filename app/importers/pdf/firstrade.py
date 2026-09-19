"""Firstrade Securities (Apex Clearing) — the one-line trade confirmation."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
DATE = r"\d{2}\.\d{2}\.\d{2}"

FIELDS = {
    "security": [r"^YOU (?:BOUGHT|SOLD) (?P<name>\S+)(?: (?P<ref>[A-Z0-9]{9}))? " + DATE + r" (?P<date>" + DATE + r") \S+ (?P<shares>" + NUM + r") \$(?P<price>" + NUM + r")$"],
    "amount": [r"NET AMOUNT (?P<currency>\$)(?P<amount>" + NUM + r")$"],
    "fees": [r"(?:^|[A-Z]+ )(?:OPTION FEE|FEES|CONTRACT FEES|COMMISSION) \$(?P<fee>" + NUM + r")$"],
}


def american(text: str) -> str:
    return re.sub(r"\b(\d{2})/(\d{2})/(\d{2})\b", r"\2.\1.\3", text)


SPEC = Spec(
    slug="firstrade_pdf",
    label="Firstrade — trade confirmation PDF",
    corpus="firstradesecuritiesinc",
    marks=[r"FIRSTRADE", r"Apex Clearing Corporation"],
    number="en",
    preprocess=american,
    docs=[
        Doc(kind="trade", when=r"^YOU (?:BOUGHT|SOLD) ", sell=r"^YOU SOLD ", fields=FIELDS),
    ],
)
