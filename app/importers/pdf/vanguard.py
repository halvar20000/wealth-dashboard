"""Vanguard Group Europe (the German invest platform) — the
Wertpapierabrechnung and the Bardividende."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{1,2}\.\d{1,2}\.\d{4}"

FIELDS = {
    "security": [r"^Wertpapierbezeichnung (?P<name>.+)\n(?:(?P<name2>[^\n]+)\n)?ISIN " + ISIN],
    "shares": [r"^Nominal ?/ ?St.ck (?P<shares>" + NUM + r")"],
    "price": [r"^Kurs \(St.ckpreis\) (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Ausf.hrungstag ?/ ?-zeit (?P<date>" + DATE + r")", r"^Zahlungsdatum (?P<date>" + DATE + r")", r"^Valutadatum[^\n]* (?P<date>" + DATE + r")",
             r"mit Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^Ausmachender Betrag (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")", r"^Kurswert (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Referenznummer (?P<ref>\d+)", r"^Ordernummer (?P<ref>\d+)"],
    "fees": [r"^(?:Provision|Geb.hr|Fremde Spesen|Handelsplatzentgelt)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}
# A sale prints the taxes twice — once as a summary, once on the tax
# page; the merge doc takes them off the proceeds once.
SALE_FIELDS = {**FIELDS, "taxes": []}
TAX_PAGE = {"taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer) (?P<currency>[A-Z]{3}) -(?P<tax>" + NUM + r")$"]}

SPEC = Spec(
    slug="vanguard_pdf",
    label="Vanguard Invest — Abrechnung PDF",
    corpus="vanguardgroupeurope",
    marks=[r"Vanguard Group Europe", r"de\.vanguard"],
    docs=[
        Doc(kind="trade", when=r"^Wertpapierabrechnung: (?:Kauf|Verkauf)", sell=r"^Wertpapierabrechnung: Verkauf", fields=SALE_FIELDS),
        Doc(kind="tax", when=r"^Wertpapierabrechnung: Verkauf(?:.|\n)*^Bemessungsgrundlage f.r Kapitalertragsteuer", fields=TAX_PAGE, also=True, merge=True),
        Doc(kind="dividend", when=r"^(?:Bardividende|Aussch.ttung|Dividende)\s*$", fields=FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale", fields=FIELDS),
    ],
)
