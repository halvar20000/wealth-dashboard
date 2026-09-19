"""Banque Pictet & Cie — the stock exchange advice and the security
event advice, in English, Swiss notation, columns run together."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?:Purchase|Sale) -?(?P<shares>" + NUM + r") (?P<name>.+?) at (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")$",
                 r"^(?:Purchase|Sale) (?P<notation>[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) at (?P<price>" + NUM + r")%$", r"^ISIN: " + ISIN],
    "date": [r"^Order date (?P<date>" + DATE + r")", r"Trade date (?P<date>" + DATE + r")", r"Execution date (?P<date>" + DATE + r")"],
    "amount": [r"^Net amount (?:Other)?(?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "ref": [r"Transaction no\.: (?P<ref>\d+)"],
    "fees": [r"^(?:Brokerage|Fees|Stock exchange fee|Third-party fees|Custody fees)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")(?: |$)"],
    "taxes": [r"^(?:Swiss stamp duty|Stamp duty|Withholding tax|Tax)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")(?: |$)"],
}
DIVIDEND_FIELDS = {
    "security": [r"^(?P<name>.+?) (?P<shares>" + NUM + r") GeneralTrade date (?P<date>" + DATE + r")", r"^ISIN: " + ISIN],
    "date": [r"Payment date (?P<date>" + DATE + r")", r"Value date (?P<date>" + DATE + r")"],
    "amount": [r"^(?P<amount>" + NUM + r") Quantity held " + NUM + r"Net amount (?P<currency>[A-Z]{3}) ", r"Net amount (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"Transaction no\.: (?P<ref>\d+)"],
    "taxes": [r"^(?:Withholding tax|Swiss withholding tax|Tax)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")(?: |$)"],
}

SPEC = Spec(
    slug="pictet_pdf",
    label="Banque Pictet — Advice PDF",
    corpus="pictetciegruppesa",
    marks=[r"Pictet"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^(?:Purchase|Sale) (?:[A-Z]{3} )?-?" + NUM + r" ", sell=r"^Sale ", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^SECURITY EVENT\n(?:Distribution|Dividend)", fields=DIVIDEND_FIELDS),
    ],
)
