"""Swissquote and Yuh — the account statement PDFs.

Switzerland is outside PSD2, so no aggregator reaches a Swiss account;
what Swissquote gives instead is paperwork, and it gives it in two
layouts:

  * the **Kontoauszug** — the monthly statement it emails, one PDF per
    account and month, with a section per currency:

        DATUM INFORMATION REFERENZ BELASTUNG GUTSCHRIFT VALUTA-DATUM SALDO
        05.02.2026
         Kauf
        SS SPDR MSCI All County World
        Anzahl: 30
        Preis: CHF 228.00
        …
        ISIN: IE00B44Z5B48
        1035799731 6’862.64 09.02.2026 37’994.14

    A row is a date on its own line, then the description over as many
    lines as it needs, then one line with the reference, the amount, the
    value date and the running balance. The amount is UNSIGNED; whether
    it was a debit or a credit is read off the balance, which is the one
    thing on the page that cannot lie about direction.

  * the **Transaktionsaufstellung** — the ad-hoc export from the web
    portal (a different layout since July 2026, same file name when
    saved). The reference comes before the description, amounts are
    signed and carry their currency, and an optional fee column can sit
    between the two:

        27.07.2026 1143867441 Einzahlung für Thomas Herbrig
        IBAN: FR76…
        2 CHF -1’428.00 CHF 27.07.2026 16’099.28 CHF

Yuh is Swissquote's app-only brand and its statements are the same
Kontoauszug with a different letterhead, so they come through here too.

A trade on the statement carries its quantity, price, fees, taxes and
ISIN, so holdings can be computed from statements alone; the per-trade
receipt (`swissquote_beleg_pdf.py`) exists for the month that has no
statement yet, and produces the same id, so importing both adds nothing
twice. The id is the bank's own reference, per currency: an automatic
currency exchange is one reference booked in two sections, and those
are two rows, not a duplicate. Dates can differ by a day or two between
the two layouts for the same reference, so the date is not in the id.

Encoding: the statements use a font pypdf cannot fully decode, and two
accented letters come out as other glyphs — é as Ø, è as Ł. Neither
glyph occurs legitimately in a Swiss statement, so both are put back.
"""

from __future__ import annotations

import hashlib
import re

from .base import ParsedTxn, ParseResult, find_isin, parse_date

SLUG = "swissquote_pdf"
CORPUS = "swissquote"
LABEL = "Swissquote / Yuh — Kontoauszug PDF"

_DATE = r"\d{2}\.\d{2}\.\d{4}"
_AMT = r"-?[\d’']*\d\.\d{2}"
_OLD_SECTION_RE = re.compile(r"^Kontoauszug in ([A-Z]{3})$")
_NEW_SECTION_RE = re.compile(r"^Transaktionsaufstellung in ([A-Z]{3})\b")
_DATE_LINE_RE = re.compile(rf"^({_DATE})$")
# The old layout's closing line of a row: [reference] amount valuta saldo.
# A single-line row ("Depotgebühren 6.67 31.03.2026 20’787.57", "Transfer
# 1148865375 6.90 04.08.2026 15’196.58") carries its description first.
_OLD_END_RE = re.compile(
    rf"^(?:(?P<head>[^\d].*?)\s+)?(?:(?P<ref>\d{{6,}})\s+)?(?P<amt>{_AMT})\s+(?P<valuta>{_DATE})\s+(?P<saldo>{_AMT})$")
# The new layout's: [fee CCY] ±amount CCY valuta saldo CCY.
_NEW_END_RE = re.compile(
    rf"(?:^|\s)(?:({_AMT}|\d+) ([A-Z]{{3}}) )?([+-]{_AMT}) ([A-Z]{{3}}) ({_DATE}) ({_AMT}) [A-Z]{{3}}$")
_NEW_START_RE = re.compile(rf"^({_DATE}) (\d{{6,}}) (.*)$")
_PERIOD_RE = re.compile(rf"({_DATE}) bis ({_DATE})")
_OLD_CLOSING_RE = re.compile(rf"^Saldo per ({_DATE}) ({_AMT}) ([A-Z]{{3}})$")

# Lines the page furniture repeats on every page, which can land in the
# middle of a row that straddles a page break.
_FURNITURE = (
    "Dokument erstellt am", "Vom ", "Herrn ", "Frau ", "IBAN :", "IBAN:",
    "Dieser Transaktionsbeleg", "Die vorliegende Benachrichtigung",
    "dir und Yuh", "Bescheid ohne Unterschrift", "Swissquote Bank",
    "Customer Care", "Seite ", "DATUM INFORMATION", "Die Bankdienstleistungen",
    "die von der Eidgen", "SE&O", "© ", "Alle", "Dieses gedruckte Dokument",
    "Unstimmigkeiten sind", "Haftung für", "Fehler zu korrigieren",
    " / ", "Datum Referenz Information", "Steuern Betrag Valuta-Datum",
)

