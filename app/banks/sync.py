"""Between the bank and the database.

`enablebanking.py` knows the protocol and nothing about this app.
`db.py` knows the tables and nothing about banks. This module is the only
place that knows both, which is what makes adding a second provider a
matter of writing one more client rather than touching the schema.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .. import categories, settings
from ..db import get_conn
from . import enablebanking as eb
from . import gocardless as gc

APP_ID_FILE = "enablebanking_app_id"
KEY_FILE = "enablebanking_private.key"
GC_ID_FILE = "gocardless_secret_id"
GC_KEY_FILE = "gocardless_secret_key"

PROVIDERS = {"enablebanking": "Enable Banking", "gocardless": "GoCardless"}


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


# ─── GoCardless credentials ──────────────────────────────────────────

def gocardless_present() -> bool:
    return ((settings.SECRETS_DIR / GC_ID_FILE).exists()
            and (settings.SECRETS_DIR / GC_KEY_FILE).exists())


def save_gocardless(secret_id: str, secret_key: str) -> None:
    settings.ensure_dirs()
    secret_id = (secret_id or "").strip()
    secret_key = (secret_key or "").strip()
    if not secret_id or not secret_key:
        raise ValueError("GoCardless needs both the Secret ID and the Secret Key "
                         "— the two halves of a user secret from the portal.")
    if len(secret_key) < 40:
        raise ValueError("That Secret Key is too short to be one. The portal shows "
                         "it once, when the user secret is created; if it is gone, "
                         "create a new user secret.")
    for name, value in ((GC_ID_FILE, secret_id), (GC_KEY_FILE, secret_key)):
        path = settings.SECRETS_DIR / name
        path.write_text(value + "\n")
        try:
            path.chmod(0o600)
        except OSError:
            pass


def forget_gocardless() -> None:
    for name in (GC_ID_FILE, GC_KEY_FILE):
        try:
            (settings.SECRETS_DIR / name).unlink()
        except FileNotFoundError:
            pass


def gc_client() -> gc.Client:
    if not gocardless_present():
        raise gc.GoCardlessError("config", "", 0, "GoCardless is not configured yet — add "
                                 "the Secret ID and Secret Key in Settings.")
    return gc.Client((settings.SECRETS_DIR / GC_ID_FILE).read_text().strip(),
                     (settings.SECRETS_DIR / GC_KEY_FILE).read_text().strip())


def providers() -> list[str]:
    """The aggregators with credentials, in the order the picker offers them."""
    out = []
    if credentials_present():
        out.append("enablebanking")
    if gocardless_present():
        out.append("gocardless")
    return out


def institutions(provider: str, country: str) -> list[dict]:
    """The banks of a country as one shape whichever aggregator lists
    them: {provider, name, country, id, sandbox, days}."""
    if provider == "gocardless":
        return [{"provider": "gocardless", "name": b.get("name") or b.get("id"),
                 "country": country.upper(), "id": b.get("id"), "sandbox": "SANDBOX" in str(b.get("id", "")).upper(),
                 "days": int(b["transaction_total_days"]) if str(b.get("transaction_total_days") or "").isdigit() else None,
                 "logo": b.get("logo")}
                for b in gc_client().institutions(country)]
    return [{"provider": "enablebanking", "name": b.get("name"), "country": b.get("country") or country.upper(),
             "id": b.get("name"), "sandbox": bool(b.get("sandbox")), "days": None, "logo": b.get("logo")}
            for b in client().aspsps(country)]


# ─── Connect ─────────────────────────────────────────────────────────

def begin_connect(account_id: int, aspsp_name: str, aspsp_country: str,
                  provider: str = "enablebanking", institution_id: str | None = None) -> str:
    """Ask the bank for an authorisation URL and remember why.

    The state row is written BEFORE the user leaves. They come back to a
    brand-new request carrying nothing but ?code and ?state, so anything
    not written down first is gone.
    """
    cfg = settings.load()
    if provider == "gocardless":
        return _begin_gocardless(account_id, aspsp_name, aspsp_country, institution_id or aspsp_name, cfg)
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


def _begin_gocardless(account_id: int, name: str, country: str, institution_id: str, cfg: dict) -> str:
    """A requisition — GoCardless's word for "connect this bank and send
    them back here" — with an agreement for ninety days of access. The
    state travels as the requisition's reference and comes back as
    ?ref= on the redirect."""
    api = gc_client()
    state = gc.new_state()
    agreement_id = None
    try:
        agreement_id = api.create_agreement(institution_id).get("id")
    except gc.GoCardlessError:
        pass                          # the requisition then carries the bank's default
    resp = api.create_requisition(institution_id, cfg["redirect_url"], state, agreement_id,
                                  language=(cfg.get("language") or "EN")[:2] or "EN")
    link = resp.get("link")
    if not link:
        raise gc.GoCardlessError("POST", "/requisitions/", 0, f"no link in the response: {resp}")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auth_states (state, account_id, aspsp_name, aspsp_country, provider, "
            "institution_id, requisition_id) VALUES (?, ?, ?, ?, 'gocardless', ?, ?)",
            (state, account_id, name, country, institution_id, resp.get("id")))
    return link


def complete_gocardless(ref: str) -> dict:
    """The user is back from the bank with the reference: read the
    requisition, and link every account it now covers, as
    complete_connect() does for Enable Banking."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM auth_states WHERE state = ? AND provider = 'gocardless'",
                           (ref,)).fetchone()
        if row is None:
            raise ValueError(
                "This authorisation is not one this app started, or it has "
                "already been used. Start the connection again.")
        pending = dict(row)
    api = gc_client()
    req = api.requisition(pending["requisition_id"])
    status = (req.get("status") or "").upper()
    if status != "LN":
        # Not linked yet: the bank's screen was abandoned, or refused.
        # The state stays, so a second try at the bank can still land.
        raise ValueError(
            f"The bank has not confirmed the connection yet (GoCardless status {status or '?'}). "
            f"Finish the bank's own screen and you will be sent back here again.")
    accounts = req.get("accounts") or []
    if not accounts:
        raise ValueError("The bank returned no accounts for that consent. This usually "
                         "means no account was ticked on the bank's own consent screen.")
    agreement = None
    if req.get("agreement"):
        try:
            agreement = api.agreement(req["agreement"])
        except gc.GoCardlessError:
            agreement = None
    until = gc.valid_until(agreement, req)
    linked = []
    with get_conn() as conn:
        conn.execute("DELETE FROM auth_states WHERE state = ?", (ref,))
        for i, uid in enumerate(accounts):
            try:
                details = api.account_details(uid)
            except gc.GoCardlessError:
                details = {}
            label = gc.account_label(details, pending["aspsp_name"])
            iban = details.get("iban")
            currency = details.get("currency") or settings.get("base_currency", "EUR")
            if i == 0:
                target_id = pending["account_id"]
            else:
                cur = conn.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                                   (f"{pending['aspsp_name']} {label}", "bank", currency))
                target_id = int(cur.lastrowid)
            try:
                conn.execute(
                    "INSERT INTO bank_links (account_id, provider, aspsp_name, aspsp_country, "
                    "session_id, account_uid, identification_hash, iban, valid_until) "
                    "VALUES (?, 'gocardless', ?, ?, ?, ?, ?, ?, ?)",
                    (target_id, pending["aspsp_name"], pending["aspsp_country"],
                     pending["requisition_id"], uid, iban or uid, iban, until))
            except sqlite3.IntegrityError:
                conn.execute(
                    "UPDATE bank_links SET session_id = ?, valid_until = ?, last_error = NULL "
                    "WHERE account_uid = ?", (pending["requisition_id"], until, uid))
            linked.append(label)
    return {"account_id": pending["account_id"], "linked": linked,
            "session_id": pending["requisition_id"]}


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
            if i == 0:
                target_id = pending["account_id"]
            else:
                cur = conn.execute(
                    "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                    (f"{pending['aspsp_name']} {label}", "bank",
                     acct.get("currency") or settings.get("base_currency", "EUR")))
                target_id = int(cur.lastrowid)

            try:
                conn.execute(
                    "INSERT INTO bank_links (account_id, provider, aspsp_name, "
                    "aspsp_country, session_id, account_uid, identification_hash, "
                    "iban, valid_until) VALUES (?, 'enablebanking', ?, ?, ?, ?, ?, ?, ?)",
                    (target_id, pending["aspsp_name"], pending["aspsp_country"],
                     session_id, uid, ident, iban,
                     session.get("access", {}).get("valid_until")))
            except sqlite3.IntegrityError:
                # Re-authorising an account that is already linked: keep
                # one link and move it to the new session, so the history
                # attached to it survives.
                conn.execute(
                    "UPDATE bank_links SET session_id = ?, valid_until = ?, "
                    "last_error = NULL WHERE account_uid = ?",
                    (session_id, session.get("access", {}).get("valid_until"), uid))
            linked.append(label)

    return {"account_id": pending["account_id"], "linked": linked,
            "session_id": session_id}


