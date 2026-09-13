"""A CSV nobody here has heard of, read through a mapping the user drew.

Every bank exports a CSV and every one of them is different, and a
parser per bank is a parser per bank — the four in this folder took a
real file each. The rest are the same thing under other headings: a
date column, an amount column, a description, perhaps an ISIN and a
quantity. So the user says once which column is which, the mapping is
kept under the file's header, and the next export from the same bank
is recognised the way a Degiro file is: by what is in it.

The mapping is a dict of field → column heading, plus a few options:

    txn_date, amount | debit + credit, description, counterparty,
    currency, isin, security_name, quantity, price, fee, tax, kind
    negate:  the export writes money out as positive
    currency_fixed: when there is no currency column

Kinds come from a kind column if there is one and its words are
known — Kauf, Buy, Achat, Verkauf, Sell, Vente, Dividende … — and are
worked out from the rest of the row if not: an ISIN and a quantity is
a buy or a sale, an ISIN and money in is a dividend, plain money is a
deposit or a withdrawal. A row's id is a hash of what it says, with a
counter for two rows that say exactly the same, so re-importing the
same export is harmless here too.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter

from ..db import get_conn
from .base import (KINDS, ParsedTxn, ParseResult, find_isin, normalise_csv_text,
                   parse_date, parse_decimal)

FIELDS = ("txn_date", "amount", "debit", "credit", "description", "counterparty",
          "currency", "isin", "security_name", "quantity", "price", "fee", "tax", "kind")
REQUIRED = ("txn_date",)

# A kind column's words, lower-cased, in the languages the app speaks
# and the ones the banks it targets write in.
KIND_WORDS = {
    "buy": {"buy", "kauf", "achat", "compra", "purchase", "bought", "acquisition"},
    "sell": {"sell", "verkauf", "vente", "venta", "sold", "sale", "cession"},
    "dividend": {"dividend", "dividende", "dividendo", "dividends", "distribution", "ausschüttung"},
    "interest": {"interest", "zinsen", "zins", "intérêts", "interets", "intereses"},
    "fee": {"fee", "fees", "gebühr", "gebühren", "frais", "comisión", "comision", "commission"},
    "tax": {"tax", "steuer", "impôt", "impot", "impuesto", "withholding", "quellensteuer"},
    "deposit": {"deposit", "einzahlung", "dépôt", "depot", "depósito", "deposito", "versement"},
    "withdrawal": {"withdrawal", "auszahlung", "retrait", "retiro", "reintegro"},
    "transfer": {"transfer", "übertrag", "transfert", "traspaso", "transferencia", "überweisung"},
}


def header_key(header: list[str]) -> str:
    return "|".join(" ".join(h.split()).lower() for h in header)


def detect_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample else ""
    counts = {d: first.count(d) for d in (",", ";", "\t", "|")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


def read(content: bytes | str, delimiter: str | None = None) -> tuple[list[str], list[list[str]], str]:
    """(header, rows, delimiter) of a CSV, spreadsheet damage undone."""
    text = content.decode("utf-8-sig", "replace") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    delimiter = delimiter or detect_delimiter(text[:4096])
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return [], [], delimiter
    header = [h.strip() for h in rows[0]]
    return header, rows[1:], delimiter


# ─── Saved mappings ──────────────────────────────────────────────────

def all_mappings() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM csv_mappings ORDER BY name").fetchall()
    return [_row(r) for r in rows]


def _row(r) -> dict:
    d = dict(r)
    d["mapping"] = json.loads(d["mapping"])
    return d


def find(header: list[str]) -> dict | None:
    with get_conn() as conn:
        r = conn.execute("SELECT * FROM csv_mappings WHERE header_key = ?",
                         (header_key(header),)).fetchone()
    return _row(r) if r else None


def save(name: str, header: list[str], delimiter: str, mapping: dict) -> int:
    """Store or replace the mapping for this header."""
    clean = {k: v for k, v in mapping.items() if k in FIELDS and v in header}
    for opt in ("negate", "currency_fixed"):
        if mapping.get(opt):
            clean[opt] = mapping[opt]
    name = " ".join(name.split())[:80] or "CSV"
    with get_conn() as conn:
        conn.execute("DELETE FROM csv_mappings WHERE header_key = ?", (header_key(header),))
        cur = conn.execute("INSERT INTO csv_mappings (name, header_key, delimiter, mapping) VALUES (?, ?, ?, ?)",
                           (name, header_key(header), delimiter, json.dumps(clean)))
        return int(cur.lastrowid)


def delete(mapping_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM csv_mappings WHERE id = ?", (mapping_id,))


def check(mapping: dict) -> list[str]:
    """What is wrong with a mapping, as field names; empty when it will do."""
    wrong = []
    if not mapping.get("txn_date"):
        wrong.append("txn_date")
    if not mapping.get("amount") and not (mapping.get("debit") or mapping.get("credit")):
        wrong.append("amount")
    return wrong


# ─── Reading a file through a mapping ────────────────────────────────

def parse_with(mapping: dict, content: bytes | str, account_currency: str = "EUR",
               delimiter: str | None = None, limit: int | None = None) -> ParseResult:
    header, rows, _ = read(content, delimiter)
    result = ParseResult()
    if not header:
        result.problems.append("The file is empty.")
        return result
    index = {h: i for i, h in enumerate(header)}

    def cell(row: list[str], field: str) -> str:
        col = mapping.get(field)
        if not col or col not in index or index[col] >= len(row):
            return ""
        return row[index[col]].strip()

    seen: Counter = Counter()
    negate = -1.0 if mapping.get("negate") else 1.0
    for n, row in enumerate(rows, start=2):
        if limit is not None and len(result.rows) >= limit:
            break
        date = parse_date(cell(row, "txn_date"))
        if not date:
            result.problems.append(f"line {n}: no date in {cell(row, 'txn_date')!r}")
            continue
        if mapping.get("amount"):
            amount = parse_decimal(cell(row, "amount"))
        else:
            debit = parse_decimal(cell(row, "debit")) or 0.0
            credit = parse_decimal(cell(row, "credit")) or 0.0
            amount = abs(credit) - abs(debit) if (debit or credit) else None
        if amount is None:
            result.skipped += 1
            continue
        amount *= negate
        currency = (cell(row, "currency") or mapping.get("currency_fixed") or account_currency).upper()[:3]
        description = " ".join(cell(row, "description").split()) or " ".join(cell(row, "counterparty").split()) or "—"
        isin = find_isin(cell(row, "isin")) or (find_isin(description) if mapping.get("isin") is None else None)
        quantity = parse_decimal(cell(row, "quantity"))
        price = parse_decimal(cell(row, "price"))
        fee = parse_decimal(cell(row, "fee"))
        tax = parse_decimal(cell(row, "tax"))
        explicit = _kind_word(cell(row, "kind"))
        kind = explicit or _kind("", isin, quantity, amount)
        # A kind the file names supplies the sign, as it does for a row
        # typed in: a "Kauf" is money out whichever way the bank wrote
        # the figure, a "Dividende" money in. Only a kind worked out
        # from the row keeps the sign the row came with — there is
        # nothing else to go on.
        if explicit in _SIGN:
            amount = _SIGN[explicit] * abs(amount)
        # The kind supplies the sign of the units, as it does for a row
        # typed in by hand; and a dividend's "units held" column is not
        # units that arrived — a holding sums every quantity it sees.
        if quantity is not None:
            if kind == "buy":
                quantity = abs(quantity)
            elif kind == "sell":
                quantity = -abs(quantity)
            elif kind != "transfer":
                quantity = None
        seed = "|".join([date, f"{amount:.2f}", currency, description, isin or "",
                         f"{quantity or 0:.6f}", cell(row, "counterparty")])
        seen[seed] += 1
        digest = hashlib.sha1(f"{seed}#{seen[seed]}".encode()).hexdigest()[:20]
        result.rows.append(ParsedTxn(
            txn_date=date, description=description[:500], amount=amount, currency=currency,
            kind=kind, external_id=f"csv:{digest}",
            counterparty=" ".join(cell(row, "counterparty").split())[:200] or None,
            isin=isin, security_name=" ".join(cell(row, "security_name").split())[:200] or None,
            quantity=quantity, price=abs(price) if price else None,
            fee=abs(fee) if fee else None, tax=abs(tax) if tax else None))
    return result


_SIGN = {"buy": -1.0, "fee": -1.0, "tax": -1.0, "withdrawal": -1.0,
         "sell": 1.0, "dividend": 1.0, "interest": 1.0, "deposit": 1.0}


def _kind_word(word: str) -> str | None:
    """The kind a kind column names, or None when it names nothing known."""
    w = " ".join(word.split()).lower()
    if not w:
        return None
    if w in KINDS:
        return w
    for kind, words in KIND_WORDS.items():
        if w in words or any(w.startswith(x) for x in words if len(x) > 3):
            return kind
    return None


def _kind(word: str, isin: str | None, quantity: float | None, amount: float) -> str:
    known = _kind_word(word)
    if known:
        return known
    if isin and quantity:
        return "sell" if (quantity < 0 or (quantity > 0 and amount > 0)) else "buy"
    if isin and amount > 0:
        return "dividend"
    if isin:
        return "other"
    return "deposit" if amount > 0 else "withdrawal"


# ─── The importer the registry sees ──────────────────────────────────

class Mapped:
    """Quacks like a module in `importers.IMPORTERS`: SLUG, LABEL, parse."""

    def __init__(self, saved: dict):
        self.saved = saved
        self.SLUG = f"csv:{saved['id']}"
        self.LABEL = saved["name"]

    def parse(self, content, account_currency="EUR"):
        return parse_with(self.saved["mapping"], content, account_currency, self.saved["delimiter"])


def sniff(content: bytes | str):
    """A saved mapping whose header this file carries, or None."""
    if isinstance(content, bytes) and content.startswith(b"%PDF"):
        return None
    try:
        header, _, _ = read(content)
    except (csv.Error, UnicodeDecodeError):
        return None
    if not header:
        return None
    saved = find(header)
    return Mapped(saved) if saved else None


def is_csv(content: bytes | str) -> bool:
    """Something a mapping could be drawn for: text with a header of
    more than one column and at least one row under it."""
    if isinstance(content, bytes):
        if content.startswith(b"%PDF") or b"\x00" in content[:4096]:
            return False
    try:
        header, rows, _ = read(content)
    except (csv.Error, UnicodeDecodeError):
        return False
    return len(header) > 1 and bool(rows)
