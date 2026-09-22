"""CSV and PDF importers, and the code that stores what they produce.

Adding a broker means adding one module with `SLUG`, `LABEL`,
`matches(header, sample)` and `parse(content)` — and adding it to
`IMPORTERS` (a CSV), `FORMAT_IMPORTERS` (a statement format: CAMT,
MT940, OFX) or `PDF_IMPORTERS` (a statement PDF, where `matches` is
handed the extracted text). Nothing else in the app changes.

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
from . import (ca_switzerland, camt053, degiro, dkb, dkb_pdf, finary, generic, ibkr_flex, mt940, ofx, payslip,
               payslip_map, swissquote_beleg_pdf, swissquote_pdf, trade_republic)
from .base import (ParsedTxn, ParseResult,  # noqa: F401  (re-exported)
                   normalise_csv_text)

IMPORTERS = [degiro, trade_republic, dkb, ca_switzerland, finary]
# The statement formats — not one bank's file but a standard every bank
# writes alike. Looked at before the CSVs: an XML or a SWIFT file is
# unmistakable, a CSV is anyone's.
FORMAT_IMPORTERS = [camt053, mt940, ofx, ibkr_flex]
from . import pdf as _pdf_specs
PDF_IMPORTERS = [dkb_pdf, swissquote_pdf, swissquote_beleg_pdf, payslip] + _pdf_specs.READERS


def catalogue() -> list[dict]:
    """Every reader, for the import page's list: {name, what, kinds}
    — one line per bank or format, its readers' papers joined, sorted
    by name. "kinds" is which of PDF, CSV and format the name has."""
    by_name: dict[str, dict] = {}
    for kind, modules in (("PDF", PDF_IMPORTERS), ("CSV", IMPORTERS), ("format", FORMAT_IMPORTERS)):
        for m in modules:
            if getattr(m, "SLUG", "") in ("payslip",):
                continue
            name, _, what = m.LABEL.partition(" — ")
            name = name.strip()
            entry = by_name.setdefault(name, {"name": name, "what": [], "kinds": []})
            if what and what not in entry["what"]:
                entry["what"].append(what)
            if kind not in entry["kinds"]:
                entry["kinds"].append(kind)
    rows = sorted(by_name.values(), key=lambda e: e["name"].lower())
    for e in rows:
        e["what"] = " · ".join(e["what"])
    return rows


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
        # Then the payslip layouts the user mapped — after the built-ins,
        # as with the CSV mappings.
        return payslip_map.sniff(text)

    text = content.decode("utf-8-sig", "replace") if isinstance(content, bytes) else content
    for module in FORMAT_IMPORTERS:
        if module.matches([], text[:8192]):
            return module
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


def _save_payslip(conn, account_id: int, slip: dict, import_id: int | None) -> None:
    """The statement, whole. The same sheet again — same employer,
    earner and month — replaces the earlier reading of it."""
    import json
    conn.execute(
        "INSERT INTO payslips (account_id, import_id, employer, employee, period, paid_on, currency, "
        " gross, base_salary, bonus, allowances, employee_social, employee_pension, tax, other_deductions, "
        " net_paid, employer_pension, employer_social, employer_side_known, layout, lines) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(employer, employee, period) DO UPDATE SET account_id = excluded.account_id, "
        " import_id = excluded.import_id, paid_on = excluded.paid_on, currency = excluded.currency, "
        " gross = excluded.gross, base_salary = excluded.base_salary, bonus = excluded.bonus, "
        " allowances = excluded.allowances, employee_social = excluded.employee_social, "
        " employee_pension = excluded.employee_pension, tax = excluded.tax, "
        " other_deductions = excluded.other_deductions, net_paid = excluded.net_paid, "
        " employer_pension = excluded.employer_pension, employer_social = excluded.employer_social, "
        " employer_side_known = excluded.employer_side_known, layout = excluded.layout, lines = excluded.lines",
        (account_id, import_id, slip["employer"], slip["employee"], slip["period"], slip["paid_on"],
         slip["currency"], slip["gross"], slip["base_salary"], slip["bonus"], slip["allowances"],
         slip["employee_social"], slip["employee_pension"], slip["tax"], slip["other_deductions"],
         slip["net_paid"], slip["employer_pension"], slip["employer_social"],
         1 if slip["employer_side_known"] else 0, slip["layout"], json.dumps(slip["lines"])))


def undo_import(account_id: int, import_id: int) -> int:
    """Remove every row this import brought — and only those: a row a
    re-import found already there belongs to the import that first
    brought it. The balance it wrote stays; a balance is a reading.

    A move-in had marked the account's ledger as on record up to its
    last row; with its rows gone that mark would keep every later file
    out, so it is set back to what the remaining moved-in rows cover,
    or cleared."""
    with get_conn() as conn:
        src = conn.execute("SELECT source FROM imports WHERE id = ? AND account_id = ?", (import_id, account_id)).fetchone()
        cur = conn.execute("DELETE FROM transactions WHERE account_id = ? AND import_id = ?",
                           (account_id, import_id))
        conn.execute("DELETE FROM payslips WHERE account_id = ? AND import_id = ?", (account_id, import_id))
        conn.execute("DELETE FROM imports WHERE id = ? AND account_id = ?", (import_id, account_id))
        if src and (src["source"] or "").startswith("financial_planner"):
            last = conn.execute("SELECT MAX(txn_date) AS d FROM transactions WHERE account_id = ? "
                                "AND source LIKE 'financial_planner%'", (account_id,)).fetchone()["d"]
            conn.execute("UPDATE accounts SET ledger_until = ? WHERE id = ?", (last, account_id))
        return cur.rowcount


def recent_imports(account_id: int, limit: int = 8) -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT i.*, (SELECT COUNT(*) FROM transactions t WHERE t.import_id = i.id) AS still "
            "FROM imports i WHERE i.account_id = ? ORDER BY i.id DESC LIMIT ?", (account_id, limit))]


# Id prefixes under which a row is recognised by its id wherever it
# comes from — this app's own shape for Trade Republic, Saxo, Kraken
# and Crédit Agricole rows, which the move from Financial Planner
# reproduces exactly. A row so marked needs no date cut-off to be
# told from a duplicate, and a cut-off must not stop it: the account
# a wallet's history moved into on the 14th still has to receive the
# withdrawal Kraken made that afternoon.
SHARED_ID_PREFIXES = ("fp:", "tr:", "saxo:", "kraken:", "ca-ch:")


def sources(account_id: int) -> list[dict]:
    """Where an account's rows came from: one line per source, with the
    count and the span. What the account page shows beside the offer
    to move a source's rows elsewhere."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT COALESCE(source, '') AS source, COUNT(*) AS rows, MIN(txn_date) AS first, MAX(txn_date) AS last "
            "FROM transactions WHERE account_id = ? GROUP BY COALESCE(source, '') ORDER BY MIN(txn_date)",
            (account_id,))]


