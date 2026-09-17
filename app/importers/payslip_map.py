"""A payslip nobody here has heard of, read through a mapping the user drew.

The two layouts in payslip.py took a real sheet each. Every other
payslip is the same thing under other labels: a list of labelled
amounts — `Bruttolohn 7'360.00`, `Salaire brut 4 120,50`, `Gross pay
3,200.00` — with a month somewhere near the top. So the user says
once which line is the gross, which the net, which the tax, which
the pension on each side, and the mapping is kept under the sheet's
own markers — the employer's name and the earner's — so that next
month's sheet from the same employer is recognised the way a Degiro
file is: by what is in it.

Nothing leaves the machine. A keyword catalogue pre-fills the choices
in the languages the app speaks and the ones payslips are printed in;
what is remembered is what the user confirmed, never the guess.

What a mapping holds:

    name, employer, employee      the sheet's markers, as typed
    format                        how numbers are written: de | ch | en | fr
    buckets: {bucket: [label, …]} the label text of each line that
                                  counts, per bucket
    period_label, paid_label      the label of the line carrying the
                                  month, and the payment date

Buckets, and their sign: gross, base, bonus, allowance, net are
amounts in; tax, social, pension, other are amounts out and are stored
negative whichever way the sheet prints them — a French bulletin
prints its retenues positive, an SAP sheet with a trailing minus —
because what a bucket means settles the sign, not the typography.
employer_pension and employer_social are the employer's side, in.
"""

from __future__ import annotations

import json
import re

from ..db import get_conn
from .base import ParseResult
from .payslip import _DE_MONTHS, _legs, _unglue

BUCKETS = ("gross", "base", "bonus", "allowance", "tax", "social", "pension", "other", "net",
           "employer_pension", "employer_social", "period", "paid", "employer", "employee")
AMOUNT_BUCKETS = BUCKETS[:11]
OUT_BUCKETS = ("tax", "social", "pension", "other")

# Month names, for the period line: the four languages and the ones
# payslips come printed in.
MONTHS = {**_DE_MONTHS,
          "january": 1, "february": 2, "march": 3, "may": 5, "june": 6, "july": 7, "october": 10, "december": 12,
          "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
          "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
          "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
          "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
          "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
          "gennaio": 1, "febbraio": 2, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "settembre": 9,
          "ottobre": 10, "dicembre": 12, "dez": 12, "mär": 3, "okt": 10, "déc": 12, "juil": 7, "sept.": 9}

# The catalogue that pre-fills the choices. Lower-cased substrings of a
# line's label; the first bucket whose words match wins, employer-side
# words checked first because "Pensionskasse AG" is the employer's
# pension, not the earner's.
_EMPLOYER_WORDS = ("arbeitgeber", " ag", "ag-anteil", "ag ", "employer", "employeur", "patronal", "part patronale",
                   "datore", "empresa", "cotisations patronales")
