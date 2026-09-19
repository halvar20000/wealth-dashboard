"""Deutsche Bank (Privat- und Geschäftskunden) — Abrechnung, Ertragsgutschrift."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"
LONG = r"(?P<date>\d{1,2}\. [A-Za-zä]+ \d{4})"

TRADE_FIELDS = {
    "security": [r"^Filialnummer Depotnummer Wertpapierbezeichnung Seite\n\S+ \S+ \S+ (?P<name>.+)\nWKN (?P<wkn>\S+) Nominal (?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r")\nISIN " + ISIN,
                 r"^WKN (?P<wkn>\S+) Nominal (?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r")\nISIN " + ISIN],
    "price": [r"^ISIN \S+ Kurs (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")"],
    "date": [r"Schlusstag/-zeit \S+ " + DATE, r"mit Wertstellung " + DATE],
    "amount": [r"^Buchung auf Kontonummer .*? mit Wertstellung \d{2}\.\d{2}\.\d{4} (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")$"],
    "ref": [r"^Belegnummer (?P<ref>\S+ / \S+)"],
    "fees": [r"^(?:Provision|Weitere Provision .*?|XETRA-Kosten|B.rsenplatzgeb.hr|Fremde Spesen|Maklercourtage|Transaktionsentgelt|Ausgabeaufschlag|Abwicklungsgeb.hr) (?P<currency>[A-Z]{3}) -?(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer)(?: .*?)? (?P<currency>[A-Z]{3}) -?(?P<tax>" + NUM + r")$"],
    "fx": [r"^Umrechnungskurs (?P<fx_quote>[A-Z]{3}) zu (?P<fx_base>[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
CREDIT_FIELDS = {
    "security": [r"^St.ck WKN ISIN\n(?P<shares>" + NUM + r") (?P<wkn>\S+) " + ISIN + r"\n(?P<name>.+)$",
                 r"^Nominal WKN ISIN\n(?P<notation>[A-Z]{3}) (?P<shares>" + NUM + r") (?P<wkn>\S+) " + ISIN + r"\n(?P<name>.+)$"],
    "date": [r"^Gutschrift mit Wert " + DATE, r"^Belastung mit Wert " + DATE, r"Zahlbar " + DATE],
    "amount": [r"^(?:Gutschrift|Belastung) mit Wert \d{2}\.\d{2}\.\d{4} (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    # "Kapitalertragsteuer (KESt) - 9,88 USD - 8,71 EUR": the euro figure
    # is the last one on the line.
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer|Einbehaltene Quellensteuer)\b[^\n]*? -? ?(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$",
              # Withheld abroad before the bank saw the money: not on
              # the bank's own tax lines, but gone from the credit.
              r"^Anrechenbare ausl.ndische Quellensteuer (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="deutschebank_pdf",
    label="Deutsche Bank — Abrechnung PDF",
    corpus="deutschebank",
    marks=[r"Deutsche Bank Privat- und Gesch.ftskunden", r"Deutsche Bank AG", r"DEUTDE"],
    docs=[
        Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^Abrechnung: Kauf von Wertpapieren", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Abrechnung: Verkauf von Wertpapieren|^Abrechnung: (?:R.ckzahlung|Einl.sung)", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zinsgutschrift|Kupongutschrift)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsgutschrift|Dividendengutschrift)\s*$", fields=CREDIT_FIELDS),
    ],
)
