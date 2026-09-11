"""The test suite.  Run it with:  python3 tests/test_all.py

No pytest, no network, no credentials. It drives a complete first run —
create the user, create an account, connect DKB, sync it — against the
fake in fake_bank.py, plus the normalisation rules that decide what a
bank's JSON means.

Why no pytest: this is meant to run on the machine it is installed on,
which is often a NAS with an unhelpful Python. A suite that needs its own
tooling is a suite nobody runs.
"""

from __future__ import annotations

import ast
import base64
import json
import re
from datetime import datetime, timezone
import os
import sys
import pathlib
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="wd-test-"))
os.environ["WD_DATA_DIR"] = str(TMP)
os.environ["WD_SECRETS_DIR"] = str(TMP / "secrets")
os.environ["WD_SECRET_KEY"] = "test-key-not-a-real-one"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import auth, db, settings                      # noqa: E402
from app.banks import enablebanking as eb               # noqa: E402
from app.banks import sync as banksync                  # noqa: E402
import fake_bank                                        # noqa: E402

PASS = FAIL = 0


def check(label, got, want=None, predicate=None):
    global PASS, FAIL
    ok = predicate(got) if predicate else (got == want)
    print(f"  {'ok  ' if ok else 'FAIL'} {label}"
          + ("" if ok else f"\n         got={got!r}\n        want={want!r}"))
    if ok:
        PASS += 1
    else:
        FAIL += 1


def make_key() -> bytes:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537,
                                   key_size=fake_bank.TEST_KEY_BITS)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())


db.init_db()
PRIVATE_KEY = make_key()

# ---------------------------------------------------------------------------
print("\n1. The JWT is what Enable Banking expects")
# ---------------------------------------------------------------------------
token = eb.mint_jwt(fake_bank.APP_ID, PRIVATE_KEY)
head_b64, payload_b64, sig_b64 = token.split(".")


def _unb64(s):
    return json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))


header, payload = _unb64(head_b64), _unb64(payload_b64)
check("signed RS256", header["alg"], "RS256")
check("the application id travels as 'kid'", header["kid"], fake_bank.APP_ID)
check("issuer", payload["iss"], "enablebanking.com")
check("audience", payload["aud"], "api.enablebanking.com")
check("it expires", payload["exp"] > payload["iat"], True)

# The signature has to actually verify — a JWT with the right claims and
# a broken signature fails at the API as a bare 401 naming nothing.
from cryptography.hazmat.primitives import hashes, serialization      # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding         # noqa: E402
pub = serialization.load_pem_private_key(PRIVATE_KEY, password=None).public_key()
sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
try:
    pub.verify(sig, f"{head_b64}.{payload_b64}".encode(),
               padding.PKCS1v15(), hashes.SHA256())
    verified = True
except Exception:
    verified = False
check("the signature verifies against the public key", verified, True)

# ---------------------------------------------------------------------------
print("\n2. Talking to the bank (fake transport)")
# ---------------------------------------------------------------------------
bank = fake_bank.FakeBank()
client = eb.Client(fake_bank.APP_ID, PRIVATE_KEY, transport=bank.transport)

banks = client.aspsps("DE")
check("DKB is in the German list", any(b["name"] == "DKB" for b in banks), True)
check("the country went in the query", bank.calls[-1]["params"]["country"], "DE")
check("the JWT is sent as a bearer token",
      bank.calls[-1]["headers"]["Authorization"].startswith("Bearer ey"), True)

auth_resp = client.start_auth(aspsp_name="DKB", aspsp_country="DE",
                              redirect_url="http://localhost:8000/connect/callback",
                              state="teststate")
body = bank.calls[-1]["body"]
check("the bank is named in the auth request", body["aspsp"],
      {"name": "DKB", "country": "DE"})
check("state is round-tripped", body["state"], "teststate")
check("a consent window is requested",
      "valid_until" in body["access"], True)
check("we get a URL to send the user to",
      auth_resp["url"].startswith("https://"), True)

# One JWT is reused rather than re-signed per call.
signed = {c["headers"]["Authorization"] for c in bank.calls}
check("the JWT is minted once and reused", len(signed), 1)

# ---------------------------------------------------------------------------
print("\n3. Errors say what went wrong")
# ---------------------------------------------------------------------------
bank.fail_next = (401, "invalid signature")
try:
    client.application()
    err = None
except eb.EnableBankingError as exc:
    err = exc
check("an API error raises", err is not None, True)
check("...carrying the status", getattr(err, "status", None), 401)
check("...and the body, which is where the real reason is",
      "invalid signature" in str(err), True)

# ---------------------------------------------------------------------------
print("\n4. Choosing a balance")
# ---------------------------------------------------------------------------
picked = eb.pick_balance(fake_bank.BALANCES_RESPONSE)
check("interim-available wins over booked", picked["amount"], 1428.55)
check("...and is labelled", picked["balance_type"], "ITAV")
check("the reference date is kept", picked["as_of"], "2026-09-08")
check("no balances at all is None, not zero",
      eb.pick_balance({"balances": []}), None)
check("an unparseable amount is None, not 0.0",
      eb.pick_balance({"balances": [
          {"balance_type": "ITAV", "balance_amount": {"amount": "n/a"}}]}), None)

# ---------------------------------------------------------------------------
print("\n5. Reading a transaction")
# ---------------------------------------------------------------------------
rows = [eb.normalise_transaction(t, "idhash0001")
        for t in fake_bank.TRANSACTIONS_PAGE_1["transactions"]]
check("a pending entry is skipped", rows[2], None)

debit = rows[0]
check("DBIT is stored negative", debit["amount"], -42.90)
check("the description is collapsed to one line",
      debit["description"], "REWE SAGT DANKE 25873946")
check("on a debit the counterparty is the creditor",
      debit["counterparty"], "REWE Markt GmbH")
check("the id uses the bank's own reference",
      debit["external_id"], "eb:idhash0001:DKB-2026-09-08-0001")

credit = rows[1]
check("CRDT is stored positive", credit["amount"], 3200.00)
check("on a credit the counterparty is the debtor",
      credit["counterparty"], "Arbeitgeber GmbH")

page2 = [eb.normalise_transaction(t, "idhash0001", default_currency="EUR")
         for t in fake_bank.TRANSACTIONS_PAGE_2["transactions"]]
check("currency 'XXX' falls back to the account's", page2[0]["currency"], "EUR")
check("a row with no reference gets a hashed id",
      page2[0]["external_id"].startswith("eb:idhash0001:h:"), True)
check("a missing direction keeps the amount's own sign",
      page2[1]["amount"], -25.0)

# The id must be namespaced per account, or the same €4.20 coffee on the
# same day at two accounts of one bank collides and one silently vanishes.
same_txn = fake_bank.TRANSACTIONS_PAGE_2["transactions"][0]
check("ids at different accounts differ",
      eb.external_id(same_txn, "idhash0001") != eb.external_id(same_txn, "idhash0002"),
      True)
check("the same row hashes the same twice",
      eb.external_id(same_txn, "idhash0001"), eb.external_id(same_txn, "idhash0001"))

# ---------------------------------------------------------------------------
print("\n6. Pagination")
# ---------------------------------------------------------------------------
bank2 = fake_bank.FakeBank()
client2 = eb.Client(fake_bank.APP_ID, PRIVATE_KEY, transport=bank2.transport)
all_txns = list(client2.all_transactions("acct-uid-0001"))
check("both pages are walked", len(all_txns), 5)
check("the longest history is requested",
      bank2.calls[0]["params"]["strategy"], "longest")
check("only booked entries are asked for",
      bank2.calls[0]["params"]["transaction_status"], "BOOK")


class LoopingBank(fake_bank.FakeBank):
    """A bank that keeps handing back the same continuation key."""

    def transport(self, method, url, headers, body):
        super().transport(method, url, headers, body)
        return 200, json.dumps({"transactions": [{"entry_reference": "x",
                                                  "booking_date": "2026-01-01",
                                                  "status": "BOOK",
                                                  "transaction_amount": {"amount": "1", "currency": "EUR"}}],
                                "continuation_key": "same"}).encode()


looper = LoopingBank()
list(eb.Client(fake_bank.APP_ID, PRIVATE_KEY, transport=looper.transport)
     .all_transactions("acct-uid-0001"))
check("a repeated continuation key stops instead of looping for ever",
      len(looper.calls) < 5, True)

# ---------------------------------------------------------------------------
print("\n7. Users and passwords")
# ---------------------------------------------------------------------------
uid = auth.create_user("alex", "a-good-password")
check("a user is created", uid > 0, True)
check("the password is not stored in the clear",
      "a-good-password" not in settings.DB_PATH.read_bytes().decode("latin-1"), True)
check("the right password verifies",
      (auth.verify("alex", "a-good-password") or {}).get("username"), "alex")
check("a wrong password does not", auth.verify("alex", "nope"), None)
check("an unknown user does not", auth.verify("nobody", "whatever"), None)
check("the username is case-insensitive",
      (auth.verify("ALEX", "a-good-password") or {}).get("username"), "alex")

for bad, why in [("", "a username is required"),
                 ("bob", "a short password is refused")]:
    try:
        auth.create_user(bad, "short" if bad else "a-good-password")
        raised = False
    except ValueError:
        raised = True
    check(why, raised, True)

try:
    auth.create_user("alex", "another-password")
    dupe = False
except ValueError:
    dupe = True
check("a duplicate username is refused", dupe, True)

check("a protocol-relative 'next' is not followed",
      auth.safe_next("//evil.example"), "/")
check("an absolute URL is not followed",
      auth.safe_next("https://evil.example"), "/")
check("a real path is kept", auth.safe_next("/accounts/3"), "/accounts/3")

# ---------------------------------------------------------------------------
print("\n8. The whole flow, through the web app")
# ---------------------------------------------------------------------------
from app.main import app as flask_app                    # noqa: E402

flask_app.config["TESTING"] = True
c = flask_app.test_client()

r = c.get("/accounts/new")
check("before signing in, a page redirects to login", r.status_code, 302)
r = c.post("/login", data={"username": "alex", "password": "a-good-password"})
check("signing in works", r.status_code, 302)

r = c.post("/accounts/new", data={"name": "DKB Girokonto", "type": "bank",
                                  "currency": "EUR"})
check("an account can be created", r.status_code, 302)
account_id = int(r.headers["Location"].rstrip("/").split("/")[-1])

r = c.get(f"/accounts/{account_id}")
check("its page renders", r.status_code, 200)
check("...and says it is not connected yet",
      b"not connected to a bank" in r.data, True)
check("...and points at Settings, because there are no credentials yet",
      b"Application ID and private key" in r.data, True)

banksync.save_credentials(fake_bank.APP_ID, PRIVATE_KEY.decode())
check("credentials are stored", banksync.credentials_present(), True)
key_mode = oct((settings.SECRETS_DIR / banksync.KEY_FILE).stat().st_mode)[-3:]
check("the private key is not world-readable", key_mode, "600")

try:
    banksync.save_credentials(fake_bank.APP_ID, "ssh-rsa AAAAB3Nza...")
    rejected = False
except ValueError as exc:
    rejected = "private key" in str(exc).lower()
check("junk in the key box is caught", rejected, True)

# The most likely mistake by far: pasting the half you uploaded to them.
try:
    banksync.save_credentials(
        fake_bank.APP_ID,
        "-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----")
    rejected = False
except ValueError as exc:
    rejected = "PUBLIC half" in str(exc)
check("the public half is named as the mistake it is", rejected, True)

try:
    banksync.save_credentials("", PRIVATE_KEY.decode())
    rejected = False
except ValueError as exc:
    rejected = "Application ID" in str(exc)
check("a missing Application ID is refused", rejected, True)

# Point the app's client at the fake for the rest of the flow.
shared = fake_bank.FakeBank()
banksync.client = lambda: eb.Client(fake_bank.APP_ID, PRIVATE_KEY,
                                    transport=shared.transport)

r = c.get(f"/connect/{account_id}?country=DE")
check("the bank picker lists DKB", b"DKB" in r.data, True)
r = c.get(f"/connect/{account_id}?country=DE&q=dkb")
check("search narrows it", r.data.count(b"Deutsche Bank"), 0)

r = c.get(f"/connect/{account_id}?country=DE")
check("sandbox banks are marked", b"sandbox</span>" in r.data, True)
check("...and recommended before a real one",
      b"<strong>Connect a sandbox bank first.</strong>" in r.data, True)
check("...and listed first, before the real banks",
      r.data.index(b"Mock ASPSP") < r.data.index(b"Deutsche Bank"), True)

r = c.post(f"/connect/{account_id}/start",
           data={"aspsp_name": "DKB", "aspsp_country": "DE"})
check("starting the connection redirects to the bank",
      r.headers["Location"], fake_bank.AUTH_RESPONSE["url"])

with db.get_conn() as conn:
    state_row = conn.execute("SELECT * FROM auth_states").fetchone()
check("the pending connection was written down before leaving",
      state_row["aspsp_name"], "DKB")

r = c.get(f"/connect/callback?code=THE-CODE&state={state_row['state']}",
          follow_redirects=False)
check("the callback lands back on the account",
      r.headers["Location"], f"/accounts/{account_id}")
with db.get_conn() as conn:
    link = conn.execute("SELECT * FROM bank_links").fetchone()
    txns = conn.execute("SELECT * FROM transactions ORDER BY txn_date").fetchall()
    bal = conn.execute("SELECT * FROM balances").fetchall()
    states = conn.execute("SELECT COUNT(*) n FROM auth_states").fetchone()["n"]

check("the account is now linked", link["aspsp_name"], "DKB")
check("...to the right bank account", link["account_uid"], "acct-uid-0001")
check("...with the consent expiry recorded",
      link["valid_until"], "2027-01-01T00:00:00+00:00")
check("the used state is consumed", states, 0)
check("the first sync ran and stored the balance", len(bal), 1)
check("...choosing the available balance", bal[0]["amount"], 1428.55)
check("four booked transactions were imported", len(txns), 4)
check("...and the pending one was not",
      any(t["amount"] == -12.0 for t in txns), False)

r = c.post(f"/accounts/{account_id}/sync", follow_redirects=True)
with db.get_conn() as conn:
    after = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
check("syncing again imports nothing new — the ids dedupe", after, 4)
check("...and says so", b"Imported 0 new" in r.data, True)

r = c.get("/")
check("the overview renders", r.status_code, 200)
check("...with a net worth headline", b"Net worth" in r.data, True)
check("...counting the synced balance into it", b"428.55" in r.data, True)
check("...and listing the account", b"DKB Girokonto" in r.data, True)
check("the accounts page renders", c.get("/accounts").status_code, 200)

