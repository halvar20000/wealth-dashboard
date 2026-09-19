"""akf bank — the Kontoauszug: a numbered row with value and booking
date, the booking text, and the amount; the Kontoabschluß row is the
interest of the period."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"[\d.]+,\d{2}"
ROW = r"^\d{2} \d{2}\.\d{2}\.\d{4} / \d{2}\.\d{2}\.\d{4} \S.* -?" + NUM + r"$"
FIELDS = {
    "date": [r"^\d{2} (?P<date>\d{2}\.\d{2}\.\d{4}) / "],
    "amount": [r"^\d{2} \S+ / \S+ (?P<type>.+?) (?P<amount>-?" + NUM + r")$"],
    "type": [r"^\d{2} \S+ / \S+ (?P<type>.+?) -?" + NUM + r"$"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
}


def fold(text: str) -> str:
    """The Kontoabschluß is several rows: the interest, then the taxes
    on it, each negative. One row: the net, with the tax beside it."""
    lines = text.split("\n")
    out: list[str] = []
    last = None                                              # index in out of the interest row
    for line in lines:
        m = re.match(r"^(\d{2} \S+ / \S+) Kontoabschlu. (-?" + NUM + r")$", line)
        if m:
            v = parse_number(m.group(2), "de") or 0.0
            if v < 0 and last is not None:
                prev = out[last]
                pm = re.match(r"^(.*Kontoabschlu.)(?: \[tax (" + NUM + r")\])? (" + NUM + r")$", prev)
                if pm:
                    tax = (parse_number(pm.group(2), "de") if pm.group(2) else 0.0) - v
                    net = (parse_number(pm.group(3), "de") or 0.0) + v
                    de = lambda v: f"{v:.2f}".replace(".", ",")
                    out[last] = f"{pm.group(1)} [tax {de(tax)}] {de(net)}"
                    continue
            last = len(out) if v > 0 else None
        out.append(line)
    return "\n".join(out)

SPEC = Spec(
    slug="akfbank_pdf",
    label="akf bank — Kontoauszug PDF",
    corpus="akfbank",
    marks=[r"akf bank", r"akf24\.de"],
    preprocess=fold,
    docs=[
        Doc(kind="rows", when=r"^Kontoauszug", block=ROW, fields=FIELDS,
            kinds={r"Kontoabschlu|Zinsen": "interest", r"Geb.hr|Entgelt": "fee"}),
    ],
)
