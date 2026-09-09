"""The database: one SQLite file, created on first run.

Six tables, and the shape of two of them is the whole design:

`accounts` is what the USER made — a name, a type, a currency. It exists
whether or not a bank is ever connected, because plenty of accounts have
no API and never will, and an app that can only hold connected accounts
cannot hold a whole net worth.

`bank_links` is the connection, and it is a SEPARATE row pointing at an
account. A bank consent expires every 90 days under PSD2; when it does,
the link dies and the account, its history and its balance do not. If the
connection lived on the account row, re-authorising would mean editing
the account, and a failed re-auth would put the account itself in a
broken state.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    rounds        INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL DEFAULT 'bank',
    currency   TEXT NOT NULL DEFAULT 'EUR',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per connected bank account. `account_uid` is Enable Banking's
-- handle for it; `identification_hash` is the bank's own stable id and
-- is what transaction ids are namespaced by, so two accounts at the same
-- bank can never collide.
CREATE TABLE IF NOT EXISTS bank_links (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    provider            TEXT NOT NULL DEFAULT 'enablebanking',
    aspsp_name          TEXT NOT NULL,
    aspsp_country       TEXT NOT NULL,
    session_id          TEXT,
    account_uid         TEXT,
    identification_hash TEXT,
    iban                TEXT,
    valid_until         TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    last_sync_at        TEXT,
    last_error          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bank_links_uid
    ON bank_links(account_uid) WHERE account_uid IS NOT NULL;

-- The pending half of an OAuth redirect. The user leaves for the bank
-- and comes back to a fresh request with nothing but ?code and ?state,
-- so what we were doing has to be written down before they go.
CREATE TABLE IF NOT EXISTS auth_states (
    state         TEXT PRIMARY KEY,
    account_id    INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    aspsp_name    TEXT NOT NULL,
    aspsp_country TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    txn_date     TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    counterparty TEXT,
    amount       REAL NOT NULL,
    currency     TEXT NOT NULL,
    external_id  TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Re-importing an overlapping window is the normal case, not the
-- exception: every sync asks the bank for the longest history it will
-- serve. The unique id is what makes that harmless instead of doubling
-- every balance.
CREATE UNIQUE INDEX IF NOT EXISTS idx_txn_external
    ON transactions(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_txn_account_date
    ON transactions(account_id, txn_date);

CREATE TABLE IF NOT EXISTS balances (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount       REAL NOT NULL,
    currency     TEXT NOT NULL,
    balance_type TEXT,
    as_of        TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_balances_account
    ON balances(account_id, as_of DESC);
"""


def init_db(path: Path | None = None) -> Path:
    settings.ensure_dirs()
    path = path or settings.DB_PATH
    conn = sqlite3.connect(path, timeout=5)
    try:
        # WAL: a read (the dashboard) and a write (a sync) happen at the
        # same time the moment anything runs on a schedule.
        #
        # Switching journal mode needs the database to itself, so this is
        # where a second instance pointed at the same file shows up. The
        # bare sqlite error for that is "database is locked", which sends
        # the reader looking for a stuck query instead of the other copy
        # of the app they forgot they started.
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                raise RuntimeError(
                    f"{path} is already in use. Another instance of the app "
                    f"is probably running against it — SQLite allows one "
                    f"writer, and two copies will corrupt the file. Stop the "
                    f"other one, or point this one at a different WD_DATA_DIR."
                ) from exc
            raise
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return path


@contextmanager
def get_conn(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path or settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def has_users() -> bool:
    """False until the first-run form has been completed."""
    if not settings.DB_PATH.exists():
        return False
    try:
        with get_conn() as conn:
            return conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
    except sqlite3.Error:
        return False
