"""Trade Republic — the transaction export.

Export it in the app: Profile → Transactions → export as CSV. Trade
Republic writes a proper machine-readable file, which makes this the
easy one of the two: ISO dates, a decimal point, one row per event, and
a real `transaction_id`.

Three things worth knowing anyway.

**`symbol` holds an ISIN**, not a ticker. That is a gift — it is the same
key Degiro puts in its own `ISIN` column, so a position held at both
brokers lines up with no mapping table.

**`amount` is already signed** from the account's point of view: a
purchase is negative, a dividend positive. Unlike the bank feed, there
is no separate direction field to apply, and applying one anyway would
flip every buy into a sale.

**`type` is a long and growing list.** The export seen while writing this
carried BUY, SELL, DIVIDEND, INTEREST_PAYMENT, CUSTOMER_INBOUND,
CUSTOMER_INPAYMENT, TRANSFER_INBOUND, TRANSFER_INSTANT_INBOUND,
CARD_TRANSACTION, MIGRATION, PRIVATE_MARKET_BUY, SHARE_EXCHANGE,
REVERSE_SPLIT, BONUS and TAX_OPTIMIZATION. An unknown one is mapped by
its `category` and, failing that, kept as `other` with its own text in
the description — never dropped. A broker adding a row type must not
make money disappear from a total.
"""

from __future__ import annotations

import csv
import io

from .base import (ParsedTxn, ParseResult, find_isin, normalise_csv_text,
                   parse_date, parse_decimal)

SLUG = "trade_republic"
LABEL = "Trade Republic — transaction export"

REQUIRED_COLUMNS = {"datetime", "date", "category", "type", "amount", "currency",
                    "transaction_id"}

# Only the types whose meaning is unambiguous. Everything else falls
# through to the category rule below, which is the honest default.
_TYPE_KIND = {
    "BUY": "buy",
    "PRIVATE_MARKET_BUY": "buy",
    "SAVINGS_PLAN_EXECUTION": "buy",
    "SELL": "sell",
    "DIVIDEND": "dividend",
    "INTEREST_PAYMENT": "interest",
    "CUSTOMER_INPAYMENT": "deposit",
    "CUSTOMER_INBOUND": "deposit",
    "TRANSFER_INBOUND": "deposit",
    "TRANSFER_INSTANT_INBOUND": "deposit",
    "CUSTOMER_OUTPAYMENT": "withdrawal",
    "TRANSFER_OUTBOUND": "withdrawal",
    "CARD_TRANSACTION": "withdrawal",
    "FEE": "fee",
    "TAX_REFUND": "tax",
    "TAX_OPTIMIZATION": "tax",
    # A securities transfer in, a share exchange, a split: units change
    # without money moving. Marked as transfers so they are visible and
    # are not counted as money entering or leaving.
    "MIGRATION": "transfer",
    "SHARE_EXCHANGE": "transfer",
    "REVERSE_SPLIT": "transfer",
    "SPLIT": "transfer",
    "BONUS": "transfer",
}


def matches(header: list[str], sample: str) -> bool:
    return REQUIRED_COLUMNS.issubset({h.strip().lower() for h in header})


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    reader = csv.DictReader(io.StringIO(text))
    result = ParseResult()

    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(
            {f.strip().lower() for f in reader.fieldnames}):
        result.problems.append(
            "This is not a Trade Republic export — expected columns include "
            + ", ".join(sorted(REQUIRED_COLUMNS)))
        return result

    for line_no, row in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}

        date = parse_date(row.get("date") or row.get("datetime"))
        if not date:
            result.problems.append(f"line {line_no}: unreadable date")
            continue

        amount = parse_decimal(row.get("amount"))
        if amount is None:
            result.skipped += 1
            continue

        ttype = (row.get("type") or "").upper()
        category = (row.get("category") or "").upper()
        kind = _TYPE_KIND.get(ttype)
        if kind is None:
            # Unknown type. Fall back to what the category says, then to
            # the direction of the money — anything but silence.
            if category == "TRADING":
                kind = "buy" if amount < 0 else "sell"
            elif category == "CORPORATE_ACTION":
                kind = "dividend" if amount > 0 else "other"
            elif category == "DELIVERY":
                kind = "transfer"
            else:
                kind = "other"

        isin = row.get("symbol") or None
        if isin and not find_isin(isin):
            # `symbol` normally holds an ISIN, but not on a cash row.
            isin = None

        quantity = parse_decimal(row.get("shares"))
        if quantity is not None and kind == "sell":
            quantity = -abs(quantity)

        description = (row.get("description") or row.get("name")
                       or ttype.replace("_", " ").title())
        if ttype and ttype not in _TYPE_KIND:
            # Keep the original word where the mapping was a guess, so a
            # surprising row can be traced back to what the broker called it.
            description = f"{description} [{ttype}]"

        result.rows.append(ParsedTxn(
            txn_date=date,
            description=" ".join(str(description).split())[:500],
            amount=amount,
            currency=(row.get("currency") or account_currency).upper()[:3],
            kind=kind,
            external_id=f"tr:{row['transaction_id']}" if row.get("transaction_id") else None,
            counterparty=row.get("counterparty_name") or None,
            isin=isin,
            security_name=row.get("name") or None,
            quantity=quantity,
            price=parse_decimal(row.get("price")),
            fee=parse_decimal(row.get("fee")),
            tax=parse_decimal(row.get("tax")),
        ))

    return result
