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

def _key(date: str, isin: str | None, quantity: float | None, amount: float, kind: str, description: str) -> tuple:
    """What makes two rows the same booking when their ids differ: a
    trade by day, security, units and money; a credit by day, kind and
    money; a payment out also by its text, since two coffees on one
    day at one price are two coffees."""
    if isin:
        return ("sec", date, isin, round(abs(quantity or 0.0), 4), round(abs(amount), 2), amount < 0)
    if kind == "withdrawal":
        return ("out", date, round(amount, 2), " ".join((description or "").lower().split()))
    return ("cash", date, kind, round(amount, 2))


def dedupe_against_account(account_id: int, source: str, parsed) -> int:
    """Rows a sync brings that the account already holds under other
    ids — from a CSV, a statement PDF, a move-in — are the same
    bookings and are dropped; rows this source stored earlier that
    duplicate such a row are deleted, so an account that was doubled
    once heals on the next sync. Returns how many rows were dropped."""
    with get_conn() as conn:
        others = conn.execute(
            "SELECT txn_date, isin, quantity, amount, kind, description FROM transactions "
            "WHERE account_id = ? AND COALESCE(source, '') != ?", (account_id, source)).fetchall()
        held = {_key(r["txn_date"], r["isin"], r["quantity"], r["amount"], r["kind"], r["description"]) for r in others}
        if held:
            mine = conn.execute(
                "SELECT id, txn_date, isin, quantity, amount, kind, description FROM transactions "
                "WHERE account_id = ? AND source = ?", (account_id, source)).fetchall()
            doubled = [r["id"] for r in mine
                       if _key(r["txn_date"], r["isin"], r["quantity"], r["amount"], r["kind"], r["description"]) in held]
            for i in range(0, len(doubled), 500):
                chunk = doubled[i:i + 500]
                conn.execute(f"DELETE FROM transactions WHERE id IN ({','.join('?' * len(chunk))})", chunk)
    seen: set = set()
    kept, dropped = [], 0
    for row in parsed.rows:
        k = _key(row.txn_date, row.isin, row.quantity, row.amount, row.kind, row.description)
        if k in held or k in seen:
            dropped += 1
            continue
        seen.add(k)
        kept.append(row)
    parsed.rows = kept
    return dropped
