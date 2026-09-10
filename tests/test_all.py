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
print("\n13. Importing, through the web app")
# ---------------------------------------------------------------------------
import io                                                             # noqa: E402

r = c.post("/accounts/new", data={"name": "Degiro", "type": "broker",
                                  "currency": "EUR"})
broker_id = int(r.headers["Location"].rstrip("/").split("/")[-1])


def upload(account, text, name="export.csv"):
    return c.post(f"/accounts/{account}/import",
                  data={"file": (io.BytesIO(text.encode()), name)},
                  content_type="multipart/form-data", follow_redirects=True)


r = upload(broker_id, fixtures.NOT_A_BROKER_CSV)
check("an unrecognised file is refused",
      b"do not match any importer" in r.data, True)

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
print("\n13. Four languages")
# ---------------------------------------------------------------------------
# The catalogues are checked against the strings the code actually asks
# for, because the failure mode of a hand-kept catalogue is not a crash:
# it is one sentence in English in the middle of a German page, which
# nobody notices until a user does.
from app import i18n, main                                 # noqa: E402

TEMPLATES = pathlib.Path(__file__).resolve().parent.parent / "app" / "templates"
SOURCES = [pathlib.Path(__file__).resolve().parent.parent / "app" / f
           for f in ("main.py", "categories.py", "auth.py")]


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
print(f"\n{PASS} passed, {FAIL} failed   ({TMP})")
sys.exit(1 if FAIL else 0)
