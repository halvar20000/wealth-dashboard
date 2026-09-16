"""Payslips — a Swiss Lohnabrechnung as a PDF, in two layouts.

A bank sees one line of a salary: the net that arrived. The payslip
carries the rest — the gross, the tax taken at source, the pension
contributions on both sides — and that is what the Income page shows
and what a tax return and a retirement forecast need. So a payslip
imports into the account the net lands in, and does two things:

  * it is kept whole, as a statement: period, gross, deductions, net,
    the employer's side, and every line the sheet printed;
  * it books what the bank never sees onto the account, zero-sum: the
    tax at source as income grossed up and tax paid, and each side's
    pension contribution as income grossed up and money invested. The
    net itself is NOT booked — the bank brings that.

Two layouts are read, told apart by their text:

  * **SAP** — the Lohnabrechnung of a large employer: wage codes in
    the left column (`0110 Monatsgehalt`, `/101 BRUTTO`, `/310
    Quellensteuer`, `6801 PF1 Beitrag AN`) and the employer's own
    contributions in a block of their own. German-formatted amounts,
    `14.852,65`, a trailing minus for a deduction.
  * **Lohnabrechnung** — the small employer's sheet: `Bruttolohn`,
    `AHV-Beitrag`, `ALV-Beitrag`, `BVG-Beitrag`, `Nettolohn`, Swiss
    apostrophes for thousands (`4’240.00`). Its text often arrives
    with the spaces missing and a capital O where a zero was printed,
    and is read all the same. It prints no employer block, so the
    employer's side is the statutory floor — AHV and ALV matched, BVG
    at the legal half — and says so.

Names are read from the sheet, never assumed: the same importer serves
every earner in a household.
"""

from __future__ import annotations

import re
from datetime import datetime

from .base import ParsedTxn, ParseResult
from .dkb_pdf import pdf_text

SLUG = "payslip"
LABEL = "Payslip (Lohnabrechnung PDF)"

_DE_MONTHS = {"januar": 1, "februar": 2, "märz": 3, "maerz": 3, "marz": 3, "april": 4, "mai": 5,
              "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11,
              "dezember": 12}


def matches(header: list[str], sample: str) -> bool:
    return _is_sap(sample) or _is_lohnabrechnung(sample)


def _is_sap(text: str) -> bool:
    return "/101 BRUTTO" in text and "Retro Beschreibung" in text


def _is_lohnabrechnung(text: str) -> bool:
    flat = text.replace(" ", "")
    return "Lohnabrechnung" in flat and "Bruttolohn" in flat and "Nettolohn" in flat


# ─── Numbers and dates ────────────────────────────────────────────────

def _de_amount(raw: str) -> float:
    """`14.852,65` → 14852.65; `787,20-` → −787.20."""
    s = raw.strip()
    sign = -1.0 if s.endswith("-") else 1.0
    s = s.rstrip("-").replace(".", "").replace(",", ".")
    return sign * float(s) if s else 0.0


def _ch_amount(raw: str) -> float:
    """`4’240.00`, `4'240.00`, `7’360.OO` (a printed O for a zero) → 4240.0."""
    s = raw.replace("’", "").replace("'", "").replace(" ", "").replace("\xa0", "")
    s = s.replace("O", "0").replace("o", "0")
    return float(s) if s not in ("", "-") else 0.0


def _month(name: str) -> int | None:
    return _DE_MONTHS.get(name.lower())


def _unglue(s: str) -> str:
    """`Marie-AngeWelker` → `Marie-Ange Welker`: a sheet whose text lost
    its spaces still changes case where a word begins."""
    s = re.sub(r"(?<=[a-zäöü])(?=[A-ZÄÖÜ])", " ", s)
    s = re.sub(r"(?<=[a-zäöü])(für|und|der|des|de|du|et|of|and)(?= )", r" \1", s)
    return s.strip()


# ─── SAP ─────────────────────────────────────────────────────────────

