"""Score Priority (Vision Financial) — the monthly account statement's
Account Activity Details: a row per booking with month and day, the
security, its CUSIP, the kind, and the settlement amount in brackets
when it is a debit; the year from the statement period."""

from __future__ import annotations

import re

from ..statement import MONTHS, Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^" + DATE + r" \S.* \(?" + NUM + r"\)?(?: \[tax [\d.]+\])?$"
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "security": [r"^" + DATE + r" (?P<name>.+?) (?P<ref>[A-Z0-9]{9}) (?:Buy|Sell) (?P<shares>" + NUM + r") (?P<price>" + NUM + r") "],
    "type": [r"^" + DATE + r" (?P<type>Ca Fee[^\n]*? Journal|Cil Allocation \S+ Journal|Cash Dividend[^\n]*? Journal)",
             r"^" + DATE + r" .*? (?P<type>Buy|Sell|Qualified Dividend|Dividend|Return of Capital|NRA Withhold|Foreign Withholding|Security Journal|Journal|Credit Interest|Interest) "],
    "shares": [r"^" + DATE + r" .*? [A-Z0-9]{9} Security Journal (?P<shares>[\d,]+)$"],
    "amount": [r" (?P<amount>\(?" + NUM + r"\)?)(?: \[tax [\d.]+\])?$", r"Security Journal (?P<amount>0)"],
    "taxes": [r"\[tax (?P<tax>[\d.]+)\]"],
}


def dated(text: str) -> str:
    """"Sep 02" → "02.09.2021", the year from the statement period."""
    m = re.search(r"STATEMENT PERIOD: ([A-Za-z]+) \d{1,2} - (?:[A-Za-z]+ )?\d{1,2}, (\d{4})", text)
    year = m.group(2) if m else None
    if not year:
        return text

    def row(mm):
        mon = MONTHS.get(mm.group(1).lower())
        return f"{int(mm.group(2)):02d}.{mon:02d}.{year} " if mon else mm.group(0)
    text = re.sub(r"^([A-Z][a-z]{2}) (\d{2}) ", row, text, flags=re.M)
    # The withholding on a dividend is a row of its own, same day and
    # CUSIP: folded onto the dividend, which then shows the net.
    lines = text.split("\n")
    divs: dict[tuple, int] = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(" + DATE + r") .*? ([A-Z0-9]{9}) (?:Qualified )?Dividend (" + NUM + r")$", line)
        if m:
            divs.setdefault((m.group(1), m.group(2)), i)
    drop: set[int] = set()
    for i, line in enumerate(lines):
        m = re.match(r"^(" + DATE + r") .*? ([A-Z0-9]{9}) (?:NRA Withhold|Foreign Withholding) \((" + NUM + r")\)$", line)
        j = divs.get((m.group(1), m.group(2))) if m else None
        if j is None:
            continue
        d = re.match(r"^(.* Dividend) (" + NUM + r")(?: \[tax (" + NUM + r")\])?$", lines[j])
        if not d:
            continue
        tax = float(m.group(3).replace(",", "")) + (float(d.group(3)) if d.group(3) else 0.0)
        net = float(d.group(2).replace(",", "")) - float(m.group(3).replace(",", ""))
        lines[j] = f"{d.group(1)} {net:.2f} [tax {tax:.2f}]"
        drop.add(i)
    return "\n".join(l for k, l in enumerate(lines) if k not in drop)


SPEC = Spec(
    slug="scorepriority_pdf",
    label="Score Priority — Account Statement PDF",
    corpus="scorepriorityinc",
    marks=[r"Score Priority", r"scorepriority\.com"],
    number="en",
    preprocess=dated,
    docs=[
        Doc(kind="rows", when=r"^Account Activity Details", block=ROW, fields=FIELDS,
            kinds={r"^Buy": "buy", r"^Sell": "sell", r"^Ca Fee": "fee", r"Allocation|Dividend": "dividend", r"Withhold": "tax", r"Return of Capital": "skip",
                   r"Security Journal": "transfer", r"Interest": "interest", r"Journal": "deposit"}),
    ],
)
