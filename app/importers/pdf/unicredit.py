"""UniCredit / HypoVereinsbank — the Geschäftsbestätigung of a trade
and the Wertpapiermitteilung of a distribution, old paper whose
umlauts come out as braces."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^Nennbetrag Wertpapierbezeichnung Wertpapierkennnummer/ISIN\n(?P<name>.+?) [A-Z0-9]{6}\n(?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r")\n(?P<name2>.+?) " + ISIN,
                 r"^(?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) [A-Z0-9]{6} (?P<name2>.+?) " + ISIN + r"$",
                 r"^(?P<name>.+?) " + ISIN + r"$"],
    "shares": [r"^(?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r")(?: |$)"],
    "price": [r"^(?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r") (?:(?P<date>" + DATE + r") )?\S+ "],
    "date": [r"^Zum Kurs von Ausf.hrungstag/Zeit[^\n]*\n(?:[A-Z]{3} " + NUM + r" )?(?P<date>" + DATE + r")", r"^Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Belastung|Gutschrift) \(vor Steuern\) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Umsatzreferenz: (?P<ref>\S+)"],
    "fees": [r"^(?:Brokerkommission|Transaktionsentgelt|Provision|Wertpapierprovision|B.rsengeb.hr|Fremde Spesen|Courtage)\*? (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")$"],
}
DIVIDEND_FIELDS = {
    "security": [r"^(?P<name>.+?) Wertpapierkennnummer [A-Z0-9]{6} / " + ISIN],
    "shares": [r"^St.ck (?P<shares>" + NUM + r")"],
    "date": [r"^Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Valuta " + DATE + r" Gutschrift (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Referenz (?P<ref>\S+)"],
}

SPEC = Spec(
    slug="unicredit_pdf",
    label="UniCredit / HypoVereinsbank — Abrechnung PDF",
    corpus="unicredit",
    marks=[r"UniCredit", r"HypoVereinsbank", r"Gesch.ftsbest.tigung vor steuerlicher Behandlung", r"Wertpapiermitteilung"],
    docs=[
        Doc(kind="trade", when=r"^- Gesch.ftsbest.tigung", sell=r"^Gutschrift \(vor Steuern\)", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Wertpapiermitteilung - Ertragszahlung", fields=DIVIDEND_FIELDS),
    ],
)
