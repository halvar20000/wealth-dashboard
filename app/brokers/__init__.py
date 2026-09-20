"""Brokers connected by API, and the table that records the connection.

Five, in three ways of getting in:

  * **Kraken** — an API key you create once, with read-only rights, and
    paste into Settings. Requests are signed with it; nothing expires.
  * **Saxo** — OAuth2 with tokens that die in minutes and a refresh
    token that is single-use and dies in an hour. The app keeps the
    chain alive on a thread and asks you to log in again when it
    cannot.
  * **Interactive Brokers** and **Trading 212** — like Kraken, a token
    or key pair made once, read-only, pasted into Settings.
  * **Trade Republic** — no API at all: the web app's own login (phone,
    PIN, the app's approval) and its WebSocket, unofficial and liable
    to break; the session cookies are kept until Trade Republic ends
    them.

What both share is `broker_links`: one row per connected sub-account,
pointing at an account the user made, so that a lapsed connection
never takes the account and its history with it — the same shape as a
bank link, for the same reason. Each provider module has `sync_link()`
and `describe()`, and `sync_all()` here runs every link the way the
daily bank sync does.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..db import get_conn

PROVIDERS = ("saxo", "kraken", "ibkr", "trading212", "traderepublic")
LABELS = {"saxo": "Saxo Bank", "kraken": "Kraken", "ibkr": "Interactive Brokers",
          "trading212": "Trading 212", "traderepublic": "Trade Republic"}


def links(account_id: int | None = None) -> list[dict]:
    with get_conn() as conn:
        if account_id is None:
            rows = conn.execute(
                "SELECT bl.*, a.name AS account, a.currency AS account_currency "
                "FROM broker_links bl JOIN accounts a ON a.id = bl.account_id "
                "ORDER BY bl.provider, a.name").fetchall()
        else:
            rows = conn.execute(
                "SELECT bl.*, a.name AS account, a.currency AS account_currency "
                "FROM broker_links bl JOIN accounts a ON a.id = bl.account_id "
                "WHERE bl.account_id = ?", (account_id,)).fetchall()
    return [dict(r) for r in rows]


def link_for(account_id: int) -> dict | None:
    found = links(account_id)
    return found[0] if found else None


def add_link(account_id: int, provider: str, remote_id: str | None = None,
             remote_label: str | None = None, currency: str | None = None) -> int:
    with get_conn() as conn:
        if remote_id:
            row = conn.execute("SELECT id FROM broker_links WHERE provider = ? AND remote_id = ?",
                               (provider, remote_id)).fetchone()
            if row:
                conn.execute("UPDATE broker_links SET account_id = ?, remote_label = ?, "
                             "currency = ?, last_error = NULL WHERE id = ?",
                             (account_id, remote_label, currency, row["id"]))
                return int(row["id"])
        cur = conn.execute(
            "INSERT INTO broker_links (account_id, provider, remote_id, remote_label, currency) "
            "VALUES (?, ?, ?, ?, ?)", (account_id, provider, remote_id, remote_label, currency))
        return int(cur.lastrowid)


def remove_links(provider: str) -> int:
    with get_conn() as conn:
        return conn.execute("DELETE FROM broker_links WHERE provider = ?", (provider,)).rowcount


def record(link_id: int, error: str | None, synced: bool = False) -> None:
    """When it last ran, and what went wrong. `synced` says the rows
    were fetched and stored even though something after that failed —
    a balance that does not add up is a finding, not a failed sync,
    and "last sync: never" over a page of synced rows is a lie."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_conn() as conn:
        if error is None:
            conn.execute("UPDATE broker_links SET last_sync_at = ?, last_error = NULL "
                         "WHERE id = ?", (now, link_id))
        elif synced:
            conn.execute("UPDATE broker_links SET last_sync_at = ?, last_error = ? WHERE id = ?",
                         (now, error[:400], link_id))
        else:
            conn.execute("UPDATE broker_links SET last_error = ? WHERE id = ?",
                         (error[:400], link_id))


