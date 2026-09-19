"""DBS / POSB (Singapore) — the savings-account statement (withdrawal
and deposit columns) and the credit-card statement (one amount column,
payments marked CR)."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

DATE = r"^\s*(?P<date>\d{2} [A-Z][a-z]{2})\s{2,}"
ACCOUNT = Table(row=DATE, date="%d %b", currency="SGD",
                stmt=r"As at (?P<date>\d{2} [A-Z][a-z]{2} \d{4})",
                header=r"DETAILS OF TRANSACTIONS", debit=r"WITHDRAWAL", credit=r"DEPOSIT")
CARD = Table(row=r"^\s*(?P<date>\d{2} [A-Z]{3})\s{2,}", date="%d %b", currency="SGD",
             stmt=r"STATEMENT DATE[\s\S]*?^\s*(?P<date>\d{2} [A-Z][a-z]{2} \d{4})", card=True)

FIELDS = fields()
KINDS = ACCOUNT.kinds


def _rows(text: str) -> str:
    return rows(rows(text, ACCOUNT), CARD)


SPEC = Spec(
    slug="dbs_pdf",
    label="DBS / POSB — statement PDF",
    corpus="mono:dbs_debit",
    marks=[r"DBS Bank", r"dbs\.com", r"DBS Cards", r"POSB"],
    number="en",
    layout=True,
    preprocess=_rows,
    docs=[
        Doc(kind="rows", when=r"DETAILS OF TRANSACTIONS|^DATE\s+DESCRIPTION\s+AMOUNT", block=r"^ROW ", fields=FIELDS, kinds=KINDS),
    ],
)
SPECS = [SPEC, Spec(slug="dbs_card_pdf", label="DBS / POSB — credit card statement PDF", corpus="mono:dbs_credit",
                    marks=SPEC.marks, number="en", layout=True, preprocess=_rows, docs=SPEC.docs)]
