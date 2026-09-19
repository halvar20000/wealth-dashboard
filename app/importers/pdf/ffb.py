"""FIL Fondsbank (FFB) — the Fondsabrechnung, a table with one block
of four lines per order: the kind and the fund, the amount, the price
and the units on the first; the order number, WKN / ISIN, rate and
price date on the second; the settlement at the end. Also the
Ausschüttungsanzeige and the newer DepotReport of a single trade."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

HEAD = r"^(?:Kauf|Verkauf|Gesamtverkauf|Splitt?kauf Betrag|Wiederanlage|Entgeltbelastung|Sparplan|Entnahmeplan|Tausch|Umtausch) .+ -?" + NUM + r" [A-Z]{3} " + NUM + r" [A-Z]{3} [-+]?" + NUM + r"$"
BLOCK_FIELDS = {
    "security": [r"^(?P<type>Kauf|Verkauf|Gesamtverkauf|Splitt?kauf Betrag|Wiederanlage|Entgeltbelastung|Sparplan|Entnahmeplan|Tausch|Umtausch) (?P<name>.+?) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3}) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) (?P<shares>[-+]?" + NUM + r")$\n\d+ (?:[A-Z0-9]{6} / |(?=[A-Z]{2}[A-Z0-9]{9}\d / ))" + ISIN + r"(?: / [A-Z0-9]{6})?(?: (?P<fx_rate>" + NUM + r") (?P<fx_quote>[A-Z]{3}))? (?P<date>" + DATE + r")"],
    "fees": [r"^(?:Ausgabeaufschlag / Provision \([\d.,]+ %\)|Additional Trading Costs|Transaktionskosten) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^abgef.hrte (?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer) (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}
FEE_FIELDS = {**BLOCK_FIELDS, "fees": [], "taxes": []}

PAYOUT_FIELDS = {
    "security": [r"^Fondsname (?P<name>.+?) Datum der Aussch.ttung (?P<date>" + DATE + r")", r"^WKN / ISIN [A-Z0-9]{6} / " + ISIN],
    "shares": [r"Anteilsbestand per " + DATE + r" (?P<shares>" + NUM + r") St"],
    "amount": [r"^Folgender Betrag wurde (?:zugunsten Ihrer Referenzbankverbindung .berwiesen|wieder angelegt|Ihrem Konto gutgeschrieben) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})",
               r"^zur Wiederanlage zur Verf.gung stehend (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})",
               r"^Aussch.ttung(?: vor Teilfreistellung)? +" + NUM + r" [A-Z]{3} (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer) +(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

REPORT_FIELDS = {
    "security": [r"^Fondsname \(WKN / ISIN\) (?P<name>.+?) \([A-Z0-9]{6} / " + ISIN + r"\)"],
    "shares": [r"^Anteile (?P<shares>" + NUM + r")"],
    "price": [r"^Abrechnungspreis (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})"],
    "date": [r"^(?P<date>" + DATE + r"): ", r"^Abrechnungsdatum (?P<date>" + DATE + r")"],
    "amount": [r"^Abrechnungsbetrag (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"^Auftragsnummer (?P<ref>\d+)"],
    "fees": [r"^Ausgabeaufschlag in EUR (?P<fee>" + NUM + r") (?P<currency>EUR)"],
    "taxes": [r"^Abgef.hrte Steuern gesamt (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})"],
}

SPEC = Spec(
    slug="ffb_pdf",
    label="FIL Fondsbank (FFB) — Fondsabrechnung PDF",
    corpus="filfondbank",
    marks=[r"FIL Fondsbank", r"ffb\.de", r"FFB Fondsdepot", r"fidelity\.de"],
    docs=[
        Doc(kind="rows", when=r"^Fondsabrechnung", block=HEAD, fields=BLOCK_FIELDS,
            kinds={r"^Verkauf|^Gesamtverkauf|^Entnahme|^Entgeltbelastung": "sell", r".": "buy"}),
        # The fee paid by selling units: the fee row itself.
        Doc(kind="rows", when=r"^Fondsabrechnung", block=r"^Entgeltbelastung .+ -?" + NUM + r" [A-Z]{3} " + NUM + r" [A-Z]{3} -?" + NUM + r"$",
            fields=FEE_FIELDS, kinds={r".": "fee"}, also=True),
        Doc(kind="dividend", when=r"^Aussch.ttungsanzeige|^Fondsname .+ Datum der Aussch.ttung", fields=PAYOUT_FIELDS),
        Doc(kind="trade", when=r"^" + DATE + r": (?:Kauf|Verkauf|Gesamtverkauf)", sell=r"^" + DATE + r": (?:Verkauf|Gesamtverkauf)", fields=REPORT_FIELDS),
    ],
)
