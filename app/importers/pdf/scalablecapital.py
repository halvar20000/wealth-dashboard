"""Scalable Capital — its own paper since it became a bank (2024): the
Wertpapierabrechnung per execution, the Dividende, the Kontoauszug.
Earlier statements came from Baader Bank and are read by that spec.

The Kontoauszug lists every purchase and sale as well; those rows are
left to the execution statements, which carry the units and the price,
so an archive holding both does not book a trade twice. What the
statement contributes is the cash side: transfers, interest, fees.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"

TRADE_LINE = (r"^(?P<type>Kauf|Verkauf|Buy|Sell|Acquisto|Vendita|Achat|Vente|Compra|Venta) (?P<name>.+?) (?P<shares>" + NUM +
              r") (?:Stk\.|pc\.|pz\.|u\.|St\.) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$\n" + ISIN)

TRADE_FIELDS = {
    "security": [TRADE_LINE],
    "date": [r"^(?:Ausf.hrung|Execution|Esecuzione|Ex.cution|Ejecuci.n) (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"Valuta: (?P<date>\d{2}\.\d{2}\.\d{4})", r"Value: (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^(?:Total|Belastung|Gutschrift|Debit|Credit|Totale|Addebito|Accredito) (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"Gesch.ft (?P<ref>\S+)$", r"Order (?P<ref>\S+)$"],
    # "+0,99 EUR": the plus marks a charge on this paper, so no sign group.
    "fees": [r"^(?:Ordergeb.hren?|Geb.hren?|Transaktionskosten|Fremdkosten|Provision|Order fees?|Commissioni d'ordine|Frais d'ordre) \+?(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Steuern|Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Taxes|Financial transaction tax) [-+]?(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

CREDIT_FIELDS = {
    "security": [r"^(?:Berechtigtes Wertpapier|Eligible security) (?P<name>.+?) ?$\nISIN " + ISIN,
                 r"^(?:Vorabpauschale|Preliminary lump sum)\n(?:f.r|for) (?P<name>.+?) \(" + ISIN + r"\)"],
    "shares": [r"^(?:Berechtigte Anzahl|Eligible quantity) (?P<shares>" + NUM + r")"],
    # Booking and value date, the value date being when the money is there.
    "date": [r"^\d{2}\.\d{2}\.\d{4} (?P<date>\d{2}\.\d{2}\.\d{4}) (?:Gutschrift|Belastung|Zahlung|Credit|Steuerabbuchung|Tax debit)",
             r"^Ex[ -]Tag (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^(?:Gesamtbetrag|Total amount|Total|Steuerbelastung|Tax charge) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Ausl.ndische Quellensteuer|Steuern|Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Foreign withholding tax|Taxes) [-+]?(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

ROW = r"^\d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4} (?!(?:Kauf|Verkauf) eines Finanzinstruments).+ [+-]" + NUM + r" [A-Z]{3}$"
STATEMENT_FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) \d{2}\.\d{2}\.\d{4} "],
    "amount": [r"^\d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4} (?P<type>.+?) (?P<amount>[+-]" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "type": [r"^\d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4} (?P<type>.+?) [+-]" + NUM + r" [A-Z]{3}$"],
}

SPEC = Spec(
    slug="scalable_pdf",
    label="Scalable Capital — Abrechnung PDF",
    corpus="scalablecapital",
    marks=[r"Scalable Capital (?:Bank )?GmbH", r"scalable\.capital"],
    number="auto",
    docs=[
        Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="trade", when=r"^(?:Wertpapierabrechnung|Contract note|Nota di eseguito|Avis d'op.r.|Nota de operaci.n)\s*$",
            sell=r"^(?:Verkauf|Sell|Vendita|Vente|Venta) .+ (?:Stk|pc|pz|u|St)\.", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^(?:Vorabpauschale|Preliminary lump sum)", fields=CREDIT_FIELDS),
        Doc(kind="interest", when=r"^Zinszahlung\s*$", fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividende|Aussch.ttung|Ertrag|Dividend|Distribution)\s*$", fields=CREDIT_FIELDS),
        Doc(kind="rows", when=r"^Kontoauszug\s*$", block=ROW, fields=STATEMENT_FIELDS,
            kinds={r"Zinsen": "interest", r"geb.hr|Geb.hr|Entgelt": "fee", r"Steuer": "tax",
                   r"Dividende|Aussch.ttung": "dividend"}),
    ],
)
