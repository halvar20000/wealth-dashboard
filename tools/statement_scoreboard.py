#!/usr/bin/env python3
"""Score the statement readers against Portfolio Performance's test corpus.

Portfolio Performance keeps, for every bank it reads, the extracted text
of real (anonymised) statements and a test that asserts what each one
contains — date, shares, amount, fees, taxes, per transaction. That is
a ready-made oracle for a reader of the same documents. The corpus is
EPL-licensed and stays out of this repository: point PP_CORPUS at a
checkout (or at the `datatransfer/pdf` folder of one) and this script
runs every fixture through our readers and says how many of the
expected transactions come out right.

    PP_CORPUS=/path/to/portfolio python3 tools/statement_scoreboard.py            # every bank we read
    PP_CORPUS=... python3 tools/statement_scoreboard.py comdirect -v              # one bank, every miss
    PP_CORPUS=... python3 tools/statement_scoreboard.py comdirect Kauf03.txt      # one fixture, in full

Matching is by kind, date and amount (to the cent); shares, fees and
taxes are compared when the test asserts them. The score is what a
reader is released on, and what a regression shows up in.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import importers  # noqa: E402

CORPUS = Path(os.environ.get("PP_CORPUS") or "").expanduser()

# PP's matcher vocabulary → our kinds. The sign is ours to add.
KIND = {"purchase": "buy", "sale": "sell", "dividend": "dividend", "interest": "interest",
        "interestCharge": "interest", "fee": "fee", "feeRefund": "fee", "taxes": "tax",
        "taxRefund": "tax", "deposit": "deposit", "removal": "withdrawal",
        "inboundDelivery": "transfer", "outboundDelivery": "transfer"}
OLD_KIND = {"BUY": "buy", "SELL": "sell", "DIVIDENDS": "dividend", "INTEREST": "interest",
            "INTEREST_CHARGE": "interest", "FEES": "fee", "FEES_REFUND": "fee", "TAXES": "tax",
            "TAX_REFUND": "tax", "DEPOSIT": "deposit", "REMOVAL": "withdrawal",
            "DELIVERY_INBOUND": "transfer", "DELIVERY_OUTBOUND": "transfer",
            "TRANSFER_IN": "transfer", "TRANSFER_OUT": "transfer"}


def pdf_dir() -> Path:
    for cand in (CORPUS, CORPUS / "name.abuchen.portfolio.tests/src/name/abuchen/portfolio/datatransfer/pdf"):
        if (cand / "dkb").is_dir():
            return cand
    sys.exit("PP_CORPUS must point at a Portfolio Performance checkout (or its datatransfer/pdf folder)")


def _num(expr: str) -> float:
    """`26.40 + 1.50` and the like, as the tests write them."""
    expr = expr.strip()
    if not re.fullmatch(r"[\d.\s+\-*/()]+", expr):
        raise ValueError(expr)
    return float(eval(expr, {"__builtins__": {}}, {}))       # noqa: S307  arithmetic only


def _arg(body: str, call: str) -> str | None:
    """The argument text of `call(`…`)`, with nested parentheses intact —
    `hasFees("EUR", 28.84 + (2 * 9.40))` has one inside."""
    i = body.find(call + "(")
    if i < 0:
        return None
    depth, j = 0, i + len(call)
    for k in range(j, len(body)):
        if body[k] == "(":
            depth += 1
        elif body[k] == ")":
            depth -= 1
            if depth == 0:
                return body[j + 1:k]
    return None


def _money(body: str, call: str):
    arg = _arg(body, call)
    if arg is None:
        return None, None
    m = re.match(r'\s*"([A-Z]{3})",\s*(.+)$', arg, re.S)
    return (m.group(1), _num(m.group(2))) if m else (None, None)


def expectations(test_java: str) -> dict[str, list[dict]]:
    """fixture name → the transactions its test asserts, either style."""
    out: dict[str, list[dict]] = {}
    for method in re.split(r"\n\s*@Test\b", test_java)[1:]:
        m = re.search(r'loadTestCase\(getClass\(\),\s*"([^"]+)"', method)
        if not m:
            continue
        name = m.group(1)
        txns: list[dict] = []
        # New style: hasItem(purchase( ... ))) blocks.
        for blk in re.finditer(r"hasItem\((\w+)\(\s*//(.*?)\)\)\)", method, re.S):
            kind = KIND.get(blk.group(1))
            if not kind:
                continue
            body = blk.group(2)
            t = {"kind": kind}
            d = re.search(r'hasDate\("([^"]+)"\)', body)
            if d:
                t["date"] = d.group(1)[:10]
            s = _arg(body, "hasShares")
            if s is not None:
                t["shares"] = _num(s)
            ccy, amount = _money(body, "hasAmount")
            if amount is not None:
                t["currency"], t["amount"] = ccy, amount
            _, fees = _money(body, "hasFees")
            if fees is not None:
                t["fees"] = fees
            _, taxes = _money(body, "hasTaxes")
            if taxes is not None:
                t["taxes"] = taxes
            txns.append(t)
        # Old style: getType() … getDateTime() … getShares() … getMonetaryAmount()
        if not txns:
            cur: dict | None = None
            for line in method.splitlines():
                # A buy/sell entry has a portfolio side and an account side,
                # asserted one after the other: one transaction, not two.
                if "getAccountTransaction().getType()" in line:
                    continue
                tm = re.search(r"getType\(\),\s*is\((?:PortfolioTransaction|AccountTransaction)\.Type\.(\w+)\)", line)
                if tm:
                    cur = {"kind": OLD_KIND.get(tm.group(1), tm.group(1).lower())}
                    txns.append(cur)
                    continue
                if cur is None:
                    continue
                dm = re.search(r'getDateTime\(\),\s*is\(LocalDateTime\.parse\("([^"]+)"\)', line)
                if dm:
                    cur["date"] = dm.group(1)[:10]
                sm = re.search(r"getShares\(\),\s*is\(Values\.Share\.factorize\(([^)]+)\)", line)
                if sm:
                    cur["shares"] = _num(sm.group(1))
                am = re.search(r'getMonetaryAmount\(\),\s*is\(Money\.of\((?:CurrencyUnit\.)?"?([A-Z]{3})"?,\s*Values\.Amount\.factorize\(([^)]+)\)', line)
                if am:
                    cur["currency"], cur["amount"] = am.group(1), _num(am.group(2))
                fm = re.search(r"getUnitSum\(Unit\.Type\.FEE\),\s*is\(Money\.of\([^,]+,\s*Values\.Amount\.factorize\(([^)]+)\)", line)
                if fm:
                    cur["fees"] = _num(fm.group(1))
                xm = re.search(r"getUnitSum\(Unit\.Type\.TAX\),\s*is\(Money\.of\([^,]+,\s*Values\.Amount\.factorize\(([^)]+)\)", line)
                if xm:
                    cur["taxes"] = _num(xm.group(1))
        # A bare kind with no date is a test of a failure message, not of
        # a transaction.
        txns = [t for t in txns if t.get("date")]
        # The same fixture loaded by a second test method (checked once
        # more with another security currency, say) is one document.
        if txns and name not in out:
            out[name] = txns
    return out


def _fixture_text(path: Path) -> str:
    """A fixture as a reader would see it: the PDFBox preamble some of
    them carry stripped, and the odd Latin-1 file read as such."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    lines = text.splitlines()
    if lines and (lines[0].startswith("```") or lines[0].startswith("PDFBox Version") or lines[0].startswith("PDF ")):
        for i, line in enumerate(lines[:8]):
            if line.startswith("-----"):
                lines = lines[i + 1:]
                break
    return "\n".join(lines)


