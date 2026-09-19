"""Trade Republic — Wertpapierabrechnung, Sparplan, Dividende,
Zinsabrechnung, Vorabpauschale, Steuerabrechnung, Kontoauszug; the
same paper in German, English, French, Italian and Spanish.

The Kontoauszug since 2024 is a table whose date is broken over three
lines — "01 Jan." above the row, "2025" below it — and whose amount
sits in one of two columns, in or out, that the text no longer tells
apart. `statement()` puts every row back on one line with its date
made whole and its sign taken from the running balance, and the doc
below reads those lines. Trades and dividends listed there are left
to the statements that carry the units and the taxes.
"""

from __future__ import annotations

import re

from ..statement import MONTHS, Doc, Spec, parse_number

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}[./]\d{2}[./]\d{4}|\d{4}-\d{2}-\d{2}"
UNITS = r"Stk\.|St.cke?|Pcs\.|Pz\.|titre\(s\)|t.t\.|units?\.?|unit\.|Ud\.|Sh\."

# "DE12… 15.05.2019 -25,05 EUR": the booking line, after the fees and taxes.
HEAD = r"^(?:VERRECHNUNGSKONTO|CLEARING ACCOUNT|SETTLEMENT ACCOUNT|IBAN|COMPTE[^\n]*|CONTO DI TRANSITO|CUENTA DE EFECTIVO) [^\n]+\n"
BOOKED = HEAD + r"[^\n]*?(?:" + DATE + r") (?P<amount>-?" + NUM + r")(?: (?P<currency>[A-Z]{3}|€))?$"
BOOKED_DATE = HEAD + r"[^\n]*?(?P<date>" + DATE + r") -?" + NUM + r"(?: (?:[A-Z]{3}|€))?$"

TAX_WORDS = (r"(?:Kapitalertrags?steuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer|Withholding Tax|Zinssteuer|Zinsabschlagsteuer"
             r"|Retenci.n IRPF|Pr.l.vements sociaux|Imp.t|Ritenuta|Capital gains tax|Church tax|Solidarity surcharge)")
# A charge carries a minus; a bare figure is a credit — the Optimierung
# after a loss, the reversal of a charge — and is a row of its own.
TAX_LINES = [r"^(?:\d+ )?" + TAX_WORDS + r"(?: [^\n]*?)? (?P<sign>-)(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3}|€)$"]
REFUND_LINES = [r"^(?:\d+ )?" + TAX_WORDS + r"(?: [^\n]*?)?(?P<refund> )(?P<tax>" + NUM + r") (?P<currency>[A-Z]{3}|€)$",
                r"^(?P<refund>Erstattung)[^\n]*? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3}|€)$"]
REFUND_HEAD = r"^(?:\d+ )?(?:" + TAX_WORDS + r"|Erstattung)(?: [^\n]*?)? (?:[1-9][\d.,]*|0[.,]\d*[1-9]\d*) (?:[A-Z]{3}|€)$"
FX = [r"(?P<fx_rate>" + NUM + r") (?P<fx_pair>EUR/[A-Z]{3})"]
FEE_LINES = [r"^(?:Fremdkostenzuschlag|External cost surcharge|Supplemento spese di terzi|Frais externes|Frais de tiers"
             r"|Tarifa plana por costes[^\n]*|Abwicklungspauschale|Geb.hr[^\n]*|Fee[^\n]*|Commission[^\n]*|Frais[^\n]*|Comisi.n[^\n]*)"
             r" (?P<sign>-?)(?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"]

