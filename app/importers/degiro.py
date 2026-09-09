"""Degiro — the `Account.csv` cash statement.

Export it from Degiro: Inbox → Account statement → pick the period →
CSV. It is the account's cash ledger: every deposit, trade, dividend,
fee and currency conversion, one row each.

Two things about this file will bite anyone who writes a parser for it.

**The header has two blank column names.**

    Date,Time,Value date,Product,ISIN,Description,FX,Change,,Balance,,Order Id

`Change` and `Balance` hold a CURRENCY; the unnamed column after each
holds the amount. Read this with `csv.DictReader` and both blank names
collapse to a single key `''` — the second silently overwrites the
first, so every row's change amount becomes its balance amount and the
whole import is wrong in a way that looks plausible. This module reads
by index for that reason. Do not "tidy" it into a DictReader.

**The descriptions are in the account's own language.**

    Achat 71 iShares Core MSCI World UCITS ETF USD (Acc)@112,5 EUR (IE…)
    Vente 1 Norwest Minerals Ltd@0,011 AUD (AU…)

A French account says Achat/Vente, a Dutch one Koop/Verkoop, a German
one Kauf/Verkauf. So classification here is STRUCTURAL and never relies
on a verb:

* an `@` in the description means a trade — that is where the price is,
  and no other row type has one;
* the quantity is the first number, the price the number after the `@`;
* **buy or sell comes from the sign of the cash amount**, not the word.
  Money out is a purchase in every language.

Keywords are used only where structure runs out — telling a fee from a
tax — and then in four languages, as a hint rather than a decision.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re

from .base import (ParsedTxn, ParseResult, find_isin, normalise_csv_text,
                   parse_date, parse_decimal)

SLUG = "degiro"
LABEL = "Degiro — Account.csv"

# The exact header Degiro writes. Used to recognise the file, and
# checked rather than assumed: a changed layout must fail loudly at the
# first row instead of quietly mapping the wrong column.
EXPECTED_HEADER = ["Date", "Time", "Value date", "Product", "ISIN",
                   "Description", "FX", "Change", "", "Balance", "", "Order Id"]

C_DATE, C_TIME, C_VALUE_DATE, C_PRODUCT, C_ISIN, C_DESC, C_FX = range(7)
C_CHANGE_CCY, C_CHANGE_AMT, C_BALANCE_CCY, C_BALANCE_AMT, C_ORDER_ID = range(7, 12)

# `<verb> <qty> <name>@<price> <ccy>`, optionally behind a corporate-action
# prefix that Degiro puts in front of the verb:
#
#     Achat 71 iShares Core MSCI World UCITS ETF USD (Acc)@112,5 EUR
#     Fusion: Vente 100 Readly International AB (publ)@0 SEK
#     Fractionnement d'actions: Achat 15 ADR on Zepp Health@0 USD
#
# Without the optional prefix group, every merger, split, delisting and
# subscription-rights row loses its quantity — 36 of them in the export
# this was tested against, each one a position that would come out wrong.
_TRADE_RE = re.compile(
    r"^(?:[^:@]{1,60}:\s*)?\S+\s+([\d.,]+)\s+(.+?)@([\d.,]+)\s*([A-Z]{3})?", re.S)

# Buy and sell verbs, only for the case below where the cash amount is
# zero and so cannot say which way the units went. Sell is checked FIRST
# and the order is not cosmetic: "Verkauf" contains "kauf" and "Verkoop"
# contains "koop", so testing for a purchase first calls every German and
# Dutch sale a purchase.
_SELL_VERBS = ("vente", "verkauf", "verkoop", "sell", "sale", "venta", "vendita")
_BUY_VERBS = ("achat", "kauf", "koop", "buy", "purchase", "compra", "acquisto")

_TAX_WORDS = ("impôt", "impot", "tax", "steuer", "belasting", "withholding")
_FEE_WORDS = ("frais", "fee", "gebühr", "gebuhr", "kosten", "commission",
              "courtage", "connexion", "exchange connectivity")
_INTEREST_WORDS = ("intérêt", "interet", "interest", "zins", "rente")
_DEPOSIT_WORDS = ("dépôt", "depot", "deposit", "einzahlung", "storting",
                  "ideal", "sofort")
_WITHDRAWAL_WORDS = ("retrait", "withdrawal", "auszahlung", "opname")
# Money moving between Degiro's own cash account and the flatex bank
# account behind it. Real rows, but internal: counting them as deposits
# and withdrawals would inflate both sides of every cash-flow total.
_INTERNAL_WORDS = ("cash sweep", "flatex withdrawal", "flatex deposit",
                   "compte espèces", "compte especes", "geldkonto",
                   "money market fund", "cash fund")


def matches(header: list[str], sample: str) -> bool:
    return [h.strip() for h in header] == EXPECTED_HEADER


def _has(text: str, words) -> bool:
    low = text.lower()
    return any(w in low for w in words)


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    reader = csv.reader(io.StringIO(text))
    result = ParseResult()

    try:
        header = next(reader)
    except StopIteration:
        result.problems.append("The file is empty.")
        return result
    if [h.strip() for h in header] != EXPECTED_HEADER:
        result.problems.append(
            "This is not the Degiro Account.csv layout. Expected columns: "
            + ", ".join(h or "(blank)" for h in EXPECTED_HEADER))
        return result

    for line_no, row in enumerate(reader, start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) < 12:
            result.problems.append(f"line {line_no}: only {len(row)} columns")
            continue

        date = parse_date(row[C_DATE])
        if not date:
            # Degiro sometimes writes a raw newline INSIDE a description
            # and does not quote the field, so one record arrives as two
            # lines:
            #
            #     …,Frais de connexion aux places boursières 2026 (New York
            #     ,,,,,Stock Exchange - NSY),,,,,,
            #
            # The second line has no date, no amount and no currency —
            # only the rest of the sentence. Stitching it back on is
            # better than reporting it: the row it belongs to is already
            # imported, just with half its description.
            tail = row[C_DESC].strip()
            if (tail and not row[C_CHANGE_AMT].strip() and result.rows):
                previous = result.rows[-1]
                previous.description = " ".join(
                    f"{previous.description} {tail}".split())[:500]
                continue
            result.problems.append(f"line {line_no}: unreadable date {row[C_DATE]!r}")
            continue

        amount = parse_decimal(row[C_CHANGE_AMT])
        if amount is None:
            # A row with no cash movement — Degiro emits a few, and they
            # carry no information this app can use. Skipped, not a problem.
            result.skipped += 1
            continue

        currency = (row[C_CHANGE_CCY] or account_currency).strip().upper()[:3]
        description = " ".join(row[C_DESC].split())
        isin = (row[C_ISIN].strip() or find_isin(description) or None)
        product = row[C_PRODUCT].strip() or None
        order_id = row[C_ORDER_ID].strip()

        txn = ParsedTxn(txn_date=date, description=description, amount=amount,
                        currency=currency, isin=isin, security_name=product,
                        external_id=_external_id(row, order_id))

        if "@" in description:
            # A trade. The sign of the cash decides the direction: money
            # out bought something, money in sold something.
            #
            # Except when no money moved. A merger, a split or a delisting
            # books both legs at a price of zero, so BOTH would come out
            # as sales and the incoming units would be subtracted instead
            # of added. That is the one place the verb has to be read —
            # and reading it is safe here precisely because it is the last
            # resort rather than the rule.
            if amount < 0:
                txn.kind = "buy"
            elif amount > 0:
                txn.kind = "sell"
            elif _has(description, _SELL_VERBS):
                txn.kind = "sell"
            elif _has(description, _BUY_VERBS):
                txn.kind = "buy"
            else:
                txn.kind = "transfer"      # units moved, direction unknown
            m = _TRADE_RE.match(description)
            if m:
                qty = parse_decimal(m.group(1))
                txn.price = parse_decimal(m.group(3))
                txn.security_name = product or " ".join(m.group(2).split())
                if qty is not None:
                    txn.quantity = qty if txn.kind == "buy" else -qty
            if txn.quantity is None and txn.kind != "transfer":
                result.problems.append(
                    f"line {line_no}: looks like a trade but the quantity "
                    f"could not be read from {description[:60]!r}")
        elif _has(description, _INTERNAL_WORDS):
            txn.kind = "transfer"
        elif isin and amount > 0:
            txn.kind = "dividend"
        elif isin and amount < 0:
            txn.kind = "tax" if _has(description, _TAX_WORDS) else "fee"
        elif _has(description, _TAX_WORDS):
            txn.kind = "tax"
        elif _has(description, _FEE_WORDS):
            txn.kind = "fee"
        elif _has(description, _INTEREST_WORDS):
            txn.kind = "interest"
        elif _has(description, _DEPOSIT_WORDS) and amount > 0:
            txn.kind = "deposit"
        elif _has(description, _WITHDRAWAL_WORDS) and amount < 0:
            txn.kind = "withdrawal"
        else:
            txn.kind = "other"

        result.rows.append(txn)

        # The running balance after this row. Degiro writes newest first,
        # so the first row that has one is the current cash balance —
        # but the file is not guaranteed to be sorted, so take the row
        # with the latest date rather than the first one seen.
        balance = parse_decimal(row[C_BALANCE_AMT])
        if balance is not None:
            current = result.closing_balance
            if current is None or date >= current["as_of"]:
                result.closing_balance = {
                    "amount": balance,
                    "currency": (row[C_BALANCE_CCY] or currency).strip().upper()[:3],
                    "as_of": date,
                }

    return result


def _external_id(row: list[str], order_id: str) -> str:
    """A stable id, so re-importing an overlapping export is harmless.

    An Order Id is not enough on its own: one order produces several
    rows — the trade, the commission, sometimes a currency conversion —
    which share it. So the id includes what makes each row distinct.

    Where there is no order id, the RUNNING BALANCE goes into the hash.
    That is the trick worth keeping: a balance is a property of the whole
    history rather than of the export window, so it is identical across
    two overlapping downloads *and* it separates two rows that share a
    date, an amount and a description — which a statement of regular
    charges is full of.
    """
    seed = "|".join([
        order_id,
        row[C_DATE], row[C_TIME],
        row[C_ISIN], row[C_CHANGE_AMT], row[C_CHANGE_CCY],
        row[C_BALANCE_AMT],
        " ".join(row[C_DESC].split()),
    ])
    return f"degiro:{hashlib.sha1(seed.encode()).hexdigest()[:20]}"
