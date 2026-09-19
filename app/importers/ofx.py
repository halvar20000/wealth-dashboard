"""OFX / QFX — Open Financial Exchange, the download of the North
American and British banks and brokers (and Quicken's "QFX", the same
file with a branding tag).

Two dialects: OFX 1.x is SGML — tags open and never close — and OFX
2.x is XML. Both are read the same way, by the tags that matter, so a
missing closer never matters. A bank statement (`STMTRS`) gives
`STMTTRN` rows: type, posted date, amount, the bank's `FITID` — an id
made for exactly the overlap-free re-import this app does — payee and
memo. A brokerage statement (`INVSTMTRS`) gives buys, sells, income,
reinvestments and the cash movements of the account, with the
security named through `SECLIST`.
"""

from __future__ import annotations

import re
from datetime import datetime

from .base import ParsedTxn, ParseResult, find_isin
from .formats import decode, kind_of

SLUG = "ofx"
LABEL = "OFX / QFX — Open Financial Exchange"

_BANK_TYPES = {"INT": "interest", "FEE": "fee", "SRVCHG": "fee", "DIV": "dividend",
               "DEP": "deposit", "DIRECTDEP": "deposit", "XFER": "transfer"}
_INV_BUY = ("BUYSTOCK", "BUYMF", "BUYOTHER", "BUYDEBT", "BUYOPT")
_INV_SELL = ("SELLSTOCK", "SELLMF", "SELLOTHER", "SELLDEBT", "SELLOPT")


def matches(header: list[str], sample: str) -> bool:
    up = sample.upper()
    return "<OFX>" in up or "OFXHEADER" in up or "<?OFX " in up


def _tag(block: str, name: str) -> str:
    """The value of the first <NAME> in a block, SGML or XML."""
    m = re.search(r"<" + name + r">\s*([^<\r\n]*)", block, re.I)
    return " ".join(m.group(1).split()) if m else ""


def _blocks(text: str, name: str) -> list[str]:
    """Every <NAME>…</NAME> block. The SGML dialect does close these
    aggregate tags, so the pair is safe to look for."""
    return re.findall(r"<" + name + r">(.*?)</" + name + r">", text, re.I | re.S)


def _date(raw: str) -> str | None:
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", raw.strip())
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date().isoformat()
    except ValueError:
        return None


