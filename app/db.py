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
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    -- What kind of event this is: deposit, withdrawal, buy, sell,
    -- dividend, interest, fee, tax, transfer, other. A bank statement is
    -- almost all deposit/withdrawal; a broker statement is mostly the
    -- rest, and telling them apart is what makes a holding computable.
    kind         TEXT NOT NULL DEFAULT 'other',
    -- Set only on rows that concern a security. `isin` is the join key
    -- across brokers: Degiro gives it in its own column and Trade
    -- Republic puts it in one called `symbol`.
    -- Assigned by a rule or by hand. Separate from `kind`: kind is what
    -- the broker or bank called the event, category is what it means to
    -- the household. A card payment is one kind and a dozen categories.
    category     TEXT,
    isin          TEXT,
    security_name TEXT,
    quantity      REAL,
    price         REAL,
    fee           REAL,
    tax           REAL,
    -- Which importer produced the row. Worth keeping: when a broker
    -- changes its export format, the first question is which rows came
    -- from the old parser.
    source       TEXT
);
-- A correction the user made, kept as a rule so it applies to what is
-- already imported as well as to what arrives next. Plain substrings,
-- not regexes: a rule nobody can read is a rule nobody can correct.
CREATE TABLE IF NOT EXISTS category_rules (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern    TEXT NOT NULL,
    category   TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- The user's own categories, and their edits to the built-in ones. A
-- row here either overrides a built-in — a new name, a new colour, or
-- `hidden` for one they removed — or is a category they invented. The
-- built-in list stays in categories.py: this table is only the delta, so
-- a category the user never touched picks up a better default colour
-- when the app ships one.
CREATE TABLE IF NOT EXISTS categories (
    slug       TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    colour     TEXT NOT NULL,
    -- 'spending' or 'non_spending'. Non-spending is what keeps moving
    -- your own money from being counted as spending it.
    cat_group  TEXT NOT NULL DEFAULT 'spending',
    hidden     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Machine-written state, as opposed to settings.json, which is the
-- user's. "When did we last ask the ECB" belongs nowhere near a file
-- somebody edits by hand — and the next thing to need this is the price
-- feed, which will have exactly the same question.
CREATE TABLE IF NOT EXISTS app_state (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ECB euro foreign exchange reference rates: one row per currency per
-- publication day, holding what one euro buys. That is the direction
-- the ECB publishes in, and storing it in any other direction means
-- deciding how to round a reciprocal before anybody has asked a
-- question.
--
-- Rows are kept rather than replaced. A rate is a fact about a day, the
-- day does not change, and the history is what a balance chart will
-- need the moment there is one.
CREATE TABLE IF NOT EXISTS fx_rates (
    as_of    TEXT NOT NULL,       -- the ECB publication date, ISO
    currency TEXT NOT NULL,       -- ISO 4217, never EUR: EUR is the unit
    per_eur  REAL NOT NULL,       -- 1 EUR buys this much of `currency`
    PRIMARY KEY (as_of, currency)
);

-- One row per security the app has tried to price. `symbol` is the
-- ticker the price source knows it by, which a broker export never
-- gives — an ISIN is the same everywhere, a ticker is per exchange —
-- so it is looked up once and kept. `symbol_source` says whether the
-- user typed it in, in which case no lookup ever replaces it.
CREATE TABLE IF NOT EXISTS securities (
    isin          TEXT PRIMARY KEY,
    symbol        TEXT,
    name          TEXT,
    symbol_source TEXT,             -- 'yahoo' or 'manual'
    resolved_at   TEXT,
    last_error    TEXT,
    -- What Yahoo says the symbol is: EQUITY, ETF, MUTUALFUND. Read off
    -- the same chart reply the price comes from, and what lets the
    -- share-ideas boards put a held ETF on the ETF board and a held
    -- share on the share board without asking anybody.
    quote_type    TEXT
);

-- Kept, not replaced: a price is a fact about a day, and the history
-- is what "why did it move" will need once there is enough of it.
CREATE TABLE IF NOT EXISTS prices (
    isin       TEXT NOT NULL,
    as_of      TEXT NOT NULL,       -- the trading day, ISO
    price      REAL NOT NULL,
    currency   TEXT NOT NULL,       -- the currency the exchange quotes in
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (isin, as_of)
);

-- What the user budgeted for a category, per month. One row per
-- category; a month with no row simply has no budget.
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    monthly  REAL NOT NULL
);

-- The people in the household, and which accounts are whose. An
-- account can belong to one person, to several (a joint account) or to
-- nobody yet. Nothing about the account itself changes: a person is a
-- lens, not a permission. The header's switch picks one, and every page
-- then adds up only that person's accounts — or everybody's.
CREATE TABLE IF NOT EXISTS people (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    birthday   TEXT,                 -- ISO date; what a retirement age is measured from
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS account_people (
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    person_id  INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    PRIMARY KEY (account_id, person_id)
);

CREATE TABLE IF NOT EXISTS balances (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    amount       REAL NOT NULL,
    currency     TEXT NOT NULL,
    balance_type TEXT,
    as_of        TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Share Ideas: a nightly cache of Yahoo fundamentals, one row per share
-- in the screening universe. Scores are NOT stored — they are pure
-- arithmetic over these columns and are recomputed on every request, so
-- a tuned threshold takes effect on reload rather than at the next
-- refresh. A failed fetch keeps the old row and stamps `last_error`:
-- a Yahoo hiccup must make a name visibly stale, never make it vanish.
-- Every rate is a FRACTION (0.034) and every ratio a RATIO, whatever
-- unit Yahoo happened to report it in — see screener.normalise().
CREATE TABLE IF NOT EXISTS screener_fundamentals (
    symbol                 TEXT PRIMARY KEY,
    name                   TEXT,
    sector                 TEXT,
    industry               TEXT,
    country                TEXT,
    exchange               TEXT,
    currency               TEXT,
    quote_type             TEXT,
    price                  REAL,
    market_cap             REAL,
    trailing_pe            REAL,
    forward_pe             REAL,
    price_to_book          REAL,
    dividend_yield         REAL,
    payout_ratio           REAL,
    div_yield_5y_avg       REAL,
    return_on_equity       REAL,
    operating_margin       REAL,
    profit_margin          REAL,
    debt_to_equity         REAL,
    current_ratio          REAL,
    revenue_growth         REAL,
    earnings_growth        REAL,
    beta                   REAL,
    week52_high            REAL,
    week52_low             REAL,
    -- The income board's inputs. dividend_rate is the FORWARD annual
    -- dividend, trailing_dividend_rate the last twelve months' actual;
    -- their ratio is the only dividend-growth signal Yahoo gives without
    -- a second request. free_cashflow and shares_outstanding give the
    -- cash payout, which catches a dividend that earnings flatter.
    dividend_rate          REAL,
    trailing_dividend_rate REAL,
    free_cashflow          REAL,
    shares_outstanding     REAL,
    fetched_at             TEXT,
    last_error             TEXT
);

-- The ETF half of Share Ideas. An ETF shares almost nothing with a
-- share: no ROE, no payout ratio, no P/E, and the one figure that
-- decides it — the TER — is curated in the universe rather than fetched,
-- because Yahoo has none for most European listings. Growth is COMPUTED
-- from the adjusted price history, in EUR; the yield from the
-- distributions actually paid. `fetch_rev` says which revision of the
-- fetch wrote the row, so a column added later is refetched rather than
-- sitting NULL behind a recent `fetched_at`.
CREATE TABLE IF NOT EXISTS screener_etfs (
    symbol           TEXT PRIMARY KEY,
    name             TEXT,
    category         TEXT,
    family           TEXT,
    currency         TEXT,
    exchange         TEXT,
    quote_type       TEXT,
    price            REAL,
    total_assets     REAL,
    yahoo_ter        REAL,           -- fraction, when Yahoo has one at all
    dividend_yield   REAL,           -- Yahoo's own, kept as a cross-check
    cagr_1y          REAL,           -- computed in EUR, total return
    cagr_3y          REAL,
    cagr_5y          REAL,
    volatility_1y    REAL,           -- annualised stdev of weekly log returns
    max_drawdown     REAL,           -- worst peak-to-trough over the series
    history_years    REAL,
    history_start    TEXT,
    history_end      TEXT,
    week52_high      REAL,
    week52_low       REAL,
    div_ttm          REAL,           -- distributions paid, last 365 days
    div_prior        REAL,           -- the 365 days before that
    div_yield_ttm    REAL,           -- div_ttm / listing price
    div_growth       REAL,           -- div_ttm / div_prior - 1
    div_worst_cut    REAL,           -- worst year-on-year fall on record
    div_events_12m   INTEGER,        -- payment frequency
    div_events_prior INTEGER,
    div_years        REAL,
    div_last_date    TEXT,
    fetch_rev        INTEGER,
    fetched_at       TEXT,
    last_error       TEXT
);

-- Starred and dismissed, keyed on the bare symbol so one list serves all
-- four boards: starring an ETF and starring a share are the same act.
CREATE TABLE IF NOT EXISTS screener_watchlist (
    symbol   TEXT PRIMARY KEY,
    status   TEXT NOT NULL DEFAULT 'watch',   -- watch | dismissed
    note     TEXT,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Indexes live apart from the tables, and the separation is not tidiness.
# `CREATE TABLE IF NOT EXISTS` is a no-op on a database an older version
# already made, so that database still has the old columns — and an index
# naming a new one fails with `no such column`, before the migration that
# would have added it has had a chance to run. Tables, then columns, then
# indexes. In that order it works on a fresh database and an upgraded one
# alike.
INDEXES = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_bank_links_uid
    ON bank_links(account_uid) WHERE account_uid IS NOT NULL;

-- Re-importing an overlapping window is the normal case, not the
-- exception: every sync asks the bank for the longest history it will
-- serve, and a broker export is chosen by hand. The unique id is what
-- makes that harmless instead of doubling every balance.
CREATE UNIQUE INDEX IF NOT EXISTS idx_txn_external
    ON transactions(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_txn_account_date
    ON transactions(account_id, txn_date);
CREATE INDEX IF NOT EXISTS idx_txn_isin
    ON transactions(account_id, isin) WHERE isin IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category, txn_date);

CREATE INDEX IF NOT EXISTS idx_balances_account
    ON balances(account_id, as_of DESC);

-- Every conversion asks the same question: the newest publication day
-- at or before some date.
CREATE INDEX IF NOT EXISTS idx_fx_as_of ON fx_rates(as_of DESC);
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
        conn.executescript(SCHEMA)          # tables
        _add_missing_columns(conn)          # columns an older version lacks
        conn.executescript(INDEXES)         # only now can they be indexed
        conn.commit()
    finally:
        conn.close()
    return path


# Columns added after v0.1 shipped. CREATE TABLE IF NOT EXISTS is a no-op
# on a table that already exists, so a database made by an earlier
# version would keep the old shape and every query naming a new column
# would fail — with an error about a missing column, not about a version.
# Adding them here means upgrading is starting the app, which is the only
# upgrade instruction anyone follows.
_ADDED_COLUMNS = {
    "people": [
        ("birthday", "TEXT"),
    ],
    "securities": [
        ("quote_type", "TEXT"),
    ],
    "transactions": [
        ("kind", "TEXT NOT NULL DEFAULT 'other'"),
        ("isin", "TEXT"),
        ("security_name", "TEXT"),
        ("quantity", "REAL"),
        ("price", "REAL"),
        ("fee", "REAL"),
        ("tax", "REAL"),
        ("source", "TEXT"),
        ("category", "TEXT"),
    ],
}


def _add_missing_columns(conn: sqlite3.Connection) -> None:
    for table, columns in _ADDED_COLUMNS.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for name, decl in columns:
            if name not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


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


def get_state(key: str) -> str | None:
    """Read a machine-written value. See the app_state table."""
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM app_state WHERE key = ?",
                           (key,)).fetchone()
    return row["value"] if row else None


def set_state(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO app_state (key, value, updated_at) "
            "VALUES (?, ?, datetime('now')) ON CONFLICT(key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at",
            (key, value))


def has_users() -> bool:
    """False until the first-run form has been completed."""
    if not settings.DB_PATH.exists():
        return False
    try:
        with get_conn() as conn:
            return conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
    except sqlite3.Error:
        return False