# base.html silently drops a child's {% block scripts %} if it has no
# matching block. The page renders perfectly and nothing happens — the
# charts were dead exactly this way and no status code showed it.
for tpl in sorted(pathlib.Path("app/templates").glob("*.html")):
    if tpl.name == "base.html":
        continue
    body = tpl.read_text()
    for block in ("scripts", "head"):
        if "{% block " + block + " %}" in body:
            check(f"base.html renders the {block!r} block {tpl.name} defines",
                  "{% block " + block + " %}" in
                  (pathlib.Path("app/templates/base.html").read_text()), True)

r = c.get("/")
check("the overview's chart code reaches the page",
      b"donut('chart-class'" in r.data, True)
# At this point in the run only the synced bank balance exists; the
# broker imports come later. So "Cash" is what must be in the chart data.
check("...carrying real data, not an empty array",
      b'"Cash"' in r.data, True)

# A stale or replayed callback must not silently attach to something.
r = c.get("/connect/callback?code=X&state=not-a-real-state", follow_redirects=True)
check("an unknown state is refused",
      b"not one this app started" in r.data, True)

# ---------------------------------------------------------------------------
print("\n8b. Finishing by hand when the callback cannot fire")
# ---------------------------------------------------------------------------
from app.main import _parse_pasted_redirect as parse            # noqa: E402

check("a full redirect URL", parse("https://example.org/cb?code=AAA&state=BBB"),
      ("AAA", "BBB"))
check("...with other parameters around it",
      parse("https://example.org/cb?foo=1&code=AAA&state=BBB&bar=2"), ("AAA", "BBB"))
check("...and a fragment on the end",
      parse("https://example.org/cb?code=AAA&state=BBB#done"), ("AAA", "BBB"))
check("a bare query string", parse("code=AAA&state=BBB"), ("AAA", "BBB"))
check("a URL-encoded code is decoded", parse("https://x/cb?code=A%2FB&state=S"),
      ("A/B", "S"))
check("just the code, no state", parse("AAA"), ("AAA", None))
check("nothing pasted", parse(""), (None, None))
check("a sentence is not a code", parse("it did not work"), (None, None))
check("a URL with no code at all",
      parse("https://example.org/cb?error=access_denied"), (None, None))

# The real flow: start a connection, never let the callback fire, finish
# it from the paste page instead.
with db.get_conn() as conn:
    conn.execute("DELETE FROM bank_links")
    conn.execute("DELETE FROM transactions")
    conn.execute("DELETE FROM balances")
    cur = conn.execute("INSERT INTO accounts (name, type, currency) "
                       "VALUES ('Second DKB', 'bank', 'EUR')")
    second_id = int(cur.lastrowid)

c.post(f"/connect/{second_id}/start",
       data={"aspsp_name": "DKB", "aspsp_country": "DE"})
with db.get_conn() as conn:
    st = conn.execute("SELECT state FROM auth_states").fetchone()["state"]

r = c.get("/connect/paste")
check("the paste page lists what is waiting", b"DKB" in r.data, True)

r = c.post("/connect/paste", data={"pasted": "this is not a url"},
           follow_redirects=True)
check("junk is refused with an instruction",
      b"Paste the whole URL" in r.data, True)

r = c.post("/connect/paste",
           data={"pasted": f"https://example.org/dead?code=THE-CODE&state={st}"},
           follow_redirects=False)
check("a pasted URL finishes the connection",
      r.headers["Location"], f"/accounts/{second_id}")
with db.get_conn() as conn:
    linked = conn.execute("SELECT COUNT(*) n FROM bank_links").fetchone()["n"]
    imported = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
check("...and links the account", linked, 1)
check("...and syncs it, exactly as the callback would", imported, 4)

r = c.get("/connect/paste")
check("nothing is left waiting afterwards",
      b"No connection is waiting" in r.data, True)

# ---------------------------------------------------------------------------
print("\n8c. Editing and deleting an account")
# ---------------------------------------------------------------------------
r = c.post("/accounts/new", data={"name": "Typo Acount", "type": "bank",
                                  "currency": "EUR"})
spare_id = int(r.headers["Location"].rstrip("/").split("/")[-1])

r = c.post(f"/accounts/{spare_id}/edit",
           data={"name": "Renamed", "type": "broker", "currency": "chf"},
           follow_redirects=True)
check("an account can be renamed and retyped", b"Renamed" in r.data, True)
with db.get_conn() as conn:
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (spare_id,)).fetchone()
check("...the type is stored", row["type"], "broker")
check("...and the currency is upper-cased", row["currency"], "CHF")

# An empty account is the one you made with a typo thirty seconds ago.
# It goes on one click: no warning, and nothing to type.
r = c.get(f"/accounts/{spare_id}/edit")
check("an empty account is not asked to be typed out",
      b"to confirm" in r.data, False)
check("...and says why there is nothing to confirm",
      b"holds nothing" in r.data, True)

r = c.post(f"/accounts/{spare_id}/delete", data={}, follow_redirects=True)
check("an empty account deletes on one click", b"Deleted Renamed" in r.data, True)
with db.get_conn() as conn:
    gone = conn.execute("SELECT COUNT(*) n FROM accounts WHERE id = ?",
                        (spare_id,)).fetchone()["n"]
check("...and it is gone", gone, 0)

# An account holding anything is confirmed by typing the name, not by a
# dialog. A dialog is clicked through without reading; a name cannot be
# typed by accident.
r = c.post("/accounts/new", data={"name": "Has History", "type": "bank",
                                  "currency": "EUR"})
held_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, external_id, txn_date, "
                 "amount, currency, description, kind) "
                 "VALUES (?, 'test-1', '2026-01-02', -12.50, 'EUR', 'A shop', "
                 "'withdrawal')",
                 (held_id,))

r = c.get(f"/accounts/{held_id}/edit")
# Tags and Jinja's whitespace out, so the check is on the sentence a
# person reads rather than on the markup it happens to arrive in.
warning = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "",
                 r.get_data(as_text=True)[r.get_data(as_text=True).index('id="delete"'):]))
check("an account with history warns before it is deleted",
      "cannot be undone" in warning, True)
check("...counting what goes with it", "removes 1 transaction." in warning, True)
check("...and counting it in the singular",
      "1 transactions" in warning, False)

r = c.post(f"/accounts/{held_id}/delete", data={"confirm": "wrong"},
           follow_redirects=True)
check("a mistyped confirmation does not delete", b"Type the account name" in r.data, True)
with db.get_conn() as conn:
    still = conn.execute("SELECT COUNT(*) n FROM accounts WHERE id = ?",
                         (held_id,)).fetchone()["n"]
check("...the account is still there", still, 1)

# The decision is made from the database, never from the form: a hidden
# field claiming the account is empty is a field anybody can send.
r = c.post(f"/accounts/{held_id}/delete", data={"empty": "1", "confirm": ""},
           follow_redirects=True)
with db.get_conn() as conn:
    still = conn.execute("SELECT COUNT(*) n FROM accounts WHERE id = ?",
                         (held_id,)).fetchone()["n"]
check("...and the form cannot claim it is empty", still, 1)

r = c.post(f"/accounts/{held_id}/delete", data={"confirm": "Has History"},
           follow_redirects=True)
check("the right name deletes it", b"Deleted Has History" in r.data, True)
with db.get_conn() as conn:
    gone = conn.execute("SELECT COUNT(*) n FROM accounts WHERE id = ?",
                        (held_id,)).fetchone()["n"]
    orphans = conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ?",
                           (held_id,)).fetchone()["n"]
check("...and it is gone", gone, 0)
check("...taking its transactions with it", orphans, 0)

# ---------------------------------------------------------------------------
print("\n9. When the bank fails")
# ---------------------------------------------------------------------------
# The connection now lives on the account finished by hand in 8b, which
# is the point: the two paths produce the same thing.
shared.fail_next = (403, "consent expired")
result = banksync.sync_account(second_id)
check("a failed sync reports the error", "consent expired" in result["error"], True)
with db.get_conn() as conn:
    kept = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
    stored = conn.execute("SELECT last_error FROM bank_links").fetchone()["last_error"]
check("...keeps the history it already had", kept, 4)
check("...and records it on the link, not as a broken page",
      "consent expired" in stored, True)
r = c.get(f"/accounts/{second_id}")
check("the account page still renders", r.status_code, 200)
check("...and shows the error", b"consent expired" in r.data, True)

check("an expired consent is reported in days",
      banksync.days_until_expiry("2020-01-01T00:00:00+00:00") < 0, True)
check("no expiry date is unknown, not expired",
      banksync.days_until_expiry(None), None)

# ---------------------------------------------------------------------------
print("\n9b. Upgrading a database made by an older version")
# ---------------------------------------------------------------------------
# Reported from a real install: starting the new version against a v0.1
# database died with `sqlite3.OperationalError: no such column: isin`.
# CREATE TABLE IF NOT EXISTS is a no-op on a table that already exists, so
# the old columns stayed — and the new index naming a new column ran
# before the migration that adds it. Tables, then columns, then indexes.
import sqlite3 as _sqlite3                                            # noqa: E402

OLD_DB = TMP / "v0_1.db"
_old = _sqlite3.connect(OLD_DB)
_old.executescript("""
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL, salt TEXT NOT NULL, rounds INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'bank', currency TEXT NOT NULL DEFAULT 'EUR',
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE bank_links (id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'enablebanking', aspsp_name TEXT NOT NULL,
  aspsp_country TEXT NOT NULL, session_id TEXT, account_uid TEXT,
  identification_hash TEXT, iban TEXT, valid_until TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')), last_sync_at TEXT, last_error TEXT);
CREATE TABLE auth_states (state TEXT PRIMARY KEY, account_id INTEGER,
  aspsp_name TEXT NOT NULL, aspsp_country TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
-- The v0.1 transactions table: no kind, no isin, no quantity.
CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  txn_date TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', counterparty TEXT,
  amount REAL NOT NULL, currency TEXT NOT NULL, external_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE balances (id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  amount REAL NOT NULL, currency TEXT NOT NULL, balance_type TEXT,
  as_of TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')));
""")
_old.execute("INSERT INTO accounts (name) VALUES ('Kept')")
_old.execute("INSERT INTO transactions (account_id, txn_date, amount, currency, "
             "external_id) VALUES (1, '2026-01-01', -5.0, 'EUR', 'old-row-1')")
_old.commit()
_old.close()

try:
    db.init_db(OLD_DB)
    upgraded, why = True, ""
except Exception as exc:                                              # noqa: BLE001
    upgraded, why = False, str(exc)
check("an older database upgrades instead of refusing to start", upgraded, True, )
if not upgraded:
    print(f"        {why}")

