"""Erste Bank / Brokerjet / ecetra (Austria) — Wertpapierbestätigung,
Erträgnisgutschrift. Dates written out ("09. April 2010") or dotted."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\. [A-Za-zä]+ \d{4})"

TRADE_FIELDS = {
    "security": [r"^Wertpapier: (?P<name>.+?)(?: (?:Tradinggeb.hren|WP-Kommission|Kurswert|Spesen)[^\n]*)?$", r"WP-Kenn-Nr\. ?: " + ISIN],
    "shares": [r"^St.ck: (?P<shares>" + NUM + r")"],
    "price": [r"^Preis: (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Handelstag: " + DATE, r"^Ausf.hrungsdatum: " + DATE],
    "amount": [r"\bGesamtbetrag: (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"Referenz Nr\.?: (?P<ref>\S+)"],
    "fees": [r"\b(?:Tradinggeb.hren|WP-Kommission|Spesen|Fremde Spesen|Provision|Geb.hren): (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")-?"],
    "taxes": [r"\b(?:KESt(?: I{1,3})?|Fremde Steuer|Quellensteuer|Kapitalertragsteuer) ?: (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")-?"],
}
CREDIT_FIELDS = {
    "security": [r"^Wertpapier ?: (?P<name>.+?)(?: (?:Aussch.ttung|Dividende|Zinsen|Ertrag)[^\n]*)?$", r"WP-Kenn-Nr\. ?: " + ISIN],
    "shares": [r"^WP-Bestand ?: (?P<shares>" + NUM + r")"],
    "date": [r"^Zahltag ?: " + DATE, r"mit Valuta " + DATE],
    "amount": [r"^Auszahlungsbetrag ?: (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")", r"\bNetto ?: (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"Referenz Nr\.?: (?P<ref>\S+)"],
    "fees": TRADE_FIELDS["fees"],
    "taxes": TRADE_FIELDS["taxes"],
}
# The ISIN sits on its own line in a two-column layout: a second
# "security" alternative captures it after the name was found.
TRADE_FIELDS["security"] = [r"^Wertpapier: (?P<name>[^\n]+?)(?: (?:Tradinggeb.hren|WP-Kommission|Kurswert)[^\n]*)?$[\s\S]*?WP-Kenn-Nr\. ?: " + ISIN]
CREDIT_FIELDS["security"] = [r"^Wertpapier ?: (?P<name>[^\n]+?)(?: (?:Aussch.ttung|Dividende|Zinsen|Ertrag)[^\n]*)?$[\s\S]*?WP-Kenn-Nr\. ?: " + ISIN]

# The 2015+ layout: "WERTPAPIERBESTÄTIGUNG / BARDIVIDENDE", details as
# "Label : value" lines, and English-style decimals in the amounts.
NEW_CREDIT = {
    "security": [r"^ISIN : " + ISIN + r"\nWertpapierbezeichnung : (?P<name>.+)$"],
    "shares": [r"^Anspruchsberechtigter : (?P<shares>" + NUM + r")"],
    "date": [r"^Zahltag : " + DATE, r"^Valutatag : " + DATE],
    "amount": [r"^Gesamtbetrag \(in : (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")\nKontow.hrung\)",
               r"^Gesamtbetrag : (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
               r"^Netto-Betrag : (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")", r"^Auszahlungsbetrag : (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"Referenz: (?P<ref>\S+)"],
    "fx": [r"^Devisenkurs : (?P<fx_rate>[\d.,]+)$"],
    "taxes": [r"^Steuern : (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")",
              r"^(?:KESt|Quellensteuer|Fremde Steuer|Kapitalertragsteuer)[^:\n]*: (?P<currency>[A-Z]{3}) -?(?P<tax>" + NUM + r")"],
    "fees": [r"^(?:Spesen|Provision|Geb.hren)[^:\n]*: (?P<currency>[A-Z]{3}) -?(?P<fee>" + NUM + r")"],
}

SPEC = Spec(
    slug="erstebank_pdf",
    label="Erste Bank / Brokerjet — Wertpapierbestätigung PDF",
    corpus="erstebank",
    marks=[r"Erste Bank", r"ERSTE BANK", r"ecetra", r"BROKERJET", r"ECTRATWW", r"GIBAATWW"],
    number="auto",
    docs=[
        Doc(kind="skip", when=r"^STORNO|^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^IHR KAUF", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^IHR VERKAUF", fields=TRADE_FIELDS),
        Doc(kind="interest", when=r"^ZINSGUTSCHRIFT|^KUPON", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^ERTR.GNISGUTSCHRIFT|^DIVIDENDE", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:BARDIVIDENDE|AUSSCH.TTUNG|ERTRAG)\s*$", fields=NEW_CREDIT),
    ],
)
