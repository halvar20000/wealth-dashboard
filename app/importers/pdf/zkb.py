"""Zürcher Kantonalbank — Effektenabrechnung, Ertragsabrechnung."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.',]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"

TRADE_FIELDS = {
    "security": [r"^(?P<name>.+)\nValor \d+ / ISIN " + ISIN],
    "shares": [r"^(?P<shares>" + NUM + r") zu (?P<price>" + NUM + r") " + NUM + r"$"],
    "price": [r"^St.ck (?P<price_currency>[A-Z]{3}) [A-Z]{3}\n" + NUM + r" zu (?P<price>" + NUM + r") "],
    "date": [r"^Abschluss per: " + DATE, r"Buchungstag:? " + DATE],
    "amount": [r"^Total zu Ihren (?:Lasten|Gunsten) Valuta \d{2}\.\d{2}\.\d{4} (?P<amount>" + NUM + r")$",
               r"^Total (?P<amount>" + NUM + r")$"],
    "ref": [r"^Abwicklungs-Nr\. (?P<ref>\S+)"],
    "fees": [r"^(?:Fremde Kommission|Kommission|Courtage|B.rsengeb.hr|Geb.hren|Spesen|Fremde Spesen|Abwicklungsgeb.hr) (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Abgaben|Eidg\. Stempelabgabe|Stempelabgabe|Quellensteuer[^\n]*?|Verrechnungssteuer[^\n]*?) (?P<tax>" + NUM + r")$"],
}
CREDIT_FIELDS = {
    "security": [r"^St.ck (?P<shares>" + NUM + r") (?P<name>.+)\nValor \d+ / ISIN " + ISIN],
    "date": [r"^Zahlbar " + DATE, r"Buchungstag " + DATE],
    "amount": [r"^Total zu Ihren Gunsten Valuta \d{2}\.\d{2}\.\d{4} (?P<amount>" + NUM + r")$", r"^Total (?P<amount>" + NUM + r")$"],
    "ref": [r"^Abwicklungs-Nr\. (?P<ref>\S+)"],
    "taxes": [r"^(?:Verrechnungssteuer|Quellensteuer|Steuerr.ckbehalt)[^\n]*? (?P<tax>" + NUM + r")$"],
    "fees": TRADE_FIELDS["fees"],
}

SPEC = Spec(
    slug="zkb_pdf",
    label="Zürcher Kantonalbank — Effektenabrechnung PDF",
    corpus="zuercherkantonalbank",
    marks=[r"Z.rcher Kantonalbank", r"ZKBKCHZZ", r"zkb\.ch"],
    number="ch",
    docs=[
        Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^Ihr Kauf", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^Ihr Verkauf", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Ertragsabrechnung", fields=CREDIT_FIELDS),
    ],
)


# The private account's statement: a table with Debit and Credit
# columns, read by its layout.
from .layout import Table, fields, rows  # noqa: E402

ACCOUNT = Table(row=r"^\s*(?P<date>\d{2}\.\d{2}\.\d{4})\s+", date="%d.%m.%Y", currency="CHF",
                header=r"^\s*Date\s+Booking text\s+Debit", debit=r"Debit [A-Z]{3}", credit=r"Credit [A-Z]{3}",
                stop=r"^\s*Balance as of|^\s*Available amount")
SPECS = [SPEC, Spec(slug="zkb_account_pdf", label="Zürcher Kantonalbank — Kontoauszug PDF", corpus="mono:zkb_debit",
                    marks=[r"Z.rcher Kantonalbank", r"CH\d{2} ?0070 ?0", r"CH\d{2}00700", r"zkb\.ch"], number="ch", layout=True,
                    preprocess=lambda t: rows(t, ACCOUNT),
                    docs=[Doc(kind="rows", when=r"Account statement|Kontoauszug", block=r"^ROW ", fields=fields(), kinds=ACCOUNT.kinds)])]
