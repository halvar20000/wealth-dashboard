"""N26 — the Kontoauszug of the savings account: a row per booking, its
value date on the line below, the sign in front of the amount and the
euro sign after it. The interest comes with its taxes on rows of their
own; `net()` folds them onto the interest."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^\S.* " + DATE + r" [-+]" + NUM + r"€$"
FIELDS = {
    "date": [r"^.* (?P<date>" + DATE + r") [-+]" + NUM + r"€$"],
    "amount": [r"^(?P<type>.+?) " + DATE + r" (?P<amount>[-+]" + NUM + r")€$"],
    "type": [r"^(?P<type>.+?) " + DATE + r" [-+]" + NUM + r"€$"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
}


def net(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    last = None
    for line in lines:
        m = re.match(r"^(Abgeltungss?teuer|Solidarit.tszuschlag|Kirchensteuer) (" + DATE + r") ([-+]" + NUM + r")€$", line)
        if m and last is not None:
            pm = re.match(r"^(Zinsertrag)(?: \[tax (" + NUM + r")\])? (" + DATE + r") ([-+]" + NUM + r")€$", out[last])
            if pm and pm.group(3) == m.group(2):
                tax = (parse_number(pm.group(2), "de") if pm.group(2) else 0.0) - (parse_number(m.group(3), "de") or 0.0)
                rest = (parse_number(pm.group(4), "de") or 0.0) + (parse_number(m.group(3), "de") or 0.0)
                de = lambda v: f"{v:.2f}".replace(".", ",")
                out[last] = f"Zinsertrag [tax {de(tax)}] {pm.group(3)} +{de(rest)}€"
                continue
        if re.match(r"^Zinsertrag " + DATE + r" ", line):
            last = len(out)
        out.append(line)
    return "\n".join(out)


SPEC = Spec(
    slug="n26_pdf",
    label="N26 — Kontoauszug PDF",
    corpus="n26bankag",
    marks=[r"N26 Bank", r"n26\.com", r"NTSBDEB1"],
    preprocess=net,
    docs=[
        Doc(kind="rows", when=r"^Beschreibung Verbuchungsdatum Betrag", block=ROW, fields=FIELDS,
            kinds={r"^Zinsertrag": "interest", r"Steuer|zuschlag": "tax", r"Geb.hr|Entgelt": "fee"}),
    ],
)
