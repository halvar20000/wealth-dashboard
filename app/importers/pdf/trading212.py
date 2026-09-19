"""Trading 212 (via FXFlat Bank) — the Aktivitätsauszug: one row per
executed order, the interest on cash with its tax, and dividends."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"-?[\d,]+(?:\.\d+)?"
STAMP = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"

ORDER = r"^" + STAMP + r" \S+ [A-Z]{2}[A-Z0-9]{9}\d [A-Z]{3} \d+ (?:Kaufen|Verkaufen|Buy|Sell) "
ORDER_FIELDS = {
    "date": [r"^(?P<date>\d{4}-\d{2}-\d{2}) "],
    "security": [r"^" + STAMP + r" (?P<name>\S+) " + ISIN + r" (?P<currency>[A-Z]{3}) (?P<ref>\d+) (?P<type>Kaufen|Verkaufen|Buy|Sell) (?P<shares>" + NUM + r") (?P<price>" + NUM + r") "],
    "amount": [r"\[net (?P<amount>" + NUM + r")\]"],
    "taxes": [r"\[tax (?P<tax>[\d.]+)\]"],
    "fees": [r"\[fee (?P<fee>[\d.]+)\]"],
}
INTEREST_ROW = r"^" + STAMP + r" Verzinsung von Geld [A-Z]{3} "
INTEREST_FIELDS = {
    "date": [r"^(?P<date>\d{4}-\d{2}-\d{2}) "],
    "type": [r"^" + STAMP + r" (?P<type>Verzinsung)"],
    "amount": [r"^" + STAMP + r" Verzinsung von Geld (?P<currency>[A-Z]{3}) " + NUM + r" " + NUM + r" \S+ (?P<amount>" + NUM + r")$"],
    "taxes": [r"^" + STAMP + r" Verzinsung von Geld [A-Z]{3} " + NUM + r" -(?P<tax>[\d.]+) "],
}


def totals(text: str) -> str:
    """The order row ends "… fee value tax": the net, the fee and the tax
    written where the fields can read them; a tax refund on a sale is
    kept as a row of its own."""
    out = []
    for line in text.split("\n"):
        m = re.match(r"^(" + STAMP + r" \S+ [A-Z]{2}[A-Z0-9]{9}\d [A-Z]{3} \d+ (Kaufen|Verkaufen|Buy|Sell) .*?) (-?[\d.]+|-) (-?[\d.]+)(?: (-?[\d.]+|-))?$", line)
        if m:
            fee = abs(float(m.group(3))) if m.group(3) != "-" else 0.0
            value = float(m.group(4))
            tax = float(m.group(5)) if m.group(5) and m.group(5) != "-" else 0.0
            sell = m.group(2) in ("Verkaufen", "Sell")
            net = value + (tax if tax < 0 else 0.0) if sell else value
            line = f"{m.group(1)} [net {net:.2f}]" + (f" [fee {fee:.2f}]" if fee else "") + (f" [tax {-tax:.2f}]" if tax < 0 else "")
            if tax > 0:
                line += f"\n{m.group(1)[:19]} Steuererstattung [refund {tax:.2f}]"
        out.append(line)
    return "\n".join(out)


SPEC = Spec(
    slug="trading212_pdf",
    label="Trading 212 — Aktivitätsauszug PDF",
    corpus="trading212",
    marks=[r"Trading 212", r"FXFlat Bank"],
    number="en",
    preprocess=totals,
    docs=[
        Doc(kind="rows", when=r"ausgef.hrte Auftr.ge", block=ORDER, fields=ORDER_FIELDS, kinds={r"^(?:Verkaufen|Sell)": "sell", r".": "buy"}),
        Doc(kind="rows", when=r"^Transaktionen\s*$", block=INTEREST_ROW, fields=INTEREST_FIELDS, kinds={r".": "interest"}, also=True),
        # The cash account: card payments, deposits, withdrawals.
        Doc(kind="rows", when=r"^Transaktionen\s*$", block=r"^" + STAMP + r" (?:Kartenkauf|Einzahlung|Auszahlung|Card|Deposit|Withdrawal|[^\n]*?[Bb]ankeinzahlung)\S* [A-Z]{3} ", also=True,
            fields={"date": [r"^(?P<date>\d{4}-\d{2}-\d{2}) "], "type": [r"^" + STAMP + r" (?P<type>.+?) [A-Z]{3} -?[\d.]+"],
                    "amount": [r"^" + STAMP + r" .+? (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")(?: |$)"]},
            kinds={r"Kartenkauf|Card|Auszahlung|Withdrawal": "withdrawal", r".": "deposit"}),
        Doc(kind="rows", when=r"Steuererstattung \[refund", block=r"^" + STAMP + r" Steuererstattung ", also=True, kinds={r".": "tax"},
            fields={"date": [r"^(?P<date>\d{4}-\d{2}-\d{2}) "], "type": [r"(?P<type>Steuererstattung)"],
                    "amount": [r"\[refund (?P<amount>[\d.]+)\]"], "security": [r"(?P<sign>Erstattung)"]}),
    ],
)
