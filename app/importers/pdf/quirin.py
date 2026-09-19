"""Quirin Privatbank / quirion — the Wertpapierabrechnung, the
Erträgnisabrechnung (a dividend, or a Vorabpauschale that only taxes),
and the Kontoauszug, one line per booking with two dates and a signed
amount. Trades and distributions listed on the statement have their
own paper and are left to it; what the statement gives is the money
in and out, the fees, the taxes, the interest."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^Wertpapierbezeichnung (?P<name>.+)\n(?:(?P<name2>.+)\n)?ISIN " + ISIN,
                 # The 2014 layout: "Nominal/Stück <name>" over "ST 31 ISIN … WKN …"
                 r"^Nominal/St.ck (?P<name>.+)\n(?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r") ISIN " + ISIN],
    "shares": [r"^Nominal ?/ ?St.ck (?P<shares>" + NUM + r") (?P<notation>ST|[A-Z]{3})"],
    "price": [r"^Kurs (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")", r"^Kurs (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^Handelstag ?/ ?(?:Zeit|-zeit) (?P<date>" + DATE + r")", r"^Zahlungstag (?P<date>" + DATE + r")", r"mit Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Ausmachender Betrag (?P<currency>[A-Z]{3}) (?P<amount>-? ?" + NUM + r")",
               r"Ausmac ?hender Betrag(?: vor Steuer(?:n|\(n\))?)? (?P<amount>-?" + NUM + r") (?P<currency>EUR)"],
    "ref": [r"^Referenz(?:-Nr)? (?P<ref>\S+)"],
    "fees": [r"^(?:Abwicklungsgeb.hren|Abwickl\.Geb.hr|Bank-Provision|Courtage|Spesen|Provision|Fremde Spesen|Maklercourtage|Mehrwertsteuer \(\d+%\))(?: \*)? (?P<currency>[A-Z]{3}) (?P<sign>-?) ?(?P<fee>" + NUM + r")$",
             r"(?:Abwickl\.Geb.hr|Bank-Provision|Courtage|Spesen|Mehrwertsteuer \(\d+%\))(?: \*)? (?P<sign>-?)(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer|Abgeltungsteuer)(?: \*)? (?P<currency>[A-Z]{3}) (?P<sign>-?) ?(?P<tax>" + NUM + r")$"],
}

ROW = r"^\S.* " + DATE + r" " + DATE + r" -?" + NUM + r" [A-Z]{3}$"
ROW_FIELDS = {
    "date": [r"^.* " + DATE + r" (?P<date>" + DATE + r") -?" + NUM + r" [A-Z]{3}$"],
    "amount": [r"^(?P<type>.*?) " + DATE + r" " + DATE + r" (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "type": [r"^(?P<type>.*?) " + DATE + r" " + DATE + r" -?" + NUM + r" [A-Z]{3}$"],
    "ref": [r"Ref\.?: ?(?P<ref>[A-Z]*-?\d+)"],
}

SPEC = Spec(
    slug="quirin_pdf",
    label="Quirin Privatbank / quirion — Abrechnung PDF",
    corpus="quirinbankag",
    marks=[r"quirin ?bank", r"Quirin Privatbank", r"quirinprivatbank\.de", r"quirion"],
    docs=[
        Doc(kind="trade", when=r"^(?:Wertpapierabrechnung\n)?(?:Kauf|Verkauf)(?: \([^)]*\))?\n", sell=r"^(?:Wertpapierabrechnung\n)?Verkauf(?: \([^)]*\))?\n", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale \(nicht gebucht\)", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertr.gnisabrechnung|Ertrag aus Investments|Dividende)", fields=TRADE_FIELDS),
        # The 2010–2014 paper: the gross, and the tax on a line of its own.
        Doc(kind="tax", when=r"Steuerbetrag -?" + NUM + r" ", also=True, merge=True, fields={
            "taxes": [r"Steuerbetrag (?:-?" + NUM + r" [A-Z]{3} )?(?P<sign>-?)(?P<tax>" + NUM + r") (?P<currency>EUR)"]}),
        Doc(kind="rows", when=r"^Kontoauszug", block=ROW, fields=ROW_FIELDS,
            kinds={r"^Wertpapier |Thesaurierung|Ertr.gnisabrechnung|Zins-/Dividendenzahlung|^Wertpapiere,": "skip",
                   r"Steuer": "tax", r"honorar|Honorar|provision|Flatrate|Fee|Geb.hr|Entgelt": "fee", r"^Zins": "interest",
                   r"gutschrift|Kontoübertrag|Interne Buchung|Aufstockung": "deposit", r"überweisung|.berweisungsauftrag": "withdrawal"}),
    ],
)

# V-Bank prints the same paper with its own letterhead.
VBANK = Spec(slug="vbank_pdf", label="V-Bank — Abrechnung PDF", corpus="vbankag",
             marks=[r"V-Bank", r"VBANDEMM"], docs=SPEC.docs)
SPECS = [SPEC, VBANK]
