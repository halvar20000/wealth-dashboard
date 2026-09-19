"""Debitum Investments (Latvia) — the period Account Statement, a
summary rather than a list: deposits, withdrawals and the interest of
the period, booked on its last day."""

from __future__ import annotations

import re

from ..statement import Doc, Spec


def _num(text: str, label: str) -> float:
    m = re.search(r"^" + label + r"\s*(-?[\d.]+)$", text, re.M)
    return float(m.group(1)) if m else 0.0


def summary(text: str) -> str:
    end = re.search(r"^Report date to \(inclusive\): (\d{4}-\d{2}-\d{2})", text, re.M)
    if not end:
        return text
    date = end.group(1)
    rows = []
    deposits = _num(text, r"DEPOSITS during reporting period:")
    withdrawals = _num(text, r"WITHDRAWALS during reporting period:")
    tax = -_num(text, r"Income tax withheld")
    gross = _num(text, r"Paid interest\*\*") + _num(text, r"Other balance increases during reporting period:")
    if deposits:
        rows.append(f"ROW {date} deposit {deposits:.2f}")
    if withdrawals:
        rows.append(f"ROW {date} withdrawal {withdrawals:.2f}")
    if gross:
        rows.append(f"ROW {date} interest {gross - tax:.2f} tax {tax:.2f}")
    return text + "\n" + "\n".join(rows) + "\n"


FIELDS = {
    "date": [r"^ROW (?P<date>\d{4}-\d{2}-\d{2}) "],
    "type": [r"^ROW \S+ (?P<type>\w+) "],
    "amount": [r"^ROW \S+ \w+ (?P<amount>[\d.]+)"],
    "taxes": [r" tax (?P<tax>[\d.]+)$"],
}

SPEC = Spec(
    slug="debitum_pdf",
    label="Debitum Investments — Account Statement PDF",
    corpus="debituminvestments",
    marks=[r"debitum\.investments", r"Debitum"],
    number="en",
    preprocess=summary,
    docs=[
        Doc(kind="rows", when=r"^ACCOUNT STATEMENT$", block=r"^ROW ", fields=FIELDS,
            kinds={r"^deposit": "deposit", r"^withdrawal": "withdrawal", r"^interest": "interest"}),
    ],
)
