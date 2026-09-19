"""ING (Germany) — Wertpapierabrechnung, Dividendengutschrift."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"

TRADE_FIELDS = {
    "security": [r"^ISIN \(WKN\) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)\nWertpapierbezeichnung (?P<name>.+)\n(?P<name2>.+)\nNominale"],
    "shares": [r"^Nominale (?P<notation>St.ck|[A-Z]{3}) (?P<shares>" + NUM + r")",
               r"^Nominale (?P<shares>" + NUM + r") (?P<notation>St.ck|[A-Z]{3})"],
    "price": [r"^Kurs (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Ausf.hrungstag(?: / -zeit)? (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"^Schlusstag (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"^Datum: (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^Endbetrag zu Ihren (?:Lasten|Gunsten) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
               r"^Endbetrag (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Ordernummer (?P<ref>\S+)"],
    "fees": [r"^(?:Provision|Handelsplatzgeb.hr|Handelsentgelt|Kurswertgeb.hr|B.rsengeb.hr|Transaktionsentgelt|Fremde Spesen|Ausgabeaufschlag|Rabatt auf Ausgabeaufschlag)(?: \S+)*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer)(?: \S+)*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

DIVIDEND_FIELDS = {
    "security": [r"^ISIN \(WKN\) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)\nWertpapierbezeichnung (?P<name>.+)\n(?P<name2>.+)\nNominale",
                 r"^ISIN \(WKN\) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)\nWertpapierbezeichnung (?P<name>.+)"],
    "shares": [r"^Nominale (?P<shares>" + NUM + r") (?P<notation>St.ck|[A-Z]{3})",
               r"^Nominale (?P<notation>St.ck|[A-Z]{3}) (?P<shares>" + NUM + r")"],
    "date": [r"^Valuta (?P<date>\d{2}\.\d{2}\.\d{4})", r"^Zahltag (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"^Datum: (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^Gesamtbetrag zu Ihren Gunsten (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
               r"^Gesamtbetrag zu Ihren Lasten (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer)(?: \S+)*? (?P<currency>[A-Z]{3}) (?P<sign>-?) ?(?P<tax>" + NUM + r")$",
              # Withholding tax abroad, with its euro value in brackets:
              # "QuSt 35,00 % (EUR 31,34) CHF 33,69"
              r"^QuSt [\d,]+ % \((?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")\)",
              r"^QuSt [\d,]+ % (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")$"],
}

TAX_FIELDS = {**DIVIDEND_FIELDS,
              "amount": [r"^Gesamtbetrag zu Ihren Lasten (?P<currency>[A-Z]{3}) (?P<amount>-? ?" + NUM + r")"]}

SPEC = Spec(
    slug="ing_pdf",
    label="ING — Wertpapierabrechnung PDF",
    corpus="ingdiba",
    marks=[r"ING-DiBa AG", r"\bING\b.*Frankfurt", r"INGDDEFFXXX"],
    docs=[
        Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^Wertpapierabrechnung (?:Kauf|Bezug|Ausf.hrung)", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Wertpapierabrechnung (?:Verk|R.cknahme|Einl.sung)|^R.ckzahlung$", fields=TRADE_FIELDS),
        # The account statements: one row per booking, the date twice
        # (booking and value) and the purpose on the lines between.
        Doc(kind="rows", when=r"^Kontoauszug (?:Januar|Februar|M.rz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) \d{4}",
            block=r"^\d{2}\.\d{2}\.\d{4} (?!Neuer Saldo)\S.* -?[\d.]+,\d{2}$",
            fields={
                "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) "],
                "amount": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>\S+) (?P<name>.*?) ?(?P<amount>-?[\d.]+,\d{2})$"],
                "type": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>\S+) "],
            },
            kinds={r"^Zins": "interest", r"^Entgelt|^Geb": "fee"}),
        Doc(kind="tax", when=r"^Vorabpauschale per St.ck", fields=TAX_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividendengutschrift|Ertragsgutschrift|Zinsgutschrift)", fields=DIVIDEND_FIELDS),
    ],
)
