"""Sydbank — the Fondsafregning (a purchase or sale) and the
Udbytte-meddelelse, in Danish with Danish notation."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"

TRADE_FIELDS = {
    "security": [r"^ISIN-kode " + ISIN, r"(?:k.bt|solgt): (?P<name>.+?) ?,"],
    "date": [r"^Du har den (?P<date>\d{2}\.\d{2}\.\d{2}) kl"],
    "shares": [r"^Antal stk Fondskurs Kursv.rdi\n(?P<shares>" + NUM + r") (?P<price>" + NUM + r") " + NUM + r"$"],
    "amount": [r"^I alt\n(?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"^Forretningsnr\. (?P<ref>\d+)"],
    "fees": [r"^\(Handelsomkostninger i alt (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")\)"],
}
DIVIDEND_FIELDS = {
    "security": [r"^\d{2}\.\d{2}\.\d{4} \d+ (?P<name>.+)\nISIN-kode: " + ISIN],
    "shares": [r"^Beholdning (?P<shares>" + NUM + r") Stk\. Udbytte (?P<gross>" + NUM + r")"],
    "gross": [r"^Beholdning " + NUM + r" Stk\. Udbytte (?P<gross>" + NUM + r")"],
    "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) \d+ "],
    "amount": [r"^Afkast i alt kr\. (?P<amount>" + NUM + r") "],
    "taxes": [r"^Udbytteskat[^\n]*? (?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="sydbank_pdf",
    label="Sydbank — Fondsafregning PDF",
    corpus="sydbankas",
    marks=[r"Sydbank", r"sydbank\.dk"],
    number="de",
    docs=[
        Doc(kind="trade", when=r"^Fondsafregning", sell=r"\bsolgt:", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Udbytte-meddelelse", fields=DIVIDEND_FIELDS),
    ],
)
