"""The BAWAG family in Austria: easybank, DADAT, Hello bank! — one
"Abrechnung" with "Wir haben für Sie am 14.6.2022 unten angeführtes
Geschäft abgerechnet:" and a Geschäftsart line saying what it was.

Austrian paper writes 14.6.2022 without the zero, "-3,-- EUR" for
three euros flat, and the security's name in letter-spaced type next
to a plain ISIN. The money out is negative on the page already.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,-]+"
DATE = r"(?P<date>\d{1,2}\.\d{1,2}\.\d{4})"

COMMON = {
    "security": [r"^Titel: " + ISIN + r" (?P<name>.+?) ?$\n(?P<name2>(?!Fondsgesellschaft|Kurs:|Ertrag:|Dividende:|Verwahrart|Handels)[^\n]+)?"],
    "shares": [r"^(?:Zugang|Abgang): (?P<shares>" + NUM + r") Stk", r"^(?P<shares>" + NUM + r") Stk$"],
    "ref": [r"^Auftrags-Nr\.: (?P<ref>\S+)", r"^(?:Abrechnung \S+|Abrechnungsauskunft)\n[^\n]*?(?P<ref>\d{6,}-\d{1,2}\.\d{1,2}\.\d{4})"],
    "fees": [r"^(?:Eigene Spesen|Grundgeb.hr|Fremde Spesen|Inkassoprovision|Umsatzsteuer|Provision|Handelsspesen|B.rsenspesen|Ausgabeaufschlag|Spesen): -?(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "taxes": [r"^(?:KESt(?: [^:\n]*)?|Quellensteuer|QESt|Kapitalertragsteuer|KESt Ausl.ndische Dividende|Ausl. Quellensteuer(?: [^:\n]*)?): -?(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "fx": [r"^Devisenkurs: (?P<fx_rate>[\d.,]+) \(\S+\)"],
}
TRADE_FIELDS = {**COMMON,
    "price": [r"^Kurs: (?P<price>[\d.,]+) (?P<price_currency>[A-Z]{3}|%)"],
    "date": [r"^Handelszeit: " + DATE, r"^Schlusstag: " + DATE, r"^Valuta " + DATE],
    "amount": [r"^Zu (?:Lasten|Gunsten) IBAN[^\n]*? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})\s*$"],
}
CREDIT_FIELDS = {**COMMON,
    "date": [r"^Valuta " + DATE, r"^Zahltag: " + DATE],
    "amount": [r"^Zu (?:Gunsten|Lasten) IBAN[^\n]*? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})\s*$"],
}

def spec(slug, label, corpus, marks):
    return Spec(slug=slug, label=label, corpus=corpus, marks=marks, docs=[
        Doc(kind="skip", when=r"^Storno\b|^Geschäftsart: Storno", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^Gesch.ftsart: (?:Kauf|Zeichnung)", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Gesch.ftsart: (?:Verkauf|Tilgung|R.ckzahlung|Einl.sung)", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Gesch.ftsart: (?:Steuerkorrektur|KESt)", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^Gesch.ftsart: (?:Kupon|Zinsen|Zinsertrag)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^Gesch.ftsart: (?:Ertrag|Dividende|Aussch.ttung)", fields=CREDIT_FIELDS),
    ])

SPECS = [
    spec("easybank_pdf", "easybank (BAWAG) — Abrechnung PDF", "easybankag", [r"easybank", r"BAWAG"]),
    spec("dadat_pdf", "DADAT — Abrechnung PDF", "dadatbankenhaus", [r"DADAT"]),
    spec("hellobank_at_pdf", "Hello bank! (Austria) — Abrechnung PDF", "hellobank", [r"Hellobank BNP Paribas Austria", r"Hello bank!"]),
]
