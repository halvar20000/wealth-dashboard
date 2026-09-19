"""Standard Chartered (Singapore) — the credit-card statement: the
transaction date first, the posting date after it, a transaction
reference beside the amount, payments marked CR."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

CARD = Table(row=r"^\s*(?P<date>\d{2} [A-Z][a-z]{2})\s+\d{2} [A-Z][a-z]{2}\s{2,}", date="%d %b", currency="SGD",
             stmt=r"Statement Date\s*:\s*(?P<date>\d{1,2} [A-Z][a-z]{2} \d{4})", card=True,
             strip=r"Transaction Ref \d+")

SPEC = Spec(
    slug="standardchartered_pdf", label="Standard Chartered — credit card statement PDF", corpus="mono:standard_chartered_credit",
    marks=[r"Standard Chartered", r"sc\.com/sg"], number="en", layout=True, preprocess=lambda t: rows(t, CARD),
    docs=[Doc(kind="rows", when=r"Credit Card and Personal Loan Statement|CREDIT CARD", block=r"^ROW ", fields=fields(), kinds=CARD.kinds)],
)
