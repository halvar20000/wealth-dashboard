"""Nordax Bank (via Raisin) — the deposit account statement."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^" + DATE + r" (?:" + DATE + r" )?\S.* " + NUM + r"(?: " + NUM + r")?$"
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?:" + DATE + r" )?(?P<type>.+?) " + NUM],
    "amount": [r"^" + DATE + r" (?:" + DATE + r" )?.+? (?P<amount>" + NUM + r")(?: " + NUM + r")?$"],
}

SPEC = Spec(
    slug="nordax_pdf",
    label="Nordax Bank — Kontoauszug PDF",
    corpus="nordaxbankab",
    marks=[r"Nordax Bank", r"NOBA Bank", r"Bank Norwegian"],
    docs=[
        Doc(kind="rows", when=r"^(?:Transaktionen|Transactions|Buchungsda|Valuta Datum Zahlungsvorgang)", block=ROW, fields=FIELDS,
            kinds={r"Kontostand|.bertrag": "skip", r"Zins|Interest": "interest", r"Zahlung an|Auszahlung": "withdrawal", r"Bezahlung von|Einzahlung": "deposit"}),
    ],
)

# Orange Bank's Raisin statement is the same paper under another letterhead.
SPECS = [SPEC, Spec(slug="orangebank_pdf", label="Orange Bank — Kontoauszug PDF", corpus="orangebank",
                    marks=[r"Orange Bank"], docs=[
                        Doc(kind="rows", when=SPEC.docs[0].when, block=ROW, fields=FIELDS,
                            kinds={r"Kontostand|.bertrag": "skip", r"Zinsauszahlung|R.ckzahlung": "withdrawal", r"Zins|Interest": "interest",
                                   r"Zahlung an|Auszahlung": "withdrawal", r"Bezahlung von|Einzahlung": "deposit"})])]
