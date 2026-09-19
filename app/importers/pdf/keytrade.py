"""Keytrade Bank (Luxembourg / Belgium) — bordereau in French, German or
Dutch: "Achat 310 HOME24 SE (DE000A14KEB5) à 15,9324 EUR"."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}/\d{2}/\d{4})"

LINE = (r"^(?P<type>Achat|Vente|Kauf|Verkauf|Aankoop|Verkoop|Buy|Sell) (?P<shares>" + NUM + r") (?P<name>.+?) \(" + ISIN +
        r"\) (?:à|für|aan|at|tegen) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})")
TRADE_FIELDS = {
    "security": [LINE],
    "date": [r"^(?:Date et heure d'ex.cution|Ausf.hrungsdatum und -zeit|Uitvoeringsdatum en -tijd|Execution date and time) : " + DATE,
             r"(?:Date valeur|Valutadatum|Valutadatum|Value date) " + DATE],
    "amount": [r"^(?:D.bit|Cr.dit|Lastschrift|Gutschrift|Debet|Credit) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"^(?:Num.ro de Bordereau|Belegnummer|Borderelnummer|Contract note number) (?P<ref>\S+)"],
    "fees": [r"^(?:Frais de transaction|Transaktionskosten|Transactiekosten|Transaction fees|Frais|Courtage|Makelaarsloon) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Taxe boursi.re|Taxe sur les op.rations|B.rsensteuer|Beurstaks|Stock exchange tax|TOB|Pr.compte mobilier|Verrechnungssteuer|Roerende voorheffing|Withholding tax)(?: [\d,]+ ?%)? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}
CREDIT_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?P<name>.+?) NR \d+ " + NUM + r" [A-Z]{3}$[\s\S]*?(?:Wertpapier|Titre|Effect|Security):\d+/" + ISIN],
    "date": [r"(?:Datum|Date) " + DATE],
    "amount": [r"^(?:Nettoguthaben|Cr.dit net|Netto tegoed|Net credit) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"Belegnr\.: (?P<ref>[^\n]+)$", r"R.f\. : (?P<ref>[^\n]+)$"],
    "taxes": [r"^(?:Verrechnungssteuer|Pr.compte mobilier|Roerende voorheffing|Withholding tax|Quellensteuer|Retenue . la source)(?: [\d,]+ ?%)? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

SPEC = Spec(
    slug="keytrade_pdf",
    label="Keytrade Bank — bordereau PDF",
    corpus="keytradebank",
    marks=[r"Keytrade Bank", r"keytradebank"],
    docs=[
        Doc(kind="trade", when=LINE, sell=r"^(?:Vente|Verkauf|Verkoop|Sell) ", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Guthaben Kupons|Cr.dit coupons|Coupons|Tegoed coupons|Coupon credit)", fields=CREDIT_FIELDS),
    ],
)