_chk = _sqlite3.connect(OLD_DB)
cols = {r[1] for r in _chk.execute("PRAGMA table_info(transactions)")}
check("...the new columns are there", {"kind", "isin", "quantity", "source"} <= cols, True)
idx = {r[0] for r in _chk.execute(
    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='transactions'")}
check("...and the index on the new column too", "idx_txn_isin" in idx, True)
check("...the data that was already there survived",
      _chk.execute("SELECT COUNT(*) FROM transactions").fetchone()[0], 1)
check("...with a default kind rather than NULL",
      _chk.execute("SELECT kind FROM transactions").fetchone()[0], "other")
check("...and running it a second time is a no-op",
      (db.init_db(OLD_DB), True)[1], True)
_chk.close()

# ---------------------------------------------------------------------------
print("\n10. Reading numbers and dates out of a European export")
# ---------------------------------------------------------------------------
from app.importers.base import parse_date, parse_decimal, find_isin   # noqa: E402

check("European decimal comma", parse_decimal("-40,80"), -40.80)
check("European thousands and decimal", parse_decimal("1.234,56"), 1234.56)
check("English thousands and decimal", parse_decimal("1,234.56"), 1234.56)
check("a small European price", parse_decimal("0,011"), 0.011)
check("Swiss apostrophe thousands", parse_decimal("1'234.50"), 1234.50)
check("parentheses mean negative", parse_decimal("(25,00)"), -25.0)
check("blank is None, not zero", parse_decimal(""), None)
check("text is None, not zero", parse_decimal("n/a"), None)

check("ISO date", parse_date("2026-05-01"), "2026-05-01")
check("day-first date", parse_date("24-04-2026"), "2026-04-24")
check("an ISO timestamp", parse_date("2026-05-01T03:49:10.717832Z"), "2026-05-01")
check("nonsense is None", parse_date("last Tuesday"), None)

check("an ISIN is found in free text",
      find_isin("Achat 71 iShares (IE00B4L5Y983)"), "IE00B4L5Y983")
check("a ticker is not mistaken for one", find_isin("AAPL"), None)

# ---------------------------------------------------------------------------
print("\n11. Degiro")
# ---------------------------------------------------------------------------
import fixtures                                                       # noqa: E402
from app import importers                                             # noqa: E402
from app.importers import degiro, trade_republic                      # noqa: E402

check("the file is recognised without being told",
      importers.sniff(fixtures.DEGIRO_CSV).SLUG, "degiro")
check("a Trade Republic file is not mistaken for it",
      importers.sniff(fixtures.TRADE_REPUBLIC_CSV).SLUG, "trade_republic")
check("an unrelated CSV matches nothing",
      importers.sniff(fixtures.NOT_A_BROKER_CSV), None)

d = degiro.parse(fixtures.DEGIRO_CSV)
check("no line was unreadable", d.problems, [])
check("every row was read", len(d.rows), 11)



def find_row(rows, needle):
    """Look a row up by a phrase in its description. Slicing the
    description to a fixed width instead makes the test fragile against
    its own arithmetic rather than against the parser."""
    for r in rows:
        if needle.lower() in r.description.lower():
            return r
    raise AssertionError(f"no row containing {needle!r}")


buy = find_row(d.rows, "Achat 71 iShares")
check("a purchase is a buy", buy.kind, "buy")
check("...the amount is the cash that left", buy.amount, -7987.50)
check("...the quantity comes out of the description", buy.quantity, 71.0)
check("...and the price from after the @", buy.price, 112.5)
check("...with the ISIN from its own column", buy.isin, "IE00B4L5Y983")

sell = find_row(d.rows, "Vente 1 Norwest")
check("a sale is a sell", sell.kind, "sell")
check("...and its quantity is negative", sell.quantity, -1.0)

check("a broker fee is a fee", find_row(d.rows, "Frais DEGIRO de courtage").kind, "fee")
check("a dividend is a dividend", find_row(d.rows, "Dividende").kind, "dividend")
check("withholding tax is tax, not a fee",
      find_row(d.rows, "Impôts sur dividende").kind, "tax")
check("a deposit is a deposit", find_row(d.rows, "Dépôt flatex").kind, "deposit")
check("a cash sweep is internal, not a withdrawal",
      find_row(d.rows, "Cash Sweep").kind, "transfer")
check("an FX conversion is not counted as a fee",
      find_row(d.rows, "Opération de change").kind, "other")

# The header has two blank column names. A DictReader collapses them and
# the balance silently overwrites the amount.
check("the change amount is not the balance amount",
      find_row(d.rows, "Dépôt flatex").amount, 1000.00)

de = degiro.parse(fixtures.DEGIRO_CSV_GERMAN)
kinds = {r.kind for r in de.rows}
check("a German-language export parses identically", kinds, {"buy", "sell"})
check("...with the same quantity", de.rows[0].quantity, 71.0)

# A description with a raw newline in an unquoted field: one record
# arrives as two lines. The tail belongs on the row before it.
split = degiro.parse(fixtures.DEGIRO_CSV_SPLIT_LINE)
check("a record split across two lines is stitched back", len(split.rows), 1)
check("...and nothing is reported as a problem", split.problems, [])
check("...with the whole description",
      split.rows[0].description.endswith("(New York Stock Exchange - NSY)"), True)
check("...and the amount intact", split.rows[0].amount, -2.50)

bad = degiro.parse(fixtures.NOT_A_BROKER_CSV)
check("a foreign file is refused, not half-parsed", bad.rows, [])
check("...and says what it expected", "Degiro Account.csv" in bad.problems[0], True)

# ---------------------------------------------------------------------------
print("\n12. Trade Republic")
# ---------------------------------------------------------------------------
tr = trade_republic.parse(fixtures.TRADE_REPUBLIC_CSV)
check("no line was unreadable", tr.problems, [])
check("every row was read", len(tr.rows), 6)
by_id = {r.external_id: r for r in tr.rows}

b = by_id["tr:22222222-2222-2222-2222-222222222222"]
check("a buy is a buy", b.kind, "buy")
check("...the amount is already signed by the broker", b.amount, -1500.00)
check("...`symbol` is really an ISIN", b.isin, "IE00BK5BQT80")
check("...fractional shares survive", b.quantity, 44.709388)
check("...and the fee is kept", b.fee, 1.0)

s = by_id["tr:33333333-3333-3333-3333-333333333333"]
check("a sale is a sell", s.kind, "sell")
check("...with a negative quantity", s.quantity, -5.0)

check("interest is interest",
      by_id["tr:11111111-1111-1111-1111-111111111111"].kind, "interest")
check("a top-up is a deposit",
      by_id["tr:44444444-4444-4444-4444-444444444444"].kind, "deposit")
div = by_id["tr:55555555-5555-5555-5555-555555555555"]
check("a dividend is a dividend", div.kind, "dividend")
check("...and its withholding tax is kept", div.tax, -1.90)

unknown = by_id["tr:66666666-6666-6666-6666-666666666666"]
check("an unknown type is not dropped", unknown is not None, True)
check("...it is classified by its category instead", unknown.kind, "buy")
check("...and the broker's own word is preserved",
      "[SOMETHING_NEW]" in unknown.description, True)

# A file that has been through Excel or Numbers: every line wrapped in one
# pair of quotes. Parsed naively it is a one-column file, and the import
# is refused for a file that plainly is the right export.
mangled = fixtures.TRADE_REPUBLIC_CSV_SPREADSHEET_MANGLED
check("a spreadsheet-mangled export is still recognised",
      importers.sniff(mangled).SLUG, "trade_republic")
tr_m = trade_republic.parse(mangled)
check("...and parses to the same rows", len(tr_m.rows), len(tr.rows))
check("...with the same ids",
      {r.external_id for r in tr_m.rows}, {r.external_id for r in tr.rows})

# ---------------------------------------------------------------------------
print("\n12b. DKB")
# ---------------------------------------------------------------------------
from app.importers import dkb                                         # noqa: E402

for name in ("DKB_CSV_GIRO", "DKB_CSV_GIRO_OLD", "DKB_CSV_VISA", "DKB_CSV_VISA_OLD"):
    raw = getattr(fixtures, name)
    raw = raw if isinstance(raw, bytes) else raw.encode()
    check(f"{name.lower()} is recognised without being told",
          importers.sniff(raw).SLUG, "dkb")

g = dkb.parse(fixtures.DKB_CSV_GIRO)
check("every booked row was read", len(g.rows), 7)
check("the pending row is listed, not imported",
      [p for p in g.problems if "pending" in p and "line 6" in p] != [], True)
check("...and nothing else is a problem", len(g.problems), 1)
check("the balance comes from the preamble",
      g.closing_balance, {"amount": 3210.55, "currency": "EUR", "as_of": "2026-08-25"})

coffees = [r for r in g.rows if "KAFFEEBAR" in (r.counterparty or "")]
check("two identical lines are two rows", len(coffees), 2)
check("...with different ids", coffees[0].external_id != coffees[1].external_id, True)
check("...both negative, with the € stripped", {r.amount for r in coffees}, {-3.40})
check("the counterparty of an outgoing row is the payee",
      coffees[0].counterparty, "KAFFEEBAR AM MARKT//BERLIN/DE")
salary = find_row(g.rows, "LOHN 08/2026")
check("salary is a deposit", salary.kind, "deposit")
check("...whose counterparty is the payer", salary.counterparty, "Some Company GmbH")
check("...with the thousands separator understood", salary.amount, 2345.67)
check("the card settlement is a transfer, not spending",
      find_row(g.rows, "Kreditkartenabrechnung").kind, "transfer")
check("interest is interest", find_row(g.rows, "Zinsen").kind, "interest")
check("the account fee is a fee", find_row(g.rows, "Kontoführung").kind, "fee")
check("rent is nothing in particular", find_row(g.rows, "Miete").kind, "other")
check("a two-digit year lands in the right century",
      find_row(g.rows, "Miete").txn_date, "2026-08-15")

# The overlapping export two weeks later. The ids must line up so that
# only the newly booked row and the genuinely new one count as new.
g2 = dkb.parse(fixtures.DKB_CSV_GIRO_OVERLAPPING)
new_ids = {r.external_id for r in g2.rows} - {r.external_id for r in g.rows}
check("an overlapping export shares its ids with the first", len(new_ids), 2)
check("...and the balance moves with it", g2.closing_balance["as_of"], "2026-09-08")

old = dkb.parse(fixtures.DKB_CSV_GIRO_OLD)
check("the pre-2023 layout parses", len(old.rows), 2)
check("...with no problems", old.problems, [])
check("...its Latin-1 umlauts intact",
      find_row(old.rows, "Brötchen").counterparty, "BÄCKEREI SCHÖN")
check("...the booking text kept on the row",
      "[Lastschrift]" in find_row(old.rows, "Brötchen").description, True)
check("...its salary booking text understood",
      find_row(old.rows, "Gehalt Oktober").kind, "deposit")
check("...and its balance read",
      old.closing_balance, {"amount": 1234.56, "currency": "EUR", "as_of": "2018-10-20"})

v = dkb.parse(fixtures.DKB_CSV_VISA)
check("the card export parses", len(v.rows), 4)
check("a card purchase is spending", find_row(v.rows, "HOTEL BELLA").kind, "other")
check("...dated when it happened, not when it settled",
      find_row(v.rows, "HOTEL BELLA").txn_date, "2026-08-28")
check("the monthly settlement is a transfer",
      find_row(v.rows, "Ausgleich Kreditkarte").kind, "transfer")
check("the card fee is a fee", find_row(v.rows, "Kartenpreis").kind, "fee")
check("a negative card balance is read as such",
      v.closing_balance, {"amount": -42.0, "currency": "EUR", "as_of": "2026-08-30"})

vo = dkb.parse(fixtures.DKB_CSV_VISA_OLD)
check("the pre-2023 card layout parses", len(vo.rows), 2)
check("...using the receipt date", find_row(vo.rows, "SOME WEBSHOP").txn_date, "2018-10-01")
check("...with the balance date from its own line",
      vo.closing_balance, {"amount": 12345.67, "currency": "EUR", "as_of": "2018-10-19"})
check("...and credit interest as interest", find_row(vo.rows, "HABENZINSEN").kind, "interest")

bad = dkb.parse(fixtures.NOT_A_BROKER_CSV)
check("a foreign file is refused, not half-parsed", bad.rows, [])
check("...and says what it expected", "DKB" in bad.problems[0], True)

# ---------------------------------------------------------------------------
print("\n12c. DKB Wertpapierabrechnung PDFs")
# ---------------------------------------------------------------------------
from app.importers import dkb_pdf                                     # noqa: E402

kauf = dkb_pdf.parse(fixtures.DKB_PDF_KAUF)
check("a purchase statement yields one row", len(kauf.rows), 1)
check("...with no problems", kauf.problems, [])
k = kauf.rows[0]
check("...a buy", k.kind, "buy")
check("...dated on the Schlusstag", k.txn_date, "2026-03-12")
check("...for the Ausmachender Betrag, money out", k.amount, -3512.50)
check("...`Stück 2.000` is two thousand, not two", k.quantity, 2000.0)
check("...priced at Kurswert ÷ quantity", k.price, 1.75)
check("...with every fee line summed", k.fee, 12.50)
check("...and the ISIN read", k.isin, "US0000000001")
check("...and the name across both lines",
      k.security_name, "EXAMPLE HOLDINGS INC. REGISTERED SHARES DL -,01")

verkauf = dkb_pdf.parse(fixtures.DKB_PDF_VERKAUF).rows[0]
check("a sale is a sell", verkauf.kind, "sell")
check("...with money in", verkauf.amount, 1106.92)
check("...a negative quantity", verkauf.quantity, -500.0)
check("...the price from the Kurswert", verkauf.price, 2.40)
check("...and the capital gains tax summed", verkauf.tax, 83.08)

anleihe = dkb_pdf.parse(fixtures.DKB_PDF_ANLEIHE).rows[0]
check("a bond's nominal becomes nominal ÷ 100 units", anleihe.quantity, 20.0)
check("...priced in per cent", anleihe.price, 97.5)
check("...for the full amount including accrued interest", anleihe.amount, -1993.00)

div = dkb_pdf.parse(fixtures.DKB_PDF_DIVIDENDE).rows[0]
check("a dividend credit is a dividend", div.kind, "dividend")
check("...for the net amount", div.amount, 103.41)
check("...dated when the money arrived", div.txn_date, "2026-05-18")
check("...with withholding, KapSt and Soli summed as tax", div.tax, 35.48)
check("...against its ISIN", div.isin, "US0000000001")

vorab = dkb_pdf.parse(fixtures.DKB_PDF_VORABPAUSCHALE).rows[0]
check("a Vorabpauschale is a tax", vorab.kind, "tax")
check("...money out", vorab.amount, -3.82)
check("...on the fund", vorab.isin, "IE0000000002")

plan = dkb_pdf.parse(fixtures.DKB_PDF_SPARPLAN)
check("a half-year Sparplan overview yields one row per purchase", len(plan.rows), 2)
check("...each a buy for the rate plus the fee",
      [(r.kind, r.amount, r.fee) for r in plan.rows],
      [("buy", -200.49, 0.49), ("buy", -200.49, 0.49)])
check("...with units and price", (plan.rows[1].quantity, plan.rows[1].price), (2.0921, 95.6))
check("...on the Schlusstag", plan.rows[1].txn_date, "2026-03-05")
check("...for the fund named above the table", plan.rows[0].isin, "IE0000000002")

single = dkb_pdf.parse(fixtures.DKB_PDF_AUSGABE).rows[0]
check("a savings-plan run's own statement is a buy", single.kind, "buy")
check("...whose id equals the overview's line for the same order",
      single.external_id, plan.rows[1].external_id)
check("...while the other line differs", single.external_id != plan.rows[0].external_id, True)

storno = dkb_pdf.parse(fixtures.DKB_PDF_STORNO)
check("a Storno is not a trade", storno.rows, [])
check("...and is named", "Storno" in storno.problems[0], True)
auszug = dkb_pdf.parse(fixtures.DKB_PDF_KONTOAUSZUG)
check("a Kontoauszug PDF is refused with a pointer to the CSV",
      "CSV" in auszug.problems[0], True)
check("an unrelated text is refused",
      "not a DKB" in dkb_pdf.parse("Dear customer, hello.").problems[0], True)

# The real PDF path: bytes in, text out, rows out.
pdf = fixtures.pdf_from_text(fixtures.DKB_PDF_KAUF)
check("a PDF is recognised by the sniffer", importers.sniff(pdf).SLUG, "dkb_pdf")
check("...and parses to the same row", dkb_pdf.parse(pdf).rows[0], k)
check("a PDF nobody wrote for us is not recognised",
      importers.sniff(fixtures.pdf_from_text("Dear customer, hello.")), None)

# ---------------------------------------------------------------------------
print("\n13. Importing, through the web app")
# ---------------------------------------------------------------------------
import io                                                             # noqa: E402

r = c.post("/accounts/new", data={"name": "Degiro", "type": "broker",
                                  "currency": "EUR"})
broker_id = int(r.headers["Location"].rstrip("/").split("/")[-1])


def upload(account, text, name="export.csv"):
    raw = text if isinstance(text, bytes) else text.encode()
    return c.post(f"/accounts/{account}/import",
                  data={"file": (io.BytesIO(raw), name)},
                  content_type="multipart/form-data", follow_redirects=True)


r = upload(broker_id, fixtures.NOT_A_BROKER_CSV)
check("an unrecognised file is refused",
      b"match an importer" in r.data, True)

r = upload(broker_id, fixtures.DEGIRO_CSV)
check("a Degiro export imports", b"11 new" in r.data, True)

r = upload(broker_id, fixtures.DEGIRO_CSV)
check("importing the same file twice adds nothing", b"0 new" in r.data, True)

r = upload(broker_id, fixtures.DEGIRO_CSV_OVERLAPPING)
check("an overlapping export adds only what is new", b"2 new" in r.data, True)

pos = importers.positions(broker_id)
holdings = {p["isin"]: p for p in pos}
check("the ETF is held", "IE00B4L5Y983" in holdings, True)
check("...at 71 + 4 shares", round(holdings["IE00B4L5Y983"]["quantity"], 6), 75.0)
check("...with net invested summed over both buys",
      round(holdings["IE00B4L5Y983"]["net_invested"], 2), 8439.50)
check("...priced at the most recent trade",
      holdings["IE00B4L5Y983"]["last_price"], 113.0)
check("a position bought and sold in full disappears",
      "LU0000000009" in holdings, False)
# A sale with no matching purchase is not a short position — it is an
# export that did not reach back far enough. Hiding it would hide that.
check("a sale whose purchase predates the export is still shown",
      "AU0000025280" in holdings, True)
check("...and is flagged rather than presented as a holding",
      holdings["AU0000025280"]["incomplete_history"], True)
check("...while a real holding is not flagged",
      holdings["IE00B4L5Y983"]["incomplete_history"], False)

degiro_position_count = len(pos)

r = c.get(f"/accounts/{broker_id}")
check("the account page shows the holding", b"IE00B4L5Y983" in r.data, True)
check("...and explains a negative quantity rather than hiding it",
      b"purchase is older than the file" in r.data, True)
check("...and says the price is not a market price",
      b"no price feed yet" in r.data, True)

# A second broker into its own account, to prove the ISIN is the join key
# and that nothing is shared by accident.
r = c.post("/accounts/new", data={"name": "Trade Republic", "type": "broker",
                                  "currency": "EUR"})
tr_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = upload(tr_id, fixtures.TRADE_REPUBLIC_CSV)
check("a Trade Republic export imports", b"6 new" in r.data, True)
check("it did not land in the other account",
      len(importers.positions(broker_id)), degiro_position_count)
tr_pos = {p["isin"]: p for p in importers.positions(tr_id)}
check("the Trade Republic fund is held", "IE00BK5BQT80" in tr_pos, True)
check("...and the stock nets buy minus sell",
      round(tr_pos["DE0007236101"]["quantity"], 6), -3.0)

# A bank, not a broker: the DKB file goes into a bank account, and what
# it says about the balance is recorded as the account's balance.
r = c.post("/accounts/new", data={"name": "DKB Giro", "type": "bank",
                                  "currency": "EUR"})
dkb_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = upload(dkb_id, fixtures.DKB_CSV_GIRO)
check("a DKB export imports", b"7 new" in r.data, True)
check("...and the pending row is explained on the page", b"pending" in r.data, True)
r = upload(dkb_id, fixtures.DKB_CSV_GIRO_OVERLAPPING)
check("the overlapping DKB export adds only what is new", b"2 new" in r.data, True)
with db.get_conn() as conn:
    bal = conn.execute("SELECT amount, as_of FROM balances WHERE account_id = ? "
                       "ORDER BY as_of DESC LIMIT 1", (dkb_id,)).fetchone()
    salary_cat = conn.execute(
        "SELECT category FROM transactions WHERE account_id = ? "
        "AND description LIKE 'LOHN%'", (dkb_id,)).fetchone()["category"]
check("the newest statement balance is the account balance",
      (bal["amount"], bal["as_of"]), (3140.56, "2026-09-08"))
check("salary into a bank account is income", salary_cat, "income")
r = upload(dkb_id, fixtures.DKB_CSV_GIRO_OLD, name="umsaetze.csv")
check("a Latin-1 export from the old portal imports", b"2 new" in r.data, True)

# A Depot: several statement PDFs at once, plus a ZIP of more, in one
# upload. Each is recognised on its own.
import zipfile                                                        # noqa: E402

r = c.post("/accounts/new", data={"name": "DKB Depot", "type": "broker",
                                  "currency": "EUR"})
depot_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
zbuf = io.BytesIO()
with zipfile.ZipFile(zbuf, "w") as z:
    z.writestr("Abrechnungen/Dividende.pdf", fixtures.pdf_from_text(fixtures.DKB_PDF_DIVIDENDE))
    z.writestr("Abrechnungen/Sparplan.pdf", fixtures.pdf_from_text(fixtures.DKB_PDF_SPARPLAN))
    z.writestr("Abrechnungen/Storno.pdf", fixtures.pdf_from_text(fixtures.DKB_PDF_STORNO))
    z.writestr("__MACOSX/._Dividende.pdf", b"junk")
    z.writestr("notes.txt", b"not a statement")
r = c.post(f"/accounts/{depot_id}/import", data={"file": [
    (io.BytesIO(fixtures.pdf_from_text(fixtures.DKB_PDF_KAUF)), "Kauf.pdf"),
    (io.BytesIO(fixtures.pdf_from_text(fixtures.DKB_PDF_VERKAUF)), "Verkauf.pdf"),
    (io.BytesIO(zbuf.getvalue()), "Postfach.zip"),
]}, content_type="multipart/form-data", follow_redirects=True)
check("PDFs and a ZIP of PDFs import in one go", b"5 new" in r.data, True)
check("...the Storno is named, not silently dropped", b"Storno.pdf: A Storno" in r.data, True)
check("...and the stray file is named too", b"notes.txt: not recognised" in r.data, True)
r = c.post(f"/accounts/{depot_id}/import", data={"file": [
    (io.BytesIO(fixtures.pdf_from_text(fixtures.DKB_PDF_AUSGABE)), "Ausgabe.pdf"),
]}, content_type="multipart/form-data", follow_redirects=True)
check("the single statement for a run already in the overview adds nothing",
      b"0 new, 1 already had" in r.data, True)
depot_pos = {p["isin"]: p for p in importers.positions(depot_id)}
check("the Depot holds what the statements say",
      round(depot_pos["US0000000001"]["quantity"], 6), 1500.0)
check("...and the fund from the Sparplan", round(depot_pos["IE0000000002"]["quantity"], 4), 4.2637)

# ---------------------------------------------------------------------------
print("\n14. Categories and rules")
# ---------------------------------------------------------------------------
from app import cashflow as cf, categories as cat, subscriptions as subs  # noqa: E402

check("a supermarket is guessed", cat.suggest("CARREFOUR MARKET 1234"), "food")
check("a streaming service is guessed", cat.suggest("NETFLIX.COM"), "subscription")
check("an unknown merchant is not guessed at", cat.suggest("ZQX BLORP"), None)
check("the counterparty is read too",
      cat.suggest("card payment", "Lidl Sarl"), "food")

seeded = cat.seed_from_kind()
check("the obvious rows are categorised without a human", seeded > 0, True)
with db.get_conn() as conn:
    fee_cat = conn.execute(
        "SELECT category FROM transactions WHERE kind='fee' LIMIT 1").fetchone()
check("a broker fee needs no rule", fee_cat["category"] if fee_cat else "fee", "fee")

# What a kind MEANS depends on the account. Money arriving in a broker is
# your own, from your own bank; calling it income inflates income by
# everything you have ever invested, and double-counts the bank side.
with db.get_conn() as conn:
    broker_deposits = conn.execute(
        "SELECT DISTINCT category FROM transactions t "
        " JOIN accounts a ON a.id = t.account_id "
        " WHERE t.kind = 'deposit' AND a.type = 'broker'").fetchall()
check("a deposit into a broker is an internal transfer, not income",
      {r["category"] for r in broker_deposits} <= {"transfer"}, True)

# A rule must reach what is ALREADY imported, or the same shop has to be
# fixed every month for a year before it stops.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, external_id) VALUES "
                 "(?, '2026-06-01', 'ZQX BLORP STORE 8891', -12.0, 'EUR', "
                 "'withdrawal', 'rule-test-1')", (broker_id,))
applied = cat.add_rule("zqx blorp", "shopping")
check("a new rule applies retroactively", applied >= 1, True)
with db.get_conn() as conn:
    got = conn.execute("SELECT category FROM transactions "
                       "WHERE external_id='rule-test-1'").fetchone()["category"]
check("...to the row that was already there", got, "shopping")

try:
    cat.add_rule("ab", "shopping")
    tooshort = False
except ValueError:
    tooshort = True
check("a two-character rule is refused as too broad", tooshort, True)
try:
    cat.add_rule("something", "not_a_category")
    badcat = False
except ValueError:
    badcat = True
check("an unknown category is refused", badcat, True)

# A trade must never be swept up by a spending rule: a share purchase is
# not shopping, and counting it would double it against the holding.
cat.add_rule("ishares", "shopping")
with db.get_conn() as conn:
    trades = conn.execute("SELECT COUNT(*) n FROM transactions "
                          "WHERE kind='buy' AND category='shopping'").fetchone()["n"]
check("a rule does not recategorise a trade", trades, 0)

# What a rule remembers a transaction by, when nobody typed a pattern.
check("the counterparty is the pattern when there is one",
      cat.suggest_pattern("KARTENZAHLUNG 12.06 REWE", "REWE SAGT DANKE"),
      "REWE SAGT DANKE")
check("without one, the merchant is dug out of the description",
      cat.suggest_pattern("SEPA-Lastschrift 2026-06-12 REWE MARKT GMBH 4711 Ref. 0815", None),
      "REWE MARKT GMBH")
check("...and is a substring of it, so the rule will actually match",
      "REWE MARKT GMBH" in "SEPA-Lastschrift 2026-06-12 REWE MARKT GMBH 4711 Ref. 0815", True)
check("a description that is only numbers yields no pattern",
      cat.suggest_pattern("4711 0815 2026", "  "), None)
check("a one-word merchant is enough", cat.suggest_pattern("Netflix", None), "Netflix")

# ---------------------------------------------------------------------------
print("\n14b. Categories the user owns")
# ---------------------------------------------------------------------------
slug = cat.add_category("Childcare", "#ff8800")
check("a new category gets a slug from its name", slug, "childcare")
check("...and appears in the catalogue", slug in cat.all_categories(), True)
check("...counted as spending unless told otherwise",
      slug in cat.spending(), True)

dup = False
try:
    cat.add_category("  childcare ", "#ff8800")
except ValueError:
    dup = True
check("a second category with the same name is refused", dup, True)

badcolour = False
try:
    cat.add_category("Nonsense", "puce")
except ValueError:
    badcolour = True
check("a colour that is not a hex colour is refused", badcolour, True)

# Renaming must not re-file anything: the slug is the identity, and it
# is the slug that sits on every transaction.
with db.get_conn() as conn:
    victim = conn.execute("SELECT id FROM transactions LIMIT 1").fetchone()["id"]
cat.set_category(victim, slug)
cat.update_category(slug, "Kids", "#ff9900", cat.NON_SPENDING_GROUP)
check("a rename keeps the slug", cat.label(slug), "Kids")
check("...and the new colour", cat.colour(slug), "#ff9900")
check("...and can move it out of spending", slug in cat.non_spending(), True)
with db.get_conn() as conn:
    still = conn.execute("SELECT COUNT(*) n FROM transactions "
                         "WHERE category = ?", (slug,)).fetchone()["n"]
check("...without re-filing the transactions it holds", still, 1)

renamed_onto = False
try:
    cat.update_category(slug, "Housing", "#ff9900", cat.SPENDING_GROUP)
except ValueError:
    renamed_onto = True
check("a rename onto another category's name is refused", renamed_onto, True)

# A built-in can be edited and removed too; removing it must not leave a
# transaction pointing at a category that no longer exists.
cat.update_category("food", "Food & drink", "#f5d76e", cat.SPENDING_GROUP)
check("a built-in can be renamed", cat.label("food"), "Food & drink")

cat.add_rule("kidsclub", slug)
moved = cat.delete_category(slug)
check("deleting reports what it moved", moved, 1)
check("...and the category is gone", slug in cat.all_categories(), False)
with db.get_conn() as conn:
    orphan = conn.execute("SELECT COUNT(*) n FROM transactions "
                          "WHERE category = ?", (slug,)).fetchone()["n"]
    left = conn.execute("SELECT COUNT(*) n FROM category_rules "
                        "WHERE category = ?", (slug,)).fetchone()["n"]
check("...leaving no transaction pointing at it", orphan, 0)
check("...and no rule filing into it", left, 0)

protected = False
try:
    cat.delete_category("other")
except ValueError:
    protected = True
check("the category deleted rows fall back to is itself undeletable",
      protected, True)
# Cash flow keys off `income`/`investment`/`transfer` by name, so a form
# that moves one into spending must be ignored rather than obeyed.
cat.update_category("income", "Income", "#34d399", cat.SPENDING_GROUP)
check("the three cash flow knows by name keep their group",
      "income" in cat.non_spending(), True)

check("nor can 'transfer', which is what keeps a transfer out of spending",
      any(not c["deletable"] for c in cat.catalogue() if c["slug"] == "transfer"),
      True)

cat.delete_category("education")
check("a built-in can be removed", "education" in cat.all_categories(), False)
restored = cat.add_category("Education", "#38bdf8")
check("...and adding it again revives the same slug", restored, "education")

check("the catalogue says how much each category holds",
      all("transactions" in c for c in cat.catalogue()), True)

# ---------------------------------------------------------------------------
print("\n15. Cash flow")
# ---------------------------------------------------------------------------
flow = cf.monthly(months=24)
check("months come back in order",
      [m["month"] for m in flow["months"]] == sorted(m["month"] for m in flow["months"]), True)
check("spending is reported as a positive size",
      all(m["spending"] >= 0 for m in flow["months"]), True)

# The rule the whole page rests on.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, '2026-06-02', 'To savings', -5000.0, 'EUR', 'transfer', "
                 "'transfer', 'xfer-out')", (broker_id,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, '2026-06-02', 'From current', 5000.0, 'EUR', 'transfer', "
                 "'transfer', 'xfer-in')", (broker_id,))
after = cf.monthly(months=24)
june = next((m for m in after["months"] if m["month"] == "2026-06"), None)
before_june = next((m for m in flow["months"] if m["month"] == "2026-06"), None)
check("an internal transfer is not income",
      june["income"], before_june["income"] if before_june else 0)
check("...and not spending either",
      june["spending"], before_june["spending"] if before_june else 0)

cf.set_budget("shopping", 200.0)
rep = cf.budget_report()
check("a budget is stored", rep["has_budgets"], True)
shopping = next(r for r in rep["rows"] if r["category"] == "shopping")
check("...and reported against", shopping["budget"], 200.0)
check("...with a pace, not just a total",
      shopping["expected_by_now"] is not None, True)
cf.set_budget("shopping", None)
check("a budget can be cleared", cf.budget_report()["has_budgets"], False)

# A category with nothing booked to it yet must still get a row: the
# row is the only place its budget can be typed in.
rep = cf.budget_report()
listed = {r["category"] for r in rep["rows"]}
check("every spending category has a budget row, used or not",
      set(cat.spending()) <= listed, True)
check("...and the non-spending ones do not, since nothing is ever spent there",
      listed & {"income", "investment", "transfer"}, set())

# ---------------------------------------------------------------------------
print("\n16. Subscriptions")
# ---------------------------------------------------------------------------
# Dates are computed backwards from today, not hard-coded. A fixture
# pinned to fixed dates passes today and fails in three months, when the
# "probably ended" rule starts firing on it — and the failure looks like
# a detection bug rather than a stale test.
from datetime import date as _date, timedelta as _timedelta            # noqa: E402

_today = _date.today()
_monthly_dates = [(_today - _timedelta(days=30 * i)).isoformat() for i in (4, 3, 2, 1, 0)]

with db.get_conn() as conn:
    # A monthly charge, a wandering one, and a pair. Only the first is
    # a subscription; announcing the others would make the page useless.
    for i, day in enumerate(_monthly_dates):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                     "counterparty, amount, currency, kind, category, external_id) "
                     "VALUES (?, ?, 'ABO', 'Streamly', -9.99, 'EUR', 'withdrawal', "
                     "'subscription', ?)", (broker_id, day, f"sub-{i}"))
    for i, day in enumerate([(_today - _timedelta(days=d)).isoformat()
                             for d in (190, 172, 74)]):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                     "counterparty, amount, currency, kind, category, external_id) "
                     "VALUES (?, ?, 'SHOP', 'Randomshop', ?, 'EUR', 'withdrawal', "
                     "'shopping', ?)", (broker_id, day, -20.0 - i * 35, f"rnd-{i}"))
    for i, day in enumerate([(_today - _timedelta(days=d)).isoformat()
                             for d in (60, 30)]):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                     "counterparty, amount, currency, kind, category, external_id) "
                     "VALUES (?, ?, 'PAIR', 'Twiceonly', -30.0, 'EUR', 'withdrawal', "
                     "'shopping', ?)", (broker_id, day, f"pair-{i}"))

