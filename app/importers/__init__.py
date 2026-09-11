"""CSV importers, and the code that stores what they produce.

Adding a broker means adding one module with `SLUG`, `LABEL`,
`matches(header, sample)` and `parse(content)` — and adding it to
`IMPORTERS`. Nothing else in the app changes.

The file is recognised rather than declared. Asking the user to pick
"Degiro" from a dropdown before uploading a file that says Degiro all
over it is asking them to get it wrong, and picking the wrong parser
produces a confident, silent mess.
"""

from __future__ import annotations

import csv
import io

from .. import categories
from ..db import get_conn
from . import degiro, trade_republic
from .base import (ParsedTxn, ParseResult,  # noqa: F401  (re-exported)
                   normalise_csv_text)

IMPORTERS = [degiro, trade_republic]


def sniff(content: bytes | str):
    """Which importer, if any, recognises this file."""
    text = content.decode("utf-8-sig", "replace") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    sample = text[:8192]
    try:
        header = next(csv.reader(io.StringIO(sample)))
    except StopIteration:
        return None
    for module in IMPORTERS:
        try:
            if module.matches(header, sample):
                return module
        except Exception:                            # noqa: BLE001
            continue
    return None


def store(account_id: int, parsed: ParseResult, source: str) -> dict:
    """Write the parsed rows. Returns what actually happened.

    `INSERT OR IGNORE` against the unique index on `external_id` is the
    whole deduplication strategy, so re-importing last month's export on
    top of this month's is free and correct rather than something the
    user has to think about.
    """
    inserted = duplicates = 0
    with get_conn() as conn:
        for row in parsed.rows:
            cur = conn.execute(
                "INSERT OR IGNORE INTO transactions "
                "(account_id, txn_date, description, counterparty, amount, "
                " currency, external_id, kind, isin, security_name, quantity, "
                " price, fee, tax, source) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (account_id, row.txn_date, row.description, row.counterparty,
                 row.amount, row.currency, row.external_id, row.kind, row.isin,
                 row.security_name, row.quantity, row.price, row.fee, row.tax,
                 source))
            if cur.rowcount:
                inserted += 1
            else:
                duplicates += 1
        if parsed.closing_balance:
            cb = parsed.closing_balance
            # Only if it is newer than what is already recorded. Importing
            # an OLD export after a recent one must not wind the balance
            # backwards — and people do import their files out of order.
            newest = conn.execute(
                "SELECT MAX(as_of) AS as_of FROM balances WHERE account_id = ?",
                (account_id,)).fetchone()["as_of"]
            if newest is None or cb["as_of"] >= newest:
                conn.execute(
                    "INSERT INTO balances (account_id, amount, currency, "
                    "balance_type, as_of) VALUES (?, ?, ?, 'statement', ?)",
                    (account_id, cb["amount"], cb["currency"], cb["as_of"]))

    if inserted:
        # Kinds and the user's rules, on the rows that just arrived —
        # see categories.categorise_new().
        categories.categorise_new(account_id)

    return {"inserted": inserted, "duplicates": duplicates,
            "skipped": parsed.skipped, "problems": parsed.problems,
            "parsed": len(parsed.rows),
            "closing_balance": parsed.closing_balance}


def positions(account_id: int) -> list[dict]:
    """What the account holds, computed from its trades.

    A broker's cash statement does not state a position; it states the
    events that produced one. So quantity is the running sum of every
    buy and sell, and a holding sold down to nothing disappears rather
    than lingering at zero.

    `last_price` is the price of the most recent trade, NOT a market
    price — this app has no price feed yet. It is labelled as such on
    the page, because a stale number presented as a valuation is worse
    than no valuation at all.
    """
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT isin,
                   MAX(security_name)               AS name,
                   SUM(COALESCE(quantity, 0))       AS quantity,
                   SUM(CASE WHEN kind = 'buy'  THEN -amount ELSE 0 END)
                     - SUM(CASE WHEN kind = 'sell' THEN amount ELSE 0 END)
                                                    AS net_invested,
                   MAX(txn_date)                    AS last_trade,
                   COUNT(*)                         AS trades,
                   MAX(currency)                    AS currency
              FROM transactions
             WHERE account_id = ? AND isin IS NOT NULL
               AND kind IN ('buy', 'sell') AND quantity IS NOT NULL
             GROUP BY isin
             ORDER BY name
            """, (account_id,)).fetchall()

        out = []
        for r in rows:
            qty = r["quantity"] or 0
            if abs(qty) < 1e-9:
                continue                 # closed position
            last = conn.execute(
                "SELECT price FROM transactions WHERE account_id = ? AND isin = ? "
                "AND price IS NOT NULL ORDER BY txn_date DESC, id DESC LIMIT 1",
                (account_id, r["isin"])).fetchone()
            item = dict(r)
            item["last_price"] = last["price"] if last else None
            item["value_at_last_price"] = (
                qty * last["price"] if last and last["price"] else None)
            # A negative quantity is not a short position — it is a sale
            # whose matching purchase is older than the export. Saying so
            # is the useful response: the fix is to export a longer
            # period, and silently hiding the row would hide the fact
            # that the history is incomplete.
            item["incomplete_history"] = qty < 0
            out.append(item)
    return out
