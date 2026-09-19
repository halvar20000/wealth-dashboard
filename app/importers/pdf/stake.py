"""Stake (Australia) — the buy and sell confirmation, a two-column
page whose labels and values interleave."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"

FIELDS = {
    "security": [r"^EFFECTIVE PRICE \$(?P<price>" + NUM + r") TICKER (?P<name>\S+)"],
    "shares": [r"^QUANTITY (?P<shares>" + NUM + r")$"],
    "date": [r"EXECUTION DATE (?P<date>\d{2}-\d{2}-\d{4})"],
    "amount": [r"^AMOUNT DUE & PAYABLE A\$(?P<amount>" + NUM + r")", r"^(?:NET PROCEEDS|AMOUNT DUE TO YOU|PROCEEDS) A\$(?P<amount>" + NUM + r")"],
    "ref": [r"^CONFIRMATION NUMBER (?P<ref>\d+)"],
    "fees": [r"^BROKERAGE & GST A\$(?P<fee>" + NUM + r")"],
}

SPEC = Spec(
    slug="stake_pdf",
    label="Stake — Confirmation PDF",
    corpus="stakeshopptyltd",
    marks=[r"Stakeshop", r"Stake"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"^(?:BUY|SELL) CONFIRMATION", sell=r"^SELL CONFIRMATION", fields=FIELDS),
    ],
)