found = subs.detect()
names = {s["name"] for s in found["confirmed"]}
check("a monthly charge is found", "Streamly" in names, True)
streamly = next(s for s in found["confirmed"] if s["name"] == "Streamly")
check("...its rhythm is named", streamly["rhythm"], "monthly")
check("...and the yearly cost follows from it",
      round(streamly["yearly"], 2), round(9.99 * 12, 2))
check("two payments are not a subscription", "Twiceonly" in names, False)
check("a wandering amount is not promoted", "Randomshop" in names, False)
check("a current subscription is not marked ended",
      streamly["likely_ended"], False)
check("the monthly total is the sum of the active ones",
      round(found["monthly_total"], 2), 9.99)

# ---------------------------------------------------------------------------
print("\n17. Every page in the nav actually renders")
# ---------------------------------------------------------------------------
for path in ["/", "/portfolio", "/cashflow", "/budget", "/subscriptions",
             "/transactions", "/categorize", "/accounts", "/settings"]:
    r = c.get(path)
    check(f"{path}", r.status_code, 200)

r = c.get("/transactions?q=ishares&category=investment")
check("the transactions filters work together", r.status_code, 200)

# Changing a category from the Transactions page — which has only the
# dropdown — must leave a rule behind, or the same shop is fixed every
# month by hand. From the Categorize page the pattern field decides.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "counterparty, amount, currency, kind, external_id) VALUES "
                 "(?, '2026-07-03', 'KARTE 4711 VELOFIX WERKSTATT 12.3', NULL, "
                 "-45.0, 'EUR', 'withdrawal', 'rule-web-1')", (broker_id,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "counterparty, amount, currency, kind, external_id) VALUES "
                 "(?, '2026-08-03', 'KARTE 4712 VELOFIX WERKSTATT 9.9', NULL, "
                 "-30.0, 'EUR', 'withdrawal', 'rule-web-2')", (broker_id,))
    web_id = conn.execute("SELECT id FROM transactions WHERE external_id="
                          "'rule-web-1'").fetchone()["id"]
