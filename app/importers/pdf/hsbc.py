"""HSBC (Singapore) — the credit-card statement: posting date, then
the transaction date, one amount column with CR for a credit."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

CARD = Table(row=r"^\s*\d{2} [A-Z][a-z]{2}\s+(?P<date>\d{2} [A-Z][a-z]{2})\s{2,}", date="%d %b", currency="SGD",
             stmt=r"Statement From \d{2} [A-Z]{3} \d{4} to (?P<date>\d{2} [A-Z]{3} \d{4})", card=True)

SPEC = Spec(
    slug="hsbc_pdf", label="HSBC (Singapore) — credit card statement PDF", corpus="mono:hsbc_credit",
    marks=[r"HSBC Bank \(Singapore\)", r"HSBC VISA", r"HSBC"], number="en", layout=True, preprocess=lambda t: rows(t, CARD),
    docs=[Doc(kind="rows", when=r"^POST\s+TRAN|DESCRIPTION\s+AMOUNT", block=r"^ROW ", fields=fields(), kinds=CARD.kinds)],
)
