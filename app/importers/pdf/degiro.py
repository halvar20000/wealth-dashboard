"""DEGIRO — the Transaktionsübersicht (one line per execution) and the
Kontoauszug (one line per cash movement), in every language DEGIRO
prints them in.

The account statement lists everything the cash account saw: the
purchases and sales that the transaction overview already carries
with units and prices, the currency exchanges around them, the
sweeps to and from the flatex cash account, the money-market fund
conversions. Those are left out; what the statement contributes is
the money in and out, the dividends and their withholding tax, the
exchange connection fees and the interest.
"""

from __future__ import annotations

import re

from ..statement import Doc, Spec, detect_style, parse_number

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"-?[\d.,']+"
NUMSP = r"-?\d{1,3}(?: \d{3})+(?:,\d+)?|-?[\d.,']+"          # Polish thousands: "-2 080,00"
DATE = r"\d{2}-\d{2}-\d{4}"
ROW = r"^" + DATE + r" \d{2}:\d{2} "

# ── the transaction overview: date time product ISIN exchange [venue] qty price value local [fx] fee total ──
TRADE = (ROW + r"(?P<name>.+?) " + ISIN + r" \S+(?: [A-Z]{4})? (?P<shares>" + NUM + r") (?P<price>" + NUMSP + r") (?P<price_currency>[A-Z]{3})"
         r" (?:" + NUMSP + r") [A-Z]{3} (?:" + NUMSP + r") [A-Z]{3}(?: " + NUM + r")?(?: (?P<sign>-?)(?P<fee>[\d.,']+) [A-Z]{3}| [A-Z]{3})? (?P<amount>" + NUMSP + r") (?P<currency>[A-Z]{3})$")
TRADE_OLD = (ROW + r"(?P<name>.+?) " + ISIN + r" \S+(?: [A-Z]{4})? (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}) (?P<price>" + NUM + r")"
             r" [A-Z]{3} " + NUM + r" [A-Z]{3} " + NUM + r"(?: " + NUM + r")?(?: [A-Z]{3} (?P<sign>-?)(?P<fee>[\d.,]+))? (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")$")
TRADE_NEW = (ROW + r"(?P<name>.+?) " + ISIN + r" \S+(?: [A-Z]{4})? (?P<shares>" + NUM + r") (?P<price>" + NUMSP + r") (?P<price_currency>[A-Z]{3})"
             r" (?:" + NUMSP + r") (?P<currency>[A-Z]{3}) (?:" + NUMSP + r") " + NUM + r"(?: (?P<sign>-?)(?P<fee>[\d.,']+))? (?P<amount>" + NUMSP + r")$")
TRADE_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "security": [TRADE, TRADE_OLD, TRADE_NEW],
    "amount": [TRADE, TRADE_OLD, TRADE_NEW],
    "fees": [TRADE, TRADE_OLD, TRADE_NEW],
}

# ── the account statement ──
IN = r"Einzahlung|Deposit|Deposito|Dep.sito|Storting|Wp.ata|Vklad|D.p.t|Versement"
OUT = r"Auszahlung|Withdrawal|Prelievo|Opname|Retirada|Retrait|Wyp.ata|V.b.r"
DIV = r"Dividende|Dividend|Dividendo|Dividenda|Fondsaussch.ttung|Aussch.ttung|Uitkering|Distribuzione"
TAX = r"Dividendensteuer|Dividendbelasting|Dividend Tax|Retenci.n|Ritenuta|Podatek|\bDa.\b|Imposta|Withholding|steuer\b|Tax\b|Belasting|Imp.t"
FEE = (r"Einrichtung von|Aansluitingskosten|Exchange Connection|Conexi.n|connessione|Weitergabegeb.hr|ADR/GDR|Neukundenaktion"
       r"|Zahlungsgeb.hr|Geb.hr|Fee\b|Kosten|Coste|Costi|Op.ata|[Pp]oplatek|Frais|Commissioni")
INT = r"Interest|Zinsen|Rente\b|Inter.s|Interessi|Odsetki|\b.rok|Int.r.ts|Juros"
# Rows that belong to something else: the trade's own fee, the cash
# sweeps, the currency legs, the money-market fund, the trades themselves.
NOT = (r"Transaktionsgeb.hr|Transaction fee|Transactiekosten|transazione|transacci.n|transakcyjna|poplatek za transak|transa..o"
       r"|Cash Sweep|Geldkonto|geldrekening|Cuenta de Efectivo|conto deposito|Compte esp.ces|W.hrungswechsel|Valuta|FX |Cambio|Wisselkoers|Change"
       r"|Geldmarktfonds|Money Market|monetario|Geldmarkt|mon.taire|Kompensation|Reservation")