TRADE_FIELDS = {
    "security": [r"^(?:ISIN ?: )?" + ISIN + r"$"],
    "shares": [r"^(?P<name>.+?) (?P<shares>" + NUM + r") (?P<notation>" + UNITS + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$",
               # A bond: nominal in currency, price in per cent.
               r"^(?P<name>.+?) (?P<shares>" + NUM + r") (?P<notation>[A-Z]{3}) (?P<price>" + NUM + r") % " + NUM + r" [A-Z]{3}$",
               r"^(?P<name>.+?) (?P<shares>" + NUM + r") (?P<notation>" + UNITS + r")",
               r"^(?P<name>.+?) (?P<shares>" + NUM + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$",
               r"^\d+ (?:Tilgung|Repayment) (?P<name>.+?) (?P<shares>" + NUM + r") (?P<notation>" + UNITS + r")"],
    "date": [r"^(?:Market|Limit|Stop)[- ]?Order[^\n]*?(?P<date>" + DATE + r")",
             r"^(?:Sparplanausf.hrung|Savings plan execution|Ex.cution de l'investissement|Esecuzione del piano|Ejecuci.n del plan|Ejecuci.n del Saveback"
             r"|Saveback[- ]?Ausf.hrung|Round[- ]?up[- ]?Ausf.hrung|Esecuzione del Saveback|Ex.cution du Saveback)[^\n]*?(?P<date>" + DATE + r")",
             r"^(?:ÜBERSICHT|OVERVIEW|PANORAMICA|R.CAPITULATIF|RESUMEN)\n[^\n]*?(?P<date>" + DATE + r")",
             BOOKED_DATE,
             r"\b(?:DATUM|DATE|DATA|FECHA) ?(?P<date>" + DATE + r")"],
    "amount": [BOOKED, r"^(?:GESAMT|TOTAL|TOTALE|Montant total) (?P<amount>-" + NUM + r") (?P<currency>[A-Z]{3}|€)$",
               r"^SUMME (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"^(?:AUSF.HRUNG|EXECUTION|ESECUZIONE|EX.CUTION|EJECUCI.N) (?P<ref>\S+)$"],
    "fees": FEE_LINES,
    "taxes": TAX_LINES,
    "fx": FX,
}

CREDIT_FIELDS = {
    "security": [r"^(?:ISIN ?: )?" + ISIN + r"(?: |$)", r"^(?P<name>.+)\n(?:ISIN ?: )?" + ISIN + r"$"],
    "shares": [r"(?P<shares>" + NUM + r") (?P<notation>" + UNITS + r")"],
    "date": [BOOKED_DATE, r"\b(?:DATUM|DATE|DATA|FECHA) ?(?P<date>" + DATE + r")"],
    "amount": [BOOKED, r"^(?:GESAMT|TOTAL|TOTALE|Gesamt|Montant total) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3}|€)$"],
    "fees": FEE_LINES,
    "taxes": TAX_LINES,
    "fx": FX,
}

REFUND_FIELDS = {
    "date": [BOOKED_DATE, r"\b(?:DATUM|DATE|DATA|FECHA) ?(?P<date>" + DATE + r")"],
    "security": [r"^(?:ISIN ?: )?" + ISIN + r"(?: |$)"],
    "taxes": REFUND_LINES,
}

INTEREST_SECTION = {
    "date": [BOOKED_DATE, r"\b(?:DATUM|DATE|DATA|FECHA) ?(?P<date>" + DATE + r")"],
    "amount": [r"^(?:Gesamt|Total|Totale) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3}|€)$"],
    "taxes": TAX_LINES,
}

TRANSFER_FIELDS = {
    "date": [r"^(?P<amount>" + NUM + r") €(?: " + NUM + r" €)? \S+ (?P<date>" + DATE + r") "],
    "amount": [r"^(?P<amount>" + NUM + r") (?P<currency>€)(?: " + NUM + r" €)? \S+ (?:" + DATE + r") "],
}

TAX_FIELDS = {**CREDIT_FIELDS,
              "amount": [BOOKED, r"^(?:GESAMT|SUMME|TOTAL) (?P<amount>-?" + NUM + r")(?: (?P<currency>[A-Z]{3}))?$"]}

# ── the old Kontoauszug (to 2023): one line per booking, the value date under it ──
OLD_ROW = (r"^\d{2}\.\d{2}\.\d{4} (?:Accepted PayIn|PayOut|Zinsen|Steuern|Steueroptimierung|Geb.hr|Einzahlung|Auszahlung|Customer .* inpayed"
           r"|Your interest payment)[^\n]* -?" + NUM + r"$")
OLD_FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.\d{4}) "],
    "amount": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>.+?) (?P<amount>-?" + NUM + r")$"],
    "type": [r"^\d{2}\.\d{2}\.\d{4} (?P<type>.+?) -?" + NUM + r"$"],
}

# ── the Kontoauszug since 2024, after `statement()` ──
NEW_FIELDS = {
    "date": [r"^TRROW (?P<date>\d{4}-\d{2}-\d{2}) "],
    "amount": [r"^TRROW \S+ (?P<type>\S+) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})"],
    "type": [r"^TRROW \S+ (?P<type>\S+) "],
}

