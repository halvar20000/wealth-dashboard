"""Bank of America — the deposit-account statement (one signed amount
column under "Deposits and other additions" and "Withdrawals and other
subtractions") and the credit-card statement (a payment negative,
reference numbers beside the description)."""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

ACCOUNT = Table(row=r"^\s*(?P<date>\d{2}/\d{2}/\d{2})\s{2,}", date="%m/%d/%y", currency="USD",
                stop=r"^\s*Total |^\s*Ending balance|^\s*Service fees")
CARD = Table(row=r"^\s*(?P<date>\d{2}/\d{2})\s+\d{2}/\d{2}\s{2,}", date="%m/%d", currency="USD",
             stmt=r"Statement Closing Date\s+(?P<date>\d{2}/\d{2}/\d{4})", card=True,
             strip=r"\s\d{4}\s+\d{4}$", stop=r"^\s*TOTAL ")


def _rows(text: str) -> str:
    return rows(rows(text, ACCOUNT), CARD)


SPEC = Spec(
    slug="bankofamerica_pdf", label="Bank of America — statement PDF", corpus="mono:bank_of_america_debit",
    marks=[r"Bank of America", r"bankofamerica\.com"], number="en", layout=True, preprocess=_rows,
    docs=[Doc(kind="rows", when=r"Deposits and other additions|Payments and Other Credits", block=r"^ROW ", fields=fields(), kinds=ACCOUNT.kinds)],
)
SPECS = [SPEC, Spec(slug="bankofamerica_card_pdf", label="Bank of America — credit card statement PDF", corpus="mono:bank_of_america_credit",
                    marks=SPEC.marks, number="en", layout=True, preprocess=_rows, docs=SPEC.docs)]
