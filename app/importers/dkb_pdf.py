"""DKB — the Wertpapierabrechnung PDFs of a Depot.

DKB's broker export is a cash ledger: it says what money left the
account, not how many units were bought or at what price. The
documents in the Postfach say exactly that. Every order, every
dividend and every Vorabpauschale produces one PDF, and this module
reads them — several at once, since there is one per event.

Where to get them: Postfach → filter by the Depot → download. A
statement is one of these, recognised by its heading:

    Wertpapier Abrechnung Kauf / Verkauf            an order, executed
    Wertpapier Abrechnung Ausgabe Investmentfonds   a fund purchase (also
                                                    each savings-plan run)
    Wertpapier Abrechnung Rücknahme Investmentfonds a fund sale
    Gesamtkündigung / Einlösung bei Gesamtfälligkeit a bond paid back
    Dividendengutschrift / Ausschüttung / Zinsgutschrift / Gutschrift …
    Vorabpauschale Investmentfonds                  the January fund tax
    Halbjahresabrechnung Sparplan                   six months of a
                                                    savings plan, one line
                                                    per purchase
    Depotbuchung - Belastung / Gutschrift           units moved out / in
    Storno zur Wertpapier Abrechnung                a cancellation — the
                                                    original is wrong,
                                                    and this one is not
                                                    a trade either

The text anchors follow Portfolio Performance's DKB extractor, whose
test corpus — the extracted text of some sixty anonymised real
statements, 2014 to 2025 — is what this module was written against.

Three things worth knowing.

**Quantity is a count or a nominal.** A share line reads `Stück 200 …`;
a bond line reads `EUR 2.000,00 …` and its price is a percentage. A
bond is kept as nominal ÷ 100 units, so that a per-cent quote times the
quantity is its value — Portfolio Performance's convention, and the one
a price feed needs. The price is worked out as Kurswert ÷ quantity,
which is right for both and in the account's own currency even when
the security traded in dollars.

**Money in or out is read off the sentence, not the number.** `Den
Gegenwert buchen wir … zu Lasten des Kontos` is money out; `zu Gunsten`
is money in. The `-`/`+` after the amount says the same thing and is
used when the sentence is missing, and the heading decides only when
both are.

**The id is the bank's own, plus what it identifies.** An order carries
an Auftragsnummer, a credit an Abrechnungsnr., a savings-plan line an
Ordernummer — and the savings-plan number is the same Auftragsnummer
the individual statement for that run carries, so importing both the
half-year overview and the single statements adds nothing twice. The
ISIN, date and amount go into the id as well, because one Abrechnungsnr.
was seen on two different credits for the same day.
"""

from __future__ import annotations

import hashlib
import io
import re

from .base import ParsedTxn, ParseResult, find_isin, parse_date

SLUG = "dkb_pdf"
CORPUS = "dkb"                  # the folder of Portfolio Performance's corpus this is scored on
LABEL = "DKB — Wertpapierabrechnung PDF"

_BANK_MARKS = ("10919 Berlin", "Deutsche Kreditbank", "BYLADEM1001")

_BUY_HEADINGS = ("Kauf", "Kauf Direkthandel", "Ausgabe", "Ausgabe Investmentfonds")
_SELL_HEADINGS = ("Verkauf", "Verkauf Direkthandel", "Verkauf aus Kapitalmaßnahme",
                  "Rücknahme Investmentfonds", "Gesamtkündigung",
                  "Teilrückzahlung mit Nennwertänderung",
                  "Teilliquidation mit Nennwertreduzierung",
                  "Einlösung bei Gesamtfälligkeit")
_TRADE_RE = re.compile(
    r"^(?:Wertpapier Abrechnung )?(" + "|".join(
        re.escape(h) for h in _BUY_HEADINGS + _SELL_HEADINGS) + r")$")
_INTEREST_HEADINGS = ("Zinsgutschrift",)
_DIVIDEND_HEADINGS = ("Dividendengutschrift", "Gutschrift von Investmenterträgen",
                      "Ausschüttung aus Genussschein", "Ausschüttung Investmentfonds",
                      "Ertragsgutschrift nach § 27 KStG", "Gutschrift",
                      "Erträgnisgutschrift aus Wertpapieren")
_SECURITY_HEADER = "Nominale Wertpapierbezeichnung ISIN (WKN)"
_SECURITY_RE = re.compile(
    r"^(Stück|[A-Z]{3}) ([\d.,]+) (.+?) ([A-Z]{2}[A-Z0-9]{9}\d) \([A-Z0-9]{6}\)$")
