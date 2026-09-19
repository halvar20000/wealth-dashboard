"""WIR Bank / VIAC — the Swiss pillar-3a paper: Börsenabrechnung (Kauf,
Verkauf, Zeichnung, Rücknahme), Dividendenausschüttung, Zins, the
Rückerstattung of withholding tax, the Einzahlung — in German, English
and French. Everything settles in francs; a foreign purchase carries
its own rate."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,']+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?:Ant|Anteile|Units?|Qty|Parts?|units) (?P<name>.+)\nISIN: " + ISIN,
                 r"^(?P<shares>" + NUM + r") (?P<name>.+)\nISIN: " + ISIN],
    "price": [r"^(?:Kurs|Price|Cours): (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"],
    "date": [r"^(?:Verrechneter Betrag|Charged amount|Amount (?:debited|credited)|Montant (?:d.bit.|cr.dit.|comptabilis.)): (?:Valuta|Value date|Date valeur|Valeur) (?P<date>" + DATE + r")",
             r"^(?:Basel|B.le|Stadt|Bâle), (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Verrechneter Betrag|Charged amount|Amount (?:debited|credited)|Montant (?:d.bit.|cr.dit.|comptabilis.)):(?: (?:Valuta|Value date|Date valeur|Valeur) " + DATE + r")? (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "fees": [r"^(?:Courtage|Commission|Frais|Geb.hr|Fee)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Stempelsteuer|Stamp duty|Droit de timbre|Umsatzabgabe) (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^(?:Umrechnungskurs|Exchange rate|Taux de (?:change|conversion)) (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}

CREDIT_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?:Ant|Anteile|Units?|Qty|Parts?|units) (?P<name>.+)\nISIN: " + ISIN,
                 r"^(?P<shares>" + NUM + r") (?P<name>.+)\nISIN: " + ISIN],
    "date": [r"^(?:Gutgeschriebener Betrag|Amount credited|Montant cr.dit.|Verrechneter Betrag|Charged amount|Amount debited|Montant d.bit.|Gutschrift|Credit):"
             r" (?:Valuta|Value date|Date valeur|Valeur) (?P<date>" + DATE + r")",
             r"^(?:Am|On|Le) (?P<date>" + DATE + r") ", r"(?:cr.dit.|d.bit.) (?:le|en date du) (?P<date>" + DATE + r")",
             r"^(?:Basel|B.le|Stadt|Bâle), (?P<date>" + DATE + r")"],
    "amount": [r"^(?:Gutgeschriebener Betrag|Amount credited|Montant cr.dit.|Verrechneter Betrag|Charged amount|Amount debited|Montant d.bit.|Gutschrift|Credit):"
               r"(?: (?:Valuta|Value date|Date valeur|Valeur) " + DATE + r")? (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "fees": [r"^(?:Commission de gestion effective|Effektive Verwaltungsgeb.hr|Effective management fee)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
}

SPEC = Spec(
    slug="wirbank_pdf",
    label="WIR Bank / VIAC — Abrechnung PDF",
    corpus="wirbank",
    marks=[r"WIR Bank", r"viac\.ch", r"VIAC Invest"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^(?:B.rsenabrechnung|Exchange Settlement|Stock exchange (?:settlement|transaction)|Op.ration de bourse|D.compte de bourse|R.glement boursier)",
            sell=r"^Ord(?:er|re): (?:Verkauf|Sell|R.cknahme|Vente|Redemption|Rachat)", fields=TRADE_FIELDS),
        # A refund of withholding tax is booked like a distribution, with
        # the kind named on the line under the heading.
        Doc(kind="tax", when=r"^(?:Dividendenart|Type of (?:distribution|dividend)|Aussch.ttungsart|Type de dividende): (?:R.ckerstattung|Refund|Remboursement)", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividendenaussch.ttung|Dividendenausschuttung|Dividend [Pp]ayment|Dividend distribution|Avis de dividende|Aussch.ttung)", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^(?:Zins|Interest|Int.r.ts)\s*$", fields=CREDIT_FIELDS),
        Doc(kind="deposit", when=r"^(?:Einzahlung|Deposit|Versement|Gutschrift)", fields=CREDIT_FIELDS),
        Doc(kind="fee", when=r"^(?:Belastung|Commission|Verwaltungsgeb.hr|Management fee|Frais de gestion|Commission de gestion)\s*$", fields=CREDIT_FIELDS),
    ],
)