TYPES = {
    "interest": r"Zinszahlung|Zinsen|Interest|Int.r.ts|Pago de intereses|Intereses|Interessi",
    "dividend": r"Ertr.ge|Earnings|Rendimientos|Rendimenti|Revenus|Dividende",
    "trade": r"^Handel$|^Trade$|^Comercio$|^Transaction$|^Negoziazione$|Sparplan",
    "tax": r"Steuern|Taxes|Impuestos|Imposte|Imp.ts",
    "fee": r"Geb.hr|Fees?|Comisi|Frais|Commissioni",
}
OUT = (r"PayOut|Outgoing|Auszahlung|Ausgehend|saliente|sortant|in uscita|Lastschrift|Direct Debit|domiciliaci|pr.l.vement|addebito diretto"
       r"|Comisi.n|Geb.hr|\bFees?\b|Frais|Commissioni|Kapitalertragss?teuer\b|Steuern Steuern")
IN = (r"Einzahlung|Incoming|Deposit accepted|Ingreso aceptado|entrante|Versement|Bonifico in entrata|Accepted PayIn"
      r"|Pr.mie|Reward|Recompensa|R.compense|Premio|Saveback|Referral|Zins|interest|int.r.t|interes|Ertr.ge|Earnings|Rendimi|Revenus"
      r"|Optimi|Erstattung|Refund")
TYPE_WORDS = (r"Zinszahlung|Zinsen|Überweisung|Kartentransaktion|Erträge|Prämie|Handel|SEPA-Lastschrift|Steuern|Gebühren|Gebühr"
              r"|Interest|Transfer|Card Transaction|Earnings|Reward|Trade|Taxes|Fees"
              r"|Pago de intereses|Transferencia|Transacción con tarjeta|Rendimientos|Recompensa|Comercio|Impuestos|Comisiones"
              r"|Intérêts|Virement|Paiement par carte|Revenus|Récompense|Transaction|Impôts|Frais"
              r"|Interessi|Bonifico|Pagamento con carta|Rendimenti|Premio|Negoziazione|Commercio|Imposte|Commissioni"
              r"|Referral|Transacci.n|Tarjeta|Comisi.n|Intereses|Pago")


def _year_for(month: int, period) -> int | None:
    if not period:
        return None
    (m1, y1), (m2, y2) = period
    if y1 == y2:
        return y1
    return y1 if month >= m1 else y2


def _month(token: str) -> int | None:
    return MONTHS.get(token.lower().rstrip(".").replace("é", "e").replace("û", "u"))


