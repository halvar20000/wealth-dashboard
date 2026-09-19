"""BSDEX (Börse Stuttgart Digital Exchange) — the Transaktionshistorie:
a row per trade with the coin in, the euros out (or the other way
round) and the fee; the fee folded into what the trade cost."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d.]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^\S+ (?:Kauf|Verkauf|Einzahlung|Auszahlung) " + DATE + r" "
FIELDS = {
    "date": [r"^\S+ (?:Kauf|Verkauf|Einzahlung|Auszahlung) (?P<date>" + DATE + r") "],
    "type": [r"^\S+ (?P<type>Kauf|Verkauf|Einzahlung|Auszahlung) "],
    "security": [r"^\S+ Kauf " + DATE + r" (?:\d{2}:\d{2}:\d{2} )?(?P<shares>" + NUM + r") (?P<name>[A-Z]{3,5}) " + NUM + r" EUR",
                 r"^\S+ Verkauf " + DATE + r" (?:\d{2}:\d{2}:\d{2} )?" + NUM + r" EUR (?P<shares>" + NUM + r") (?P<name>[A-Z]{3,5}) "],
    "amount": [r"\[total (?P<amount>" + NUM + r") (?P<currency>EUR)\]", r"^\S+ (?:Einzahlung|Auszahlung) " + DATE + r" (?:\d{2}:\d{2}:\d{2} )?(?P<amount>" + NUM + r") (?P<currency>EUR) "],
    "fees": [r"\[fee (?P<fee>" + NUM + r") EUR\]"],
}


def totals(text: str) -> str:
    return re.sub(r"^\S+ (Kauf|Verkauf) " + DATE + r" (?:\d{2}:\d{2}:\d{2} )?(?:" + NUM + r" [A-Z]{3,5} (" + NUM + r") EUR|(" + NUM + r") EUR " + NUM + r" [A-Z]{3,5}) (" + NUM + r") EUR$",
                  lambda m: fold_(m), text, flags=re.M)


def fold_(m):
    kind = m.group(1)
    euros = float(m.group(2) or m.group(3))
    fee = float(m.group(4))
    total = euros + fee if kind == "Kauf" else euros - fee
    return f"{m.group(0)} [total {total:.2f} EUR] [fee {fee:.2f} EUR]"


SPEC = Spec(
    slug="bsdex_pdf",
    label="BSDEX — Transaktionshistorie PDF",
    corpus="bsdex",
    marks=[r"BSDEX", r"B.rse Stuttgart Digital", r"^Transaktionshistorie"],
    number="en",
    preprocess=totals,
    docs=[
        Doc(kind="rows", when=r"^Transaktionshistorie", block=ROW, fields=FIELDS, kinds={r"^Verkauf": "sell", r"^Kauf": "buy", r"^Einzahlung": "deposit", r"^Auszahlung": "withdrawal"}),
    ],
)