STATEMENT_ROW = ROW + r"(?!.*(?:" + NOT + r"))(?:[^\n]*? )?(?:" + IN + r"|" + OUT + r"|" + DIV + r"|" + TAX + r"|" + FEE + r"|" + INT + r")"
STATEMENT_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "security": [ROW + r"(?:\d{2}-\d{2}-\d{4} )?(?P<name>.+?) " + ISIN + r" "],
    "amount": [ROW + r"(?:\d{2}-\d{2}-\d{4} )?(?:.+? [A-Z]{2}[A-Z0-9]{9}\d )?(?P<type>.+?)(?: \[(?:tax|fee) [^\]]+\])* (?:[\d.,]+ )?(?P<currency>[A-Z]{3}) (?P<amount>" + NUMSP + r")(?: [A-Z]{3} (?:" + NUMSP + r"))?$"],
    "type": [ROW + r"(?:\d{2}-\d{2}-\d{4} )?(?:.+? [A-Z]{2}[A-Z0-9]{9}\d )?(?P<type>.+?)(?: \[(?:tax|fee) [^\]]+\])* (?:[\d.,]+ )?[A-Z]{3} (?:" + NUMSP + r")(?: [A-Z]{3} (?:" + NUMSP + r"))?$"],
    "taxes": [r"\[tax (?P<tax>[\d.,']+)\]"],
    "fees": [r"\[fee (?P<fee>[\d.,']+)\]"],
}

NOTE_FIELDS = {
    "security": [r"^Security name: (?P<name>.+)$", r"^Security ISIN: " + ISIN],
    "date": [r"^Dividend date \(Pay date\): (?P<date>\d{4}-\d{2}-\d{2})"],
    "shares": [r"^(?P<shares>[\d.,]+) [\d.,]+ [\d.,]+ -?[\d.,]+ [\d.,]+ [A-Z]{3}$"],
    "amount": [r"^[\d.,]+ [\d.,]+ [\d.,]+ -?[\d.,]+ (?P<amount>[\d.,]+) (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^[\d.,]+ [\d.,]+ [\d.,]+ (?P<sign>-?)(?P<tax>[\d.,]+) [\d.,]+ (?P<currency>[A-Z]{3})$"],
}

LINE = re.compile(r"^(?P<stamp>" + DATE + r" \d{2}:\d{2}) (?:\d{2}-\d{2}-\d{4} )?(?:(?P<name>.+?) (?P<isin>[A-Z]{2}[A-Z0-9]{9}\d) )?(?P<desc>.+?) (?P<ccy>[A-Z]{3}) (?P<amount>" + NUMSP + r")(?P<rest>(?: [A-Z]{3} (?:" + NUMSP + r"))?)$")