_SECURITY_NO_ISIN_RE = re.compile(r"^(Stück|[A-Z]{3}) ([\d.,]+) (.+)$")
_DATE = r"(\d{2}\.\d{2}\.\d{4})"
_AMOUNT_RE = re.compile(r"^Ausmachender Betrag ([\d.,]+)\s*([-+])? ([A-Z]{3})$")
_KURSWERT_RE = re.compile(r"^(?:Kurswert|Rückzahlungsbetrag) ([\d.,]+)\s*[-+]? ([A-Z]{3})$")
_PRICE_RE = re.compile(r"^(?:Ausführungskurs|Abrech\.-Preis) ([\d.,]+) ([A-Z]{3})\b")
_FEE_RE = re.compile(
    r"^(?:Provision|Transaktionsentgelt Börse|Übertragungs-/Liefergebühr|"
    r"Fremde Abwicklungsgebühr|Abwicklungskosten Börse|Maklercourtage|"
    r"Eigene Spesen|Fremde Spesen|Fremde Auslagen|Fremde Gebühren|Ausgabeaufschlag|"
    r"Börsengebühr|Handelsplatzgebühr|Clearstream-Gebühr|Variable Börsenspesen|"
    r"Umschreibeentgelt|Lieferentgelt|Fremdspesen)\b.*?([\d.,]+)\s*-? ([A-Z]{3})$")
_TAX_RE = re.compile(
    r"^(?:Kapitalertragsteuer|Solidaritätszuschlag|Kirchensteuer) [\d.,]+\s*%.*? "
    r"([\d.,]+)\s*([-+]) ([A-Z]{3})$")
_FLAT_TAX_RE = re.compile(
    r"^(?:Finanztransaktionssteuer|Einbehaltene Quellensteuer\b.*?) ([\d.,]+)\s*- ([A-Z]{3})$")
_SPARPLAN_ROW_RE = re.compile(
    r"^Kauf ([\d.,]+) (\S+) ([\d.,]+) [\d.,]+ ([\d.,]+) " + _DATE + " " + _DATE)
_SPARPLAN_FEE_RE = re.compile(r"^\+ Provision ([\d.,]+) Summe ([\d.,]+)$")


def matches(header: list[str], sample: str) -> bool:
    """Called with the extracted text, not with CSV cells."""
    return any(m in sample for m in _BANK_MARKS) and _document_kind(
        _lines(sample)) is not None


