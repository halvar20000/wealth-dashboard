"""The same booking twice, under two ids — and which copy goes.

A bank account's rows can arrive by two roads: the bank connection
(`banks.sync`, ids `eb:…`, no source, no category) and a move-in from
Financial Planner or a file import (a source, and often a kind, a
category and a counterparty already). `accounts.ledger_until` keeps
the sync from booking the span another road already covered — but
only from then on. Where the sync ran *first* and the move-in came
later, both copies sit in the ledger, and every sum over it is
doubled while every single amount looks right, which is the worst
kind of wrong.

This pairs the sync's bare rows with the other road's rows one to
one — same account, same amount and currency, a day apart at most —
and deletes the bare twin. The enriched copy is the one kept: it
carries the kind, the category and the counterparty; the bare one
carries nothing the pair does not have twice. A category or a
counterparty the bare row did pick up in the meantime goes onto the
survivor first. The twin's id is remembered in `removed_rows`, so a
later sync cannot bring it back.
"""

from __future__ import annotations

from datetime import date, timedelta

from .db import get_conn

# The road whose copies are the ones to drop, and the roads whose
# copies are kept. A manual entry is neither: a row typed by hand
# that happens to match a bank row is the user's to reconcile.
_BARE = "source IS NULL AND external_id LIKE 'eb:%'"
_KEPT = "source IS NOT NULL AND source != 'manual'"


def _pairs(conn, account_id: int | None) -> list[tuple[dict, dict]]:
    """(bare row, its enriched twin), one to one: each enriched row
    claims at most one bare row in its life — `twin_claims` remembers
    a claim across passes — and takes the nearest by day among those
    of its account, amount and currency, a day apart at most."""
    only = " AND account_id = ?" if account_id is not None else ""
    params = [account_id] if account_id is not None else []
    kept = conn.execute(
        f"SELECT id, account_id, txn_date, amount, currency, category, counterparty FROM transactions "
        f"WHERE {_KEPT}{only} AND id NOT IN (SELECT kept_id FROM twin_claims)", params).fetchall()
    if not kept:
        return []
    pool: dict[tuple, list] = {}
    for r in kept:
        pool.setdefault((r["account_id"], round(r["amount"], 2), r["currency"]), []).append(dict(r))
    bare = conn.execute(
        f"SELECT id, account_id, txn_date, amount, currency, category, counterparty, external_id "
        f"FROM transactions WHERE {_BARE}{only} ORDER BY txn_date, id", params).fetchall()
    pairs = []
    for b in bare:
        mates = pool.get((b["account_id"], round(b["amount"], 2), b["currency"]))
        if not mates:
            continue
        day = date.fromisoformat(b["txn_date"])
        near = [m for m in mates if abs((date.fromisoformat(m["txn_date"]) - day).days) <= 1]
        if not near:
            continue
        twin = min(near, key=lambda m: abs((date.fromisoformat(m["txn_date"]) - day).days))
        mates.remove(twin)
        pairs.append((dict(b), twin))
    return pairs


def heal_twins(account_id: int | None = None, path=None) -> int:
    """Delete every bare sync row that has an enriched twin; returns
    how many went. All accounts when none is given."""
    gone = 0
    with get_conn(path) as conn:
        for b, twin in _pairs(conn, account_id):
            if b["category"] and not twin["category"]:
                conn.execute("UPDATE transactions SET category = ? WHERE id = ?", (b["category"], twin["id"]))
            if b["counterparty"] and not twin["counterparty"]:
                conn.execute("UPDATE transactions SET counterparty = ? WHERE id = ?", (b["counterparty"], twin["id"]))
            conn.execute("INSERT OR IGNORE INTO removed_rows (external_id, account_id) VALUES (?, ?)",
                         (b["external_id"], b["account_id"]))
            conn.execute("INSERT OR IGNORE INTO twin_claims (kept_id, removed_external_id) VALUES (?, ?)",
                         (twin["id"], b["external_id"]))
            conn.execute("DELETE FROM transactions WHERE id = ?", (b["id"],))
            gone += 1
    return gone