_GLYPHS = str.maketrans({"Ø": "é", "Ł": "è", "’": "'"})


def matches(header: list[str], sample: str) -> bool:
    """Called with the extracted text."""
    return ("Swissquote" in sample or "Yuh" in sample) and any(
        _OLD_SECTION_RE.match(l) or _NEW_SECTION_RE.match(l) for l in _lines(sample))


def _lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def _num(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = raw.strip().replace("’", "").replace("'", "")
    try:
        return float(s)
    except ValueError:
        return None


def _clean(s: str) -> str:
    return " ".join(s.translate(_GLYPHS).split())


def _furniture(line: str) -> bool:
    s = line.strip()
    return any(s.startswith(f) for f in _FURNITURE) or s == "/ 3" or re.match(r"^/ \d+$", s) is not None


def _customer(lines: list[str]) -> str | None:
    """The 7-digit customer number: `Kunde 3163201` on the old layout, a
    line of its own under `Kunde` on the new one, or dug out of the
    IBAN, whose account part is the customer number with `00` appended."""
    for line in lines:
        m = re.match(r"^Kunde(?:nnummer)?\s+(\d{7})\b", line.strip())
        if m:
            return m.group(1)
    for line in lines:
        if re.match(r"^\d{7}$", line.strip()):
            return line.strip()
    for line in lines:
        m = re.search(r"IBAN\s*:?\s*(CH[\d ]{19,})", line)
        if m:
            digits = re.sub(r"\D", "", m.group(1))
            if len(digits) == 19:
                return digits[10:17]
    return None


def _stable_id(customer, reference, currency, *fallback) -> str:
    if reference:
        return f"sq:{customer or '?'}:{reference}:{currency}"
    seed = "|".join(str(p) for p in (customer, currency, *fallback))
    return f"sq:{hashlib.sha1(seed.encode()).hexdigest()[:20]}"


# ─── Classification, shared by both layouts ──────────────────────────

def _classify(head: str, body: list[str], amount: float) -> tuple[str, str | None, dict]:
    """(kind, counterparty, trade fields) from a row's description.

    Structural where it can be — a buy has a quantity and a price, a
    dividend a `Total` — and by the row's own heading otherwise. The
    sign is never inferred here: the caller has it from the balance or
    the printed sign.
    """
    h = head.lower()
    extra: dict = {}
    party = None

    if h.startswith(("kauf", "verkauf")) or any(l.startswith("Anzahl:") for l in body) \
            and any(l.startswith("Preis:") for l in body):
        fields = _fields(body)
        name = _clean(body[0]) if body and ":" not in body[0] else None
        # The name is followed by its ticker in brackets; keep the name.
        if name:
            name = re.sub(r"\s*\([A-Z0-9.]+\)$", "", name)
        qty = _num(fields.get("Anzahl"))
        sell = h.startswith("verkauf") or amount > 0
        extra = {
            "isin": find_isin(fields.get("ISIN")) or find_isin(" ".join(body)),
            "security_name": name,
            "quantity": (-abs(qty) if sell else abs(qty)) if qty else None,
            "price": _money(fields.get("Preis")),
            "fee": _money(fields.get("Kommission")) or None,
            "tax": _money(fields.get("Taxen")) or None,
        }
        return ("sell" if sell else "buy"), None, extra

    if h.startswith("dividende") or h.startswith("ausschüttung"):
        fields = _fields(body)
        name = _clean(body[0]) if body and ":" not in body[0] else None
        if name:
            name = re.sub(r"\s*\([A-Z0-9.]+\)$", "", name)
        extra = {"isin": find_isin(" ".join(body)), "security_name": name,
                 "tax": _money(fields.get("Taxen")) or None}
        return "dividend", None, extra

    if "zins" in h or "interest" in h:
        return "interest", None, extra
    if "gebühr" in h or "gebuhr" in h or "fee" in h or "kommission" in h:
        return "fee", None, extra
    if "steuer" in h and "gebühr" not in h:
        return "tax", None, extra
    if "währungstausch" in h or "an eur" in h or "an chf" in h or "an usd" in h \
            or h.startswith("automatisierte überweisung") or h == "transfer":
        return "transfer", None, extra

    if h.startswith("zahlung per debitkarte") or h.startswith("kartenzahlung"):
        # Old: "xxxx 5861 -" then the merchant; new: the merchant is next.
        merchant = next((l for l in body if not l.lower().startswith("xxxx")), None)
        return "withdrawal", _clean(merchant) if merchant else None, extra

    if h.startswith("einzahlung für"):
        return "withdrawal", _clean(head[len("Einzahlung für"):]) or None, extra
    if h.startswith("zahlung an"):
        return "withdrawal", _clean(body[0]) if body else None, extra
    if h.startswith("zahlung von") or h.startswith("eingehende zahlung"):
        return "deposit", _clean(body[0]) if body else None, extra

    return ("deposit" if amount > 0 else "withdrawal"), None, extra


def _fields(body: list[str]) -> dict[str, str]:
    """`Anzahl: 30` / `Preis: CHF 228.00` lines as a dict."""
    out = {}
    for line in body:
        m = re.match(r"^([A-Za-zäöü]+):\s*(.+)$", line.strip())
        if m:
            out.setdefault(m.group(1), m.group(2).strip())
    return out


def _money(raw: str | None) -> float | None:
    """`CHF 228.00` → 228.0."""
    if not raw:
        return None
    m = re.search(rf"({_AMT})", raw.replace("’", ""))
    return _num(m.group(1)) if m else None


# ─── The two layouts ─────────────────────────────────────────────────

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

    lines = _lines(text)
    customer = _customer(lines)
    period = next((m for m in map(_PERIOD_RE.search, lines) if m), None)
    period_end = parse_date(period.group(2)) if period else None
    is_new = any(_NEW_SECTION_RE.match(l) for l in lines)

    if not any(_OLD_SECTION_RE.match(l) or _NEW_SECTION_RE.match(l) for l in lines):
        result.problems.append(
            "This is not a Swissquote or Yuh account statement — no "
            "'Kontoauszug in …' or 'Transaktionsaufstellung in …' section found.")
        return result

    closings: dict[str, tuple[str, float]] = {}
    (_parse_new if is_new else _parse_old)(lines, customer, result, closings)

    wanted = (account_currency or "CHF").upper()[:3]
    pick = closings.get(wanted) or (next(iter(closings.values())) if closings else None)
    if pick:
        as_of, amount = pick
        ccy = wanted if wanted in closings else next(iter(closings))
        result.closing_balance = {"amount": amount, "currency": ccy,
                                  "as_of": as_of or period_end}
    return result


def _parse_old(lines, customer, result, closings) -> None:
    currency = None
    section: list[str] = []

    def flush():
        if currency and section:
            _old_rows(section, currency, customer, result)

    for line in lines:
        m = _OLD_SECTION_RE.match(line.strip())
        if m:
            flush()
            currency, section = m.group(1), []
            continue
        if currency is None:
            continue
        if line.strip().startswith("Vertriebsentsch"):
            flush()
            currency, section = None, []
            continue
        c = _OLD_CLOSING_RE.match(line.strip())
        if c:
            # Two of these per section: the opening and the closing
            # balance. The later date wins.
            when = parse_date(c.group(1))
            if currency not in closings or when >= closings[currency][0]:
                closings[currency] = (when, _num(c.group(2)))
            continue
        if _furniture(line):
            continue
        section.append(line)
    flush()


def _old_rows(section, currency, customer, result) -> None:
    balance: float | None = None
    i = 0
    while i < len(section):
        line = section[i].strip()
        m = re.match(rf"^Anfangsbestand ({_AMT})$", line)
        if m:
            balance = _num(m.group(1))
            i += 1
            continue
        if line.startswith("Schlussbilanz"):
            i += 1
            continue
        d = _DATE_LINE_RE.match(line)
        if not d:
            i += 1
            continue
        date = parse_date(d.group(1))
        # Collect the body up to the closing line. A single-line row
        # ("Transfer 1148… 6.90 04.08.2026 15’196.58", "Depotgebühren
        # 6.67 31.03.2026 20’787.57") has the description and the
        # closing figures on one line.
        body: list[str] = []
        end = None
        j = i + 1
        while j < len(section):
            s = section[j].strip()
            if _DATE_LINE_RE.match(s):
                break
            m = re.match(rf"^(Anfangsbestand|Schlussbilanz) ({_AMT})$", s)
            if m:
                # The opening and closing lines sit under a date of
                # their own; they are balances, not movements.
                if m.group(1) == "Anfangsbestand":
                    balance = _num(m.group(2))
                j += 1
                break
            e = _OLD_END_RE.match(s)
            if e:
                if e.group("head"):
                    body.append(e.group("head").strip())
                end = e
                j += 1
                break
            body.append(s)
            j += 1
        i = j
        if end is None:
            if body:
                result.problems.append(
                    f"{date}: row without an amount line, skipped ({body[0][:40]})")
            continue
        reference, amt, saldo = end.group("ref"), _num(end.group("amt")), \
            _num(end.group("saldo"))
        if amt is None or saldo is None:
            result.problems.append(f"{date}: unreadable amounts, skipped")
            continue
        # Direction from the running balance. When the balance does not
        # move by the amount (it should always), fall back to the words.
        if balance is not None and abs(abs(saldo - balance) - amt) < 0.011:
            signed = saldo - balance
        else:
            head_l = (body[0].lower() if body else "")
            credit = head_l.startswith(("zahlung von", "dividende", "verkauf",
                                        "eingehende", "zins"))
            signed = amt if credit else -amt
        balance = saldo
        head = body[0] if body else ""
        rest = body[1:]
        kind, party, extra = _classify(head, rest, signed)
        description = _clean(" ".join([head] + [l for l in rest if not l.startswith(
            ("Anzahl:", "Preis:", "Betrag:", "Kommission:", "Taxen:", "Handelsplatz:",
             "ISIN:", "Total:", "xxxx"))]))[:500]
        result.rows.append(ParsedTxn(
            txn_date=date, description=description or head, amount=round(signed, 2),
            currency=currency, kind=kind,
            external_id=_stable_id(customer, reference, currency, date, f"{signed:.2f}",
                                   description),
            counterparty=party, **extra))


def _parse_new(lines, customer, result, closings) -> None:
    currency = None
    rows: list[str] = []
    open_row: list[str] | None = None
    period_end = None

    def close(row_lines: list[str]):
        first = row_lines[0]
        start = _NEW_START_RE.match(first)
        # The closing figures are on the LAST line — matched there and
        # not on the joined row, because a currency exchange carries
        # "Betrag: 56.42 EUR" in its body, which would otherwise read as
        # the optional fee column.
        end = _NEW_END_RE.search(row_lines[-1])
        if not start or not end:
            result.problems.append(f"{first[:60]!r}: unreadable row, skipped")
            return
        date = parse_date(start.group(1))
        reference = start.group(2)
        # The description is the rest of the first line; further lines
        # are the counterparty details.
        head = start.group(3).strip()
        if _NEW_END_RE.search(head):
            head = head[:_NEW_END_RE.search(head).start()].strip()
        rest = [l.strip() for l in row_lines[1:]]
        if rest:
            last = rest[-1]
            e = _NEW_END_RE.search(last)
            if e:
                rest[-1] = last[:e.start()].strip()
            rest = [l for l in rest if l]
        fee = _num(end.group(1)) if end.group(1) else None
        signed = _num(end.group(3))
        ccy = end.group(4)
        kind, party, extra = _classify(head, rest, signed or 0.0)
        if fee and "fee" not in extra:
            extra["fee"] = fee
        description = _clean(" ".join([head] + [l for l in rest if not l.startswith(
            ("IBAN:", "BIC/SWIFT:", "Referenz:", "Kontonummer:", "Wechselkurs:",
             "Betrag:"))]))[:500]
        result.rows.append(ParsedTxn(
            txn_date=date, description=description or head, amount=round(signed, 2),
            currency=ccy, kind=kind,
            external_id=_stable_id(customer, reference, ccy),
            counterparty=party, **extra))

    for line in lines:
        m = _NEW_SECTION_RE.match(line.strip())
        if m:
            if open_row:
                close(open_row)
            currency, open_row = m.group(1), None
            continue
        if currency is None:
            continue
        s = line.strip()
        if s.startswith("Vertriebsentsch"):
            if open_row:
                close(open_row)
            currency, open_row = None, None
            continue
        if _furniture(s):
            continue
        b = re.match(rf"^Endsaldo$", s)
        if b:
            continue
        e = re.match(rf"^({_AMT}) ([A-Z]{{3}})$", s)
        if e and open_row is None:
            # The summary figures above the table: Anfangssaldo,
            # Einzahlung, Auszahlung, Endsaldo — the last one is the
            # closing balance, and the period end is its date.
            closings[currency] = (period_end, _num(e.group(1)))
            continue
        if _NEW_START_RE.match(s):
            if open_row:
                close(open_row)
            open_row = [s]
            if _NEW_END_RE.search(s):
                close(open_row)
                open_row = None
            continue
        if open_row is not None:
            open_row.append(s)
            if _NEW_END_RE.search(s):
                close(open_row)
                open_row = None
    if open_row:
        close(open_row)
    # The period is in the section header line; stamp it on every closing.
    for line in lines:
        p = _PERIOD_RE.search(line)
        if p:
            period_end = parse_date(p.group(2))
            break
    for ccy, (_, amount) in list(closings.items()):
        closings[ccy] = (period_end, amount)
