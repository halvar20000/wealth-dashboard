"""Ford Money (Ford Bank) — the Tagesgeld Kontoauszug: the month's
interest comes as one Abschluss row per rate, its taxes as rows of
their own; all of a day's folded into one interest row."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"-?[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = re.compile(r"^(" + DATE + r") (" + DATE + r") (.+?) (" + NUM + r")$")


def _de(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fold(text: str) -> str:
    lines = text.splitlines()
    days: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        m = ROW.match(line)
        if m and re.match(r"Abschluss|Zinsen|Kapitalertrag|Solidarit|Kirchensteuer", m.group(3)):
            days.setdefault(m.group(1), []).append(i)
    drop = set()
    for date, idx in days.items():
        rows = [ROW.match(lines[i]) for i in idx]
        gross = sum(parse_number(m.group(4), "de") for m in rows if re.match(r"Abschluss|Zinsen", m.group(3)))
        tax = -sum(parse_number(m.group(4), "de") for m in rows if not re.match(r"Abschluss|Zinsen", m.group(3)))
        if not gross:
            continue
        lines[idx[0]] = f"{date} {rows[0].group(2)} Zinsen {_de(gross - tax)}" + (f" [tax {_de(tax)}]" if tax else "")
        drop.update(idx[1:])
    return "\n".join(l for i, l in enumerate(lines) if i not in drop)


FIELDS = {
    "date": [r"^" + DATE + r" (?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" " + DATE + r" (?P<type>.+?) " + NUM],
    "amount": [r"^" + DATE + r" " + DATE + r" .+? (?P<amount>" + NUM + r")(?: \[tax [\d.,]+\])?$"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
}

SPEC = Spec(
    slug="fordmoney_pdf",
    label="Ford Money — Kontoauszug PDF",
    corpus="fordmoney",
    marks=[r"Ford Money", r"fordmoney\.de", r"Ford Bank"],
    number="de",
    preprocess=fold,
    docs=[
        Doc(kind="rows", when=r"^Tagesgeld Kontoauszug", block=r"^" + DATE + r" " + DATE + r" .+? " + NUM, fields=FIELDS,
            kinds={r"^Zinsen": "interest"}),
    ],
)