rules_before = len(cat.rules())
r = c.post(f"/transactions/{web_id}/category", data={"category": "transport"},
           follow_redirects=True)
check("a category change on the Transactions page makes a rule",
      len(cat.rules()), rules_before + 1)
check("...from the merchant, not the card and reference numbers",
      cat.rules()[0]["pattern"], "VELOFIX WERKSTATT")
with db.get_conn() as conn:
    sibling = conn.execute("SELECT category FROM transactions WHERE external_id="
                           "'rule-web-2'").fetchone()["category"]
check("...and the next payment to the same shop is filed with it",
      sibling, "transport")
check("...which the page says", "VELOFIX WERKSTATT".encode() in r.data, True)

c.post(f"/transactions/{web_id}/category", data={"category": "other"})
check("filing under Uncategorised makes no rule", len(cat.rules()), rules_before + 1)

c.post(f"/transactions/{web_id}/category",
       data={"category": "shopping", "pattern": ""})
check("an emptied pattern on the Categorize page makes no rule",
      len(cat.rules()), rules_before + 1)
with db.get_conn() as conn:
    one = conn.execute("SELECT category FROM transactions WHERE external_id="
                       "'rule-web-1'").fetchone()["category"]
check("...but still corrects the one row", one, "shopping")

with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "counterparty, amount, currency, kind, external_id) VALUES "
                 "(?, '2026-08-04', 'POS 9981 20260804', 'Bakery Quorn', "
                 "-4.5, 'EUR', 'withdrawal', 'rule-web-3')", (broker_id,))
r = c.get("/categorize")
check("the queue pre-fills the pattern it would remember",
      b'value="Bakery Quorn"' in r.data, True)
r = c.get("/budget")
check("the budget page has a field for a category nobody has used yet",
      b'name="budget_education"' in r.data, True)
cf.set_budget("shopping", 200.0)
r = c.get("/budget")
check("with a budget set, the page draws budget against spent",
      b'id="chart-budget"' in r.data and b"new Chart" in r.data, True)
check("...and a pace bar on the row", b'class="pbar-fill' in r.data, True)
check("...with the three-figure summary", b"Remaining" in r.data, True)
cf.set_budget("shopping", None)
r = c.get("/transactions?account=999999")
check("an account that does not exist filters to nothing, not an error",
      r.status_code, 200)

# The seam that has broken twice: a block a page defines and base.html
# does not render is silently dropped.
base_src = pathlib.Path("app/templates/base.html").read_text()
for tpl in sorted(pathlib.Path("app/templates").glob("*.html")):
    if tpl.name == "base.html":
        continue
    for block in ("scripts", "head", "content", "heading", "lede"):
        if "{% block " + block + " %}" in tpl.read_text():
            check(f"base.html renders {block!r} for {tpl.name}",
                  "block " + block in base_src, True)

# ---------------------------------------------------------------------------
print("\n18. Managing categories from the Settings page")
# ---------------------------------------------------------------------------
r = c.get("/settings")
check("the settings page offers the category editor", b'id="categories"' in r.data, True)
import html as _html                                      # noqa: E402
check("...with every category in it",
      all(_html.escape(cc["label"]).encode() in r.data
          for cc in cat.catalogue()), True)

c.post("/settings", data={"form": "category_new", "label": "Hobbies",
                          "colour": "#123456", "group": "spending"})
check("a category can be added from the page", cat.label("hobbies"), "Hobbies")
check("...with the colour that was picked", cat.colour("hobbies"), "#123456")

c.post("/settings", data={"form": "category_edit", "slug": "hobbies",
                          "label": "Hobbies & sport", "colour": "#abcdef",
                          "group": "non_spending"})
check("...edited from the page", cat.label("hobbies"), "Hobbies & sport")
check("...and moved out of spending", "hobbies" in cat.non_spending(), True)

r = c.post("/settings", data={"form": "category_delete", "slug": "hobbies"},
           follow_redirects=True)
check("...and deleted from the page", "hobbies" in cat.all_categories(), False)

r = c.post("/settings", data={"form": "category_delete", "slug": "other"},
           follow_redirects=True)
check("deleting a load-bearing category is refused with a sentence",
      b"cannot be removed" in r.data, True)
check("...and it is still there", "other" in cat.all_categories(), True)

r = c.post("/settings", data={"form": "category_new", "label": "",
                              "colour": "#123456", "group": "spending"},
           follow_redirects=True)
check("a nameless category is refused", b"needs a name" in r.data, True)

# ---------------------------------------------------------------------------
print("\n19. Typing it in by hand")
# ---------------------------------------------------------------------------
# An account nothing reports on: no bank, no CSV. Every row and the
# balance are typed in, and they have to count exactly like imported
# ones — a purchase is a holding, a dividend is income — or the page
# is a notebook, not a dashboard.
from app import manual, overview as ov                    # noqa: E402

r = c.post("/accounts/new", data={"name": "Work share plan", "type": "broker",
                                  "currency": "EUR"})
hand_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{hand_id}")
check("an unconnected account offers to record a balance",
      b'name="as_of"' in r.data, True)
check("...and to add by hand", f"/accounts/{hand_id}/add".encode() in r.data, True)
r = c.get(f"/accounts/{hand_id}/add")
check("the entry page renders", r.status_code, 200)
check("...offering trades on a broker account", b'value="buy"' in r.data, True)

# A purchase, typed the way a German keyboard types it.
r = c.post(f"/accounts/{hand_id}/add", data={
    "kind": "buy", "txn_date": "2026-05-04", "isin": "ie00b4l5y983",
    "security_name": "iShares Core MSCI World", "quantity": "10",
    "price": "82,40", "fee": "1,00"}, follow_redirects=True)
check("a purchase is accepted", b"Added." in r.data, True)
with db.get_conn() as conn:
    buy = conn.execute("SELECT * FROM transactions WHERE account_id = ? "
                       "AND kind = 'buy'", (hand_id,)).fetchone()
check("...the ISIN is upper-cased", buy["isin"], "IE00B4L5Y983")
check("...money left the account: quantity × price plus the fee",
      round(buy["amount"], 2), -825.0)
check("...the quantity is positive on a buy", buy["quantity"], 10.0)
check("...and it says where it came from", buy["source"], "manual")
check("...with a description nobody had to type",
      "iShares" in buy["description"], True)
pos = {p["isin"]: p for p in importers.positions(hand_id)}
check("the holding exists", pos["IE00B4L5Y983"]["quantity"], 10.0)

# A sale of part of it, with the broker's own total.
c.post(f"/accounts/{hand_id}/add", data={
    "kind": "sell", "txn_date": "2026-06-10", "isin": "IE00B4L5Y983",
    "quantity": "4", "price": "90", "fee": "1", "total": "358,90"})
pos = {p["isin"]: p for p in importers.positions(hand_id)}
check("a sale reduces the holding", pos["IE00B4L5Y983"]["quantity"], 6.0)
with db.get_conn() as conn:
    sell = conn.execute("SELECT * FROM transactions WHERE account_id = ? "
                        "AND kind = 'sell'", (hand_id,)).fetchone()
check("...money came in, at the statement's total, not the arithmetic",
      sell["amount"], 358.90)
check("...and the quantity is negative on a sell", sell["quantity"], -4.0)
check("...and the holding's last price is the sale's", pos["IE00B4L5Y983"]["last_price"], 90.0)

# The rest of a broker's life: no sign to type, and no category to pick.
c.post(f"/accounts/{hand_id}/add", data={"kind": "dividend", "txn_date": "2026-06-15",
                                         "amount": "12,50"})
c.post(f"/accounts/{hand_id}/add", data={"kind": "fee", "txn_date": "2026-06-30",
                                         "amount": "-3"})
c.post(f"/accounts/{hand_id}/add", data={"kind": "deposit", "txn_date": "2026-05-01",
                                         "amount": "1000"})
c.post(f"/accounts/{hand_id}/add", data={"kind": "transfer", "txn_date": "2026-07-01",
                                         "amount": "200", "direction": "in"})
with db.get_conn() as conn:
    by_kind = {r["kind"]: r for r in conn.execute(
        "SELECT * FROM transactions WHERE account_id = ?", (hand_id,))}
check("a dividend is money in", by_kind["dividend"]["amount"], 12.5)
check("...and is income without anyone saying so", by_kind["dividend"]["category"], "income")
check("a fee is money out even when typed with a sign", by_kind["fee"]["amount"], -3.0)
check("...and is a fee", by_kind["fee"]["category"], "fee")
check("a deposit into a broker is your own money arriving",
      by_kind["deposit"]["category"], "transfer")
check("a transfer takes the direction it was given", by_kind["transfer"]["amount"], 200.0)
check("a row with no description is named after its kind",
      by_kind["dividend"]["description"], "dividend")

# A bank account: the rules the user already made apply to what they type.
r = c.post("/accounts/new", data={"name": "Cash envelope", "type": "bank",
                                  "currency": "EUR"})
cash_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{cash_id}/add")
check("a bank account is not offered trades", b'value="buy"' in r.data, False)
c.post(f"/accounts/{cash_id}/add", data={"kind": "withdrawal", "txn_date": "2026-08-02",
                                         "amount": "15", "counterparty": "Zqx Blorp Store"})
c.post(f"/accounts/{cash_id}/add", data={"kind": "withdrawal", "txn_date": "2026-08-03",
                                         "amount": "40", "category": "health"})
c.post(f"/accounts/{cash_id}/add", data={"kind": "deposit", "txn_date": "2026-08-04",
                                         "amount": "2500", "description": "Salary"})
with db.get_conn() as conn:
    rows = conn.execute("SELECT * FROM transactions WHERE account_id = ? "
                        "ORDER BY txn_date", (cash_id,)).fetchall()
check("an existing rule files a typed row", rows[0]["category"], "shopping")
check("a category picked by hand wins", rows[1]["category"], "health")
check("a deposit into a bank account is income", rows[2]["category"], "income")

# What is refused, and how: the form comes back filled in.
r = c.post(f"/accounts/{hand_id}/add", data={
    "kind": "buy", "txn_date": "2026-05-04", "isin": "not an isin",
    "quantity": "10", "price": "82.40"})
check("a trade without an ISIN is refused", b"needs the security" in r.data, True)
check("...and the typed values survive the refusal", b'value="10"' in r.data, True)
r = c.post(f"/accounts/{hand_id}/add", data={"kind": "fee", "txn_date": "2099-01-01",
                                             "amount": "3"})
check("a date in the future is refused", b"in the future" in r.data, True)
r = c.post(f"/accounts/{hand_id}/add", data={"kind": "fee", "txn_date": "2026-01-01",
                                             "amount": "0"})
check("a zero amount is refused", b"cannot be zero" in r.data, True)
r = c.post(f"/accounts/{cash_id}/add", data={"kind": "buy", "txn_date": "2026-01-01",
                                             "isin": "IE00B4L5Y983", "quantity": "1",
                                             "price": "1"})
check("a trade on a bank account is refused", b"what kind of entry" in r.data, True)
with db.get_conn() as conn:
    n_hand = conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ?",
                          (hand_id,)).fetchone()["n"]
check("nothing refused was stored", n_hand, 6)

# Only what was typed can be removed.
r = c.post(f"/accounts/{hand_id}/transactions/{by_kind['fee']['id']}/delete",
           follow_redirects=True)
check("a typed row can be removed", b"Removed." in r.data, True)
with db.get_conn() as conn:
    gone = conn.execute("SELECT COUNT(*) n FROM transactions WHERE id = ?",
                        (by_kind["fee"]["id"],)).fetchone()["n"]
check("...and is gone", gone, 0)
with db.get_conn() as conn:
    imported = conn.execute("SELECT id, account_id FROM transactions "
                            "WHERE source = 'degiro' LIMIT 1").fetchone()
r = c.post(f"/accounts/{imported['account_id']}/transactions/{imported['id']}/delete",
           follow_redirects=True)
check("an imported row cannot", b"typed in by hand can be removed" in r.data, True)
with db.get_conn() as conn:
    still = conn.execute("SELECT COUNT(*) n FROM transactions WHERE id = ?",
                         (imported["id"],)).fetchone()["n"]
