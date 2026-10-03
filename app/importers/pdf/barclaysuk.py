"""Barclays (UK) — the Bank Account and Bank Card statements.

Read by its columns: *Money out*, *Money in* and the running balance,
which is never a booking. The paper's habits: the day is printed once
and the bookings of that day follow under it, each opening with what
Barclays calls the payment — "Card Payment to", "Direct Debit to",
"Cash Machine Withdrawal at", "Account Credit: Deposit at"; the
merchant's branch, a reference or a till time sits on the next line and
belongs to the booking above it; and the balance is printed on the last
booking of a day rather than on every one.

The year is nowhere on a row — "9 Jan" is all a row says — so it comes
from the statement date in the header, and a January row on a February
statement keeps the year it was in.
"""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

# What Barclays prints at the head of a booking. A further booking under
# the same day starts with one of these and no date of its own; a line
# that does not is the branch, the reference or the time, and belongs to
# the booking above.
TYPES = (r"(?:Card \w+ to|Card Payment|Direct Debit|Cash Machine|Account Credit|"
         r"Bill Payment|Standing Order|Bank Giro Credit|Giro Received|Received from|"
         r"Receipt|Transfer|Interest|Charges?|Payment|Cheque|Refund)")

ACCOUNT = Table(
    row=r"^\s*(?P<date>\d{1,2} [A-Z][a-z]{2})\s+",
    more=r"^\s{3,}(?=" + TYPES + r"\b)",
    date="%d %b",
    currency="GBP",
    stmt=r"Statement date\s+(?P<date>\d{1,2} [A-Z][a-z]{2} \d{4})",
    header=r"Money out\s+Money in|Description.*Money out",
    debit=r"Money out", credit=r"Money in", balance=r"Balance",
    # The small print under the table has no figures in it, so without
    # this it would be read as the address of the last booking.
    stop=r"^\s*(?:Continued|Your agreed limits|At a glance|Total payments|"
         r"Barclays Bank PLC|Registered (?:No|Office))",
    skip=r"(?i)start balance|end balance|balance brought|your transactions",
    strip=r"(?i)\bRef:?\s*[\w/]+(?:\s+\d+)*|\bTransferred \d{1,2}:\d{2}\b.*$",
)


SPEC = Spec(
    slug="barclaysuk_pdf",
    label="Barclays (UK) — Bank Account / Bank Card statement PDF",
    corpus="mono:barclaysuk",
    marks=[r"Your Barclays Bank (?:Account|Card) statement",
           r"Barclays Bank PLC\. Registered in England", r"BARCGB22"],
    number="en",
    layout=True,
    preprocess=lambda text: rows(text, ACCOUNT),
    docs=[
        Doc(kind="rows", when=r"Money out\s+Money in|Your transactions", block=r"^ROW ",
            fields=fields(),
            kinds={r"(?i)interest": "interest",
                   r"(?i)\bcharges?\b|overdraft|\bfee\b": "fee"}),
    ],
)
