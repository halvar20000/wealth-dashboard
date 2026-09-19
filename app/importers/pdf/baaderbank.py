"""Baader Bank — the settlement bank behind Scalable Capital (until
2024), finanzen.net zero, Smartbroker+ and a few more. One spec reads
them all: the paper carries the broker's logo and Baader's layout.

German and English versions exist ("Wertpapierabrechnung: Kauf" and
"Transaction Statement: Sale"), and the English one writes 2.54 where
the German writes 2,54 — so numbers are read by their last separator.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
CCY = r"(?P<currency>[A-Z]{3})"

FEES = (r"^(?:Provision|Transaktionsgeb.hr|Fremde Spesen|B.rsengeb.hr|Handelsplatzgeb.hr|Ausgabeaufschlag|Maklercourtage|"
        r"Abwicklungsgeb.hr|Commission|Third-party (?:fees|expenses)|Transaction fee|Exchange fee|Brokerage fee) " + CCY +
        r" (?P<fee>" + NUM + r") ?(?P<sign>[-+]?)$")
TAXES = (r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|(?:US-)?Quellensteuer|Finanztransaktionssteuer|"
         r"Capital gains tax|Solidarity surcharge|Church tax|(?:US )?[Ww]ithholding tax|Financial transaction tax) " + CCY +
         r" (?P<tax>" + NUM + r") ?(?P<sign>[-+]?)$")

TRADE_FIELDS = {
    "security": [
        r"^Nominale ISIN: " + ISIN + r" WKN: (?P<wkn>\S+)(?: Kurs)?\n(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")$\n(?P<name2>(?!Auftraggeber|Art der|Kurswert)[^\n]+)?",
        r"^Quantity ISIN: " + ISIN + r" WKN: (?P<wkn>\S+)(?: Price)?\n(?P<notation>Units|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")$\n(?P<name2>(?!Order placed|Method of|Market Value)[^\n]+)?",
        r"^Nominale ISIN: " + ISIN + r" WKN: (?P<wkn>\S+)\n(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+)$",
    ],
    "date": [r"^(?:Handelsdatum Handelsuhrzeit|Trade Date Trade Time)\n(?P<date>\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})",
             r"^(?:Auftragsdatum|Order Date): (?P<date>\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})",
             r"Valuta: (?P<date>\d{2}\.\d{2}\.\d{4})", r"Value: (?P<date>\d{4}-\d{2}-\d{2})"],
    "amount": [r"^Zu (?:Lasten|Gunsten) Konto \S+ Valuta: \S+ " + CCY + r" (?P<amount>" + NUM + r")$",
               r"^Amount (?:debited to|credited to) account \S+ Value: \S+ " + CCY + r" (?P<amount>" + NUM + r")$"],
    "ref": [r"^(?:Vorgangs-Nr\.|Transaction No\.): (?P<ref>\S+)"],
    "fees": [FEES],
    "taxes": [TAXES],
    "fx": [r"^(?:Umrechnungskurs|Exchange rate): (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}

CREDIT_FIELDS = {
    "security": [
        r"^Nominale ISIN: " + ISIN + r" WKN: (?P<wkn>\S+)(?: [A-Za-z.]+)?\n(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?)(?: [A-Z]{3} " + NUM + r" p\.STK)?$",
        r"^Quantity ISIN: " + ISIN + r" WKN: (?P<wkn>\S+)(?: [A-Za-z.]+)?\n(?P<notation>Units|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?)(?: [A-Z]{3} " + NUM + r" (?:p\.|per )?[A-Za-z]+)?$",
    ],
    "date": [r"Valuta: (?P<date>\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})", r"Value: (?P<date>\d{4}-\d{2}-\d{2})",
             r"^(?:Zahltag|Payment date): (?P<date>\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})"],
    "amount": [r"^Zu (?:Gunsten|Lasten) Konto \S+ Valuta: \S+ " + CCY + r" (?P<amount>" + NUM + r")$",
               r"^Amount (?:credited to|debited to) account \S+ Value: \S+ " + CCY + r" (?P<amount>" + NUM + r")$"],
    "ref": [r"^(?:Vorgangs-Nr\.|Transaction No\.): (?P<ref>\S+)"],
    "taxes": [TAXES],
    "fx": TRADE_FIELDS["fx"],
}

SPEC = Spec(
    slug="baader_pdf",
    label="Baader Bank (Scalable, finanzen.net zero, Smartbroker+) — Abrechnung PDF",
    corpus="baaderbank",
    marks=[r"Baader Bank", r"baaderbank\.de", r"Unterschlei.heim"],
    number="auto",
    docs=[
        Doc(kind="skip", when=r"^(?:Storno|Cancellation)\b|Storno der", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^Wertpapierabrechnung: (?:Kauf|Zeichnung)|^Transaction Statement: (?:Purchase|Buy|Subscription)", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Wertpapierabrechnung: (?:Verkauf|R.cknahme|Einl.sung)|^Transaction Statement: (?:Sale|Redemption)", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^(?:Vorabpauschale|Advance lump sum|Steuerausgleichsrechnung)", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zinsabrechnung|Interest Statement)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividendenabrechnung|Ertragsabrechnung|Aussch.ttung|Dividend Statement|Distribution Statement|Fondsaussch.ttung)", fields=CREDIT_FIELDS),
    ],
)
