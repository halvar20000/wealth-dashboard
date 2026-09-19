"""Liechtensteinische Landesbank / wiLLBe — the Börsenabrechnung, the
dividend advice, the Kontoauszug."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}|\d{1,2}\. [A-Za-zä]+ \d{4}"

TRADE_FIELDS = {
    "security": [r"^Auftragsnummer \S+\n(?P<name>.+)\n(?:Anzahl / Nominal|Ihr Bestand)"],
    "isin": [r"^ISIN " + ISIN],
    "shares": [r"^Anzahl / Nominal (?P<shares>" + NUM + r")", r"^Ihr Bestand per \S+ (?P<shares>" + NUM + r") St.ck"],
    "price": [r"^Kurs (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"Valuta (?P<date>" + DATE + r")", r"^Zahlungsdatum (?P<date>" + DATE + r")", r"^Abschlussdatum (?P<date>" + DATE + r")"],
    "amount": [r"^Zu Ihren (?:Lasten|Gunsten) Valuta (?:" + DATE + r") (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")"],
    "ref": [r"^Auftragsnummer (?P<ref>\S+)"],
    "fees": [r"^(?:Courtage|Kommission|B.rsengeb.hr|Spesen|Geb.hr)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:[\d.]+ % )?(?:Quellensteuer|Verrechnungssteuer|Eidg\. Umsatzabgabe|Stempelsteuer)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Umrechnungskurs (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
TRADE_FIELDS["security"].append(r"^ISIN " + ISIN)

# "31.12. Abschluss 31.12. 456.60 50'614.57": day and month, text, value day, amount, balance.
ROW = r"^\d{2}\.\d{2}\. \S.* \d{2}\.\d{2}\. " + NUM + r" " + NUM + r"$"
ROW_FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.) "],
    "year": [r"^Kontoauszug in [A-Z]{3} \d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.(?P<year>\d{4})", r"^Per \d{1,2}\. [A-Za-zä]+ (?P<year>\d{4})"],
    "amount": [r"^\d{2}\.\d{2}\. (?P<type>.+?) \d{2}\.\d{2}\. (?P<amount>" + NUM + r") " + NUM + r"$"],
    "type": [r"^\d{2}\.\d{2}\. (?P<type>.+?) \d{2}\.\d{2}\. " + NUM + r" " + NUM + r"$"],
}

SPEC = Spec(
    slug="llb_pdf",
    label="Liechtensteinische Landesbank / wiLLBe — Abrechnung PDF",
    corpus="liechtensteinischelandesbankag",
    marks=[r"Liechtensteinische Landesbank", r"willbe-invest", r"wiLLBe", r"\bLLB\b"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^B.rsenabrechnung - Ihr (?:Kauf|Verkauf)", sell=r"^B.rsenabrechnung - Ihr Verkauf", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Bardividende|Dividende|Aussch.ttung|Kapitalr.ckzahlung)", fields=TRADE_FIELDS),
        Doc(kind="rows", when=r"^Datum Buchungstext / Details Valuta", block=ROW, fields=ROW_FIELDS,
            kinds={r"Kauf|Verkauf|Zeichnung|R.cknahme|Dividende|Saldo": "skip", r"Zins|Abschluss": "interest", r"Geb.hr|Kommission|Entgelt": "fee", r"Steuer": "tax",
                   r"Belastung|Auszahlung|Lastschrift": "withdrawal", r"Gutschrift|Einzahlung": "deposit"}),
    ],
)
