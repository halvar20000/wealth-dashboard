"""Interactive Brokers — a Flex Query statement (XML).

IBKR's own export: Account Management → Reports → Flex Queries → an
Activity Flex Query with Trades, Cash Transactions, Open Positions and
the Cash Report ticked, run for any period and downloaded as XML. The
same XML is what the Flex Web Service hands the connector in
`brokers/ibkr.py`; this module reads either.

What is read, and what it becomes
---------------------------------
  * **Trades** (`<Trade>`, execution level) — a buy or a sale: the
    quantity signed, the trade price, the money as IBKR's `netCash`
    (proceeds less commission and taxes), the commission as the fee.
    A currency conversion (`assetCategory="CASH"`) is not a trade in
    a security and is left out and counted.
  * **Cash transactions** (`<CashTransaction>`) — Dividends and
    Payment In Lieu Of Dividends as dividends, with the Withholding
    Tax of the same security and day folded in as the tax; Broker and
    Bond Interest Received as interest; Deposits/Withdrawals by their
    sign; Other Fees, Commission Adjustments and Interest Paid as fees
    (a positive adjustment is a refund).
  * **Open positions** and the **Cash Report** — the holdings IBKR
    says you have, for the connector's drift check, and the cash of
    the account's currency as its balance.

Every element carries `transactionID`, which is the id: two overlapping
statements never double a row.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .base import ParsedTxn, ParseResult

SLUG = "ibkr_flex"
LABEL = "Interactive Brokers — Flex Query XML"

_DIVIDEND_TYPES = ("Dividends", "Payment In Lieu Of Dividends")
_INTEREST_TYPES = ("Broker Interest Received", "Bond Interest Received")
_FEE_TYPES = ("Other Fees", "Commission Adjustments", "Broker Interest Paid", "Bond Interest Paid",
              "Broker Fees", "Advisor Fees")


def matches(header: list[str], sample: str) -> bool:
    return "<FlexQueryResponse" in sample


@dataclass
class Statement:
    account_id: str = ""
    currency: str = ""
    from_date: str | None = None
    to_date: str | None = None
    rows: list = field(default_factory=list)
    positions: dict = field(default_factory=dict)     # ISIN or symbol → (quantity, name)
    cash: dict = field(default_factory=dict)          # currency → ending cash
    skipped: int = 0
    problems: list = field(default_factory=list)


def _num(raw: str | None) -> float | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _date(raw: str | None) -> str | None:
    """20240315, 2024-03-15, 20240315;093000 or 2024-03-15 09:30:00."""
    if not raw:
        return None
    m = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})", raw.strip())
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def _rows_of(stmt: ET.Element, container: str, row: str) -> list[ET.Element]:
    found = [r for c in stmt.findall(container) for r in c.findall(row)]
    return found or stmt.findall(row)


def read(content: bytes | str) -> list[Statement]:
    """Every FlexStatement in the XML, read."""
    text = content.decode("utf-8-sig", "replace") if isinstance(content, bytes) else content
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"not well-formed XML: {e}") from None
    if root.tag != "FlexQueryResponse":
        raise ValueError("no <FlexQueryResponse> root — not an IBKR Flex statement")
    out = []
    for stmt in root.iter("FlexStatement"):
        s = Statement(account_id=stmt.get("accountId", ""), from_date=_date(stmt.get("fromDate")),
                      to_date=_date(stmt.get("toDate")))
        info = stmt.find("AccountInformation")
        s.currency = ((info.get("currency") if info is not None else "") or "").upper()
        _trades(stmt, s)
        _cash(stmt, s)
        for p in _rows_of(stmt, "OpenPositions", "OpenPosition"):
            if (p.get("levelOfDetail") or "SUMMARY").upper() not in ("SUMMARY", ""):
                continue
            qty = _num(p.get("position"))
            key = (p.get("isin") or p.get("symbol") or "").strip()
            if key and qty:
                s.positions[key] = (qty, p.get("description") or p.get("symbol") or key)
        for c in _rows_of(stmt, "CashReport", "CashReportCurrency"):
            ccy = (c.get("currency") or "").upper()
            end = _num(c.get("endingCash"))
            if ccy and ccy != "BASE_SUMMARY" and end is not None:
                s.cash[ccy] = end
        out.append(s)
    return out


def _trades(stmt: ET.Element, s: Statement) -> None:
    for t in _rows_of(stmt, "Trades", "Trade"):
        level = (t.get("levelOfDetail") or "EXECUTION").upper()
        if level not in ("EXECUTION", ""):
            continue                                  # ORDER / SUMMARY rows repeat the fills
        category = (t.get("assetCategory") or "").upper()
        if category == "CASH":
            s.skipped += 1                            # a currency conversion, not a security
            continue
        qty = _num(t.get("quantity"))
        price = _num(t.get("tradePrice"))
        date = _date(t.get("tradeDate") or t.get("dateTime"))
        if qty is None or not date:
            s.problems.append(f"a trade without quantity or date was left out ({t.get('symbol')})")
            continue
        commission = abs(_num(t.get("ibCommission")) or 0.0)
        taxes = abs(_num(t.get("taxes")) or 0.0)
        net = _num(t.get("netCash"))
        if net is None:
            proceeds = _num(t.get("proceeds"))
            net = (proceeds if proceeds is not None else -(qty * (price or 0.0))) - commission - taxes
        side = (t.get("buySell") or "").upper() or ("BUY" if qty > 0 else "SELL")
        kind = "buy" if side.startswith("BUY") else "sell"
        multiplier = _num(t.get("multiplier")) or 1.0
        ref = t.get("transactionID") or t.get("tradeID") or ""
        s.rows.append(ParsedTxn(
            txn_date=date,
            description=f"{'Kauf' if kind == 'buy' else 'Verkauf'} {t.get('description') or t.get('symbol') or ''}".strip()[:500],
            amount=round(net, 2), currency=(t.get("currency") or s.currency or "USD").upper(),
            kind=kind, external_id=f"ibkr:{s.account_id}:{ref}" if ref else None,
            isin=(t.get("isin") or None), security_name=t.get("description") or t.get("symbol"),
            quantity=abs(qty) if kind == "buy" else -abs(qty),
            price=abs(price) * multiplier if price and multiplier != 1.0 else (abs(price) if price else None),
            fee=round(commission, 2) or None, tax=round(taxes, 2) or None,
        ))


def _cash(stmt: ET.Element, s: Statement) -> None:
    items = []
    for c in _rows_of(stmt, "CashTransactions", "CashTransaction"):
        level = (c.get("levelOfDetail") or "DETAIL").upper()
        if level not in ("DETAIL", ""):
            continue
        amount = _num(c.get("amount"))
        date = _date(c.get("dateTime") or c.get("settleDate") or c.get("reportDate"))
        if amount is None or not date:
            s.problems.append(f"a cash transaction without amount or date was left out ({c.get('type')})")
            continue
        items.append((c, amount, date))
    # Withholding tax by (security, day), folded into the dividend it belongs to.
    withheld: dict[tuple, list] = {}
    for c, amount, date in items:
        if c.get("type") == "Withholding Tax":
            withheld.setdefault((c.get("isin") or c.get("symbol") or "", date, (c.get("currency") or "").upper()), []).append((c, amount))
    for c, amount, date in items:
        ctype = c.get("type") or ""
        ccy = (c.get("currency") or s.currency or "USD").upper()
        ref = c.get("transactionID") or ""
        ext = f"ibkr:{s.account_id}:{ref}" if ref else None
        name = c.get("description") or c.get("symbol") or ctype
        isin = c.get("isin") or None
        if ctype == "Withholding Tax":
            key = (c.get("isin") or c.get("symbol") or "", date, ccy)
            if any(d.get("type") in _DIVIDEND_TYPES and (d.get("isin") or d.get("symbol") or "") == key[0]
                   and _date(d.get("dateTime") or d.get("settleDate") or d.get("reportDate")) == date for d, _, _ in items):
                continue                              # folded below
            s.rows.append(ParsedTxn(txn_date=date, description=f"Steuer {name}"[:500], amount=round(amount, 2), currency=ccy,
                                    kind="tax", external_id=ext, isin=isin, security_name=c.get("symbol")))
            continue
        if ctype in _DIVIDEND_TYPES:
            key = (c.get("isin") or c.get("symbol") or "", date, ccy)
            tax = sum(abs(a) for _, a in withheld.pop(key, []))
            s.rows.append(ParsedTxn(txn_date=date, description=f"Dividende {c.get('symbol') or name}"[:500],
                                    amount=round(amount - tax, 2), currency=ccy, kind="dividend", external_id=ext,
                                    isin=isin, security_name=c.get("symbol") or name, tax=round(tax, 2) or None))
        elif ctype in _INTEREST_TYPES:
            s.rows.append(ParsedTxn(txn_date=date, description=f"Zinsen {name}"[:500], amount=round(amount, 2), currency=ccy,
                                    kind="interest", external_id=ext))
        elif ctype == "Deposits/Withdrawals":
            s.rows.append(ParsedTxn(txn_date=date, description=(name or ctype)[:500], amount=round(amount, 2), currency=ccy,
                                    kind="deposit" if amount > 0 else "withdrawal", external_id=ext))
        elif ctype in _FEE_TYPES:
            s.rows.append(ParsedTxn(txn_date=date, description=f"Gebühr {name}"[:500], amount=round(amount, 2), currency=ccy,
                                    kind="fee", external_id=ext))
        else:
            s.skipped += 1


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    result = ParseResult()
    try:
        statements = read(content)
    except ValueError as e:
        result.problems.append(f"This is not an IBKR Flex statement: {e}")
        return result
    if not statements:
        result.problems.append("The Flex XML holds no statement.")
        return result
    for s in statements:
        result.rows.extend(s.rows)
        result.skipped += s.skipped
        result.problems.extend(s.problems)
        ccy = account_currency.upper()[:3]
        if ccy in s.cash:
            result.closing_balance = {"amount": round(s.cash[ccy], 2), "currency": ccy, "as_of": s.to_date}
        elif s.currency in s.cash and result.closing_balance is None:
            result.closing_balance = {"amount": round(s.cash[s.currency], 2), "currency": s.currency, "as_of": s.to_date}
    return result