_SAP_LINE = re.compile(
    r"^(\d{4}|/\d{3})\s+(.+?)\s+"            # wage code, description
    r"(?:([\d.]+,\d{2})\s+)?"                # basis
    r"(?:([\d.,]+)\s*%\s+)?"                 # rate
    r"([\d.]+,\d{2}-?)\s*$")                 # amount
_SAP_EMPLOYER_LINE = re.compile(r"^(.+?)\s+([\d.]+,\d{2}-?)\s*$")
_PENSION_CODES = ("6801", "6805", "6809", "6813", "6817", "6819")
_EMPLOYER_PENSION = ("PF1", "PF2", "KSP", "ÜV", "UV ", "BVG", "Pensionskasse")
_EMPLOYER_SOCIAL = ("FAK", "AHV", "ALV", "Nichtberufsunfall", "Berufsunfall", "Krankentaggeld", "IV ", "EO ")


def _parse_sap(text: str) -> dict:
    lines = [l.rstrip() for l in text.splitlines()]
    out = {"layout": "sap", "employer": None, "employee": None, "period": None, "paid_on": None,
           "currency": "CHF", "gross": 0.0, "base_salary": None, "bonus": 0.0, "allowances": 0.0,
           "employee_social": 0.0, "employee_pension": 0.0, "tax": 0.0, "other_deductions": 0.0,
           "net_paid": 0.0, "employer_pension": 0.0, "employer_social": 0.0,
           "employer_side_known": True, "lines": []}
    section = "head"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if section == "head":
            m = re.match(r"^(Herr|Frau|Mr|Mrs|Ms|M\.|Mme)\s+(.+?)\s*$", line)
            if m and not out["employee"]:
                out["employee"] = m.group(2).strip()
            m = re.match(r"^(.+?)Firma$", line)
            if m:
                out["employer"] = m.group(1).strip()
            m = re.match(r"^Monat\s+([A-Za-zäöüÄÖÜ]+)\s+(\d{4})", line)
            if m and _month(m.group(1)):
                out["period"] = f"{m.group(2)}-{_month(m.group(1)):02d}"
            m = re.match(r"^Valuta\s+(\d{2})\.(\d{2})\.(\d{4})", line)
            if m:
                out["paid_on"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            if line.startswith("Retro Beschreibung"):
                section = "wages"
            continue
        if line.startswith("Arbeitgeberbeiträge"):
            section = "employer"
            continue
        if line.startswith(("Bankverbindung", "Mitteilung")):
            section = "tail"
        if section == "tail":
            m = re.search(r"\b([\d.]+,\d{2})\s+([A-Z]{3})\s*$", line)
            if m and "CH" in line:
                out["currency"] = m.group(2)
            continue
        if section == "wages":
            if line.startswith("Auszahlung"):
                m = re.search(r"([\d.]+,\d{2})", line)
                if m:
                    out["net_paid"] = _de_amount(m.group(1))
                continue
            m = _SAP_LINE.match(line)
            if not m:
                continue
            code, desc = m.group(1), m.group(2).strip()
            basis = _de_amount(m.group(3)) if m.group(3) else None
            rate = float(m.group(4).replace(",", ".")) if m.group(4) else None
            amount = _de_amount(m.group(5))
            side = "income"
            if code == "/101":
                out["gross"] = amount; side = "total"
            elif code == "/260":
                side = "total"                       # the sum of the social deductions
            elif code == "/310":
                out["tax"] = amount; side = "tax"
            elif code == "/550":
                side = "total"                       # net before tax
            elif code == "/110":
                side = "total"                       # tax plus the other deductions
            elif code in ("/411", "/420"):
                out["employee_social"] += amount; side = "employee_deduction"
            elif code.startswith("/"):
                side = "total"
            elif code.startswith("6"):
                side = "employee_deduction"
                if code in _PENSION_CODES:
                    out["employee_pension"] += amount
                elif amount < 0:
                    out["other_deductions"] += amount
            else:
                if code == "0110":
                    out["base_salary"] = amount
                elif code.startswith("4"):
                    out["bonus"] += amount
                elif code.startswith(("5", "9")):
                    out["allowances"] += amount
            out["lines"].append({"code": code, "description": desc, "side": side,
                                 "basis": basis, "rate": rate, "amount": amount})
            continue
        if section == "employer":
            if line.startswith(("Beschreibung", "Sonderzahlungen", "Betrag")):
                continue
            m = _SAP_EMPLOYER_LINE.match(line)
            if not m:
                continue
            desc, amount = m.group(1).strip(), _de_amount(m.group(2))
            if any(k in desc for k in _EMPLOYER_PENSION):
                out["employer_pension"] += amount
            elif any(k in desc for k in _EMPLOYER_SOCIAL):
                out["employer_social"] += amount
            else:
                out["employer_social"] += amount
            out["lines"].append({"code": None, "description": desc, "side": "employer",
                                 "basis": None, "rate": None, "amount": amount})
    # The employee's social deductions on the sheet are the AHV/ALV lines
    # plus anything else in the 6xxx range that is not the pension; the
    # sheet's own /260 total is the check.
    for k in ("gross", "tax", "employee_social", "employee_pension", "other_deductions",
              "employer_pension", "employer_social", "bonus", "allowances", "net_paid"):
        out[k] = round(out[k], 2)
    return out


# ─── Lohnabrechnung ──────────────────────────────────────────────────

_AMT = r"-?\d[\d’'O]*\.[\dO]{2}"


def _parse_lohnabrechnung(text: str) -> dict:
    flat = text.replace(" ", "")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = {"layout": "lohnabrechnung", "employer": None, "employee": None, "period": None, "paid_on": None,
           "currency": "CHF", "gross": 0.0, "base_salary": None, "bonus": 0.0, "allowances": 0.0,
           "employee_social": 0.0, "employee_pension": 0.0, "tax": 0.0, "other_deductions": 0.0,
           "net_paid": 0.0, "employer_pension": 0.0, "employer_social": 0.0,
           "employer_side_known": False, "lines": []}
    if lines:
        out["employer"] = _unglue(lines[0])
    m = re.search(r"Lohnabrechnung\s*([A-Za-zäöüÄÖÜ]+?)\s*(\d{4})", text)
    if m and _month(m.group(1)):
        out["period"] = f"{m.group(2)}-{_month(m.group(1)):02d}"
        # The line after the title names the earner.
        for i, l in enumerate(lines):
            if "Lohnabrechnung" in l.replace(" ", "") and i + 1 < len(lines):
                out["employee"] = _unglue(lines[i + 1])
                break
    m = re.search(r"Auszahlung\s*am\s*(\d{2})\.(\d{2})\.(\d{4})", flat)
    if m:
        out["paid_on"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    else:
        m = re.search(r"Datum:\s*(\d{1,2})\.([A-Za-zäöüÄÖÜ]+)(\d{4})", flat)
        if m and _month(m.group(2)):
            out["paid_on"] = f"{m.group(3)}-{_month(m.group(2)):02d}-{int(m.group(1)):02d}"

    def grab(pattern: str, default: float = 0.0) -> float:
        mm = re.search(pattern, flat)
        return _ch_amount(mm.group(1)) if mm else default

    def line_item(label: str, amount: float, side: str, basis=None, rate=None):
        if amount:
            out["lines"].append({"code": None, "description": label, "side": side,
                                 "basis": basis, "rate": rate, "amount": round(amount, 2)})

    gross = grab(rf"Bruttolohn({_AMT})")
    monthly = grab(rf"(?<![.\dO])Monatslohn({_AMT})")
    hourly = grab(rf"Stundenlohn[^\n]*?({_AMT})\s*$") if "Stundenlohn" in flat else 0.0
    thirteenth = grab(rf"13\.Monatslohn({_AMT})")
    gratification = grab(rf"Gratifikation({_AMT})")
    # The deduction lines carry basis, rate and amount glued together;
    # the amounts having exactly two decimals is what tells them apart.
    def ded(label: str) -> float:
        mm = re.search(rf"{label}({_AMT})(\d+\.\d{{2}})%({_AMT})", flat)
        if mm:
            line_item(label, _ch_amount(mm.group(3)), "employee_deduction", _ch_amount(mm.group(1)), float(mm.group(2)))
            return _ch_amount(mm.group(3))
        mm = re.search(rf"{label}({_AMT})", flat)
        if mm:
            line_item(label, _ch_amount(mm.group(1)), "employee_deduction")
            return _ch_amount(mm.group(1))
        return 0.0
    ahv = ded("AHV-Beitrag")
    alv = ded("ALV-Beitrag")
    nbu = ded("NBUV?-Beitrag")
    bvg = ded("BVG-Beitrag")
    tax = ded("Quellensteuer")
    net = grab(rf"Nettolohn({_AMT})")
    paid = grab(rf"Auszahlung(?!am)({_AMT})") or grab(rf"Fr\.({_AMT})auf")
    out.update({
        "employer_side_known": False,
        "gross": gross, "base_salary": monthly or hourly or None,
        "bonus": round(thirteenth + gratification, 2),
        "employee_social": round(-(abs(ahv) + abs(alv) + abs(nbu)), 2),
        "employee_pension": round(-abs(bvg), 2),
        "tax": round(-abs(tax), 2),
        "net_paid": paid or net,
        # The statutory floor, since the sheet prints no employer block:
        # AHV and ALV are matched, BVG at the legal half.
        "employer_social": round(abs(ahv) + abs(alv), 2),
        "employer_pension": round(abs(bvg), 2),
    })
    line_item("Monatslohn", monthly, "income")
    line_item("Stundenlohn", hourly, "income")
    line_item("13. Monatslohn", thirteenth, "income")
    line_item("Gratifikation", gratification, "income")
    line_item("Bruttolohn", gross, "total")
    line_item("Nettolohn", net, "total")
    return out


# ─── The importer's contract ─────────────────────────────────────────

def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    text = pdf_text(content) if isinstance(content, bytes) else content
    slip = _parse_sap(text) if _is_sap(text) else _parse_lohnabrechnung(text)
    result = ParseResult()
    if not slip["period"] or not slip["gross"]:
        result.problems.append("the payslip's month or gross could not be read")
        return result
    slip["employee"] = slip["employee"] or "?"
    slip["employer"] = slip["employer"] or "?"
    result.payslip = slip
    result.rows = _legs(slip)
    return result


def _legs(slip: dict) -> list[ParsedTxn]:
    """What the bank never sees, booked zero-sum onto the account: the
    tax taken at source, and each side's pension contribution. Ids
    are the sheet's identity, so the same month twice is once."""
    day = slip["paid_on"] or f"{slip['period']}-25"
    ccy = slip["currency"]
    who = slip["employee"].split()[0] if slip["employee"] else "?"
    key = f"payslip:{slip['employer']}:{slip['employee']}:{slip['period']}".replace(" ", "_")
    rows: list[ParsedTxn] = []

    def pair(what: str, amount: float, out_kind: str, out_category: str, note: str):
        if amount <= 0.005:
            return
        rows.append(ParsedTxn(txn_date=day, description=f"{who} {slip['period']}: {note}, grossed up",
                              amount=round(amount, 2), currency=ccy, kind="deposit",
                              counterparty=slip["employer"], external_id=f"{key}:{what}:gross",
                              category="salary"))
        rows.append(ParsedTxn(txn_date=day, description=f"{who} {slip['period']}: {note}",
                              amount=round(-amount, 2), currency=ccy, kind=out_kind,
                              counterparty=slip["employer"], external_id=f"{key}:{what}",
                              category=out_category))

    pair("tax", abs(slip["tax"]), "tax", "tax", "tax at source")
    pair("pension", abs(slip["employee_pension"]), "transfer", "investment", "pension contribution, employee")
    pair("pension_employer", abs(slip["employer_pension"]), "transfer", "investment", "pension contribution, employer")
    return rows
