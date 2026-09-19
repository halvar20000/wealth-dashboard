"""apoBank (Deutsche Apotheker- und Ärztebank) — Wertpapierabrechnung
and Bardividende, the settlement on a "Belastung - EUR … Konto" line."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^Wertpapierbezeichnung: (?P<name>.+)\nISIN: " + ISIN],
    "shares": [r"^Nominal / St.ck: (?P<shares>" + NUM + r")"],
    "price": [r"^Ausf.hrungspreis: (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Schlusstag: (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Belastung|Gutschrift) - [A-Z]{3} [^\n]*? (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")$",
               r"^Ausmachender Betrag: (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "ref": [r"^\S+ \S+ / \S+ (?P<ref>\d+) " + DATE + r" \d+ / \d+$"],
    "fees": [r"^(?:Provision|Geb.hr[^\n]*?|Fremde Spesen|Handelsplatzentgelt|Courtage): (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer): (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Devisenkurs: (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
DIVIDEND_FIELDS = {
    "security": [r"^Wertpapierbezeichnung (?P<name>.+)\n(?:(?P<name2>[^\n]+)\n)?ISIN " + ISIN],
    "shares": [r"^Nominal/St.ck (?P<shares>" + NUM + r") ST"],
    "date": [r"^Zahlungsdatum (?P<date>" + DATE + r")", r"mit Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Ausmachender Betrag (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="apobank_pdf",
    label="apoBank — Wertpapierabrechnung PDF",
    corpus="apobank",
    marks=[r"apoBank", r"apobank\.de", r"DAAEDEDD"],
    docs=[
        Doc(kind="trade", when=r"^Transaktion: (?:Kauf|Verkauf)", sell=r"^Transaktion: Verkauf", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Bardividende|Aussch.ttung|Dividende)\s*$", fields=DIVIDEND_FIELDS),
    ],
)
