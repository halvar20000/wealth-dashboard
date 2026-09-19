"""Revolut — the trade confirmation, the 2020 DriveWealth account
statement (American dates, amounts in brackets) and the 2026 one
(a row per event with the time)."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d,]+(?:\.\d+)?"
MONEY = r"[€$£]" + NUM
WRITTEN = r"\d{1,2} [A-Za-z]{3} \d{4}"

CONFIRMATION = {
    "security": [r"^(?P<ticker>[A-Z0-9.]+) (?P<name>.+?) " + ISIN + r" (?P<type>Buy|Sell) (?P<shares>" + NUM + r") (?:[€$£](?P<price>" + NUM + r") )?(?P<currency>[€$£])(?P<amount>" + NUM + r") (?P<date>" + WRITTEN + r")$"],
    "fees": [r"^Total Fee charged [€$£](?P<fee>" + NUM + r")"],
}
OLD_ROW = r"^\d{2}/\d{2}/\d{4} \d{2}/\d{2}/\d{4} [A-Z]{3} \S+ "
OLD_FIELDS = {
    "date": [r"^(?P<date>\d{2}/\d{2}/\d{4}) "],
    "type": [r"^\S+ \S+ [A-Z]{3} (?P<type>\S+) "],
    "security": [r"^\S+ \S+ [A-Z]{3} (?:BUY|SELL) (?P<name>[A-Z.]+) - .+? (?P<shares>" + NUM + r") (?P<price>" + NUM + r") \(?(?P<amount>" + NUM + r")\)?$"],
    "amount": [r"^\S+ \S+ (?P<currency>[A-Z]{3}) \S+ .+? \(?(?P<amount>" + NUM + r")\)?$"],
}
NEW_ROW = r"^" + WRITTEN + r" \d{2}:\d{2}:\d{2} GMT "
NEW_FIELDS = {
    "date": [r"^(?P<date>" + WRITTEN + r") \d{2}:\d{2}:\d{2} GMT "],
    "type": [r"GMT (?P<type>(?:[A-Z0-9.]+ )?(?:Trade - \w+ " + NUM + r" " + MONEY + r" (?:Buy|Sell)|Cash top-up|Cash withdrawal|Dividend|Interest|[A-Za-z -]*?[Ff]ee|[A-Za-z -]+?)) "],
    "security": [r"GMT (?P<name>[A-Z0-9.]+) Trade - \w+ (?P<shares>" + NUM + r") [€$£](?P<price>" + NUM + r") (?:Buy|Sell) "],
    "amount": [r"GMT (?:[A-Z0-9.]+ )?(?:Trade - \w+ " + NUM + r" " + MONEY + r" (?:Buy|Sell)|[A-Za-z -]+?) (?P<sign>-?)(?P<currency>[€$£])(?P<amount>" + NUM + r")"],
    "fees": [r"\[fee (?P<fee>" + NUM + r")\]"],
}


def totals(text: str) -> str:
    """"Buy €1.27 €0.02 €0.01": the fees added onto what the trade cost."""
    def fold(m):
        gross, f1, f2 = (float(x.replace(",", "")) for x in (m.group(2), m.group(3), m.group(4)))
        total = gross + f1 + f2 if m.group(1) == "Buy" else gross - f1 - f2
        return f"{m.group(1)} €{total:.2f} [fee {f1 + f2:.2f}]"
    return re.sub(r"(Buy|Sell) €(" + NUM + r") €(" + NUM + r") €(" + NUM + r")$", fold, text, flags=re.M)


def american(text: str) -> str:
    return re.sub(r"^(\d{2})/(\d{2})/(\d{4}) (\d{2})/(\d{2})/(\d{4}) ", r"\2.\1.\3 \5.\4.\6 ", text, flags=re.M)


SPEC = Spec(
    slug="revolut_pdf",
    label="Revolut — Trade Confirmation / Account Statement PDF",
    corpus="revolutltd",
    marks=[r"Revolut"],
    number="en",
    preprocess=lambda t: totals(american(t)),
    docs=[
        Doc(kind="rows", when=r"^Trade Confirmation", block=r"^[A-Z0-9.]+ .+ [A-Z]{2}[A-Z0-9]{9}\d (?:Buy|Sell) ", fields=CONFIRMATION,
            kinds={r"^Sell": "sell", r".": "buy"}),
        Doc(kind="rows", when=r"^Trade Date Settle Date Currency Activity Type", block=r"^\d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4} [A-Z]{3} \S+ ",
            fields={**OLD_FIELDS, "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) "]},
            kinds={r"^BUY": "buy", r"^SELL": "sell", r"^CDEP|^DEP": "deposit", r"^CWD|^WDL": "withdrawal", r"^DIV": "dividend", r"^INT": "interest", r"^FEE": "fee", r".": "skip"}),
        Doc(kind="rows", when=r"GMT (?:Cash top-up|[A-Z0-9.]+ Trade - )", block=NEW_ROW, fields=NEW_FIELDS,
            kinds={r"Sell": "sell", r"Buy": "buy", r"top-up|Deposit": "deposit", r"withdrawal": "withdrawal", r"Dividend": "dividend", r"Interest": "interest", r"[Ff]ee": "fee"}),
    ],
)
