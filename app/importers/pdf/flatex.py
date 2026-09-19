"""flatex / flatexDEGIRO / FinTech Group Bank / biw — Wertpapierabrechnung,
Sammelabrechnung, Ertragsmitteilung, Kontoauszug.

Three generations of the same paper. The transaction line is the
anchor in all of them — `Nr.230975068/1 Kauf FRAPORT AG (XS…/A3E444)`
— and a Sammelabrechnung is just several of those lines, so every
trade doc is cut at that line. Labels appear with a colon in the new
paper ("Kurswert : 1.690,00 EUR") and without in the old one
("Kurswert EUR 1.050,00"), currency before or after the figure.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
# "Label : 1.234,56 EUR" or "Label EUR 1.234,56" or "Label : EUR 1.234,56"
def money(label: str, group: str) -> list[str]:
    return [
        r"^" + label + r" ?:? (?P<" + group + r">-?" + NUM + r") (?P<currency>[A-Z]{3})\b",
        r"^" + label + r" ?:? (?P<currency>[A-Z]{3}) (?P<" + group + r">-?" + NUM + r")\b",
    ]

TRADE_LINE = r"^Nr\.\S+ (?:Kauf|Verkauf|Zeichnung|Tilgung|R.cknahme|Einl.sung|Ausbuchung|Kupon)"

TRADE_FIELDS = {
    "security": [r"^Nr\.\S+ (?:Kauf|Verkauf|Zeichnung|Tilgung|R.cknahme|Einl.sung) (?P<name>.+?) \(" + ISIN + r"/(?P<wkn>[A-Z0-9]{6})\)"],
    "shares": [r"^(?:Ausgef.hrt|davon ausgef\.) ?:? (?P<shares>" + NUM + r") (?P<notation>St\.|[A-Z]{3})(?=\s|$)",
               r"\bdavon ausgef\. ?:? (?P<shares>" + NUM + r") (?P<notation>St\.|[A-Z]{3})(?=\s|$)",
               r"^Ausgef.hrt ?:? (?P<notation>[A-Z]{3}) (?P<shares>" + NUM + r")\b",
               r"^Ausgef.hrt ?:? (?P<shares>" + NUM + r")\b"],
    "price": [r"^Kurs ?:? (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}|%)",
              r"^Kurs ?:? (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"\b(?:Handelstag|Schlusstag) ?:? ?(?P<date>\d{2}\.\d{2}\.\d{4})", r"\bValuta ?:? ?(?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"\bEndbetrag ?:? (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})\b",
               r"\bEndbetrag ?:? (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")\b",
               r"^Endbetrag ?:? (?P<amount>-?" + NUM + r")$"],
    "ref": [r"^Nr\.(?P<ref>\S+) "],
    # Courtage, Tradinggebühr and Regulierung are the parts of "Fremde
    # Spesen", listed underneath it — not charges of their own.
    "fees": [r"\b(?:Provision|Eigene Spesen|\*?Fremde Spesen|Transaktionsentgelt|Ausgabeaufschlag|B.rsengeb.hr|Maklercourtage|Fremde Geb.hren) ?:? (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})\b",
             r"\b(?:Provision|Eigene Spesen|\*?Fremde Spesen|Transaktionsentgelt|Ausgabeaufschlag|B.rsengeb.hr|Maklercourtage|Fremde Geb.hren) ?:? (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")\b"],
    "taxes": [r"\*?\*?Einbeh\. Steuer ?:? (?P<tax>-?" + NUM + r") (?P<currency>[A-Z]{3})\b",
              r"\*?\*?Einbeh\. Steuer ?:? (?P<currency>[A-Z]{3}) (?P<tax>-?" + NUM + r")\b",
              r"\b(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer|Finanztransaktionssteuer) ?:? (?P<tax>-?" + NUM + r") (?P<currency>[A-Z]{3})\b"],
    "fx": [r"Devisenkurs ?:? (?P<fx_rate>" + NUM + r")(?: (?P<fx_pair>[A-Z]{3}/[A-Z]{3}))?"],
}

CREDIT_FIELDS = {
    "security": [r"^Nr\.\S+ (?P<name>.+?) \(" + ISIN + r"/(?P<wkn>[A-Z0-9]{6})\)"],
    "shares": [r"^St\. ?: (?P<shares>" + NUM + r")\b", r"^(?:Nominal|St\.) ?:? (?P<shares>" + NUM + r") (?P<notation>St\.|[A-Z]{3})?"],
    "date": [r"^Valuta ?: (?P<date>\d{2}\.\d{2}\.\d{4})", r"\bValuta (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": money(r"Endbetrag", "amount"),
    "ref": [r"^Nr\.(?P<ref>\S+) "],
    "taxes": TRADE_FIELDS["taxes"],
    "fx": TRADE_FIELDS["fx"],
}

# Kontoauszug rows: "07.07. 08.07. Überweisung 200,00+"
ROW = r"^(?P<day>\d{2}\.\d{2}\.) \d{2}\.\d{2}\. (?P<type>.+?) (?P<amount>" + NUM + r")(?P<sign>[+-])$"
STATEMENT_FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.) \d{2}\.\d{2}\. "],
    "year": [r"^Kontoauszug Nr: \d+/(?P<year>\d{4})"],
    "amount": [ROW],
    "type": [ROW],
}

SPEC = Spec(
    slug="flatex_pdf",
    label="flatex / FinTech Group Bank — Abrechnung PDF",
    corpus="fintechgroupbank",
    marks=[r"flatex", r"FinTech Group Bank", r"biw AG", r"flatexDEGIRO"],
    docs=[
        Doc(kind="skip", when=r"^Storno\b|Stornierung", note="A Storno (cancellation) — not imported."),
        Doc(kind="trade", when=r"^(?:Wertpapierabrechnung|Sammelabrechnung)|^Nr\.\S+ (?:Kauf|Verkauf)",
            sell=r"^Nr\.\S+ (?:Verkauf|Tilgung|R.cknahme|Einl.sung)", block=TRADE_LINE, fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zinsgutschrift|Zinsmitteilung|Kuponzahlung)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsmitteilung|Dividendengutschrift|Aussch.ttung)", fields=CREDIT_FIELDS),
        Doc(kind="rows", when=r"^Kontoauszug Nr:", block=ROW, fields=STATEMENT_FIELDS,
            kinds={r"^Zins": "interest", r"geb.hr|Geb.hr|Entgelt": "fee", r"Steuer": "tax",
                   r"Dividende|Ertrag": "dividend"}),
    ],
)