CATALOGUE = {
    "pension": ("bvg", "lpp", "pensionskasse", "pension", "retraite", "prévoyance", "prevoyance", "pf1", "pf2", "ksp",
                "altersvorsorge", "agirc", "arrco", "401k", "vorsorge", "previdenza", "plan de pensiones", "2. säule", "2e pilier"),
    "social": ("ahv", "alv", "avs", "ac ", "nbu", "suva", "krankentaggeld", "ktg", "urssaf", "csg", "crds", "sécurité sociale",
               "securite sociale", "national insurance", "social security", "sozialversicherung", "rentenversicherung",
               "arbeitslosenversicherung", "krankenversicherung", "pflegeversicherung", "chômage", "chomage", "maladie",
               "assurance", "seguridad social", "inps", "iv-beitrag", "eo-beitrag", "unfall", "accident", "cotisation"),
    "tax": ("quellensteuer", "lohnsteuer", "kirchensteuer", "impôt", "impot", "prélèvement à la source", "prelevement",
            "tax", "paye", "withholding", "irpf", "irpef", "steuer", "retención", "retencion"),
    "net": ("nettolohn", "netto", "net à payer", "net a payer", "net pay", "net paid", "auszahlung", "auszahlungsbetrag",
            "take home", "net versé", "neto a pagar", "líquido", "liquido", "netto da pagare", "montant net"),
    "gross": ("bruttolohn", "brutto", "gross", "salaire brut", "brut", "lordo", "total brut", "bruto", "/101"),
    "bonus": ("bonus", "gratifikation", "13.", "13e", "13ème", "13th", "prime", "prämie", "incentive", "sti", "premio", "gratification"),
    "allowance": ("zulage", "familienzulage", "kinderzulage", "allocation", "allowance", "indemnité", "indemnite",
                  "subsidio", "assegno", "spesen", "pauschale"),
    "base": ("monatslohn", "monatsgehalt", "grundgehalt", "gehalt", "salaire de base", "base salary", "basic",
             "stundenlohn", "salaire mensuel", "salario base", "stipendio", "lohn", "salaire", "salary", "sueldo"),
    "other": ("kantine", "canteen", "cantine", "parking", "tickets", "abzug", "retenue", "deduction", "mutuelle",
              "restaurant", "vorschuss", "avance"),
    "period": ("lohnabrechnung", "monat ", "période", "periode", "period", "abrechnungsmonat", "mois", "month",
               "bulletin de paie", "payslip", "nómina", "nomina", "busta paga"),
    "paid": ("valuta", "auszahlung am", "auszahlungam", "date de paiement", "payment date", "zahltag", "versement le",
             "pay date", "fecha de pago", "paid on", "date de virement"),
}

# ─── The sheet, as lines ─────────────────────────────────────────────

_FORMATS = {
    # thousands, decimals — and the token that is an amount in that format
    # No lookahead after the two decimals: a glued sheet writes the
    # basis, the rate and the amount as one run — 7’360.005.30%-390.10 —
    # and the first two decimals are where the first number ends.
    "ch": re.compile(r"-?\d[\dO’']*\.[\dO]{2}"),
    "de": re.compile(r"-?\d{1,3}(?:\.\d{3})*,\d{2}-?(?!\d)|-?\d+,\d{2}-?(?!\d)"),
    "en": re.compile(r"-?\d{1,3}(?:,\d{3})*\.\d{2}(?!\d)|-?\d+\.\d{2}(?!\d)"),
    "fr": re.compile(r"-?\d{1,3}(?:[   ]\d{3})*,\d{2}(?!\d)|-?\d+,\d{2}(?!\d)"),
}


def number_format(text: str) -> str:
    """How this sheet writes its amounts, from the sheet itself."""
    if re.search(r"\d[’']\d{3}", text):
        return "ch"
    de = len(re.findall(r"\d\.\d{3},\d{2}", text)) + len(re.findall(r"\d,\d{2}-", text))
    en = len(re.findall(r"\d,\d{3}\.\d{2}", text))
    fr = len(re.findall(r"\d[   ]\d{3},\d{2}", text))
    if fr > de and fr >= en:
        return "fr"
    if en > de:
        return "en"
    if de or len(re.findall(r"\d+,\d{2}(?!\d)", text)) > len(re.findall(r"\d+\.\d{2}(?!\d)", text)):
        return "de"
    return "en"


def amount(token: str, fmt: str) -> float:
    s = token.strip().replace("O", "0")
    neg = s.startswith("-") or s.endswith("-")
    s = s.strip("-")
    if fmt == "ch":
        s = s.replace("’", "").replace("'", "")
    elif fmt == "de":
        s = s.replace(".", "").replace(",", ".")
    elif fmt == "fr":
        s = re.sub(r"[   ]", "", s).replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return -v if neg else v


