"""Wealthsimple (Canada) — the monthly / annual Performance Report's
activity pages: deposits, trades, dividends, withholding tax and the
management fee (gross, promotion and sales tax folded into one)."""

from __future__ import annotations

import re

from ..statement import MONTHS, Doc, Spec

NUM = r"[\d,]+(?:\.\d+)?"
DATE = r"\d{2}\.\d{2}\.\d{4}"
_ROW = re.compile(r"^([A-Z][a-z]{2}) (\d{2}) (.*)$")
_FEE = re.compile(r"^(?:Gross management fee|Promotions and discounts applied|Sales tax on management fee).* (-?)\$(" + NUM + r")$")


def activity(text: str) -> str:
    """Rows dated 'Jun 29' get the report's year; the fee lines of a month
    become one 'Management fee' row; every row ends in its currency."""
    ym = re.search(r"(\d{4}) Performance Report", text)
    year = ym.group(1) if ym else None
    out, fees, order = [], {}, []
    for line in text.splitlines():
        m = _ROW.match(line)
        if not (m and year and m.group(1).lower() in MONTHS):
            out.append(line)
            continue
        date = f"{int(m.group(2)):02d}.{MONTHS[m.group(1).lower()]:02d}.{year}"
        f = _FEE.match(m.group(3))
        if f:
            v = float(f.group(2).replace(",", "")) * (-1 if f.group(1) else 1)
            if date not in fees:
                order.append(date)
            fees[date] = fees.get(date, 0.0) + v
            continue
        out.append(f"{date} {m.group(3)} CAD")
    for date in order:
        out.append(f"{date} Management fee – – -${-fees[date]:,.2f} CAD")
    return "\n".join(out)


FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" (?:settled \w+ \d+ )?(?P<type>.+?) CAD$"],
    "security": [r" (?:Sold|Bought) (?P<shares>" + NUM + r") of (?P<name>.+?) for " + NUM + r" [A-Z]{3} -?" + NUM + r" \$(?P<price>" + NUM + r") ",
                 r"^" + DATE + r" (?P<name>.+?): \d{2}-[A-Z]{3}-\d{2} \(record date\) (?P<shares>" + NUM + r") shares",
                 r"^" + DATE + r" (?P<name>.+?): Non-resident tax"],
    "amount": [r" (?P<sign>-?)\$(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="wealthsimple_pdf",
    label="Wealthsimple — Performance Report PDF",
    corpus="wealthsimpleInvestmentsInc",
    marks=[r"Wealthsimple"],
    number="en",
    preprocess=activity,
    docs=[
        Doc(kind="rows", when=r" activity$", block=r"^" + DATE + r" .+ CAD$", fields=FIELDS,
            kinds={r"^Sold ": "sell", r"^Bought ": "buy", r"Transfer In": "deposit", r"Transfer Out": "withdrawal",
                   r"^Management fee": "fee", r"Non-resident tax": "tax", r"\(record date\)": "dividend"}),
    ],
)