def sync_link(link: dict) -> dict:
    """{account, inserted, error} for one link, whichever provider."""
    from . import ibkr, kraken, saxo, traderepublic, trading212
    module = {"saxo": saxo, "kraken": kraken, "ibkr": ibkr, "trading212": trading212,
              "traderepublic": traderepublic}[link["provider"]]
    drift = (kraken.HoldingsDrift, ibkr.HoldingsDrift, trading212.HoldingsDrift, traderepublic.HoldingsDrift)
    try:
        inserted = module.sync_link(link)
        record(link["id"], None)
        result = {"account": link["account"], "provider": link["provider"],
                  "inserted": inserted, "error": None}
    except Exception as exc:                          # noqa: BLE001
        record(link["id"], str(exc), synced=isinstance(exc, drift))
        result = {"account": link["account"], "provider": link["provider"],
                  "inserted": 0, "error": str(exc)}
    try:
        from .. import webhooks
        webhooks.fire("sync.failed" if result["error"] else "sync.completed", dict(result))
    except Exception:                                 # noqa: BLE001
        pass
    return result


def sync_all() -> list[dict]:
    return [sync_link(link) for link in links()]


def set_wallet(link_id: int, wallet_account_id: int | None) -> None:
    """Where a coin goes when it leaves the exchange: one of the
    user's own accounts, or nowhere."""
    with get_conn() as conn:
        conn.execute("UPDATE broker_links SET wallet_account_id = ? WHERE id = ?",
                     (wallet_account_id, link_id))


# ─── A sync into an account that already has the history ────────────

def _same(a: dict, b: dict) -> bool:
    """Two rows with different ids that are the same booking. A trade:
    the security, the units, the direction, the day give or take one
    (the broker's timestamp is UTC, an export's date is local), and the
    money within what a fee explains — an export may carry the fee
    inside the total, a timeline beside it. A credit: day, kind and
    money. A payment out: also its text, since two coffees on one day
    at one price are two coffees."""
    try:
        days = abs((datetime.fromisoformat(a["txn_date"]) - datetime.fromisoformat(b["txn_date"])).days)
    except (TypeError, ValueError):
        return False
    if a["isin"] or b["isin"]:
        if a["isin"] != b["isin"] or days > 1 or (a["amount"] < 0) != (b["amount"] < 0):
            return False
        if abs(abs(a["quantity"] or 0.0) - abs(b["quantity"] or 0.0)) > 0.0006:
            return False
        slack = max(2.0, 0.02 * max(abs(a["amount"]), abs(b["amount"])), (a["fee"] or 0.0) + (b["fee"] or 0.0) + 0.05)
        return abs(abs(a["amount"]) - abs(b["amount"])) <= slack
    if a["kind"] != b["kind"] or days > 1 or abs(a["amount"] - b["amount"]) > 0.005:
        return False
    if a["kind"] == "withdrawal":
        return " ".join((a["description"] or "").lower().split()) == " ".join((b["description"] or "").lower().split())
    return True


def _facts(row) -> dict:
    if isinstance(row, dict):
        return row
    return {"txn_date": row.txn_date, "isin": row.isin, "quantity": row.quantity, "amount": row.amount,
            "kind": row.kind, "description": row.description, "fee": row.fee}


def dedupe_against_account(account_id: int, source: str, parsed) -> int:
    """Rows a sync brings that the account already holds under other
    ids — from a CSV, a statement PDF, a move-in — are the same
    bookings and are dropped; rows this source stored earlier that
    duplicate such a row are deleted, so an account that was doubled
    once heals on the next sync. Returns how many rows were dropped."""
    with get_conn() as conn:
        others = [dict(r) for r in conn.execute(
            "SELECT txn_date, isin, quantity, amount, kind, description, fee FROM transactions "
            "WHERE account_id = ? AND COALESCE(source, '') != ?", (account_id, source))]
        by_isin: dict = {}
        for r in others:
            by_isin.setdefault(r["isin"], []).append(r)
        if others:
            mine = [dict(r) for r in conn.execute(
                "SELECT id, txn_date, isin, quantity, amount, kind, description, fee FROM transactions "
                "WHERE account_id = ? AND source = ?", (account_id, source))]
            doubled = [r["id"] for r in mine if any(_same(r, o) for o in by_isin.get(r["isin"], []))]
            for i in range(0, len(doubled), 500):
                chunk = doubled[i:i + 500]
                conn.execute(f"DELETE FROM transactions WHERE id IN ({','.join('?' * len(chunk))})", chunk)
    kept: list = []
    kept_facts: list = []
    dropped = 0
    for row in parsed.rows:
        f = _facts(row)
        if any(_same(f, o) for o in by_isin.get(f["isin"], [])) or any(_same(f, k) for k in kept_facts if k["isin"] == f["isin"]):
            dropped += 1
            continue
        kept.append(row)
        kept_facts.append(f)
    parsed.rows = kept
    return dropped
