"""Statements read by their columns.

The specs in this package see a document as lines of words. A cash or
card statement of the kind the Singaporean, Malaysian and American
banks print is not that: it is a table, and what a figure means —
withdrawal or deposit, charge or payment — is the column it sits in.
So these are read from the PDF with its layout kept (`Spec.layout`),
and this module turns the table into rows a spec can read:

    ROW 2024-11-04 | Cash Withdrawal ATM CASH KESTREL AVE | -210.00 SGD

A `Table` says what the bank's table looks like: how a row begins
(its date), where the statement's own date is (for rows that print no
year), what the columns are called when two of them hold the money,
how a credit is marked when one column holds it all, and where the
table ends. `rows(text, table)` appends one ROW line per booking to
the text it was given; a spec then reads the ROW lines and nothing
else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from ..statement import MONTHS

# A figure in a statement's column: 1,250.00 (300.00) -400.00 +80.00
# 60.00CR 500.00 CR 120.00- 300.00+ 8'500.00 S$27.00 RM1,209.50
NUMBER = re.compile(r"(?<![\w.])(?:S\$|RM|\$|€|£)?(?P<open>\()?(?P<sign>[+-])?(?P<figure>[\d,']*\d\.\d{2})(?P<close>\))?(?P<tail>\s?CR\b|[+-](?!\d))?(?![\d.])")


@dataclass
class Table:
    row: str                        # regex; a row's first line, with (?P<date>…)
    date: str                       # strptime-like: "%d %b", "%d/%m", "%m/%d", "%d/%m/%y", "%m/%d/%y", "%d.%m.%Y", "%d %b %y"
    currency: str
    stmt: str | None = None         # regex with (?P<date>…): the statement's date, for the year
    header: str | None = None       # regex; the line whose column labels place the figures
    debit: str | None = None        # regex; the label of the column money leaves in
    credit: str | None = None       # regex; …and comes in
    amount: str | None = None       # regex; the label of one signed amount column, when a
                                    # balance column beside it would be taken for it
    balance: str | None = None      # regex; the running-balance column, whose figures are
                                    # never the booking's amount
    more: str | None = None         # regex; a further booking under the date above it —
                                    # a bank that prints the day once for several rows
    card: bool = False              # one Amount column where a bare figure is a charge and a
                                    # marked one (CR, brackets, a sign) a payment or refund
    stop: str = r"^\s*(?:Total|TOTAL|SUB TOTAL|Balance Carried|BALANCE C/F|NEW BALANCE|End of|Page \d)"
    skip: str = r"(?i)balance (?:b/f|brought|from previous|carried)|previous (?:statement )?balance|last month's balance|beginning balance|outstanding balance|total (?:outstanding|debit|credit)"
    strip: str | None = None        # regex cut out of a description (a reference column)
    kinds: dict = field(default_factory=lambda: {r"(?i)interest": "interest", r"(?i)\bfee\b|charge|prices|commission": "fee"})


def _stmt_date(text: str, pattern: str | None) -> tuple[int | None, int | None]:
    """(year, month) of the statement, from wherever the bank prints it."""
    if not pattern:
        return None, None
    m = re.search(pattern, text, re.M)
    if not m:
        return None, None
    raw = " ".join(m.group("date").replace(",", " ").split())
    for fmt in ("%d %b %Y", "%d %B %Y", "%B %d %Y", "%b %d %Y", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y",
                "%Y-%m-%d", "%d %b %y", "%d %B %y", "%d%b%Y", "%d%b%y"):
        try:
            d = datetime.strptime(raw, fmt)
            return d.year, d.month
        except ValueError:
            continue
    return None, None


def _row_date(raw: str, fmt: str, year: int | None, month: int | None) -> str | None:
    """The row's date, the statement's year lent to a row without one —
    the year before when the row's month lies after the statement's."""
    raw = " ".join(raw.split())
    if "%y" in fmt or "%Y" in fmt:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            return None
    if year is None:
        return None
    m = re.match(r"^(\d{1,2})[ /.-]+(\d{1,2}|[A-Za-z]{3,})$", raw)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if b.isdigit():
        day, mon = (int(a), int(b)) if fmt.startswith("%d") else (int(b), int(a))
    else:
        day, mon = int(a), MONTHS.get(b.lower()[:3])
    if not mon or not 1 <= mon <= 12:
        return None
    y = year - 1 if (month and mon > month) else year
    try:
        return datetime(y, mon, day).date().isoformat()
    except ValueError:
        return None


def _value(m: re.Match) -> tuple[float, bool, bool]:
    """(figure, marked as negative, marked as a credit)."""
    v = float(m.group("figure").replace(",", "").replace("'", ""))
    tail = (m.group("tail") or "").strip()
    negative = bool(m.group("open")) or m.group("sign") == "-" or tail == "-"
    credit = tail in ("CR", "+") or m.group("sign") == "+"
    return v, negative, credit


def _spans(header_line: str, pattern: str | None) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(pattern, header_line)] if pattern else []


def _money(figures: list, has_balance: bool) -> tuple[list, bool]:
    """(the figures of a line that can be money, whether the running
    balance was taken off the end).

    Where the table has a balance column, the last figure of a line is
    it: a statement prints the balance after the amount, and a line
    whose columns sit a little off their heads — pypdf lays a row with
    no description out differently — is still unambiguous in that
    order. Once the balance is accounted for, the figures left are
    money and are placed between the money columns alone."""
    if has_balance and len(figures) > 1:
        return figures[:-1], True
    return figures, False


def _column(m: re.Match, debit: list, credit: list, balance: list = ()) -> str | None:
    """Which column a figure sits under: the label whose right edge is
    nearest the figure's — numbers are right-aligned under their heads.
    A figure under the running balance is none of the two."""
    best, where = None, None
    for name, spans in (("debit", debit), ("credit", credit), ("balance", balance)):
        for start, end in spans:
            d = abs(m.end() - end)
            if best is None or d < best:
                best, where = d, name
    if best is None or best > 24 or where == "balance":
        return None
    return where


def rows(text: str, table: Table, strip_type: str | None = None) -> str:
    """The text with a ROW line per booking appended. `strip_type` is a
    regex for the payment-type word a bank prints before the merchant
    — kept out of the description, where it says nothing the kind does
    not."""
    year, month = _stmt_date(text, table.stmt)
    row_re = re.compile(table.row)
    more_re = re.compile(table.more) if table.more else None
    stop_re, skip_re = re.compile(table.stop), re.compile(table.skip)
    header_re = re.compile(table.header) if table.header else None
    debit = credit = column = balance = []
    last_date: str | None = None
    out: list[str] = []
    current: list | None = None     # [date, description, amount]

    def flush():
        nonlocal current
        if current and current[2] is not None and not skip_re.search(current[1]):
            desc = " ".join(current[1].split())
            if strip_type:
                without_type = re.sub(r"^" + strip_type + r"\b\s*", "", desc)
                desc = without_type or desc      # a row that is only its type keeps it

            if table.strip:
                desc = " ".join(re.sub(table.strip, " ", desc).split())
            out.append(f"ROW {current[0]} | {desc} | {current[2]:.2f} {table.currency}")
        current = None

    for line in text.splitlines():
        if header_re and header_re.search(line):
            flush()
            debit, credit, column = _spans(line, table.debit), _spans(line, table.credit), _spans(line, table.amount)
            balance = _spans(line, table.balance)
            continue
        if not line.strip():
            flush()
            continue
        if stop_re.search(line):
            flush()
            continue
        m = row_re.match(line)
        more = more_re.match(line) if (more_re and not m and last_date) else None
        if m or more:
            flush()
            if m:
                date = _row_date(m.group("date"), table.date, year, month)
                if not date:
                    continue
                last_date = date
            else:
                date, m = last_date, more
            rest = line[m.end():]
            amount = None
            figures = list(NUMBER.finditer(rest))
            if table.debit or table.credit:
                money, took_balance = _money(figures, bool(balance))
                left = [] if took_balance else [(s - m.end(), e - m.end()) for s, e in balance]
                for f in money:
                    where = _column(f, [(s - m.end(), e - m.end()) for s, e in debit],
                                    [(s - m.end(), e - m.end()) for s, e in credit], left)
                    if where:
                        v, _, _ = _value(f)
                        amount = v if where == "credit" else -v
                        rest = rest[:f.start()]
                        break
            elif figures:
                f = figures[-1]
                if column:
                    # the figure under the amount label, not the balance beside it
                    shifted = [(s - m.end(), e - m.end()) for s, e in column]
                    f = min(figures, key=lambda g: min(abs(g.end() - e) for _, e in shifted))
                v, negative, credited = _value(f)
                if table.card:
                    # a charge is printed bare; anything marked is money
                    # coming back to the card
                    amount = v if (negative or credited) else -v
                else:
                    amount = -v if negative else v
                rest = rest[:f.start()]
            current = [date, rest.strip(), amount]
            continue
        if current is None:
            continue
        if not NUMBER.search(line):
            current[1] += " " + line.strip()
            continue
        # A bank that prints the merchant on the booking's line and the
        # place and the money on the next: the figure under a money
        # column here is this booking's, and the words are its address.
        if current[2] is None and (table.debit or table.credit):
            text_end = len(line)
            money, took_balance = _money(list(NUMBER.finditer(line)), bool(balance))
            for f in money:
                where = _column(f, debit, credit, () if took_balance else balance)
                if where:
                    v, _, _ = _value(f)
                    current[2] = v if where == "credit" else -v
                    text_end = min(text_end, f.start())
                    break
            words = line[:text_end].strip()
            if words:
                current[1] += " " + words
    flush()
    return text + "\n" + "\n".join(out) + "\n"


def fields() -> dict:
    """The spec fields that read a ROW line."""
    return {
        "date": [r"^ROW (?P<date>\d{4}-\d{2}-\d{2}) \| "],
        "security": [r"^ROW \S+ \| (?P<name>.+?) \| "],
        "type": [r"^ROW \S+ \| (?P<type>.+?) \| "],
        "amount": [r" \| (?P<amount>-?[\d.]+) (?P<currency>[A-Z]{3})$"],
    }
