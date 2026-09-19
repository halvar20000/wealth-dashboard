"""KFintech / CAMS — the Indian Consolidated Account Statement: one
table per mutual-fund folio, purchases, redemptions, switches, IDCW
payouts, with stamp duty / STT / TDS on their own lines below."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d+"
DATE = r"\d{2}-[A-Z][a-z]{2}-\d{4}"

_HEAD = re.compile(r"^(.*?)\s*-\s*ISIN:\s*([A-Z]{2}[A-Z0-9]{9}\d|INF)?")
_ROW = re.compile(r"^(" + DATE + r") (.+?) (\(?" + NUM + r"\)?) (\(?" + NUM + r"\)?) (" + NUM + r") (" + NUM + r")$")
_UNITS = re.compile(r"^(" + DATE + r") (Creation of units.*?) (" + NUM + r") (" + NUM + r")$")
_PAYOUT = re.compile(r"^(" + DATE + r") \*\*\*IDCW Payout @ Rs\.[\d.]+ per unit.*?\*\*\* (" + NUM + r")$")
_TAX = re.compile(r"^(" + DATE + r") \*\*\* (Stamp Duty|STT Paid|TDS on Above) \*\*\* (\(?[\d,.]+\)?)$")


def _f(s: str) -> float:
    neg = s.startswith("(")
    v = float(s.strip("()").replace(",", ""))
    return -v if neg else v


def cas(text: str) -> str:
    """Every transaction onto one canonical line carrying its fund and its taxes."""
    lines = text.splitlines()
    out, rows = [], []                    # rows: [date, kind, amount, units, price, tax, isin, name]
    name = isin = ""
    for i, line in enumerate(lines):
        m = _HEAD.match(line)
        if m and "ISIN:" in line:
            head = m.group(1)
            if not re.sub(r"\(Non-Demat\)|\W", "", head):
                head = lines[i - 1] if i else ""
            head = re.sub(r"^[A-Z0-9]+-", "", head)
            name = " ".join(re.sub(r"\(Non-Demat\)|\(formerly[^)]*\)", "", head, flags=re.I).split(" - ")[0].split())
            isin = m.group(2) if m.group(2) and len(m.group(2)) == 12 else ""
            continue
        m = _ROW.match(line)
        if m:
            amount, units = _f(m.group(3)), _f(m.group(4))
            kind = "sell" if amount < 0 or units < 0 else "buy"
            rows.append([m.group(1), kind, abs(amount), abs(units), _f(m.group(5)), 0.0, isin, name])
            continue
        m = _UNITS.match(line)
        if m:
            rows.append([m.group(1), "transfer", 0.0, _f(m.group(3)), 0.0, 0.0, isin, name])
            continue
        m = _PAYOUT.match(line)
        if m:
            rows.append([m.group(1), "dividend", _f(m.group(2)), 0.0, 0.0, 0.0, isin, name])
            continue
        m = _TAX.match(line)
        if m:
            tax = _f(m.group(3))
            for row in reversed(rows):
                if row[0] == m.group(1) and row[1] != "transfer":
                    row[5] += tax
                    # the statement's figure is the cash moved without the levy
                    row[2] += tax if row[1] == "buy" else -tax
                    break
            continue
        out.append(line)
    for d, kind, amount, units, price, tax, isin, name in rows:
        out.append(f"TXN {d} {kind} INR {amount:.2f} units {units:.3f} price {price:.4f} tax {tax:.2f} isin {isin or '-'} {name}")
    return "\n".join(out)


FIELDS = {
    "date": [r"^TXN (?P<date>" + DATE + r") "],
    "type": [r"^TXN " + DATE + r" (?P<type>\w+) "],
    "amount": [r"^TXN " + DATE + r" \w+ (?P<currency>INR) (?P<amount>[\d.]+) "],
    "shares": [r" units (?P<shares>[\d.]+) price (?P<price>[\d.]+) "],
    "security": [r" isin (?P<isin>[A-Z]{2}[A-Z0-9]{9}\d) (?P<name>.+)$", r" isin - (?P<name>.+)$"],
    "taxes": [r" tax (?P<tax>[\d.]+) "],
}

SPEC = Spec(
    slug="kfintech_pdf",
    label="KFintech / CAMS — Consolidated Account Statement PDF",
    corpus="kfintech",
    marks=[r"KFintech", r"CAMS"],
    number="en",
    preprocess=cas,
    docs=[
        Doc(kind="rows", when=r"^Consolidated Account Statement", block=r"^TXN ", fields=FIELDS,
            kinds={r"^buy": "buy", r"^sell": "sell", r"^dividend": "dividend", r"^transfer": "transfer"}),
    ],
)