# ─── Sync ────────────────────────────────────────────────────────────

def sync_link(link_id: int) -> dict:
    """Pull balance and transactions for one linked account."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT bl.*, a.currency AS account_currency, a.name AS account_name "
            "FROM bank_links bl JOIN accounts a ON a.id = bl.account_id "
            "WHERE bl.id = ?", (link_id,)).fetchone()
    if row is None:
        raise ValueError(f"No such connection: {link_id}")
    link = dict(row)
    result = {"account": link["account_name"], "inserted": 0,
              "balance": None, "error": None}
    if link.get("provider") == "gocardless":
        return _sync_gocardless(link, link_id, result)
    api = client()

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
    return result


def _store_rows(conn, account_id: int, rows: list[dict]) -> int:
    inserted = 0
    for r in rows:
        cur = conn.execute(
            "INSERT OR IGNORE INTO transactions (account_id, txn_date, "
            "description, counterparty, amount, currency, external_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, r["txn_date"], r["description"], r["counterparty"],
             r["amount"], r["currency"], r["external_id"]))
        inserted += cur.rowcount
    return inserted


def _sync_gocardless(link: dict, link_id: int, result: dict) -> dict:
    """The GoCardless half of sync_link(): one balance call, one
    transactions call — the whole window the agreement allows, every
    time, because the ids make a re-read free and GoCardless counts
    calls per day, not rows."""
    try:
        api = gc_client()
        balance = gc.pick_balance(api.balances(link["account_uid"]))
        if balance:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (link["account_id"], balance["amount"],
                     balance["currency"] or link["account_currency"],
                     balance["balance_type"], balance["as_of"]))
            result["balance"] = balance
        rows = []
        for txn in api.all_transactions(link["account_uid"]):
            norm = gc.normalise_transaction(txn, default_currency=link["account_currency"])
            if norm:
                rows.append(norm)
        with get_conn() as conn:
            result["inserted"] = _store_rows(conn, link["account_id"], rows)
            conn.execute("UPDATE bank_links SET last_sync_at = ?, last_error = NULL WHERE id = ?",
                         (datetime.now(timezone.utc).isoformat(timespec="seconds"), link_id))
        if result["inserted"]:
            categories.categorise_new(link["account_id"])
    except Exception as exc:                        # noqa: BLE001
        result["error"] = str(exc)
        with get_conn() as conn:
            conn.execute("UPDATE bank_links SET last_error = ? WHERE id = ?", (str(exc)[:500], link_id))
    return result


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
