"""MT940 — the SWIFT customer statement (".sta", ".mt940", ".940"), the
export of the older banking portals and of most business banking:
Sparkassen, Volksbanken, the Swiss banks, HBCI/FinTS tools.

One file holds one or more statements, each a run of tagged fields:
`:20:` reference, `:25:` account, `:28C:` statement number, `:60F:`
opening balance, then per booking a `:61:` line — value date, an
optional booking month-day, C/D (or RC/RD for a reversal), the
amount with a comma decimal, a transaction type, the customer
reference and after `//` the bank's — and a `:86:` line with the
details. German banks structure `:86:` with `?` fields: `?00` the
booking text, `?20`–`?29` the purpose, `?30` BIC, `?31` IBAN, `?32`
and `?33` the counterparty's name, `?34` the GVC code; SEPA purposes
carry `EREF+`, `MREF+`, `SVWZ+` markers inside. `:62F:` closes.
"""

from __future__ import annotations

import re
from datetime import datetime

from .base import ParsedTxn, ParseResult
from .formats import decode, kind_of, row_id

SLUG = "mt940"
LABEL = "MT940 — SWIFT Kontoauszug (.sta)"

_TAG = re.compile(r"^:(\d{2}[A-Z]?):", re.M)
_61 = re.compile(
    r"^(?P<vdate>\d{6})(?P<bdate>\d{4})?(?P<sign>RC|RD|C|D)(?P<fund>[A-Z])?(?P<amount>[\d,]+)"
    r"(?P<type>[NFS][A-Z0-9]{3})(?P<ref>.*?)(?://(?P<bankref>[^\n]*))?$", re.S)
_SEPA = re.compile(r"(EREF|MREF|CRED|DEBT|SVWZ|ABWA|ABWE|KREF|BREF|RREF|COAM|OAMT|IBAN|BIC|PURP)\+")


def matches(header: list[str], sample: str) -> bool:
    return bool(re.search(r"^:20:", sample, re.M) and re.search(r"^:61:", sample, re.M))


def _blocks(text: str) -> list[list[tuple[str, str]]]:
    """The file as statements, each a list of (tag, value) in order."""
    # A SWIFT envelope ({1:...}{4: ... -}) around the fields is stripped.
    text = re.sub(r"^\{[^{}]*\}", "", text.strip(), flags=re.M)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    fields: list[tuple[str, str]] = []
    pos = [(m.start(), m.end(), m.group(1)) for m in _TAG.finditer(text)]
    for i, (start, end, tag) in enumerate(pos):
        stop = pos[i + 1][0] if i + 1 < len(pos) else len(text)
        value = text[end:stop].strip("\n")
        value = re.sub(r"\n-\s*$", "", value)          # the block's closing dash
        fields.append((tag, value))
    blocks: list[list[tuple[str, str]]] = []
    for tag, value in fields:
        if tag == "20" or not blocks:
            blocks.append([])
        blocks[-1].append((tag, value))
    return blocks


def _date(yymmdd: str, bdate: str | None = None) -> tuple[str | None, str | None]:
    """(value date, booking date) — the booking date carries only month
    and day, and belongs to the value date's year unless that wraps."""
    try:
        v = datetime.strptime(yymmdd, "%y%m%d").date()
    except ValueError:
        return None, None
    if not bdate:
        return v.isoformat(), None
    year = v.year
    try:
        b = datetime.strptime(f"{year}{bdate}", "%Y%m%d").date()
    except ValueError:
        return v.isoformat(), None
    if (b - v).days > 180:        # a December booking for a January value date
        b = b.replace(year=year - 1)
    elif (v - b).days > 180:
        b = b.replace(year=year + 1)
    return v.isoformat(), b.isoformat()


def _balance(value: str) -> tuple[float | None, str, str | None]:
    """A :60F:/:62F: — C/D, YYMMDD, currency, amount."""
    m = re.match(r"^(C|D)(\d{6})([A-Z]{3})([\d,]+)", value.strip())
    if not m:
        return None, "", None
    amount = float(m.group(4).replace(",", "."))
    d, _ = _date(m.group(2))
    return (amount if m.group(1) == "C" else -amount), m.group(3), d