def _days_apart(a: str, b: str) -> int:
    from datetime import date as _d
    try:
        return abs((_d.fromisoformat(a) - _d.fromisoformat(b)).days)
    except ValueError:
        return 999


def _close(a, b, tol) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def score_fixture(module, text: str, expected: list[dict]) -> tuple[list[dict], list[str]]:
    """(rows we produced, list of misses) for one document."""
    result = module.parse(text)
    rows = [{"kind": r.kind, "date": r.txn_date, "amount": abs(r.amount), "currency": r.currency,
             "shares": abs(r.quantity) if r.quantity is not None else None,
             "fees": r.fee, "taxes": r.tax} for r in result.rows]
    misses = []
    used: set[int] = set()
    for e in expected:
        hit = None
        for i, r in enumerate(rows):
            # A bond coupon is interest here and a dividend to PP: both
            # are income, and the test is about the figures.
            same_kind = r["kind"] == e["kind"] or {r["kind"], e["kind"]} == {"interest", "dividend"}
            if i in used or not same_kind:
                continue
            if e.get("date") and r["date"] != e["date"]:
                # A credit has a pay date and a value date a day or two
                # apart; PP asserts one or the other depending on the
                # bank. Either is the truth, so a few days' slack.
                if not (r["kind"] in ("dividend", "interest", "tax") and _days_apart(r["date"], e["date"]) <= 4):
                    continue
            if "amount" in e and not _close(r["amount"], e["amount"], 0.011):
                # A bank that credits a dividend before tax: PP books the
                # gross, this app the cash with the tax beside it. Same
                # facts, so it counts — when the two add up.
                if not (r["kind"] in ("dividend", "interest")
                        and _close(r["amount"] + (r["taxes"] or 0.0), e["amount"], 0.011)):
                    continue
            hit = i
            break
        if hit is None:
            misses.append(f"expected {e}, got {[ (r['kind'], r['date'], r['amount']) for r in rows]}"
                          + (f" — problems: {result.problems[:2]}" if result.problems else ""))
            continue
        used.add(hit)
        r = rows[hit]
        # Units matter on what moves a holding; a tax or a dividend row
        # carries none here, whatever PP notes on it.
        if e["kind"] in ("buy", "sell", "transfer") and "shares" in e and not _close(r["shares"], e["shares"], 0.0011):
            misses.append(f"shares {r['shares']} ≠ {e['shares']} on {e['date']} {e['kind']}")
        if "fees" in e and e["fees"] and not _close(r["fees"] or 0.0, e["fees"], 0.011):
            misses.append(f"fees {r['fees']} ≠ {e['fees']} on {e['date']} {e['kind']}")
        if "taxes" in e and e["taxes"] and not _close(r["taxes"] or 0.0, e["taxes"], 0.011) \
                and not _close(r["amount"] + (r["taxes"] or 0.0), e.get("amount", -1), 0.011):
            misses.append(f"taxes {r['taxes']} ≠ {e['taxes']} on {e['date']} {e['kind']}")
    return rows, misses


