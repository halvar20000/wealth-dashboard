"""One reader for every bank's statement PDF, driven by a spec per bank.

A securities statement is the same document everywhere: a heading that
says what happened (a purchase, a sale, a dividend, a tax), a security
with its ISIN, a number of units, a price, a date, the settlement
amount, and a handful of fee and tax lines. What differs per bank is
the wording and the layout — which is to say, the regular expressions.
So a bank is a *spec*: a few marks that identify its paper, and for
each kind of document a heading and the anchors for each field. This
module turns a spec into a reader with the same `SLUG`, `LABEL`,
`matches` and `parse` as the hand-written importers, and the import
page cannot tell the difference.

Specs live in `importers/pdf/`, one file per bank, and are scored
against Portfolio Performance's corpus of real statements with
`tools/statement_scoreboard.py` before a bank is listed as read.

How a spec is read, in order:

1. The text must contain one of the spec's `marks` — the bank's name,
   its BIC, its address line — or the reader passes.
2. The first `Doc` whose `when` is found in the text claims it — so a
   Vorabpauschale listed before a Dividendengutschrift wins over it —
   plus any later doc marked `also`, for a second transaction printed
   on the same paper. A `skip` doc (a Storno, a cancellation) wins
   outright and produces a problem rather than rows.
3. A doc without a `block` is one transaction from the whole text; with
   a `block`, the text is cut at every line matching it and each piece
   is one transaction — an account statement's rows.
4. Each field is a list of regexes tried in order against the piece
   (multi-line, so `\\n` may be used to reach the line after an anchor);
   the first that matches supplies its named groups. `fees` and
   `taxes` are different: every match of every regex is summed.

Named groups the engine understands:

    isin wkn name name2 shares notation price price_currency date time
    amount currency fee tax ref sign refund type gross fx_pair fx_rate year

`notation`: a bond's nominal ("EUR 2.000,00") becomes 20 units at a
per-cent price — anything not starting with "St" divides by 100. `sign`
on a fee or tax: a "+" or the word "Erstattung" makes it a refund; a
"-" is the charge itself, which is how most banks print it. `type` on a statement row: looked up in the doc's `kinds` to
decide deposit from withdrawal, interest from fee.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime

from .base import ParsedTxn, ParseResult, find_isin

MONTHS = {
    "januar": 1, "jan": 1, "january": 1, "janvier": 1, "janv": 1, "gennaio": 1, "gen": 1, "enero": 1, "ene": 1,
    "februar": 2, "feb": 2, "february": 2, "février": 2, "fevrier": 2, "févr": 2, "fevr": 2, "febbraio": 2, "febrero": 2,
    "märz": 3, "maerz": 3, "mär": 3, "mrz": 3, "mar": 3, "march": 3, "mars": 3, "marzo": 3,
    "april": 4, "apr": 4, "avril": 4, "avr": 4, "aprile": 4, "abril": 4, "abr": 4,
    "mai": 5, "may": 5, "maggio": 5, "mag": 5, "mayo": 5,
    "juni": 6, "jun": 6, "june": 6, "juin": 6, "giugno": 6, "giu": 6, "junio": 6,
    "juli": 7, "jul": 7, "july": 7, "juillet": 7, "juil": 7, "luglio": 7, "lug": 7, "julio": 7,
    "august": 8, "aug": 8, "août": 8, "aout": 8, "agosto": 8, "ago": 8,
    "september": 9, "sep": 9, "sept": 9, "septembre": 9, "settembre": 9, "set": 9, "septiembre": 9,
    "oktober": 10, "okt": 10, "oct": 10, "october": 10, "octobre": 10, "ottobre": 10, "ott": 10, "octubre": 10,
    "november": 11, "nov": 11, "novembre": 11, "noviembre": 11,
    "dezember": 12, "dez": 12, "dec": 12, "december": 12, "décembre": 12, "decembre": 12, "déc": 12, "dicembre": 12, "diciembre": 12, "dic": 12,
}


@dataclass
class Doc:
    kind: str                       # buy sell trade dividend interest tax fee deposit withdrawal transfer rows skip
    when: str                       # regex; found anywhere → this doc applies
    fields: dict = field(default_factory=dict)
    sell: str | None = None         # regex; found → a 'trade' is a sale
    transfer: str | None = None     # regex; found → a 'trade' is a delivery in or out
    block: str | None = None        # regex; each line matching starts a new transaction
    kinds: dict | None = None       # for `type`: regex → kind ("skip" leaves the row out)
    note: str | None = None         # what a `skip` says
    also: bool = False              # runs in addition to the doc that claimed the text
                                    # (a tax settlement printed under a sale)
    merge: bool = False             # an `also` doc whose taxes and after-tax amount go
                                    # onto the primary row instead of making a row
    split: bool = False             # an `also` row that was part of the primary's booked
                                    # total (a tax credit under a sale): taken out of it


@dataclass
class Spec:
    slug: str
    label: str
    corpus: str                     # the Portfolio Performance corpus folder, for the scoreboard
    marks: list
    docs: list
    number: str = "de"              # de 1.234,56 · en 1,234.56 · ch 1'234.56 · auto (per document)
    preprocess: object = None       # callable(text) -> text, for a bank's quirks


NUMBER_RE = r"[\d.,'’\s]+"


def parse_number(raw: str | None, style: str = "de") -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().replace("’", "'").replace(" ", "").replace("\u00a0", "")
    s = s.replace(",--", ",00").replace(".--", ".00")          # Austrian "-3,-- EUR"
    neg = s.endswith("-") or s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("+-() ")
    if not s:
        return None
    s = s.replace("'", "")                           # a Swiss thousands mark, whatever the style
    if style == "ch":
        s = s.replace(",", ".")
    elif style == "en":
        s = s.replace(",", "")
    elif style == "de":
        s = s.replace(".", "").replace(",", ".")
    else:                                            # auto: the last separator is the decimal one
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_date(raw: str | None) -> str | None:
    if not raw:
        return None
    s = " ".join(str(raw).replace(",", " ").split()).strip(". ")
    s = re.sub(r"^(\d{1,2})-([A-Za-zÀ-ÿ]+)-(\d{4})$", r"\1 \2 \3", s)        # 05-Dez-2024
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.match(r"^(\d{1,2})\.?\s+([A-Za-zÀ-ÿ]+)\.?\s+(\d{4})$", s)
    if m and m.group(2).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.match(r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return None


def _first(text: str, patterns, flags=re.M) -> dict:
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return {k: v for k, v in m.groupdict().items() if v is not None}
    return {}


def _fx(text: str, patterns, style: str) -> tuple[str | None, str | None, float | None]:
    """(base, quote, rate) from a "Devisenkurs EUR/USD 1,2502" line: one
    base buys `rate` quote."""
    g = _first(text, patterns)
    rate = parse_number(g.get("fx_rate"), style)
    pair = (g.get("fx_pair") or "").upper().replace(" ", "")
    if rate and "/" in pair:
        a, b = pair.split("/", 1)
        return a, b, rate
    return None, None, None


def _sum(text: str, patterns, group: str, style: str, currency: str | None = None,
         fx: tuple = (None, None, None)) -> tuple[float, bool]:
    """Every match of every pattern, summed; a refund counts negative.
    A line in another currency is turned into the settlement currency
    with the document's own rate, or left out when there is none —
    dollars must not be added to euros."""
    total, seen = 0.0, False
    counted: set[str] = set()
    for p in patterns:
        for m in re.finditer(p, text, re.M):
            # A second page that repeats the first page's lines is not a
            # second charge: an identical line counts once.
            if m.group(0) in counted:
                continue
            counted.add(m.group(0))
            v = parse_number(m.group(group), style) if group in m.groupdict() and m.group(group) else None
            if v is None:
                continue
            ccy = (m.groupdict().get("currency") or "").upper()
            if currency and ccy and ccy != currency:
                base, quote, rate = fx
                if rate and ccy == quote and base == currency:
                    v = v / rate
                elif rate and ccy == base and quote == currency:
                    v = v * rate
                else:
                    continue
            # A fee or tax line is a charge unless it says otherwise: a
            # "+" or a word like Erstattung makes it a refund. A "-" is
            # how most banks mark the charge itself. A spec whose bank
            # prints charges with a minus and credits bare names the
            # bare case with a `refund` group instead.
            sign = (m.groupdict().get("sign") or "").strip()
            refund = m.groupdict().get("refund") is not None
            if refund or sign == "+" or "rstatt" in sign.lower() or "refund" in sign.lower():
                v = -abs(v)
            else:
                v = abs(v)
            total += v
            seen = True
    return round(total, 4), seen


def detect_style(text: str) -> str:
    """Which way this document writes its decimals — for a bank that
    prints German paper for one customer and English for the next."""
    t = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", " ", text)       # dotted dates are not decimals
    t = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", t)
    t = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})*\b", " ", t)           # nor times
    de = len(re.findall(r"\d,\d{1,4}(?![\d.])", t))                # 1,04 · 0,118 — not 1,042.04
    en = len(re.findall(r"\d\.\d{1,4}(?![\d,])", t))               # 1.04 · 0.118 — not 1.042,04
    return "de" if de >= en else "en"


class Reader:
    """Quacks like an importer module: SLUG, LABEL, CORPUS, matches, parse."""

    def __init__(self, spec: Spec):
        self.spec = spec
        self.SLUG = spec.slug
        self.LABEL = spec.label
        self.CORPUS = spec.corpus
        self._marks = [re.compile(m, re.M) for m in spec.marks]
        self._docs = [(d, re.compile(d.when, re.M)) for d in spec.docs]

    # ── recognising ──
    def _text(self, content) -> str:
        if isinstance(content, bytes):
            from .dkb_pdf import pdf_text
            text = pdf_text(content)
        else:
            text = content
        text = "\n".join(" ".join(line.split()) for line in text.splitlines())
        return self.spec.preprocess(text) if self.spec.preprocess else text

    def matches(self, header, sample: str) -> bool:
        text = self._text(sample)
        if not any(m.search(text) for m in self._marks):
            return False
        return any(rx.search(text) for _, rx in self._docs)

    # ── reading ──
    def parse(self, content, account_currency: str = "EUR") -> ParseResult:
        result = ParseResult()
        text = self._text(content)
        if not any(m.search(text) for m in self._marks):
            result.problems.append(f"This is not a {self.LABEL}.")
            return result
        matching = [(d, rx) for d, rx in self._docs if rx.search(text)]
        if not matching:
            result.problems.append(f"{self.LABEL}: no heading this reader knows.")
            return result
        for d, rx in matching:
            if d.kind == "skip":
                result.problems.append(d.note or "A cancellation — not imported.")
                return result
        # The first doc whose heading fits AND whose anchors find a row
        # claims the text. Two families of paper can share a heading —
        # "Ertragsgutschrift" on DAB's old layout and on its new one —
        # and only the anchors tell them apart.
        seen_ids: set[str] = set()
        primary_rows: list[ParsedTxn] = []
        primary = None
        for d, rx in matching:
            if d.also:
                continue
            attempt = ParseResult()
            rows = []
            for piece in self._pieces(text, d):
                row = self._row(piece, d, rx, account_currency, attempt, text)
                if row and row.external_id not in seen_ids:
                    rows.append(row)
            if rows:
                primary = (d, rx)
                for row in rows:
                    seen_ids.add(row.external_id)
                    result.rows.append(row)
                    primary_rows.append(row)
                break
            if not result.problems:
                result.problems.extend(attempt.problems)
        if primary is not None:
            result.problems.clear()
        primary_kind = primary[0].kind if primary else None
        applicable = ([primary] if primary else []) + [pair for pair in matching if pair[0].also]
        for d, rx in applicable:
            if d.merge or not d.also:
                continue
            for piece in self._pieces(text, d):
                row = self._row(piece, d, rx, account_currency, result, text)
                if row and row.external_id not in seen_ids:
                    seen_ids.add(row.external_id)
                    result.rows.append(row)
                    if d.split and len(primary_rows) == 1 and primary_rows[0].currency == row.currency:
                        # The booked total held this credit: the sale
                        # keeps its own proceeds, the credit its own row.
                        main = primary_rows[0]
                        rest = round(abs(main.amount) - abs(row.amount), 2)
                        main.amount = rest if main.amount >= 0 else -rest
        # A tax page printed under the statement it belongs to: its
        # taxes go onto that row, and its after-tax figure replaces the
        # amount, because that is what reached the account.
        for d, rx in applicable:
            # Only onto a trade or a credit: a tax page on its own is
            # its own row, not something to merge into itself.
            if not d.merge or len(primary_rows) != 1 or primary_kind == "tax":
                continue
            row = primary_rows[0]
            style = detect_style(text) if self.spec.number == "auto" else self.spec.number
            after = parse_number(_first(text, d.fields.get("amount", [])).get("amount"), style)
            gross = parse_number(_first(text, d.fields.get("gross", [])).get("gross"), style)
            if after is not None and gross is not None:
                taxes, seen = round(abs(abs(gross) - abs(after)), 2), True
            else:
                style = detect_style(text) if self.spec.number == "auto" else self.spec.number
                taxes, seen = _sum(text, d.fields.get("taxes", []), "tax", style, row.currency,
                                   _fx(text, d.fields.get("fx", []), style))
            if seen and taxes:
                row.tax = round((row.tax or 0.0) + taxes, 2)
            if after is not None:
                row.amount = abs(after) * (-1 if row.amount < 0 else 1)
            elif seen and taxes and not d.fields.get("amount"):
                # No after-tax figure on the page: the primary was the
                # gross, and the tax comes off it.
                row.amount = round((abs(row.amount) - taxes) * (-1 if row.amount < 0 else 1), 2)
        if not result.rows and not result.problems:
            result.problems.append(f"{self.LABEL}: the document was recognised but nothing could be read from it.")
        return result

    def _pieces(self, text: str, d: Doc) -> list[str]:
        if not d.block:
            return [text]
        starts = [m.start() for m in re.finditer(d.block, text, re.M)]
        if not starts:
            return []
        return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]

    def _row(self, piece: str, d: Doc, rx, account_currency: str, result: ParseResult,
             whole: str | None = None):
        style = detect_style(piece) if self.spec.number == "auto" else self.spec.number
        f = d.fields
        g: dict = {}
        # First field to name a group keeps it: the settlement line's
        # value date must not overwrite the trade date found before it.
        for key in ("security", "shares", "price", "date", "amount", "ref", "type"):
            for k, v in _first(piece, f.get(key, [])).items():
                g.setdefault(k, v)
        # A statement's header carries the date once for every row cut
        # out below it: when the row has none of its own, the header's.
        if "date" not in g and whole is not None and whole != piece:
            g.update(_first(whole, f.get("date", [])))
        kind = d.kind
        if kind == "trade":
            kind = "sell" if (d.sell and re.search(d.sell, piece, re.M)) else "buy"
            if d.transfer and re.search(d.transfer, piece, re.M):
                kind = "transfer"
        if kind == "rows":
            kind = None
            word = (g.get("type") or "")
            for pattern, k in (d.kinds or {}).items():
                if re.search(pattern, word, re.I):
                    kind = k
                    break
            if kind == "skip":
                return None
            if kind is None:
                amount_probe = parse_number(g.get("amount"), style)
                sign = (g.get("sign") or "").strip()
                if amount_probe is None:
                    return None
                negative = amount_probe < 0 or sign in ("-", "S")
                kind = "withdrawal" if negative else "deposit"
        date = parse_date(g.get("date"))
        if not date and g.get("date") and re.fullmatch(r"\d{1,2}\.\d{1,2}\.?", g["date"].strip()):
            # "07.07." on a statement whose year is printed once, in the
            # header: the doc's `year` field says where.
            year = _first(whole or piece, f.get("year", [])).get("year")
            if year:
                date = parse_date(g["date"].strip().rstrip(".") + "." + year)
        if not date:
            if d.block is None:
                result.problems.append(f"{self.LABEL}: no date found.")
            return None
        amount = parse_number(g.get("amount"), style)
        gross = parse_number(_first(piece, f.get("gross", [])).get("gross"), style)
        if d.kind == "tax" and gross is not None and amount is not None:
            # A tax page that prints before-tax and after-tax figures:
            # the difference is the tax, whatever the lines between
            # them look like — comdirect prints some of them in a font
            # that comes out as underscores.
            taxes_from_totals = round(abs(abs(gross) - abs(amount)), 2)
            amount = taxes_from_totals
            g["_taxes_override"] = taxes_from_totals
        refund = False
        if amount is None and d.kind == "tax":
            # A tax statement often has no total of its own: the tax is
            # the sum of its lines — and when those add up to a credit,
            # the statement is a refund.
            taxes_only, seen = _sum(piece, f.get("taxes", []), "tax", style)
            amount = taxes_only if seen else None
            refund = seen and taxes_only < 0
        if amount is None and kind == "transfer":
            amount = 0.0                                     # units move, no money does
        if amount is None:
            if d.block is None:
                result.problems.append(f"{self.LABEL}: no amount found on {date}.")
            return None
        currency = (g.get("currency") or account_currency).replace("€", "EUR").upper()[:3]
        fx = _fx(piece, f.get("fx", []), style)
        isin = g.get("isin") or find_isin(g.get("isin_text") or "")
        name = " ".join(f"{g.get('name') or ''} {g.get('name2') or ''}".split()) or None
        shares = parse_number(g.get("shares"), style)
        notation = (g.get("notation") or "").strip()
        if shares is not None and notation and not notation.lower().startswith(("st", "stk", "shs", "sh", "qty", "nom")) \
                and re.fullmatch(r"[A-Z]{3}", notation):
            shares = shares / 100.0
        price = parse_number(g.get("price"), style)
        fees, _ = _sum(piece, f.get("fees", []), "fee", style, currency, fx)
        taxes, _ = _sum(piece, f.get("taxes", []), "tax", style, currency, fx)
        if "_taxes_override" in g:
            taxes = g["_taxes_override"]

        amount = abs(amount)
        sign_word = (g.get("sign") or "").strip()
        if kind in ("buy", "fee", "tax", "withdrawal"):
            amount = -amount
        elif kind == "transfer":
            amount = 0.0
        if kind == "tax" and (refund or re.search(r"(?i)erstattung|refund|gutschrift|rückzahlung|optimierung", piece[:400] + sign_word)):
            amount = abs(amount)
        quantity = None
        if shares is not None and kind in ("buy", "sell", "transfer"):
            quantity = abs(shares) if kind != "sell" else -abs(shares)
            if kind == "transfer" and re.search(r"(?i)ausgang|belastung|outbound|abgang", piece[:300]):
                quantity = -abs(shares)
        seed = "|".join([self.SLUG, kind, date, isin or "", f"{amount:.2f}", currency, g.get("ref") or "",
                         f"{quantity or 0:.6f}"])
        return ParsedTxn(
            txn_date=date, description=self._description(d, kind, name, isin),
            amount=amount, currency=currency, kind=kind,
            external_id=f"{self.SLUG}:{hashlib.sha1(seed.encode()).hexdigest()[:20]}",
            isin=isin, security_name=name, quantity=quantity,
            price=abs(price) if price else None,
            fee=abs(fees) if fees else None, tax=taxes if taxes else None,
        )

    @staticmethod
    def _description(d: Doc, kind: str, name: str | None, isin: str | None) -> str:
        word = {"buy": "Kauf", "sell": "Verkauf", "dividend": "Dividende", "interest": "Zinsen",
                "tax": "Steuer", "fee": "Gebühr", "deposit": "Einzahlung", "withdrawal": "Auszahlung",
                "transfer": "Übertrag"}.get(kind, kind)
        return " ".join(f"{word} {name or isin or ''}".split())[:500]
