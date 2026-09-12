"""Swissquote — the Transaktionsbeleg (Börsenabrechnung) of one trade.

The monthly statement carries every trade with its quantity and price,
but it arrives on the first of the next month. A trade executed on the
10th is invisible until then — and the holding is short by that trade
for up to a month. Swissquote emails a receipt the moment a trade
executes, and this reads it:

    TRANSAKTIONSBELEG
    Kunde: 3170565 - Invest Easy
    Unsere Referenz: 1152802345
    Börsentransaktion: Kauf
    Total CHF 1'013.30
    Börsengebühren CHF 0.07
    Zu Ihren Lasten CHF 1'013.37
    Titel Börse
    Ambitious Portfolio IndexIndex ISIN: CH1236310558
    Gemäss Ihrem Kaufauftrag vom 10.08.2026 haben wir …
    Anzahl Preis Betrag
    28 36.19 CHF 1'013.32

The row it produces has the same id as the statement's row for the
same trade — the bank's reference, per currency — so importing the
receipt now and the statement next month adds nothing twice. Money
out is `Zu Ihren Lasten`, money in `Zu Ihren Gunsten`, and the heading
decides only when neither is found.
"""

from __future__ import annotations

import re

from .base import ParsedTxn, ParseResult, find_isin, parse_date

SLUG = "swissquote_beleg_pdf"
LABEL = "Swissquote — Transaktionsbeleg PDF"

_AMT = r"-?[\d']*\d(?:\.\d+)?"
_DATE = r"\d{2}\.\d{2}\.\d{4}"
_FEE_RE = re.compile(
    rf"^(Kommission\b.*?|Börsengebühren|Abgabe \(Eidg\. Stempelsteuer\)|Stempelsteuer|"
    rf"Fremde Gebühren|Fremde Spesen|Courtage.*?) ([A-Z]{{3}}) ({_AMT})$")


def matches(header: list[str], sample: str) -> bool:
    return "TRANSAKTIONSBELEG" in sample and "Swissquote" in sample \
        and "Börsentransaktion" in sample


def _num(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw.replace("'", "").replace("’", ""))
    except ValueError:
        return None


def _first(lines, pattern, group=1):
    rx = re.compile(pattern)
    for line in lines:
        m = rx.search(line)
        if m:
            return m.group(group)
    return None


def parse(content: bytes | str, account_currency: str = "CHF") -> ParseResult:
    result = ParseResult()
    if isinstance(content, bytes):
        if not content.startswith(b"%PDF"):
            result.problems.append("This is not a PDF.")
            return result
        from .dkb_pdf import pdf_text
        try:
            text = pdf_text(content)
        except Exception as exc:                     # noqa: BLE001
            result.problems.append(f"The PDF could not be read: {exc}")
            return result
    else:
        text = content

    lines = [" ".join(l.split()) for l in text.splitlines() if l.strip()]
    if not matches([], "\n".join(lines)):
        result.problems.append("This is not a Swissquote Transaktionsbeleg.")
        return result

    heading = (_first(lines, r"^Börsentransaktion:\s*(\S+)") or "").lower()
    customer = _first(lines, r"^Kunde:\s*(\d{7})")
    reference = _first(lines, r"^Unsere Referenz:\s*(\d{6,})")
    date = parse_date(_first(lines, rf"auftrag vom ({_DATE})")
                      or _first(lines, rf"^Gland, ({_DATE})"))
    if not date:
        result.problems.append("No trade date found on the receipt.")
        return result

    # The cash that moved, and its direction.
    m = next((m for m in (re.match(rf"^Zu Ihren (Lasten|Gunsten) ([A-Z]{{3}}) ({_AMT})$", l)
                          for l in lines) if m), None)
    if not m:
        result.problems.append("No 'Zu Ihren Lasten/Gunsten' amount found on the receipt.")
        return result
    direction = -1 if m.group(1) == "Lasten" else 1
    currency, cash = m.group(2), _num(m.group(3))
    is_sell = heading.startswith("verkauf") if heading else direction > 0

    # The security: the line carrying the ISIN, minus the ISIN.
    isin_line = next((l for l in lines if "ISIN:" in l), "")
    isin = find_isin(isin_line)
    name = re.sub(r"\s*ISIN:.*$", "", isin_line).strip() or None
    if name and name.endswith("Index"):
        # "Ambitious Portfolio IndexIndex" — the column header glued on.
        name = re.sub(r"Index$", "", name) if name.count("Index") > 1 else name

    # Quantity and price: the line under "Anzahl Preis Betrag".
    qty = price = None
    try:
        at = lines.index("Anzahl Preis Betrag")
        q = re.match(rf"^({_AMT}) ({_AMT}) ([A-Z]{{3}}) ({_AMT})$", lines[at + 1])
        if q:
            qty, price = _num(q.group(1)), _num(q.group(2))
    except (ValueError, IndexError):
        pass

    fees = 0.0
    for line in lines:
        f = _FEE_RE.match(line)
        if f:
            fees += _num(f.group(3)) or 0.0

    result.rows.append(ParsedTxn(
        txn_date=date,
        description=f"{'Verkauf' if is_sell else 'Kauf'} {name or isin or ''}".strip()[:500],
        amount=round(abs(cash or 0.0) * direction, 2),
        currency=currency,
        kind="sell" if is_sell else "buy",
        external_id=f"sq:{customer or '?'}:{reference}:{currency}" if reference
        else f"sq:{customer or '?'}:{date}:{isin}:{cash}",
        isin=isin,
        security_name=name,
        quantity=(-abs(qty) if is_sell else abs(qty)) if qty else None,
        price=price,
        fee=round(fees, 2) or None,
    ))
    return result
