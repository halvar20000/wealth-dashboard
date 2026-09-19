"""Suresse Direkt Bank (Santander Consumer Finance, Belgium) — the
Kontoauszug: "Nr dd-mm dd-mm text amount EUR", one statement page per
booking, the year on its "Neuer Saldo am dd-mm-yyyy" line."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"-?[\d.]+,\d{2}"
DM = r"\d{2}-\d{2}"

FIELDS = {
    "date": [r"^\d+ (?P<date>" + DM + r") " + DM + r" "],
    "year": [r"^Neuer Saldo am " + DM + r"-(?P<year>\d{4})", r"^(?P<year>\d{4})-\d{2}-\d{2}$"],
    "type": [r"^\d+ " + DM + r" " + DM + r" (?P<type>.+?) " + NUM + r" [A-Z]{3}$"],
    "amount": [r"^\d+ " + DM + r" " + DM + r" .+? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="suresse_pdf",
    label="Suresse Direkt Bank — Kontoauszug PDF",
    corpus="suressedirektbank",
    marks=[r"Suresse", r"suressedirektbank\.de"],
    number="de",
    docs=[
        Doc(kind="rows", when=r"^Nr\. Trans\.", block=r"^\d+ " + DM + r" " + DM + r" .+? " + NUM + r" [A-Z]{3}$", fields=FIELDS,
            kinds={r"zinsen": "interest"}),
    ],
)
