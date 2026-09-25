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
from datetime import datetime
from pathlib import Path
from typing import Iterator

from . import __version__, settings

# How many pre-upgrade copies of the database to keep, newest first. A
# rollback wants the last one; the rest are for the bug that only shows
# a week later.
KEEP_BACKUPS = 5

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
    source       TEXT,
    -- When the user corrected the row by hand. The correction survives
    -- a re-import — the row is recognised by its id and left alone —
    -- and the page says the figures are the user's, not the file's.
    edited_at    TEXT
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

-- A document archive (Paperless-ngx) the app pulls from — see
-- archive.py. One filter per account says which documents are its; one
-- row per document and account remembers what became of it, so a pull
-- lists once and imports nothing twice, and a document no reader
-- understood is on record by name rather than skipped in silence.
CREATE TABLE IF NOT EXISTS archive_filters (
    account_id    INTEGER PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    tags          TEXT NOT NULL DEFAULT '',
    correspondent TEXT NOT NULL DEFAULT '',
    query         TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS archive_documents (
    doc_id     INTEGER NOT NULL,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    title      TEXT,
    created    TEXT,
    seen_at    TEXT NOT NULL,
    result     TEXT NOT NULL,          -- imported | unread | failed
    note       TEXT,
    import_id  INTEGER,
    PRIMARY KEY (doc_id, account_id)
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

-- A broker connected by API — Saxo through OAuth, Kraken through a key —
-- as a separate row pointing at an account, for the same reason a bank
-- link is: the connection can lapse (a Saxo refresh chain breaks, a
-- Kraken key is revoked) and the account, its history and its balance
-- must not. `remote_id` is the broker's own handle for the sub-account
-- (Saxo's AccountKey; nothing for Kraken, which has one balance sheet
-- per key), so a client with several Saxo accounts gets several rows.
CREATE TABLE IF NOT EXISTS broker_links (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    provider     TEXT NOT NULL,           -- 'saxo' | 'kraken'
    remote_id    TEXT,
    remote_label TEXT,
    currency     TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_sync_at TEXT,
    last_error   TEXT
);

-- A loan's terms. The loan itself is an account of type `loan`, so it
-- belongs to people and carries a balance like any other; this row is
-- what lets that balance be computed rather than typed. See loans.py.
CREATE TABLE IF NOT EXISTS loans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
    principal     REAL NOT NULL,
    rate_pct      REAL NOT NULL DEFAULT 0,      -- nominal, per year
    first_payment TEXT NOT NULL,                -- ISO date of the first instalment
    period_months INTEGER NOT NULL DEFAULT 1,   -- 1 monthly, 3 quarterly, 6, 12
    payment       REAL,                         -- per period; NULL = from the term
    term_months   INTEGER,
    extras        TEXT,                         -- JSON [{date, amount}] lump sums
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Starred and dismissed, keyed on the bare symbol so one list serves all
-- four boards: starring an ETF and starring a share are the same act.
CREATE TABLE IF NOT EXISTS screener_watchlist (
    symbol   TEXT PRIMARY KEY,
    status   TEXT NOT NULL DEFAULT 'watch',   -- watch | dismissed
    note     TEXT,
    added_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- What a security is, for the allocation: an asset class, a region,
-- and a bucket of the user's own — "Core", "Satellite", "Play money".
-- Guessed once from the name and Yahoo's type, kept once typed. See
-- allocation.py.
CREATE TABLE IF NOT EXISTS security_classes (
    isin        TEXT PRIMARY KEY,
    asset_class TEXT,
    region      TEXT,
    bucket      TEXT,
    guessed     INTEGER NOT NULL DEFAULT 1,   -- 1 until a person set it
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- The target share of each class, region or bucket, in percent.
CREATE TABLE IF NOT EXISTS allocation_targets (
    dimension  TEXT NOT NULL,                 -- asset_class | region | bucket
    key        TEXT NOT NULL,
    target_pct REAL NOT NULL,
    PRIMARY KEY (dimension, key)
);

-- A bill: a payment expected on a rhythm — rent, insurance, the
-- electricity — declared by hand or adopted from a detected
-- subscription, matched against the rows as they arrive so the page
-- can say paid, due, or missed. See bills.py.
CREATE TABLE IF NOT EXISTS bills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    pattern     TEXT NOT NULL,                -- text in the counterparty or description
    amount      REAL,                         -- expected, unsigned; NULL = any
    currency    TEXT NOT NULL DEFAULT 'EUR',
    rhythm      TEXT NOT NULL DEFAULT 'monthly',
    due_day     INTEGER,                      -- day of the month it is usually taken
    account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    active      INTEGER NOT NULL DEFAULT 1,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- A savings goal: an amount by a date, fed either by an account whose
-- balance is the progress, or by hand. See goals.py.
CREATE TABLE IF NOT EXISTS goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    target      REAL NOT NULL,
    currency    TEXT NOT NULL DEFAULT 'EUR',
    target_date TEXT,
    account_id  INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    saved       REAL NOT NULL DEFAULT 0,      -- by hand, when no account feeds it
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- What a security paid per share, by ex-date, as Yahoo lists it —
-- the past year of which, times the units held, is next year's
-- expected income. Fetched once a day at most. See dividends.py.
CREATE TABLE IF NOT EXISTS dividend_events (
    isin       TEXT NOT NULL,
    ex_date    TEXT NOT NULL,
    amount     REAL NOT NULL,                 -- per share, in `currency`
    currency   TEXT,
    PRIMARY KEY (isin, ex_date)
);

-- A URL of the user's own to POST to when something happened — a
-- sync, a missed bill. See webhooks.py.
CREATE TABLE IF NOT EXISTS webhooks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT NOT NULL,
    events     TEXT NOT NULL,                 -- comma-separated
    secret     TEXT NOT NULL,                 -- for the HMAC signature
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_at    TEXT,
    last_error TEXT
);

-- One file import: which file, through which importer, when, and
-- how many rows it brought — so it can be undone as one thing when
-- the mapping was wrong. Rows carry the import's id; rows a re-import
-- found already there keep the id of the import that first brought
-- them. See importers.store().
-- A row the user removed, by the id it arrived under. An imported row
-- is the bank's word and comes back with the next import or sync —
-- unless its id is remembered here, which is what makes "remove"
-- mean remove and not "hide until tomorrow".
CREATE TABLE IF NOT EXISTS removed_rows (
    external_id TEXT PRIMARY KEY,
    account_id  INTEGER,
    removed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Which enriched row took which bare twin's place (ledger.py): a row
-- that has claimed its twin does not claim another on the next pass,
-- so two identical bookings the bank really made stay two.
-- What the user has said about a detected subscription: that it is one
-- (so it counts even when the rhythm is ragged), or that it is not (so
-- it stops being offered). The key is the fingerprint subscriptions.py
-- groups by; a detection nobody has judged has no row here.
CREATE TABLE IF NOT EXISTS subscription_marks (
    key        TEXT PRIMARY KEY,
    state      TEXT NOT NULL,               -- 'confirmed' or 'ignored'
    name       TEXT,                        -- what it was called when marked
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS twin_claims (
    kept_id             INTEGER NOT NULL,
    removed_external_id TEXT NOT NULL,
    PRIMARY KEY (kept_id, removed_external_id)
);

-- Net worth as another app recorded it, day by day, from before this
-- app's own records reach. The history line uses these up to the day
-- the records take over; nothing else does — a total nobody here can
-- take apart is a total, not an account.
CREATE TABLE IF NOT EXISTS net_worth_readings (
    as_of    TEXT NOT NULL,
    currency TEXT NOT NULL,
    amount   REAL NOT NULL,
    source   TEXT,
    PRIMARY KEY (as_of, currency)
);

CREATE TABLE IF NOT EXISTS imports (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    filename   TEXT,
    source     TEXT,
    inserted   INTEGER NOT NULL DEFAULT 0,
    at         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- A payslip, whole — see importers/payslip.py. One per employer, earner
-- and month; the same sheet imported again replaces its reading. The
-- rows it books sit in transactions under the import like any other.
CREATE TABLE IF NOT EXISTS payslips (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id          INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    import_id           INTEGER,
    employer            TEXT NOT NULL,
    employee            TEXT NOT NULL,
    period              TEXT NOT NULL,             -- YYYY-MM
    paid_on             TEXT,
    currency            TEXT NOT NULL,
    gross               REAL NOT NULL,
    base_salary         REAL,
    bonus               REAL NOT NULL DEFAULT 0,
    allowances          REAL NOT NULL DEFAULT 0,
    employee_social     REAL NOT NULL DEFAULT 0,   -- negative: AHV, ALV, accident
    employee_pension    REAL NOT NULL DEFAULT 0,   -- negative
    tax                 REAL NOT NULL DEFAULT 0,   -- negative: tax at source
    other_deductions    REAL NOT NULL DEFAULT 0,   -- negative: the canteen, and such
    net_paid            REAL NOT NULL,
    employer_pension    REAL NOT NULL DEFAULT 0,
    employer_social     REAL NOT NULL DEFAULT 0,
    employer_side_known INTEGER NOT NULL DEFAULT 1, -- 0: the sheet prints no employer block; the floor is shown
    layout              TEXT,
    lines               TEXT,                      -- JSON, every line the sheet printed
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (employer, employee, period)
);

-- A payslip layout the user mapped themselves — see importers/
-- payslip_map.py. Keyed on the sheet's own markers, the employer and
-- the earner, so next month's sheet is recognised by what is in it.
CREATE TABLE IF NOT EXISTS payslip_mappings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    employer   TEXT NOT NULL,
    employee   TEXT NOT NULL,
    mapping    TEXT NOT NULL,                 -- JSON {format, buckets, period_label, paid_label, currency}
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (employer, employee)
);

-- A column mapping the user drew for a CSV no built-in importer knows,
-- keyed on the file's header so the next export from the same bank is
-- recognised without asking again. See importers/generic.py.
CREATE TABLE IF NOT EXISTS csv_mappings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    header_key TEXT NOT NULL UNIQUE,
    delimiter  TEXT NOT NULL DEFAULT ',',
    mapping    TEXT NOT NULL,                 -- JSON {field: column, …options}
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_links_remote
    ON broker_links(provider, remote_id) WHERE remote_id IS NOT NULL;

-- Every conversion asks the same question: the newest publication day
-- at or before some date.
CREATE INDEX IF NOT EXISTS idx_fx_as_of ON fx_rates(as_of DESC);
"""


def backup_before_upgrade(conn: sqlite3.Connection, path: Path) -> Path | None:
    """A copy of the database as the previous version left it, made
    the first time a different version opens it — before a single
    column is added.

    The migrations here only go forward: a column, once added, is not
    taken away, and a repair, once run, is not undone. That is fine
    until an upgrade goes wrong, at which point "install the old
    version" is only half an answer — the old code and the new file
    may not agree. The other half is this copy, next to the live file,
    named after the version that wrote it, so the instruction becomes:
    pin the old tag, put the copy back, start. Made through SQLite's
    own backup call, not a file copy, so a write-ahead log with pages
    not yet in the main file is included. The newest KEEP_BACKUPS are
    kept; a database that was never opened by another version has no
    copy, because there is nothing to go back to.
    """
    try:
        row = conn.execute("SELECT value FROM app_state WHERE key = 'last_version'").fetchone()
        previous = row[0] if row else None
    except sqlite3.OperationalError:            # a database from before app_state
        previous = None
    if previous == __version__:
        return None
    folder = path.parent / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = folder / f"{path.stem}-{previous or 'pre-' + __version__}-{stamp}{path.suffix}"
    for i in range(2, 100):                     # two starts in one second: keep both
        if not target.exists():
            break
        target = target.with_name(f"{path.stem}-{previous or 'pre-' + __version__}-{stamp}-{i}{path.suffix}")
    copy = sqlite3.connect(target)
    try:
        conn.backup(copy)
    finally:
        copy.close()
    for old in sorted(folder.glob(f"{path.stem}-*{path.suffix}"), key=lambda f: (f.stat().st_mtime, f.name),
                      reverse=True)[KEEP_BACKUPS:]:
        old.unlink(missing_ok=True)
    return target


def init_db(path: Path | None = None) -> Path:
    settings.ensure_dirs()
    path = path or settings.DB_PATH
    existed = path.is_file() and path.stat().st_size > 0
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
        if existed:
            saved = backup_before_upgrade(conn, path)
            if saved:
                print(f"  backup:  {saved}", flush=True)
        conn.executescript(SCHEMA)          # tables
        _add_missing_columns(conn)          # columns an older version lacks
        conn.executescript(INDEXES)         # only now can they be indexed
        _repair_rows(conn)                  # what an older parser got wrong
        conn.execute("INSERT INTO app_state (key, value, updated_at) VALUES ('last_version', ?, datetime('now')) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                     (__version__,))
        done_keys = {r[0] for r in conn.execute("SELECT key FROM app_state")}
        heal = "eb_twins_of_moved_in_rows" not in done_keys
        heal_trades = "fp_trade_twins_and_openings" not in done_keys
        conn.commit()
    finally:
        conn.close()
    if heal:
        # 0.69.1: an account whose bank sync ran before its move-in from
        # Financial Planner held every booking twice — the sync's bare
        # copy and the move-in's enriched one. Paired and healed once,
        # in Python because the pairing is one to one; see ledger.py.
        from . import ledger
        gone = ledger.heal_twins(path=path)
        with get_conn(path) as conn:
            conn.execute("INSERT OR REPLACE INTO app_state (key, value, updated_at) VALUES "
                         "('eb_twins_of_moved_in_rows', ?, datetime('now'))", (str(gone),))
        if gone:
            print(f"  healed:  {gone} doubled bank rows", flush=True)
    if heal_trades:
        # 0.70.6: a trade booked by a reader and again by the move-in,
        # and the opening position that counted the pair twice.
        from . import ledger
        fixed = ledger.heal_trade_twins(path=path)
        with get_conn(path) as conn:
            conn.execute("INSERT OR REPLACE INTO app_state (key, value, updated_at) VALUES "
                         "('fp_trade_twins_and_openings', ?, datetime('now'))", (str(fixed),))
        if fixed["twins"] or fixed["openings"]:
            print(f"  healed:  {fixed['twins']} doubled trades, {fixed['openings']} opening positions", flush=True)
    return path


# Rows an earlier version stored wrongly, put right on start — for the
# same reason the columns are: starting the app is the upgrade. Every
# statement here must be idempotent and must leave a row the user has
# corrected by hand alone, which `edited_at` marks.
_REPAIRS = [
    # Up to 0.38.0 the Trade Republic parser stored `shares` and `price`
    # off a dividend row — the position it was paid on and the amount
    # per share — as a quantity and a price. Everything that sums
    # quantities counted the whole position again on every payout.
    "UPDATE transactions SET quantity = NULL, price = NULL "
    "WHERE source = 'trade_republic' AND kind IN ('dividend', 'interest') "
    "AND quantity IS NOT NULL AND edited_at IS NULL",
]

# Re-filings that run ONCE, keyed in app_state: the first start after
# the change moves the rows, and what the user does with them after
# that is theirs — a row filed back by hand on the Categorize page
# must not be moved again at the next start.
_ONCE = [
    # 0.44.0: the move from Financial Planner summed the lines of every
    # snapshot of a day — and a day with two snapshots (a manual one
    # beside the nightly one) came out doubled. A reading that is
    # twice the day before and twice the day after, on the same
    # account from the same move, is that day; it is halved.
    ("fp_double_snapshot_day",
     "UPDATE balances SET amount = amount / 2 WHERE id IN ("
     "  SELECT b.id FROM balances b "
     "  JOIN balances p ON p.account_id = b.account_id AND p.balance_type = b.balance_type AND p.as_of = date(b.as_of, '-1 day') "
     "  JOIN balances n ON n.account_id = b.account_id AND n.balance_type = b.balance_type AND n.as_of = date(b.as_of, '+1 day') "
     "  WHERE b.balance_type = 'financial_planner' AND abs(p.amount) > 1 AND abs(n.amount) > 1 "
     "    AND abs(b.amount - 2 * p.amount) < abs(p.amount) * 0.02 + 1 "
     "    AND abs(b.amount - 2 * n.amount) < abs(n.amount) * 0.02 + 1)"),
    # 0.42.0 folded the day and the amount into a bank row's id — the
    # reference alone is not unique at every bank. The rows already
    # synced get the new shape from what they carry, so the next sync
    # recognises them. The id is eb:<hash>:<rest>; a rest that is a
    # hash of the row (h:…) or already starts with a day is left alone.
    ("eb_ids_with_day",
     "UPDATE OR IGNORE transactions SET external_id = "
     "  substr(external_id, 1, instr(substr(external_id, 4), ':') + 3) || txn_date || ':' "
     "  || printf('%.2f', abs(amount)) || ':' || substr(external_id, instr(substr(external_id, 4), ':') + 4) "
     "WHERE external_id LIKE 'eb:%' AND instr(substr(external_id, 4), ':') > 0 "
     "  AND substr(external_id, instr(substr(external_id, 4), ':') + 4) NOT LIKE 'h:%' "
     "  AND substr(external_id, instr(substr(external_id, 4), ':') + 4) NOT LIKE '____-__-__:%'"),
    # 0.39.0 gave income its own categories. Dividends and interest had
    # been filed as plain income by their kind; they now have a category
    # of their own, and the rows already there go with it.
    ("refiled_capital_income",
     "UPDATE transactions SET category = 'capital_income' "
     "WHERE kind IN ('dividend', 'interest') AND category = 'income'"),
    # Up to 0.46 the move from Financial Planner kept a Kraken trade's
    # id bare — TUT7MA-K67YX-X6Z4TJ — where the Kraken sync writes
    # kraken:trade:TUT7MA-K67YX-X6Z4TJ, so the same fill arrived twice:
    # once from the old app, once from Kraken, and the cost basis of a
    # coin counted every such buy double. Where both copies exist the
    # old app's goes — Kraken's carries the fee the way this app books
    # a buy — and a copy on its own takes the id the sync would give
    # it, so the next sync recognises it.
    ("fp_kraken_trade_ids",
     ["DELETE FROM transactions WHERE source LIKE 'financial_planner%' AND edited_at IS NULL "
      "AND external_id GLOB '[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]' "
      "AND EXISTS (SELECT 1 FROM transactions k WHERE k.account_id = transactions.account_id "
      "            AND k.external_id = 'kraken:trade:' || transactions.external_id)",
      "UPDATE OR IGNORE transactions SET external_id = 'kraken:trade:' || external_id "
      "WHERE source LIKE 'financial_planner%' "
      "AND external_id GLOB '[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]'"]),
]


def _repair_rows(conn: sqlite3.Connection) -> None:
    for sql in _REPAIRS:
        conn.execute(sql)
    done = {r[0] for r in conn.execute("SELECT key FROM app_state")}
    for key, sql in _ONCE:
        if key in done:
            continue
        for stmt in ([sql] if isinstance(sql, str) else sql):
            conn.execute(stmt)
        conn.execute("INSERT INTO app_state (key, value, updated_at) "
                     "VALUES (?, 'done', datetime('now'))", (key,))


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
    # 0.42.0: rows up to this day are on record from elsewhere — moved
    # in from another app under ids this app's importers would not
    # produce — so an import or a sync leaves that span alone rather
    # than booking every row a second time. See migrate.py.
    "accounts": [
        ("ledger_until", "TEXT"),
    ],
    # A rule that says where to look, which way the money went, and
    # how much — see categories.py. Older rows: anywhere, any, any.
    "category_rules": [
        ("field", "TEXT NOT NULL DEFAULT 'any'"),
        ("direction", "TEXT NOT NULL DEFAULT 'any'"),
        ("amount_min", "REAL"),
        ("amount_max", "REAL"),
        # 0.32.0: more to match on, more to do. A rule may confine itself
        # to one account or one kind, match the text as a start, an exact
        # value or a pattern; and beyond the category it may rename the
        # counterparty, set the kind, and add a tag.
        ("account_id", "INTEGER"),
        ("kind", "TEXT"),
        ("match_mode", "TEXT NOT NULL DEFAULT 'contains'"),
        ("set_counterparty", "TEXT"),
        ("set_kind", "TEXT"),
        ("add_tag", "TEXT"),
        # 0.70.0: whose spending a match is — a person's id, or "shared".
        ("set_owner", "TEXT"),
    ],
    # 0.71.0: what the receiver speaks. "json" is this app's own
    # payload with its signature; "ntfy" is a line of prose to a
    # phone, which is what a push server wants. See webhooks.py.
    "webhooks": [
        ("kind", "TEXT NOT NULL DEFAULT 'json'"),
    ],
    "securities": [
        ("quote_type", "TEXT"),
    ],
    # 0.55.0: what the loan was drawn as, when it was drawn in another
    # currency — €150 000 at 1.12166 for a CHF mortgage — so the page
    # can say what it cost the day it began, not only what it is worth
    # at today's rate.
    "loans": [
        ("drawn_amount", "REAL"),
        ("drawn_currency", "TEXT"),
    ],
    # 0.47.0: where a coin goes when it leaves the exchange — the
    # user's own wallet, an account here — so a withdrawal is a move
    # between two of their accounts, not units vanishing. See
    # brokers/kraken.py.
    "broker_links": [
        ("wallet_account_id", "INTEGER"),
    ],
    "goals": [
        ("kind", "TEXT NOT NULL DEFAULT 'saving'"),
    ],
    "transactions": [
        ("import_id", "INTEGER"),
        # Tags: any number of words on a row, beside the one category.
        # Stored as a comma-separated string, lower-case, searched with
        # LIKE on ',tag,' — the simplest thing that works in one column.
        ("tags", "TEXT"),
        ("edited_at", "TEXT"),
        ("kind", "TEXT NOT NULL DEFAULT 'other'"),
        ("isin", "TEXT"),
        ("security_name", "TEXT"),
        ("quantity", "REAL"),
        ("price", "REAL"),
        ("fee", "REAL"),
        ("tax", "REAL"),
        ("source", "TEXT"),
        ("category", "TEXT"),
        # 0.70.0: whose spending a row is — one of the people, or shared
        # by the household — for the Who spent page. NULL and 0: nobody
        # has said. See expenses.py.
        ("owner_id", "INTEGER"),
        ("owner_shared", "INTEGER NOT NULL DEFAULT 0"),
        # 0.72.0: how a row counts on the Cash Flow page. NULL is the
        # ordinary case, the amount on its own month; 0 leaves it out of
        # the averages — a one-off nobody wants in a monthly figure; N
        # spreads it over N months from its own, which is what a car
        # bought in one payment actually costs per month. The row's
        # amount is untouched: a balance, a net worth and a budget see
        # what was really paid. See cashflow.py.
        ("spread_months", "INTEGER"),
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
    # SQLite has the REGEXP operator but no function behind it; a rule
    # that matches a pattern needs one. Case-insensitive, as every other
    # match in this app is.
    conn.create_function("regexp", 2, _regexp)
    # SQLite's own LOWER() and UPPER() fold ASCII and nothing else, so
    # LOWER('BÄCKER') is 'bÄcker' — while Python lowers the pattern to
    # 'bäcker'. Every rule and every search whose text carries Ä, Ö, Ü,
    # É or any other letter above ASCII therefore matched nothing, in
    # silence. Python's own casing is put in their place, for every
    # query in the app at once.
    conn.create_function("lower", 1, _lower, deterministic=True)
    conn.create_function("upper", 1, _upper, deterministic=True)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _lower(value):
    """LOWER() as the rest of the world means it. NULL stays NULL."""
    return None if value is None else str(value).lower()


def _upper(value):
    return None if value is None else str(value).upper()


def _regexp(pattern, value) -> bool:
    import re
    if pattern is None or value is None:
        return False
    try:
        return re.search(pattern, str(value), re.IGNORECASE) is not None
    except re.error:
        return False


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
