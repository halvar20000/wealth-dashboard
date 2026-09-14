"""CSV and PDF importers, and the code that stores what they produce.

Adding a broker means adding one module with `SLUG`, `LABEL`,
`matches(header, sample)` and `parse(content)` — and adding it to
`IMPORTERS` (a CSV) or `PDF_IMPORTERS` (a statement PDF, where
`matches` is handed the extracted text). Nothing else in the app changes.

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
from . import (ca_switzerland, degiro, dkb, dkb_pdf, generic, swissquote_beleg_pdf,
               swissquote_pdf, trade_republic)
from .base import (ParsedTxn, ParseResult,  # noqa: F401  (re-exported)
                   normalise_csv_text)

IMPORTERS = [degiro, trade_republic, dkb, ca_switzerland]
PDF_IMPORTERS = [dkb_pdf, swissquote_pdf, swissquote_beleg_pdf]


def sniff(content: bytes | str):
    """Which importer, if any, recognises this file."""
    if isinstance(content, bytes) and content.startswith(b"%PDF"):
        try:
            text = dkb_pdf.pdf_text(content)
        except RuntimeError:
            raise                        # pypdf missing: say so, not "unrecognised"
        except Exception:                            # noqa: BLE001
            return None
        for module in PDF_IMPORTERS:
            try:
                if module.matches([], text):
                    return module
            except Exception:                        # noqa: BLE001
                continue
        return None

    text = content.decode("utf-8-sig", "replace") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    sample = text[:8192]
    try:
        header = next(csv.reader(io.StringIO(sample)))
    except (StopIteration, csv.Error):
        return None
    for module in IMPORTERS:
        try:
            if module.matches(header, sample):
                return module
        except Exception:                            # noqa: BLE001
            continue
    # Then the mappings the user drew, by the file's header — see
    # generic.py. After the built-ins on purpose: a mapping saved for a
    # Degiro file would be a mistake, and the built-in is the right one.
    return generic.sniff(content)


def begin_import(account_id: int, filename: str | None, source: str) -> int:
    """A record of the file about to be imported, so it can be undone."""
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO imports (account_id, filename, source) VALUES (?, ?, ?)",
                           (account_id, (filename or "")[-120:] or None, source))
        return int(cur.lastrowid)


def undo_import(account_id: int, import_id: int) -> int:
    """Remove every row this import brought — and only those: a row a
    re-import found already there belongs to the import that first
    brought it. The balance it wrote stays; a balance is a reading."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM transactions WHERE account_id = ? AND import_id = ?",
                           (account_id, import_id))
        conn.execute("DELETE FROM imports WHERE id = ? AND account_id = ?", (import_id, account_id))
        return cur.rowcount


def recent_imports(account_id: int, limit: int = 8) -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT i.*, (SELECT COUNT(*) FROM transactions t WHERE t.import_id = i.id) AS still "
            "FROM imports i WHERE i.account_id = ? ORDER BY i.id DESC LIMIT ?", (account_id, limit))]


def store(account_id: int, parsed: ParseResult, source: str, import_id: int | None = None) -> dict:
    """Write the parsed rows. Returns what actually happened.

    `INSERT OR IGNORE` against the unique index on `external_id` is the
    whole deduplication strategy, so re-importing last month's export on
    top of this month's is free and correct rather than something the
    user has to think about.
    """
    inserted = duplicates = 0
    with get_conn() as conn:
        # Rows the account already has from elsewhere, under other ids
        # — see accounts.ledger_until. They count as duplicates, which
        # is what they are.
        until = conn.execute("SELECT ledger_until FROM accounts WHERE id = ?",
                             (account_id,)).fetchone()
        until = until["ledger_until"] if until else None
        for row in parsed.rows:
            if until and row.txn_date <= until and not (row.external_id or "").startswith("fp:"):
                duplicates += 1
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO transactions "
                "(account_id, txn_date, description, counterparty, amount, "
                " currency, external_id, kind, isin, security_name, quantity, "
                " price, fee, tax, source, import_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (account_id, row.txn_date, row.description, row.counterparty,
                 row.amount, row.currency, row.external_id, row.kind, row.isin,
                 row.security_name, row.quantity, row.price, row.fee, row.tax,
                 source, import_id))
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
    if import_id is not None:
        with get_conn() as conn:
            conn.execute("UPDATE imports SET inserted = inserted + ? WHERE id = ?", (inserted, import_id))

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

    Every row that carries a quantity moves units — a buy, a sale, a
    transfer in from another broker, a staking reward — and all of
    them count towards what is held. Only a buy or a sale moves money
    in or out for it, so net_invested is theirs alone: a position
    transferred in has a quantity and no cost here, which is the truth.

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
               AND quantity IS NOT NULL
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
