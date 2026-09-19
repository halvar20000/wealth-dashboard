"""UOB (Singapore) — the account statement (withdrawals and deposits
columns) and the credit-card statement (payments marked CR)."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

ACCOUNT = Table(row=r"^\s*(?P<date>\d{2} [A-Z][a-z]{2})\s{2,}", date="%d %b", currency="SGD",
                stmt=r"Period: \d{2} [A-Z][a-z]{2} \d{4} to (?P<date>\d{2} [A-Z][a-z]{2} \d{4})",
                header=r"^\s*Date\s+Description\s+Withdrawals", debit=r"Withdrawals", credit=r"Deposits")
CARD = Table(row=r"^\s*\d{2} [A-Z]{3}\s+(?P<date>\d{2} [A-Z]{3})\s{2,}", date="%d %b", currency="SGD",
             stmt=r"Statement Date\s+(?P<date>\d{2} [A-Z]{3} \d{4})", card=True)


def _rows(text: str) -> str:
    return rows(rows(text, ACCOUNT), CARD)


SPEC = Spec(
    slug="uob_pdf", label="UOB — statement PDF", corpus="mono:uob_debit",
    marks=[r"UOB", r"uobgroup\.com", r"United Overseas Bank"], number="en", layout=True, preprocess=_rows,
    docs=[Doc(kind="rows", when=r"Account Transaction Details|Credit Card\(s\) Statement", block=r"^ROW ", fields=fields(), kinds=ACCOUNT.kinds)],
)
SPECS = [SPEC, Spec(slug="uob_card_pdf", label="UOB — credit card statement PDF", corpus="mono:uob_credit",
                    marks=SPEC.marks, number="en", layout=True, preprocess=_rows, docs=SPEC.docs)]
