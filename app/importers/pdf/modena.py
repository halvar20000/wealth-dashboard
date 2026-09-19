"""Modena (Estonia) — the income statement of the vault: a row per
credit, revenue share and bonus alike."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
ROW = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \S.* €-?" + NUM + r"$"
FIELDS = {
    "date": [r"^(?P<date>\d{4}-\d{2}-\d{2}) "],
    "type": [r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (?P<type>.+?) €"],
    "amount": [r" (?P<currency>€)(?P<amount>-?" + NUM + r")$"],
}

SPEC = Spec(
    slug="modena_pdf",
    label="Modena — Income statement PDF",
    corpus="modenaestonia",
    marks=[r"Modena", r"Vault revenue share", r"Total Vault Net Income"],
    number="en",
    docs=[
        Doc(kind="rows", when=r"^Income statement", block=ROW, fields=FIELDS,
            kinds={r"revenue|[Ii]nterest": "interest", r"bonus": "deposit", r"buyback": "interest"}),
    ],
)
