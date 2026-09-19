"""Alpaca Securities — the trade confirmation, one block per order
under "BUY/SELL QTY CURRENCY PRICE GROSSAMOUNT FEES NET AMOUNT"."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"-?[\d,]+(?:\.\d+)?"
DATE = r"[A-Z][a-z]{2} \d{1,2}, \d{4}"
ROW = r"^(?:buy|sell) " + NUM + r" [A-Z]{3} "


def symbols(text: str) -> str:
    """Each order row learns the SYMBOL printed above its header."""
    out, symbol = [], ""
    for line in text.splitlines():
        m = re.match(r"^SYMBOL: (\S+)", line)
        if m:
            symbol = m.group(1)
        elif re.match(ROW, line) and symbol:
            line += f" SYMBOL {symbol}"
        out.append(line)
    return "\n".join(out)


FIELDS = {
    "security": [r"^(?:buy|sell) (?P<shares>" + NUM + r") (?P<currency>[A-Z]{3}) (?P<price>" + NUM + r") .* SYMBOL (?P<name>\S+)$"],
    "date": [r" (?P<date>" + DATE + r") SYMBOL "],
    "amount": [r" (?P<amount>" + NUM + r") " + DATE + r" SYMBOL "],
    "fees": [r"commission: -(?P<fee>" + NUM + r") "],
    "ref": [r"^\S+ \(ET\) " + DATE + r" \S+ \S+ \S+ (?P<ref>[A-Z0-9]{9}) "],
}

SPEC = Spec(
    slug="alpaca_pdf",
    label="Alpaca Securities — trade confirmation PDF",
    corpus="alpaccapital",
    marks=[r"Alpaca"],
    number="en",
    preprocess=symbols,
    docs=[
        Doc(kind="trade", when=r"^BUY/SELL QTY CURRENCY PRICE", block=ROW, sell=r"^sell ", fields=FIELDS),
    ],
)
