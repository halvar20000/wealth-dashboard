"""Barclays (Germany) — the credit card statement: booking day, value
day, merchant, and the amount with a trailing minus for a charge."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^" + DATE + r" " + DATE + r" \S.* -?" + NUM + r"$"
FIELDS = {
    "date": [r"^" + DATE + r" (?P<date>" + DATE + r") "],
    "amount": [r"^" + DATE + r" " + DATE + r" (?P<type>.+?) (?P<amount>-?" + NUM + r")$"],
    "type": [r"^" + DATE + r" " + DATE + r" (?P<type>.+?) -?" + NUM + r"$"],
}

SPEC = Spec(
    slug="barclays_pdf",
    label="Barclays — Kreditkartenabrechnung PDF",
    corpus="barclaysbankirelandplc",
    marks=[r"Barclays", r"BARCDEHA"],
    preprocess=lambda t: re.sub(r"(" + NUM + r")\+$", r"\1", re.sub(r"(" + NUM + r")-$", r"-\1", t, flags=re.M), flags=re.M),
    docs=[
        Doc(kind="rows", when=r"^Kontoauszug", block=ROW, fields=FIELDS,
            kinds={r"Zins": "interest", r"steuer|zuschlag": "tax", r"Geb.hr|Entgelt|Jahresbeitrag": "fee"}),
    ],
)

# BAWAG's German branch took the Barclays card book over, statement and all.
SPECS = [SPEC, Spec(slug="bawag_card_pdf", label="BAWAG (Barclays Kreditkarte) — Kontoauszug PDF", corpus="bawagag",
                    marks=[r"BAWAG AG Niederlassung Deutschland"], preprocess=SPEC.preprocess, docs=SPEC.docs)]
