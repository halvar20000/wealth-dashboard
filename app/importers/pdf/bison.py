"""BISON (EUWAX) — the yearly Info-Report: a line per crypto trade
with the coin and the units, the time, price and amount on the next."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^(?:Kauf|Verkauf\*?|Einzahlung|Auszahlung|Krypto-Einzahlung|Krypto-Auszahlung)(?: [A-Z]{3,5} " + NUM + r")?$"
FIELDS = {
    "security": [r"^(?:Kauf|Verkauf\*?) (?P<name>[A-Z]{3,5}) (?P<shares>" + NUM + r")\n" + DATE + r" \d{2}:\d{2} (?P<price>" + NUM + r") €/[A-Z]{3,5} [-+] (?P<amount>" + NUM + r") €"],
    "type": [r"^(?P<type>Kauf|Verkauf|Einzahlung|Auszahlung|Krypto-Einzahlung|Krypto-Auszahlung)\b"],
    "date": [r"^(?P<date>" + DATE + r") \d{2}:\d{2} "],
    "amount": [r"^" + DATE + r" \d{2}:\d{2} (?:" + NUM + r" €/[A-Z]{3,5} )?[-+] (?P<amount>" + NUM + r") €"],
}

SPEC = Spec(
    slug="bison_pdf",
    label="BISON — Info-Report PDF",
    corpus="bison",
    marks=[r"BISON", r"bisonapp\.com", r"EUWAX"],
    docs=[
        Doc(kind="rows", when=r"^BISON Info-Report", block=ROW, fields=FIELDS,
            kinds={r"^Kauf": "buy", r"^Verkauf": "sell", r"^Krypto": "transfer", r"^Einzahlung": "deposit", r"^Auszahlung": "withdrawal"}),
    ],
)
