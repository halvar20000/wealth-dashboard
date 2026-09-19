"""SelfWealth (Australia) — the buy and sell confirmation."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d+"

FIELDS = {
    "security": [r"^(?P<shares>[\d,]+) (?P<name>[A-Z0-9]+ .+?) (?P<price>" + NUM + r") \$" + NUM + r" [A-Z]{3}$"],
    "date": [r"Trade Date: (?P<date>\d{1,2} [A-Za-z]+ \d{4})"],
    "amount": [r"^(?:Net Value|Total Amount Payable|Net Proceeds) \$(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"Reference No: (?P<ref>\S+)"],
    "fees": [r"^(?:Brokerage|Adviser Fee)\*? \$(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})"],
}

SPEC = Spec(
    slug="selfwealth_pdf",
    label="SelfWealth — Confirmation PDF",
    corpus="selfwealth",
    marks=[r"SelfWealth", r"selfwealth\.com\.au"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"^(?:Buy|Sell) Confirmation", sell=r"^Sell Confirmation|WE HAVE SOLD", fields=FIELDS),
    ],
)
