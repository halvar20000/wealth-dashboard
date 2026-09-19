"""DekaBank — the Depot-Tagesauszug (one section per booking: a
Lastschrifteinzug, a Kauf, a Verkauf, an Ertragsabrechnung) and the
Quartalsbericht / Jahresdepotauszug, whose Umsatzübersicht lists every
movement of every fund under the fund's own heading.

The report's rows carry no ISIN of their own — it stands above them,
once per fund — so `report()` writes each row out again with the ISIN
of the section it is in, and the doc reads those lines. A reinvested
distribution ("Ausschüttung / Kauf aus Ertrag") is two things: the
income, and the units it bought.
"""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

# ── Tagesauszug: sections that each start with the fund's name ──
SECTION = r"^(?:[A-ZÄÖÜ]+ )?(?:Fonds)?[Bb]ezeichnung: "
SECTION_FIELDS = {
    "security": [r"[Bb]ezeichnung: (?P<name>.+?)\s*$(?:\n[^\n]*)?\nISIN: " + ISIN, r"^ISIN: " + ISIN],
    "date": [r"Abrechnungstag: (?P<date>" + DATE + r")"],
    "shares": [r"Anteilumsatz: (?P<shares>-?" + NUM + r")"],
    "price": [r" (?P<price_currency>EUR) (?P<price>\d[\d.]*,\d{4,}) "],
    "amount": [r"^=? ?(?:Abrechnungsbetrag|Wiederanlagebetrag|Auszahlungsbetrag) (?P<currency>EUR) (?P<amount>" + NUM + r")"],
    "ref": [r"Auftragsnummer: (?P<ref>\d+ \d+)"],
}
PAYOUT_FIELDS = {
    **SECTION_FIELDS,
    "amount": [r"^=? ?Wiederanlagebetrag (?P<currency>EUR) (?P<amount>" + NUM + r")",
               r"^ ?Aussch.ttung(?: \(pro Anteil EUR " + NUM + r"\):)? (?P<currency>EUR) (?P<amount>" + NUM + r")"],
    "taxes": [r"^ ?(?:(?P<sign>-)|(?P<refund>\+)) ?Verrechnete Steuern (?P<currency>EUR) (?P<tax>" + NUM + r")"],
}

# ── Quartalsbericht: rows rewritten by report() ──
ROW = r"^DEKAROW "
ROW_FIELDS = {
    "security": [r"^DEKAROW " + ISIN + r" \| (?P<name>.*?) \| "],
    "type": [r"^DEKAROW \S+ \| .*? \| (?P<type>.+?) \| "],
    "shares": [r" \| (?P<shares>[+-]?" + NUM + r") \| " + DATE + r"$"],
    "price": [r" \| (?P<price>" + NUM + r") \| [+-]?" + NUM + r" \| " + DATE + r"$"],
    "amount": [r" \| (?P<amount>" + NUM + r") \| " + NUM + r" \| [+-]?" + NUM + r" \| " + DATE + r"$"],
    "date": [r" \| (?P<date>" + DATE + r")$"],
}
TRANSFER = r"Auslieferung|Einlieferung|Übertrag|Zulagenzahlung|Steuererstattung"
FEE = r"Depotpreis|Entgelt|Vertragsgeb.hr"
PAYOUT = r"Verkauf aus Ertrag"
FEE_FIELDS = {
    "date": [r"^(?:Quartalsbericht|Jahresdepotauszug|Depotauszug)[^\n]* per (?P<date>" + DATE + r")", r"^per (?P<date>" + DATE + r")"],
    "amount": [r"^(?P<amount>" + NUM + r") (?P<currency>EUR)(?: inkl\. " + NUM + r" EUR MwSt)? wurden f.r \d{4} belastet",
               r"^Depotpreis in[ck]l\. [^\n]*?: (?P<amount>" + NUM + r")(?: (?P<currency>EUR))? (?:am " + DATE + r" )?belastet"],
}


def report(text: str) -> str:
    """Every row of an Umsatzübersicht on one line, with its fund."""
    if not re.search(r"^Umsatz(?:-Jahres)?.bersicht", text, re.M):
        return text
    out, isin, name = [], None, None
    for line in text.split("\n"):
        m = re.match(r"^(?:(?P<name>.+?)/ )?ISIN: (?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)\b", line)
        if m:
            isin = m.group("isin")
            name = m.group("name") or (out[-1].strip() if out else None)
        r = re.match(r"^(?P<type>\S.*?) (?P<amount>\d[\d.]*,\d{2})(?: (?P<fx>\d[\d.]*,\d{4,}))? (?P<price>\d[\d.]*,\d{6})"
                     r" (?P<shares>[+-] ?" + NUM + r") (?P<date>" + DATE + r") " + DATE + r"$", line)
        if r and isin and "Bestand am" not in line:
            shares = r.group("shares").replace(" ", "")
            if r.group("amount") == "0,00" and float(shares.replace(".", "").replace(",", ".")) == 0:
                continue                                    # a distribution of nothing
            out.append(f"DEKAROW {isin} | {name or ''} | {shares[0]}{r.group('type').strip()} | {r.group('amount')} | {r.group('price')} | "
                       f"{shares} | {r.group('date')}")
            continue
        out.append(line)
    return "\n".join(out)


def sections(text: str) -> str:
    """A Tagesauszug's section heading — VERKAUF, AUSLIEFERUNG — put
    on the line that names the fund, where the section's piece can see it."""
    out, heading = [], None
    for line in text.split("\n"):
        h = re.match(r"^([A-ZÄÖÜ]{4,})(?: [A-ZÄÖÜ/ ]+)?\s*(?:/ .*)?$", line)
        if h and h.group(1) not in ("ISIN", "EUR"):
            heading = h.group(1)
        elif heading and re.match(r"^(?:Fonds)?[Bb]ezeichnung: ", line):
            line = f"{heading} {line}"
        out.append(line)
    return "\n".join(out)


SPEC = Spec(
    slug="dekabank_pdf",
    label="DekaBank — Depotauszug PDF",
    corpus="dekabank",
    marks=[r"DekaBank", r"deka\.de"],
    preprocess=lambda text: sections(report(text)),
    docs=[
        Doc(kind="rows", when=r"^Umsatz(?:-Jahres)?.bersicht", block=ROW, fields=ROW_FIELDS,
            kinds={PAYOUT: "skip", FEE: "fee", TRANSFER: "transfer", r"^-": "sell", r"^\+": "buy"}),
        # The income behind a reinvested distribution.
        Doc(kind="rows", when=r"^Umsatz(?:-Jahres)?.bersicht", block=ROW + r"[^\n]*\| [+-](?:Aussch.ttung / Kauf aus Ertrag|Abrechnungsbetrag Aussch.ttung|Thesaurierung / Kauf aus Ertrag|Abrechnungsbetrag Thesaurierung|Verkauf aus Ertrag)",
            fields=ROW_FIELDS, kinds={r".": "dividend"}, also=True),
        Doc(kind="fee", when=r"^D ?epotpreis in[ck]l", fields=FEE_FIELDS, also=True),
        Doc(kind="trade", when=r"^(?:Wertpapierabrechnung|Depot-Tagesauszug)", block=SECTION, sell=r"Anteilumsatz: -",
            transfer=r"^(?:AUSLIEFERUNG|EINLIEFERUNG) ", fields=SECTION_FIELDS),
        Doc(kind="dividend", when=r"^ERTRAGS(?:ABRECHNUNG|AUSSCH.TTUNG)", block=SECTION, fields=PAYOUT_FIELDS, also=True),
    ],
)