def statement(text: str) -> str:
    """Rewrite the rows of a 2024-style Kontoauszug into one canonical
    line each: `TRROW <date> <type> <signed amount> EUR <description>`.
    Everything else is left as it is."""
    # The second page, "Steuerliche Behandlung", explains the tax in
    # German notation under an English first page; nothing on it is a
    # booking.
    text = re.split(r"\n(?:STEUERLICHE BEHANDLUNG|TAX TREATMENT|TRAITEMENT FISCAL|TRATTAMENTO FISCALE|TRATAMIENTO FISCAL)\s*\n", text, 1)[0]
    # The rate is the foreign currency per euro whichever way the pair
    # is printed — "1.1599 USD/EUR" on one paper, "1.0894 EUR/USD" on the next.
    text = re.sub(r"(\d) ([A-Z]{3})/EUR\b", r"\1 EUR/\2", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    if not re.search(r"^(?:UMSATZ.BERSICHT|TRANSACCIONES DE CUENTA|TRANSACTIONS|RELEV. DE TRANSACTION|MOVIMENTI|TRANSAZIONI SUL CONTO|ACCOUNT TRANSACTIONS)\s*$", text, re.M):
        return text
    period = None
    m = re.search(r"\b(?:DATUM|DATE|FECHA|DATA) (\d{2}) (\S+) (\d{4}) - (\d{2}) (\S+) (\d{4})", text)
    if m and _month(m.group(2)) and _month(m.group(5)):
        period = ((_month(m.group(2)), int(m.group(3))), (_month(m.group(5)), int(m.group(6))))
    balance = None
    m = re.search(r"^(?:PRODUKT|PRODUCTO|PRODUCT|PRODUIT|PRODOTTO) [^\n]*\n[^\n]*? (-?" + NUM + r") €", text, re.M)
    if m:
        balance = parse_number(m.group(1), "de")
    lines = text.split("\n")
    out: list[str] = []
    row: list[str] | None = None
    in_table = False

    def flush():
        nonlocal balance, row
        if not row:
            return
        joined = " ".join(row)
        lines_of_row, row = row, None
        m = re.match(r"^(\d{2}) (.*)$", joined)
        if not m:
            out.append(joined)
            return
        day, rest = int(m.group(1)), m.group(2)
        tokens = rest.split(" ")
        month = at = None
        # The month can trail the description: "16 … Feb. SEPA-Lastschrift …"
        for i, t in enumerate(tokens):
            if _month(t) and re.fullmatch(r"[A-Za-zÀ-ÿ]{3,9}\.?", t):
                month, at = _month(t), i
                break
        if month is None:
            out.append(joined)
            return
        # The year: right after the month on a one-line row, at the
        # start of a line of its own below a broken one, else from the
        # statement's period.
        year = None
        plausible = {period[0][1], period[1][1]} if period else None
        if at + 1 < len(tokens) and re.fullmatch(r"20\d{2}", tokens[at + 1]):
            year = int(tokens[at + 1])
        else:
            for line in lines_of_row:
                ym = re.match(r"^(20\d{2})(?: |$)", line)
                if ym and (plausible is None or int(ym.group(1)) in plausible):
                    year = int(ym.group(1))
                    break
        year = year or _year_for(month, period)
        if year is None:
            out.append(joined)
            return
        # "1.234,56 €" on the German paper, "€1,234.56" on the English;
        # the amount and the balance are the first two, whatever the
        # page prints after the row.
        if re.search(r"€\d[\d,]*\.\d{2}\b", joined):
            style, amounts = "en", re.findall(r"€(-?" + NUM + r")", joined)
        else:
            style, amounts = "de", re.findall(r"(-?" + NUM + r") ?€", joined)
        if not amounts:
            out.append(joined)
            return
        amount = abs(parse_number(amounts[0], style) or 0.0)
        new_balance = parse_number(amounts[1], style) if len(amounts) >= 2 else None
        tm = re.search(TYPE_WORDS, joined, re.I)
        kind_word = tm.group(0) if tm else "Buchung"
        # In or out: the wording decides where it can, the running
        # balance where it cannot (a refund on the card, say).
        if re.search(OUT, joined, re.I):
            signed = -amount
        elif re.search(IN, joined, re.I):
            signed = amount
        elif balance is not None and new_balance is not None:
            signed = amount if new_balance > balance else -amount
        elif re.search(r"Kartentransaktion|Card Transaction|tarjeta|carte|carta", joined, re.I):
            signed = -amount
        else:
            signed = amount
        if new_balance is not None:
            balance = new_balance
        desc = re.sub(r"\s+", " ", joined).strip()
        figure = f"{signed:.2f}" if style == "en" else f"{signed:.2f}".replace(".", ",")   # the table's own notation
        out.append(f"TRROW {year:04d}-{month:02d}-{day:02d} {kind_word.replace(' ', '_')} {figure} EUR {desc}")

    for line in lines:
        if re.match(r"^(?:DATUM|DATE|FECHA|DATA) (?:TYP|TYPE|TIPO) ", line):
            flush()
            in_table = True
            out.append(line)
            continue
        if in_table and re.match(r"^(?:Seite \d|Page \d|P.gina \d|Pagina \d|Trade Republic Bank GmbH|HAFTUNGSAUSSCHLUSS|BARMITTEL|Erstellt am|Generated on|Created on|Creado en|Cr.. le|Creato il|KONTO.BERSICHT|TRANSAKTIONS.BERSICHT|RESUMEN DE|ACCOUNT SUMMARY|SYNTH.SE)", line):
            flush()
            in_table = False
            out.append(line)
            continue
        if in_table and re.match(r"^\d{2}(?: |$)", line):
            flush()
            row = [line.rstrip()]
            continue
        if in_table and row is not None:
            row.append(line.rstrip())
            continue
        out.append(line)
    flush()
    return "\n".join(out)


SPEC = Spec(
    slug="traderepublic_pdf",
    label="Trade Republic — Abrechnung PDF",
    corpus="traderepublic",
    marks=[r"TRADE REPUBLIC BANK GMBH", r"Trade Republic Bank GmbH", r"traderepublic\.com"],
    number="auto",
    preprocess=statement,
    docs=[
        Doc(kind="skip", when=r"^(?:STORNO|STORNIERUNG)\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="rows", when=r"^(?:UMSATZ.BERSICHT|TRANSACCIONES DE CUENTA|TRANSACTIONS|RELEV. DE TRANSACTION|MOVIMENTI|TRANSAZIONI SUL CONTO|ACCOUNT TRANSACTIONS)\s*$",
            block=r"^TRROW (?!\S+ (?:Handel|Trade|Comercio|Commercio|Transaction|Negoziazione|Ertr.ge|Earnings|Rendimientos|Rendimenti|Revenus) )",
            fields=NEW_FIELDS,
            kinds={TYPES["interest"]: "interest", TYPES["tax"]: "tax", TYPES["fee"]: "fee"}),
        Doc(kind="rows", when=r"^KONTOAUSZUG\s*$", block=OLD_ROW, fields=OLD_FIELDS,
            kinds={r"Zinsen|interest": "interest", r"^Steuer": "tax", r"^Geb": "fee"}),
        Doc(kind="trade", when=r"^(?:WERTPAPIERABRECHNUNG|SECURITIES SETTLEMENT|REGOLAMENTO TITOLI|LIQUIDACI.N DE VALORES|CONFIRMATION D'EX.CUTION"
                                r"|CONFIRMATION DE L'INVESTISSEMENT|PIANO D'INVESTIMENTO|ABRECHNUNG CRYPTO|RELEV. DE TRANSACTION)",
            sell=r"(?i)^(?:[\w-]*Order ?)?(?:Verkauf|Sell|Vendita|Vente|Venta)\b", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^(?:TILGUNG|REPAYMENT)\s*$", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^VORABPAUSCHALE\s*$", fields=TAX_FIELDS),
        Doc(kind="tax", when=r"^(?:STEUERABRECHNUNG|STEUERLICHE OPTIMIERUNG|STEUERKORREKTUR)\s*$", fields=TAX_FIELDS),
        # A tax credit printed under a sale or a dividend: its own row,
        # taken out of the booked total.
        Doc(kind="tax", when=REFUND_HEAD, fields=REFUND_FIELDS, also=True, split=True),
        # Interest on cash and on the money-market fund settled on one
        # paper, a section each: one row per section.
        Doc(kind="interest", when=r"^(?:ABRECHNUNG ZINSEN|INTEREST INVOICE|RAPPORT D'INT.R.TS|INFORME DE INTERESES|RESOCONTO INTERESSI)",
            block=r"^(?:ABRECHNUNG|INVOICE|RELEV.|FATTURAZIONE|LIQUIDACI.N) - ", fields=INTEREST_SECTION),
        Doc(kind="interest", when=r"^(?:ABRECHNUNG ZINSEN|INTEREST INVOICE|RAPPORT D'INT.R.TS|INFORME DE INTERESES|RESOCONTO INTERESSI|ZINSZAHLUNG)",
            fields=CREDIT_FIELDS),
        Doc(kind="dividend", when=r"^(?:DIVIDENDE|AUSSCH.TTUNG|BARAUSSCH.TTUNG|CASH DIVIDEND|DIVIDEND|DIVIDENDE EN ESP.CES|DIVIDENDO|DISTRIBUZIONE|DISTRIBUTION)\s*$",
            fields=CREDIT_FIELDS),
        Doc(kind="deposit", when=r"^(?:ABRECHNUNG EINZAHLUNG|R.GLEMENT DU VERSEMENT)", fields=CREDIT_FIELDS),
        Doc(kind="tax", when=r"^AUSSCH.TTUNG / AUSSCH.TTUNGSGLEICHER ERTRAG", fields={
            "security": [r"^" + ISIN + r" \| (?P<name>.+?) -?" + NUM + r" €$"],
            "date": [r"\bDATUM (?P<date>" + DATE + r")"],
            "amount": [r"^[A-Z]{2}[A-Z0-9]{9}\d \| .+? (?P<amount>-?" + NUM + r") (?P<currency>€)$"],
        }),
        # A transfer confirmation: to the account when the sender is
        # named, from it when the recipient is.
        Doc(kind="deposit", when=r"^ÜBERWEISUNGSBEST.TIGUNG\s*\n(?:[^\n]*\n){0,6}ANGABEN ZUM SENDER", fields=TRANSFER_FIELDS),
        Doc(kind="withdrawal", when=r"^ÜBERWEISUNGSBEST.TIGUNG\s*\n(?:[^\n]*\n){0,6}ANGABEN ZUM EMPF.NGER", fields=TRANSFER_FIELDS),
        Doc(kind="fee", when=r"^PAIEMENTS PAR CARTE|^KARTENZAHLUNGEN|^CARD PAYMENTS", fields={
            "date": [r"^(?:Carte|Karte|Card)[^\n]*? (?P<date>" + DATE + r") \d"],
            "amount": [r"^(?:Total|Gesamt|GESAMT|TOTAL) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3}|€)$"],
        }),
    ],
)
