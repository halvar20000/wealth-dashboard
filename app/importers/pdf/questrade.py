"""Questrade — the monthly account statement's Transactions table: a
row per booking with the trade and settle dates, the activity, the
symbol, and the CAD columns (quantity, price, gross, commission, net)
followed by the USD ones; a description that runs onto the next line."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d+"
MONEY = r"\(?" + NUM + r"\)?|-"
DATE = r"\d{2}[.-]\d{2}[.-]\d{4}"
ROW = r"^" + DATE + r" " + DATE + r" "
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") " + DATE + r" "],
    "type": [r"^" + DATE + r" " + DATE + r" (?P<type>[^\n]*?) (?:\d+(?:\.\d+)? " + NUM + r" |- - - - )"],
    "security": [r"^" + DATE + r" " + DATE + r" (?:Buy|Sell) (?P<name>\.?[A-Z.]+) "],
    "shares": [r" (?P<shares>\d+(?:\.\d+)?) (?P<price>" + NUM + r") \(?" + NUM + r"\)? (?:\(" + NUM + r"\)|-) \(?" + NUM + r"\)? "],
    # The CAD net is the fifth figure from the end, the USD columns after it.
    "amount": [r" \d+(?:\.\d+)? " + NUM + r" \(?" + NUM + r"\)? (?:\(" + NUM + r"\)|-) (?P<amount>\(?" + NUM + r"\)?)(?: (?:" + MONEY + r")){0,4}$",
               r"^" + DATE + r" " + DATE + r" .*? - - - - (?P<amount>\(?" + NUM + r"\)?)(?: (?:" + MONEY + r")){0,4}$"],
    "fees": [r" \d+(?:\.\d+)? " + NUM + r" \(?" + NUM + r"\)? \((?P<fee>" + NUM + r")\) "],
}


def join(text: str) -> str:
    """A row's description wraps: the continuation joined onto the row;
    and the dates are American, month first."""
    text = re.sub(r"^(\d{2})-(\d{2})-(\d{4}) (\d{2})-(\d{2})-(\d{4}) ", r"\2.\1.\3 \5.\4.\6 ", text, flags=re.M)
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if out and re.match(r"^" + DATE + r" " + DATE + r" ", out[-1]) and not re.search(r"(?:" + MONEY + r" ){3}" + MONEY + r"$", out[-1]) \
                and not re.match(r"^" + DATE, line) and not line.startswith("Closing balance"):
            out[-1] = out[-1].rstrip() + " " + line.strip()
            continue
        out.append(line)
    return "\n".join(out)


SPEC = Spec(
    slug="questrade_pdf",
    label="Questrade — Account Statement PDF",
    corpus="questradegroup",
    marks=[r"Questrade"],
    number="en",
    preprocess=join,
    docs=[
        Doc(kind="rows", when=r"^Trans Date\.", block=ROW, fields=FIELDS,
            kinds={r"^Buy": "buy", r"^Sell": "sell", r"^Contribution|^Deposit": "deposit", r"^Withdrawal": "withdrawal",
                   r"DIST|Dividend": "dividend", r"Interest|INT": "interest", r"Fee|FEE": "fee"}),
    ],
)
