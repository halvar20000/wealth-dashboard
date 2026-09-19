"""Audi Bank / Volkswagen Bank (Plus Konto) — the Kontoauszug /
Saldenmitteilung: numbered rows, the interest's taxes on rows of their
own right after it."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"-?[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = re.compile(r"^(\d+) (" + DATE + r") (.+?) (" + DATE + r") (" + NUM + r")$", re.M)


def fold(text: str) -> str:
    """Solidaritätszuschlag / Kirchensteuer / Abgeltungsteuer rows go onto
    the Habenzinsen row before them as [tax x], the row's figure netted."""
    out, last = [], None
    for line in text.splitlines():
        m = ROW.match(line)
        if m and re.match(r"Solidarit|Kirchensteuer|Abgeltungsteuer|Kapitalertragsteuer|KapSt", m.group(3)) and last is not None:
            tax = -parse_number(m.group(5), "de")
            last[1] -= tax
            last[2] += tax
            continue
        if last is not None:
            out.append(_row(last))
            last = None
        if m and re.match(r"Habenzinsen|Zinsen", m.group(3)):
            last = [m, parse_number(m.group(5), "de"), 0.0]
            continue
        out.append(line)
    if last is not None:
        out.append(_row(last))
    return "\n".join(out)


def _de(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _row(last) -> str:
    m, net, tax = last
    return f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)} {_de(net)}" + (f" [tax {_de(tax)}]" if tax else "")


FIELDS = {
    "date": [r"^\d+ " + DATE + r" .+? (?P<date>" + DATE + r") "],
    "type": [r"^\d+ " + DATE + r" (?P<type>.+?) " + DATE + r" "],
    "amount": [r"^\d+ " + DATE + r" .+? " + DATE + r" (?P<amount>" + NUM + r")"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
}

SPEC = Spec(
    slug="audibank_pdf",
    label="Audi Bank / Volkswagen Bank — Kontoauszug PDF",
    corpus="audibank",
    marks=[r"Audi Bank", r"AUDFDE21", r"Volkswagen Bank", r"VOWADE2B"],
    number="de",
    preprocess=fold,
    docs=[
        Doc(kind="rows", when=r"^lfd\. Buchungs- Umsatzinformationen Wertstellung", block=r"^\d+ " + DATE + r" .+? " + DATE + r" " + NUM, fields=FIELDS,
            kinds={r"zinsen": "interest"}),
    ],
)
