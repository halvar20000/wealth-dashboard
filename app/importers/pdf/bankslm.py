"""Bank SLM (Spar + Leihkasse Münsingen) — Börsenabrechnung and
Dividende, Swiss paper with mangled umlauts."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,'’]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?P<shares>" + NUM + r") (?:Anteile )?(?P<name>.+)\n(?P<name2>.+)\nValor: (?P<ref>\d+)",
                 r"^(?P<shares>" + NUM + r") (?:Anteile )?(?P<name>.+)\n(?:[^\n]*\n)?[^\n]*\nValor: (?P<ref>\d+)", r"^ISIN: " + ISIN],
    "price": [r"^Menge/Nominal Preis\n" + NUM + r" (?P<price>" + NUM + r")", r"^Menge Ausf.hrung Preis Wrg Betrag\n" + NUM + r" \S+ (?P<price>" + NUM + r") "],
    "date": [r"^Wir haben f.r Sie am (?P<date>" + DATE + r")", r"Valuta: (?P<date>" + DATE + r")"],
    "amount": [r"^Netto [A-Z]{3} -?" + NUM + r"\nChange [A-Z]{3}/[A-Z]{3} " + NUM + r" (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")",
               r"^Netto (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "fees": [r"^(?:Eigene Courtage|Courtage|B.rsengeb.hren?|Fremde Spesen)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^(?:Eidg\. Umsatzabgabe|Eidg\. Umsatz Stempel|\d+% Verrechnungssteuer|Verrechnungssteuer|Quellensteuer)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
    "fx": [r"^Change (?P<fx_pair>[A-Z]{3} ?/ ?[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
DIVIDEND_FIELDS = {
    "security": [r"^ISIN: " + ISIN, r"^Valor: (?P<ref>\d+)"],
    "shares": [r"^Bestand: (?P<shares>" + NUM + r") zu "],
    "date": [r"Zahlbar Datum: (?P<date>" + DATE + r")", r"^Am (?P<date>" + DATE + r") wurde", r"per (?P<date>" + DATE + r")"],
    "amount": [r"^Netto (?P<currency>[A-Z]{3}) (?P<amount>-?" + NUM + r")"],
    "taxes": [r"^(?:\d+% )?(?:Verrechnungssteuer|Quellensteuer|Nicht r.ckforderbare Steuern)[^\n]*? (?P<currency>[A-Z]{3}) (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="bankslm_pdf",
    label="Bank SLM — Abrechnung PDF",
    corpus="bankslm",
    marks=[r"Bank SLM", r"Spar \+ Leihkasse M.nsingen", r"M.nsingen"],
    number="ch",
    docs=[
        Doc(kind="trade", when=r"^B.rsenabrechnung - (?:Kauf|Verkauf|Zeichnung|R.cknahme|Emission)", sell=r"^B.rsenabrechnung - (?:R.cknahme|Verkauf)|f.r Sie am \S+ verkauft", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividende|Aussch.ttung|Kapitalr.ckzahlung)\s*$", fields=DIVIDEND_FIELDS),
    ],
)

# The same Finnova paper under other letterheads.
SPECS = [
    SPEC,
    Spec(slug="radicant_pdf", label="radicant / Basellandschaftliche Kantonalbank — Abrechnung PDF", corpus="basellandschaftlichekantonalbank",
         marks=[r"radicant", r"Basellandschaftliche Kantonalbank", r"BLKB"], number="ch", docs=SPEC.docs),
    Spec(slug="vz_pdf", label="VZ Depotbank — Abrechnung PDF", corpus="vzvermoegenszentrumag",
         marks=[r"VZ Depotbank", r"vzdepotbank\.ch", r"VZ Verm.genszentrum"], number="ch", docs=SPEC.docs),
    Spec(slug="fkb_pdf", label="Freiburger Kantonalbank — Abrechnung PDF", corpus="freiburgerkantonalbank",
         marks=[r"fkb\.ch", r"Freiburger Kantonalbank", r"BCF / FKB"], number="ch", docs=SPEC.docs),
]


# Liberty Vorsorge (Everon) prints the same Finnova paper, but its PDF text
# comes out with stray blanks inside words ("V erk a u f", "CH F 2.00").
# Glue the words the spec relies on back together before matching.
_WORDS = ["Liberty Vorsorge", "Wir haben für Sie am", "verkauft", "gezeichnet", "gekauft",
          "Börsenabrechnung", "Verkauf", "Zeichnung", "Rücknahme", "Kauf", "Ausschüttung",
          "Dividende", "Kapitalrückzahlung", "Total Kurswert", "Andere Spesen", "Stempel",
          "Eigene Courtage", "Verrechnungssteuer", "Quellensteuer", "Netto", "Brutto",
          "Bestand:", "Valor:", "ISIN:", "Zahlbar Datum:", "Ex Datum:", "Unsere Gutschrift",
          "Menge/Nominal", "Auftragsnummer", "Valuta", "Anteile", "Change"]
_GLUE = [(re.compile(r"\b" + r"\s?".join(re.escape(c) for c in w.replace(" ", ""))), w) for w in _WORDS]


def _despace(text: str) -> str:
    out = []
    for line in text.splitlines():
        for rx, word in _GLUE:
            line = rx.sub(word, line)
        # currency codes ("CH F", "U SD") and the ISIN / Valor values
        line = re.sub(r"\b([A-Z]) ?([A-Z]) ?([A-Z])\b(?= -?[\d'.]+$| )", r"\1\2\3", line)
        line = re.sub(r"\b([A-Z]{3}) ?/ ?([A-Z]{3})\b", r"\1/\2", line)
        line = re.sub(r"^(ISIN|Valor):\s*(.+)$", lambda m: f"{m.group(1)}: " + m.group(2).replace(" ", ""), line)
        out.append(line)
    return "\n".join(out)


SPECS.append(
    Spec(slug="liberty_pdf", label="Liberty Vorsorge — Abrechnung PDF", corpus="libertyvorsorgeag",
         marks=[r"Liberty Vorsorge", r"liberty\.ch", r"Everon"], number="ch", docs=SPEC.docs,
         preprocess=_despace))
