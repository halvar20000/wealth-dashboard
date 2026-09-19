"""TARGOBANK — Effektenabrechnung, Ertragsgutschrift, Steuerbeilage.

The tax comes on a separate Steuerbeilage that names the same
security and ex-date; it is booked as its own tax row.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"
LONG = r"(?P<date>\d{1,2}\. [A-Za-zä]+ \d{4})"

COMMON = {
    "security": [r"^Wertpapier (?P<name>.+)\nWKN / ISIN (?P<wkn>\S+) / " + ISIN],
    "shares": [r"^St.ck (?P<shares>" + NUM + r")$", r"^Nominal (?P<shares>" + NUM + r") (?P<notation>[A-Z]{3})$"],
    "ref": [r"^Rechnungsnummer: (?P<ref>\S+)", r"^Transaktionsreferenz (?P<ref>\S+)"],
    "fees": [r"^(?:Provision|Handelsplatzentgelt|B.rsengeb.hr|Fremde Spesen|Transaktionsentgelt|Ausgabeaufschlag|Maklercourtage) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer)(?: \S+ %)? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$",
              r"^\d+ % Ausl.ndische Quellensteuer(?: \([A-Z]+\))? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$",
              r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer) (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")$"],
}
TRADE_FIELDS = {**COMMON,
    "price": [r"^Kurs (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}|%)"],
    "date": [r"^Schlusstag(?: / Handelszeit)? " + DATE, r"mit Wertstellung zum " + LONG],
    "amount": [r"^(?:Belastung Ihres Kontos|Gutschrift auf Ihrem Konto) mit Wertstellung zum [^\n]+\n(?:Konto-Nr\. \S+ )?(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}
CREDIT_FIELDS = {**COMMON,
    "date": [r"^Zahlbar " + DATE, r"mit Wertstellung zum " + LONG, r"^(?:Ertragsgutschrift|Dividendengutschrift|Zinsgutschrift)(?: \(Steuerbeilage\))? " + DATE],
    "amount": [r"^(?:Belastung Ihres Kontos|Gutschrift auf Ihrem Konto) mit Wertstellung zum [^\n]+\n(?:Konto-Nr\. \S+ )?(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}
TAX_PAGE_FIELDS = {**COMMON,
    "date": [r"^Ex-Tag " + DATE, r"mit Wertstellung zum " + LONG, r"\(Steuerbeilage\) " + DATE],
    "amount": [r"^Gesamtsumme Steuern (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Kapitalertragsteuer \(KESt\)|Solidarit.tszuschlag auf KESt|Kirchensteuer auf KESt): (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="targobank_pdf",
    label="TARGOBANK — Effektenabrechnung PDF",
    corpus="targobank",
    marks=[r"TARGOBANK", r"targobank\.de"],
    docs=[
        Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="tax", when=r"\(Steuerbeilage\)", fields=TAX_PAGE_FIELDS),
        Doc(kind="buy", when=r"^Transaktionstyp Kauf", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Transaktionstyp Verkauf", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^Zinsgutschrift", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsgutschrift|Dividendengutschrift)", fields=CREDIT_FIELDS),
    ],
)
