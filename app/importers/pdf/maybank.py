"""Maybank (Malaysia) — the savings-account statement (one amount
column, signed with a trailing + or -) and the credit-card statement
(payments marked CR)."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

ACCOUNT = Table(row=r"^\s*(?P<date>\d{2}/\d{2}/\d{2})\s{2,}", date="%d/%m/%y", currency="MYR",
                header=r"TRANSACTION DESCRIPTION", amount=r"TRANSACTION AMOUNT",
                stop=r"^\s*(?:TOTAL|ENDING BALANCE|CLOSING BALANCE)")
CARD = Table(row=r"^\s*\d{2}/\d{2}\s+(?P<date>\d{2}/\d{2})\s{2,}", date="%d/%m", currency="MYR",
             stmt=r"Statement Date\s+(?P<date>\d{2} [A-Z][a-z]{2} \d{2})", card=True)


def _rows(text: str) -> str:
    return rows(rows(text, ACCOUNT), CARD)


SPEC = Spec(
    slug="maybank_pdf", label="Maybank — statement PDF", corpus="mono:maybank_debit",
    marks=[r"Maybank", r"MAYBANK", r"Malayan Banking"], number="en", layout=True, preprocess=_rows,
    docs=[Doc(kind="rows", when=r"TRANSACTION DESCRIPTION|^\s*Date\s+Description\s+Amount", block=r"^ROW ", fields=fields(), kinds=ACCOUNT.kinds)],
)
SPECS = [SPEC, Spec(slug="maybank_card_pdf", label="Maybank — credit card statement PDF", corpus="mono:maybank_credit",
                    marks=SPEC.marks, number="en", layout=True, preprocess=_rows, docs=SPEC.docs)]
