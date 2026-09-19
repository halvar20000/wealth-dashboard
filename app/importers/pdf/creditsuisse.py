"""Credit Suisse (Schweiz) — the Wertschriftenabrechnung and the
Ertragsabrechnung, English-style thousands on Swiss paper."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d,']+(?:\.\d+)?"
DATE = r"\d{2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?P<name>.+)\nValor \d+, [^,]*, ISIN " + ISIN,
                 r"^(?P<notation>[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+)\n(?:.*\n){0,2}?Valor \d+, [^,]*, ISIN " + ISIN,
                 r"ISIN " + ISIN],
    "price": [r"^zum Kurs von (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^Datum (?P<date>" + DATE + r")", r"^Coupon-Verfall (?P<date>" + DATE + r")", r"^Valuta (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Belastung|Gutschrift) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"Auftrags-Nr\. (?P<ref>\S+)"],
    "fees": [r"^(?:Kommission[^\n]*?|Kosten und Abgaben[^\n]*?|Courtage[^\n]*?) (?P<currency>[A-Z]{3}) (?P<sign>-? ?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidgen.ssische Umsatzabgabe|Verrechnungssteuer[^\n]*?|Quellensteuer[^\n]*?) (?P<currency>[A-Z]{3}) (?P<sign>-? ?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="creditsuisse_pdf",
    label="Credit Suisse — Wertschriftenabrechnung PDF",
    corpus="creditsuisseag",
    marks=[r"CREDIT SUISSE", r"credit-suisse\.com", r"CRESCHZZ"],
    number="en",
    docs=[
        Doc(kind="trade", when=r"^Ihr (?:Kauf|Verkauf)", sell=r"^Ihr Verkauf", fields=FIELDS),
        Doc(kind="dividend", when=r"^Ertragsabrechnung", fields=FIELDS),
        # The online discount on the commission: a fee credit of its own,
        # which the booked total already held.
        Doc(kind="fee", when=r"^Internet-Verg.nstigung ", also=True, split=True, fields={
            "date": [r"^Datum (?P<date>" + DATE + r")"],
            "security": [r"ISIN " + ISIN],
            "amount": [r"^(?P<sign>Internet-Verg.nstigung) (?P<currency>[A-Z]{3}) (?:- ?)?(?P<amount>" + NUM + r")$"],
        }),
    ],
)
