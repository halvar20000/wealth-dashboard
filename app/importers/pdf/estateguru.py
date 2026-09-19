"""Estateguru — the Transaktionsbericht: one row per cash flow with the
payment date, confirmation date, kind, status, project and amount, a
debit in brackets."""

from __future__ import annotations

from ..statement import Doc, Spec

NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"
ROW = r"^" + DATE + r", \d{2}:\d{2} " + DATE + r", \d{2}:\d{2} .+? (?:Genehmigt|Approved) "
FIELDS = {
    "date": [r"^(?P<date>" + DATE + r"), "],
    "type": [r"^" + DATE + r", \d{2}:\d{2} " + DATE + r", \d{2}:\d{2} (?P<type>\S+) "],
    "amount": [r" (?P<amount>\(€ -?" + NUM + r"\)|€ -?" + NUM + r") € -?" + NUM + r"$"],
}

SPEC = Spec(
    slug="estateguru_pdf",
    label="Estateguru — Transaktionsbericht PDF",
    corpus="estateguru",
    marks=[r"Estateguru", r"estateguru\.co"],
    number="auto",
    preprocess=lambda t: __import__("re").sub(r"\(€ -?([\d.,]+)\) ", r"-\1 ", __import__("re").sub(r"(?<![(-])€ (-?[\d.,]+) €", r"\1 €", t)),
    docs=[
        Doc(kind="rows", when=r"^Transaktionsbericht|^Transactions? [Rr]eport", block=ROW, fields={
                "date": [r"^(?P<date>" + DATE + r"), "],
                "type": [r"^" + DATE + r", \d{2}:\d{2} " + DATE + r", \d{2}:\d{2} (?P<type>.+?) (?:Genehmigt|Approved) "],
                "amount": [r" (?P<amount>-?" + NUM + r") € -?" + NUM + r"$"],
            },
            # A loan funded is money out of the account, a repayment money back in.
            kinds={r"^Zins|^Interest|^Cashback|^Entsch.digung|^Strafe|^Penalty|^Bonus": "interest", r"geb.hr|[Ff]ee": "fee",
                   r"^Investition|^Investment|^Auszahlung|^Withdrawal": "withdrawal",
                   r"^Hauptbetrag|^Principal|^Kapital|^Einzahlung|^Deposit": "deposit"}),
    ],
)
