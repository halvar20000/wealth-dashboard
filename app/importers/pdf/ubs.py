"""UBS Switzerland — Transaktion (Kauf/Verkauf) and the upper-case
DIVIDENDENZAHLUNG notice."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.',]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"

TRADE_FIELDS = {
    "security": [r"^Whrg\. Anzahl/Betrag Beschreibung Valor/ISIN Laufzeit\n[A-Z]{3} " + NUM + r" (?P<name>.+?) \d+\n(?P<name2>.+?) " + ISIN],
    "shares": [r"^Abschluss \d{2}\.\d{2}\.\d{4} [\d:]+ \S+ (?:Kauf|Verkauf) \S+ (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Abschluss " + DATE, r"^Valuta " + DATE],
    "amount": [r"^Abrechnungsbetrag (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "ref": [r"^Buchung \d{2}\.\d{2}\.\d{4} (?P<ref>\S+)"],
    "fees": [r"^(?:Courtage|Diverse|Geb.hren|B.rsengeb.hr|Fremde Kosten|Kommission) (?P<currency>[A-Z]{3}) -?(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Stempelsteuer|Stempelsteuer|Umsatzabgabe|Quellensteuer|Verrechnungssteuer) (?P<currency>[A-Z]{3}) -?(?P<tax>" + NUM + r")$"],
}
CREDIT_FIELDS = {
    "security": [r"^STUECKZAHL VALOR \d+ ISIN " + ISIN + r" ANSATZ\n(?P<shares>" + NUM + r") (?P<name>.+?) BRUTTO"],
    "date": [r"VALUTA " + DATE, r"^VERFALL " + DATE],
    "amount": [r"^GUTSCHRIFT KONTO \S+ VALUTA \d{2}\.\d{2}\.\d{4} (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"^Auftrags-Nr\. (?P<ref>\S+)"],
    "taxes": [r"^(?:STEUERABZUG|VERRECHNUNGSSTEUER|QUELLENSTEUER)[^\n]*? (?P<currency>[A-Z]{3}) -?(?P<tax>" + NUM + r")$"],
    "fx": [r"^UMRECHNUNGSKURS (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}

SPEC = Spec(
    slug="ubs_pdf",
    label="UBS Switzerland — Abrechnung PDF",
    corpus="ubsag",
    marks=[r"UBS Switzerland", r"UBS Wertschriftendepot", r"ubs\.com", r"UBSWCHZH"],
    number="ch",
    docs=[
        Doc(kind="skip", when=r"^Storno\b|^STORNO", note="A Storno (cancellation) — not imported."),
        Doc(kind="trade", when=r"^Transaktion$", sell=r"^Abschluss .* Verkauf ", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^DIVIDENDENZAHLUNG|^AUSSCH.TTUNG", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^ZINSZAHLUNG|^COUPONZAHLUNG", fields=CREDIT_FIELDS),
    ],
)
