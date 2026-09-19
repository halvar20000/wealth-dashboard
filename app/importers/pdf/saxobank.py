"""Saxo Bank — the Trade Details, Corporate Action, Cash Transfer and
Cash Amount reports, in German and English. Every report books in the
account's currency, named in its header; a trade in another currency
carries the rate and the conversion cost."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"-?[\d.,']+"
DATE = r"\d{2}-[A-Za-zä]{3,4}-\d{4}"

CURRENCY = [r"(?:W.hrung|Currency): (?P<currency>[A-Z]{3})"]

TRADE_FIELDS = {
    "security": [r"^Instrument (?P<name>.+?) (?:Handelszeit|Trade time) (?P<date>" + DATE + r")", r"^ISIN " + ISIN],
    "shares": [r"(?:Menge|Quantity) (?P<shares>" + NUM + r")"],
    "price": [r"(?:Preis|Price) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"(?:Handelszeit|Trade time) (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Nettobetrag|Net Amount) - - - - - " + NUM + r" (?P<amount>" + NUM + r")$"],
    "ref": [r"(?:Order-ID|Order ID) (?P<ref>\d+)"],
    "type": CURRENCY,
    "fees": [r"^(?:Gesamte Trading-Kosten|Total Trading Costs) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$",
             r"^(?:Umrechnungskosten|Conversion cost)[^\n]*? (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Stempelgeb.hr|Stamp duty|Steuer|Tax)[^\n]*? \d+ " + DATE + r" " + DATE + r" " + NUM + r" " + NUM + r" " + NUM + r" (?P<tax>" + NUM + r")$"],
}

DIVIDEND_FIELDS = {
    "security": [r"^ISIN " + ISIN, r"^(?:Description|Beschreibung) (?P<name>.+?) (?:Dividend per share|Dividende pro Aktie)"],
    "shares": [r"(?:Eligible quantity|Berechtigte Menge) (?P<shares>" + NUM + r")"],
    "date": [r"^\S.* \d+ " + DATE + r" " + DATE + r" " + DATE + r" (?P<date>" + DATE + r") " + NUM + r" " + NUM + r" " + NUM + r"$",
             r"(?:Pay Date|Zahlungsdatum) (?P<date>" + DATE + r")", r"(?:Reporting period|Berichtszeitraum)\n(?P<date>" + DATE + r")"],
    "amount": [r"(?:Cash Dividends|Bardividenden) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "type": CURRENCY,
}
# The tax stands beside the gross; the net is the difference.
WITHHOLDING = {"taxes": [r"(?:Withholding Tax|Quellensteuer) (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"]}

STATEMENT_ROW = r"^" + DATE + r" " + DATE + r" (?:DEPOSIT|WITHDRAWAL|EINZAHLUNG|AUSZAHLUNG|Einlage|Deposit)\b"
STATEMENT_FIELDS = {
    "date": [r"^" + DATE + r" (?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" " + DATE + r" (?P<type>\S+)"],
    "amount": [r"^" + DATE + r" " + DATE + r" \S+ \([^)]*\) (?P<amount>" + NUM + r") " + NUM + r"$"],
}

CASH_ROW = r"^(?:Einlage|Deposit|Auszahlung|Withdrawal|Einzahlung|Cash Transfer|Bargeldtransfer|Transfer)\S* \d+ " + DATE
CASH_FIELDS = {
    "date": [r"^\S+ \d+ (?P<date>" + DATE + r") "],
    "amount": [r"^(?P<type>\S+) \d+ " + DATE + r" " + DATE + r" " + NUM + r" " + NUM + r" " + NUM + r" (?P<amount>" + NUM + r")$"],
    "type": [r"^(?P<type>\S+) \d+ " + DATE],
}

INTEREST_FIELDS = {
    "date": [r"^(?:Interest|Zinsen) \d+ (?P<date>" + DATE + r") "],
    "amount": [r"^(?:Interest|Zinsen) \d+ " + DATE + r" (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3}) " + NUM + r" " + NUM + r"$"],
}

SPEC = Spec(
    slug="saxobank_pdf",
    label="Saxo Bank — Report PDF",
    corpus="saxobank",
    marks=[r"Saxo Bank", r"saxobank\.com"],
    number="auto",
    docs=[
        Doc(kind="trade", when=r"^(?:Trade Details Report|Trade details, [A-Z]{3}|Handelsdetails)", sell=r"^(?:K/V Verkauf|B/S Sell)", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Corporate Action Detail|Kapitalma.nahme)", fields=DIVIDEND_FIELDS),
        Doc(kind="tax", when=r"(?:Withholding Tax|Quellensteuer) " + NUM + r" [A-Z]{3}$", fields=WITHHOLDING, also=True, merge=True),
        Doc(kind="rows", when=r"^Kontoauszug, ", block=STATEMENT_ROW, fields=STATEMENT_FIELDS,
            kinds={r"WITHDRAWAL|AUSZAHLUNG": "withdrawal", r".": "deposit"}),
        Doc(kind="rows", when=r"^(?:Cash Transfer Details|Bargeldtransfer)", block=CASH_ROW, fields=CASH_FIELDS,
            kinds={r"Auszahlung|Withdrawal": "withdrawal", r".": "deposit"}),
        Doc(kind="interest", when=r"^(?:Cash Amount Details|Barbetrag)", fields=INTEREST_FIELDS),
    ],
)