def move_rows(account_id: int, source: str, to_account_id: int) -> int:
    """Every row a source brought into this account goes to another.

    For the account that was two things at once — the rows of a wallet
    moved in from another app landing in the account an exchange is
    linked to — so that each account holds what it physically holds
    and a sync's balance check can mean something. The rows keep their
    ids, so nothing is imported twice afterwards. Returns how many
    moved.
    """
    if to_account_id == account_id:
        return 0
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM accounts WHERE id = ?", (to_account_id,)).fetchone() is None:
            return 0
        cur = conn.execute(
            "UPDATE transactions SET account_id = ? WHERE account_id = ? AND COALESCE(source, '') = ?",
            (to_account_id, account_id, source))
        return cur.rowcount


def store(account_id: int, parsed: ParseResult, source: str, import_id: int | None = None) -> dict:
    """Write the parsed rows. Returns what actually happened.

    `INSERT OR IGNORE` against the unique index on `external_id` is the
    whole deduplication strategy, so re-importing last month's export on
    top of this month's is free and correct rather than something the
    user has to think about.
    """
    inserted = duplicates = on_record = kept_out = 0
    with get_conn() as conn:
        # Rows the account already has from elsewhere, under other ids
        # — see accounts.ledger_until. They count as duplicates, which
        # is what they are — and are counted apart, because "already
        # had" about rows the account visibly does not have is the
        # one message that sends someone looking in the wrong place.
        until = conn.execute("SELECT ledger_until FROM accounts WHERE id = ?",
                             (account_id,)).fetchone()
        until = until["ledger_until"] if until else None
        removed = {r["external_id"] for r in conn.execute("SELECT external_id FROM removed_rows")}
        for row in parsed.rows:
            if until and row.txn_date <= until and not (row.external_id or "").startswith(SHARED_ID_PREFIXES):
                duplicates += 1
                on_record += 1
                continue
            if row.external_id in removed:
                duplicates += 1           # the user removed it; it stays removed
                kept_out += 1
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
                if row.category:
                    conn.execute("UPDATE transactions SET category = ? WHERE id = ?",
                                 (row.category, cur.lastrowid))
            else:
                duplicates += 1
        if parsed.payslip:
            _save_payslip(conn, account_id, parsed.payslip, import_id)
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
            "on_record": on_record, "until": until, "kept_out": kept_out,
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
