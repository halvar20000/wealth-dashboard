"""American Express (Singapore) — the card statement: dated rows with
one amount column; a payment is a credit."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

CARD = Table(row=r"^\s*(?P<date>\d{2}\.\d{2}\.\d{2})\s{2,}", date="%d.%m.%y", currency="SGD", card=True,
             skip=r"(?i)balance|total of new transactions")


def _rows(text: str) -> str:
    # A payment carries no CR here: it is named.
    out = rows(text, CARD)
    return "\n".join(
        line.replace(" | -", " | ", 1) if line.startswith("ROW ") and "PAYMENT" in line.upper() and " | -" in line else line
        for line in out.splitlines())


SPEC = Spec(
    slug="amex_pdf", label="American Express — card statement PDF", corpus="mono:amex_credit",
    marks=[r"American Express", r"americanexpress\.com"], number="en", layout=True, preprocess=_rows,
    docs=[Doc(kind="rows", when=r"Statement of Account|Statement Period", block=r"^ROW ", fields=fields(), kinds=CARD.kinds)],
)