def doubled(account_id: int | None = None) -> dict:
    """How many bare sync rows have an enriched twin, per account — the
    diagnosis, nothing deleted."""
    out: dict[int, int] = {}
    with get_conn() as conn:
        for b, _ in _pairs(conn, account_id):
            out[b["account_id"]] = out.get(b["account_id"], 0) + 1
    return out


# ─── The same trade twice: a reader's row and the move-in's ──────────

def heal_trade_twins(account_id: int | None = None, path=None) -> dict:
    """A trade this app's reader booked and the move-in booked again
    under the old app's id — same account, security and units, a day
    apart at most, the amount within a percent — and the opening
    position the move-in wrote to make the units add up, which counted
    the pair twice and so is short by the twin.

    The old app's copy goes (the reader's carries the fee and the tax
    as this app books them); the opening is corrected by what went, or
    by the reader's buy it plainly negates where the copy was removed
    by hand before this ran; an opening left at nothing goes too.
    Returns {"twins": n, "openings": n}.
    """
    only = " AND account_id = ?" if account_id is not None else ""
    params = [account_id] if account_id is not None else []
    gone = {"twins": 0, "openings": 0}
    with get_conn(path) as conn:
        readers = {}
        for r in conn.execute(
                f"SELECT id, account_id, txn_date, isin, quantity, amount FROM transactions "
                f"WHERE kind IN ('buy', 'sell') AND isin IS NOT NULL AND quantity IS NOT NULL "
                f"AND (source IS NULL OR source NOT LIKE 'financial_planner%'){only}", params):
            readers.setdefault((r["account_id"], r["isin"]), []).append(dict(r))
        taken: dict[tuple, float] = {}
        for f in conn.execute(
                f"SELECT id, account_id, txn_date, isin, quantity, amount FROM transactions "
                f"WHERE kind IN ('buy', 'sell') AND isin IS NOT NULL AND quantity IS NOT NULL "
                f"AND source LIKE 'financial_planner%'{only} ORDER BY txn_date, id", params).fetchall():
            key = (f["account_id"], f["isin"])
            day = date.fromisoformat(f["txn_date"])
            for i, r in enumerate(readers.get(key, [])):
                if abs(r["quantity"] - f["quantity"]) < 1e-6 \
                        and abs((date.fromisoformat(r["txn_date"]) - day).days) <= 1 \
                        and abs(abs(r["amount"]) - abs(f["amount"])) <= 0.01 * max(abs(f["amount"]), 1.0) + 0.05:
                    readers[key].pop(i)
                    conn.execute("DELETE FROM transactions WHERE id = ?", (f["id"],))
                    taken[key] = taken.get(key, 0.0) + f["quantity"]
                    gone["twins"] += 1
                    break
        for o in conn.execute(
                f"SELECT id, account_id, txn_date, isin, quantity FROM transactions "
                f"WHERE external_id LIKE 'fp:open:%' AND quantity < 0{only}", params).fetchall():
            key = (o["account_id"], o["isin"])
            new_q = o["quantity"] + taken.get(key, 0.0)
            if abs(new_q) < 1e-6:
                conn.execute("DELETE FROM transactions WHERE id = ?", (o["id"],))
                gone["openings"] += 1
                continue
            if key not in taken:
                # The copy was removed by hand already: the opening still
                # negates the reader's buy of the very next day exactly.
                day = date.fromisoformat(o["txn_date"])
                negated = conn.execute(
                    "SELECT 1 FROM transactions WHERE account_id = ? AND isin = ? AND kind = 'buy' "
                    "AND abs(quantity + ?) < 1e-6 AND txn_date BETWEEN ? AND ? "
                    "AND (source IS NULL OR source NOT LIKE 'financial_planner%')",
                    (o["account_id"], o["isin"], o["quantity"], o["txn_date"], (day + timedelta(days=1)).isoformat())).fetchone()
                if negated:
                    conn.execute("DELETE FROM transactions WHERE id = ?", (o["id"],))
                    gone["openings"] += 1
                continue
            conn.execute("UPDATE transactions SET quantity = ? WHERE id = ?", (new_q, o["id"]))
            gone["openings"] += 1
    return gone
