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

import re
from datetime import datetime

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
    stop=r"(?i)^\s*(?:Total|End of statement|Interest Rates|AER\b|Your interest rates)",
    # The rates table prints figures too — a limit, a per-cent, an AER.
    # None of them is a booking, wherever on the line they sit.
    skip=r"(?i)balance (?:brought|carried) forward|opening balance|closing balance|"
         r"%|\bAER\b|\bEAR\b|interest rate|overdraft limit|credit interest",
)

# ─── The same statement, scanned ─────────────────────────────────────
#
# OCR gives the words back but not the columns: "18 May 26 DD B/CARD
# CASHBACK 262.97 540.39" is one line, and which of the two figures is
# the money and which the balance cannot be told from where they sit.
# It can be told from what they do. The sheet states its opening
# balance, every booking states the balance after it, and the
# difference between two balances is the booking — sign and all. So
# where the columns are gone, the balance column does the work.

MONEY = r"-?\d[\d,]*\.\d{2}"
_LINE = re.compile(r"^\s*(?P<date>\d{2} [A-Za-z]{3} \d{2})?\s*(?P<body>.*?)\s+"
                   r"(?P<figures>" + MONEY + r"(?:\s+" + MONEY + r")?)\s*$")
_OPENING = re.compile(r"(?i)balance (?:brought forward|b/f)\D*(" + MONEY + r")")
# After the bookings, the sheet prints its rates: AER, EAR, the £250
# that costs nothing. Those lines carry figures and words and would
# otherwise be read as bookings — one user got an "over 250" payment
# and a "Credit interest is not paid" one out of them. The table ends
# where the balance is carried forward; anything with a per-cent sign
# in it was never a booking anyway.
_RATES = re.compile(r"(?i)\bAER\b|\bEAR\b|interest rate|overdraft (?:rate|limit)|"
                    r"arranged overdraft|formal overdraft|representative")


def _money(raw: str) -> float:
    return float(raw.replace(",", ""))


def by_balance(text: str) -> str:
    """ROW lines read from the running balance.

    Works on the columns' ruins as well as on the columns: the sheet
    states its opening balance, most bookings state the balance after
    them, and the difference is the booking, sign and all. A line
    without figures is the merchant, kept for the line that carries
    the money; a line whose balance the paper left out is signed by
    the next balance that follows it.
    """
    opening = _OPENING.search(text)
    if not opening:
        return text
    balance = _money(opening.group(1))
    out: list[str] = []
    pending: list[tuple[str, str, float]] = []      # date, text, size
    label: list[str] = []
    last_date = None
    started = False                                 # the table begins at the opening balance
    for raw in text.splitlines():
        line = raw.strip()
        if re.search(r"(?i)balance (?:brought forward|b/f)", line):
            started, label = True, []
            continue
        if re.search(r"(?i)balance (?:carried forward|c/f)", line):
            # The end of this page's table. The next page says "brought
            # forward" and turns it on again; what follows the last one
            # is the rates, not the money.
            started, label = False, []
            continue
        if not started or not line:
            continue
        if "%" in line or _RATES.search(line):
            label = []
            continue
        day = re.match(r"^(\d{2} [A-Za-z]{3} \d{2})\s*", line)
        if day:
            try:
                last_date = datetime.strptime(" ".join(day.group(1).split()), "%d %b %y").date().isoformat()
            except ValueError:
                pass
            line = line[day.end():]
        line = re.sub(r"^" + TYPES + r"\s+", "", line.strip())
        figures = re.findall(MONEY, line)
        words = " ".join(re.sub(MONEY, " ", line).split())
        if not figures:
            if words:
                label.append(words)
                del label[:-2]                      # the merchant and its place, no more
            continue
        if not last_date:
            label = []
            continue
        body = " ".join([*label, words]).strip() or "first direct"
        label = []
        if len(figures) >= 2:
            size, after = _money(figures[0]), _money(figures[-1])
            step = round(after - balance, 2)        # what the balance did over this line
            balance = after
            # The lines before this one had no balance of their own;
            # together with this booking they make the step. This
            # booking's size is printed, so its sign is the one that
            # leaves those lines their own sizes.
            mine = min((-size, size), key=lambda c: abs(round(step - c, 2) - sum(-p[2] for p in pending)))
            rest = round(step - mine, 2)
            if len(pending) == 1:
                out.append(f"ROW {pending[0][0]} | {pending[0][1]} | {rest:.2f} GBP")
            else:
                for d_, t_, s_ in pending:
                    out.append(f"ROW {d_} | {t_} | {-s_:.2f} GBP")
            pending = []
            out.append(f"ROW {last_date} | {body} | {mine:.2f} GBP")
        else:
            pending.append((last_date, body, _money(figures[0])))
    for d_, t_, s_ in pending:
        # No balance ever followed: a payment out, which is what an
        # unbalanced line in a current account almost always is.
        out.append(f"ROW {d_} | {t_} | {-s_:.2f} GBP")
    return text + "\n" + "\n".join(out) + "\n"


def read(text: str) -> str:
    """The balance where the sheet states one — it is arithmetic, and
    survives a scan that has flattened the columns; the columns where
    it does not."""
    done = by_balance(text)
    if any(line.startswith("ROW ") for line in done.splitlines()):
        return done
    return rows(text, ACCOUNT, strip_type=TYPES)


SPEC = Spec(
    slug="firstdirect_pdf",
    label="first direct — 1st Account statement PDF",
    corpus="mono:firstdirect",
    marks=[r"firstdirect\.com", r"first direct is a division of HSBC", r"Your 1st Account details"],
    number="en",
    layout=True,
    preprocess=read,
    docs=[
        Doc(kind="rows", when=r"Your 1st Account details|Payment type and details", block=r"^ROW ",
            fields=fields(), kinds={r"(?i)interest": "interest", r"(?i)\bfee\b|charge|overdraft": "fee"}),
    ],
)
