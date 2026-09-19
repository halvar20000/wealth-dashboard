"""Bank11 (Tagesgeld) — the Kontoauszug: "dd.mm. dd.mm. Vorgang amount H|S",
the year on the statement's header."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.]+,\d{2}"
DM = r"\d{2}\.\d{2}\."

FIELDS = {
    "date": [r"^(?P<date>" + DM + r") " + DM + r" "],
    "year": [r"^erstellt am \d{2}\.\d{2}\.(?P<year>\d{4})", r"Kontoauszug Nr\. \d+/(?P<year>\d{4})"],
    "type": [r"^" + DM + r" " + DM + r" (?P<type>.+?) " + NUM + r" [HS]$"],
    "amount": [r"^" + DM + r" " + DM + r" .+? (?P<amount>" + NUM + r") (?P<sign>[HS])$"],
}

SPEC = Spec(
    slug="bank11_pdf",
    label="Bank11 — Kontoauszug PDF",
    corpus="bank11",
    marks=[r"Bank11"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^Bu-Tag Wert Vorgang", block=r"^" + DM + r" " + DM + r" .+? " + NUM + r" [HS]$", fields=FIELDS,
            kinds={r"^Abschluss": "interest"}),
    ],
)

# Sberbank Europe's German Tagesgeld came on the same statement paper.
SPECS = [SPEC, Spec(slug="sberbank_pdf", label="Sberbank Europe — Kontoauszug PDF", corpus="sberbankeuropeag",
                    marks=[r"Sberbank"], number="de", docs=SPEC.docs)]
