"""first direct (HSBC UK) — the 1st Account statement.

Read by its columns: *£ Paid out*, *£ Paid in* and the running
balance, which is never a booking. The paper's habits: the day is
printed once and the bookings of that day follow under it, each
opening with its payment type (VIS, DD, SO, BP, ATM, ))) for
contactless); the merchant sits on the booking's line and the place
and the money on the next; and the sheet opens and closes with a
brought-forward and a carried-forward balance, which are not
bookings either.
"""

from __future__ import annotations

from ..statement import Doc, Spec
from .layout import Table, fields, rows

# A booking's own line: "01 Jun 26  VIS  SUPERDRY"; or, under the same
# day, "VIS  ALDO" with no date of its own.
TYPES = r"(?:VIS|DD|SO|BP|ATM|CR|TFR|CHQ|DR|BGC|POS|FPI|FPO|\)\)\))"
ACCOUNT = Table(
    row=r"^\s*(?P<date>\d{2} [A-Z][a-z]{2} \d{2})\s+",
    more=r"^\s+" + TYPES + r"\s",
    date="%d %b %y", currency="GBP",
    header=r"Paid out.*Paid in|Payment type and details",
    debit=r"(?:£ )?Paid out", credit=r"(?:£ )?Paid in", balance=r"(?:£ )?Balance",
    stop=r"^\s*(?:Total|End of statement)",
    skip=r"(?i)balance (?:brought|carried) forward|opening balance|closing balance",
)

SPEC = Spec(
    slug="firstdirect_pdf",
    label="first direct — 1st Account statement PDF",
    corpus="mono:firstdirect",
    marks=[r"firstdirect\.com", r"first direct is a division of HSBC", r"Your 1st Account details"],
    number="en",
    layout=True,
    preprocess=lambda t: rows(t, ACCOUNT, strip_type=TYPES),
    docs=[
        Doc(kind="rows", when=r"Your 1st Account details|Payment type and details", block=r"^ROW ",
            fields=fields(), kinds={r"(?i)interest": "interest", r"(?i)\bfee\b|charge|overdraft": "fee"}),
    ],
)