check("...and is still there", still, 1)
r = c.get(f"/accounts/{hand_id}")
check("the account page marks typed rows and offers to remove them",
      b"/delete" in r.data, True)

# The balance: a reading, dated, which the overview then adds up.
r = c.post(f"/accounts/{hand_id}/balance", data={"amount": "1.234,56",
                                                  "as_of": "2026-09-01"},
           follow_redirects=True)
check("a balance can be typed in", b"Balance recorded" in r.data, True)
acct = next(a for a in ov.summary("EUR")["accounts"] if a["id"] == hand_id)
check("...and the overview counts it", acct["balance"], 1234.56)
check("...as of the day it was true", acct["balance_as_of"], "2026-09-01")
r = c.get(f"/accounts/{hand_id}")
check("...and the account page says it was typed in", b"typed in" in r.data, True)
r = c.post(f"/accounts/{hand_id}/balance", data={"amount": "", "as_of": "2026-09-01"},
           follow_redirects=True)
check("an empty balance is refused", b"balance is missing" in r.data, True)

# The other half of the rules promise: what ARRIVES gets the rules too,
# not only what was there when the rule was made. Through the importer,
# and never over a category somebody chose.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, '2026-08-09', 'ZQX BLORP STORE', -9.0, 'EUR', 'withdrawal', "
                 "'restaurants', 'kept-by-hand')", (cash_id,))
parsed = importers.ParseResult(rows=[
    importers.ParsedTxn(txn_date="2026-08-10", description="ZQX BLORP STORE 77",
                        amount=-20.0, currency="EUR", kind="withdrawal",
                        external_id="arrived-1"),
    importers.ParsedTxn(txn_date="2026-08-10", description="Custody",
                        amount=-2.0, currency="EUR", kind="fee",
                        external_id="arrived-2")])
importers.store(cash_id, parsed, "test")
with db.get_conn() as conn:
    arrived = {r["external_id"]: r["category"] for r in conn.execute(
        "SELECT external_id, category FROM transactions WHERE external_id "
        "IN ('arrived-1', 'arrived-2', 'kept-by-hand')")}
check("a rule applies to a row that arrives after it", arrived["arrived-1"], "shopping")
check("a kind that settles it needs no rule", arrived["arrived-2"], "fee")
check("a category somebody chose is not overwritten by a rule",
      arrived["kept-by-hand"], "restaurants")

# ---------------------------------------------------------------------------
print("\n20. Whose accounts are whose")
# ---------------------------------------------------------------------------
# A household: two people, one account each, a joint one, and one that
# belongs to nobody yet. The header's switch is a lens on the same data.
from app import overview, people                                      # noqa: E402

r = c.get("/")
check("with no people there is no switch", b'class="viewswitch"' in r.data, False)

r = c.post("/settings", data={"form": "person_add", "name": "  Alex  "},
           follow_redirects=True)
check("a person is added from Settings", b"Alex" in r.data, True)
c.post("/settings", data={"form": "person_add", "name": "Sam"})
r = c.post("/settings", data={"form": "person_add", "name": "alex"}, follow_redirects=True)
check("the same name twice is refused, case aside",
      b"already somebody called alex" in r.data, True)
r = c.post("/settings", data={"form": "person_add", "name": "   "}, follow_redirects=True)
check("a blank name is refused", b"needs a name" in r.data, True)
names = {p["name"]: p["id"] for p in people.all_people()}
check("two people exist", sorted(names), ["Alex", "Sam"])
alex, sam = names["Alex"], names["Sam"]

r = c.get("/")
check("now the switch is in the header", b'class="viewswitch"' in r.data, True)
check("...offering everyone and each person",
      all(x in r.data for x in (b">Everyone<", b">Alex<", b">Sam<")), True)

# Assign: Alex gets the Degiro broker, Sam the DKB bank account, both the
# hand-typed broker; the cash envelope belongs to nobody.
c.post(f"/accounts/{broker_id}/edit", data={"name": "Degiro", "type": "broker",
                                            "currency": "EUR", "people": [str(alex)]})
c.post(f"/accounts/{dkb_id}/edit", data={"name": "DKB Giro", "type": "bank",
                                         "currency": "EUR", "people": [str(sam)]})
c.post(f"/accounts/{hand_id}/edit", data={"name": "By hand", "type": "broker",
                                          "currency": "EUR", "people": [str(alex), str(sam)]})
check("an account can belong to two people",
      [p["name"] for p in people.for_account(hand_id)], ["Alex", "Sam"])
check("...and the edit form shows both ticked",
      c.get(f"/accounts/{hand_id}/edit").data.count(b"checked"), 2)
check("an account nobody was ticked for belongs to nobody", people.for_account(cash_id), [])

everyone = overview.summary("EUR")
check("Everyone counts every account", everyone["hidden_accounts"], 0)
mine = overview.summary("EUR", account_ids=people.account_ids(alex))
check("one person's summary holds only their accounts",
      sorted(a["name"] for a in mine["accounts"]), ["By hand", "Degiro"])
check("...and says how many it leaves out",
      mine["hidden_accounts"], everyone["account_count"] - 2)
check("...with the holdings of those accounts only",
      all(set(h["accounts"]) <= {"By hand", "Degiro"} for h in mine["holdings"]), True)
check("...and the recent rows likewise",
      {t["account_name"] for t in mine["recent"]} <= {"By hand", "Degiro"}, True)
nobody = overview.summary("EUR", account_ids=[])
check("a person with no accounts sees nothing, not everything",
      (nobody["accounts"], nobody["holdings"], nobody["net_worth"]), ([], [], 0))
check("the accounts page names whose each account is",
      b"Alex, Sam" in c.get("/accounts").data, True)

# The switch, through the web app.
r = c.post("/view", data={"person": str(sam), "next": "/accounts"}, follow_redirects=True)
check("switching lands back on the page it was pressed on", b"<h1>Accounts</h1>" in r.data, True)
check("...says whose accounts are counted", b"Only Sam" in r.data, True)
check("...lists only theirs", b"DKB Giro" in r.data and b"Degiro" not in r.data, True)
check("...and says what it leaves out", b"switch to Everyone" in r.data, True)
r = c.get("/transactions")
check("the transactions page is filtered too",
      b"KAFFEEBAR" in r.data and b"Achat 71" not in r.data, True)
check("...down to the account filter it offers",
      b"Degiro" not in r.data.split(b"<select")[1] if b"<select" in r.data else True, True)
r = c.get("/cashflow")
check("cash flow is filtered", b"Only Sam" in r.data, True)
sam_flow = cf.monthly(13, "EUR", account_ids=people.account_ids(sam))
all_flow = cf.monthly(13, "EUR")
check("...and adds up less than the household",
      sam_flow["total_spending"] < all_flow["total_spending"], True)
check("the budget page says whose spending it measures",
      b"is Sam" in c.get("/budget").data, True)
check("the categorise queue is filtered",
      cat.uncategorised(account_ids=people.account_ids(sam))[1]
      <= cat.uncategorised()[1], True)
for path in ("/", "/portfolio", "/subscriptions", "/categorize", "/budget"):
    check(f"{path} renders under a person", c.get(path).status_code, 200)

# A new account made while looking at Sam starts as Sam's.
r = c.get("/accounts/new")
check("the new-account form pre-ticks the person in view",
      f'value="{sam}" checked'.encode() in r.data, True)
r = c.post("/accounts/new", data={"name": "Sam savings", "type": "savings",
                                  "currency": "EUR", "people": [str(sam)]})
new_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
check("...and the tick is kept", [p["name"] for p in people.for_account(new_id)], ["Sam"])

# A bad `next` is not followed off-site.
r = c.post("/view", data={"person": "", "next": "//evil.example/x"})
check("the switch never redirects off the site",
      r.headers["Location"].startswith("/") and "evil" not in r.headers["Location"], True)
r = c.get("/accounts")
check("Everyone shows every account again", b"Degiro" in r.data and b"DKB Giro" in r.data, True)

# Removing a person: the accounts stay, and a browser still set to them
# falls back to Everyone.
c.post("/view", data={"person": str(alex), "next": "/"})
r = c.post("/settings", data={"form": "person_rename", "id": str(alex), "name": "Alexandra"},
           follow_redirects=True)
check("a person can be renamed", b"Alexandra" in r.data, True)
c.post("/settings", data={"form": "person_delete", "id": str(alex)}, follow_redirects=True)
check("a removed person is gone", [p["name"] for p in people.all_people()], ["Sam"])
check("...their accounts are not", c.get(f"/accounts/{broker_id}").status_code, 200)
check("...the joint account is now Sam's alone",
      [p["name"] for p in people.for_account(hand_id)], ["Sam"])
r = c.get("/accounts")
check("...and a view set to them falls back to Everyone",
      b"Only " not in r.data and b"Degiro" in r.data, True)
with db.get_conn() as conn:
    check("the link rows went with the person", conn.execute(
        "SELECT COUNT(*) AS n FROM account_people WHERE person_id = ?",
        (alex,)).fetchone()["n"], 0)

# ---------------------------------------------------------------------------
print("\n21. Forecast")
# ---------------------------------------------------------------------------
from app import forecast                                              # noqa: E402

# At 0 % the arithmetic is plain: start plus twelve deposits a year.
flat = forecast.project(1000, 100, 0.0, 2, first_year=2026)
check("year 0 is today", (flat[0]["year"], flat[0]["value"]), (2026, 1000.0))
check("at 0 % a year adds twelve deposits", round(flat[1]["value"], 2), 2200.0)
check("...and nothing is earned", flat[2]["returns"], 0.0)
check("one point per year, plus today", len(flat), 3)

# At 6 % the closed form says: 1000·1.005^12 + 100·(1.005^12−1)/0.005
g = 1.005 ** 12
expected = 1000 * g + 100 * (g - 1) / 0.005
grown = forecast.project(1000, 100, 6.0, 1)
check("at 6 % the year matches the annuity formula",
      round(grown[1]["value"], 6), round(expected, 6))
check("...contributions are counted apart from returns",
      (grown[1]["contributed"], round(grown[1]["returns"], 6)),
      (2200.0, round(expected - 2200, 6)))
check("a negative rate is allowed and shrinks",
      forecast.project(1000, 0, -10.0, 1)[1]["value"] < 1000, True)

# The inverse: what a month must be to hit a target, and it round-trips.
m = forecast.required_monthly(1000, 50000, 6.0, 10)
check("the required monthly lands on the target",
      round(forecast.project(1000, m, 6.0, 10)[-1]["value"], 4), 50000.0)
check("at 0 % it is the gap divided by the months",
      forecast.required_monthly(1000, 13000, 0.0, 1), 1000.0)
check("a target already met needs nothing", forecast.required_monthly(5000, 4000, 5.0, 3), 0.0)
check("...never a negative", forecast.required_monthly(100000, 1000, 5.0, 1), 0.0)
check("years to reach a goal", forecast.years_to_reach(1000, 100, 0.0, 3400), 2)
check("...None when it is out of reach", forecast.years_to_reach(0, 1, 0.0, 10**9), None)

# Inputs are bounded, and nonsense falls back rather than failing.
cleaned = forecast.clean({"mode": "target", "monthly": "abc", "rate": "99",
                          "years": "400", "target": "1.500,50"})
check("an unreadable number takes the default", cleaned["monthly"], 500.0)
check("the rate is capped", cleaned["rate"], forecast.MAX_RATE)
check("the horizon is capped", cleaned["years"], forecast.MAX_YEARS)
check("a German-style amount is read", cleaned["target"], 1500.5)
check("the mode is one of two", forecast.clean({"mode": "x"})["mode"], "project")

plan = forecast.plan(10000, {"mode": "target", "target": 100000, "rate": 5.0,
                             "years": 15, "monthly": 0})
check("a goal plan works out the monthly", plan["monthly"] > 0, True)
check("...and the projection ends on the goal", round(plan["end_value"]), 100000)
plan2 = forecast.plan(10000, {"mode": "project", "target": 20000, "rate": 0.0,
                              "years": 5, "monthly": 500})
check("a savings plan with a goal says when it gets there", plan2["reach_years"], 2)

# The page: remembers what was typed, starts from the real balance, and
# follows the header's person.
c.post("/view", data={"person": "", "next": "/"})
r = c.get("/forecast")
check("the forecast page renders", r.status_code, 200)
check("...with the chart", b"chart-forecast" in r.data, True)
check("...starting from the household's net worth", b"Starting from" in r.data, True)
r = c.post("/forecast", data={"mode": "target", "target": "250000", "years": "12",
                              "rate": "4.5"}, follow_redirects=True)
check("a goal is remembered", b'value="250000"' in r.data, True)
check("...and the answer is a monthly figure", b"Save per month" in r.data, True)
check("...kept in the settings file", settings.load()["forecast"]["years"], 12)
r = c.post("/forecast", data={"mode": "project", "monthly": "300", "years": "10",
                              "rate": "5"}, follow_redirects=True)
check("switching to a savings plan shows the end value",
      b"In 20" in r.data and b"You put in" in r.data, True)
sam_id = people.all_people()[0]["id"]
c.post("/view", data={"person": str(sam_id), "next": "/forecast"})
r = c.get("/forecast")
check("under a person the forecast starts from their balance",
      b"what Sam adds up to" in r.data, True)
c.post("/view", data={"person": "", "next": "/"})

# ---------------------------------------------------------------------------
print("\n22. Syncing every day, without being asked")
# ---------------------------------------------------------------------------
from datetime import datetime as _dt                                  # noqa: E402

cfg = {"auto_sync": True, "sync_time": "12:00"}
noon = _dt(2026, 9, 11, 12, 0)
check("due at the configured minute", banksync.sync_due(noon, cfg, None), True)
check("not before it", banksync.sync_due(_dt(2026, 9, 11, 11, 59), cfg, None), False)
check("still due later the same day if it was missed",
      banksync.sync_due(_dt(2026, 9, 11, 18, 30), cfg, "2026-09-10T12:00:05"), True)
check("not twice on one day",
      banksync.sync_due(_dt(2026, 9, 11, 12, 1), cfg, "2026-09-11T12:00:05"), False)
check("off means off", banksync.sync_due(noon, {"auto_sync": False}, None), False)
check("a broken time falls back to noon",
      banksync.sync_due(noon, {"auto_sync": True, "sync_time": "x"}, None), True)

results = banksync.sync_all()
check("sync_all reaches every connected account", len(results), 1)
check("...and reports per account, without error", results[0]["error"], None)
r = c.post("/settings", data={"form": "sync_all"}, follow_redirects=True)
check("the Settings button syncs them all", b"across 1 accounts" in r.data, True)
r = c.post("/settings", data={"base_currency": "EUR", "redirect_url": "http://x/cb",
                              "auto_sync": "1", "sync_time": "07:30"},
           follow_redirects=True)
