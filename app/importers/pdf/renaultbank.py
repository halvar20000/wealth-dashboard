"""Renault Bank direkt — the Kontoauszug: a day and month, the booking
text, and the amount with its sign at the end; the year printed once,
in "erstellt am"."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
ROW = r"^\d{2}\.\d{2}\. \S.* -?" + NUM + r"$"
FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.) "],
    "year": [r"erstellt am \d{2}\.\d{2}\.(?P<year>\d{4})"],
    "amount": [r"^\d{2}\.\d{2}\. (?P<type>.+?) (?P<amount>-?" + NUM + r")$"],
    "type": [r"^\d{2}\.\d{2}\. (?:Wertstellung: \d{2}\.\d{2}\. )?(?P<type>.+?) -?" + NUM + r"$"],
}


def tidy(text: str) -> str:
    """"4.480,00+" and "400,00-": the sign in front, where the engine reads it."""
    return re.sub(r"(" + NUM + r")([-+])$", lambda m: ("-" if m.group(2) == "-" else "") + m.group(1), text, flags=re.M)


# The Tagesgeld layout: booking day, value day, text, amount and H (credit) or S (debit).
ROW2 = r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. \S.* " + NUM + r" [HS]$"
FIELDS2 = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.) "],
    "year": [r"erstellt am \d{2}\.\d{2}\.(?P<year>\d{4})"],
    "amount": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) (?P<amount>" + NUM + r") (?P<sign>[HS])$"],
    "type": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) " + NUM + r" [HS]$"],
}

# The Austrian Tagesgeld: date, text, reference, amount, value date, balance.
ROW3 = r"^\d{2}\.\d{2}\.\d{4} \S.* -?" + NUM + r" \d{2}\.\d{2}\.\d{4} -?" + NUM + r"$"
FIELDS3 = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) "],
    "amount": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>.+?) (?P<amount>-?" + NUM + r") \d{2}\.\d{2}\.\d{4} -?" + NUM + r"$"],
    "type": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>.+?) -?" + NUM + r" \d{2}\.\d{2}\.\d{4} -?" + NUM + r"$"],
}

# J&T Direktbank's Tagesgeld statement comes from the same printer in Gladbeck.
JT = Spec(
    slug="jtdirekt_pdf",
    label="J&T Direktbank — Kontoauszug PDF",
    corpus="jtdirektbank",
    marks=[r"J&T Direktbank", r"JTBPDEFF"],
    preprocess=tidy,
    docs=[
        Doc(kind="rows", when=r"^Bu-Tag Wert Vorgang", block=ROW2, fields=FIELDS2,
            kinds={r"Abschluss|Zinsen": "interest", r"Geb.hr|Entgelt": "fee", r"Kontostand": "skip"}),
    ],
)

SPEC = Spec(
    slug="renaultbank_pdf",
    label="Renault Bank direkt — Kontoauszug PDF",
    corpus="renaultbankdirekt",
    marks=[r"Renault B", r"RCIDDE3N", r"RCNOATW1", r"305 200 37", r"Gladbeck"],
    preprocess=tidy,
    docs=[
        Doc(kind="rows", when=r"KONTOAUSZUG", block=ROW, fields=FIELDS,
            kinds={r"Zinsen": "interest", r"Geb.hr|Entgelt": "fee", r"GESAMTUMSATZ|KONTOSTAND": "skip"}),
        Doc(kind="rows", when=r"^Kontoauszug Tagesgeld", block=ROW3, fields=FIELDS3,
            kinds={r"Zins|Abschluss": "interest", r"Steuer|KESt": "tax", r"Geb.hr|Entgelt": "fee", r"saldo": "skip"}),
        Doc(kind="rows", when=r"^Bu-Tag Wert Vorgang", block=ROW2, fields=FIELDS2,
            kinds={r"Abschluss|Zinsen": "interest", r"Geb.hr|Entgelt": "fee", r"Kontostand": "skip"}),
    ],
)

SPECS = [SPEC, JT]
