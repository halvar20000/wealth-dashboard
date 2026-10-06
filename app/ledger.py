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


# ─── The same booking twice: the move-in's row and a reader's ────────

def _norm(text: str | None) -> str:
    """A description stripped to what two apps can agree on."""
    import re as _re
    return " ".join(_re.sub(r"[^\w\s]", " ", (text or "").lower()).split())


def _same_booking(a: str | None, b: str | None) -> bool:
    """Whether two descriptions are the same booking's.

    The two apps read the same statement line and keep slightly
    different texts of it — one truncates, one adds the reference. So:
    the same words, or one text beginning the other, or most of the
    words in common.
    """
    x, y = _norm(a), _norm(b)
    if not x or not y:
        return True                     # one side says nothing: the figures decide
    if x == y or x.startswith(y[:24]) or y.startswith(x[:24]):
        return True
    xs, ys = set(x.split()), set(y.split())
    return bool(xs & ys) and len(xs & ys) / len(xs | ys) >= 0.6


def _richer(a: dict, b: dict) -> tuple[dict, dict]:
    """(the row to keep, the row to drop).

    The units decide first: a trade booked with its quantity is worth
    more than the same money booked as a plain withdrawal, and deleting
    the one that carries the units would empty the position. Otherwise
    the move-in's copy is the one that goes, because the reader's row
    carries the counterparty and the category this app assigns.
    """
    a_units = a["quantity"] is not None
    b_units = b["quantity"] is not None
    if a_units != b_units:
        return (a, b) if a_units else (b, a)
    a_fp = (a["source"] or "").startswith("financial_planner")
    return (b, a) if a_fp else (a, b)


def heal_moved_twins(account_id: int | None = None, path=None) -> int:
    """The move-in's copy of a booking a reader has booked again.

    `heal_twins` pairs the bank sync's bare rows, `heal_trade_twins` the
    trades by their units; between them sits everything else a broker's
    statement carries — a dividend, the tax withheld on it, a cash
    sweep, a currency conversion. Where the move-in brought those and a
    statement import later brought the same ones, both sit in the
    ledger: every single amount looks right and every sum is double.

    What makes two rows the same booking is the account, the currency,
    the amount to the cent, the day (one apart at most) and the text.
    The *kind* and the *security* deliberately do not: they are the two
    apps' readings of the booking, and they are precisely what differs
    — one calls a conversion `other`, the other `transfer`; one knows
    the ISIN, the other does not. Requiring them to agree left 469 of
    a user's 966 doubled rows standing.

    One copy goes, one to one. Which one is in `_richer`: never the one
    that carries the units. What the loser knew and the keeper does not
    — a category, a counterparty, an ISIN — moves across first, and the
    removal is remembered so a second move-in cannot undo it.
    """
    only = " AND account_id = ?" if account_id is not None else ""
    params = [account_id] if account_id is not None else []
    columns = ("id, account_id, txn_date, amount, currency, kind, isin, quantity, "
               "category, counterparty, description, source, external_id")
    gone = 0
    with get_conn(path) as conn:
        pool: dict[tuple, list] = {}
        for r in conn.execute(
                f"SELECT {columns} FROM transactions "
                f"WHERE (source IS NULL OR source NOT LIKE 'financial_planner%'){only} "
                f"AND id NOT IN (SELECT kept_id FROM twin_claims)", params):
            pool.setdefault((r["account_id"], round(r["amount"], 2), r["currency"]), []).append(dict(r))
        if not pool:
            return 0
        for f in conn.execute(
                f"SELECT {columns} FROM transactions "
                f"WHERE source LIKE 'financial_planner%'{only} ORDER BY txn_date, id", params).fetchall():
            mates = pool.get((f["account_id"], round(f["amount"], 2), f["currency"]))
            if not mates:
                continue
            day = date.fromisoformat(f["txn_date"])
            near = [m for m in mates
                    if abs((date.fromisoformat(m["txn_date"]) - day).days) <= 1
                    and _same_booking(m["description"], f["description"])]
            if not near:
                continue
            twin = min(near, key=lambda m: abs((date.fromisoformat(m["txn_date"]) - day).days))
            mates.remove(twin)
            keep, drop = _richer(dict(f), twin)
            for field in ("category", "counterparty", "isin", "security_name"):
                if field == "security_name":
                    continue
                if drop.get(field) and not keep.get(field):
                    conn.execute(f"UPDATE transactions SET {field} = ? WHERE id = ?",
                                 (drop[field], keep["id"]))
            if drop["external_id"]:
                conn.execute("INSERT OR IGNORE INTO removed_rows (external_id, account_id) VALUES (?, ?)",
                             (drop["external_id"], drop["account_id"]))
                conn.execute("INSERT OR IGNORE INTO twin_claims (kept_id, removed_external_id) VALUES (?, ?)",
                             (keep["id"], drop["external_id"]))
            conn.execute("DELETE FROM transactions WHERE id = ?", (drop["id"],))
            gone += 1
    return gone


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