check("the sync time is saved", settings.load()["sync_time"], "07:30")
check("...and shown", b"07:30" in r.data, True)
r = c.post("/settings", data={"base_currency": "EUR", "redirect_url": "http://x/cb",
                              "sync_time": "25:99"}, follow_redirects=True)
check("an unticked box turns it off", settings.load()["auto_sync"], False)
check("an impossible time falls back to noon", settings.load()["sync_time"], "12:00")

# ---------------------------------------------------------------------------
print("\n13. Four languages")
# ---------------------------------------------------------------------------
# The catalogues are checked against the strings the code actually asks
# for, because the failure mode of a hand-kept catalogue is not a crash:
# it is one sentence in English in the middle of a German page, which
# nobody notices until a user does.
from app import changelog, i18n, main                      # noqa: E402

TEMPLATES = pathlib.Path(__file__).resolve().parent.parent / "app" / "templates"
SOURCES = [pathlib.Path(__file__).resolve().parent.parent / "app" / f
           for f in ("main.py", "categories.py", "auth.py", "manual.py")]


def wanted_keys() -> set:
    """Every string the app can ask to have translated."""
    keys = set()
    for f in sorted(TEMPLATES.glob("*.html")):
        text = f.read_text()
        keys |= set(re.findall(r'_\("([^"]+)"\)', text))
        keys |= set(re.findall(r"_\('([^']+)'\)", text))
        keys |= set(re.findall(r'_f\(\s*"([^"]+)"', text))
        keys |= set(re.findall(r"_f\(\s*'([^']+)'", text))
        for one, many in re.findall(r'_n\([^,]+,\s*"([^"]+)",\s*"([^"]+)"', text):
            keys |= {one, many}
    join = lambda chunk: "".join(re.findall(r'"([^"]*)"', chunk))
    for f in SOURCES:
        text = f.read_text()
        for m in re.findall(r'(?:_t|i18n\.t)\(\s*((?:"[^"]*"\s*)+)\)', text):
            keys.add(join(m))
        for m in re.findall(r'(?:_f|i18n\.f)\(\s*((?:"[^"]*"\s*)+),', text):
            keys.add(join(m))
        for one, many in re.findall(
                r'(?:_n|i18n\.n)\(\s*[^,]+,\s*((?:"[^"]*"\s*)+),\s*((?:"[^"]*"\s*)+)[,)]',
                text):
            keys |= {join(one), join(many)}
    # The label tables, which are data rather than calls.
    keys |= set(main.ACCOUNT_TYPES.values())
    keys |= {f"{k} [kind]" for k in main.KINDS}
    keys |= {f"{r} [rhythm]" for r in main.RHYTHMS}
    keys |= {f"{s} [changelog]" for s in changelog.SECTIONS}
    keys |= {name for name, _colour, _group in cat.BUILTIN.values()}
    return keys


WANTED = wanted_keys()
check("the extractor found the strings to translate", len(WANTED) > 300, True)

for code, catalogue in sorted(i18n.CATALOGUES.items()):
    missing = WANTED - set(catalogue)
    check(f"{code} translates every string the app uses", sorted(missing), [])
    stale = set(catalogue) - WANTED
    check(f"...and carries none the app no longer has", sorted(stale), [])

# A translation that drops a placeholder renders "Deleted ." — worse than
# English, because it looks like data went missing rather than a word.
for code, catalogue in sorted(i18n.CATALOGUES.items()):
    wrong = [src for src, dst in catalogue.items()
             if set(re.findall(r"\{(\w+)\}", src))
             != set(re.findall(r"\{(\w+)\}", dst))]
    check(f"{code} keeps every placeholder", wrong, [])

# Duplicate keys in a dict literal are silent: the last one wins and the
# earlier translation is simply never used.
for code in sorted(i18n.CATALOGUES):
    path = pathlib.Path(__file__).resolve().parent.parent / "app" / "lang" / f"{code}.py"
    literals = [ast.literal_eval(k)
                for node in ast.walk(ast.parse(path.read_text()))
                if isinstance(node, ast.Dict)
                for k in node.keys if isinstance(k, ast.Constant)]
    dupes = sorted({k for k in literals if literals.count(k) > 1})
    check(f"{code} defines each key once", dupes, [])

check("an unknown string falls back to English",
      i18n.translate("Not in any catalogue", "de"), "Not in any catalogue")
check("a context marker never reaches the page",
      i18n.translate("Balance [somewhere]", "de"), "Balance")
check("...even when the catalogue has no entry for it",
      "[" in i18n.translate("buy [kind]", "en"), False)

# Numbers and dates follow the language, not the machine's locale.
# The space before the currency is non-breaking on purpose: an amount
# that wraps between the number and its currency is unreadable, and it
# happens on a phone in a table cell.
check("English groups with a comma and a dot",
      i18n.money(1234.5, "EUR", "en"), "1\u00a0234.50\u00a0EUR")
check("German swaps both separators",
      i18n.money(1234.5, "EUR", "de"), "1.234,50\u00a0EUR")
check("French groups with a narrow space",
      i18n.money(1234.5, "EUR", "fr"), "1\u202f234,50\u00a0EUR")
check("Spanish writes it like German",
      i18n.money(1234.5, "EUR", "es"), "1.234,50\u00a0EUR")
check("a negative keeps its sign in front",
      i18n.money(-99.9, "EUR", "de"), "-99,90\u00a0EUR")
check("the number never wraps away from its currency",
      " " in i18n.money(1234.5, "EUR", "de"), False)
check("no amount is a dash, not a zero", i18n.money(None, "EUR", "de"), "—")
check("English keeps ISO dates", i18n.fmt_date("2026-09-08", "en"), "2026-09-08")
check("German writes them with dots", i18n.fmt_date("2026-09-08", "de"), "08.09.2026")
check("French with slashes", i18n.fmt_date("2026-09-08", "fr"), "08/09/2026")
check("a timestamp is cut down to its date",
      i18n.fmt_date("2026-09-08T11:22:33+00:00", "de"), "08.09.2026")
check("something that is not a date is shown as it is",
      i18n.fmt_date("whenever", "de"), "whenever")
check("a month becomes a name", i18n.fmt_month("2026-09", "de"), "Sep 2026")
check("...in the language's own abbreviation",
      i18n.fmt_month("2026-09", "fr"), "sept. 2026")
check("share counts lose their trailing zeroes",
      i18n.qty(1061.0, "de"), "1.061")
check("...but keep the fraction when there is one",
      i18n.qty(0.5432, "fr"), "0,5432")

# Which language a request is in.
check("a configured language wins", i18n.resolve("fr", "de-DE,de;q=0.9"), "fr")
check("no setting follows the browser", i18n.resolve("", "de-DE,de;q=0.9"), "de")
check("...respecting the browser's own order",
      i18n.resolve("", "en-GB;q=0.7,es-ES;q=0.9"), "es")
check("a region is dropped, the language is not",
      i18n.resolve("", "de-AT"), "de")
check("a language we do not speak is English",
      i18n.resolve("", "is-IS,is;q=0.9"), "en")
check("garbage is English", i18n.resolve("", ";;;"), "en")
check("a nonsense setting is ignored rather than shown",
      i18n.resolve("klingon", None), "en")

# End to end: the setting changes the page, and the numbers with it.
r = c.post("/settings", data={"form": "general", "language": "de",
                              "base_currency": "EUR",
                              "redirect_url": "http://localhost:8000/connect/callback"},
           follow_redirects=True)
check("the language can be set from the page",
      settings.load()["language"], "de")
check("...and the confirmation is already in it",
      "Einstellungen gespeichert".encode() in r.data, True)

r = c.get("/")
check("the navigation is translated", "Übersicht".encode() in r.data, True)
check("...and the page says which language it is in",
      b'<html lang="de">' in r.data, True)
check("...and built-in category names come with it",
      "Lebensmittel".encode() in c.get("/settings").data, True)

r = c.get("/accounts")
check("amounts are punctuated the German way",
      re.search(rb"\d\.\d{3},\d{2}", r.data) is not None, True)

# The catalogue is cached per language, so one reader's page cannot be
# served out of another reader's cache.
r = c.post("/settings", data={"form": "general", "language": "fr",
                              "base_currency": "EUR",
                              "redirect_url": "http://localhost:8000/connect/callback"},
           follow_redirects=True)
check("switching again switches the catalogue with it",
      "Courses".encode() in c.get("/settings").data, True)
check("...and the German labels are gone",
      "Lebensmittel".encode() in c.get("/settings").data, False)

# A category the user renamed is theirs, in whatever language they typed
# it. Translating over the top of it would undo their edit on every page.
c.post("/settings", data={"form": "category_edit", "slug": "food",
                          "label": "Bouffe", "colour": "#5b9dff",
                          "group": "spending"})
c.post("/settings", data={"form": "general", "language": "de",
                          "base_currency": "EUR",
                          "redirect_url": "http://localhost:8000/connect/callback"})
check("a renamed built-in keeps the name the user gave it",
      cat.label("food"), "Bouffe")
check("...on every page, in every language",
      "Bouffe".encode() in c.get("/settings").data, True)

# Eleven sentences interpolate a link and are marked safe so the anchor
# survives. None of them takes user data — this is the check that keeps
# it that way, because the day one does, the name of an account becomes
# a script tag on the page that confirms deleting it.
r = c.post("/accounts/new", data={"name": "<b>Bold</b> & \"quoted\"",
                                  "type": "bank", "currency": "EUR"})
nasty_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
page = c.get(f"/accounts/{nasty_id}/edit").get_data(as_text=True)
check("a name with markup in it is escaped, not rendered",
      "<b>Bold</b>" in page, False)
check("...and arrives on the page as text",
      "&lt;b&gt;Bold&lt;/b&gt;" in page, True)
check("...quotes included", "&#34;quoted&#34;" in page or "&quot;quoted&quot;" in page, True)
c.post(f"/accounts/{nasty_id}/delete", data={})

c.post("/settings", data={"form": "general", "language": "",
                          "base_currency": "EUR",
                          "redirect_url": "http://localhost:8000/connect/callback"})
check("and it can be handed back to the browser",
      settings.load()["language"], "")

# ---------------------------------------------------------------------------
print("\n14. Saying which version this is")
# ---------------------------------------------------------------------------
from app import __version__                                 # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
entries = changelog.load(REPO / "CHANGELOG.md")
check("the changelog parses", len(entries) >= 8, True)
check("newest release first", entries[0]["version"], __version__)
check("...and the code agrees with the file", changelog.latest(), __version__)
check("every release carries a date",
      [e["version"] for e in entries if not e["date"]], [])

versions = [tuple(int(p) for p in e["version"].split(".")) for e in entries]
check("versions are in descending order", versions, sorted(versions, reverse=True))
check("...and none is listed twice", len(set(versions)), len(versions))
check("every release says something",
      [e["version"] for e in entries if not e["sections"]], [])
check("every section has at least one bullet",
      [(e["version"], s["name"]) for e in entries for s in e["sections"]
       if not s["items"]], [])
check("only the four known section names are used",
      sorted({s["name"] for e in entries for s in e["sections"]}
             - set(changelog.SECTIONS)), [])

# The parser turns markdown into markup, which means it decides what is
# allowed to be HTML on that page.
sample = changelog._inline("`code` and **bold** and [a link](https://example.org)")
check("backticks become code", "<code>code</code>" in sample, True)
check("stars become strong", "<strong>bold</strong>" in sample, True)
check("a full link becomes an anchor",
      '<a href="https://example.org" rel="noreferrer">a link</a>' in sample, True)
nasty = changelog._inline("a <script>alert(1)</script> in a release note")
check("markup in a note is escaped, not run", "<script>" in nasty, False)
check("...and shown as text", "&lt;script&gt;" in nasty, True)
relative = changelog._inline("see [the readme](../README.md)")
check("a relative link is left as text, because it would 404 here",
      "<a href" in relative, False)

check("a missing changelog is empty, not an error",
      changelog.load(REPO / "no-such-file.md"), [])

# A bullet wrapped over three lines is one bullet.
wrapped = pathlib.Path(TMP) / "wrapped.md"
wrapped.write_text("# Changelog\n\n## [9.9.9] — 2026-01-01\n\n### Added\n"
                   "- one bullet that\n  carries on over\n  three lines\n"
                   "- and a second\n")
one = changelog.load(wrapped)
check("a wrapped bullet is joined back up",
      str(one[0]["sections"][0]["items"][0]),
      "one bullet that carries on over three lines")
check("...without swallowing the next one",
      len(one[0]["sections"][0]["items"]), 2)

# What the app reports about itself.
r = c.get("/healthz")
check("the health check names the version",
      r.get_json()["version"], __version__)

r = c.get("/changelog")
check("the changelog page renders", r.status_code, 200)
check("...naming the running version", __version__.encode() in r.data, True)
check("...and the oldest release too", b"0.1.0" in r.data, True)
check("...with the section names translated",
      "Behoben".encode() in r.data or b"Fixed" in r.data, True)

r = c.get("/")
check("the version is in the header", b"version-badge" in r.data, True)

# The changelog ships in the image, so the page is not empty for the
# people who install it rather than clone it.
dockerignore = (REPO / ".dockerignore").read_text()
check("the build context keeps CHANGELOG.md", "!CHANGELOG.md" in dockerignore, True)
check("...and the Dockerfile copies it",
      "COPY CHANGELOG.md" in (REPO / "Dockerfile").read_text(), True)
workflow = (REPO / ".github" / "workflows" / "docker-image.yml").read_text()
check("...and editing it rebuilds the image",
      "'**.md'" in workflow, False)

# ---------------------------------------------------------------------------
print("\n15. Exchange rates")
# ---------------------------------------------------------------------------
# Against a fixture, never the ECB. The suite runs on a NAS with no way
# out, and a test that needs the internet is a test that gets skipped.
from app import fx, overview as ov                          # noqa: E402

ECB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
 xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
<gesmes:subject>Reference rates</gesmes:subject>
<Cube>
<Cube time="2026-09-09"><Cube currency="USD" rate="1.1652"/>
  <Cube currency="CHF" rate="0.9404"/><Cube currency="GBP" rate="0.85898"/></Cube>
<Cube time="2026-09-08"><Cube currency="USD" rate="1.1700"/>
  <Cube currency="CHF" rate="0.9500"/><Cube currency="GBP" rate="0.86000"/></Cube>
