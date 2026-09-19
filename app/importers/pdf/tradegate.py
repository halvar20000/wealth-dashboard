"""Tradegate (tradegate.direct) — Wertpapierabrechnung, Ertragsgutschrift,
Vorabpauschale, the Steuerausgleichsrechnung and the Kontoauszug."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^ISIN " + ISIN + r"\n(?:WKN [A-Z0-9]{6}\n)?Wertpapier (?P<name>.+)", r"^Wertpapier (?P<name>.+)\nISIN " + ISIN],
    "shares": [r"^St.ck ausgef.hrt (?P<shares>" + NUM + r")", r"^Nominal/St.ck (?P<shares>" + NUM + r") St.ck", r"^St.ck (?P<shares>" + NUM + r")$"],
    "price": [r"^Ausf.hrungskurs (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^Handelstag/-zeit (?P<date>" + DATE + r")", r"^Zahlungsdatum (?P<date>" + DATE + r")", r"mit Valuta (?P<date>" + DATE + r")", r"^Ex-Datum (?P<date>" + DATE + r")"],
    "amount": [r"^Ausmachender Betrag (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"Order-/Ref\.nr\. (?P<ref>\d+)"],
    "fees": [r"^(?:Orderprovision|Fremde Geb.hren und Spesen|Handelsplatzgeb.hr|Provision) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^Abgef.hrte[rn]? (?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer) (?P<sign>-?)(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "fx": [r"^Devisenkurs (?P<fx_rate>" + NUM + r") (?P<fx_pair>[A-Z]{3}/[A-Z]{3})"],
}
TAX_FIELDS = {**FIELDS, "amount": [r"^Ausmachender Betrag (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})"]}
REFUND_FIELDS = {
    "date": [r"^Kontoauszug Datum (?P<date>" + DATE + r")", r"bis (?P<date>" + DATE + r")\s*\n"],
    "amount": [r"^(?:Gutgeschriebener Betrag|Belasteter Betrag|Belastung|Gutschrift) (?P<amount>-?" + NUM + r")(?: (?P<currency>[A-Z]{3}))?$"],
}
ROW = r"^\d+ \S.* " + DATE + r" -?" + NUM + r"$"
ROW_FIELDS = {
    "date": [r"^\d+ .* (?P<date>" + DATE + r") -?" + NUM + r"$"],
    "amount": [r"^(?P<ref>\d+) (?P<type>.+?) " + DATE + r" (?P<amount>-?" + NUM + r")$"],
    "type": [r"^\d+ (?P<type>.+?) " + DATE + r" -?" + NUM + r"$"],
}

SPEC = Spec(
    slug="tradegate_pdf",
    label="Tradegate — Wertpapierabrechnung PDF",
    corpus="tradegateag",
    marks=[r"Tradegate AG", r"tradegate\.direct"],
    docs=[
        Doc(kind="trade", when=r"^Wertpapierabrechnung", sell=r"^Orderart Verkauf", fields=FIELDS),
        Doc(kind="tax", when=r"^Vorabpauschale\s*$", fields=TAX_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertragsgutschrift|Dividendengutschrift|Zinsgutschrift|Bardividende)", fields=FIELDS),
        Doc(kind="tax", when=r"^Durch steuerliche ?Verrechnungen", fields=REFUND_FIELDS),
        Doc(kind="rows", when=r"^Kontoauszug", block=ROW, fields=ROW_FIELDS,
            kinds={r"Wertpapier|Kauf|Verkauf|Ertrag|Dividende": "skip", r"Zins": "interest", r"Geb.hr|Entgelt|Depotf": "fee", r"Steuer": "tax"}),
    ],
)
