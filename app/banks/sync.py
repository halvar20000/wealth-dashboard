"""Between the bank and the database.

`enablebanking.py` knows the protocol and nothing about this app.
`db.py` knows the tables and nothing about banks. This module is the only
place that knows both, which is what makes adding a second provider a
matter of writing one more client rather than touching the schema.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .. import categories, settings
from ..db import get_conn
from . import enablebanking as eb

APP_ID_FILE = "enablebanking_app_id"
KEY_FILE = "enablebanking_private.key"


# ─── Credentials ─────────────────────────────────────────────────────

def credentials_present() -> bool:
    return ((settings.SECRETS_DIR / APP_ID_FILE).exists()
            and (settings.SECRETS_DIR / KEY_FILE).exists())


def save_credentials(app_id: str, private_key_pem: str) -> None:
    settings.ensure_dirs()
    app_id = (app_id or "").strip()
    if not app_id:
        raise ValueError("An Application ID is required.")
    pem = (private_key_pem or "").strip()
    if "BEGIN PUBLIC KEY" in pem or "BEGIN CERTIFICATE" in pem:
        raise ValueError(
            "That is the PUBLIC half — the file you uploaded to Enable "
            "Banking. You need the private one: if you chose 'Generate' when "
            "creating the application, it is the <application-id>.pem your "
            "browser downloaded.")
    if "PRIVATE KEY" not in pem:
        # Catching this here is worth a line: the same mistake made
        # silently produces a signature failure on every later call,
        # reported by the API as a generic 401 that names nothing.
        raise ValueError(
            "That does not look like a private key. Paste the whole file, "
            "including the -----BEGIN PRIVATE KEY----- line. If you pasted "
            "the .pem you uploaded to Enable Banking, that is the PUBLIC "
            "half — you need the other one.")

    (settings.SECRETS_DIR / APP_ID_FILE).write_text(app_id + "\n")
    key_path = settings.SECRETS_DIR / KEY_FILE
    key_path.write_text(pem + "\n")
    for p in (settings.SECRETS_DIR / APP_ID_FILE, key_path):
        try:
            p.chmod(0o600)
        except OSError:
            pass


def client() -> eb.Client:
    """A configured client, or a readable error saying what is missing."""
    app_id_path = settings.SECRETS_DIR / APP_ID_FILE
    if not app_id_path.exists():
        raise eb.EnableBankingError(
            "config", str(app_id_path), 0,
            "Enable Banking is not configured yet — add your Application ID "
            "and private key in Settings.")
    return eb.Client(app_id_path.read_text().strip(),
                     eb.load_private_key(settings.SECRETS_DIR / KEY_FILE))


# ─── Connect ─────────────────────────────────────────────────────────

def begin_connect(account_id: int, aspsp_name: str, aspsp_country: str) -> str:
    """Ask the bank for an authorisation URL and remember why.

    The state row is written BEFORE the user leaves. They come back to a
    brand-new request carrying nothing but ?code and ?state, so anything
    not written down first is gone.
    """
    cfg = settings.load()
    state = eb.new_state()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auth_states (state, account_id, aspsp_name, aspsp_country) "
            "VALUES (?, ?, ?, ?)",
            (state, account_id, aspsp_name, aspsp_country))
    resp = client().start_auth(
        aspsp_name=aspsp_name, aspsp_country=aspsp_country,
        redirect_url=cfg["redirect_url"], state=state)
    url = resp.get("url")
    if not url:
        raise eb.EnableBankingError("POST", "/auth", 0,
                                    f"no authorisation URL in the response: {resp}")
    return url


def complete_connect(code: str, state: str) -> dict:
    """Exchange the code, then link the bank's accounts to ours.

    Returns {account_id, linked: [labels], session_id}.
    """
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM auth_states WHERE state = ?",
                           (state,)).fetchone()
        if row is None:
            # Either a stale bookmark, a second click on the callback, or
            # someone else's redirect. All three are refusals, not errors
            # to recover from by guessing which connection was meant.
            raise ValueError(
                "This authorisation is not one this app started, or it has "
                "already been used. Start the connection again.")
        pending = dict(row)
        conn.execute("DELETE FROM auth_states WHERE state = ?", (state,))

    session = client().create_session(code)
    session_id = session.get("session_id")
    accounts = session.get("accounts") or []
    if not accounts:
        raise ValueError(
            "The bank returned no accounts for that consent. This usually "
            "means no account was ticked on the bank's own consent screen.")

    linked = []
    valid_until = session.get("access", {}).get("valid_until")
    with get_conn() as conn:
        for i, acct in enumerate(accounts):
            uid = acct.get("uid") or acct.get("account_uid")
            if not uid:
                continue
            ident = (acct.get("identification_hash")
                     or acct.get("identification_hashes", [None])[0]
                     or uid)
            iban = (acct.get("account_id") or {}).get("iban")
            label = eb.account_label(acct)

            # The first bank account goes on the account the user was
            # connecting. A consent covering several — a current account
            # and its savings account — creates the extra ones rather
            # than merging them, because two balances added together is
            # not a balance.
            target_id = pending["account_id"] if i == 0 else None
            existing = _renewable_link(conn, uid, ident, iban, target_id)
            if existing:
                # A renewal, not a second connection. An account has one
                # link, and the link is the consent: a new session goes
                # on the row the history was synced through, so the
                # account page, the sync and the nightly job all find
                # one connection and it is the live one. Two links on
                # an account is how a bank account's every booking
                # arrives twice under two ids.
                if existing["iban"] and existing["iban"] == iban:
                    # The same bank account, whatever hash it carries
                    # today: its bookings are already on record under
                    # the old one, and a re-sync must find them there.
                    ident = existing["identification_hash"] or ident
                conn.execute(
                    "UPDATE bank_links SET aspsp_name = ?, aspsp_country = ?, "
                    "session_id = ?, account_uid = ?, identification_hash = ?, "
                    "iban = ?, valid_until = ?, last_error = NULL WHERE id = ?",
                    (pending["aspsp_name"], pending["aspsp_country"], session_id,
                     uid, ident, iban, valid_until, existing["id"]))
                conn.execute("DELETE FROM bank_links WHERE account_id = ? AND id != ?",
                             (existing["account_id"], existing["id"]))
                linked.append(label)
                continue

            if target_id is None:
                cur = conn.execute(
                    "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                    (f"{pending['aspsp_name']} {label}", "bank",
                     acct.get("currency") or settings.get("base_currency", "EUR")))
                target_id = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO bank_links (account_id, provider, aspsp_name, "
                "aspsp_country, session_id, account_uid, identification_hash, "
                "iban, valid_until) VALUES (?, 'enablebanking', ?, ?, ?, ?, ?, ?, ?)",
                (target_id, pending["aspsp_name"], pending["aspsp_country"],
                 session_id, uid, ident, iban, valid_until))
            linked.append(label)

    return {"account_id": pending["account_id"], "linked": linked,
            "session_id": session_id}


def _renewable_link(conn, uid: str, ident: str, iban: str | None,
                    target_id: int | None):
    """The link a bank account from a fresh consent renews, or None.

    By Enable Banking's uid first — the same session finished twice,
    from the callback and the paste page. Then the link on the account
    the user was connecting: its consent ran out, or they are moving
    it to another bank, and either way what they asked for is one
    connection on this account. For the further accounts a consent
    covers there is no chosen account, so the bank account itself is
    looked for — by the hash the bank identifies it with, or its IBAN —
    so a renewal does not create "DKB Tagesgeld" a second time.
    """
    row = conn.execute("SELECT * FROM bank_links WHERE account_uid = ?",
                       (uid,)).fetchone()
    if row is None and target_id is not None:
        row = conn.execute("SELECT * FROM bank_links WHERE account_id = ? "
                           "ORDER BY id DESC LIMIT 1", (target_id,)).fetchone()
    if row is None and target_id is None:
        row = conn.execute(
            "SELECT * FROM bank_links WHERE identification_hash = ? "
            "OR (iban IS NOT NULL AND iban = ?) ORDER BY id DESC LIMIT 1",
            (ident, iban)).fetchone()
    return dict(row) if row else None


def disconnect(account_id: int) -> int:
    """Drop the bank connection(s) of an account; the account, its
    balances and its history stay. Returns how many links went.

    The consent at Enable Banking is ended too, as a courtesy and so
    that "disconnected" means what it says — best effort: a consent
    that has already expired, or a bank that will not answer, must not
    keep a link alive on this side.
    """
    with get_conn() as conn:
        links = [dict(r) for r in conn.execute(
            "SELECT id, session_id FROM bank_links WHERE account_id = ?", (account_id,))]
        conn.execute("DELETE FROM bank_links WHERE account_id = ?", (account_id,))
    for link in links:
        if link["session_id"]:
            try:
                client().delete_session(link["session_id"])
            except Exception:                       # noqa: BLE001
                pass
    return len(links)


# ─── Sync ────────────────────────────────────────────────────────────

def sync_link(link_id: int) -> dict:
    """Pull balance and transactions for one linked account."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT bl.*, a.currency AS account_currency, a.name AS account_name, "
            "a.ledger_until AS ledger_until "
            "FROM bank_links bl JOIN accounts a ON a.id = bl.account_id "
            "WHERE bl.id = ?", (link_id,)).fetchone()
    if row is None:
        raise ValueError(f"No such connection: {link_id}")
    link = dict(row)
    api = client()
    result = {"account": link["account_name"], "inserted": 0,
              "balance": None, "error": None}

    try:
        balance = eb.pick_balance(api.balances(link["account_uid"]))
        if balance:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO balances (account_id, amount, currency, "
                    "balance_type, as_of) VALUES (?, ?, ?, ?, ?)",
                    (link["account_id"], balance["amount"],
                     balance["currency"] or link["account_currency"],
                     balance["balance_type"], balance["as_of"]))
            result["balance"] = balance

        rows = []
        for txn in api.all_transactions(link["account_uid"]):
            norm = eb.normalise_transaction(
                txn, link["identification_hash"] or link["account_uid"],
                default_currency=link["account_currency"])
            if norm:
                rows.append(norm)
        # The span already on record from elsewhere — see
        # accounts.ledger_until — is not booked a second time.
        if link.get("ledger_until"):
            rows = [r for r in rows if r["txn_date"] > link["ledger_until"]]

        with get_conn() as conn:
            for r in rows:
                # INSERT OR IGNORE against the unique index is the whole
                # deduplication strategy: a re-sync of an overlapping
                # window costs nothing and cannot double a balance.
                cur = conn.execute(
                    "INSERT OR IGNORE INTO transactions (account_id, txn_date, "
                    "description, counterparty, amount, currency, external_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (link["account_id"], r["txn_date"], r["description"],
                     r["counterparty"], r["amount"], r["currency"],
                     r["external_id"]))
                result["inserted"] += cur.rowcount
            conn.execute(
                "UPDATE bank_links SET last_sync_at = ?, last_error = NULL "
                "WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), link_id))
        # The user's rules apply to what arrives next, not only to what
        # was there when the rule was made — that is the promise on the
        # Categorize page, and this is where it is kept.
        if result["inserted"]:
            categories.categorise_new(link["account_id"])
    except Exception as exc:                        # noqa: BLE001
        # The error is stored on the link, not raised into the page. A
        # consent that expired last night is the normal end of a
        # connection's life; the account must keep its history and say
        # what happened, not become an error screen.
        result["error"] = str(exc)
        with get_conn() as conn:
            conn.execute("UPDATE bank_links SET last_error = ? WHERE id = ?",
                         (str(exc)[:500], link_id))
    _announce(result)
    return result


def _announce(result: dict) -> None:
    """A webhook for whoever listens — see webhooks.py. Never lets a
    listener's trouble become the sync's."""
    try:
        from .. import webhooks
        webhooks.fire("sync.failed" if result.get("error") else "sync.completed",
                      {k: result.get(k) for k in ("account", "inserted", "balance", "error")})
    except Exception:                               # noqa: BLE001
        pass


def sync_all() -> list[dict]:
    """Every connected account, one after another. Each result carries
    its own error, so one bank refusing does not stop the next."""
    with get_conn() as conn:
        ids = [int(r["id"]) for r in conn.execute(
            "SELECT id FROM bank_links WHERE account_uid IS NOT NULL ORDER BY id")]
    return [sync_link(i) for i in ids]


def sync_due(now: datetime, cfg: dict, last_run: str | None) -> bool:
    """Whether the daily sync should run at `now`.

    Once a day at the configured time, and never twice on one day even
    if the clock is checked more often than once a minute. A day whose
    time slot was slept through — the machine was off at noon — is
    caught up the moment the app is next awake past that time, because
    "it runs at noon" must not mean "it does not run today".
    """
    if not cfg.get("auto_sync", True):
        return False
    hhmm = str(cfg.get("sync_time") or "12:00")
    try:
        hour, minute = (int(x) for x in hhmm.split(":", 1))
    except ValueError:
        hour, minute = 12, 0
    today = now.date().isoformat()
    if last_run and last_run[:10] >= today:
        return False
    return (now.hour, now.minute) >= (hour, minute)


def health(now: datetime | None = None) -> list[dict]:
    """Every connection, graded — so a consent that lapsed last night is
    noticed on the overview and not weeks later in a total that stopped
    moving. Worst thing wins: an expired session beats a fresh sync.

        red     expired, never synced, or silent for two days
        yellow  expires within two weeks, or a day without a sync
        green   otherwise
    """
    now = now or datetime.now(timezone.utc)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT bl.id, bl.account_id, bl.aspsp_name, bl.last_sync_at, "
            "       bl.valid_until, bl.last_error, a.name AS account "
            "  FROM bank_links bl JOIN accounts a ON a.id = bl.account_id "
            " WHERE bl.account_uid IS NOT NULL ORDER BY a.name").fetchall()
    out = []
    for r in rows:
        days_left = days_until_expiry(r["valid_until"])
        last = _parse_iso(r["last_sync_at"])
        age_h = (now - last).total_seconds() / 3600 if last else None
        if days_left is not None and days_left < 0:
            status, hint = "red", "expired"
        elif last is None:
            status, hint = "red", "never"
        elif r["last_error"]:
            status, hint = "red", "error"
        elif age_h >= 48:
            status, hint = "red", "stale"
        elif days_left is not None and days_left < 14:
            status, hint = "yellow", "expiring"
        elif age_h >= 12:
            status, hint = "yellow", "old"
        else:
            status, hint = "green", "ok"
        out.append({"link_id": r["id"], "account_id": r["account_id"],
                    "account": r["account"], "bank": r["aspsp_name"],
                    "last_sync_at": r["last_sync_at"], "hours_ago": age_h,
                    "days_left": days_left, "error": r["last_error"],
                    "status": status, "hint": hint})
    order = {"red": 0, "yellow": 1, "green": 2}
    out.sort(key=lambda c: (order[c["status"]], c["account"]))
    return out


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def sync_account(account_id: int) -> dict | None:
    """Sync whichever link belongs to this account, if any."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM bank_links WHERE account_id = ? LIMIT 1",
            (account_id,)).fetchone()
    return sync_link(int(row["id"])) if row else None


def days_until_expiry(valid_until: str | None) -> int | None:
    if not valid_until:
        return None
    try:
        when = datetime.fromisoformat(str(valid_until).replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (when - datetime.now(timezone.utc)).days
