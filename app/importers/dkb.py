"""DKB — the Umsätze CSV of a Girokonto, Tagesgeld or Visa card.

Export it in the banking portal: open the account → Umsätze → choose
the period → CSV-Export. The card has the same button on its own page.

This is a bank statement, not a broker ledger: there are no ISINs, no
quantities and no transaction ids. What there is, is four layouts —
DKB replaced its portal in 2023 and changed the file with it — and all
four are recognised here, because the old one is still what anyone's
archived downloads look like.

    old Girokonto   "Kontonummer:";"DE… / Girokonto";        ISO-8859-1
    new Girokonto   "Girokonto";"DE…"   (or "Konto", "Tagesgeld")   UTF-8
    old Visa        "Kreditkarte:";"1234********5678";       ISO-8859-1
    new Visa        "Karte";"Visa Kreditkarte 1234••••"      UTF-8

Above the column header sit a few `"key";"value"` lines: the account,
the period, and the balance as of a date. The balance is taken — for a
DKB account without a bank connection this is the only balance the app
will ever get.

Three things worth knowing.

**The amount may carry its currency:** `"-10,22 €"` in one export and
`"-10,22"` in the next, `"1234,56 EUR"` in the preamble. Stripped
before parsing, never assumed absent.

**A row can be pending.** The new layout has a `Status` column that
says `Vorgemerkt` until the booking is final. Pending rows are NOT
imported: their date and text change when they book, so a row taken
now would come back as a second, different row later. They are listed
so the user knows to export again once they are booked.

**There is no id, and a statement repeats itself.** Two coffees at the
same place on the same day are two identical lines. So the id is a
hash of the row plus a counter for its repeats within the file, which
is stable across two overlapping exports as long as both cover the
whole day — which an export by date range always does.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import Counter
from datetime import datetime

from .base import ParsedTxn, ParseResult, parse_date, parse_decimal

SLUG = "dkb"
LABEL = "DKB — Umsätze CSV (Girokonto, Tagesgeld, Visa)"

# The column-header line of each layout, by its first columns. Checked
# against the raw text so that a Latin-1 file whose umlauts came
# through as replacement characters still matches — none of these
# signatures has one.
_SIGNATURES = (
    '"Buchungstag";"Wertstellung";"Buchungstext"',           # old Girokonto
    '"Buchungsdatum";"Wertstellung";"Status"',               # new Girokonto / Tagesgeld
    '"Umsatz abgerechnet und nicht im Saldo enthalten"',     # old Visa
    '"Belegdatum";"Wertstellung";"Status";"Beschreibung"',   # new Visa
)

_PREAMBLE_ACCOUNT_KEYS = ("kontonummer", "girokonto", "tagesgeld", "konto",
                          "kreditkarte", "karte")
# "Kontostand vom 25.08.2023:" / "Saldo vom 30.10.2023:" / old Visa "Saldo:"
# with the date on its own "Datum:" line.
_BALANCE_KEY_RE = re.compile(r"^(?:kontostand|saldo)(?:\s+vom\s+(\d{2}\.\d{2}\.\d{2,4}))?:?$")

_INTEREST_WORDS = ("zins", "interest")
_FEE_WORDS = ("entgelt", "gebühr", "gebuhr", "kartenpreis", "kontoführung",
              "kontofuhrung")
_TAX_WORDS = ("steuer", "kapitalertrag", "solidaritätszuschlag", "soli ",
              "kirchensteuer")
_SALARY_WORDS = ("lohn", "gehalt", "rente", "salary", "pension", "besoldung")
# The card is paid off from the Girokonto once a month. That shows on
# the card as "Ausgleich Kreditkarte" and on the account as a direct
# debit to the card: money moving between two of the user's own
# accounts, not spending, and not income either.
_SETTLEMENT_WORDS = ("ausgleich kreditkarte", "kreditkartenabrechnung",
                     "kreditkarten-abrechnung", "kreditkartenumsatz",
                     "visa-abrechnung", "ausgleich visa")


def matches(header: list[str], sample: str) -> bool:
    return any(sig in sample for sig in _SIGNATURES)


def _decode(content: bytes | str) -> str:
    """UTF-8 for the current portal's files, Latin-1 for the old one.

    Tried strictly rather than with replacement: a strict decode either
    succeeds or tells us it is the other encoding, whereas a lenient one
    would quietly turn every "Gläubiger" into "Gl�ubiger" and every
    payee with an umlaut into a name the user's rules cannot match.
    """
    if isinstance(content, str):
        return content.lstrip("\ufeff")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252", "replace")


def _date(raw: str | None) -> str | None:
    """`25.08.23` in the new files, `25.08.2023` in the old ones."""
    iso = parse_date(raw)
    if iso:
        return iso
    try:
        return datetime.strptime((raw or "").strip(), "%d.%m.%y").date().isoformat()
    except ValueError:
        return None


def _amount(raw: str | None) -> float | None:
    """`-10,22 €`, `-10,22`, `1234,56 EUR`, `100.000,00 €` — all the same
    number, in one file or another."""
    if raw is None:
        return None
    s = raw.replace("€", "").replace("EUR", "").strip()
    return parse_decimal(s)


def _has(text: str, words) -> bool:
    low = text.lower()
    return any(w in low for w in words)


def _split(text: str) -> tuple[dict, list[list[str]], int]:
    """The preamble as a dict, the rows from the column header on, and
    the line number of that header (for messages that point at a line)."""
    lines = text.splitlines()
    header_at = next(
        (i for i, line in enumerate(lines)
         if any(line.startswith(sig) for sig in _SIGNATURES)), None)
    if header_at is None:
        return {}, [], 0

    preamble: dict[str, str] = {}
    for line in lines[:header_at]:
        cells = next(csv.reader([line], delimiter=";"), [])
        cells = [c.strip() for c in cells]
        if len(cells) >= 2 and cells[0]:
            preamble[cells[0].rstrip(":").strip().lower()] = cells[1]

    rows = list(csv.reader(io.StringIO("\n".join(lines[header_at:])),
                           delimiter=";"))
    return preamble, rows, header_at + 1


def _closing_balance(preamble: dict, currency: str) -> dict | None:
    for key, value in preamble.items():
        m = _BALANCE_KEY_RE.match(key)
        if not m:
            continue
        amount = _amount(value)
        if amount is None:
            continue
        as_of = _date(m.group(1)) if m.group(1) else _date(preamble.get("datum"))
        if not as_of:
            continue
        ccy = currency
        if "EUR" in value.upper() or "€" in value:
            ccy = "EUR"
        return {"amount": amount, "currency": ccy, "as_of": as_of}
    return None


def _account_ref(preamble: dict) -> str:
    for key in _PREAMBLE_ACCOUNT_KEYS:
        if preamble.get(key):
            return preamble[key].replace(" ", "")
    return ""


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    text = _decode(content)
    result = ParseResult()
    preamble, rows, header_line = _split(text)

    if not rows:
        result.problems.append(
            "This is not a DKB Umsätze export — expected a column header "
            "starting with Buchungstag, Buchungsdatum or Belegdatum.")
        return result

    header = [h.strip() for h in rows[0]]
    col = {name: i for i, name in enumerate(header) if name}
    # Every layout has these two, under one name or another.
    c_date = col.get("Buchungstag", col.get("Buchungsdatum", col.get("Belegdatum")))
    c_amount = next((i for name, i in col.items() if name.startswith("Betrag")), None)
    if c_date is None or c_amount is None:
        result.problems.append("This DKB file has no date or amount column.")
        return result
    is_card = "Beschreibung" in col and "Verwendungszweck" not in col

    def cell(row, name):
        i = col.get(name)
        return row[i].strip() if i is not None and i < len(row) else ""

    currency = account_currency.upper()[:3]
    result.closing_balance = _closing_balance(preamble, currency)
    account_ref = _account_ref(preamble)
    seen: Counter[str] = Counter()

    for offset, row in enumerate(rows[1:], start=1):
        line_no = header_line + offset
        if not any(c.strip() for c in row):
            continue
        if len(row) <= max(c_date, c_amount):
            result.problems.append(f"line {line_no}: only {len(row)} columns")
            continue

        status = cell(row, "Status").lower()
        if status and status != "gebucht":
            # Vorgemerkt: not booked yet, so not final yet — see the
            # module docstring. Said, not counted.
            result.problems.append(
                f"line {line_no}: pending ({cell(row, 'Status')}), not imported — "
                "export again once it is booked")
            continue

        date = _date(row[c_date].strip())
        if not date:
            result.problems.append(
                f"line {line_no}: unreadable date {row[c_date].strip()!r}")
            continue
        amount = _amount(row[c_amount])
        if amount is None:
            result.problems.append(
                f"line {line_no}: unreadable amount {row[c_amount].strip()!r}")
            continue

        if is_card:
            counterparty = None
            purpose = cell(row, "Beschreibung")
            booking_text = cell(row, "Umsatztyp")
            description = purpose
        else:
            purpose = cell(row, "Verwendungszweck")
            booking_text = cell(row, "Buchungstext") or cell(row, "Umsatztyp")
            # Old layout: one column for "the other party". New layout:
            # payer and payee, one of which is the user — the other one
            # is the counterparty, and the direction of the money says
            # which.
            counterparty = cell(row, "Auftraggeber / Begünstigter")
            if not counterparty:
                payer = cell(row, "Zahlungspflichtige*r")
                payee = cell(row, "Zahlungsempfänger*in")
                counterparty = (payer if amount > 0 else payee) or payee or payer
            counterparty = counterparty or None
            description = purpose or counterparty or booking_text

        blob = f"{booking_text} {purpose} {counterparty or ''}"
        if _has(blob, _SETTLEMENT_WORDS):
            kind = "transfer"
        elif _has(blob, _TAX_WORDS):
            kind = "tax"
        elif _has(blob, _INTEREST_WORDS) and amount > 0:
            kind = "interest"
        elif _has(blob, _FEE_WORDS) and amount < 0:
            kind = "fee"
        elif _has(f"{booking_text} {purpose}", _SALARY_WORDS) and amount > 0:
            kind = "deposit"
        else:
            kind = "other"

        description = " ".join(description.split())
        if booking_text and booking_text.lower() not in ("eingang", "ausgang") \
                and booking_text.lower() not in description.lower():
            description = f"{description} [{booking_text}]"

        seed = "|".join([account_ref, date, _date(cell(row, "Wertstellung")) or "",
                         f"{amount:.2f}", counterparty or "", " ".join(purpose.split()),
                         cell(row, "Mandatsreferenz"), cell(row, "Kundenreferenz")])
        seen[seed] += 1
        digest = hashlib.sha1(f"{seed}#{seen[seed]}".encode()).hexdigest()[:20]

        result.rows.append(ParsedTxn(
            txn_date=date,
            description=description[:500] or "DKB",
            amount=amount,
            currency=currency,
            kind=kind,
            external_id=f"dkb:{digest}",
            counterparty=counterparty,
        ))

    return result
