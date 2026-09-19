"""E*TRADE (Morgan Stanley) — the Employee Stock Plan Purchase
Confirmation."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"

FIELDS = {
    "security": [r"^Company Name \(Symbol\) (?P<name>.+?) Beginning Balance"],
    "shares": [r"^\S+ Shares Purchased (?P<shares>" + NUM + r")$"],
    "price": [r"^\(\S+ of \$" + NUM + r"\) \$(?P<price>" + NUM + r")$"],
    "date": [r"^Purchase Date (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^Total Price \((?P<currency>\$)(?P<amount>" + NUM + r")\)"],
}


def american(text: str) -> str:
    return re.sub(r"\b(\d{2})-(\d{2})-(\d{4})\b", r"\2.\1.\3", text)


SPEC = Spec(
    slug="etrade_pdf",
    label="E*TRADE — Stock Plan Purchase Confirmation PDF",
    corpus="etrade",
    marks=[r"E\*TRADE"],
    number="en",
    preprocess=american,
    docs=[
        Doc(kind="trade", when=r"^EMPLOYEE STOCK PLAN PURCHASE CONFIRMATION", fields=FIELDS),
    ],
)
