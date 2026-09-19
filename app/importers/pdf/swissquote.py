"""Swissquote and Yuh — the Transaktionsbeleg for a trade, a dividend,
an incoming or outgoing payment, in German and English, and the
Zinsabrechnung. The hand-written `swissquote_pdf` and
`swissquote_beleg_pdf` readers come first on the import page; this
spec takes the paper they do not know — dividends, the English
notification, derivatives, crypto — and is what the corpus scores."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?P<name>.+?) ISIN: " + ISIN, r"^(?P<name>.+?) (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")$\n"],
    "shares": [r"^(?:Anzahl|Quantity) (?:Preis|Price) (?:Betrag|Amount)\n(?P<shares>" + NUM + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM,
               r"^(?:Bezeichnung|Description) (?:Anzahl|Quantity) (?:Kontraktw.hrung|Contract currency) (?:Preis|Price)\n(?P<name>.+?) (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")$",
               r"^(?:Anzahl|Quantity) (?P<shares>" + NUM + r")$",
               # Crypto: "Anzahl Währung Rate / 0.02 BTC 63'643.9"
               r"^(?:Anzahl|Quantity) (?:W.hrung|Currency) (?:Rate|Kurs)\n(?P<shares>" + NUM + r") (?P<name>[A-Z]{3,5}) (?P<price>" + NUM + r")$"],
    "date": [r"^(?:Gem.ss Ihrem \S+auftrag vom|In accordance with your \w+ order of|Am|On) (?P<date>" + DATE + r")",
             r"^(?:Valutadatum|Value date) (?P<date>" + DATE + r")", r"(?:Valutadatum|on value date of) (?P<date>" + DATE + r")",
             r"^Gland, (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Zu Ihren (?:Lasten|Gunsten)|To your (?:debit|credit)|Total (?:belastet|gutgeschrieben|debited|credited)) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$",
               r"^Total (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$\n(?:Betrag belastet|Betrag gutgeschrieben|Amount (?:debited|credited))"],
    "ref": [r"(?:Unsere Referenz|Our reference): (?P<ref>\d+)"],
    "fees": [r"^(?:Kommission[^\n]*?|Commission[^\n]*?|B.rsengeb.hren|Stock exchange fee|Fremde (?:Geb.hren|Spesen)|Courtage[^\n]*?|Third-party fees) (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Abgabe \(Eidg\. Stempelsteuer\)|Stempelsteuer|Tax \(Federal stamp duty\)|Stamp duty|Umsatzabgabe) (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")$"],
}

DIVIDEND_FIELDS = {
    "security": [r"^(?P<name>.+?) ISIN: " + ISIN],
    "shares": [r"^(?:Anzahl|Quantity) (?P<shares>" + NUM + r")$"],
    "date": [r"^(?:Valutadatum|Value date) (?P<date>" + DATE + r")", r"^Gland, (?P<date>" + DATE + r")"],
    # "Total USD 23.88 CHF 21.48": the security's currency first, the account's after.
    "amount": [r"^Total (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")(?: [A-Z]{3} " + NUM + r")?$"],
    "taxes": [r"^(?:Quellensteuer|Withholding tax|Verrechnungssteuer|Swiss withholding tax|Nicht r.ckforderbare Steuern|Non-recoverable tax|Zus.tzlicher Steuerr.ckbehalt|Additional withholding)[^\n]*? (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")(?: [A-Z]{3}(?: " + NUM + r")?)?$"],
    "ref": [r"(?:Unsere Referenz|Our reference): (?P<ref>\d+)"],
}

PAYMENT_FIELDS = {
    "date": [r"^(?:Valutadatum|Value date) (?P<date>" + DATE + r")", r"^Gland, (?P<date>" + DATE + r")"],
    "amount": [r"^Total (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"(?:Unsere Referenz|Our reference): (?P<ref>\d+)"],
}

INTEREST_ROW = r"^" + DATE + r" " + NUM + r" " + NUM + r" " + NUM + r" " + NUM + r" " + NUM
INTEREST_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^(?P<type>" + DATE + r") "],
    "amount": [r"^" + DATE + r" " + NUM + r" " + NUM + r" " + NUM + r" " + NUM + r" (?P<amount>" + NUM + r")"],
    "taxes": [r"^" + DATE + r" " + NUM + r" " + NUM + r" " + NUM + r" (?P<tax>" + NUM + r") "],
}

SPEC = Spec(
    slug="swissquote_spec_pdf",
    label="Swissquote / Yuh — Transaktionsbeleg PDF",
    corpus="swissquote",
    marks=[r"Swissquote", r"Yuh"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^(?:B.rsentransaktion|Derivatetransaktion|Kryptotransaktion|Stock-Exchange Transaction|Derivative transaction|Crypto transaction|Sell|Buy|Kauf|Verkauf)\b",
            sell=r"^(?:B.rsentransaktion|Derivatetransaktion|Kryptotransaktion|Stock-Exchange Transaction|Derivative transaction|Crypto transaction)?:? ?(?:Verkauf|Sell)\b|^Zu Ihren Gunsten|^To your credit|^Betrag gutgeschrieben",
            fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividende|Dividend|Aussch.ttung|Distribution|Kapitalr.ckzahlung|Kapitalgewinn|Capital (?:repayment|gain)|Option Premium|Optionspr.mie) (?:Unsere Referenz|Our reference)", fields=DIVIDEND_FIELDS),
        Doc(kind="fee", when=r"^(?:Depotgeb.hren|Custody fees|Geb.hren|Fees) (?:Unsere Referenz|Our reference)", fields={
            **PAYMENT_FIELDS, "amount": [r"^(?:Betrag belastet|Amount debited|Total) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"]}),
        Doc(kind="deposit", when=r"^(?:Zahlungsverkehr - Gutschrift|Payment - Credit|Eingehende .berweisung|Incoming transfer)", fields=PAYMENT_FIELDS),
        Doc(kind="withdrawal", when=r"^(?:Zahlungsverkehr - Belastung|Payment - Debit|Ausgehende .berweisung|Outgoing transfer)", fields=PAYMENT_FIELDS),
        Doc(kind="rows", when=r"^(?:Zinsabrechnung|Interest statement)", block=INTEREST_ROW, fields=INTEREST_FIELDS, kinds={r".": "interest"}),
    ],
)