def pdf_text(content: bytes, layout: bool = False, ocr: bool = True) -> str:
    """The text of every page, in reading order, one line per printed
    line. pypdf is pure Python and the only dependency this needs.
    `layout` keeps the columns where they were printed, padded with
    blanks, for a statement whose meaning sits in the column.

    A scan carries no text. Where `ocrmypdf` is installed it is asked
    for one, once per file, and the readers see the result; where it
    is not, the empty string comes back and the caller says what kind
    of file this is — see importers/ocr.py."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:                       # pragma: no cover
        raise RuntimeError(
            "Reading PDFs needs the pypdf package: pip install pypdf") from exc

    def extract(raw: bytes) -> str:
        reader = PdfReader(io.BytesIO(raw))
        if layout:
            return "\n".join((page.extract_text(extraction_mode="layout") or "") for page in reader.pages)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    text = extract(content)
    if ocr:
        from . import ocr as _ocr
        if _ocr.looks_scanned(content, text) and _ocr.available():
            done = _ocr.text_layer(content)
            if done:
                text = extract(done)
    return text


def _num(raw: str | None) -> float | None:
    """A German number: `1.400,00` is fourteen hundred and `1.000` is a
    thousand — always. The shared parser reads a lone `1.000` as one
    point zero because it cannot know the locale; this module can."""
    if raw is None:
        return None
    s = raw.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _lines(text: str) -> list[str]:
    return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


def _document_kind(lines: list[str]) -> str | None:
    for line in lines:
        if line.startswith("Storno"):
            return "storno"
        if _TRADE_RE.match(line):
            return "trade"
        if line in _INTEREST_HEADINGS:
            return "interest"
        if line in _DIVIDEND_HEADINGS:
            return "dividend"
        if line.startswith("Vorabpauschale Investmentfonds"):
            return "vorabpauschale"
        if line.startswith("Halbjahresabrechnung Sparplan"):
            return "sparplan"
        if line.startswith("Depotbuchung - "):
            return "depotbuchung"
        if line.startswith("Kontoauszug Nummer"):
            return "kontoauszug"
    return None


def _first(lines: list[str], pattern: str, group: int = 1) -> str | None:
    rx = re.compile(pattern)
    for line in lines:
        m = rx.search(line)
        if m:
            return m.group(group)
    return None


def _security(lines: list[str]) -> tuple[float | None, str | None, str | None, bool]:
    """(quantity, isin, name, is_nominal) from the block under the
    Nominale header. The ISIN is normally on the same line as the
    name; on a few older credits it is on a line of its own below."""
    try:
        at = lines.index(_SECURITY_HEADER)
    except ValueError:
        return None, None, None, False
    block = lines[at + 1:at + 5]
    if not block:
        return None, None, None, False
    m = _SECURITY_RE.match(block[0])
    if m:
        notation, qty, name, isin = m.groups()
    else:
        m = _SECURITY_NO_ISIN_RE.match(block[0])
        if not m:
            return None, None, None, False
        notation, qty, name = m.groups()
        isin = next((find_isin(l) for l in block[1:] if find_isin(l)), None)
    # The second line continues the name ("INHABER-ANTEILE I O.N.") —
    # unless it is already the next field.
    if len(block) > 1 and not re.match(
            r"^(Börse|Handels|Schlusstag|Limit|Zahlbarkeitstag|Rückzahlung|"
            r"Girosammel|Wertpapierrechnung|Ausführung|[A-Z]{2}[A-Z0-9]{9}\d \()",
            block[1]):
        name = f"{name} {block[1]}"
    quantity = _num(qty)
    if notation != "Stück" and quantity is not None:
        # A bond is held by nominal and quoted in per cent. Kept as
        # nominal ÷ 100, so that quantity × a per-cent quote is its value
        # — the convention a price feed and Portfolio Performance share.
        quantity = quantity / 100
    return quantity, isin, " ".join(name.split()), notation != "Stück"


def _amount(lines: list[str]) -> tuple[float | None, str | None, str | None]:
    """(amount, its sign as printed, currency) of the Ausmachender Betrag."""
    for line in lines:
        m = _AMOUNT_RE.match(line)
        if m:
            return _num(m.group(1)), m.group(2), m.group(3)
    return None, None, None


def _direction(lines: list[str]) -> int | None:
    """-1 for money out, +1 for money in, from the booking sentence."""
    text = " ".join(lines)
    if "zu Lasten" in text:
        return -1
    if "zu Gunsten" in text:
        return +1
    return None


def _fees_and_taxes(lines: list[str]) -> tuple[float, float]:
    fees = taxes = 0.0
    for line in lines:
        m = _FEE_RE.match(line)
        if m:
            fees += abs(_num(m.group(1)) or 0)
            continue
        m = _TAX_RE.match(line)
        if m:
            value = _num(m.group(1)) or 0
            taxes += value if m.group(2) == "-" else -value
            continue
        m = _FLAT_TAX_RE.match(line)
        if m:
            taxes += abs(_num(m.group(1)) or 0)
    return round(fees, 2), round(taxes, 2)


def _stable_id(*parts) -> str:
    seed = "|".join(str(p) for p in parts)
    return f"dkb-pdf:{hashlib.sha1(seed.encode()).hexdigest()[:20]}"


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    result = ParseResult()
    if isinstance(content, bytes):
        if not content.startswith(b"%PDF"):
            result.problems.append("This is not a PDF.")
            return result
        try:
            text = pdf_text(content)
        except Exception as exc:                     # noqa: BLE001
            result.problems.append(f"The PDF could not be read: {exc}")
            return result
    else:
        text = content

    lines = _lines(text)
    kind = _document_kind(lines)
    currency = account_currency.upper()[:3]

    if kind is None:
        result.problems.append(
            "This is not a DKB securities statement — no Wertpapier "
            "Abrechnung, Dividendengutschrift, Vorabpauschale or Sparplan "
            "heading found.")
    elif kind == "storno":
        result.problems.append(
            "A Storno (cancellation) — not imported. If the original "
            "statement it cancels was imported, delete that transaction.")
    elif kind == "kontoauszug":
        result.problems.append(
            "A Kontoauszug is a bank statement; use the account's CSV "
            "export for those.")
    elif kind == "trade":
        _parse_trade(lines, currency, result)
    elif kind in ("dividend", "interest"):
        _parse_credit(lines, currency, result, kind)
    elif kind == "vorabpauschale":
        _parse_vorabpauschale(lines, currency, result)
    elif kind == "sparplan":
        _parse_sparplan(lines, currency, result)
    elif kind == "depotbuchung":
        _parse_depotbuchung(lines, currency, result)
    return result


def _parse_trade(lines, currency, result):
    heading = next(m.group(1) for m in map(_TRADE_RE.match, lines) if m)
    is_sell = heading in _SELL_HEADINGS
    quantity, isin, name, _ = _security(lines)
    amount, sign, ccy = _amount(lines)
    if amount is None:
        result.problems.append("No 'Ausmachender Betrag' found on the statement.")
        return
    direction = _direction(lines) or {"-": -1, "+": 1}.get(sign) or (1 if is_sell else -1)
    amount = abs(amount) * direction

    date = (_first(lines, r"^Schlusstag(?:/-Zeit)? " + _DATE)
            or _first(lines, r"buchen wir .*?Valuta " + _DATE)
            or _first(lines, r"^(?:Fälligkeitstag|Rückzahlungsdatum|Bestandsstichtag) " + _DATE)
            or _first(lines, r"\bDatum " + _DATE))
    date = parse_date(date)
    if not date:
        result.problems.append("No date found on the statement.")
        return

    kw = next((m for m in map(_KURSWERT_RE.match, lines) if m), None)
    kurswert = _num(kw.group(1)) if kw else None
    kurswert_ccy = kw.group(2) if kw else None
    price = None
    if kurswert and quantity:
        price = round(abs(kurswert) / quantity, 6)
    else:
        m = next((m for m in map(_PRICE_RE.match, lines) if m), None)
        if m and m.group(2) == (ccy or currency):
            price = _num(m.group(1))
    fees, taxes = _fees_and_taxes(lines)
    order = _first(lines, r"^(?:.* )?Auftragsnummer (\S+)")
    # The statement adds up: Kurswert plus every cost is the amount.
    # A cost line under a label this parser has never seen would
    # otherwise vanish — the amount would still be right, the fee
    # column not. So the arithmetic is checked, and what is left over
    # is counted as fee and named as such.
    if kurswert and kurswert_ccy == (ccy or currency):
        expected = abs(kurswert) + (fees + taxes) * (1 if not is_sell else -1)
        residual = round(abs(amount) - expected, 2)
        unnamed = residual if not is_sell else -residual
        if unnamed >= 0.01:
            fees = round(fees + unnamed, 2)
            result.problems.append(
                f"{date} {name or isin}: {unnamed:.2f} {ccy or currency} of costs on the "
                f"statement carry no label this importer knows; counted as fee.")

    result.rows.append(ParsedTxn(
        txn_date=date,
        description=f"{heading} {name or isin or ''}".strip()[:500],
        amount=amount,
        currency=(ccy or currency).upper()[:3],
        kind="sell" if is_sell else "buy",
        external_id=_stable_id("order", order, isin, date, f"{amount:.2f}") if order
        else _stable_id("trade", date, isin, f"{amount:.2f}"),
        isin=isin,
        security_name=name,
        quantity=(-abs(quantity) if is_sell else abs(quantity)) if quantity else None,
        price=price,
        fee=fees or None,
        tax=taxes or None,
    ))


def _parse_credit(lines, currency, result, kind):
    _, isin, name, _ = _security(lines)
    amount, sign, ccy = _amount(lines)
    if amount is None:
        result.skipped += 1                 # a credit that paid nothing out
        return
    date = parse_date(_first(lines, r"buchen wir mit Wertstellung " + _DATE)
                      or _first(lines, r"^Zahlbarkeitstag " + _DATE)
                      or _first(lines, r"\bDatum " + _DATE))
    if not date:
        result.problems.append("No date found on the statement.")
        return
    _, taxes = _fees_and_taxes(lines)
    heading = next(l for l in lines if l in _DIVIDEND_HEADINGS + _INTEREST_HEADINGS)
    ref = _first(lines, r"Abrechnungsnr\. (\d+)")
    result.rows.append(ParsedTxn(
        txn_date=date,
        description=f"{heading} {name or isin or ''}".strip()[:500],
        amount=abs(amount) * (_direction(lines) or {"-": -1}.get(sign, 1)),
        currency=(ccy or currency).upper()[:3],
        kind=kind,
        external_id=_stable_id("credit", ref, isin, date, f"{amount:.2f}") if ref
        else _stable_id("credit", date, isin, f"{amount:.2f}"),
        isin=isin,
        security_name=name,
        tax=taxes or None,
    ))


def _parse_vorabpauschale(lines, currency, result):
    _, isin, name, _ = _security(lines)
    amount, sign, ccy = _amount(lines)
    if amount is None or abs(amount) < 0.005:
        # Below the Sparer-Pauschbetrag: a statement, but no money moved.
        result.skipped += 1
        return
    date = parse_date(_first(lines, r"buchen wir mit Wertstellung " + _DATE)
                      or _first(lines, r"\bDatum " + _DATE))
    if not date:
        result.problems.append("No date found on the statement.")
        return
    ref = _first(lines, r"Abrechnungsnr\. (\d+)")
    result.rows.append(ParsedTxn(
        txn_date=date,
        description=f"Vorabpauschale {name or isin or ''}".strip()[:500],
        amount=-abs(amount),
        currency=(ccy or currency).upper()[:3],
        kind="tax",
        external_id=_stable_id("vorab", ref, isin, date, f"{amount:.2f}") if ref
        else _stable_id("vorab", date, isin, f"{amount:.2f}"),
        isin=isin,
        security_name=name,
        tax=abs(amount),
    ))


def _parse_sparplan(lines, currency, result):
    """One row per purchase line of the half-year overview.

        Kauf 90,00 531781/77.00 40,1900 1,0000 2,2394 05.07.2018 09.07.2018 0,00 0,00
        + Provision 0,49 Summe 200,49            (only when a fee was charged)
    """
    try:
        at = lines.index("Wertpapierbezeichnung ISIN (WKN)")
        isin = find_isin(lines[at + 1])
        name = re.sub(r"\s*[A-Z]{2}[A-Z0-9]{9}\d \([A-Z0-9]{6}\).*$", "", lines[at + 1])
        if at + 2 < len(lines) and not lines[at + 2].startswith("Im Rahmen"):
            name = f"{name} {lines[at + 2]}"
    except (ValueError, IndexError):
        isin, name = None, None
    ccy = _first(lines, r"^Im Abrechnungszeitraum angelegter Betrag ([A-Z]{3}) ") or currency

    for i, line in enumerate(lines):
        m = _SPARPLAN_ROW_RE.match(line)
        if not m:
            continue
        rate, order, price, shares, trade_date, _valuta = m.groups()
        amount = _num(rate) or 0.0
        fee = None
        if i + 1 < len(lines):
            f = _SPARPLAN_FEE_RE.match(lines[i + 1])
            if f:
                fee = _num(f.group(1))
                amount = _num(f.group(2)) or amount
        date = parse_date(trade_date)
        if not date:
            result.problems.append(f"unreadable date in {line[:60]!r}")
            continue
        result.rows.append(ParsedTxn(
            txn_date=date,
            description=f"Sparplan Kauf {name or isin or ''}".strip()[:500],
            amount=-abs(amount),
            currency=ccy.upper()[:3],
            kind="buy",
            external_id=_stable_id("order", order, isin, date, f"{-abs(amount):.2f}"),
            isin=isin,
            security_name=" ".join((name or "").split()) or None,
            quantity=_num(shares),
            price=_num(price),
            fee=fee,
        ))
    if not result.rows:
        result.problems.append("No purchase lines found in the Sparplan overview.")


def _parse_depotbuchung(lines, currency, result):
    """Units leaving or arriving without money moving: a transfer to
    another broker. Recorded as a transfer with the quantity signed,
    so the movement is visible even though no cash changed hands."""
    heading = next(l for l in lines if l.startswith("Depotbuchung - "))
    outgoing = "Belastung" in heading
    quantity, isin, name, _ = _security(lines)
    date = parse_date(_first(lines, r"^Valuta " + _DATE)
                      or _first(lines, r"^Schlusstag " + _DATE)
                      or _first(lines, r"\bDatum " + _DATE))
    if not date:
        result.problems.append("No date found on the statement.")
        return
    order = _first(lines, r"Auftrags(?:nummer|-Nr\.) (\S+)")
    result.rows.append(ParsedTxn(
        txn_date=date,
        description=f"{heading} {name or isin or ''}".strip()[:500],
        amount=0.0,
        currency=currency,
        kind="transfer",
        external_id=_stable_id("depot", order, isin, date) if order
        else _stable_id("depot", date, isin, quantity),
        isin=isin,
        security_name=name,
        quantity=(-abs(quantity) if outgoing else abs(quantity)) if quantity else None,
    ))
