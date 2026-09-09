"""What every CSV importer produces, and the parsing every one needs.

An importer's whole job is to turn one broker's file into `ParsedTxn`
rows. It does not touch the database, which is what lets the test suite
run a real export through a real parser and inspect the result without a
database existing at all.

The two helpers below look trivial and are not. European exports use a
comma as the decimal separator and a dot as the thousands separator —
so `float("1.234,56")` raises, and `float("1.234")` silently returns one
point two three four instead of one thousand two hundred and thirty
four. A number that parses to the wrong value is worse than one that
fails to parse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# The kinds a row can be. Deliberately small: enough to compute a
# holding and to tell money entering the account from money moving
# inside it, and no finer, because a taxonomy nobody uses is a taxonomy
# that goes wrong quietly.
KINDS = {"deposit", "withdrawal", "buy", "sell", "dividend", "interest",
         "fee", "tax", "transfer", "other"}


@dataclass
class ParsedTxn:
    txn_date: str                  # ISO, YYYY-MM-DD
    description: str
    amount: float                  # signed: money into the account is +
    currency: str
    kind: str = "other"
    external_id: str | None = None
    counterparty: str | None = None
    isin: str | None = None
    security_name: str | None = None
    quantity: float | None = None  # signed: bought is +, sold is −
    price: float | None = None
    fee: float | None = None
    tax: float | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind {self.kind!r}")


@dataclass
class ParseResult:
    rows: list[ParsedTxn] = field(default_factory=list)
    skipped: int = 0
    # Lines the parser could not read. Kept and shown rather than
    # counted: "3 rows skipped" tells the user nothing they can act on.
    problems: list[str] = field(default_factory=list)


def parse_decimal(raw: str | None) -> float | None:
    """A number from a European or an English export.

    Decides by looking at which separator comes LAST, because that is the
    decimal one in both conventions:

        "1.234,56" -> 1234.56      (European)
        "1,234.56" -> 1234.56      (English)
        "0,011"    -> 0.011        (European, no thousands separator)
        "1,234"    -> 1234.0       (English thousands — see below)

    The genuinely ambiguous case is a single comma with exactly three
    digits after it: "1,234" is one thousand in an English export and one
    point two three four in a European one. It is resolved as thousands,
    because a broker quoting a share price to exactly three decimals is
    rarer than one writing a four-figure amount — and the caller can pass
    an unambiguous string if it knows better.
    """
    if raw is None:
        return None
    s = str(raw).strip().replace(" ", "").replace(" ", "")
    if not s:
        return None
    s = s.replace("'", "")                   # Swiss thousands separator
    neg = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.lstrip("+-").strip("()")

    last_comma, last_dot = s.rfind(","), s.rfind(".")
    if last_comma > last_dot:                # European: comma is decimal
        s = s.replace(".", "").replace(",", ".")
    elif last_dot > last_comma:              # English: dot is decimal
        s = s.replace(",", "")
    elif last_comma == last_dot == -1:
        pass                                 # plain integer
    try:
        value = float(s)
    except ValueError:
        return None
    return -value if neg else value


_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d")


def parse_date(raw: str | None) -> str | None:
    """An ISO date from whatever the broker wrote.

    `%d-%m-%Y` is tried before `%Y-%m-%d` never happens by accident —
    the formats are unambiguous by length. What is NOT tried is
    `%m/%d/%Y`: a US-order date is indistinguishable from a European one
    for the first twelve days of any month, so guessing would put one
    row in three in the wrong month and be invisible in the other two.
    An importer that needs it must say so explicitly.
    """
    if not raw:
        return None
    s = str(raw).strip()
    if "T" in s:                             # ISO timestamp
        s = s.split("T", 1)[0]
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


_ISIN_RE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b")


def find_isin(text: str | None) -> str | None:
    """An ISIN is two country letters, nine alphanumerics and a check
    digit. Specific enough to pull out of free text without matching a
    ticker or an order reference."""
    if not text:
        return None
    m = _ISIN_RE.search(str(text).upper())
    return m.group(1) if m else None


def normalise_csv_text(text: str) -> str:
    """Undo the damage a spreadsheet does to a CSV.

    A file that has been opened and re-saved by Excel or Numbers can come
    back with every LINE wrapped in one pair of quotes and the original
    quotes doubled:

        "datetime,""date"",""category"",..."
        "2026-05-04T10:20:34Z,""2026-05-04"",""DEFAULT"",..."

    Parsed normally that is a one-column file, so a header check fails and
    the import is refused for a file that plainly is the right export.
    The user sees "this is not a Trade Republic export" about a Trade
    Republic export, which is the least helpful true statement available.

    Detected by shape rather than guessed: every line parses to exactly
    one field, and that field itself contains commas. Then the real CSV
    is the concatenation of those fields.
    """
    import csv as _csv
    import io as _io

    try:
        rows = list(_csv.reader(_io.StringIO(text)))
    except _csv.Error:
        return text
    rows = [r for r in rows if r]
    if len(rows) < 2:
        return text
    if not all(len(r) == 1 for r in rows[:20]):
        return text
    if "," not in rows[0][0]:
        return text
    return "\n".join(r[0] for r in rows)
