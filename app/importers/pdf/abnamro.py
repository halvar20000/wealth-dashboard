"""ABN AMRO / MoneYou (Tagesgeld, Festgeld) — the Kontoauszug: booking
date, value date, account, text, figure; the year-end taxes on rows of
their own next to the interest."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = re.compile(r"^(" + DATE + r") (" + DATE + r") (\S+) (.+?) (" + NUM + r")$")


def _de(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fold(text: str) -> str:
    """Abgeltungssteuer / Solidaritätszuschlag / Kirchensteuer rows onto the
    Zinsen row of the same value date, as [tax x], the interest netted."""
    lines = text.splitlines()
    rows = [(i, m) for i, m in ((i, ROW.match(l)) for i, l in enumerate(lines)) if m]
    interest = {m.group(2): i for i, m in rows if re.search(r"[Zz]ins", m.group(4))}
    drop = set()
    for i, m in rows:
        j = interest.get(m.group(2))
        if j is None or not re.match(r"Abgeltungs|Solidarit|Kirchensteuer|Kapitalertrag", m.group(4)):
            continue
        z = ROW.match(lines[j].split(" [tax")[0])
        carried = re.search(r"\[tax (" + NUM + r")\]$", lines[j])
        tax = parse_number(m.group(5), "de") + (parse_number(carried.group(1), "de") if carried else 0.0)
        net = parse_number(z.group(5), "de") - parse_number(m.group(5), "de")
        lines[j] = f"{z.group(1)} {z.group(2)} {z.group(3)} {z.group(4)} {_de(net)} [tax {_de(tax)}]"
        drop.add(i)
    return "\n".join(l for i, l in enumerate(lines) if i not in drop)


FIELDS = {
    "date": [r"^" + DATE + r" (?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" " + DATE + r" \S+ (?P<type>.+?) " + NUM],
    "amount": [r"^" + DATE + r" " + DATE + r" \S+ .+? (?P<amount>" + NUM + r")(?: \[tax [\d.,]+\])?$"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
    "ref": [r"^" + DATE + r" " + DATE + r" (?P<ref>\S+) "],
}

SPEC = Spec(
    slug="abnamro_pdf",
    label="ABN AMRO / MoneYou — Kontoauszug PDF",
    corpus="abnamrogroup",
    marks=[r"ABN AMRO", r"moneyou\.de", r"MoneYou"],
    number="de",
    preprocess=fold,
    docs=[
        Doc(kind="rows", when=r"^datum stellung von/nach Konto Buchungstext", block=r"^" + DATE + r" " + DATE + r" \S+ .+? " + NUM, fields=FIELDS,
            kinds={r"[Zz]ins": "interest", r"Zahlungseingang|R.{1,2}ckzahlung": "deposit",
                   r"Zahlungsausgang|Abschluss eines Festgeldes": "withdrawal",
                   r"Abgeltungs|Solidarit|Kirchensteuer": "tax"}),
    ],
)
