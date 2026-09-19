"""neon Switzerland (simply3a, held at Lienhardt & Partner) — the daily
statement: a row per booking with debit or credit and the balance,
the fund's number, units and rate on the lines under a fund trade."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^" + DATE + r" \S.* " + DATE + r" " + NUM + r" -?" + NUM + r"$"
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "amount": [r"^" + DATE + r" (?P<type>.+?) " + DATE + r" (?P<amount>" + NUM + r") -?" + NUM + r"$"],
    "type": [r"^" + DATE + r" (?P<type>.+?) " + DATE + r" " + NUM + r" -?" + NUM + r"$"],
    "security": [r"^" + DATE + r" Fund (?:buy|sell) [^\n]*\n(?P<name>.+)\nSecur\.Nr\. (?P<ref>\S+)"],
    "shares": [r"^Unit (?P<shares>" + NUM + r")"],
    "price": [r"^Rate (?P<price>" + NUM + r")"],
}

SPEC = Spec(
    slug="neon_pdf",
    label="neon simply3a — Daily statement PDF",
    corpus="neonswitzerlandag",
    marks=[r"neon Switzerland", r"neon-free\.ch", r"simply3a"],
    number="ch",
    docs=[
        Doc(kind="rows", when=r"^Date Detail Value date Debit Credit Balance", block=ROW, fields=FIELDS,
            kinds={r"^Fund buy": "buy", r"^Fund sell": "sell", r"fee|Fee": "fee", r"[Ii]nterest": "interest",
                   r"Deposit|Transfer in": "deposit", r"Withdrawal|Payout|Transfer out": "withdrawal"}),
    ],
)
