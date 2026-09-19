"""Tiger Brokers (Singapore) — the monthly Activity Statement: a Trades
table with one row per execution, and the Deposits & Withdrawals,
Dividends and Withholding Tax tables. The tax on a dividend stands in
a table of its own; `net()` folds it onto the dividend's line."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"-?[\d,]+\.\d+"
DATE = r"\d{4}-\d{2}-\d{2}"

TRADE_ROW = r"^[A-Z.]+ " + DATE + r", \d{2}:\d{2}:\d{2}, GMT[+-]\d+ -?[\d,.]+ " + NUM
TRADE_FIELDS = {
    "security": [r"^(?P<name>[A-Z.]+) (?P<date>" + DATE + r"), \d{2}:\d{2}:\d{2}, GMT[+-]\d+ (?P<shares>-?[\d,.]+) (?P<price>" + NUM + r") " + NUM + r" (?P<amount>" + NUM + r") "],
    "date": [r"^[A-Z.]+ (?P<date>" + DATE + r"), "],
    "fees": [r"Commission: (?P<sign>-?)(?P<fee>[\d.]+) (?:-?[\d.]+) ", r"^(?:Platform|Settlement) Fee: (?P<sign>-?)(?P<fee>[\d.]+)$"],
    "type": [r"^Stock Currency: (?P<currency>[A-Z]{3})"],
}
CASH_ROW = r"^" + DATE + r" \S.* " + NUM + r"(?: [A-Z]{3})?$"
CASH_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "amount": [r"^" + DATE + r" (?P<type>.+?) (?P<amount>" + NUM + r")(?: (?P<currency>[A-Z]{3}))?$"],
    "type": [r"^" + DATE + r" (?P<type>.+?) " + NUM + r"(?: [A-Z]{3})?$"],
    "security": [r"^" + DATE + r" (?P<name>[A-Z.]+) Cash Dividend"],
    "taxes": [r"\[tax (?P<tax>[\d.]+)\]"],
}


def net(text: str) -> str:
    """The withholding tax table, folded onto the dividend lines."""
    if "Withholding Tax" not in text:
        return text
    lines = text.split("\n")
    taxes: dict[tuple, float] = {}
    section = None
    for line in lines:
        if re.match(r"^(?:Dividends|Withholding Tax|Deposits & Withdrawals|Trades|Transaction Fees|Interest)\s*$", line):
            section = line.strip()
        m = re.match(r"^(" + DATE + r") ([A-Z.]+) Cash Dividend .* - Tax (" + NUM + r")(?: [A-Z]{3})?$", line)
        if m and section == "Withholding Tax":
            taxes[(m.group(1), m.group(2))] = abs(parse_number(m.group(3), "en") or 0.0)
    out = []
    section = None
    for line in lines:
        if re.match(r"^(?:Dividends|Withholding Tax|Deposits & Withdrawals|Trades|Transaction Fees|Interest)\s*$", line):
            section = line.strip()
        m = re.match(r"^(" + DATE + r") ([A-Z.]+) Cash Dividend (.*) (" + NUM + r")((?: [A-Z]{3})?)$", line)
        if m and section == "Dividends" and (m.group(1), m.group(2)) in taxes:
            tax = taxes[(m.group(1), m.group(2))]
            gross = parse_number(m.group(4), "en") or 0.0
            line = f"{m.group(1)} {m.group(2)} Cash Dividend {m.group(3)} [tax {tax:.2f}] {gross - tax:.2f}{m.group(5)}"
        out.append(line)
    return "\n".join(out)


SPEC = Spec(
    slug="tigerbrokers_pdf",
    label="Tiger Brokers — Activity Statement PDF",
    corpus="tigerbrokerspteltd",
    marks=[r"Tiger Brokers"],
    number="en",
    preprocess=net,
    docs=[
        Doc(kind="rows", when=r"^Trades\s*$", block=TRADE_ROW, fields=TRADE_FIELDS,
            kinds={r"^-": "sell", r".": "buy"}),
        Doc(kind="rows", when=r"^Deposits & Withdrawals", block=r"^" + DATE + r" (?:Deposit|Withdrawal) ", fields=CASH_FIELDS, also=True,
            kinds={r"Withdrawal": "withdrawal", r".": "deposit"}),
        Doc(kind="rows", when=r"^Dividends\s*$", block=r"^" + DATE + r" [A-Z.]+ Cash Dividend .* " + NUM + r"(?: [A-Z]{3})?$", fields=CASH_FIELDS, also=True,
            kinds={r"- Tax": "skip", r".": "dividend"}),
        Doc(kind="rows", when=r"^Interest\s*$", block=r"^" + DATE + r" .*[Ii]nterest.* " + NUM + r"(?: [A-Z]{3})?$", fields=CASH_FIELDS, also=True,
            kinds={r".": "interest"}),
    ],
)
TRADE_FIELDS["type"] = [r"^(?P<type>[A-Z.]+ " + DATE + r", \d{2}:\d{2}:\d{2}, GMT[+-]\d+ -?)"]
