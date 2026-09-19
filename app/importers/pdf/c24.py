"""C24 Bank — the Kontoauszug: booking day, value day, kind, and the
amount with its sign set apart."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
ROW = r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. \S.* [-+] " + NUM + r" €$"
FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.) "],
    "year": [r"^Kontoauszug \d{2}/(?P<year>\d{4})", r"^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.(?P<year>\d{4})"],
    "amount": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) (?P<sign>[-+]) (?P<amount>" + NUM + r") €$"],
    "type": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) [-+] " + NUM + r" €$"],
}

SPEC = Spec(
    slug="c24_pdf",
    label="C24 Bank — Kontoauszug PDF",
    corpus="c24bankgmbh",
    marks=[r"C24 Bank", r"C24 Smartkonto"],
    preprocess=lambda t: __import__("re").sub(r" - (" + NUM + r") €$", r" -\1 €", t, flags=__import__("re").M),
    docs=[
        Doc(kind="rows", when=r"^Buchung Valuta Transaktionsinformation Betrag", block=r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. \S.* [-+] ?" + NUM + r" €$",
            fields={**FIELDS,
                    "amount": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) (?P<amount>[-+] ?" + NUM + r") €$"],
                    "type": [r"^\d{2}\.\d{2}\. \d{2}\.\d{2}\. (?P<type>.+?) [-+] ?" + NUM + r" €$"]},
            kinds={r"^Zinsen": "interest", r"^Steuern": "tax", r"Geb.hr|Entgelt": "fee"}),
    ],
)
