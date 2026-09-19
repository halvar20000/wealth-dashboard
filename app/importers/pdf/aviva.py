"""Aviva (UK workplace pension) — the contract note, one block per
trade under "You have PURCHASED" or "You have SOLD"."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d,]+(?:\.\d+)?"

BLOCK = r"^You have (?:PURCHASED|SOLD):?\s*$"
FIELDS = {
    "security": [r"^Investment Name: (?P<name>.+)"],
    "isin": [r"^ISIN: " + ISIN],
    "shares": [r"^Number of units: (?P<shares>" + NUM + r")"],
    "price": [r"^Price: £(?P<price>" + NUM + r")"],
    "date": [r"^Execution date(?:/time)?: (?P<date>\d{2} [A-Za-z]{3} \d{4})"],
    "amount": [r"^(?:Total Consideration|Net proceeds|Total proceeds|Consideration):? £(?P<amount>" + NUM + r")"],
    "price": [r"^Price:? £(?P<price>" + NUM + r")"],
    "ref": [r"^Order reference: (?P<ref>\S+)"],
}
FIELDS["security"].append(r"^ISIN: " + ISIN)

SPEC = Spec(
    slug="aviva_pdf",
    label="Aviva — Contract Note PDF",
    corpus="avivaplc",
    marks=[r"Aviva"],
    number="en",
    docs=[
        Doc(kind="trade", when=BLOCK, block=BLOCK, sell=r"^You have SOLD", fields={**FIELDS, "type": [r"^(?P<currency>GBP)?"]}),
    ],
)
