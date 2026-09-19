"""OCBC (Singapore) — the account statement (withdrawal and deposit
columns) and the credit-card statement (payments in brackets)."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

ACCOUNT = Table(row=r"^\s*(?P<date>\d{2} [A-Z]{3})\s+\d{2} [A-Z]{3}\s{2,}", date="%d %b", currency="SGD",
                stmt=r"\d{2} [A-Z]{3} \d{4} TO (?P<date>\d{2} [A-Z]{3} \d{4})",
                header=r"^\s*Date\s+Date\s+Description", debit=r"Withdrawal", credit=r"Deposit")
CARD = Table(row=r"^\s*(?P<date>\d{2}/\d{2})\s{2,}", date="%d/%m", currency="SGD",
             stmt=r"STATEMENT DATE[\s\S]*?^\s*(?P<date>\d{2}-\d{2}-\d{4})", card=True)


def _rows(text: str) -> str:
    return rows(rows(text, ACCOUNT), CARD)


SPEC = Spec(
    slug="ocbc_pdf", label="OCBC — statement PDF", corpus="mono:ocbc_debit",
    marks=[r"OCBC"], number="en", layout=True, preprocess=_rows,
    docs=[Doc(kind="rows", when=r"STATEMENT OF ACCOUNT|TRANSACTION DATE\s+DESCRIPTION", block=r"^ROW ", fields=fields(), kinds=ACCOUNT.kinds)],
)
SPECS = [SPEC, Spec(slug="ocbc_card_pdf", label="OCBC — credit card statement PDF", corpus="mono:ocbc_credit",
                    marks=SPEC.marks, number="en", layout=True, preprocess=_rows, docs=SPEC.docs)]
