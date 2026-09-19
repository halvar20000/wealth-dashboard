"""The dwpbank family: one layout, seventeen banks.

Deutsche WertpapierService Bank settles securities for most of the
German savings banks, the Volksbanken and Raiffeisenbanken (through DZ
Bank), Postbank, DKB, S Broker, 1822direkt, GenoBroker, MLP, Merkur
Privatbank, Santander, UmweltBank, Weberbank, NORD/LB and others — and
prints the same statement for all of them, with the bank's name in the
letterhead. The anchor that gives it away is the security line:

    Nominale Wertpapierbezeichnung ISIN (WKN)
    Stück 150 LTC PROPERTIES INC. US5021751020 (884625)

So this is one field set, instantiated once per bank with that bank's
marks and label, plus a catch-all at the end for any bank the list
does not name — a Volksbank the corpus never saw prints the same
paper. DKB has its own hand-written reader, older and tested against
more; it comes first and keeps DKB.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"(?P<date>\d{2}\.\d{2}\.\d{4})"
NEXT = r"(?!Börse|Handels|Schlusstag|Limit|Zahlbarkeitstag|Rückzahlung|Girosammel|Wertpapierrechnung|Ausführung|Kurswert|Auftrag|Bestandsstichtag|Ex-Tag|Zinstermin|Fälligkeit|Kupon|Ertrag|Dividende|Zahl|Lagerstelle|Verwahr)"

SECURITY = [
    r"^Nominale Wertpapierbezeichnung ISIN \(WKN\)\n(?P<notation>St.ck|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)\n(?P<name2>" + NEXT + r"[^\n]+)",
    r"^Nominale Wertpapierbezeichnung ISIN \(WKN\)\n(?P<notation>St.ck|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+?) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)",
    r"^Nominale Wertpapierbezeichnung ISIN \(WKN\)\n(?P<notation>St.ck|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<name>.+)\n(?P<name2>.+)\n" + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)",
]
FEES = [r"^(?:Provision|Transaktionsentgelt B.rse|.bertragungs-/Liefergeb.hr|Fremde Abwicklungsgeb.hr|Abwicklungskosten B.rse|"
        r"Maklercourtage|Eigene Spesen|Fremde Auslagen|Ausgabeaufschlag|Handelsentgelt|Kurswertabschlag|Fremde Spesen|"
        r"Grundgeb.hr|B.rsengeb.hr|Clearstream-Geb.hr|Orderprovision|Variable Geb.hr)\b.*? (?P<fee>" + NUM + r")(?P<sign>[-+]?) (?P<currency>[A-Z]{3})$"]
TAXES = [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer) [\d,]+ ?%.*? (?P<tax>" + NUM + r")(?P<sign>[-+]) (?P<currency>[A-Z]{3})$",
         r"^(?:Finanztransaktionssteuer|Einbehaltene Quellensteuer\b.*?|Quellensteuer\b.*?) (?P<tax>" + NUM + r")(?P<sign>[-+]) (?P<currency>[A-Z]{3})$"]
FX = [r"^Devisenkurs (?P<fx_pair>[A-Z]{3} ?/ ?[A-Z]{3}) (?P<fx_rate>" + NUM + r")", r"^Devisenkurs \((?P<fx_pair>[A-Z]{3}/[A-Z]{3})\) (?P<fx_rate>" + NUM + r")"]

TRADE_FIELDS = {
    "security": SECURITY,
    "price": [r"^(?:Ausf.hrungskurs|Abrech\.-Preis|R.ckzahlungskurs) (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}|%)"],
    "date": [r"^Schlusstag(?:/-Zeit)? " + DATE, r"buchen wir .*?Valuta " + DATE,
             r"^(?:F.lligkeitstag|R.ckzahlungsdatum|Bestandsstichtag) " + DATE, r"\bDatum " + DATE],
    "amount": [r"^Ausmachender Betrag (?P<amount>" + NUM + r")(?P<sign>[-+]?) (?P<currency>[A-Z]{3})$"],
    "ref": [r"Auftragsnummer (?P<ref>\S+)", r"Abrechnungsnr\. (?P<ref>\d+)"],
    "fees": FEES,
    "taxes": TAXES,
    "fx": FX,
}
CREDIT_FIELDS = {
    "security": SECURITY,
    # The pay date, as the bank names it; the value date a day or two
    # later is when the money shows in the account.
    "date": [r"^Zahlbarkeitstag " + DATE, r"buchen wir mit Wertstellung " + DATE, r"\bDatum " + DATE],
    "amount": [r"^Ausmachender Betrag (?P<amount>" + NUM + r")(?P<sign>[-+]?) (?P<currency>[A-Z]{3})$"],
    "ref": [r"Abrechnungsnr\. (?P<ref>\d+)"],
    "taxes": TAXES,
    "fx": FX,
}
SPARPLAN_ROW = r"^Kauf " + NUM + r" \S+ " + NUM + r" " + NUM + r" " + NUM + r" \d{2}\.\d{2}\.\d{4} \d{2}\.\d{2}\.\d{4}"
SPARPLAN_FIELDS = {
    "security": [r"^Wertpapierbezeichnung ISIN \(WKN\)\n(?P<name>.+?) " + ISIN + r" \((?P<wkn>[A-Z0-9]{6})\)"],
    "shares": [r"^Kauf " + NUM + r" \S+ " + NUM + r" " + NUM + r" (?P<shares>" + NUM + r") "],
    "price": [r"^Kauf " + NUM + r" \S+ (?P<price>" + NUM + r") "],
    "date": [r"^Kauf " + NUM + r" \S+ " + NUM + r" " + NUM + r" " + NUM + r" " + DATE],
    "amount": [r"^\+ Provision " + NUM + r" Summe (?P<amount>" + NUM + r")$", r"^Kauf (?P<amount>" + NUM + r") "],
    "ref": [r"^Kauf " + NUM + r" (?P<ref>\S+) "],
    "fees": [r"^\+ Provision (?P<fee>" + NUM + r") Summe"],
}

BUY = r"^(?:Wertpapier Abrechnung )?(?:Kauf|Kauf Direkthandel|Ausgabe|Ausgabe Investmentfonds|Zeichnung|Bezug)$"
SELL = r"^(?:Wertpapier Abrechnung )?(?:Verkauf|Verkauf Direkthandel|Verkauf aus Kapitalma.nahme|R.cknahme Investmentfonds|Gesamtk.ndigung|Teilr.ckzahlung mit Nennwert.nderung|Teilliquidation mit Nennwertreduzierung|Einl.sung bei Gesamtf.lligkeit|Einl.sung)$"


def spec(slug: str, label: str, corpus: str, marks: list) -> Spec:
    return Spec(
        slug=slug, label=label, corpus=corpus, marks=marks,
        docs=[
            Doc(kind="skip", when=r"^Storno\b", note="A Storno (cancellation) — not imported."),
            Doc(kind="buy", when=BUY, fields=TRADE_FIELDS),
            Doc(kind="sell", when=SELL, fields=TRADE_FIELDS),
            Doc(kind="tax", when=r"^Vorabpauschale Investmentfonds", fields=CREDIT_FIELDS),
            Doc(kind="interest", when=r"^Zinsgutschrift$", fields=CREDIT_FIELDS),
            Doc(kind="dividend", when=r"^(?:Dividendengutschrift|Gutschrift von Investmentertr.gen|Aussch.ttung aus Genussschein|"
                                       r"Aussch.ttung Investmentfonds|Ertragsgutschrift nach . 27 KStG|Gutschrift|Ertr.gnisgutschrift aus Wertpapieren|"
                                       r"Aussch.ttung|Ertragsgutschrift)$", fields=CREDIT_FIELDS),
            Doc(kind="buy", when=r"^Halbjahresabrechnung Sparplan", block=SPARPLAN_ROW, fields=SPARPLAN_FIELDS),
        ],
    )


FAMILY = "Nominale Wertpapierbezeichnung ISIN \\(WKN\\)"

from . import dab as _dab   # noqa: E402  S Broker's older paper is the DAB family's

SPECS = [
    Spec(slug="sbroker_pdf", label="S Broker / Sparkasse — Wertpapierabrechnung PDF", corpus="sbroker",
         marks=[r"S Broker AG", r"SBRO_", r"Sparkasse", r"Kreissparkasse", r"Stadtsparkasse", r"Wiesbaden, \d{2}\.\d{2}\.\d{4}"],
         docs=spec("x", "x", "", []).docs + _dab.docs()),
    spec("volksbank_pdf", "Volksbank / Raiffeisenbank (DZ Bank) — Wertpapierabrechnung PDF", "dzbankgruppe",
         [r"BIC GENODE", r"DZ BANK", r"Volksbank", r"Raiffeisenbank", r"VR-Bank", r"VR Bank"]),
    spec("raiffeisen_pdf", "Raiffeisen / VR Bank — Wertpapierabrechnung PDF", "raiffeisenbankgruppe",
         [r"VR Bank", r"Raiffeisen", r"BIC GENODE"]),
    spec("postbank_pdf", "Postbank — Wertpapierabrechnung PDF", "postbank", [r"Postbank", r"PBNKDEFF"]),
    spec("1822direkt_pdf", "1822direkt — Wertpapierabrechnung PDF", "direkt1822bank", [r"1822direkt", r"HELADEF1822"]),
    spec("genobroker_pdf", "GenoBroker — Wertpapierabrechnung PDF", "genobroker", [r"GENO Broker", r"GenoBroker"]),
    spec("mlp_pdf", "MLP Banking — Wertpapierabrechnung PDF", "mlpbank", [r"MLP Banking", r"MLPBDE61"]),
    spec("merkur_pdf", "Merkur Privatbank — Wertpapierabrechnung PDF", "merkurprivatbank", [r"Merkur", r"GENODEF1M06"]),
    spec("santander_pdf", "Santander Consumer Bank — Wertpapierabrechnung PDF", "santanderconsumerbank", [r"Santander"]),
    spec("gladbacher_pdf", "Gladbacher Bank — Wertpapierabrechnung PDF", "gladbacherbankag", [r"Gladbacher Bank", r"GENODED1GBM"]),
    spec("weberbank_pdf", "Weberbank — Wertpapierabrechnung PDF", "weberbank", [r"Weberbank", r"WELADED1WBB"]),
    spec("umweltbank_pdf", "UmweltBank — Wertpapierabrechnung PDF", "umweltbankag", [r"UmweltBank"]),
    spec("nordlb_pdf", "NORD/LB — Wertpapierabrechnung PDF", "norddeutschelandesbank", [r"Norddeutsche Landesbank", r"NOLADE2H"]),
    spec("nibc_pdf", "NIBC Direct — Wertpapierabrechnung PDF", "nibcbank", [r"NIBC", r"NZFMDEF1"]),
    spec("sutorbank_pdf", "Sutor Bank — Wertpapierabrechnung PDF", "sutorbankgmbh", [r"SUTOR BANK", r"Sutor Bank"]),
    # Any other bank on the same paper: the structural line alone.
    spec("dwpbank_pdf", "Sparkasse / Volksbank (dwpbank layout) — Wertpapierabrechnung PDF", "", [FAMILY]),
]
