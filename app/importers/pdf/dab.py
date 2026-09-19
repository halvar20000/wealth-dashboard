"""The DAB family: DAB BNP Paribas, onvista bank, S Broker before 2022,
Raisin (Weltsparen), Upvest — one back office, one statement.

    Wir haben für Sie gekauft
    Gattungsbezeichnung ISIN
    ARERO - Der Weltfonds Inhaber-Anteile o.N. LU0360863863
    Nominal Kurs
    STK 0,9192 EUR 163,1900
    Handelstag 06.01.2015 Kurswert EUR 150,00-
    Wert Konto-Nr. Betrag zu Ihren Lasten
    08.01.2015 0000000000 EUR 150,00

Fees and taxes sit at the end of lines that start with something else
("Handelszeit 20:35 Orderentgelt EUR 1,48-"), so their anchors are
not tied to the line start. A trailing "-" is the charge; a tax line
without one, under "Steuerausgleich", is a refund the bank books
separately and this reader leaves out.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"

SETTLEMENT = (r"^Wert Konto-Nr\.[^\n]*Betrag zu Ihren (?:Lasten|Gunsten)\n" + DATE +
              r" \S+(?: [A-Z]{3}/[A-Z]{3} " + NUM + r")? (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")")

FEES = [r"\b(?:Orderentgelt|B.rsengeb.hr|Provision|Orderprovision|Handelsplatzentgelt|Abwicklungskosten(?: Ausland)?|Courtage|"
        r"Fremde Spesen|Spesen|Transaktionsentgelt|Ausgabeaufschlag|Maklercourtage|Clearstream-Geb.hr|Grundgeb.hr|"
        r"Handelsentgelt|Fremdspesen|B.rsenspesen) (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")(?P<sign>-)"]
TAXES = [r"\b(?:einbehaltene Kapitalertragsteuer|einbehaltener Solidarit.tszuschlag|einbehaltene Kirchensteuer|"
         r"Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer|Finanztransaktionssteuer) (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r")(?P<sign>-)"]
FX = [r"(?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r") [A-Z]{3} " + NUM + r"$"]

TRADE_FIELDS = {
    "security": [r"^Gattungsbezeichnung ISIN\n(?P<name>.+?) " + ISIN + r"$"],
    "shares": [r"^(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")$",
               r"^(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r")\b"],
    "date": [r"^Handelstag " + DATE, r"^Wert Konto-Nr\.[^\n]*\n" + DATE],
    "amount": [SETTLEMENT],
    "ref": [r"Abrechnungs-Nr\.[^\n]*\n[^\n]*?(?P<ref>\d{6,}) / \d{2}\.\d{2}\.\d{4}"],
    "fees": FEES,
    "taxes": TAXES,
    "fx": FX,
}
CREDIT_FIELDS = {
    "security": [r"^Gattungsbezeichnung ISIN\n(?P<name>.+?) " + ISIN + r"$"],
    "shares": [r"^(?P<notation>STK|[A-Z]{3}) (?P<shares>" + NUM + r") \d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4}"],
    "date": [r"^Wert Konto-Nr\.[^\n]*\n" + DATE, r"^Zahlungstag " + DATE],
    "amount": [SETTLEMENT],
    "fees": FEES,
    "taxes": TAXES,
    "fx": FX,
}

BUY = r"^Wir haben f.r Sie gekauft"
SELL = r"^Wir haben f.r Sie verkauft"


def docs() -> list:
    return [
        Doc(kind="skip", when=r"^Storno\b|^Stornierung", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=BUY, fields=TRADE_FIELDS),
        Doc(kind="sell", when=SELL, fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^Steuerpflichtige Vorabpauschale", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zinsgutschrift|Zinsertrag)\b", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Ertr.gnisgutschrift|Dividendengutschrift|Ertragsgutschrift|Aussch.ttung|Ertragsaussch.ttung)\b",
            fields=CREDIT_FIELDS),
    ]


def spec(slug: str, label: str, corpus: str, marks: list) -> Spec:
    return Spec(slug=slug, label=label, corpus=corpus, marks=marks, docs=docs())


FAMILY = r"^Gattungsbezeichnung ISIN$"

from . import consorsbank as _consors   # noqa: E402  DAB's paper since 2022 is Consorsbank's (both BNP Paribas)

SPECS = [
    Spec(slug="dab_pdf", label="DAB BNP Paribas — Wertpapierabrechnung PDF", corpus="dab",
         marks=[r"DAB BNP Paribas", r"DAB Bank", r"\bDAB\b", r"BNP Paribas"], docs=docs() + _consors.docs()),
    spec("onvista_pdf", "onvista bank — Wertpapierabrechnung PDF", "onvista", [r"onvista", r"Frankfurt am Main, \d{2}\.\d{2}\.\d{4}"]),
    spec("dabfamily_pdf", "DAB-layout statement (Raisin, Upvest and others)", "", [FAMILY]),
]
