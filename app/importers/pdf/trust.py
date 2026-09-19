"""Trust Bank (Singapore) — the credit-card statement: one amount
column, a payment marked with a plus."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

CARD = Table(row=r"^\s*(?P<date>\d{1,2} [A-Z][a-z]{2})\s{2,}", date="%d %b", currency="SGD",
             stmt=r"Statement cycle\s+\d{1,2} [A-Z][a-z]{2} \d{4} - (?P<date>\d{1,2} [A-Z][a-z]{2} \d{4})", card=True)

SPEC = Spec(
    slug="trust_pdf", label="Trust Bank — credit card statement PDF", corpus="mono:trust_credit",
    marks=[r"Trust Bank", r"TRUST CREDIT CARD", r"trustbank\.sg"], number="en", layout=True, preprocess=lambda t: rows(t, CARD),
    docs=[Doc(kind="rows", when=r"Credit card statement|Posting date\s+Description", block=r"^ROW ", fields=fields(), kinds=CARD.kinds)],
)