def lines(text: str, fmt: str | None = None) -> list[dict]:
    """Every line that carries an amount, a month or a date:
    [{n, text, label, amounts: [float], rates: [float], month, date}]."""
    fmt = fmt or number_format(text)
    rx = _FORMATS[fmt]
    out = []
    for n, raw in enumerate(text.splitlines()):
        t = raw.strip()
        if not t:
            continue
        # A number followed by a percent sign is a rate, not an amount —
        # whatever the format, and even glued to its neighbours.
        amounts, rates, first = [], [], None
        for m in rx.finditer(t):
            if t[m.end():].lstrip().startswith("%"):
                rates.append(amount(m.group(), fmt))
                continue
            amounts.append(amount(m.group(), fmt))
            if first is None:
                first = m.start()
        month = _month_in(t)
        date = None
        m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", t)
        if m and 1 <= int(m.group(2)) <= 12 and 1 <= int(m.group(1)) <= 31:
            date = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        if not (amounts or month or date):
            continue
        # The label is what stands before the first amount.
        label = t[:first] if first is not None else t
        label = re.sub(r"\d{1,2}[./-]\d{1,2}[./-]\d{4}", "", label)
        label = re.sub(r"\d+[.,]\d+\s*%", "", label)
        label = " ".join(label.replace(":", " ").split()).strip(" -–:")
        if not label:
            label = t[:40]
        out.append({"n": n, "text": t, "label": label, "amounts": amounts, "rates": rates,
                    "month": month, "date": date})
    return out


