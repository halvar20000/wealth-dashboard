"""AJ Bell Youinvest — the contract note."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"

FIELDS = {
    "date": [r"^(?P<date>\d{2}/\d{2}/\d{2}) \d{2}\.\d{2} \d{2}/\d{2}/\d{2} (?:Bought|Sold) "],
    "security": [r"^We have (?:bought|sold) for you as agent\n(?P<name>.+)"],
    "shares": [r"^Venue Quantity Price Consideration\n\S+ (?P<shares>" + NUM + r") (?P<price>" + NUM + r") " + NUM + r" [A-Z]{3}$"],
    "amount": [r"^Total (?:debit|credit) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"^\d{2}/\d{2}/\d{2} \d{2}\.\d{2} \d{2}/\d{2}/\d{2} (?:Bought|Sold) \S+ (?P<ref>\S+)$"],
    "fees": [r"^(?:Dealing charge|Commission|Fund manager.s initial charge) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Stamp duty|PTM levy|Stamp Duty Reserve Tax)[^\n]*? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="ajbell_pdf",
    label="AJ Bell Youinvest — Contract Note PDF",
    corpus="ajbellsecuritieslimited",
    marks=[r"AJ Bell", r"Youinvest"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"^CONTRACT NOTE", sell=r"^We have sold for you", fields=FIELDS),
    ],
)