def tidy(text: str) -> str:
    """A dividend's withholding tax is a row of its own, printed with
    the same time stamp and ISIN as the dividend: folded into it here,
    so the dividend row carries the cash that arrived and the tax
    beside it, as every other bank's paper does."""
    style = detect_style(text)
    fmt0 = (lambda v: f"{v:.2f}".replace(".", ",")) if style == "de" else (lambda v: f"{v:.2f}")

    def two_fees(m):
        a, b = parse_number(m.group(2), style), parse_number(m.group(3), style)
        return f"{m.group(1)} {fmt0(a + b)} {m.group(4)}" if a is not None and b is not None else m.group(0)
    # The 2019 layout has two fee columns, the AutoFX one and the
    # transaction one: one fee here.
    text = re.sub(r"^(" + ROW[1:] + r".+ [A-Z]{3} -?[\d.,']+ [A-Z]{3} -?[\d.,']+ [\d.,']+) (-?[\d.,']+) (-?[\d.,']+) (-?[\d.,']+)$",
                  two_fees, text, flags=re.M)
    lines = text.split("\n")
    parsed = [LINE.match(line) for line in lines]
    dividends: dict[tuple, int] = {}
    for i, m in enumerate(parsed):
        if m and m.group("isin") and re.search(DIV, m.group("desc")) and not re.search(TAX, m.group("desc")):
            dividends.setdefault((m.group("stamp"), m.group("isin"), m.group("ccy")), i)
    fmt = (lambda v: f"{v:.2f}".replace(".", ",")) if style == "de" else (lambda v: f"{v:.2f}")
    drop: set[int] = set()
    folded: dict[int, tuple[float, float]] = {}            # dividend line → (net, tax)
    fees: dict[int, float] = {}
    for i, m in enumerate(parsed):
        if not m or not m.group("isin"):
            continue
        is_tax, is_fee = bool(re.search(TAX, m.group("desc"))), bool(re.search(r"ADR/GDR|Weitergabegeb.hr", m.group("desc")))
        if not (is_tax or is_fee):
            continue
        j = dividends.get((m.group("stamp"), m.group("isin"), m.group("ccy")))
        if j is None or j in drop:
            continue
        d = parsed[j]
        gross, charge = parse_number(d.group("amount"), style), parse_number(m.group("amount"), style)
        if gross is None or charge is None:
            continue
        net, old_tax = folded.get(j, (gross, 0.0))
        if is_tax:
            folded[j] = (round(net + charge, 2), round(old_tax - charge, 2))   # the tax row is negative
        else:
            folded[j] = (round(net + charge, 2), old_tax)
            fees[j] = round(fees.get(j, 0.0) - charge, 2)
        drop.add(i)
    # A dividend in dollars is changed into the account's currency by
    # a pair of rows — the dollars out, with the rate, the euros in —
    # printed when the exchange ran. The dividend row gets the euros
    # that arrived and its tax at the same rate.
    fx = [(i, m) for i, m in enumerate(parsed) if m and re.search(r"W.hrungswechsel|FX |Valuta|Cambio|Wisselkoers|Change", m.group("desc"))]
    used: set[int] = set()
    for j, d in enumerate(parsed):
        if not d or j in drop or j not in folded and not (d.group("isin") and re.search(DIV, d.group("desc")) and not re.search(TAX, d.group("desc"))):
            continue
        net, tax = folded.get(j, (parse_number(d.group("amount"), style) or 0.0, 0.0))
        out_leg = next((i for i, m in fx if i not in used and m.group("ccy") == d.group("ccy")
                        and abs((parse_number(m.group("amount"), style) or 0.0) + net) < 0.011), None)
        pooled = out_leg is None
        if pooled:
            # Several dividends changed in one go: the next exchange in
            # that currency (the rows run newest first) gives the rate.
            out_leg = next((i for i, m in fx if i < j and m.group("ccy") == d.group("ccy")
                            and (parse_number(m.group("amount"), style) or 0.0) <= -net + 0.011), None)
        if out_leg is None:
            continue
        stamp = parsed[out_leg].group("stamp")
        in_leg = next((i for i, m in fx if i not in used and i != out_leg and m.group("stamp") == stamp
                       and m.group("ccy") != d.group("ccy")), None)
        if in_leg is None:
            continue
        rate = None
        for i in (out_leg, in_leg):
            r = re.search(r" (\d[\d.,']*) [A-Z]{3} " + NUM + r" [A-Z]{3} " + NUM + r"$", lines[i])
            if r:
                rate = parse_number(r.group(1), style)
        home = parse_number(parsed[in_leg].group("amount"), style) or 0.0
        if pooled:
            if not rate:
                continue
            home = net / rate
        else:
            used.update((out_leg, in_leg))
        folded[j] = (abs(home), round(tax / rate, 2) if rate else 0.0)
        if j in fees and rate:
            fees[j] = round(fees[j] / rate, 2)
        parsed[j] = None                                    # rewritten below with the home currency
        lines[j] = (f"{d.group('stamp')} {d.group('name')} {d.group('isin')} {d.group('desc')} [tax {fmt(folded[j][1])}]"
                    f"{' [fee ' + fmt(fees[j]) + ']' if j in fees else ''} {parsed[in_leg].group('ccy')} {fmt(folded[j][0])}{d.group('rest')}")
    for j, (net, tax) in folded.items():
        d = parsed[j]
        if d is None:
            continue
        lines[j] = (f"{d.group('stamp')} {d.group('name')} {d.group('isin')} {d.group('desc')} [tax {fmt(tax)}]"
                    f"{' [fee ' + fmt(fees[j]) + ']' if j in fees else ''} {d.group('ccy')} {fmt(net)}{d.group('rest')}")
    return "\n".join(line for i, line in enumerate(lines) if i not in drop)


SPEC = Spec(
    slug="degiro_pdf",
    label="DEGIRO — Transaktionsübersicht / Kontoauszug PDF",
    corpus="degiro",
    marks=[r"DEGIRO B\.V\.", r"degiro\.(?:de|nl|com|es|it|fr|pl|cz|pt|ch|at|ie|gr|dk|se|fi|no|hu)"],
    number="auto",
    preprocess=tidy,
    docs=[
        Doc(kind="trade", when=r"^(?:Transaktions.bersicht|Transacties|Transacciones|Transactions|Transakcje|Transakce|Operazioni|Transa..es) "
                                r"(?:von|van|de|from|od|da|desde|du) ",
            block=ROW + r".+ [A-Z]{2}[A-Z0-9]{9}\d \S+", sell=ROW + r".+ [A-Z]{2}[A-Z0-9]{9}\d \S+(?: [A-Z]{4})? -\d", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Dividend note\b", fields=NOTE_FIELDS),
        Doc(kind="rows", when=r"^(?:Kontoauszug|Rekeningoverzicht|Estratto conto|Account [Ss]tatement|Estado de cuenta|P.ehled ..tu|Relev. de compte|Wyci.g|Extrato)\b",
            block=STATEMENT_ROW, fields=STATEMENT_FIELDS,
            kinds={INT: "interest", TAX: "tax", DIV: "dividend", FEE: "fee", IN: "deposit", OUT: "withdrawal"}),
    ],
)
