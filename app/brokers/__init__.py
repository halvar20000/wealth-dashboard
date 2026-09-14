"""Brokers connected by API, and the table that records the connection.

Two so far, and they could not be more different in how you get in:

  * **Kraken** — an API key you create once, with read-only rights, and
    paste into Settings. Requests are signed with it; nothing expires.
  * **Saxo** — OAuth2 with tokens that die in minutes and a refresh
    token that is single-use and dies in an hour. The app keeps the
    chain alive on a thread and asks you to log in again when it
    cannot.

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

PROVIDERS = ("saxo", "kraken")


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


def record(link_id: int, error: str | None) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_conn() as conn:
        if error is None:
            conn.execute("UPDATE broker_links SET last_sync_at = ?, last_error = NULL "
                         "WHERE id = ?", (now, link_id))
        else:
            conn.execute("UPDATE broker_links SET last_error = ? WHERE id = ?",
                         (error[:400], link_id))


def sync_link(link: dict) -> dict:
    """{account, inserted, error} for one link, whichever provider."""
    from . import kraken, saxo
    module = {"saxo": saxo, "kraken": kraken}[link["provider"]]
    try:
        inserted = module.sync_link(link)
        record(link["id"], None)
        result = {"account": link["account"], "provider": link["provider"],
                  "inserted": inserted, "error": None}
    except Exception as exc:                          # noqa: BLE001
        record(link["id"], str(exc))
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
