"""PostFinance (E-Trading, run by Swissquote) — Transaktionsbeleg for a
Börsentransaktion, a Dividende, a Zinsabschluss. Swiss numbers: 2'837.40."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.',]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"

TRADE_FIELDS = {
    "security": [r"^(?P<name>.+?) ISIN: " + ISIN],
    "shares": [r"^Anzahl Preis Betrag\n(?P<shares>" + NUM + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r"$"],
    "date": [r"^Gem.ss Ihrem \S+auftrag vom " + DATE, r"Valutadatum " + DATE, r"^Bern, " + DATE],
    "amount": [r"^Zu Ihren (?:Lasten|Gunsten) (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"Unsere Referenz: (?P<ref>\S+)"],
    "fees": [r"^(?:Kommission|B.rsengeb.hren|Geb.hren|Courtage|Fremde Spesen|Abwicklungsgeb.hr) (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Abgabe \(Eidg\. Stempelsteuer\)|Eidg\. Stempelsteuer|Stempelsteuer|Quellensteuer[^\n]*?|Verrechnungssteuer[^\n]*?) (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")$"],
}
CREDIT_FIELDS = {
    "security": [r"^ISIN: " + ISIN + r"\n(?P<name>.+?) NKN: \d+ " + NUM + r"$", r"^(?P<name>.+?) ISIN: " + ISIN],
    "shares": [r"^Anzahl (?P<shares>" + NUM + r")$"],
    "date": [r"^Valutadatum " + DATE, r"^Ausf.hrungsdatum " + DATE],
    "amount": [r"^Total (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$"],
    "ref": [r"Unsere Referenz: (?P<ref>\S+)"],
    "taxes": TRADE_FIELDS["taxes"],
    "fees": TRADE_FIELDS["fees"],
}

SPEC = Spec(
    slug="postfinance_pdf",
    label="PostFinance E-Trading — Transaktionsbeleg PDF",
    corpus="postfinance",
    marks=[r"PostFinance", r"POFICHBE"],
    number="ch",
    docs=[
        Doc(kind="skip", when=r"^Storno\b|^Annullierung", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^B.rsentransaktion: Kauf", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^B.rsentransaktion: Verkauf", fields=TRADE_FIELDS),
        Doc(kind="interest", when=r"^(?:Zins|Coupon|Kapitalzins)\b.*Unsere Referenz", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividende|Aussch.ttung|Kapitalr.ckzahlung) Unsere Referenz", fields=CREDIT_FIELDS),
    ],
)