def main(argv: list[str]) -> int:
    verbose = "-v" in argv
    args = [a for a in argv if a != "-v"]
    base = pdf_dir()
    readers = {m.CORPUS: m for m in importers.PDF_IMPORTERS if getattr(m, "CORPUS", None)}
    banks = [args[0]] if args else sorted(readers)
    total_docs = total_ok = 0
    for bank in banks:
        module = readers.get(bank)
        folder = base / bank
        if module is None or not folder.is_dir():
            print(f"{bank}: no reader or no corpus folder")
            continue
        tests = list(folder.glob("*Test.java"))
        exp = {}
        for t in tests:
            exp.update(expectations(t.read_text(encoding="utf-8")))
        fixtures = sorted(folder.glob("*.txt"))
        if len(args) > 1:
            fixtures = [f for f in fixtures if f.name == args[1]]
        ok = 0
        for f in fixtures:
            text = _fixture_text(f)
            expected = exp.get(f.name, [])
            rows, misses = score_fixture(module, text, expected)
            good = not misses and (bool(rows) or not expected)
            ok += good
            if len(args) > 1:
                for r in rows:
                    print("  row", r)
                print("  expected", expected)
            if (verbose or len(args) > 1) and misses:
                print(f"  ✗ {f.name}")
                for m in misses:
                    print(f"      {m}")
        total_docs += len(fixtures)
        total_ok += ok
        pct = (ok / len(fixtures) * 100) if fixtures else 0
        print(f"{bank:22} {ok:4}/{len(fixtures):<4} {pct:5.1f} %")
    if len(banks) > 1:
        print(f"{'all':22} {total_ok:4}/{total_docs:<4} {total_ok / total_docs * 100 if total_docs else 0:5.1f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
