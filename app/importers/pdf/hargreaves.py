"""Hargreaves Lansdown — the contract note."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d,]+(?:\.\d+)?"

FIELDS = {
    "security": [r"^" + ISIN + r"(?: STOCK CODE: \S+)?\n(?P<name>.+)\n(?P<shares>" + NUM + r") (?P<name2>.+?) (?P<price>" + NUM + r") " + NUM + r"$"],
    "date": [r"^Date (?P<date>\d{2}/\d{2}/\d{4}) Time", r"^Date (?P<date>\d{2} ?/ ?\d{2} ?/ ?\d{4}) Time"],
    "amount": [r"Settlement Date: \d{2}/\d{2}/\d{4} (?P<amount>" + NUM + r")$"],
    "ref": [r"Contract Note No\. (?P<ref>\S+)"],
    "fees": [r"^Commission (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Stamp Duty|PTM Levy|Stamp duty reserve tax)[^\n]*? (?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="hargreaves_pdf",
    label="Hargreaves Lansdown — Contract Note PDF",
    corpus="hargreaveslansdownplc",
    marks=[r"Hargreaves Lansdown", r"h-l\.co\.uk"],
    number="en",
    preprocess=lambda t: __import__("re").sub(r"^Date (\d{2}) ?/ ?(\d{2}) ?/ ?(\d{3}) ?(\d) ", r"Date \1/\2/\3\4 ", t, flags=__import__("re").M),
    docs=[
        Doc(kind="trade", when=r"^We have today on your instructions \*\* ?(?:BOUGHT|SOL ?D) ?\*\*", sell=r"\*\* ?SOL ?D ?\*\*", fields=FIELDS),
    ],
)