def _num(raw: str) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def _securities(text: str) -> dict[str, tuple[str, str | None]]:
    """UNIQUEID → (name, ISIN or None) from the SECLIST."""
    out = {}
    for info in _blocks(text, "SECINFO"):
        uid = _tag(info, "UNIQUEID")
        name = _tag(info, "SECNAME") or _tag(info, "TICKER")
        isin = uid if _tag(info, "UNIQUEIDTYPE").upper() == "ISIN" else find_isin(uid)
        out[uid] = (name, isin)
    return out


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    result = ParseResult()
    text = decode(content)
    if not matches([], text[:8192]):
        result.problems.append("This is not an OFX file.")
        return result
    currency = (_tag(text, "CURDEF") or account_currency).upper()[:3]
    account = _tag(text, "ACCTID")

    for bal in _blocks(text, "LEDGERBAL"):
        amount = _num(_tag(bal, "BALAMT"))
        if amount is not None:
            result.closing_balance = {"amount": amount, "currency": currency, "as_of": _date(_tag(bal, "DTASOF"))}

    # ── a bank or card statement (a brokerage account's cash rows sit
    # inside INVBANKTRAN and are read with the brokerage below) ──
    bank_text = re.sub(r"<INVBANKTRAN>.*?</INVBANKTRAN>", "", text, flags=re.I | re.S)
    for n, trn in enumerate(_blocks(bank_text, "STMTTRN")):
        amount = _num(_tag(trn, "TRNAMT"))
        date = _date(_tag(trn, "DTPOSTED"))
        if amount is None or not date:
            result.problems.append(f"transaction {n + 1} has no amount or date")
            continue
        ttype = _tag(trn, "TRNTYPE").upper()
        name, memo = _tag(trn, "NAME") or _tag(trn, "PAYEE/NAME"), _tag(trn, "MEMO")
        description = memo if memo and name.lower() in memo.lower() else " ".join(x for x in (name, memo) if x)
        kind = _BANK_TYPES.get(ttype) or kind_of(f"{name} {memo}", amount)
        if kind == "deposit" and amount < 0:
            kind = "other"
        fitid = _tag(trn, "FITID")
        result.rows.append(ParsedTxn(
            txn_date=date, description=(description or ttype or "OFX")[:500], amount=round(amount, 2),
            currency=currency, kind=kind,
            external_id=f"ofx:{account}:{fitid}" if fitid else None,
            counterparty=name or None,
        ))

    # ── a brokerage statement ──
    secs = _securities(text)
    for tname in _INV_BUY + _INV_SELL + ("REINVEST", "INCOME", "INVEXPENSE", "INVBANKTRAN", "TRANSFER"):
        for block in _blocks(text, tname):
            inner = _tag(block, "FITID")
            date = _date(_tag(block, "DTTRADE") or _tag(block, "DTPOSTED") or _tag(block, "DTSETTLE"))
            if not date:
                continue
            uid = _tag(block, "UNIQUEID")
            sec_name, isin = secs.get(uid, (uid or None, find_isin(uid)))
            units = _num(_tag(block, "UNITS"))
            price = _num(_tag(block, "UNITPRICE"))
            total = _num(_tag(block, "TOTAL"))
            fee = (_num(_tag(block, "COMMISSION")) or 0.0) + (_num(_tag(block, "FEES")) or 0.0)
            tax = (_num(_tag(block, "TAXES")) or 0.0) + (_num(_tag(block, "WITHHOLDING")) or 0.0)
            memo = _tag(block, "MEMO")
            if tname == "INVBANKTRAN":
                trn = _blocks(block, "STMTTRN")
                if not trn:
                    continue
                amount = _num(_tag(trn[0], "TRNAMT"))
                if amount is None:
                    continue
                ttype = _tag(trn[0], "TRNTYPE").upper()
                kind = _BANK_TYPES.get(ttype) or ("deposit" if amount > 0 else "withdrawal")
                result.rows.append(ParsedTxn(
                    txn_date=date, description=(_tag(trn[0], "NAME") or _tag(trn[0], "MEMO") or ttype)[:500],
                    amount=round(amount, 2), currency=currency, kind=kind,
                    external_id=f"ofx:{account}:{_tag(trn[0], 'FITID')}" if _tag(trn[0], "FITID") else None))
                continue
            if tname == "TRANSFER":
                kind, amount = "transfer", 0.0
            elif tname in _INV_BUY:
                kind, amount = "buy", -(abs(total) if total is not None else abs((units or 0) * (price or 0)) + fee)
            elif tname in _INV_SELL:
                kind, amount = "sell", (abs(total) if total is not None else abs((units or 0) * (price or 0)) - fee)
                units = -abs(units) if units else units
            elif tname == "REINVEST":
                kind, amount = "buy", -abs(total or 0.0)
            elif tname == "INCOME":
                itype = _tag(block, "INCOMETYPE").upper()
                kind = "interest" if itype == "INTEREST" else "dividend"
                amount = total if total is not None else 0.0
                units = None
            else:
                kind, amount = "fee", -(abs(total) if total is not None else 0.0)
                units = None
            result.rows.append(ParsedTxn(
                txn_date=date, description=(memo or f"{tname} {sec_name or ''}").strip()[:500],
                amount=round(amount, 2), currency=currency, kind=kind,
                external_id=f"ofx:{account}:{inner}" if inner else None,
                isin=isin, security_name=sec_name, quantity=units, price=price,
                fee=round(fee, 2) or None, tax=round(tax, 2) or None,
            ))
    if not result.rows and not result.problems:
        result.problems.append("An OFX file with no transactions in it.")
    return result
