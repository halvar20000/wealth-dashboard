"""Consorsbank (and Cortal Consors before it) — Wertpapierabrechnung,
Ertragsgutschrift, Vorabpauschale, Kontoauszug.

Two generations of paper: the old one shouts ("KAUF AM 15.01.2015 UM
08:13:35 MUENCHEN", "PROVISION EUR 8,26"), the new one writes
"Preis pro Anteil 332,85 EUR" with the currency after the number. The
anchors below take both, currency before or after.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
AMT_AFTER = r"(?P<amount>" + NUM + r")-? (?P<currency>[A-Z]{3})"       # 200,00 EUR
AMT_BEFORE = r"(?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")-?"      # EUR 200,00

FEE_WORDS = (r"(?:abzgl\. )?(?:Provision|PROVISION|Grundgeb.hr|GRUNDGEBUEHR|B.rsenplatzgeb.hr|Handelsplatzkosten|"
             r"Transaktionsentgelt|Eig\. Spesen|EIG\. SPESEN|Fremde Spesen|Courtage|Maklercourtage|Ausgabeaufschlag|"
             r"Handelsentgelt|Abwicklungsentgelt)")
TAX_WORDS = r"(?:abzgl\. )?(?:Kapitalertragsteuer|KAPST|Solidarit.tszuschlag|SOLZ|Kirchensteuer|KIST|Quellensteuer|QUST|Finanztransaktionssteuer)"

TRADE_FIELDS = {
    "security": [
        r"^(?:Wertpapier|Bezeichnung) WKN ISIN\n(?P<name>.+?) (?P<wkn>[A-Z0-9]{6}) " + ISIN + r"$",
        r"^ST " + NUM + r" WKN: (?P<wkn>[A-Z0-9]{6})\n(?P<name>.+)$",
        r"^(?P<notation>[A-Z]{3}) " + NUM + r" WKN: (?P<wkn>[A-Z0-9]{6})\n(?P<name>.+)$",
    ],
    "shares": [r"^(?P<notation>ST|[A-Z]{3}) (?P<shares>" + NUM + r")\b"],
    "price": [r"^(?:Kurs|Preis pro Anteil|Preis pro St.ck|Nettoinventarwert) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}|%)"],
    "date": [r"^(?:KAUF|Verkauf|VERKAUF|Kauf|BEZUG|Bezug|R.CKNAHME|EINLOESUNG|Einl.sung) AM (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"^Datum: (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [
        r"^(?:WERT|Wert|Valuta) \d{2}\.\d{2}\.\d{4} " + AMT_BEFORE + r"$",
        r"^zu(?:lasten|gunsten) Konto-Nr\. \S+ " + AMT_AFTER + r"$",
        r"^(?:Netto|Ausmachender Betrag) zu(?:lasten|gunsten) IBAN \S+(?: \S+)* " + AMT_AFTER + r"$",
    ],
    "ref": [r"NR\. ?(?P<ref>[\d.]+)$", r"^Ordernummer (?P<ref>\S+)"],
    "fees": [r"^" + FEE_WORDS + r"(?: [\d,]+ %)? (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")(?P<sign>[-+]?)$",
             r"^" + FEE_WORDS + r"(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<fee>" + NUM + r")(?P<sign>[-+]?) (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^" + TAX_WORDS + r"(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")(?P<sign>[-+]?)$",
              r"^" + TAX_WORDS + r"(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<tax>" + NUM + r")(?P<sign>[-+]?) (?P<currency>[A-Z]{3})$"],
    "fx": [r"^Devisenkurs (?P<fx_rate>" + NUM + r") (?P<fx_pair>[A-Z]{3} ?/ ?[A-Z]{3})"],
}

# A withholding tax printed in dollars and again "in EUR": only the
# euro line counts, so the dollar line is taken only when no euro line
# follows it anywhere in the document.
CREDIT_TAXES = [
    # "QUST 15,00000 % EUR 24,45 USD 27,00": the euro figure, printed first.
    r"^QUST [\d,]+ % (?P<currency>EUR) (?P<tax>" + NUM + r") [A-Z]{3} " + NUM + r"$",
    r"^" + TAX_WORDS + r"(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")(?P<sign>[-+]?)$",
    r"^(?:Quellensteuer|Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer) in (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r") [A-Z]{3}$",
    r"^" + TAX_WORDS + r"(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<tax>" + NUM + r")(?P<sign>[-+]?) (?P<currency>EUR)$",
    r"^abzgl\. Quellensteuer(?: [\d,]+ %)?(?: von " + NUM + r" [A-Z]{3})? (?P<tax>" + NUM + r") (?P<currency>(?!EUR)[A-Z]{3})$(?![\s\S]*^Quellensteuer in EUR)",
]

CREDIT_FIELDS = {
    "security": [r"^Wertpapierbezeichnung WKN ISIN\n(?P<name>.+?) (?P<wkn>[A-Z0-9]{6}) " + ISIN + r"$",
                 r"^(?:ST|St.ck) " + NUM + r" WKN: (?P<wkn>[A-Z0-9]{6})\n ?(?P<name>.+)\n ?(?P<name2>.+)$",
                 r"^(?:ST|St.ck) " + NUM + r" WKN: (?P<wkn>[A-Z0-9]{6})\n ?(?P<name>.+)$"],
    "shares": [r"^(?P<shares>" + NUM + r") (?P<notation>St.ck)\b", r"^(?P<notation>ST) (?P<shares>" + NUM + r")\b"],
    "date": [r"^Valuta (?P<date>\d{2}\.\d{2}\.\d{4})", r"^WERT (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"^Datum: (?P<date>\d{2}\.\d{2}\.\d{4})", r"^NUERNBERG, (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^Netto zu(?:gunsten|lasten) IBAN \S+(?: \S+)* " + AMT_AFTER + r"$",
               r"^Netto zu(?:gunsten|lasten) Konto-Nr\. \S+ " + AMT_AFTER + r"$",
               # The newest layout puts the figure on the line above its label.
               r"^" + AMT_AFTER + r"\nNetto zu(?:gunsten|lasten) IBAN",
               r"^WERT \d{2}\.\d{2}\.\d{4} " + AMT_BEFORE + r"$",
               r"^Netto (?:in [A-Z]{3} )?" + AMT_AFTER + r"$"],
    "ref": [r"^Abrechnungsnr\.? ?:? ?(?P<ref>\S+)"],
    "taxes": CREDIT_TAXES,
    "fx": TRADE_FIELDS["fx"],
}

# The Verrechnungskonto statement: a booking line, then its text.
#   ZINS/DIVID. 10.12. 8809 09.12. 11,66+
#   EURO-UEBERW. 21.12. 8420 21.12. 6.000,00-
ROW = r"^(?P<type>[A-ZÄÖÜ][A-ZÄÖÜ./ -]+?) (?P<day>\d{2}\.\d{2}\.) \d{4} \d{2}\.\d{2}\. (?P<amount>" + NUM + r")(?P<sign>[+-])$"
STATEMENT_FIELDS = {
    "date": [r"^[A-ZÄÖÜ][A-ZÄÖÜ./ -]+? (?P<date>\d{2}\.\d{2}\.\d{2,4})\b"],
    "amount": [ROW],
    "type": [ROW],
}

def docs() -> list:
    return [
        Doc(kind="skip", when=r"^Storno\b|STORNO", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^(?:KAUF|Kauf|BEZUG|Bezug|Anschaffung) AM \d{2}\.\d{2}\.\d{4}", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^(?:VERKAUF|Verkauf|R.CKNAHME|R.cknahme|EINLOESUNG|Einl.sung) AM \d{2}\.\d{2}\.\d{4}", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale$", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zinsgutschrift|ZINSGUTSCHRIFT)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsgutschrift|Dividendengutschrift|DIVIDENDENGUTSCHRIFT|ERTRAGSGUTSCHRIFT|Ertr.gnisgutschrift)", fields=CREDIT_FIELDS),
        Doc(kind="rows", when=r"^Text/Verwendungszweck Datum PNNr Wert Soll Haben", block=ROW, fields=STATEMENT_FIELDS,
            kinds={r"ZINS/DIVID": "dividend", r"^ZINSEN|ZINSABSCHL": "interest", r"GEB.HR|ENTGELT|KOSTEN": "fee",
                   r"STEUER|KAPST|SOLZ": "tax", r"EFFEKTEN|WP-": "transfer"}),
    ]


SPEC = Spec(
    slug="consorsbank_pdf",
    label="Consorsbank — Abrechnung PDF",
    corpus="consorsbank",
    marks=[r"Consorsbank", r"Cortal Consors", r"CSDBDE71"],
    docs=docs(),
)
