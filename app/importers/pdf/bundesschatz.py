"""Bundesschatz (Austrian treasury savings) — the Kontoauszug of
settled interest periods and the Ein- und Auszahlungen list."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"-?[\d.]+,\d{2}"
DATE = r"\d{2}\.\d{2}\.\d{4}"

CASH_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?P<type>Einzahlung|Auszahlung) "],
    "amount": [r"^" + DATE + r" \S+ (?P<amount>" + NUM + r") ", r"^" + DATE + r" \S+ .+ (?P<amount>" + NUM + r")$"],
    "ref": [r"^" + DATE + r" \S+ (?:" + NUM + r" )?(?P<ref>[A-Z]{2}\d{2}[A-Z0-9 ]+?)(?: " + NUM + r")?$"],
}
# Produkt Erwerb Fälligkeit Kapital Zinssatz Zinsen Steuersatz Steuer Zinsen netto Gesamt Abgerechnet
INTEREST_ROW = r"^.+? " + DATE + r" " + DATE + r" " + NUM + r" [\d,]+ % " + NUM + r" [\d,]+% " + NUM + r" " + NUM + r" " + NUM + r" ja$"
INTEREST_FIELDS = {
    "date": [r"^.+? " + DATE + r" (?P<date>" + DATE + r") "],
    "amount": [r" (?P<gross>" + NUM + r") [\d,]+% (?P<tax>" + NUM + r") (?P<amount>" + NUM + r") " + NUM + r" ja$"],
    "type": [r"^(?P<type>.+?) " + DATE],
}

SPEC = Spec(
    slug="bundesschatz_pdf",
    label="Bundesschatz — Kontoauszug PDF",
    corpus="bundesschatz",
    marks=[r"Bundesschatz"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^Datum Art Betrag", block=r"^" + DATE + r" (?:Einzahlung|Auszahlung) ", fields=CASH_FIELDS,
            kinds={r"^Einzahlung": "deposit", r"^Auszahlung": "withdrawal"}),
        Doc(kind="interest", when=r"^Produkt Erwerb F.lligkeit Kapital", block=INTEREST_ROW, fields=INTEREST_FIELDS),
    ],
)