</Cube></gesmes:Envelope>"""

days = fx.parse(ECB_XML)
check("both days are read", sorted(days), ["2026-09-08", "2026-09-09"])
check("...with their currencies", sorted(days["2026-09-09"]), ["CHF", "GBP", "USD"])
check("the euro is never a row, it is the unit", "EUR" in days["2026-09-09"], False)
check("rates are numbers", days["2026-09-09"]["USD"], 1.1652)

err = None
try:
    fx.parse("<html>the ECB had an outage</html>")
except fx.FxError as exc:
    err = exc
check("a page that is not the feed is refused", err is not None, True)
err = None
try:
    fx.parse("not xml at all {")
except fx.FxError as exc:
    err = exc
check("...and so is something that is not XML", err is not None, True)

check("nothing is stored before it is fetched", fx.latest_date(), None)
check("...and no rates means stale", fx.is_stale(), True)
fx.store(days)
check("storing writes both days", fx.latest_date(), "2026-09-09")
fx.store(days)
with db.get_conn() as conn:
    rows = conn.execute("SELECT COUNT(*) n FROM fx_rates").fetchone()["n"]
check("...and storing twice does not double them", rows, 6)

as_of, rates = fx.rates_on()
check("the newest day wins", as_of, "2026-09-09")
check("...and the euro is in the table as 1", rates["EUR"], 1.0)

amount, on = fx.convert(100, "USD", "EUR")
check("dollars into euros", round(amount, 2), 85.82)
check("...at a rate that names its day", on, "2026-09-09")
check("euros into dollars", round(fx.convert(100, "EUR", "USD")[0], 2), 116.52)
# USD -> CHF crosses through the euro, which is the only way the ECB
# publishes it: 100 / 1.1652 * 0.9404.
check("a cross rate goes through the euro",
      round(fx.convert(100, "USD", "CHF")[0], 2), 80.71)
check("the same currency is not converted at all", fx.convert(100, "EUR", "EUR"),
      (100, None))
check("a currency the ECB does not publish is refused",
      fx.convert(100, "XYZ", "EUR"), (None, None))
check("...in either direction", fx.convert(100, "EUR", "XYZ"), (None, None))
check("no amount converts to no amount", fx.convert(None, "USD", "EUR"),
      (None, None))
check("lower case is fine", round(fx.convert(100, "usd", "eur")[0], 2), 85.82)

# A date picks the newest publication at or before it, which is what
# makes a Sunday work: nothing traded, so Friday's rate is the rate.
check("an exact date is used", fx.rates_on("2026-09-08")[0], "2026-09-08")
check("a day with no publication falls back to the one before",
      fx.rates_on("2026-09-10")[0], "2026-09-09")
check("...and yesterday's rate is yesterday's number",
      round(fx.convert(100, "USD", "EUR", "2026-09-08")[0], 2), 85.47)
check("before any rate exists, there is no rate",
      fx.rates_on("2020-01-01"), (None, {}))

# Staleness is about when we last asked, not how old the rate is. On a
# Monday the freshest rate in the world is Friday's.
check("storing alone does not count as having asked", fx.is_stale(), True)
db.set_state(fx.FETCHED_AT, datetime.now(timezone.utc).isoformat(timespec="seconds"))
check("...having asked does", fx.is_stale(), False)
check("an old ask is stale again",
      fx.is_stale(hours=-1), True)

st = fx.status()
check("the settings page is told the date", st["as_of"], "2026-09-09")
check("...and how many currencies", st["count"], 3)

# Whether any of that reaches the page. Two foreign balances: one the
# ECB publishes and one it does not, so both halves of the rule show up
# in a single total.
r = c.post("/accounts/new", data={"name": "US brokerage cash", "type": "bank",
                                  "currency": "USD"})
usd_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.post("/accounts/new", data={"name": "Tokyo account", "type": "bank",
                                  "currency": "JPY"})
jpy_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
with db.get_conn() as conn:
    conn.execute("INSERT INTO balances (account_id, amount, currency, as_of) "
                 "VALUES (?, 1000.0, 'USD', '2026-09-08')", (usd_id,))
    conn.execute("INSERT INTO balances (account_id, amount, currency, as_of) "
                 "VALUES (?, 50000.0, 'JPY', '2026-09-08')", (jpy_id,))

before = ov.summary("EUR")
converted = {x["currency"]: x for x in before["converted"]}
unconverted = {x["currency"]: x for x in before["unconverted"]}
check("a currency with a rate is converted", "USD" in converted, True)
check("...into the base currency", round(converted["USD"]["in_base"], 2), 858.22)
check("...and the total carries it",
      round(before["net_worth"], 2) >= 858.22, True)
check("...naming the day the rate came from", before["fx_as_of"], "2026-09-09")
check("a currency with no rate is not converted", "JPY" in unconverted, True)
check("...and is not silently added either",
      any(x["currency"] == "JPY" for x in before["converted"]), False)

r = c.get("/")
check("the page says what it converted",
      "converted at the ECB rate".encode() in r.data, True)
check("...and what it could not", b"no rate here covers them" in r.data, True)

# With no rates at all, the app is exactly what it was before this
# existed: two numbers, neither of them wrong.
with db.get_conn() as conn:
    conn.execute("DELETE FROM fx_rates")
bare = ov.summary("EUR")
check("with no rates, nothing is converted", bare["converted"], [])
check("...and both currencies sit beside the total",
      sorted(x["currency"] for x in bare["unconverted"]), ["JPY", "USD"])
check("...and the total is the base currency alone",
      round(bare["net_worth"], 2), round(bare["cash"] + bare["securities"], 2))
r = c.get("/settings")
check("the settings page offers to fetch them", b"fx_refresh" in r.data, True)
check("...and says why it matters", b"No rates yet" in r.data, True)
fx.store(days)                       # put them back for anything after

# Spending in another currency is spending. Until 0.10.1 the Cash Flow
# and Budget pages summed the base currency only, so a categorised
# dollar purchase was simply absent from its category — with nothing on
# the page to say so.
_ym = _date.today().strftime("%Y-%m")
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, ?, 'Whole Foods', -116.52, 'USD', 'withdrawal', 'food', "
                 "'usd-food')", (usd_id, _ym + "-02"))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, ?, 'Konbini', -1000.0, 'JPY', 'withdrawal', 'food', "
                 "'jpy-food')", (jpy_id, _ym + "-03"))
    # An old dollar row, older than any rate on file: converted at the
    # oldest rate rather than dropped.
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, '2026-03-02', 'Old dollars', -117.0, 'USD', 'withdrawal', "
                 "'food', 'usd-old')", (usd_id,))
rep = cf.budget_report("EUR")
food = next(r for r in rep["rows"] if r["category"] == "food")
check("a dollar purchase reaches its category this month",
      food["spent"] >= 100.0, True)
check("...converted at the ECB rate of its month",
      any(u["currency"] == "USD" for u in rep["converted"]), True)
check("a currency with no rate is not counted",
      any(u["currency"] == "JPY" for u in rep["unconverted"]), True)
check("...and the amount left out is named",
      next(u["amount"] for u in rep["unconverted"] if u["currency"] == "JPY"), 1000.0)
flow = cf.monthly(months=13, base_currency="EUR")
march = next((m for m in flow["months"] if m["month"] == "2026-03"), None)
check("a row older than the rates on file is converted at the oldest, not dropped",
      march is not None and march["categories"].get("food", 0) >= 99.0, True)
r = c.get("/budget")
check("the budget page says what it converted", b"converted at ECB rates" in r.data, True)
check("...and what it could not", b"no rate here covers them" in r.data, True)
r = c.get("/cashflow")
check("so does the cash flow page", b"converted at ECB rates" in r.data, True)
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id IN "
                 "('usd-food', 'jpy-food', 'usd-old')")

# ---------------------------------------------------------------------------
print("\n16. Market prices")
# ---------------------------------------------------------------------------
# Against canned Yahoo answers, never Yahoo. The shape is what the real
# endpoints return; the numbers are made up.
from app import prices                                    # noqa: E402

SEARCH = {
    "IE00B4L5Y983": {"quotes": [
        {"symbol": "IWDA.L", "exchange": "LSE", "quoteType": "ETF",
         "shortname": "ISHARES III PLC ISHRS CORE MSCI"},
        {"symbol": "IWDA.AS", "exchange": "AMS", "quoteType": "ETF",
         "longname": "iShares Core MSCI World UCITS ETF USD (Acc)"},
    ]},
    "IE00BK5BQT80": {"quotes": [
        {"symbol": "VWCE.DE", "exchange": "GER", "quoteType": "ETF",
         "longname": "Vanguard FTSE All-World UCITS ETF"}]},
    "DE0007236101": {"quotes": [
        {"symbol": "SIE.DE", "exchange": "GER", "quoteType": "EQUITY",
         "longname": "Siemens AG"}]},
    "GB00B03MLX29": {"quotes": [
        {"symbol": "SHEL.L", "exchange": "LSE", "quoteType": "EQUITY",
         "longname": "Shell plc"}]},
}
CHART = {
    "IWDA.AS": {"chart": {"result": [{"meta": {"symbol": "IWDA.AS", "currency": "EUR",
                "regularMarketPrice": 126.17, "regularMarketTime": 1789119714}}]}},
    "VWCE.DE": {"chart": {"result": [{"meta": {"symbol": "VWCE.DE", "currency": "EUR",
                "regularMarketPrice": 140.5, "regularMarketTime": 1789119714}}]}},
    "SIE.DE": {"chart": {"result": [{"meta": {"symbol": "SIE.DE", "currency": "EUR",
               "regularMarketPrice": 180.0, "regularMarketTime": 1789119714}}]}},
    "SHEL.L": {"chart": {"result": [{"meta": {"symbol": "SHEL.L", "currency": "GBp",
               "regularMarketPrice": 2650.0, "regularMarketTime": 1789119714}}]}},
    "NOPE.XX": {"chart": {"result": None, "error": {"code": "Not Found",
                "description": "No data found, symbol may be delisted"}}},
}
asked = []


def fake_get(url):
    asked.append(url)
    if "/finance/search" in url:
        q = url.split("q=")[1].split("&")[0]
        return SEARCH.get(q, {"quotes": []})
    sym = url.split("/chart/")[1].split("?")[0]
    if sym not in CHART:
        raise prices.PriceError(f"Yahoo refused the request (404).")
    return CHART[sym]


prices._get_json = fake_get          # the web routes must never reach Yahoo

check("a euro portfolio prefers the euro listing",
      prices.pick_symbol(SEARCH["IE00B4L5Y983"]["quotes"], "EUR"), "IWDA.AS")
check("...and a sterling one the London listing",
      prices.pick_symbol(SEARCH["IE00B4L5Y983"]["quotes"], "GBP"), "IWDA.L")
check("nothing to choose from is None", prices.pick_symbol([], "EUR"), None)
q = prices.quote("SHEL.L", fake_get)
check("pence become pounds", (q["price"], q["currency"]), (26.5, "GBP"))
check("...and the price names its day", q["as_of"], "2026-09-11")
err = None
try:
    prices.quote("NOPE.XX", fake_get)
except prices.PriceError as exc:
    err = str(exc)
check("a delisted ticker is a sentence, not a zero", "delisted" in (err or ""), True)

held = prices.held_isins()
check("what is held is what gets priced", "IE00B4L5Y983" in held, True)
check("...and a closed position is not", "XX0000000000" in held, False)

info = prices.refresh("EUR", get=fake_get)
check("a refresh prices the holdings", info["priced"] >= 1, True)
priced = prices.latest()
check("...the fund at its Amsterdam price", priced["IE00B4L5Y983"]["price"], 126.17)
check("...remembering the ticker", priced["IE00B4L5Y983"]["symbol"], "IWDA.AS")
asked.clear()
prices.refresh("EUR", get=fake_get)
check("the ticker is looked up once per security ever",
      any("search?q=IE00B4L5Y983" in u for u in asked), False)

# The overview now values at market, and says so.
sm = ov.summary("EUR")
iwda = next(h for h in sm["holdings"] if h["isin"] == "IE00B4L5Y983")
check("the overview uses the market price", iwda["price_kind"], "market")
check("...and the value follows", round(iwda["value"], 2),
      round(iwda["quantity"] * 126.17, 2))
check("...naming the day", sm["prices_as_of"], "2026-09-11")
r = c.get("/portfolio")
check("the portfolio page says which day the prices are from",
      b"at market prices of" in r.data, True)
r = c.get("/settings")
check("the settings page lists each holding's ticker",
      b'name="symbol"' in r.data and b"IWDA.AS" in r.data, True)

# A ticker the search got wrong is typed in, and a lookup never
# replaces it.
prices.set_symbol("IE00B4L5Y983", "vwce.de")
prices.refresh("EUR", get=fake_get, isins=["IE00B4L5Y983"])
check("a typed ticker is used", prices.latest()["IE00B4L5Y983"]["price"], 140.5)
asked.clear()
prices.refresh("EUR", get=fake_get)
check("...and never looked up again",
      any("/finance/search?q=IE00B4L5Y983" in u for u in asked), False)
check("...and the settings page says it was typed",
      next(x for x in prices.status() if x["isin"] == "IE00B4L5Y983")["manual"], True)
prices.set_symbol("IE00B4L5Y983", "")
with db.get_conn() as conn:
    sym = conn.execute("SELECT symbol FROM securities WHERE isin = 'IE00B4L5Y983'"
                       ).fetchone()["symbol"]
check("clearing it forgets the ticker so the next refresh starts over", sym, None)
try:
    prices.set_symbol("IE00B4L5Y983", "not a ticker!")
    bad = False
except ValueError:
    bad = True
check("something that is not a ticker is refused", bad, True)

# One security failing must not stop the rest, and must be written
# down where the Settings page shows it.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, isin, security_name, quantity, price, "
                 "external_id) VALUES (?, '2026-08-01', 'Mystery', -100, 'EUR', "
                 "'buy', 'XX1234567890', 'Mystery Corp', 10, 10, 'mystery-buy')",
                 (broker_id,))
info = prices.refresh("EUR", get=fake_get)
check("an ISIN Yahoo does not know is reported",
      "XX1234567890" in {f["isin"] for f in info["failed"]}, True)
check("...and the others are still priced", info["priced"] >= 3, True)
mystery = next(x for x in prices.status() if x["isin"] == "XX1234567890")
check("...with the reason on the settings page",
      "does not know" in (mystery["error"] or ""), True)
sm = ov.summary("EUR")
my = next(h for h in sm["holdings"] if h["isin"] == "XX1234567890")
check("the unpriced holding falls back to its last trade", my["price_kind"], "trade")
check("...counted", sm["holdings_at_trade"] >= 1, True)
r = c.get("/portfolio")
check("...and the page says so", b"last trade, no market price" in r.data, True)
r = c.post("/settings", data={"form": "price_symbol", "isin": "XX1234567890",
                              "symbol": "NOPE.XX"}, follow_redirects=True)
check("a wrong ticker typed in comes back with Yahoo's reason",
      b"delisted" in r.data, True)

# ---------------------------------------------------------------------------
print(f"\n{PASS} passed, {FAIL} failed   ({TMP})")
sys.exit(1 if FAIL else 0)