def _details(raw: str) -> dict:
    """The :86: line, structured or not."""
    text = " ".join(raw.split())
    out = {"booking_text": "", "purpose": "", "name": "", "iban": "", "gvc": "", "e2e": "", "mandate": "", "text": text}
    if "?" not in text:
        out["purpose"] = text
    else:
        head, *parts = re.split(r"\?(\d{2})", text)
        out["gvc"] = head.strip()[:3] if head.strip().isdigit() else ""
        fields: dict[str, str] = {}
        for i in range(0, len(parts) - 1, 2):
            fields[parts[i]] = fields.get(parts[i], "") + parts[i + 1]
        out["booking_text"] = fields.get("00", "").strip()
        out["purpose"] = "".join(fields.get(f"{n}", "") for n in range(20, 30)).strip()
        out["name"] = " ".join((fields.get("32", "") + " " + fields.get("33", "")).split())
        out["iban"] = fields.get("31", "").strip()
        out["gvc"] = out["gvc"] or fields.get("34", "").strip()
    # SEPA markers inside the purpose: the purpose proper is SVWZ+, the
    # rest are references worth keeping for the id.
    if _SEPA.search(out["purpose"]):
        pieces = _SEPA.split(out["purpose"])
        marked = {pieces[i]: pieces[i + 1].strip() for i in range(1, len(pieces) - 1, 2)}
        out["e2e"] = marked.get("EREF", "")
        out["mandate"] = marked.get("MREF", "")
        out["purpose"] = marked.get("SVWZ") or out["purpose"]
        if not out["name"] and marked.get("ABWA"):
            out["name"] = marked["ABWA"]
    return out


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    result = ParseResult()
    text = decode(content)
    blocks = _blocks(text)
    if not any(tag == "61" for b in blocks for tag, _ in b):
        result.problems.append("No :61: booking lines — not an MT940 statement.")
        return result
    counts: dict[str, int] = {}
    for block in blocks:
        account = next((v.strip() for t, v in block if t == "25"), "")
        currency = ""
        for t, v in block:
            if t in ("60F", "60M"):
                _, currency, _ = _balance(v)
            if t in ("62F", "62M"):
                amount, ccy, as_of = _balance(v)
                if amount is not None:
                    result.closing_balance = {"amount": amount, "currency": ccy, "as_of": as_of}
                    currency = currency or ccy
        currency = currency or account_currency.upper()[:3]

        pending = None
        for tag, value in block:
            if tag == "61":
                if pending is not None:
                    _emit(result, pending, {}, account, currency, counts)
                pending = value
            elif tag == "86" and pending is not None:
                _emit(result, pending, _details(value), account, currency, counts)
                pending = None
        if pending is not None:
            _emit(result, pending, {}, account, currency, counts)
    return result


def _emit(result: ParseResult, line61: str, d: dict, account: str, currency: str, counts: dict) -> None:
    first, _, extra = line61.partition("\n")
    m = _61.match(first.strip())
    if not m:
        result.problems.append(f"a :61: line could not be read: {first.strip()[:60]}")
        return
    value_date, booking_date = _date(m.group("vdate"), m.group("bdate"))
    if not value_date:
        result.problems.append(f"a :61: line has no readable date: {first.strip()[:60]}")
        return
    amount = float(m.group("amount").replace(",", "."))
    sign = m.group("sign")
    if sign in ("D", "RC"):
        amount = -amount
    d = d or {"booking_text": "", "purpose": "", "name": "", "iban": "", "gvc": "", "e2e": "", "mandate": "", "text": ""}
    purpose = d["purpose"] or " ".join(extra.split())
    description = purpose or d["booking_text"] or d["name"] or m.group("type")
    if d["booking_text"] and d["booking_text"].lower() not in description.lower():
        description = f"{description} [{d['booking_text']}]"
    blob = " ".join(x for x in (d["booking_text"], purpose, d["name"], m.group("type")) if x)
    kind = kind_of(blob, amount, m.group("type")[1:] if m.group("type") else None)
    bankref = (m.group("bankref") or "").strip()
    seed = (account, booking_date or value_date, value_date, f"{amount:.2f}", currency, d["name"], d["iban"],
            purpose, d["e2e"], d["mandate"], bankref, (m.group("ref") or "").strip())
    counts[str(seed)] = counts.get(str(seed), 0) + 1
    result.rows.append(ParsedTxn(
        txn_date=booking_date or value_date,
        description=description[:500],
        amount=round(amount, 2),
        currency=currency,
        kind=kind,
        external_id=row_id("mt940", *seed, counts[str(seed)]),
        counterparty=d["name"] or None,
    ))