def _month_in(t: str) -> str | None:
    """`Monat März 2026`, `LohnabrechnungDezember2025`, `Période : Mars
    2026`, `03/2026` → 2026-03. A month name may be glued to the word
    before it, so a word that ENDS in a month name counts."""
    for m in re.finditer(r"([A-Za-zäöüéèêûôàÄÖÜÉ.]+)\s*(\d{4})\b", t):
        word, year = m.group(1).lower().rstrip("."), int(m.group(2))
        if not 1990 < year < 2100:
            continue
        for name, num in MONTHS.items():
            if word == name or (len(name) > 3 and word.endswith(name)):
                return f"{year}-{num:02d}"
    m = re.search(r"(?<![\d.])(\d{2})[./](\d{4})\b", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{m.group(2)}-{m.group(1)}"
    return None


def label_key(label: str) -> str:
    """A label as it is remembered: without its spaces or its case, so a
    sheet whose text lost its spaces still matches its own mapping."""
    return re.sub(r"[\s.:]+", "", label).lower()


_EMPLOYER_RE = re.compile(r"(?i)(?<![a-z])(ag|arbeitgeber|employer|employeur|patronal|patronale|datore|empresa)(?![a-z])")


def _has(words: tuple, label: str) -> bool:
    """A catalogue word in a label. A word with a space in it, or a
    label whose spaces are gone, is compared without spaces; a plain
    word is looked for between non-letters, so "paye" is not "payer"."""
    low = label.lower()
    flat = re.sub(r"\s+", "", low)
    glued = " " not in low.strip() and len(low) > 12
    for w in words:
        if " " in w or glued:
            if w.replace(" ", "") in flat:
                return True
        elif re.search(r"(?<![a-zäöüéè])" + re.escape(w) + r"(?![a-zäöüéè])", low):
            return True
    return False


def suggest(ls: list[dict]) -> dict[int, str]:
    """{line index: bucket} from the catalogue — the pre-filled ticks."""
    picks: dict[int, str] = {}
    for i, l in enumerate(ls):
        label = l["label"]
        if l["month"] and _has(CATALOGUE["period"], label):
            picks[i] = "period"; continue
        if l["date"] and _has(CATALOGUE["paid"], label):
            picks[i] = "paid"; continue
        if not l["amounts"]:
            continue
        employer_side = bool(_EMPLOYER_RE.search(label))
        for bucket in ("net", "gross", "pension", "social", "tax", "bonus", "allowance", "base", "other"):
            if _has(CATALOGUE[bucket], label):
                if employer_side and bucket in ("pension", "social", "tax", "other"):
                    bucket = "employer_pension" if bucket == "pension" else "employer_social"
                picks[i] = bucket
                break
    # One gross and one net: the last candidate for each — a sheet lists
    # the parts first and the total after them.
    for one in ("gross", "net"):
        idx = [i for i, b in picks.items() if b == one]
        for i in idx[:-1]:
            del picks[i]
    return picks


_TITLES = r"(Herr|Frau|Mr|Mrs|Ms|M\.|Mme|Mlle|Salarié|Salariée|Employee|Mitarbeiter|Sr\.|Sra\.|Dipendente|Empleado)"
_EMPLOYER_LABELS = r"(Firma|Employeur|Employer|Arbeitgeber|Empresa|Datore di lavoro)"


def guess_names(text: str) -> tuple[str, str]:
    """(employer, earner) as the sheet seems to say them — a first
    guess for the two fields the user confirms."""
    ls = [l.strip() for l in text.splitlines() if l.strip()]
    employer, employee = "", ""
    for i, l in enumerate(ls[:40]):
        m = re.search(_TITLES + r"\s*:?\s+([^:]+?)\s*$", l)
        if m and not employee:
            employee = _unglue(m.group(2))
            l = l[:m.start()]
        if not employer and re.search(_EMPLOYER_LABELS, l, re.I):
            employer = _unglue(re.sub(r"(?i)\s*" + _EMPLOYER_LABELS + r"\s*:?\s*", " ", l)).strip(" :-")
    if not employee:
        # The small employer's sheet: the name stands under the title.
        for i, l in enumerate(ls[:40]):
            if _month_in(l) and _has(CATALOGUE["period"], l) and i + 1 < len(ls) and not re.search(r"\d", ls[i + 1]):
                employee = _unglue(ls[i + 1])
                break
    if not employer and ls:
        employer = _unglue(ls[0])[:80]
    return employer[:80], employee[:80]


# ─── Reading a sheet through a mapping ───────────────────────────────

def read(mapping: dict, text: str) -> ParseResult:
    """The statement a mapping makes of a sheet, and the legs to book."""
    fmt = mapping.get("format") or number_format(text)
    ls = lines(text, fmt)
    by_label: dict[str, list[dict]] = {}
    for l in ls:
        by_label.setdefault(label_key(l["label"]), []).append(l)
    slip = {"layout": "mapped", "employer": mapping.get("employer") or "?", "employee": mapping.get("employee") or "?",
            "period": None, "paid_on": None, "currency": mapping.get("currency") or "CHF",
            "gross": 0.0, "base_salary": None, "bonus": 0.0, "allowances": 0.0,
            "employee_social": 0.0, "employee_pension": 0.0, "tax": 0.0, "other_deductions": 0.0,
            "net_paid": 0.0, "employer_pension": 0.0, "employer_social": 0.0,
            "employer_side_known": bool(mapping.get("buckets", {}).get("employer_pension")
                                        or mapping.get("buckets", {}).get("employer_social")),
            "lines": []}
    field = {"gross": "gross", "base": "base_salary", "bonus": "bonus", "allowance": "allowances",
             "tax": "tax", "social": "employee_social", "pension": "employee_pension", "other": "other_deductions",
             "net": "net_paid", "employer_pension": "employer_pension", "employer_social": "employer_social"}
    result = ParseResult()
    for bucket, labels in (mapping.get("buckets") or {}).items():
        if bucket not in AMOUNT_BUCKETS:
            continue
        for lab in labels:
            hits = by_label.get(label_key(lab)) or []
            if not hits:
                continue
            for l in hits:
                if not l["amounts"]:
                    continue
                v = l["amounts"][-1]                    # the amount is the last number on the line
                if bucket in OUT_BUCKETS:
                    v = -abs(v)
                elif bucket in ("gross", "net", "base", "bonus", "allowance", "employer_pension", "employer_social"):
                    v = abs(v)
                if bucket in ("gross", "net"):
                    slip[field[bucket]] = v            # a total, not a sum
                elif bucket == "base":
                    slip["base_salary"] = (slip["base_salary"] or 0.0) + v
                else:
                    slip[field[bucket]] += v
                slip["lines"].append({"code": None, "description": l["label"], "side": bucket,
                                      "basis": None, "rate": l["rates"][0] if l["rates"] else None, "amount": v})
    for key, want in (("period_label", "month"), ("paid_label", "date")):
        lab = mapping.get(key)
        if lab:
            for l in by_label.get(label_key(lab)) or []:
                if l[want]:
                    slip["period" if want == "month" else "paid_on"] = l[want]
                    break
    if not slip["period"]:
        # Any month on the sheet, the first one — a sheet names its
        # month near the top.
        for l in ls:
            if l["month"]:
                slip["period"] = l["month"]
                break
    if not slip["paid_on"]:
        # The payment date often shares the period's line, or stands
        # under one of the words for it.
        for l in ls:
            if l["date"] and (l["month"] == slip["period"] or _has(CATALOGUE["paid"], l["label"])):
                slip["paid_on"] = l["date"]
                break
    for k in ("gross", "bonus", "allowances", "employee_social", "employee_pension", "tax", "other_deductions",
              "net_paid", "employer_pension", "employer_social"):
        slip[k] = round(slip[k], 2)
    if not slip["period"] or not slip["gross"]:
        result.problems.append("the payslip's month or gross could not be read through the mapping")
        return result
    result.payslip = slip
    result.rows = _legs(slip)
    return result


def adds_up(slip: dict) -> float:
    """Gross less every deduction against the net: zero when the mapping
    caught every line, the size of what it missed when not."""
    return round(slip["gross"] + slip["tax"] + slip["employee_social"] + slip["employee_pension"]
                 + slip["other_deductions"] - slip["net_paid"], 2)


# ─── Storage ─────────────────────────────────────────────────────────

def all_mappings() -> list[dict]:
    with get_conn() as conn:
        return [_row(r) for r in conn.execute("SELECT * FROM payslip_mappings ORDER BY name")]


def _row(r) -> dict:
    d = dict(r)
    d["mapping"] = json.loads(d["mapping"])
    return d


def find(text: str) -> dict | None:
    """The saved mapping whose markers this sheet carries: the employer
    and the earner, as the sheet writes them, spaces or no spaces."""
    flat = label_key(text)
    for m in all_mappings():
        if label_key(m["employer"]) in flat and label_key(m["employee"]) in flat:
            return m
    return None


def save(name: str, employer: str, employee: str, mapping: dict) -> int:
    name = " ".join(name.split())[:80] or employer
    with get_conn() as conn:
        conn.execute("DELETE FROM payslip_mappings WHERE employer = ? AND employee = ?", (employer, employee))
        cur = conn.execute("INSERT INTO payslip_mappings (name, employer, employee, mapping) VALUES (?, ?, ?, ?)",
                           (name, employer, employee, json.dumps(mapping)))
        return int(cur.lastrowid)


def delete(mapping_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM payslip_mappings WHERE id = ?", (mapping_id,))


def check(mapping: dict) -> list[str]:
    """What a mapping lacks: gross and net are the least."""
    b = mapping.get("buckets") or {}
    return [k for k in ("gross", "net") if not b.get(k)]


class Mapped:
    """Quacks like a module in `importers.PDF_IMPORTERS`: SLUG, LABEL, parse."""

    def __init__(self, saved: dict):
        self.saved = saved
        self.SLUG = "payslip"
        self.LABEL = saved["name"]

    def parse(self, content, account_currency="EUR"):
        from .dkb_pdf import pdf_text
        text = pdf_text(content) if isinstance(content, bytes) else content
        mapping = {**self.saved["mapping"], "employer": self.saved["employer"], "employee": self.saved["employee"]}
        return read(mapping, text)


def sniff(text: str):
    saved = find(text)
    return Mapped(saved) if saved else None


def looks_like_payslip(text: str) -> bool:
    """Enough labelled amounts and a month: something a mapping could
    be drawn for. A bank statement has amounts and no month name; a
    letter has neither."""
    ls = lines(text)
    return sum(1 for l in ls if l["amounts"]) >= 3 and any(l["month"] for l in ls)
