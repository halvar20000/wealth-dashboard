"""CommSec (Commonwealth Securities, Australia) — the Confirmation
Contract Note."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
DATE = r"\d{2}/\d{2}/\d{4}"

FIELDS = {
    "security": [r"^COMPANY:? (?P<name>.+)$"],
    "shares": [r"^TOTAL UNITS: (?P<shares>" + NUM + r")"],
    "price": [r"^AVERAGE PRICE: (?P<price>" + NUM + r")"],
    "date": [r"^AS AT DATE: (?P<date>" + DATE + r")", r"^DATE: (?P<date>" + DATE + r")"],
    "amount": [r"^CONSIDERATION \((?P<currency>[A-Z]{3})\)[\s\S]*?^(?:TOTAL COST|NET PROCEEDS): \$(?P<amount>" + NUM + r")"],
    "fees": [r"^BROKERAGE & COSTS INCL GST: \$(?P<fee>" + NUM + r")"],
    "ref": [r"^CONFIRMATION NO: (?P<ref>\d+)"],
}

SPEC = Spec(
    slug="commsec_pdf",
    label="CommSec — Confirmation Contract Note PDF",
    corpus="commsec",
    marks=[r"commsec\.com\.au", r"Commonwealth Securities"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"^WE HAVE (?:BOUGHT|SOLD) THE FOLLOWING SECURITIES", sell=r"^WE HAVE SOLD", fields=FIELDS),
    ],
)
