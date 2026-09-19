"""CAMT.053 / CAMT.052 — the ISO 20022 account statement every European
online-banking portal exports ("Kontoauszug als XML", "camt.053").

The richest statement a bank hands out: booking and value date, the
counterparty's name and IBAN, the SEPA end-to-end and mandate
references, the bank's own transaction code, and — unlike any CSV —
the bank's reference for the entry, which makes an id that survives
two overlapping exports.

Read with a namespace-blind walk: the versions (camt.053.001.02 to
.10) differ in their namespace and in fields this importer does not
need. camt.052 (the intraday report) has the same entries under
another root and is read the same way. A batch entry — one booking
carrying several transactions with their own amounts — becomes one
row per transaction. Pending entries are left out and counted: their
date changes when they book.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from .base import ParsedTxn, ParseResult, parse_date
from .formats import decode, kind_of, row_id

SLUG = "camt053"
LABEL = "CAMT.053 / CAMT.052 — ISO 20022 Kontoauszug (XML)"

_ROOTS = ("BkToCstmrStmt", "BkToCstmrAcctRpt", "BkToCstmrDbtCdtNtfctn")


def matches(header: list[str], sample: str) -> bool:
    return "<Document" in sample and any(f"<{r}" in sample for r in _ROOTS)


def _strip(tree: ET.Element) -> ET.Element:
    for el in tree.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return tree


def _text(el: ET.Element | None, path: str) -> str:
    found = el.find(path) if el is not None else None
    return " ".join((found.text or "").split()) if found is not None else ""


def _amount(el: ET.Element | None) -> tuple[float | None, str]:
    """(value, currency) of an <Amt Ccy="EUR">12.34</Amt>."""
    if el is None or not (el.text or "").strip():
        return None, ""
    try:
        return float(el.text.strip()), (el.get("Ccy") or "").upper()
    except ValueError:
        return None, ""


def _date(el: ET.Element | None) -> str | None:
    """A <BookgDt>/<ValDt>: either <Dt> or <DtTm>."""
    if el is None:
        return None
    return parse_date(_text(el, "Dt") or _text(el, "DtTm"))


def _party(tx: ET.Element | None, credit: bool) -> tuple[str | None, str | None]:
    """The other side of a transaction: the debtor of a credit, the
    creditor of a debit — name and IBAN."""
    if tx is None:
        return None, None
    side = "Dbtr" if credit else "Cdtr"
    parties = tx.find("RltdPties")
    if parties is None:
        return None, None
    # camt.053.001.08+ wraps the party in <Pty>; earlier versions do not.
    name = _text(parties, f"{side}/Pty/Nm") or _text(parties, f"{side}/Nm")
    iban = _text(parties, f"{side}Acct/Id/IBAN") or _text(parties, f"{side}Acct/Id/Othr/Id")
    return name or None, iban or None


def _purpose(tx: ET.Element | None, entry: ET.Element) -> str:
    if tx is not None:
        ustrd = [" ".join((u.text or "").split()) for u in tx.findall("RmtInf/Ustrd")]
        text = " ".join(u for u in ustrd if u)
        if text:
            return text
        strd = _text(tx, "RmtInf/Strd/CdtrRefInf/Ref")
        if strd:
            return strd
    return _text(entry, "AddtlNtryInf")


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    result = ParseResult()
    text = decode(content)
    try:
        root = _strip(ET.fromstring(text.encode("utf-8")))
    except ET.ParseError as e:
        result.problems.append(f"This is not well-formed XML: {e}")
        return result
    statements = [s for r in _ROOTS for s in root.iter(r) for s in (s.findall("Stmt") + s.findall("Rpt") + s.findall("Ntfctn"))]
    if not statements:
        result.problems.append("This XML has no <Stmt> — not a CAMT.053 statement.")
        return result

    counts: dict[str, int] = {}
    for stmt in statements:
        account = _text(stmt, "Acct/Id/IBAN") or _text(stmt, "Acct/Id/Othr/Id")
        stmt_ccy = _text(stmt, "Acct/Ccy").upper()
        for bal in stmt.findall("Bal"):
            code = _text(bal, "Tp/CdOrPrtry/Cd")
            if code in ("CLBD", "CLAV"):
                value, ccy = _amount(bal.find("Amt"))
                if value is not None:
                    if _text(bal, "CdtDbtInd") == "DBIT":
                        value = -value
                    as_of = _date(bal.find("Dt"))
                    # CLBD (booked) is the balance; CLAV (available) only
                    # when no booked one is given.
                    if code == "CLBD" or result.closing_balance is None:
                        result.closing_balance = {"amount": value, "currency": ccy or stmt_ccy or account_currency, "as_of": as_of}

        for entry in stmt.findall("Ntry"):
            status = _text(entry, "Sts") or _text(entry, "Sts/Cd")
            if status and status != "BOOK":
                result.skipped += 1
                continue
            e_value, e_ccy = _amount(entry.find("Amt"))
            if e_value is None:
                result.problems.append("an entry without an amount was left out")
                continue
            credit = _text(entry, "CdtDbtInd") == "CRDT"
            if _text(entry, "RvslInd") == "true":
                credit = not credit
            date = _date(entry.find("BookgDt")) or _date(entry.find("ValDt"))
            if not date:
                result.problems.append("an entry without a date was left out")
                continue
            value_date = _date(entry.find("ValDt"))
            svcr_ref = _text(entry, "AcctSvcrRef") or _text(entry, "NtryRef")
            sub_family = _text(entry, "BkTxCd/Domn/Fmly/SubFmlyCd")
            gvc = _text(entry, "BkTxCd/Prtry/Cd")
            info = _text(entry, "AddtlNtryInf")

            details = entry.findall("NtryDtls/TxDtls")
            # A batch: one row per transaction with an amount of its own.
            legs = [tx for tx in details if tx.find("Amt") is not None or tx.find("AmtDtls/TxAmt/Amt") is not None]
            if len(legs) < 2:
                legs = details[:1] or [None]
            for n, tx in enumerate(legs):
                value, ccy = e_value, e_ccy
                if len(legs) > 1:
                    v, c = _amount(tx.find("Amt"))
                    if v is None:
                        v, c = _amount(tx.find("AmtDtls/TxAmt/Amt"))
                    if v is not None:
                        value, ccy = v, c or e_ccy
                        if _text(tx, "CdtDbtInd") == "DBIT":
                            credit = False
                        elif _text(tx, "CdtDbtInd") == "CRDT":
                            credit = True
                amount = value if credit else -value
                name, iban = _party(tx, credit)
                purpose = _purpose(tx, entry)
                e2e = _text(tx, "Refs/EndToEndId") if tx is not None else ""
                tx_id = _text(tx, "Refs/TxId") if tx is not None else ""
                mandate = _text(tx, "Refs/MndtId") if tx is not None else ""
                if e2e in ("NOTPROVIDED", "NOTPROVIDED."):
                    e2e = ""
                description = purpose or info or name or (gvc and f"GVC {gvc}") or "CAMT"
                blob = " ".join(x for x in (info, purpose, name, gvc) if x)
                kind = kind_of(blob, amount, sub_family)

                # The bank's own reference is the id when it has one; a
                # batch adds the leg's number. Otherwise the row's facts.
                if svcr_ref:
                    ext = f"camt:{svcr_ref}" + (f"#{n + 1}" if len(legs) > 1 else "")
                else:
                    seed = (account, date, value_date, f"{amount:.2f}", ccy, name, iban, purpose, e2e, tx_id, mandate)
                    counts[str(seed)] = counts.get(str(seed), 0) + 1
                    ext = row_id("camt", *seed, counts[str(seed)])
                result.rows.append(ParsedTxn(
                    txn_date=date,
                    description=" ".join(description.split())[:500],
                    amount=round(amount, 2),
                    currency=ccy or stmt_ccy or account_currency.upper()[:3],
                    kind=kind,
                    external_id=ext,
                    counterparty=name,
                ))
    return result
