"""Crédit Agricole next bank (Suisse) — the Buchungsliste CSV.

Export it in the e-banking: the account → Buchungen → export. One line
per booking, semicolon-separated, Latin-1 encoded, German-Swiss dates:

    Transaktionsdatum;Valutadatum;Auftragsnummer;Text;Belastungsbetrag (CHF);Gutschriftsbetrag (CHF);Saldo (CHF)
    24.08.2026;24.08.2026;236765220;Paiement en faveur de: Swissquote Bank SA;3700.00;;11.26

Three things make this one of the easier files.

**The Auftragsnummer is the bank's own id** — unique, stable, and
carried on every row — so re-importing an overlapping export is exactly
free and there is no hashing to get wrong.

**Debit and credit are two columns**, never both filled, in the
account's own currency, which the header names.

**Every row carries the running balance**, newest row first, so the
first row's balance is the account's balance as of that day.

Interest arrives as a row whose text is the period it covers
(`31.12.24-31.12.25`); the same shape on the debit side is the tax
withheld on it. Switzerland is outside PSD2, so this file is the only
way this account's history reaches the app.
"""

from __future__ import annotations

import csv
import io

from .base import ParsedTxn, ParseResult, parse_date, parse_decimal
from .dkb import _decode

SLUG = "ca_switzerland"
LABEL = "Crédit Agricole next bank (Suisse) — Buchungsliste CSV"

_HEADER_START = ("Transaktionsdatum", "Valutadatum", "Auftragsnummer", "Text")
_FEE_WORDS = ("fee", "gebühr", "frais", "spesen")
_INTEREST_WORDS = ("zins", "intérêt", "interet", "interest")


def matches(header: list[str], sample: str) -> bool:
    if header and header[0].lstrip("﻿").strip() == "Transaktionsdatum":
        return True
    first = sample.lstrip("﻿").split("\n", 1)[0]
    return first.startswith("Transaktionsdatum;Valutadatum;Auftragsnummer;Text")


def _period_text(text: str) -> bool:
    """`31.12.24-31.12.25`: the text of an interest or interest-tax row."""
    import re
    return re.match(r"^\d{2}\.\d{2}\.\d{2,4}\s*-\s*\d{2}\.\d{2}\.\d{2,4}$", text.strip()) is not None


def _kind(text: str, amount: float) -> tuple[str, str | None]:
    """(kind, counterparty) from the booking text."""
    t = text.strip()
    low = t.lower()
    if _period_text(t):
        return ("interest" if amount > 0 else "tax"), None
    if any(w in low for w in _INTEREST_WORDS):
        return "interest", None
    if any(w in low for w in _FEE_WORDS):
        # A refunded fee is still a fee row, with the sign the bank gave it.
        return "fee", None
    for prefix in ("Paiement en faveur de:", "Instant Payment in favour of:",
                   "Zahlung zugunsten:", "Payment in favour of:", "Zahlung an:"):
        if t.startswith(prefix):
            return "withdrawal", t[len(prefix):].strip() or None
    if amount > 0:
        # A credit's text is the sender, usually with their address.
        return "deposit", t.split(",")[0].strip() or None
    return "withdrawal", None


def parse(content: bytes | str, account_currency: str = "CHF") -> ParseResult:
    result = ParseResult()
    text = _decode(content)
    reader = csv.reader(io.StringIO(text), delimiter=";", quotechar='"')
    try:
        header = next(reader)
    except StopIteration:
        result.problems.append("The file is empty.")
        return result
    header = [h.lstrip("﻿").strip() for h in header]
    if tuple(header[:4]) != _HEADER_START:
        result.problems.append("This is not a Crédit Agricole (Suisse) Buchungsliste — "
                               "the columns are not the ones expected.")
        return result
    col = {name: i for i, name in enumerate(header)}
    debit_col = next((i for n, i in col.items() if n.startswith("Belastungsbetrag")), 4)
    credit_col = next((i for n, i in col.items() if n.startswith("Gutschriftsbetrag")), 5)
    saldo_col = next((i for n, i in col.items() if n.startswith("Saldo")), 6)
    # The currency is in the column names: "Belastungsbetrag (CHF)".
    import re
    m = re.search(r"\(([A-Z]{3})\)", header[debit_col])
    currency = m.group(1) if m else (account_currency or "CHF").upper()[:3]

    newest: tuple[str, float] | None = None
    for lineno, row in enumerate(reader, start=2):
        if not row or not any(cell.strip() for cell in row):
            continue
        if len(row) <= max(debit_col, credit_col):
            result.problems.append(f"line {lineno}: too few columns, skipped")
            continue
        date = parse_date(row[col.get("Transaktionsdatum", 0)])
        if not date:
            result.problems.append(f"line {lineno}: unreadable date {row[0]!r}, skipped")
            continue
        debit = parse_decimal(row[debit_col])
        credit = parse_decimal(row[credit_col])
        if debit is None and credit is None:
            result.skipped += 1
            continue
        amount = (credit or 0.0) - (debit or 0.0)
        if abs(amount) < 0.005:
            result.skipped += 1
            continue
        text_ = " ".join(row[col.get("Text", 3)].split())
        order = row[col.get("Auftragsnummer", 2)].strip()
        kind, party = _kind(text_, amount)
        result.rows.append(ParsedTxn(
            txn_date=date, description=text_[:500], amount=round(amount, 2),
            currency=currency, kind=kind,
            external_id=f"ca-ch:{order}" if order else f"ca-ch:{date}:{amount:.2f}:{text_[:40]}",
            counterparty=party))
        saldo = parse_decimal(row[saldo_col]) if len(row) > saldo_col else None
        if saldo is not None and (newest is None or date > newest[0]):
            newest = (date, saldo)
    if newest:
        result.closing_balance = {"amount": newest[1], "currency": currency,
                                  "as_of": newest[0]}
    return result
