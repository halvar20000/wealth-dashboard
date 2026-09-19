"""Citibank (Singapore) — the credit-card statement: one amount
column, payments and refunds in brackets."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

CARD = Table(row=r"^\s*(?P<date>\d{2} [A-Z]{3})\s{2,}", date="%d %b", currency="SGD",
             stmt=r"Statement Date:?\s+(?P<date>[A-Z][a-z]+ \d{1,2}, \d{4})", card=True)

SPEC = Spec(
    slug="citibank_pdf", label="Citibank — credit card statement PDF", corpus="mono:citibank_credit",
    marks=[r"Citibank", r"CITIBANK", r"citibank\.com"], number="en", layout=True, preprocess=lambda t: rows(t, CARD),
    docs=[Doc(kind="rows", when=r"^\s*DATE\s+DESCRIPTION\s+AMOUNT", block=r"^ROW ", fields=fields(), kinds=CARD.kinds)],
)
