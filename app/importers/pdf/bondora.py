"""Bondora Go & Grow — the statement: a date, a kind, an amount and
the balance, the euro sign before or after the figure depending on
the year the PDF was made."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d.,']+"
DATE = r"\d{2}[.-]\d{2}[.-]\d{4}|\d{4}-\d{2}-\d{2}"
ROW = r"^" + DATE + r" \S.* €$|^" + DATE + r" \S.* €\S+$"
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "amount": [r"^" + DATE + r" (?P<type>.+?) (?:€ ?)?(?P<amount>" + NUM + r") ?(?:€)? (?:€ ?)?" + NUM + r" ?€?$"],
    "type": [r"^" + DATE + r" (?P<type>[^\d€]+?) (?:€ ?)?\d"],
}


def tidy(text: str) -> str:
    """"€1" and "1 €" alike: the figure alone, then the sign."""
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"^(\d{1,2})/(\d{1,2})/(\d{4}) ", lambda m: f"{int(m.group(2)):02d}.{int(m.group(1)):02d}.{m.group(3)} ", line)   # 4/6/2023, the American way
        if not line.endswith("€"):
            line = re.sub(r"€ ?(\d[\d.,' ]*\d|\d)", lambda m: m.group(1).replace(" ", "") + " €", line)
        lines.append(line.replace("'", "."))
    return "\n".join(lines)


SPEC = Spec(
    slug="bondora_pdf",
    label="Bondora Go & Grow — Kontoauszug PDF",
    corpus="bondoracapital",
    marks=[r"Go & Grow", r"Bondora", r"Referenznummer GG", r"Reference number GG"],
    number="auto",
    preprocess=tidy,
    docs=[
        Doc(kind="rows", when=r"^(?:Datum|Date) (?:Zahlungsart|Payment type|Type)", block=r"^(?:" + DATE + r") \S.* " + NUM + r" € -?" + NUM + r" €$",
            fields={
                "date": [r"^(?P<date>" + DATE + r") "],
                "amount": [r"^(?:" + DATE + r") (?P<type>.+?) (?P<amount>" + NUM + r") € -?" + NUM + r" €$"],
                "type": [r"^(?:" + DATE + r") (?P<type>.+?) " + NUM + r" € -?" + NUM + r" €$"],
            },
            kinds={r"Zinsen|returns|Interest|Rendite": "interest", r"Abheben|Withdrawal|Auszahlung": "withdrawal",
                   r"Überweisen|Transfer|Einzahlung|SEPA|Deposit|payment": "deposit"}),
    ],
)
