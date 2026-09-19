"""LGT Bank — the Abrechnung Kauf / Verkauf and the dividend advice,
Liechtenstein paper with Swiss notation and written dates."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}|\d{1,2}\. [A-Za-zä]+ \d{4}"

TRADE_FIELDS = {
    "security": [r"^Titel (?P<name>.+)\n(?:.*\n){0,3}?ISIN " + ISIN],
    "shares": [r"^Anzahl (?P<shares>" + NUM + r") (?P<notation>St.ck|[A-Z]{3})"],
    "price": [r"^Kurs (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Abschlussdatum (?P<date>\d{2}\.\d{2}\.\d{4})", r"^Zeichnungstag \(NAV\) (?P<date>\d{2}\.\d{2}\.\d{4})", r"^Auftragserteilung (?P<date>\d{2}\.\d{2}\.\d{4})", r"^Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Belastung|Gutschrift) [A-Z]{3} \S*[Kk]onto \S+ (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Auftragsnummer: (?P<ref>\d+)"],
    "fees": [r"^(?:Courtage|Broker Kommission|B.rsengeb.hr|Fremde Spesen|Abwicklungsgeb.hr|Spesen)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Umsatzabgabe|Stempelsteuer|Quellensteuer[^\n]*?|Verrechnungssteuer[^\n]*?) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}
DIVIDEND_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?P<name>.+)\n(?:.*\n){0,2}?ISIN: " + ISIN],
    "date": [r"^Valuta (?P<date>" + DATE + r")", r"^Ex-Datum (?P<date>" + DATE + r")"],
    "amount": [r"^Zu Ihren (?:Gunsten|Lasten) (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")", r"^Netto (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "ref": [r"^Auftragsnummer: (?P<ref>\d+)"],
    "taxes": [r"^(?:Quellensteuer|Verrechnungssteuer|Steuerr.ckbehalt)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fees": [r"^(?:Kommission|Spesen|Geb.hr)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
}

SPEC = Spec(
    slug="lgt_pdf",
    label="LGT Bank — Abrechnung PDF",
    corpus="lgtbank",
    marks=[r"LGT Bank", r"lgt\.(?:li|com)", r"BLFLLI2X"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^Abrechnung (?:Kauf|Verkauf|Zeichnung|R.cknahme)", sell=r"^Abrechnung (?:Verkauf|R.cknahme)|^Gutschrift [A-Z]{3} Konto", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Wir rechnen folgende Ertr.gnisse|Dividende|Aussch.ttung|Ertr.gnisabrechnung)", fields=DIVIDEND_FIELDS),
    ],
)
