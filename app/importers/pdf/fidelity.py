"""Fidelity (US) — the brokerage Transaction Confirmation, one block
per order under a "REFERENCE NO. TYPE …" header, and the stock-plan
purchase and sale statements."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
DATE = r"\d{2}-\d{2}-\d{2}"

BLOCK = r"^REFERENCE NO\. TYPE REG\.REP\. TRADE DATE SETTLEMENT DATE CUSIP NO\."
CONFIRM_FIELDS = {
    "date": [r"^\S+ \S+ \S+ (?P<date>" + DATE + r") " + DATE + r" "],
    "security": [r"^You (?:Bought|Sold) (?P<name>.+?) Principal Amount " + NUM + r"$\n(?P<shares>[\d.,]+) "],
    "price": [r"^at (?P<price>" + NUM + r")"],
    "amount": [r"Settlement Amount +(?P<amount>" + NUM + r")$"],
    "ref": [r"^(?P<ref>\S+) \S+ \S+ " + DATE + r" " + DATE + r" "],
    "fees": [r"^Commission (?P<fee>" + NUM + r")$", r"Activity Assessment Fee (?P<fee>" + NUM + r")$"],
}
PLAN_FIELDS = {
    "date": [r"^\S+ \S+ \S+ (?P<date>" + DATE + r") " + DATE + r" ", r"^\S+ \S+ \S+ \S+ (?P<date>" + DATE + r") " + DATE + r" "],
    "shares": [r"^YOU (?:PURCHASED|SOLD) (?P<shares>" + NUM + r") AT \$?(?P<price>" + NUM + r")"],
    "amount": [r"(?:Accumulated Contributions\*|Net Proceeds|Net Amount|Total Proceeds|Settlement Amount) +\$?(?P<amount>" + NUM + r")$"],
    "fees": [r"Total Fees +\$?(?P<fee>" + NUM + r")$"],
    "security": [r"^SECURITY DESCRIPTION SYMBOL: (?P<name>\S+)"],
}


def american(text: str) -> str:
    """Month-first dates turned round; the stock-plan sale's proceeds netted of its fees."""
    text = re.sub(r"\b(\d{2})-(\d{2})-(\d{2})\b", r"\2.\1.\3", text)
    gross = re.search(r"Sale Proceeds +\$([\d,.]+)", text)
    fees = re.search(r"Total Fees +\$([\d,.]+)", text)
    if gross and fees:
        net = float(gross.group(1).replace(",", "")) - float(fees.group(1).replace(",", ""))
        text += f"\nNet Proceeds ${net:,.2f}\n"
    return text


SPEC = Spec(
    slug="fidelity_pdf",
    label="Fidelity — Transaction Confirmation PDF",
    corpus="fidelityinternational",
    marks=[r"Fidelity", r"FIDELITY"],
    number="en",
    preprocess=american,
    docs=[
        Doc(kind="trade", when=BLOCK, block=BLOCK, sell=r"^You Sold", fields={**CONFIRM_FIELDS,
            "date": [r"^\S+ \S+ \S+ (?P<date>\d{2}\.\d{2}\.\d{2}) \d{2}\.\d{2}\.\d{2} "],
            "ref": [r"^(?P<ref>\S+) \S+ \S+ \d{2}\.\d{2}\.\d{2} \d{2}\.\d{2}\.\d{2} "]}),
        Doc(kind="trade", when=r"^YOU (?:PURCHASED|SOLD) ", sell=r"^YOU SOLD", fields={**PLAN_FIELDS,
            "date": [r"^\S+ \S+ \S+ (?P<date>\d{2}\.\d{2}\.\d{2}) \d{2}\.\d{2}\.\d{2} ", r"^\S+ \S+ \S+ \S+ (?P<date>\d{2}\.\d{2}\.\d{2}) \d{2}\.\d{2}\.\d{2} "]}),
    ],
)
