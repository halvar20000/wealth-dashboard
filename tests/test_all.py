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
import contextlib
import hashlib
import hmac
import urllib.parse
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

from app import auth, db, gains, settings               # noqa: E402
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
# The reference, with the day and the amount folded in: Crédit Agricole
# sends base64 of the description as the reference, so every quarterly
# "ECH PRET" of a year shares one, and an id made of it alone would
# keep the first and silently drop the rest.
check("the id uses the bank's own reference, with the day and the amount",
      debit["external_id"], "eb:idhash0001:2026-09-08:42.90:DKB-2026-09-08-0001")
same_ref = [dict(t, booking_date="2026-06-08") for t in fake_bank.TRANSACTIONS_PAGE_1["transactions"][:1]]
check("...so the same reference on another day is another row",
      eb.normalise_transaction(same_ref[0], "idhash0001")["external_id"] != debit["external_id"], True)
# Rows synced under the old shape are given the new one on start.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (id, name, type, currency) VALUES (9002, 'Old ids', 'bank', 'EUR')")
    conn.execute("INSERT INTO transactions (account_id, txn_date, amount, currency, kind, external_id) VALUES "
                 "(9002, '2026-05-29', -65.99, 'EUR', 'withdrawal', 'eb:abc:REF-77'), "
                 "(9002, '2026-05-30', 5, 'EUR', 'deposit', 'eb:abc:h:deadbeef'), "
                 "(9002, '2026-05-31', 5, 'EUR', 'deposit', 'eb:abc:2026-05-31:5.00:REF-9')")
    conn.execute("DELETE FROM app_state WHERE key = 'eb_ids_with_day'")
db.init_db()
with db.get_conn() as conn:
    ids = sorted(r_["external_id"] for r_ in conn.execute("SELECT external_id FROM transactions WHERE account_id = 9002"))
    conn.execute("DELETE FROM accounts WHERE id = 9002")
check("...and an old-shape id already on record is reshaped, the others left alone",
      ids, ["eb:abc:2026-05-29:65.99:REF-77", "eb:abc:2026-05-31:5.00:REF-9", "eb:abc:h:deadbeef"])

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


class StrictBank(fake_bank.FakeBank):
    """Trade Republic through Enable Banking, as observed: the
    continuation key is stamped with a status of the connector's own;
    repeating our BOOK is refused, the key alone is "wrong", and only
    the key with the original strategy and BOTH gets the page."""

    def transport(self, method, url, headers, body):
        status, data = super().transport(method, url, headers, body)
        params = self.calls[-1]["params"]
        if params.get("continuation_key"):
            if params.get("transaction_status") == "BOOK":
                return 422, json.dumps({"code": 422, "message":
                    "transactionStatus in request is not the same as in continuationKey. "
                    "Continuation key is only valid for the same getAccountTransactions "
                    "parameters"}).encode()
            if params.get("transaction_status") != "BOTH" or "strategy" not in params:
                return 422, json.dumps({"code": 422, "message": "Wrong continuation key provided",
                                        "error": "WRONG_CONTINUATION_KEY"}).encode()
        return status, data


strict = StrictBank()
rows_ = list(eb.Client(fake_bank.APP_ID, PRIVATE_KEY, transport=strict.transport)
             .all_transactions("acct-uid-0001"))
check("a connector that rejects the repeated parameters still yields every page",
      len(rows_), 5)
check("...the first page was asked for with the full parameters",
      strict.calls[0]["params"]["transaction_status"], "BOOK")
check("...then the repeat, then without a status, then with BOTH",
      [c["params"].get("transaction_status") for c in strict.calls[1:]],
      ["BOOK", None, "BOTH"])
check("...keeping the strategy the key is bound to",
      strict.calls[-1]["params"], {"continuation_key": "page-2", "strategy": "longest",
                                   "transaction_status": "BOTH"})
check("a bank that accepts the repeat is never asked twice", len(bank2.calls), 2)


class BrokenBank(fake_bank.FakeBank):
    """A 422 for any other reason is still an error."""

    def transport(self, method, url, headers, body):
        status, data = super().transport(method, url, headers, body)
        if self.calls[-1]["params"].get("continuation_key"):
            return 422, json.dumps({"message": "date_from is malformed"}).encode()
        return status, data


try:
    list(eb.Client(fake_bank.APP_ID, PRIVATE_KEY, transport=BrokenBank().transport)
         .all_transactions("acct-uid-0001"))
    check("any other 422 on a later page is raised, not retried", False, True)
except eb.EnableBankingError as exc:
    check("any other 422 on a later page is raised, not retried", exc.status, 422)

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
print("\n9a. Renewing a connection, and ending one")
# ---------------------------------------------------------------------------
# A consent runs out every ninety days. Renewing it gives the bank
# account a NEW Enable Banking uid — and a second link on the same
# account would mean the account page and the sync finding the dead one,
# and, if the hash differed, every booking arriving twice under two ids.
# One account, one link: a renewal goes on the row that is there.
def _connect(acct_id, session):
    saved = fake_bank.SESSION_RESPONSE
    fake_bank.SESSION_RESPONSE = session
    try:
        c.post(f"/connect/{acct_id}/start", data={"aspsp_name": "DKB", "aspsp_country": "DE"})
        with db.get_conn() as conn:
            st = conn.execute("SELECT state FROM auth_states").fetchone()["state"]
        return c.get(f"/connect/callback?code=THE-CODE&state={st}")
    finally:
        fake_bank.SESSION_RESPONSE = saved

renewed = json.loads(json.dumps(fake_bank.SESSION_RESPONSE))
renewed["session_id"] = "sess-renewed"
renewed["access"]["valid_until"] = "2027-04-01T00:00:00+00:00"
renewed["accounts"][0]["uid"] = "acct-uid-0002"
_connect(second_id, renewed)
with db.get_conn() as conn:
    links = [dict(r) for r in conn.execute("SELECT * FROM bank_links")]
    n_txn = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
check("a renewed consent does not add a second link", len(links), 1)
check("...the one link moves to the new session", links[0]["session_id"], "sess-renewed")
check("...and the new uid", links[0]["account_uid"], "acct-uid-0002")
check("...and the new expiry", links[0]["valid_until"], "2027-04-01T00:00:00+00:00")
check("...with the old error cleared", links[0]["last_error"], None)
check("...and the history is not doubled", n_txn, 4)

# The bank account itself may come back with a different hash — the
# IBAN says it is the same account, and its bookings are on record
# under the old hash, so that is the namespace the sync keeps using.
rehashed = json.loads(json.dumps(renewed))
rehashed["session_id"] = "sess-rehashed"
rehashed["accounts"][0]["uid"] = "acct-uid-0003"
rehashed["accounts"][0]["identification_hash"] = "idhash-changed"
_connect(second_id, rehashed)
with db.get_conn() as conn:
    links = [dict(r) for r in conn.execute("SELECT * FROM bank_links")]
    n_txn = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
check("a changed hash on the same IBAN keeps the old namespace",
      links[0]["identification_hash"], "idhash0001")
check("...so the re-sync finds every booking already there", n_txn, 4)

# A leftover from the days before this: two links on one account. The
# next renewal leaves one.
with db.get_conn() as conn:
    conn.execute("INSERT INTO bank_links (account_id, aspsp_name, aspsp_country, "
                 "session_id, account_uid, identification_hash) "
                 "VALUES (?, 'DKB', 'DE', 'sess-old', 'acct-uid-stale', 'idhash0001')",
                 (second_id,))
_connect(second_id, renewed)
with db.get_conn() as conn:
    uids = [r["account_uid"] for r in conn.execute("SELECT account_uid FROM bank_links")]
check("a stale second link is dropped by the renewal", uids, ["acct-uid-0002"])

# A consent that covers two bank accounts creates the second one once,
# not once per renewal.
two = json.loads(json.dumps(renewed))
two["session_id"] = "sess-two"
two["accounts"].append({
    "uid": "acct-uid-savings-1", "identification_hash": "idhash-savings",
    "account_id": {"iban": "DE02120300000000202052"}, "name": "Tagesgeld",
    "product": "DKB Tagesgeld", "currency": "EUR", "cash_account_type": "SVGS"})
_connect(second_id, two)
two_again = json.loads(json.dumps(two))
two_again["session_id"] = "sess-two-again"
two_again["accounts"][0]["uid"] = "acct-uid-0004"
two_again["accounts"][1]["uid"] = "acct-uid-savings-2"
_connect(second_id, two_again)
with db.get_conn() as conn:
    savings = conn.execute("SELECT COUNT(*) n FROM accounts WHERE name LIKE '%Tagesgeld%'").fetchone()["n"]
    links = [dict(r) for r in conn.execute("SELECT * FROM bank_links ORDER BY id")]
check("the savings account a consent covers is created once", savings, 1)
check("...with one link each", [l["account_uid"] for l in links],
      ["acct-uid-0004", "acct-uid-savings-2"])
check("...both on the newest session", {l["session_id"] for l in links}, {"sess-two-again"})
with db.get_conn() as conn:
    conn.execute("DELETE FROM accounts WHERE name LIKE '%Tagesgeld%'")

# Disconnecting drops the link and nothing else. What the user is
# telling the app is "stop syncing this", not "forget it".
r = c.get(f"/accounts/{second_id}")
check("a connected account offers to disconnect", b"/disconnect" in r.data, True)
shared.calls.clear()
r = c.post(f"/accounts/{second_id}/disconnect", follow_redirects=True)
check("disconnecting says what stayed", b"The history stays" in r.data, True)
with db.get_conn() as conn:
    links = conn.execute("SELECT COUNT(*) n FROM bank_links").fetchone()["n"]
    n_txn = conn.execute("SELECT COUNT(*) n FROM transactions").fetchone()["n"]
    n_bal = conn.execute("SELECT COUNT(*) n FROM balances WHERE account_id = ?",
                         (second_id,)).fetchone()["n"]
    acct = conn.execute("SELECT id FROM accounts WHERE id = ?", (second_id,)).fetchone()
check("...the link is gone", links, 0)
check("...the account is not", acct is not None, True)
check("...nor its transactions", n_txn, 4)
check("...nor its balances", n_bal > 0, True)
check("...and the consent was ended at the bank too",
      [(x["method"], x["path"]) for x in shared.calls],
      [("DELETE", "/sessions/sess-two-again")])
r = c.get(f"/accounts/{second_id}")
check("the page offers to connect again", b"Connect a bank" in r.data, True)
r = c.post(f"/accounts/{second_id}/disconnect", follow_redirects=True)
check("disconnecting twice says there was nothing to disconnect",
      b"not connected to a bank" in r.data, True)
r = c.post("/accounts/999999/disconnect")
check("...and a missing account is a 404", r.status_code, 404)

# Back to the state section 9 left, for everything after.
_connect(second_id, fake_bank.SESSION_RESPONSE)
shared.fail_next = (403, "consent expired")
banksync.sync_account(second_id)

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
# The export fills `shares` and `price` on a dividend row — the
# position it was paid on and the amount per share. Stored as a
# quantity it is counted into the holding on every payout, and the
# position grows by itself each quarter.
check("...but the shares it was paid on are not a quantity", div.quantity, None)
check("...nor the per-share amount a price", div.price, None)
# Rows an earlier version imported that way are put right when the app
# starts — unless the user has been at them by hand.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (id, name, type, currency) VALUES (9001, 'Old TR', 'broker', 'EUR')")
    conn.execute("INSERT INTO transactions (account_id, txn_date, amount, currency, kind, isin, "
                 "quantity, price, source, external_id) VALUES "
                 "(9001, '2026-03-01', 12.5, 'EUR', 'dividend', 'DE0007236101', 100, 0.125, 'trade_republic', 'tr:old-div'), "
                 "(9001, '2026-03-02', 12.5, 'EUR', 'dividend', 'DE0007236101', 100, 0.125, 'kraken', 'k:reward'), "
                 "(9001, '2026-03-03', -500, 'EUR', 'buy', 'DE0007236101', 5, 100, 'trade_republic', 'tr:old-buy')")
    conn.execute("INSERT INTO transactions (account_id, txn_date, amount, currency, kind, isin, "
                 "quantity, price, source, external_id, edited_at) VALUES "
                 "(9001, '2026-03-04', 12.5, 'EUR', 'dividend', 'DE0007236101', 3, 4.1667, 'trade_republic', 'tr:old-edited', '2026-09-01T00:00:00')")
db.init_db()
with db.get_conn() as conn:
    fixed = {r["external_id"]: (r["quantity"], r["price"]) for r in conn.execute(
        "SELECT external_id, quantity, price FROM transactions WHERE account_id = 9001")}
    conn.execute("DELETE FROM accounts WHERE id = 9001")
check("an old dividend row loses its quantity on start", fixed["tr:old-div"], (None, None))
check("...a Kraken reward keeps its units", fixed["k:reward"], (100.0, 0.125))
check("...a buy keeps its quantity", fixed["tr:old-buy"], (5.0, 100.0))
check("...and a row the user corrected is left alone", fixed["tr:old-edited"], (3.0, 4.1667))

unknown = by_id["tr:66666666-6666-6666-6666-666666666666"]
check("an unknown type is not dropped", unknown is not None, True)
check("...it is classified by its category instead", unknown.kind, "buy")
check("...and the broker's own word is preserved",
      "[SOMETHING_NEW]" in unknown.description, True)

# Finary's crypto export: a buy, a swap, a withdrawal to one's own wallet.
from app.importers import finary                                      # noqa: E402
check("a Finary export is recognised", importers.sniff(fixtures.FINARY_CSV).SLUG, "finary")
fn = finary.parse(fixtures.FINARY_CSV)
check("every row is read, the withdrawal to one's own wallet set aside", (len(fn.rows), fn.skipped, fn.problems), (5, 1, []))
fb = {r.external_id: r for r in fn.rows}
b = fb["019c13b6-064f-72a1-8cdf-a82bc96247f1"]
check("a buy is a buy of the coin, keyed the way the crypto page keys it",
      (b.kind, b.isin, b.security_name, b.quantity, round(b.price, 2), b.amount, b.fee, b.currency), ("buy", "CRYPTO:BTC", "Bitcoin", 0.00035318, 70077.58, -25.0, 0.25, "EUR"))
sw_out, sw_in = fb["019e403f-004b-7541-a2ee-9c51ef7a6851:sell"], fb["019e403f-004b-7541-a2ee-9c51ef7a6851:buy"]
check("a swap is a sale of the coin sent and a buy of the coin received, both at the euro value",
      ((sw_out.kind, sw_out.isin, sw_out.quantity, sw_out.amount), (sw_in.kind, sw_in.isin, sw_in.quantity, sw_in.amount)),
      (("sell", "CRYPTO:ETH", -0.011072, 2338.83), ("buy", "CRYPTO:BTC", 0.03500598, -2338.83)))
check("...and a fee paid in coin is not written as if it were euros", sw_in.fee, None)
check("a fiat deposit is a deposit", (fb["019c0000-0000-0000-0000-000000000000"].kind, fb["019c0000-0000-0000-0000-000000000000"].amount), ("deposit", 50.0))
check("the coins moved to one's own wallet are still held: the withdrawal is no row",
      any(r.txn_date == "2026-05-22" for r in fn.rows), False)

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

# A cost line under a label the parser has never seen: the arithmetic
# catches it. Kurswert 3 500 plus 12,50 named is 3 512,50; the amount
# says 3 513,71 — 1,21 of costs without a name, counted as fee.
odd = dkb_pdf.parse(fixtures.DKB_PDF_KAUF.replace("Ausmachender Betrag 3.512,50- EUR",
                                                  "Sonstige Entgelte 1,21- EUR\nAusmachender Betrag 3.513,71- EUR"))
check("a cost line under an unknown label is not lost: the amount minus Kurswert minus what was named is fee",
      (odd.rows[0].fee, odd.rows[0].amount), (13.71, -3513.71))
check("...and the statement says so", any("1.21 EUR of costs" in p for p in odd.problems), True)
odd_sell = dkb_pdf.parse(fixtures.DKB_PDF_VERKAUF)
check("a sale that adds up carries no such note", [p for p in odd_sell.problems if "no label" in p], [])

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
print("\n12d. Swissquote, Yuh and Crédit Agricole (Suisse)")
# ---------------------------------------------------------------------------
# Switzerland is outside PSD2, so these three arrive as files: the
# Swissquote statement in both of its layouts (which Yuh shares), the
# per-trade receipt, and the CA next bank CSV.
from app.importers import ca_switzerland, swissquote_beleg_pdf, swissquote_pdf  # noqa: E402

old = swissquote_pdf.parse(fixtures.SWISSQUOTE_KONTOAUSZUG, "CHF")
check("the old-layout statement parses without problems", old.problems, [])
chf = [r for r in old.rows if r.currency == "CHF"]
eur = [r for r in old.rows if r.currency == "EUR"]
check("every row of the CHF section is read", len(chf), 9)
check("...and the EUR section's too", len(eur), 2)
check("the rows add up to the statement's own movement",
      round(sum(r.amount for r in chf), 2), round(21295.65 - 22443.21, 2))
check("...in the EUR section as well", round(sum(r.amount for r in eur), 2), 0.0)
check("the direction is read off the running balance",
      [r.amount for r in chf[:3]], [6900.0, -6862.64, -102.0])
by = {r.external_id: r for r in old.rows}
kauf = by["sq:3163201:1090000002:CHF"]
check("a Kauf is a buy with ISIN, quantity, price, fee and tax",
      (kauf.kind, kauf.isin, kauf.quantity, kauf.price, kauf.fee, kauf.tax),
      ("buy", "IE00B44Z5B48", 30.0, 228.0, 9.85, 10.26))
check("...named without its ticker", kauf.security_name, "SS SPDR MSCI All County World")
div = by["sq:3163201:1090000006:CHF"]
check("a Dividende is a dividend net of the tax, which is kept",
      (div.kind, div.amount, div.tax, div.security_name), ("dividend", 6.4, 3.45, "iSh Cor SPI CH CHF D"))
card = by["sq:3163201:1090000005:CHF"]
check("a card payment names the merchant", (card.kind, card.counterparty),
      ("withdrawal", "CFF Genève Cornavin WC"))
check("...with pypdf's mangled accents put back", "Genève" in card.description, True)
check("an incoming payment names the sender",
      (by["sq:3163201:1090000001:CHF"].kind, by["sq:3163201:1090000001:CHF"].counterparty),
      ("deposit", "MAX MUSTER"))
check("an outgoing one the payee",
      (by["sq:3163201:1090000003:CHF"].kind, by["sq:3163201:1090000003:CHF"].counterparty),
      ("withdrawal", "Erika Beispiel"))
fx = [r for r in old.rows if r.kind == "transfer" and "1090000004" in r.external_id]
check("a currency exchange is one reference in two sections, both transfers",
      sorted((r.currency, r.amount) for r in fx), [("CHF", -99.84), ("EUR", 108.0)])
check("...with distinct ids", len({r.external_id for r in fx}), 2)
check("a single-line fee row without a reference is still a row",
      next(r for r in chf if r.kind == "fee").amount, -20.0)
check("a single-line row with a reference too",
      by["sq:3163201:1090000007:CHF"].amount, -6.9)
check("the page furniture in the middle of the table is stepped over",
      by["sq:3163201:1090000008:CHF"].amount, -961.08)
check("the closing balance is the statement's, in the account currency",
      old.closing_balance, {"amount": 21295.65, "currency": "CHF", "as_of": "2026-05-31"})
check("...or the first section's when the account currency is elsewhere",
      swissquote_pdf.parse(fixtures.SWISSQUOTE_KONTOAUSZUG, "USD").closing_balance["currency"], "CHF")

new = swissquote_pdf.parse(fixtures.SWISSQUOTE_TRANSAKTIONSAUFSTELLUNG, "CHF")
check("the new-layout export parses without problems", new.problems, [])
check("...every row", len(new.rows), 8)
check("...adding up to the export's own movement",
      round(sum(r.amount for r in new.rows if r.currency == "CHF"), 2), round(13844.10 - 18957.33, 2))
nby = {r.external_id: r for r in new.rows}
check("the signed amount is taken as printed",
      nby["sq:3163201:1142225922:CHF"].amount, 11616.0)
check("...and the sender from the line below", nby["sq:3163201:1142225922:CHF"].counterparty, "BEISPIEL AG")
check("the optional fee column is read", nby["sq:3163201:1143867441:CHF"].fee, 2.0)
check("...and an exchange's 'Betrag:' line is not mistaken for one",
      nby["sq:3163201:1152885176:CHF"].fee, None)
check("a one-line fee row is a fee", (nby["sq:3163201:1148865375:CHF"].kind,
                                     nby["sq:3163201:1148865375:CHF"].amount), ("fee", -6.9))
check("a card payment names the merchant", nby["sq:3163201:1144621900:CHF"].counterparty, "Digitec Galaxus AG")
check("'Einzahlung für' is money out, to the named payee",
      (nby["sq:3163201:1150239202:CHF"].kind, nby["sq:3163201:1150239202:CHF"].counterparty),
      ("withdrawal", "Helsana Versicherungen AG"))
check("the closing balance is the export's Endsaldo",
      new.closing_balance, {"amount": 13844.10, "currency": "CHF", "as_of": "2026-08-24"})

yuh = swissquote_pdf.parse(fixtures.YUH_KONTOAUSZUG, "CHF")
check("a Yuh statement is the same layout and parses", (yuh.problems, len(yuh.rows)), ([], 4))
check("...its fractional trades kept to four decimals",
      [r.quantity for r in yuh.rows if r.kind == "buy"], [2.5741, 3.3933, 2.2198])
check("...under its own customer number", yuh.rows[0].external_id, "sq:2892062:972551649:CHF")
check("...adding up", round(sum(r.amount for r in yuh.rows), 2), round(81.10 - 994.25, 2))

rc = swissquote_beleg_pdf.parse(fixtures.SWISSQUOTE_BELEG)
check("a trade receipt yields one row", (rc.problems, len(rc.rows)), ([], 1))
t = rc.rows[0]
check("...a buy with everything the statement will later say",
      (t.kind, t.txn_date, t.amount, t.isin, t.quantity, t.price, t.security_name),
      ("buy", "2026-05-05", -6862.64, "IE00B44Z5B48", 30.0, 228.0, "SPDR MSCI ACWI"))
check("...fees summed", t.fee, 22.64)
check("...and the SAME id as the statement's row, so both can be imported",
      t.external_id, kauf.external_id)
sell = swissquote_beleg_pdf.parse(fixtures.SWISSQUOTE_BELEG_VERKAUF).rows[0]
check("a sale is money in with a negative quantity",
      (sell.kind, sell.amount, sell.quantity), ("sell", 1013.23, -28.0))
check("...and the glued column header is taken off the name",
      sell.security_name, "Ambitious Portfolio Index")
# Payslips: the sheet whole, and the legs the bank never sees.
from app import importers, income                             # noqa: E402
from app.importers import payslip                             # noqa: E402

check("an SAP payslip is recognised by its wage codes", payslip.matches([], fixtures.PAYSLIP_SAP), True)
sap = payslip.parse(fixtures.PAYSLIP_SAP)
sl = sap.payslip
check("...read: who, where, which month, paid when",
      (sl["employee"], sl["employer"], sl["period"], sl["paid_on"], sl["currency"]),
      ("Max Muster", "Muster Chemie AG", "2026-03", "2026-03-25", "CHF"))
check("...the gross, the tax at source, the social deductions, the pension, the rest, the net",
      (sl["gross"], sl["tax"], sl["employee_social"], sl["employee_pension"], sl["other_deductions"], sl["net_paid"]),
      (10250.0, -1230.0, -656.0, -500.0, -40.0, 7824.0))
check("...the base salary and the allowance apart", (sl["base_salary"], sl["allowances"], sl["bonus"]), (10000.0, 250.0, 0.0))
check("...and the employer's side from its own block",
      (sl["employer_pension"], sl["employer_social"], sl["employer_side_known"]), (1180.0, 766.0, True))
check("...every printed line kept", len(sl["lines"]), 19)
check("the sheet adds up: gross less every deduction is the net",
      round(sl["gross"] + sl["tax"] + sl["employee_social"] + sl["employee_pension"] + sl["other_deductions"], 2), sl["net_paid"])
legs = sap.rows
check("it books three zero-sum pairs: tax, the employee's pension, the employer's",
      (len(legs), round(sum(r.amount for r in legs), 2)), (6, 0.0))
check("...each grossed up as salary and then paid as tax or moved as investment",
      [(r.kind, r.category, r.amount) for r in legs],
      [("deposit", "salary", 1230.0), ("tax", "tax", -1230.0), ("deposit", "salary", 500.0), ("transfer", "investment", -500.0),
       ("deposit", "salary", 1180.0), ("transfer", "investment", -1180.0)])
check("...under ids that are the sheet's identity", legs[1].external_id, "payslip:Muster_Chemie_AG:Max_Muster:2026-03:tax")

check("a small employer's Lohnabrechnung is recognised too", payslip.matches([], fixtures.PAYSLIP_LOHNABRECHNUNG), True)
lo = payslip.parse(fixtures.PAYSLIP_LOHNABRECHNUNG).payslip
check("...with the spaces put back into the names",
      (lo["employee"], lo["employer"], lo["period"], lo["paid_on"]),
      ("Erika Muster", "Musterstiftung für Forschung", "2025-12", "2025-12-15"))
check("...and a printed O read as the zero it is",
      (lo["gross"], lo["base_salary"], lo["bonus"], lo["net_paid"]), (7000.0, 4000.0, 3000.0, 5421.5))
check("...AHV and ALV as social, BVG as pension, no tax at source for a frontalier",
      (lo["employee_social"], lo["employee_pension"], lo["tax"]), (-448.0, -130.5, 0.0))
check("...the employer's side as the statutory floor, and flagged as such",
      (lo["employer_social"], lo["employer_pension"], lo["employer_side_known"]), (448.0, 130.5, False))
check("a sheet with no month is a problem, not a statement",
      payslip.parse("Lohnabrechnung Bruttolohn Nettolohn nothing else").problems, ["the payslip's month or gross could not be read"])

# Through the app: imported into the account the net lands in, shown
# per earner on the Income page, undone with the import.
r = c.get("/income")
check("the income page renders with nothing on it", (r.status_code, b"Adding a payslip" in r.data), (200, True))
with db.get_conn() as conn:
    slip_acct = conn.execute("SELECT id FROM accounts WHERE type = 'bank' ORDER BY id LIMIT 1").fetchone()[0]
imp = importers.begin_import(slip_acct, "PAYSLIP_2026_03.pdf", "payslip")
rep = importers.store(slip_acct, payslip.parse(fixtures.PAYSLIP_SAP), "payslip", imp)
importers.store(slip_acct, payslip.parse(fixtures.PAYSLIP_LOHNABRECHNUNG), "payslip", imp)
check("storing a payslip books its legs and keeps the sheet", (rep["inserted"], rep["duplicates"]), (6, 0))
with db.get_conn() as conn:
    check("...with the categories the parser set, not the kind's default",
          [r_[0] for r_ in conn.execute("SELECT category FROM transactions WHERE import_id = ? ORDER BY id LIMIT 2", (imp,))], ["salary", "tax"])
    check("...and two statements on record", conn.execute("SELECT COUNT(*) FROM payslips").fetchone()[0], 2)
rep = importers.store(slip_acct, payslip.parse(fixtures.PAYSLIP_SAP), "payslip", imp)
check("the same sheet again is nothing new", (rep["inserted"], rep["duplicates"]), (0, 6))
r = c.get("/income")
body = r.data.decode()
check("the income page shows each earner with their employer",
      ("Max Muster" in body, "Muster Chemie AG" in body, "Erika Muster" in body, "Musterstiftung" in body), (True, True, True, True))
check("...the year's totals and the months under them", ("2026" in body and "2025" in body, "statutory floor" in body), (True, True))
ers = {e_["name"]: e_ for e_ in income.earners()}
check("the earner's totals: gross, tax rate, pension inflow, employer's cost",
      (ers["Max Muster"]["totals"]["gross"], round(ers["Max Muster"]["totals"]["tax_rate"], 3), ers["Max Muster"]["totals"]["pension_inflow"], ers["Max Muster"]["totals"]["employer_cost"]),
      (10250.0, 0.12, 1680.0, 12196.0))
check("...and the small employer's floor is flagged", ers["Erika Muster"]["employer_side_known"], False)
n = importers.undo_import(slip_acct, imp)
with db.get_conn() as conn:
    check("undoing the import removes the legs and the sheets alike",
          (n, conn.execute("SELECT COUNT(*) FROM payslips").fetchone()[0]), (10, 0))

# The mapper: a sheet no parser was written for, read through what the
# user confirms — suggested from a catalogue, remembered by the sheet's
# own markers, so next month's sheet is recognised by itself.
from app.importers import payslip_map as pm                  # noqa: E402

bul = fixtures.PAYSLIP_BULLETIN
check("a French bulletin is not one of the built-in layouts", payslip.matches([], bul), False)
check("...but it reads like a payslip: labelled amounts and a month", pm.looks_like_payslip(bul), True)
check("its numbers are read the French way", pm.number_format(bul), "fr")
check("...an SAP sheet the German way, a Swiss sheet with apostrophes",
      (pm.number_format(fixtures.PAYSLIP_SAP), pm.number_format(fixtures.PAYSLIP_LOHNABRECHNUNG)), ("de", "ch"))
bl = pm.lines(bul)
check("every line with an amount, a month or a date is offered", len(bl), 12)
by_label = {l["label"]: l for l in bl}
check("...the label is what stands before the first amount; a rate is not an amount",
      (by_label["Sécurité sociale maladie"]["amounts"], by_label["Sécurité sociale maladie"]["rates"]), ([3620.0, 27.15], [0.75]))
check("...and a glued Swiss line still splits into basis, rate and amount",
      next(l for l in pm.lines(fixtures.PAYSLIP_LOHNABRECHNUNG) if l["label"] == "AHV-Beitrag")["amounts"], [7000.0, -371.0])
check("...a printed O reads as a zero there too",
      next(l for l in pm.lines(fixtures.PAYSLIP_LOHNABRECHNUNG) if l["label"] == "Gratifikation")["amounts"], [1000.0])
sug = {bl[i]["label"]: b for i, b in pm.suggest(bl).items()}
check("the catalogue suggests what each line means, in French too",
      (sug.get("Salaire brut"), sug.get("Net à payer"), sug.get("Prélèvement à la source"), sug.get("Retraite complémentaire AGIRC-ARRCO"),
       sug.get("Assurance chômage"), sug.get("Retraite part patronale"), sug.get("Mutuelle"), sug.get("Période Mars 2026 Date de paiement")),
      ("gross", "net", "tax", "pension", "social", "employer_pension", "other", "period"))
check("...and 'payer' is not 'paye'", sug.get("Net à payer"), "net")
check("...and the employer's AG lines on an SAP sheet go to the employer's side, the AN lines to the earner's",
      {fixtures.PAYSLIP_SAP and l["label"]: b for l, b in ((pm.lines(fixtures.PAYSLIP_SAP)[i], b) for i, b in pm.suggest(pm.lines(fixtures.PAYSLIP_SAP)).items())
       if l["label"] in ("PF1 Beitrag AG", "6801 PF1 Beitrag AN", "AHV-Prämie AG-Anteil", "/411 AHV-Beitrag")},
      {"PF1 Beitrag AG": "employer_pension", "6801 PF1 Beitrag AN": "pension", "AHV-Prämie AG-Anteil": "employer_social", "/411 AHV-Beitrag": "social"})
check("the names are guessed from the sheet", pm.guess_names(bul), ("Exemple SAS", "Jean Dupont"))
check("...on a glued sheet from the line under the title", pm.guess_names(fixtures.PAYSLIP_LOHNABRECHNUNG)[1], "Erika Muster")
buckets: dict = {}
period_label = None
for lab, b in sug.items():
    if b == "period":
        period_label = lab
    elif b in pm.AMOUNT_BUCKETS:
        buckets.setdefault(b, []).append(lab)
mapping = {"format": "fr", "buckets": buckets, "period_label": period_label, "paid_label": None, "currency": "EUR",
           "employer": "Exemple SAS", "employee": "Jean Dupont"}
rd = pm.read(mapping, bul)
bs = rd.payslip
check("read through the mapping: the sheet's figures, deductions negative whichever way they were printed",
      (bs["period"], bs["paid_on"], bs["gross"], bs["tax"], bs["employee_social"], bs["employee_pension"], bs["other_deductions"], bs["net_paid"], bs["employer_pension"]),
      ("2026-03", "2026-03-31", 3620.0, -350.0, -362.03, -114.03, -40.0, 2753.94, 250.0))
check("...and it adds up: gross less every deduction is the net", pm.adds_up(bs), 0.0)
check("...with the legs a built-in parser would book", [(r_.kind, r_.amount) for r_ in rd.rows],
      [("deposit", 350.0), ("tax", -350.0), ("deposit", 114.03), ("transfer", -114.03), ("deposit", 250.0), ("transfer", -250.0)])
check("a mapping without gross and net is not enough", pm.check({"buckets": {"tax": ["x"]}}), ["gross", "net"])
pm.save("Exemple SAS bulletin", "Exemple SAS", "Jean Dupont", mapping)
check("saved, next month's sheet is recognised by its markers",
      pm.sniff(bul.replace("Mars 2026", "Avril 2026")).LABEL, "Exemple SAS bulletin")
check("...spaces and case notwithstanding", pm.find(bul.upper().replace(" ", "")) is not None, True)
check("...and another employer's sheet is not", pm.find(bul.replace("Exemple SAS", "Autre SARL")), None)
mp = pm.sniff(bul.replace("Mars 2026", "Avril 2026")).parse(bul.replace("Mars 2026", "Avril 2026"))
check("...and reads through the saved mapping", (mp.payslip["period"], mp.payslip["gross"]), ("2026-04", 3620.0))
r = c.post("/settings", data={"form": "payslip_mapping_delete", "mapping_id": str(pm.all_mappings()[0]["id"])}, follow_redirects=True)
check("a mapping can be forgotten under Settings", (b"Mapping forgotten" in r.data, pm.all_mappings()), (True, []))

check("a receipt that is not one says so",
      "not a Swissquote" in swissquote_beleg_pdf.parse("Hello there").problems[0], True)
check("a statement that is not one says so",
      "not a Swissquote" in swissquote_pdf.parse("Kontoauszug Nummer 3").problems[0], True)

cs = ca_switzerland.parse(fixtures.CA_SWITZERLAND_CSV)
check("the CA Suisse CSV parses without problems", cs.problems, [])
check("...every row, Latin-1 decoded", (len(cs.rows), cs.rows[-1].description),
      (8, "Paiement en faveur de: Café Zürich Müller"))
check("debit and credit become one signed amount",
      [r.amount for r in cs.rows[:2]], [-3700.0, 3714.8])
check("the Auftragsnummer is the id", cs.rows[0].external_id, "ca-ch:236765220")
check("a payment names its payee", (cs.rows[0].kind, cs.rows[0].counterparty),
      ("withdrawal", "Swissquote Bank SA"))
check("a credit names its sender, address dropped",
      (cs.rows[1].kind, cs.rows[1].counterparty), ("deposit", "Schweizerische Stiftung"))
check("fees are fees, refunded or not", [r.kind for r in cs.rows[2:4]], ["fee", "fee"])
check("an interest period on the credit side is interest", cs.rows[6].kind, "interest")
check("...and on the debit side the tax on it", cs.rows[5].kind, "tax")
check("the newest row's balance is the closing balance",
      cs.closing_balance, {"amount": 11.26, "currency": "CHF", "as_of": "2026-08-24"})
check("the CSV is recognised by the sniffer",
      importers.sniff(fixtures.CA_SWITZERLAND_CSV).SLUG, "ca_switzerland")
for fx_text, slug in ((fixtures.SWISSQUOTE_KONTOAUSZUG, "swissquote_pdf"),
                      (fixtures.SWISSQUOTE_TRANSAKTIONSAUFSTELLUNG, "swissquote_pdf"),
                      (fixtures.YUH_KONTOAUSZUG, "swissquote_pdf"),
                      (fixtures.SWISSQUOTE_BELEG, "swissquote_beleg_pdf")):
    pdf = fixtures.pdf_from_text(fx_text)
    got = importers.sniff(pdf)
    check(f"a {slug} PDF is recognised by the sniffer", got.SLUG if got else None, slug)
check("...and a real PDF parses to the same rows as its text",
      [r.external_id for r in swissquote_pdf.parse(fixtures.pdf_from_text(fixtures.YUH_KONTOAUSZUG)).rows],
      [r.external_id for r in yuh.rows])

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
check("an unrecognised CSV is not refused: it is sent to the mapping page",
      b"Map the columns" in r.data, True)
r = upload(broker_id, "just one line of prose, no columns at all")
check("...while a file that is not even a table is refused",
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

# A Swissquote account: the monthly statement and the receipt of one of
# its trades, uploaded together — the trade must land once.
r = c.post("/accounts/new", data={"name": "Swissquote Trading", "type": "broker",
                                  "currency": "CHF"})
sq_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.post(f"/accounts/{sq_id}/import", data={"file": [
    (io.BytesIO(fixtures.pdf_from_text(fixtures.SWISSQUOTE_KONTOAUSZUG)), "Kontoauszug_3163201_20260601.pdf"),
    (io.BytesIO(fixtures.pdf_from_text(fixtures.SWISSQUOTE_BELEG)), "Borsenabrechnung_3163201_1090000002_20260505.pdf"),
]}, content_type="multipart/form-data", follow_redirects=True)
check("a Swissquote statement and a receipt import together",
      b"11 new" in r.data and b"1 already had" in r.data, True)
sq_pos = importers.positions(sq_id)
check("...and the trade is held once", [(p["isin"], p["quantity"]) for p in sq_pos],
      [("IE00B44Z5B48", 30.0)])
with db.get_conn() as conn:
    sq_bal = conn.execute("SELECT amount, currency, as_of FROM balances WHERE account_id = ? "
                          "ORDER BY as_of DESC LIMIT 1", (sq_id,)).fetchone()
check("...with the statement's closing balance recorded",
      (sq_bal["amount"], sq_bal["currency"], sq_bal["as_of"]), (21295.65, "CHF", "2026-05-31"))
r = c.post(f"/accounts/{sq_id}/import", data={"file": [
    (io.BytesIO(fixtures.pdf_from_text(fixtures.SWISSQUOTE_TRANSAKTIONSAUFSTELLUNG)), "Kontoauszug_3163201_20260825.pdf")]},
    content_type="multipart/form-data", follow_redirects=True)
check("the web export of a later period imports on top", b"8 new" in r.data, True)
# Gone again, so the CHF balance does not sit in every later total.
c.post(f"/accounts/{sq_id}/delete", data={"confirm": "Swissquote Trading"})

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
      "income" in cat.income(), True)
cat.update_category("investment", "Investment", "#5b9dff", cat.INCOME_GROUP)
check("...investment included", "investment" in cat.non_spending(), True)
# A database from before the income group existed has `income` stored
# as not-spending on its override row; the stored group is not the
# catalogue's.
with db.get_conn() as conn:
    conn.execute("UPDATE categories SET cat_group = 'non_spending' WHERE slug = 'income'")
cat.invalidate()
check("...and a stored group from before the income group is ignored",
      "income" in cat.income(), True)

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

# Income is whatever the user says it is. One category was the whole of
# it; now every category in the income group counts, each as its own
# line — a salary, a rent coming in, interest — and one of their own
# can be moved in beside them.
r = c.post("/settings", data={"form": "category_new", "label": "Side gig",
                              "colour": "#ff00ff", "group": "income"})
check("a category can be created as income", "side_gig" in cat.income(), True)
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, "
                 "amount, currency, kind, category, external_id) VALUES "
                 "(?, '2026-06-03', 'Lohn', 3000.0, 'EUR', 'deposit', 'salary', 'inc-salary'), "
                 "(?, '2026-06-04', 'Miete Whg 2', 900.0, 'EUR', 'deposit', 'rental_income', 'inc-rent'), "
                 "(?, '2026-06-05', 'Gig', 150.0, 'EUR', 'deposit', 'side_gig', 'inc-gig'), "
                 "(?, '2026-06-06', 'Refund', 40.0, 'EUR', 'deposit', 'shopping', 'inc-refund')",
                 (broker_id, broker_id, broker_id, broker_id))
after = cf.monthly(months=24)
june = next(m for m in after["months"] if m["month"] == "2026-06")
check("every income category is added up",
      round(june["income"] - (before_june["income"] if before_june else 0), 2), 4050.0)
check("...each kept apart", {k: round(v) for k, v in june["income_categories"].items()
                                if k in ("salary", "rental_income", "side_gig")},
      {"salary": 3000, "rental_income": 900, "side_gig": 150})
check("...a refund in a spending category is not income",
      "shopping" in june["income_categories"], False)
srcs = {x["category"]: x for x in after["income_by_category"]}
check("...and the page gets the sources with their colours",
      (srcs["side_gig"]["colour"], srcs["salary"]["label"]), ("#ff00ff", "Salary"))
r = c.get("/cashflow")
check("the page lists where it comes from", b"Where it comes from" in r.data, True)
check("...and stacks the income bar by category", b"stack: 'in'" in r.data, True)
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id LIKE 'inc-%'")
cat.delete_category("side_gig")

# The dividends and interest already filed as plain income move to
# their own category — once. A row the user files back by hand stays.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, "
                 "currency, kind, category, external_id) VALUES "
                 "(?, '2026-05-01', 'Old dividend', 10.0, 'EUR', 'dividend', 'income', 'old-div')",
                 (broker_id,))
    conn.execute("DELETE FROM app_state WHERE key = 'refiled_capital_income'")
db.init_db()
with db.get_conn() as conn:
    moved = conn.execute("SELECT category FROM transactions WHERE external_id = 'old-div'").fetchone()["category"]
    conn.execute("UPDATE transactions SET category = 'income' WHERE external_id = 'old-div'")
db.init_db()
with db.get_conn() as conn:
    again = conn.execute("SELECT category FROM transactions WHERE external_id = 'old-div'").fetchone()["category"]
    conn.execute("DELETE FROM transactions WHERE external_id = 'old-div'")
check("an old dividend filed as income moves to its own category on start", moved, "capital_income")
check("...once: filed back by hand, it stays", again, "income")

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
r = c.get("/settings/categories")
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
check("...and is income without anyone saying so", by_kind["dividend"]["category"], "capital_income")
check("...of the kind that has its own line on Cash Flow", "capital_income" in cat.income(), True)
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

r = c.post(f"/accounts/{hand_id}/transactions/{by_kind['fee']['id']}/delete",
           follow_redirects=True)
check("a typed row can be removed", b"Removed." in r.data, True)
with db.get_conn() as conn:
    gone = conn.execute("SELECT COUNT(*) n FROM transactions WHERE id = ?",
                        (by_kind["fee"]["id"],)).fetchone()["n"]
check("...and is gone", gone, 0)
# An imported row can be removed too — and stays removed: its id is
# remembered, and the next import of the same file leaves it out. That
# is the difference between removing and hiding until tomorrow.
with db.get_conn() as conn:
    imported = dict(conn.execute("SELECT id, account_id, external_id FROM transactions "
                                 "WHERE source = 'degiro' AND external_id IS NOT NULL LIMIT 1").fetchone())
r = c.post(f"/accounts/{imported['account_id']}/transactions/{imported['id']}/delete",
           follow_redirects=True)
check("an imported row can be removed", b"will not bring it back" in r.data, True)
with db.get_conn() as conn:
    still = conn.execute("SELECT COUNT(*) n FROM transactions WHERE id = ?", (imported["id"],)).fetchone()["n"]
    remembered = conn.execute("SELECT COUNT(*) n FROM removed_rows WHERE external_id = ?", (imported["external_id"],)).fetchone()["n"]
check("...it is gone, and its id remembered", (still, remembered), (0, 1))
r = upload(imported["account_id"], fixtures.DEGIRO_CSV)
with db.get_conn() as conn:
    back = conn.execute("SELECT COUNT(*) n FROM transactions WHERE external_id = ?", (imported["external_id"],)).fetchone()["n"]
check("...and importing the file again does not bring it back", back, 0)
with db.get_conn() as conn:
    conn.execute("DELETE FROM removed_rows WHERE external_id = ?", (imported["external_id"],))
upload(imported["account_id"], fixtures.DEGIRO_CSV)
with db.get_conn() as conn:
    back = conn.execute("SELECT COUNT(*) n FROM transactions WHERE external_id = ?", (imported["external_id"],)).fetchone()["n"]
check("...forgetting the removal lets it in again", back, 1)
r = c.post(f"/accounts/{hand_id}/transactions/99999999/delete", follow_redirects=True)
check("a row that is not there says so", b"not there" in r.data, True)
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
# A second reading, and the account has a line: the readings, day by
# day, on its page.
r = c.get(f"/accounts/{hand_id}")
check("one reading is a figure, not a line", b"Balance over time" in r.data, False)
c.post(f"/accounts/{hand_id}/balance", data={"amount": "1300", "as_of": "2026-09-08"})
r = c.get(f"/accounts/{hand_id}")
check("two readings are a line on the account's page",
      (b"Balance over time" in r.data, b"2 readings since" in r.data, b'"amount": 1234.56' in r.data, b'"amount": 1300.0' in r.data), (True, True, True, True))
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

# At 6 % a year the closed form says: 1000·1.06 + 100·(1.06−1)/i, with i
# the monthly rate that compounds to 6 % — so a year is exactly 6 %.
i = 1.06 ** (1 / 12) - 1
expected = 1000 * 1.06 + 100 * (1.06 - 1) / i
grown = forecast.project(1000, 100, 6.0, 1)
check("at 6 % the year matches the annuity formula",
      round(grown[1]["value"], 6), round(expected, 6))
check("...and 6 % a year is exactly 6 % after twelve months",
      round(forecast.project(1000, 0, 6.0, 1)[1]["value"], 6), 1060.0)
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
check("...kept in the settings file", settings.load()["forecast"]["all"]["years"], 12)
r = c.post("/forecast", data={"mode": "project", "monthly": "300", "years": "10",
                              "rate": "5"}, follow_redirects=True)
check("switching to a savings plan shows the end value",
      b"In 20" in r.data and b"You put in" in r.data, True)
sam_id = people.all_people()[0]["id"]
c.post("/view", data={"person": str(sam_id), "next": "/forecast"})
r = c.get("/forecast")
check("under a person the forecast starts from their balance",
      b"what Sam adds up to" in r.data, True)
check("...with their own plan, not the household's", b'value="300"' not in r.data, True)
c.post("/forecast", data={"mode": "target", "target": "80000", "years": "8", "rate": "3"})
r = c.get("/forecast")
check("a person's plan is kept for them", b'value="80000"' in r.data, True)
c.post("/view", data={"person": "", "next": "/"})
r = c.get("/forecast")
check("...and the household's plan is untouched", b'value="300"' in r.data, True)
check("...both in the settings file",
      sorted(settings.load()["forecast"]), ["all", f"person:{sam_id}"])
# A 0.16.0 settings file held one flat plan: it becomes the household's.
old_cfg = settings.load(); old_cfg["forecast"] = {"mode": "project", "monthly": 250,
                                                  "rate": 4, "years": 30, "target": 0}
settings.save(old_cfg)
r = c.get("/forecast")
check("a flat plan from before is read as the household's", b'value="250"' in r.data, True)
c.post("/forecast", data={"mode": "project", "monthly": "300", "years": "10", "rate": "5"})
c.post("/view", data={"person": str(sam_id), "next": "/"})
c.post("/settings", data={"form": "person_delete", "id": str(sam_id)}, follow_redirects=True)
check("a removed person's plan goes with them",
      f"person:{sam_id}" in settings.load()["forecast"], False)
c.post("/settings", data={"form": "person_add", "name": "Sam"})
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
print("\n23. Net worth over time, bank connection health, retirement")
# ---------------------------------------------------------------------------
from app import history                                               # noqa: E402
from datetime import date as _date                                    # noqa: E402

# History is rebuilt from the readings: a fresh account with balance
# readings on three days, and a holding bought on the second.
r = c.post("/accounts/new", data={"name": "History bank", "type": "bank", "currency": "EUR"})
hist_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.post("/accounts/new", data={"name": "History broker", "type": "broker", "currency": "EUR"})
hist_broker = int(r.headers["Location"].rstrip("/").split("/")[-1])
with db.get_conn() as conn:
    for day, amount in (("2026-06-01", 1000), ("2026-06-15", 1500), ("2026-07-01", 1200)):
        conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                     "VALUES (?, ?, 'EUR', 'manual', ?)", (hist_id, amount, day))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, "
                 "currency, kind, isin, quantity, price, external_id) VALUES "
                 "(?, '2026-06-15', 'buy', -500, 'EUR', 'buy', 'XX0000000001', 10, 50, 'hist-1')",
                 (hist_broker,))
    conn.execute("INSERT INTO prices (isin, as_of, price, currency) VALUES "
                 "('XX0000000001', '2026-06-28', 60, 'EUR')")
h = history.series("EUR", [hist_id, hist_broker], "all", today=_date(2026, 7, 2))
by_day = {p["date"]: p for p in h["points"]}
check("the history starts with the first reading", h["first_date"], "2026-06-01")
check("...and covers every sampled day to today", h["points"][-1]["date"], "2026-07-02")
check("a day before the holding was bought is cash only", by_day["2026-06-02"]["net_worth"], 1000.0)
check("the day of the purchase values it at the price paid",
      by_day["2026-06-15"]["net_worth"], 1500.0 + 10 * 50)
check("a later day uses the market price on file", by_day["2026-06-29"]["net_worth"], 1500.0 + 10 * 60)
check("...and the newest balance reading", by_day["2026-07-02"]["net_worth"], 1200.0 + 600)
check("a range with no readings yet is empty, not zero",
      history.series("EUR", [hist_id], "1m", today=_date(2026, 5, 1))["start"], None)
check("a person with no accounts has no history", history.series("EUR", [], "all")["points"][-1]["net_worth"], None)
check("the period's first day is the start of the year for YTD",
      history.period_start("ytd", _date(2026, 7, 2)), _date(2026, 1, 1))
check("a long range is thinned to a fixed number of points",
      len(history.series("EUR", [hist_id, hist_broker], "all", today=_date(2036, 7, 2))["points"]) <= history.MAX_POINTS, True)

# The two tiles under the hero: a month back, and the year so far.
ch = history.changes(1800.0, "EUR", [hist_id, hist_broker], today=_date(2026, 7, 2))
check("a month back is 30 days before today", ch["month"]["since"], "2026-06-02")
check("...valued as the chart would value that day", ch["month"]["from"], 1000.0)
check("...and the change is against the number in the hero", (ch["month"]["diff"], round(ch["month"]["pct"], 1)), (800.0, 80.0))
check("the year starts where the records do, when that is later than 1 January",
      ch["ytd"]["since"], "2026-06-01")
ch = history.changes(1800.0, "EUR", [hist_id], today=_date(2026, 6, 1))
check("a change measured from no reading is no change", ch["month"]["diff"], None)
check("...and says which day it would have compared with", ch["month"]["since"], "2026-06-01")

r = c.get("/")
check("the overview carries the chart", b"chart-networth" in r.data, True)
check("...the four tiles under it", (b"Liquid + investments" in r.data, b"This month" in r.data, b"YTD" in r.data), (True, True, True))
check("...with the change coloured by its sign",
      (b'class="stat-value gain">+' in r.data) or (b'class="stat-value loss">' in r.data) or (b"no reading to compare with yet" in r.data), True)
check("...and the two donuts, by asset class and by account",
      (b"By asset class" in r.data, b"By account" in r.data), (True, True))
check("...and says how far back the records go", b"Records go back to" in r.data, True)
r = c.get("/api/networth?period=3m")
check("the chart's data is served as JSON", r.status_code, 200)
check("...for the period asked", r.get_json()["period"], "3m")
check("...and an unknown period falls back", c.get("/api/networth?period=x").get_json()["period"], "ytd")

# Connection health: the fake bank's link, graded.
from datetime import datetime as _dtm, timezone as _tz, timedelta as _td   # noqa: E402
now = _dtm.now(_tz.utc)
h = banksync.health(now)
check("every connection is graded", len(h), 1)
check("a connection synced just now with months of consent is green", h[0]["status"], "green")
with db.get_conn() as conn:
    conn.execute("UPDATE bank_links SET last_sync_at = ?", ((now - _td(hours=30)).isoformat(),))
check("a day without a sync is yellow", banksync.health(now)[0]["hint"], "old")
with db.get_conn() as conn:
    conn.execute("UPDATE bank_links SET last_sync_at = ?", ((now - _td(days=3)).isoformat(),))
check("three days without one is red", banksync.health(now)[0]["hint"], "stale")
with db.get_conn() as conn:
    conn.execute("UPDATE bank_links SET last_sync_at = ?, valid_until = ?",
                 (now.isoformat(), (now + _td(days=5)).isoformat()))
check("a consent about to expire is flagged before a fresh sync can hide it",
      banksync.health(now)[0]["hint"], "expiring")
with db.get_conn() as conn:
    conn.execute("UPDATE bank_links SET valid_until = ?", ((now - _td(days=1)).isoformat(),))
check("an expired consent is red whatever else is true", banksync.health(now)[0]["hint"], "expired")
r = c.get("/")
check("the overview shows the connections card", b"Bank connections" in r.data, True)
check("...with the problem spelled out", b"Consent expired" in r.data, True)
with db.get_conn() as conn:
    conn.execute("UPDATE bank_links SET valid_until = ?", ((now + _td(days=80)).isoformat(),))

# Retirement: a birthday per person, and the outlook from it.
sam_id = people.all_people()[0]["id"]
r = c.post("/settings", data={"form": "person_rename", "id": str(sam_id), "name": "Sam",
                              "birthday": "2099-01-01"}, follow_redirects=True)
check("a birthday in the future is refused", b"needs to be a date" in r.data, True)
c.post("/settings", data={"form": "person_rename", "id": str(sam_id), "name": "Sam",
                          "birthday": "1980-06-15"})
check("a birthday is kept", people.all_people()[0]["birthday"], "1980-06-15")
check("age is fractional", people.age_on("1980-06-15", _date(2026, 6, 15)), 46.0)
check("...to the day", people.age_on("1980-06-15", _date(2026, 12, 15)), 46.5)

o = forecast.retirement(100000, 500, 0.0, 47.5, 65, today=_date(2026, 9, 11))
check("the months to go come from the fractional age", o["months_to_go"], 210)
check("at 0 % the sum at retirement is deposits", o["at_retirement"], 100000 + 500 * 210)
check("...the 4 % rule turns it into a monthly figure",
      round(o["monthly_income"], 2), round((100000 + 500 * 210) * 0.04 / 12, 2))
check("the path ends at the retirement age", o["points"][-1]["age"], 65.0)
check("...in the right year", o["retire_year"], 2044)
check("somebody past the age is told so", forecast.retirement(1, 1, 5, 70, 65)["retired_already"], True)
cleaned = forecast.clean_retirement({"retire_age": "30", "rate": "6", "monthly": ""})
check("the retirement age is bounded", cleaned["retire_age"], forecast.MIN_RETIRE_AGE)
check("an empty monthly means: from the Forecast plan", cleaned["monthly"], None)

c.post("/view", data={"person": "", "next": "/"})
r = c.get("/forecast")
check("the forecast page shows Sam's outlook", b"Retirement outlook" in r.data and b"Retire at" in r.data, True)
check("...with the monthly amount taken from the Forecast plan", b"taken from this person" in r.data, True)
r = c.post("/forecast", data={"form": "retirement", "person": str(sam_id), "retire_age": "62",
                              "rate": "4", "monthly": "750"}, follow_redirects=True)
check("retirement settings are kept per person",
      settings.load()["retirement"][f"person:{sam_id}"]["retire_age"], 62)
check("...and a typed monthly overrides the plan", b"Overrides the Forecast plan" in r.data, True)
check("...and the plan itself is untouched", settings.load()["forecast"]["all"]["years"], 10)
c.post("/settings", data={"form": "person_add", "name": "Kim"})
r = c.get("/forecast")
check("a person without a birthday is named, not silently skipped", b"No birthday on file for Kim" in r.data, True)

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
           for f in ("main.py", "categories.py", "auth.py", "manual.py", "loans.py", "splits.py", "allocation.py", "bills.py", "goals.py", "retirement.py",
                     "screener.py", "screener_etf.py", "report.py")]


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
    keys |= {f"{v} [class]" for v in main.ASSET_CLASS_LABELS.values()}
    keys |= {f"{v} [region]" for v in main.REGION_LABELS.values()}
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
# The name of this check said "comma" while the assertion pinned a
# non-breaking space, and the assertion won for as long as nobody read
# both. English groups with a comma — en-GB and en-US alike — so the
# behaviour now matches what this check always claimed to be testing.
check("English groups with a comma and a dot",
      i18n.money(1234.5, "EUR", "en"), "1,234.50\u00a0EUR")
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
      "Lebensmittel".encode() in c.get("/settings/categories").data, True)

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
      "Courses".encode() in c.get("/settings/categories").data, True)
check("...and the German labels are gone",
      "Lebensmittel".encode() in c.get("/settings/categories").data, False)

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
      "Bouffe".encode() in c.get("/settings/categories").data, True)

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

# Is there a newer version. A pipx install has nobody to tell it, so
# the app asks PyPI once a day and the badge in the menu grows a dot.
from app import updates                                         # noqa: E402

check("versions compare as numbers, not strings", updates.is_newer("0.10.0", "0.9.0"), True)
check("...and the same version is not newer", updates.is_newer(__version__), False)
check("...nor an older one", updates.is_newer("0.1.0"), False)
check("...nor garbage", updates.is_newer("latest"), False)
check("never checked means due", updates.is_stale(), True)


class _FakeResponse:
    def __init__(self, body): self.body = body
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *a): return False


_real_urlopen = updates.urllib.request.urlopen
asked = []
updates.urllib.request.urlopen = lambda req, timeout=0: (asked.append(req.full_url) or
                                                         _FakeResponse(b'{"info": {"version": "99.0.0"}}'))
try:
    check("the check asks PyPI for the project's JSON", updates.check(), "99.0.0")
    check("...at the public URL", asked, [updates.PYPI_URL])
    check("...and is then not due again today", updates.is_stale(), False)
    check("a newer answer is available to the pages", updates.available(), "99.0.0")
    r = c.get("/")
    body = r.data.decode()
    check("the version badge gets its dot", 'version-badge has-update' in body, True)
    check("...naming the version", "Version 99.0.0 is available." in body, True)
    r = c.get("/changelog", headers={"X-Ingress-Path": "/api/hassio_ingress/x"})
    check("through Home Assistant the advice is the add-on's",
          "Update the add-on in Home Assistant." in r.data.decode(), True)
    check("...and elsewhere it is not", "add-on in Home Assistant" in body, False)
    updates.urllib.request.urlopen = lambda req, timeout=0: (_ for _ in ()).throw(OSError("no route"))
    check("a failed check is None, not an exception", updates.check(), None)
    check("...and the last good answer stands", updates.available(), "99.0.0")
finally:
    updates.urllib.request.urlopen = _real_urlopen
    db.set_state("latest_version", __version__)
check("running the newest, nothing is available", updates.available(), None)
check("...and the badge is plain again", 'has-update' in c.get("/").data.decode(), False)
check("the check is on by default", settings.DEFAULTS["check_updates"], True)
c.post("/settings", data={"form": "general", "base_currency": "EUR",
                          "redirect_url": "http://localhost:8000/connect/callback"})
check("...and the switch under Settings turns it off", settings.load()["check_updates"], False)
c.post("/settings", data={"form": "general", "base_currency": "EUR", "check_updates": "1",
                          "redirect_url": "http://localhost:8000/connect/callback"})
check("...and on", settings.load()["check_updates"], True)

# The Home Assistant add-on pulls the image tagged with the version in
# its config.yaml. A version there that was never tagged is an add-on
# that installs nothing.
addon_cfg = (REPO / "homeassistant" / "wealth-dashboard" / "config.yaml").read_text()
addon_version = re.search(r'^version:\s*"?([\d.]+)"?\s*$', addon_cfg, re.M)
check("the Home Assistant add-on names the same version",
      addon_version and addon_version.group(1), __version__)
check("...and the same image the workflow publishes",
      "image: ghcr.io/halvar20000/wealth-dashboard\n" in addon_cfg, True)
check("...with its changelog being the app's",
      (REPO / "homeassistant" / "wealth-dashboard" / "CHANGELOG.md").resolve(),
      (REPO / "CHANGELOG.md").resolve())

# Behind a reverse proxy that mounts the app under a prefix — Home
# Assistant's ingress, nginx with X-Forwarded-Prefix — every link, form
# action, fetch() and redirect has to carry the prefix, or the first
# click leaves the app. The test client can say the header itself.
ingress = {"X-Ingress-Path": "/api/hassio_ingress/abc"}
r = c.get("/", headers=ingress)
check("under a prefix the page renders", r.status_code, 200)
body = r.data.decode()
check("...links carry the prefix", 'href="/api/hassio_ingress/abc/transactions"' in body, True)
check("...and so does the stylesheet", '/api/hassio_ingress/abc/static/' in body, True)
check("...while no link points at the root",
      re.search(r'(href|action)="/(?!api/hassio_ingress/)', body) is None, True)
r = c.get("/transactions", headers=ingress)
check("a form's action carries the prefix",
      'action="/api/hassio_ingress/abc/transactions/' in r.data.decode(), True)
r = c.post("/view", data={"next": "/transactions"}, headers=ingress)
check("a 'back to where you were' redirect carries it too",
      r.headers.get("Location"), "/api/hassio_ingress/abc/transactions")
r = c.post("/view", data={"next": "//evil.example"}, headers=ingress)
check("...and a bad one still falls back inside the app",
      r.headers.get("Location"), "/api/hassio_ingress/abc/")
r = c.get("/", headers={"X-Ingress-Path": "//evil.example"})
check("a prefix that is a host is ignored", 'href="//evil' in r.data.decode(), False)
r = c.get("/", headers={"X-Forwarded-Prefix": "/wealth/"})
check("X-Forwarded-Prefix works the same, trailing slash dropped",
      'href="/wealth/transactions"' in r.data.decode(), True)

# The changelog ships in the image, so the page is not empty for the
# people who install it rather than clone it.
dockerignore = (REPO / ".dockerignore").read_text()
check("the build context keeps CHANGELOG.md", "!CHANGELOG.md" in dockerignore, True)
check("...and the Dockerfile copies it",
      "COPY CHANGELOG.md" in (REPO / "Dockerfile").read_text(), True)
check("the image drops root through the entrypoint",
      ("/entrypoint.sh" in (REPO / "Dockerfile").read_text(), "setpriv" in (REPO / "docker" / "entrypoint.sh").read_text(),
       "PUID" in (REPO / "templates" / "wealth-dashboard.xml").read_text()), (True, True, True))
# The first start of a different version copies the database aside
# before touching it, so a rollback has something to go back to.
import sqlite3 as _sq
_bk = TMP / "bk"; _bk.mkdir()
_dbp = db.init_db(_bk / "wealth.db")
check("a fresh database is not backed up", (_bk / "backups").exists(), False)
db.init_db(_dbp)
check("...nor is one the same version opened before", (_bk / "backups").exists(), False)
with _sq.connect(_dbp) as _c:
    _c.execute("UPDATE app_state SET value = '0.50.0' WHERE key = 'last_version'")
db.init_db(_dbp)
_copies = sorted((_bk / "backups").glob("*.db"))
check("a database last opened by another version is copied aside first, named after that version",
      (len(_copies), _copies[0].name.startswith("wealth-0.50.0-")), (1, True))
with _sq.connect(_copies[0]) as _c:
    check("...and the copy is a database", _c.execute("SELECT value FROM app_state WHERE key = 'last_version'").fetchone()[0], "0.50.0")
with _sq.connect(_dbp) as _c:
    check("...after which the version on record is this one",
          _c.execute("SELECT value FROM app_state WHERE key = 'last_version'").fetchone()[0], __version__)
for _i in range(db.KEEP_BACKUPS + 2):
    with _sq.connect(_dbp) as _c:
        _c.execute("UPDATE app_state SET value = ? WHERE key = 'last_version'", (f"0.4{_i}.0",))
    db.init_db(_dbp)
check("only the newest few are kept", len(list((_bk / "backups").glob("*.db"))), db.KEEP_BACKUPS)
workflow = (REPO / ".github" / "workflows" / "docker-image.yml").read_text()
check("...and editing it rebuilds the image",
      "'**.md'" in workflow, False)

# The PyPI package: `pipx install wealth-dashboard`. The code is the
# same `app/` mapped to the import name `wealth_dashboard`, and what
# the image gets from the repo — the changelog, the dependencies — the
# package has to carry itself.
pyproject = (REPO / "pyproject.toml").read_text()
check("the package maps app/ to wealth_dashboard",
      'package-dir = { "wealth_dashboard" = "app" }' in pyproject, True)
check("...with the version read from the code, not typed again",
      'attr = "wealth_dashboard.__version__"' in pyproject, True)
pins = re.findall(r'^\s*"([A-Za-z]+[^"]*)",\s*$', pyproject.split("dependencies = [", 1)[1].split("]", 1)[0], re.M)
wants = [ln.split("#", 1)[0].strip() for ln in (REPO / "requirements.txt").read_text().splitlines()]
check("...and the same dependencies as requirements.txt",
      pins, [w for w in wants if w])
check("the changelog is inside the package",
      (REPO / "app" / "CHANGELOG.md").resolve(), (REPO / "CHANGELOG.md").resolve())
check("...and the package data ships it", '"CHANGELOG.md"' in pyproject, True)
check("...and the app finds it there", changelog.CHANGELOG_PATH.is_file(), True)
ep = re.search(r'^wealth-dashboard = "wealth_dashboard\.(\w+):(\w+)"', pyproject, re.M)
from app import cli                                             # noqa: E402
check("the command line entry point exists",
      ep and callable(getattr(__import__("app." + ep.group(1), fromlist=[ep.group(2)]), ep.group(2), None)), True)

buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        cli.main(["--version"])
except SystemExit as exc:
    check("--version exits cleanly", exc.code, 0)
check("...naming the version", buf.getvalue().strip(), f"wealth-dashboard {__version__}")

# Installed rather than cloned, data goes where the OS keeps a user's
# files — not next to the code, which the next upgrade replaces.
_xdg = os.environ.get("XDG_DATA_HOME")
os.environ["XDG_DATA_HOME"] = "/tmp/xdg-test"
try:
    if sys.platform.startswith("linux"):
        check("on Linux the user data folder follows XDG",
              str(settings.user_data_dir()), "/tmp/xdg-test/wealth-dashboard")
finally:
    if _xdg is None:
        del os.environ["XDG_DATA_HOME"]
    else:
        os.environ["XDG_DATA_HOME"] = _xdg
# `wealth-dashboard install`: a shortcut and start-at-login, written
# into this user's folders and nowhere else — so a throwaway HOME shows
# everything it touches, and uninstall must leave only the data.
from app import launcher                                        # noqa: E402

if sys.platform.startswith("linux"):
    fake_home = pathlib.Path(TMP) / "home"
    (fake_home / "Desktop").mkdir(parents=True)
    _saved = {k: os.environ.get(k) for k in ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME")}
    os.environ["HOME"] = str(fake_home)
    os.environ.pop("XDG_DATA_HOME", None)
    os.environ.pop("XDG_CONFIG_HOME", None)
    # Record the systemctl calls instead of making them: the suite must
    # not enable a real service on the machine running it.
    calls: list[list[str]] = []
    _real_run = launcher._run
    launcher._run = lambda cmd: calls.append(cmd) is None
    try:
        written = launcher.install(["--port", "8123"])
        entry = fake_home / ".local" / "share" / "applications" / "wealth-dashboard.desktop"
        check("install writes a menu entry", entry.is_file(), True)
        text = entry.read_text()
        check("...that runs this interpreter with -m, not a PATH lookup",
              f"Exec={sys.executable} -m app --port 8123" in text, True)
        check("...from the checkout, which is where `-m app` imports from",
              f"Path={REPO}" in text, True)
        check("...without a terminal", "Terminal=false" in text, True)
        check("...and a copy on the desktop, executable so GNOME trusts it",
              (fake_home / "Desktop" / "wealth-dashboard.desktop").stat().st_mode & 0o100, 0o100)
        check("...and the icon where the menu looks for it",
              (fake_home / ".local/share/icons/hicolor/512x512/apps/wealth-dashboard.png").is_file(), True)
        service = fake_home / ".config" / "systemd" / "user" / "wealth-dashboard.service"
        autostart = fake_home / ".config" / "autostart" / "wealth-dashboard.desktop"
        check("start-at-login is a user service or, without systemd, an autostart entry",
              service.is_file() or autostart.is_file(), True)
        login_text = (service if service.is_file() else autostart).read_text()
        check("...which does not try to open a browser at boot",
              "--no-browser" in login_text, True)
        check("...and every written path is reported", len(written) >= 3, True)
        gone = launcher.uninstall()
        check("uninstall removes what install wrote",
              [p for p in (entry, service, autostart, fake_home / "Desktop" / "wealth-dashboard.desktop")
               if p.exists()], [])
        check("...and reports it", len(gone) >= 3, True)
        if service.exists() or any(c[:2] == ["systemctl", "--user"] for c in calls):
            check("with systemd the service is enabled and started, then disabled",
                  [c[2:4] for c in calls if c[:2] == ["systemctl", "--user"] and c[2] in ("enable", "disable")],
                  [["enable", "--now"], ["disable", "--now"]])
    finally:
        launcher._run = _real_run
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

# The Windows icon is the PNG in an .ico envelope — check the envelope,
# since no Windows is going to.
ico = pathlib.Path(TMP) / "t.ico"
launcher._ico_from_png(launcher.ICON, ico)
raw = ico.read_bytes()
check("the .ico header says one icon", raw[:6], b"\x00\x00\x01\x00\x01\x00")
check("...whose bytes are the PNG itself", raw[22:], launcher.ICON.read_bytes())
ps = launcher._ps_shortcut(pathlib.Path("DESKTOP") / "Wealth Dashboard.lnk",
                           ["C:\\py\\pythonw.exe", "-m", "wealth_dashboard", "--no-browser"], pathlib.Path("C:\\i.ico"))
check("a desktop shortcut on Windows asks Windows where the desktop is",
      "GetFolderPath('Desktop')" in ps and "$s.Arguments = '-m wealth_dashboard --no-browser'" in ps, True)

# A second start on the same port is not an error: it opens the running one.
check("nothing listening means not running", cli.running_version("127.0.0.1", "1"), None)

_wd = os.environ.pop("WD_DATA_DIR")
try:
    if not (pathlib.Path("/data").is_dir() and os.access("/data", os.W_OK)):
        check("a checkout keeps its data beside the repo",
              settings._data_dir(), REPO / "data")
finally:
    os.environ["WD_DATA_DIR"] = _wd

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

# The whole table is read once and kept — the Portfolio page used to
# read two hundred thousand rows per holding — but kept is not stale: a
# rate planted, changed in place or removed under it is seen on the
# next read, with no restart.
days_, table_ = fx.table()
check("the kept table has every day", days_, ["2026-09-08", "2026-09-09"])
check("...and the euro as 1 on each", table_["2026-09-09"]["EUR"], 1.0)
check("...and is the same object the next time round", fx.table()[1] is table_, True)
with db.get_conn() as conn:
    conn.execute("INSERT OR REPLACE INTO fx_rates (as_of, currency, per_eur) "
                 "VALUES ('2026-09-09', 'USD', 2.0)")
check("a rate changed in place is seen", fx.table()[1]["2026-09-09"]["USD"], 2.0)
with db.get_conn() as conn:
    conn.execute("DELETE FROM fx_rates WHERE as_of = '2026-09-08'")
check("...and so is a day removed", fx.table()[0], ["2026-09-09"])
fx.store(days)
check("...and the rates put back", fx.table()[1]["2026-09-09"]["USD"], 1.1652)

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
r = c.get("/settings/market")
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
                "instrumentType": "ETF",
                "regularMarketPrice": 126.17, "regularMarketTime": 1789119714}}]}},
    "VWCE.DE": {"chart": {"result": [{"meta": {"symbol": "VWCE.DE", "currency": "EUR",
                "regularMarketPrice": 140.5, "regularMarketTime": 1789119714}}]}},
    "SIE.DE": {"chart": {"result": [{"meta": {"symbol": "SIE.DE", "currency": "EUR",
               "instrumentType": "EQUITY",
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
r = c.get("/settings/market")
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
print("\n24. Share Ideas")
# ---------------------------------------------------------------------------
# Four boards over two caches, scored from canned Yahoo answers. The unit
# traps are the reason most of this exists: Yahoo reports the same
# quantity as a fraction and as a percent depending on the field and the
# day, and each one is a silent 100x error in a ranking.
from datetime import date, timedelta                        # noqa: E402
from app import screener, screener_etf, screener_jobs, yahoo   # noqa: E402


def near(want, tol=1e-6):
    return lambda got: got is not None and abs(got - want) < tol


# The flattener: quoteSummary wraps every value and sends {} for absent.
flat = yahoo._flatten({
    "price": {"longName": "Sanofi", "exchangeName": "Paris", "quoteType": "EQUITY",
              "regularMarketPrice": {"raw": 73.45, "fmt": "73.45"},
              "marketCap": {"raw": 8.8e10, "fmt": "88B"}},
    "summaryDetail": {"dividendYield": {"raw": 0.056, "fmt": "5.60%"},
                      "marketCap": {"raw": 1, "fmt": "1"}, "yield": {}},
    "fundProfile": {"family": "Vanguard", "categoryName": None,
                    "feesExpensesInvestment": {
                        "annualReportExpenseRatio": {"raw": 0.0029, "fmt": "0.29%"},
                        "netExpRatio": {}}},
})
check("wrapped values are unwrapped", flat["regularMarketPrice"], 73.45)
check("an empty {} is missing, not a dict", "yield" in flat, False)
check("the first module's figure wins", flat["marketCap"], 8.8e10)
check("nested fee blocks are flattened", flat["annualReportExpenseRatio"], 0.0029)
check("names the screener expects are filled in",
      (flat["fullExchangeName"], flat["fundFamily"]), ("Paris", "Vanguard"))

# The chart reply: adjusted closes and paid distributions in one call.
hist = yahoo.history("VHYL.AS", get=lambda url: {"chart": {"result": [{
    "meta": {"currency": "EUR", "instrumentType": "ETF"},
    "timestamp": [1600000000, 1600604800, 1601209600],
    "indicators": {"quote": [{"close": [42.5, 42.7, None]}],
                   "adjclose": [{"adjclose": [34.9, 35.0, None]}]},
    "events": {"dividends": {"1600930800": {"amount": 0.41, "date": 1600930800}}},
}]}})
check("adjusted closes are used, not raw", hist["closes"][0][1], 34.9)
check("a missing bar is dropped", len(hist["closes"]), 2)
check("distributions come with the same reply", hist["dividends"], [("2020-09-24", 0.41)])
check("...and so does the instrument type", hist["quote_type"], "ETF")
err = None
try:
    yahoo.history("NOPE.XX", get=lambda url: {"chart": {"result": None, "error": {
        "code": "Not Found", "description": "No data found, symbol may be delisted"}}})
except prices.PriceError as exc:
    err = str(exc)
check("a delisted symbol is a sentence", "delisted" in (err or ""), True)

# --- unit normalisation ---
g = screener.normalise({"dividendYield": 3.6, "debtToEquity": 62.0,
                        "fiveYearAvgDividendYield": 3.2, "payoutRatio": 0.48,
                        "returnOnEquity": 0.19, "currentPrice": 70.0})
f = screener.normalise({"dividendYield": 0.036, "debtToEquity": 0.62,
                        "fiveYearAvgDividendYield": 3.2, "payoutRatio": 0.48,
                        "returnOnEquity": 0.19, "currentPrice": 70.0})
check("percent dividendYield 3.6 → 0.036", g["dividend_yield"], predicate=near(0.036))
check("fraction dividendYield 0.036 → 0.036", f["dividend_yield"], predicate=near(0.036))
check("debtToEquity 62.0 (percent) → 0.62", g["debt_to_equity"], predicate=near(0.62))
check("debtToEquity 0.62 (ratio) stays 0.62", f["debt_to_equity"], predicate=near(0.62))
check("5y avg yield 3.2 → 0.032", g["div_yield_5y_avg"], predicate=near(0.032))
check("absurd yield discarded",
      screener.normalise({"dividendYield": 45.0, "currentPrice": 10.0})["dividend_yield"], None)
check("yield derived from rate/price when the field is absent",
      screener.normalise({"trailingAnnualDividendRate": 2.0, "currentPrice": 50.0})["dividend_yield"],
      predicate=near(0.04))
check("NaN survives as None", screener._num(float("nan")), None)

# --- ramps, plateau, blend ---
check("ramp at the poor end = 0", screener._ramp(0.05, 0.05, 0.40), predicate=near(0.0))
check("ramp at the good end = 100", screener._ramp(0.40, 0.05, 0.40), predicate=near(100.0))
check("ramp clamps", screener._ramp(0.90, 0.05, 0.40), predicate=near(100.0))
check("inverted ramp: P/E 16.5 is mid", screener._ramp(16.5, 25.0, 8.0), predicate=near(50.0))
check("missing input is None, not 0", screener._ramp(None, 0, 1), None)
check("payout 0.40 is in the sweet spot", screener._plateau(0.40, 0.25, 0.60), predicate=near(100.0))
check("payout 1.20 is well outside", screener._plateau(1.20, 0.25, 0.60),
      predicate=lambda v: v is not None and v < 5)
sc, cov = screener._blend({"a": 80.0, "b": None}, {"a": 0.5, "b": 0.5})
check("a missing field does not drag the score down", sc, predicate=near(80.0))
check("...but coverage records the gap", cov, predicate=near(0.5))
check("nothing present → no score", screener._blend({}, {"a": 1.0}), (None, 0.0))

# --- derived figures ---
check("drawdown 70 vs high 100 = 30%",
      screener.drawdown({"price": 70.0, "week52_high": 100.0}), predicate=near(0.30))
check("a price above its own high clamps to 0",
      screener.drawdown({"price": 110.0, "week52_high": 100.0}), predicate=near(0.0))
check("negative trailing P/E falls back to forward",
      screener.effective_pe({"trailing_pe": -5.0, "forward_pe": 9.5}), predicate=near(9.5))
check("no positive earnings anywhere → None",
      screener.effective_pe({"trailing_pe": -5.0, "forward_pe": None}), None)

# --- the share cache, from canned fundamentals ---
FAKE = {
    "GOOD.PA": {"longName": "Good Industrials SA", "sector": "Industrials",
                "industry": "Machinery", "country": "France", "currency": "EUR",
                "quoteType": "EQUITY", "currentPrice": 70.0, "marketCap": 24e9,
                "trailingPE": 11.0, "forwardPE": 10.0, "priceToBook": 1.8,
                "dividendYield": 3.6, "payoutRatio": 0.48, "fiveYearAvgDividendYield": 3.2,
                "returnOnEquity": 0.19, "operatingMargins": 0.16, "profitMargins": 0.11,
                "debtToEquity": 62.0, "currentRatio": 1.7, "revenueGrowth": 0.04,
                "earningsGrowth": 0.02, "fiftyTwoWeekHigh": 100.0, "fiftyTwoWeekLow": 64.0},
    "FRACY.DE": {"longName": "Fraction Reporting AG", "sector": "Industrials",
                 "country": "Germany", "currency": "EUR", "quoteType": "EQUITY",
                 "currentPrice": 70.0, "marketCap": 24e9, "trailingPE": 11.0,
                 "forwardPE": 10.0, "priceToBook": 1.8, "dividendYield": 0.036,
                 "payoutRatio": 0.48, "fiveYearAvgDividendYield": 3.2,
                 "returnOnEquity": 0.19, "operatingMargins": 0.16, "profitMargins": 0.11,
                 "debtToEquity": 0.62, "currentRatio": 1.7, "revenueGrowth": 0.04,
                 "earningsGrowth": 0.02, "fiftyTwoWeekHigh": 100.0, "fiftyTwoWeekLow": 64.0},
    "NODIV.MI": {"longName": "No Dividend SpA", "sector": "Technology", "country": "Italy",
                 "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 40.0,
                 "marketCap": 8e9, "trailingPE": 9.0, "priceToBook": 1.2,
                 "dividendYield": None, "payoutRatio": 0.0, "returnOnEquity": 0.22,
                 "operatingMargins": 0.20, "debtToEquity": 30.0, "currentRatio": 2.4,
                 "fiftyTwoWeekHigh": 70.0, "fiftyTwoWeekLow": 38.0},
    "LOSS.AS": {"longName": "Turnaround NV", "sector": "Consumer Cyclical",
                "country": "Netherlands", "currency": "EUR", "quoteType": "EQUITY",
                "currentPrice": 12.0, "marketCap": 3e9, "trailingPE": None, "forwardPE": 9.5,
                "priceToBook": 0.9, "dividendYield": 2.5, "payoutRatio": 0.40,
                "returnOnEquity": 0.09, "operatingMargins": 0.06, "debtToEquity": 80.0,
                "currentRatio": 1.2, "earningsGrowth": -0.35,
                "fiftyTwoWeekHigh": 22.0, "fiftyTwoWeekLow": 11.4},
    "TRAP.L": {"longName": "Yield Trap plc", "sector": "Utilities", "country": "United Kingdom",
               "currency": "GBP", "quoteType": "EQUITY", "currentPrice": 50.0,
               "marketCap": 5e9, "trailingPE": 12.0, "priceToBook": 0.7,
               "dividendYield": 11.0, "payoutRatio": 1.40, "fiveYearAvgDividendYield": 4.5,
               "returnOnEquity": 0.06, "operatingMargins": 0.09, "debtToEquity": 260.0,
               "currentRatio": 0.7, "fiftyTwoWeekHigh": 96.0, "fiftyTwoWeekLow": 49.0},
    "TINY.BR": {"longName": "Small Cap NV", "sector": "Industrials", "country": "Belgium",
                "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 9.0,
                "marketCap": 2e8, "trailingPE": 8.0, "dividendYield": 4.0,
                "payoutRatio": 0.35, "returnOnEquity": 0.15, "debtToEquity": 40.0,
                "fiftyTwoWeekHigh": 15.0, "fiftyTwoWeekLow": 8.5},
    "THIN.MC": {"longName": "Thin Data SA", "sector": "Energy", "country": "Spain",
                "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 20.0,
                "marketCap": 6e9, "trailingPE": 10.0, "dividendYield": 4.5,
                "fiftyTwoWeekHigh": 30.0, "fiftyTwoWeekLow": 19.0},
    "DEAD.XX": {},
}
with db.get_conn() as conn:
    res = screener.refresh(conn, symbols=list(FAKE), force=True,
                           fetcher=lambda s: dict(FAKE.get(s, {})))
check("every live symbol fetched", res["ok"], len(FAKE) - 1)
check("the dead one is recorded as failed", res["failed"], 1)
with db.get_conn() as conn:
    row = dict(conn.execute("SELECT * FROM screener_fundamentals WHERE symbol='GOOD.PA'").fetchone())
    dead = dict(conn.execute("SELECT * FROM screener_fundamentals WHERE symbol='DEAD.XX'").fetchone())
check("stored yield is the fraction", row["dividend_yield"], predicate=near(0.036))
check("stored debt/equity is the ratio", row["debt_to_equity"], predicate=near(0.62))
check("the dead symbol carries an error and no fabricated price",
      (bool(dead["last_error"]), dead["price"]), (True, None))


def boom(sym):
    raise TimeoutError("boom")


with db.get_conn() as conn:
    screener.refresh(conn, symbols=["GOOD.PA"], force=True, fetcher=boom)
    row2 = dict(conn.execute("SELECT * FROM screener_fundamentals WHERE symbol='GOOD.PA'").fetchone())
    again = screener.refresh(conn, symbols=["GOOD.PA"], force=True,
                             fetcher=lambda s: dict(FAKE[s]))
    skip = screener.refresh(conn, symbols=["GOOD.PA"],
                            fetcher=lambda s: dict(FAKE[s]))
check("a failed refetch keeps the previous price", row2["price"], predicate=near(70.0))
check("...and stamps the error", row2["last_error"], "TimeoutError: boom")
check("a fresh row is skipped, not refetched", (skip["skipped"], skip["attempted"]), (1, 0))

with db.get_conn() as conn:
    data = screener.results(conn, top=500, include_failed=True)
ranked = {r["symbol"]: r for r in data["ranked"]}
gated = {r["symbol"]: r for r in data["rejected"]}
check("GOOD.PA is ranked", "GOOD.PA" in ranked, True)
check("NODIV.MI is gated for paying no dividend",
      "pays no dividend" in (gated.get("NODIV.MI") or {}).get("gate_failed", []), True)
check("TINY.BR is gated for being too small",
      any(x.startswith("too small") for x in gated["TINY.BR"]["gate_failed"]), True)
check("a gated row carries no score", gated["NODIV.MI"]["score"], None)
check("LOSS.AS ranks on its forward P/E", ranked["LOSS.AS"]["pe_basis"], "forward")
check("TRAP.L is not gated (140% payout is under the 150% limit)", "TRAP.L" in ranked, True)
good, frac = ranked["GOOD.PA"], ranked["FRACY.DE"]
check("GOOD.PA scores well", good["score"], predicate=lambda v: v is not None and v >= 60)
check("percent and fraction reporting give the SAME score",
      abs(good["score"] - frac["score"]) < 0.05, True)
check("full data → full coverage", good["coverage"], predicate=near(1.0))
check("PEA-eligible (France)", good["pea_eligible"], True)
check("the UK is not EEA", ranked["TRAP.L"]["pea_eligible"], False)
check("the board is sorted best first",
      [r["score"] for r in data["ranked"]] == sorted((r["score"] for r in data["ranked"]), reverse=True), True)
thin = ranked["THIN.MC"]
check("a thin row still scores", thin["score"] is not None, True)
check("...but reports low coverage", thin["coverage"], predicate=lambda v: v < 0.6)
check("...its quality pillar is empty, not zero", thin["pillars"]["quality"], None)
check("...and is flagged", any("thin data" in x for x in thin["flags"]), True)
trap = ranked["TRAP.L"]["flags"]
check("yield trap: near its 52-week low", any("52-week low" in x for x in trap), True)
check("yield trap: payout above 90%", any("90%" in x for x in trap), True)
check("yield trap: yield far above its own average", any("5-year average" in x for x in trap), True)
check("yield trap: leverage called out", any("leveraged" in x for x in trap), True)
check("GOOD.PA carries no flags", good["flags"], [])
check("LOSS.AS flags the missing trailing profit",
      any("forward estimate" in x for x in ranked["LOSS.AS"]["flags"]), True)

# --- watchlist and filters ---
with db.get_conn() as conn:
    screener.set_watch(conn, "trap.l", "dismissed", "not touching it")
    d2 = screener.results(conn, top=500)
    screener.set_watch(conn, "TRAP.L", "watch")
    d3 = screener.results(conn, top=500)
    screener.set_watch(conn, "TRAP.L", None)
    d4 = screener.results(conn, top=500)
    pea = screener.results(conn, top=500, pea_only=True)
    top1 = screener.results(conn, top=1)
    sect = screener.results(conn, top=500, sectors=["Utilities"])
    hi = screener.results(conn, top=500, min_score=60)
r2 = {r["symbol"]: r for r in d2["ranked"]}["TRAP.L"]
r3 = {r["symbol"]: r for r in d3["ranked"]}["TRAP.L"]
r4 = {r["symbol"]: r for r in d4["ranked"]}["TRAP.L"]
check("watch status stored, symbol upper-cased", (r2["watch_status"], r2["note"]),
      ("dismissed", "not touching it"))
check("the note survives a status change without one", (r3["watch_status"], r3["note"]),
      ("watch", "not touching it"))
check("the mark can be cleared", r4["watch_status"], None)
check("the PEA filter drops the UK name and keeps the French one",
      ("TRAP.L" in {r["symbol"] for r in pea["ranked"]},
       "GOOD.PA" in {r["symbol"] for r in pea["ranked"]}), (False, True))
check("top-N is honoured", len(top1["ranked"]), 1)
check("the sector filter is honoured", {r["sector"] for r in sect["ranked"]}, {"Utilities"})
check("min_score is honoured", all(r["score"] >= 60 for r in hi["ranked"]), True)
try:
    with db.get_conn() as conn:
        screener.results(conn, profile="nonsense")
    check("an unknown profile is refused", False, True)
except ValueError:
    check("an unknown profile is refused", True, True)

# --- the universe: shipped, the user's file, and what is held ---
prices.refresh("EUR", get=fake_get)          # re-resolve, and store the types
with db.get_conn() as conn:
    held_now = screener.held_symbols(conn)
    uni = screener.load_universe(conn)
    etf_uni = screener_etf.load_universe(conn)
check("the shipped share universe is non-trivial", len(uni) > 250, True)
check("...with no duplicates", len(uni), len(set(uni)))
check("a held fund is typed from the price feed",
      held_now.get("IWDA.AS", {}).get("quote_type"), "ETF")
check("...and folded into the ETF universe, not the share one",
      ("IWDA.AS" in etf_uni, "IWDA.AS" in uni), (True, False))
check("...with its name", bool(etf_uni["IWDA.AS"].get("name")), True)
if "SIE.DE" in held_now:
    check("a held share goes to the share universe",
          ("SIE.DE" in uni, "SIE.DE" in etf_uni), (True, False))
screener.UNIVERSE_FILE.write_text('{"symbols": ["extra.pa"], "exclude": ["TTE.PA"]}')
with db.get_conn() as conn:
    uni2 = screener.load_universe(conn)
check("user additions are picked up, upper-cased", "EXTRA.PA" in uni2, True)
check("user exclusions are honoured even against the shipped list", "TTE.PA" in uni2, False)
screener.UNIVERSE_FILE.unlink()

# --- config sections do not leak into each other ---
screener.CONFIG_FILE.write_text(
    '{"gates": {"require_dividend": false, "max_pe": 99},'
    ' "income": {"gates": {"min_dividend_yield": 0.04}},'
    ' "etf": {"gates": {"max_ter": 0.001}}}')
vcfg, icfg, ecfg = screener.load_config("value"), screener.load_config("income"), \
    screener_etf.load_config("growth")
check("the value board reads the top level", vcfg["gates"]["max_pe"], 99)
check("siblings in the overridden section survive", vcfg["gates"]["min_market_cap"], 1e9)
check("untouched sections keep their defaults", vcfg["weights"]["quality"], 0.30)
check("the income board reads its own section", icfg["gates"]["min_dividend_yield"], 0.04)
check("the top level does not leak into the income board", icfg["gates"]["max_pe"], 40.0)
check("the ETF board reads its own section", ecfg["gates"]["max_ter"], 0.001)
check("...and keeps its own defaults", ecfg["weights"]["cost"], 0.30)
with db.get_conn() as conn:
    d5 = screener.results(conn, top=500)
check("NODIV.MI is rankable once the dividend gate is off",
      "NODIV.MI" in {r["symbol"] for r in d5["ranked"]}, True)
screener.CONFIG_FILE.unlink()

# --- the income board: highest dividend that is still growing ---
INCOME = {
    "ARIST.PA": {"longName": "Steady Dividend SA", "sector": "Consumer Defensive",
                 "country": "France", "currency": "EUR", "quoteType": "EQUITY",
                 "currentPrice": 100.0, "marketCap": 30e9, "trailingPE": 15.0,
                 "priceToBook": 2.4, "dividendYield": 4.2, "payoutRatio": 0.55,
                 "fiveYearAvgDividendYield": 4.0, "dividendRate": 4.20,
                 "trailingAnnualDividendRate": 3.96, "freeCashflow": 7e9,
                 "sharesOutstanding": 1e9, "returnOnEquity": 0.18,
                 "operatingMargins": 0.17, "profitMargins": 0.12, "debtToEquity": 70.0,
                 "currentRatio": 1.5, "revenueGrowth": 0.04, "earningsGrowth": 0.06,
                 "fiftyTwoWeekHigh": 108.0, "fiftyTwoWeekLow": 88.0},
    "CUTTER.DE": {"longName": "About To Cut AG", "sector": "Utilities", "country": "Germany",
                  "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 40.0,
                  "marketCap": 9e9, "trailingPE": 11.0, "priceToBook": 0.9,
                  "dividendYield": 6.5, "payoutRatio": 0.85, "fiveYearAvgDividendYield": 4.0,
                  "dividendRate": 1.82, "trailingAnnualDividendRate": 2.60,
                  "freeCashflow": 1e9, "sharesOutstanding": 225e6, "returnOnEquity": 0.10,
                  "operatingMargins": 0.11, "profitMargins": 0.07, "debtToEquity": 180.0,
                  "currentRatio": 0.9, "revenueGrowth": 0.01, "earningsGrowth": -0.05,
                  "fiftyTwoWeekHigh": 62.0, "fiftyTwoWeekLow": 39.0},
    "LOWY.MC": {"longName": "Token Payer SA", "sector": "Technology", "country": "Spain",
                "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 50.0,
                "marketCap": 12e9, "trailingPE": 22.0, "dividendYield": 1.2,
                "payoutRatio": 0.20, "dividendRate": 0.60, "trailingAnnualDividendRate": 0.55,
                "returnOnEquity": 0.24, "operatingMargins": 0.25, "revenueGrowth": 0.12,
                "earningsGrowth": 0.15, "fiftyTwoWeekHigh": 55.0, "fiftyTwoWeekLow": 38.0},
    "DISTRESS.MI": {"longName": "Fourteen Percent SpA", "sector": "Financial Services",
                    "country": "Italy", "currency": "EUR", "quoteType": "EQUITY",
                    "currentPrice": 10.0, "marketCap": 2e9, "trailingPE": 5.0,
                    "dividendYield": 14.0, "payoutRatio": 0.70, "dividendRate": 1.40,
                    "trailingAnnualDividendRate": 1.40, "returnOnEquity": 0.11,
                    "operatingMargins": 0.15, "revenueGrowth": 0.02,
                    "fiftyTwoWeekHigh": 24.0, "fiftyTwoWeekLow": 9.6},
    "SHRINK.AS": {"longName": "Melting Ice NV", "sector": "Communication Services",
                  "country": "Netherlands", "currency": "EUR", "quoteType": "EQUITY",
                  "currentPrice": 20.0, "marketCap": 7e9, "trailingPE": 10.0,
                  "dividendYield": 5.0, "payoutRatio": 0.60, "dividendRate": 1.00,
                  "trailingAnnualDividendRate": 1.00, "returnOnEquity": 0.12,
                  "operatingMargins": 0.14, "revenueGrowth": -0.08, "earningsGrowth": -0.10,
                  "fiftyTwoWeekHigh": 34.0, "fiftyTwoWeekLow": 19.0},
    "FCFBAD.BR": {"longName": "Cash Poor NV", "sector": "Utilities", "country": "Belgium",
                  "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 30.0,
                  "marketCap": 6e9, "trailingPE": 13.0, "dividendYield": 5.0,
                  "payoutRatio": 0.60, "dividendRate": 1.50, "trailingAnnualDividendRate": 1.45,
                  "freeCashflow": 2e8, "sharesOutstanding": 2e8, "returnOnEquity": 0.11,
                  "operatingMargins": 0.13, "profitMargins": 0.08, "debtToEquity": 150.0,
                  "currentRatio": 1.1, "revenueGrowth": 0.03, "earningsGrowth": 0.02,
                  "fiftyTwoWeekHigh": 38.0, "fiftyTwoWeekLow": 28.0},
    "NOGROW.VI": {"longName": "Unknown Growth AG", "sector": "Real Estate", "country": "Austria",
                  "currency": "EUR", "quoteType": "EQUITY", "currentPrice": 25.0,
                  "marketCap": 4e9, "trailingPE": 12.0, "dividendYield": 4.8,
                  "payoutRatio": 0.55, "returnOnEquity": 0.10, "operatingMargins": 0.20,
                  "fiftyTwoWeekHigh": 31.0, "fiftyTwoWeekLow": 24.0},
}
with db.get_conn() as conn:
    screener.refresh(conn, symbols=list(INCOME), force=True,
                     fetcher=lambda s: dict(INCOME.get(s, {})))
    inc = screener.results(conn, top=500, include_failed=True, profile="income")
    val = screener.results(conn, top=500, profile="value")
IBY = {r["symbol"]: r for r in inc["ranked"]}
IGATED = {r["symbol"]: r for r in inc["rejected"]}
VBY = {r["symbol"]: r for r in val["ranked"]}
check("dividend growth = forward / trailing - 1",
      screener.dividend_growth({"dividend_rate": 4.20, "trailing_dividend_rate": 3.96}),
      predicate=near(0.0606, 1e-3))
check("a zero trailing rate does not divide by zero",
      screener.dividend_growth({"dividend_rate": 1.0, "trailing_dividend_rate": 0.0}), None)
check("FCF payout = dividends / free cash flow",
      screener.fcf_payout({"dividend_rate": 4.2, "shares_outstanding": 1e9, "free_cashflow": 7e9}),
      predicate=near(0.60))
check("negative free cash flow yields no ratio rather than a negative one",
      screener.fcf_payout({"dividend_rate": 1.0, "shares_outstanding": 1e9, "free_cashflow": -1e9}), None)
check("the income payload names its profile and pillars",
      (inc["profile"], inc["pillar_order"]), ("income", ["yield", "growth", "safety", "quality"]))
check("ARIST.PA tops the income board", inc["ranked"][0]["symbol"], "ARIST.PA")
check("a 1.2% yield is not an income idea",
      any("too low" in x for x in IGATED["LOWY.MC"]["gate_failed"]), True)
check("a 14% yield is a distress signal, not a top rank",
      any("distress" in x for x in IGATED["DISTRESS.MI"]["gate_failed"]), True)
check("a shrinking business is gated",
      any("shrinking" in x for x in IGATED["SHRINK.AS"]["gate_failed"]), True)
check("...and it is the value board that still ranks it", "SHRINK.AS" in VBY, True)
check("a declared cut is flagged in words",
      any("cut is already declared" in x for x in IBY["CUTTER.DE"]["flags"]), True)
check("...so the 6.5% yielder loses to the 4.2% one",
      IBY["CUTTER.DE"]["score"] < IBY["ARIST.PA"]["score"], True)
check("a dividend costing more than free cash flow is flagged",
      any("free cash flow" in x for x in IBY["FCFBAD.BR"]["flags"]), True)
check("missing growth data is not a gate", "NOGROW.VI" in IBY, True)
check("...it is missing coverage", IBY["NOGROW.VI"]["pillar_coverage"]["growth"], 0.0)
check("the two share boards agree on the yield they read",
      VBY["ARIST.PA"]["dividend_yield"], IBY["ARIST.PA"]["dividend_yield"])
check("...but rank differently, which is the point",
      VBY["ARIST.PA"]["score"] != IBY["ARIST.PA"]["score"], True)

# --- ETFs: series maths on synthetic weekly series ---
END = date(2026, 9, 4)


def geometric(annual_rate, weeks=320, start=100.0):
    per_week = (1.0 + annual_rate) ** (1.0 / 52.1775) - 1.0
    return [((END - timedelta(weeks=i)).isoformat(), start * (1.0 + per_week) ** (weeks - i))
            for i in range(weeks, -1, -1)]


s10 = geometric(0.10)
check("5-year CAGR of a 10%/yr series", screener_etf.cagr(s10, 5.0), predicate=near(0.10, 1e-4))
check("1-year CAGR of the same series", screener_etf.cagr(s10, 1.0), predicate=near(0.10, 1e-4))
check("a smooth series has ~zero volatility",
      screener_etf.volatility(s10), predicate=lambda v: v is not None and v < 1e-6)
check("a rising series has no drawdown", screener_etf.max_drawdown(s10), predicate=near(0.0, 1e-12))
short = geometric(0.10, weeks=100)
check("a 5-year CAGR is refused on 2 years of history", screener_etf.cagr(short, 5.0), None)
crash = geometric(0.0, weeks=100)
crash = crash[:50] + [(d, v * 0.6) for d, v in crash[50:]]
check("a 40% fall is a 40% drawdown", screener_etf.max_drawdown(crash), predicate=near(0.40, 1e-9))
m = screener_etf.series_metrics(s10)
check("history span is measured, not assumed", m["history_years"], predicate=lambda v: 6.0 < v < 6.3)

FLAT_FX = [(d, 1.10) for d, _ in s10]
conv = screener_etf.to_eur([(d, v * 1.10) for d, v in s10], FLAT_FX)
check("a constant FX rate leaves the CAGR unchanged",
      screener_etf.cagr(conv, 5.0), predicate=near(0.10, 1e-4))
check("...and the level is the EUR level", conv[-1][1], predicate=near(s10[-1][1], 1e-9))
rising = [(d, 1.10 - 0.10 * i / len(FLAT_FX)) for i, (d, _) in enumerate(FLAT_FX)]
check("a strengthening dollar raises the EUR return",
      screener_etf.cagr(screener_etf.to_eur([(d, v * 1.10) for d, v in s10], rising), 5.0),
      predicate=lambda v: v is not None and v > 0.11)
check("pence are divided by 100", screener_etf.to_eur([("2026-01-01", 250.0)], [], pence=True)[0][1], 2.5)
check("prices before the first known FX rate are dropped, not invented",
      len(screener_etf.to_eur(s10, FLAT_FX[100:])), len(s10) - 100)

check("annualReportExpenseRatio is a fraction",
      screener_etf._yahoo_ter({"annualReportExpenseRatio": 0.0020}), predicate=near(0.0020))
check("netExpenseRatio is a percent",
      screener_etf._yahoo_ter({"netExpenseRatio": 0.20}), predicate=near(0.0020))
check("a zero expense ratio is a missing one, not a free fund",
      screener_etf._yahoo_ter({"annualReportExpenseRatio": 0.0}), None)
check("the curated TER wins over Yahoo's",
      screener_etf.effective_ter({"ter": 0.0007, "yahoo_ter": 0.0030}), (0.0007, "curated"))
check("Yahoo's is used when there is no curated one",
      screener_etf.effective_ter({"yahoo_ter": 0.0030}), (0.0030, "yahoo"))

# --- ETFs end to end, from canned info and series ---
INFO = {
    "CHEAP.DE": {"longName": "Cheap Core World", "quoteType": "ETF", "currency": "EUR",
                 "fullExchangeName": "XETRA", "category": "Global Large-Cap Blend Equity",
                 "fundFamily": "Testers", "totalAssets": 8e9,
                 "annualReportExpenseRatio": 0.0007, "regularMarketPrice": 1.0},
    "DEAR.DE": {"longName": "Dear Core World", "quoteType": "ETF", "currency": "EUR",
                "totalAssets": 8e9, "netExpenseRatio": 0.65, "regularMarketPrice": 1.0},
    "USDX.AS": {"longName": "Cheap Core World USD", "quoteType": "ETF", "currency": "USD",
                "totalAssets": 8e9, "annualReportExpenseRatio": 0.0007},
    "DISTY.DE": {"longName": "Cheap Core World Dist", "quoteType": "ETF", "currency": "EUR",
                 "totalAssets": 8e9, "yield": 2.4, "annualReportExpenseRatio": 0.0007},
    "YOUNG.DE": {"longName": "Young Fund", "quoteType": "ETF", "currency": "EUR",
                 "totalAssets": 2e9, "annualReportExpenseRatio": 0.0015},
    "NOTER.DE": {"longName": "Mystery Fund", "quoteType": "ETF", "currency": "EUR",
                 "totalAssets": 2e9},
    "LEV3.DE": {"longName": "Index 3x Daily Long", "quoteType": "ETF", "currency": "EUR",
                "totalAssets": 2e9, "annualReportExpenseRatio": 0.0060},
    "TINY.DE": {"longName": "Tiny Fund", "quoteType": "ETF", "currency": "EUR",
                "totalAssets": 1e7, "annualReportExpenseRatio": 0.0020},
    "NOSIZE.DE": {"longName": "Unreported Size Fund", "quoteType": "ETF", "currency": "EUR",
                  "annualReportExpenseRatio": 0.0020},
}
S12 = geometric(0.12)


def quarterly(start_year, per_quarter, years=3, step=0.0):
    out, amt = [], per_quarter
    for y in range(years):
        for mth in (3, 6, 9, 12):
            out.append((date(start_year + y, mth, 20).isoformat(), round(amt, 6)))
        amt += step
    return out


HIST = {
    "CHEAP.DE": S12, "DEAR.DE": S12, "USDX.AS": [(d, v * 1.10) for d, v in S12],
    "DISTY.DE": S12, "YOUNG.DE": geometric(0.12, weeks=100), "NOTER.DE": S12,
    "LEV3.DE": S12, "TINY.DE": S12, "NOSIZE.DE": S12, "EURUSD=X": FLAT_FX,
}
DIVS = {"DISTY.DE": quarterly(2023, 1.2, years=4, step=0.1)}
FX_CALLS = []


def fake_hist(sym):
    if sym.endswith("=X"):
        FX_CALLS.append(sym)
    if sym not in HIST:
        return {}
    return {"closes": HIST[sym], "dividends": DIVS.get(sym, []),
            "currency": "USD" if sym == "USDX.AS" else "EUR", "quote_type": "ETF"}


screener_etf.UNIVERSE_FILE.write_text(json.dumps({"etfs": [
    {"symbol": "CHEAP.DE", "ter": 0.0007, "dist": "acc", "pea": True, "region": "World"},
    {"symbol": "DEAR.DE", "ter": 0.0065, "dist": "acc", "pea": False, "region": "World"},
    {"symbol": "USDX.AS", "ter": 0.0007, "dist": "acc", "pea": False, "region": "World"},
    {"symbol": "DISTY.DE", "ter": 0.0007, "dist": "dist", "pea": False, "region": "World"},
    {"symbol": "YOUNG.DE", "ter": 0.0015, "dist": "acc", "pea": False, "region": "Theme"},
    {"symbol": "NOTER.DE", "dist": "acc", "pea": False, "region": "World"},
    {"symbol": "LEV3.DE", "ter": 0.0060, "dist": "acc", "pea": False, "region": "Theme"},
    {"symbol": "TINY.DE", "ter": 0.0020, "dist": "acc", "pea": False, "region": "Europe"},
    {"symbol": "NOSIZE.DE", "ter": 0.0020, "dist": "acc", "pea": False, "region": "Europe"},
    {"symbol": "IWDA.AS", "ter": 0.0018}],
    "exclude": ["EXXT.DE"]}))
with db.get_conn() as conn:
    uni3 = screener_etf.load_universe(conn)
    res = screener_etf.refresh(conn, symbols=list(INFO), force=True,
                               info_fetcher=lambda s: INFO.get(s, {}),
                               history_fetcher=fake_hist)
    data = screener_etf.results(conn, top=500, include_failed=True)
check("an override replaces just the field given, and keeps the rest",
      (uni3["IWDA.AS"]["ter"], uni3["IWDA.AS"]["dist"], uni3["IWDA.AS"]["pea"]),
      (0.0018, "acc", False))
check("exclusions are honoured", "EXXT.DE" in uni3, False)
check("no US-listed ETF sneaked into the shipped list",
      all("." in e["symbol"] for e in screener_etf.DEFAULT_ETF_UNIVERSE), True)
check("no London listing either",
      any(e["symbol"].endswith(".L") for e in screener_etf.DEFAULT_ETF_UNIVERSE), False)
check("every fake ETF stored", (res["ok"], res["failed"]), (len(INFO), 0))
check("the FX series was fetched once, not once per symbol", FX_CALLS.count("EURUSD=X"), 1)
BY = {r["symbol"]: r for r in data["ranked"]}
GATED = {r["symbol"]: r for r in data["rejected"]}
check("CHEAP.DE beats DEAR.DE on cost alone", BY["CHEAP.DE"]["score"] > BY["DEAR.DE"]["score"], True)
check("...their growth pillars are identical",
      BY["CHEAP.DE"]["pillars"]["growth"], BY["DEAR.DE"]["pillars"]["growth"])
check("the USD twin scores the same as the EUR one",
      abs(BY["USDX.AS"]["score"] - BY["CHEAP.DE"]["score"]) < 0.05, True)
check("...and is relabelled as EUR", BY["USDX.AS"]["currency"], "EUR")
check("the distributing twin scores the same", abs(BY["DISTY.DE"]["score"] - BY["CHEAP.DE"]["score"]) < 0.05, True)
check("...but is flagged for the tax drag",
      any("distributing" in x for x in BY["DISTY.DE"]["flags"]), True)
check("the 5-year CAGR is the fund's", BY["CHEAP.DE"]["cagr_5y"], predicate=near(0.12, 1e-3))
check("YOUNG.DE is gated on history, with the years in the reason",
      any("years of history" in x for x in GATED["YOUNG.DE"]["gate_failed"]), True)
check("NOTER.DE is gated for having no TER",
      any("no TER" in x for x in GATED["NOTER.DE"]["gate_failed"]), True)
check("LEV3.DE is gated as leveraged",
      any("leveraged" in x for x in GATED["LEV3.DE"]["gate_failed"]), True)
check("TINY.DE is gated on fund size",
      any("too small" in x for x in GATED["TINY.DE"]["gate_failed"]), True)
check("an unreported fund size is NOT a gate, but a flag",
      ("NOSIZE.DE" in BY, any("size unknown" in x for x in BY["NOSIZE.DE"]["flags"])), (True, True))
check("...and exactly the size weight is missing from coverage",
      BY["NOSIZE.DE"]["coverage"], predicate=near(0.90, 1e-6))
check("gated rows are counted", data["rejected_count"], 4)
check("PEA eligibility is the curated flag",
      (BY["CHEAP.DE"]["pea_eligible"], BY["DEAR.DE"]["pea_eligible"]), (True, False))
check("regions come from the curated universe", "Theme" in data["regions"], True)
check("the growth payload names itself", (data["profile"], data["pillar_order"]),
      ("etf", ["growth", "cost", "risk", "size"]))
check("a 0.65% TER scores zero on cost", BY["DEAR.DE"]["pillars"]["cost"], 0.0)

# An FX series that cannot be fetched leaves the row in its own currency
# and says so, rather than stamping EUR on an unconverted return.
with db.get_conn() as conn:
    screener_etf.refresh(conn, symbols=["USDX.AS"], force=True,
                         info_fetcher=lambda s: INFO[s],
                         history_fetcher=lambda s: {} if s.endswith("=X") else fake_hist(s))
    nofx = {r["symbol"]: r for r in screener_etf.results(conn, top=500)["ranked"]}["USDX.AS"]
check("an unconverted row keeps its listing currency", nofx["currency"], "USD")
check("...and says so in a flag", any("not EUR" in x for x in nofx["flags"]), True)

# A failed fetch keeps the old figures; a good one clears the error.
with db.get_conn() as conn:
    screener_etf.refresh(conn, symbols=["CHEAP.DE"], force=True,
                         info_fetcher=lambda s: INFO[s], history_fetcher=lambda s: {})
    after = dict(conn.execute("SELECT * FROM screener_etfs WHERE symbol='CHEAP.DE'").fetchone())
    screener_etf.refresh(conn, symbols=["CHEAP.DE"], force=True,
                         info_fetcher=lambda s: INFO[s], history_fetcher=fake_hist)
    fixed = dict(conn.execute("SELECT * FROM screener_etfs WHERE symbol='CHEAP.DE'").fetchone())
    skip2 = screener_etf.refresh(conn, symbols=["CHEAP.DE"],
                                 info_fetcher=lambda s: INFO[s], history_fetcher=fake_hist)
check("a failed fetch keeps the previous figures", after["cagr_5y"], predicate=near(0.12, 1e-3))
check("...and stamps the error", bool(after["last_error"]), True)
check("a good fetch clears it", fixed["last_error"], None)
check("a fresh row is skipped", (skip2["skipped"], skip2["attempted"]), (1, 0))

# --- distributions: the dividend board's inputs ---
TODAY = date(2026, 9, 8)
dm = screener_etf.dividend_metrics(quarterly(2024, 0.50, years=3), 100.0, TODAY)
check("trailing yield is last 12 months over price", round(dm["div_yield_ttm"], 4), 0.02)
check("payment frequency is counted", dm["div_events_12m"], 4)
check("a flat payer shows no growth", round(dm["div_growth"], 6), 0.0)
usd = screener_etf.dividend_metrics(quarterly(2024, 0.54, years=3), 108.0, TODAY)
check("the same fund quoted in another currency yields the same",
      round(usd["div_yield_ttm"], 6), round(dm["div_yield_ttm"], 6))
grow = screener_etf.dividend_metrics(quarterly(2024, 0.50, years=3, step=0.05), 100.0, TODAY)
check("a rising distribution shows positive growth, and no cut",
      (grow["div_growth"] > 0, grow["div_worst_cut"] >= 0), (True, True))


def ago(days):
    return (TODAY - timedelta(days=days)).isoformat()


mc = screener_etf.dividend_metrics(
    [(ago(1125), 1.0), (ago(760), 1.0), (ago(395), 0.5), (ago(30), 0.6)], 100.0, TODAY)
check("a past cut is remembered even when growth is positive now",
      (mc["div_growth"] > 0, mc["div_worst_cut"] < -0.4), (True, True))
future = quarterly(2024, 0.50, years=3) + [((TODAY + timedelta(days=20)).isoformat(), 0.50)]
mf = screener_etf.dividend_metrics(future, 100.0, TODAY)
check("an announced future distribution is not counted as paid",
      (mf["div_events_12m"], round(mf["div_yield_ttm"], 4)), (4, 0.02))
check("an accumulating fund reports zero, not None",
      screener_etf.dividend_metrics([], 100.0, TODAY)["div_ttm"], 0.0)
check("zero is accumulating, something is not, nothing is unknown",
      (screener_etf.is_accumulating({"div_ttm": 0.0, "div_events_12m": 0}),
       screener_etf.is_accumulating({"div_ttm": 1.9, "div_events_12m": 4}),
       screener_etf.is_accumulating({"div_ttm": None, "div_events_12m": None})),
      (True, False, None))
md = screener_etf.dividend_metrics(
    [("2024-12-28", 1.0), ("2025-12-28", 1.0)], 100.0, date(2026, 6, 1))
check("a December payer is not read as having cut to zero",
      (md["div_ttm"] > 0, md["div_prior"] > 0), (True, True))

DCFG = screener_etf.load_config("dividend")


def drow(**over):
    r = {"symbol": "TEST.DE", "name": "Test Dividend ETF", "quote_type": "ETF",
         "ter": 0.0030, "dist": "dist", "region": "Dividend", "currency": "EUR",
         "price": 100.0, "total_assets": 8e8, "cagr_5y": 0.07, "cagr_3y": 0.06,
         "max_drawdown": 0.25, "volatility_1y": 0.14, "history_years": 8.0,
         "div_ttm": 3.5, "div_prior": 3.3, "div_yield_ttm": 0.035, "div_growth": 0.06,
         "div_worst_cut": -0.02, "div_years": 8.0, "div_events_12m": 4, "div_events_prior": 4}
    r.update(over)
    return r


base = screener_etf.score_dividend_row(drow(), DCFG)
check("a healthy income fund passes every gate", base["gate_failed"], None)
check("net yield is yield minus TER", round(base["net_yield"], 4), 0.032)
check("a higher yield scores higher",
      screener_etf.score_dividend_row(drow(div_yield_ttm=0.045), DCFG)["score"] > base["score"], True)
check("a cheaper fund scores higher",
      screener_etf.score_dividend_row(drow(ter=0.0010), DCFG)["score"] > base["score"], True)
shrinking = screener_etf.score_dividend_row(drow(div_growth=-0.10), DCFG)
check("a shrinking distribution scores lower, and says so",
      (shrinking["score"] < base["score"], any("shrinking" in x for x in shrinking["flags"])), (True, True))
cutter = screener_etf.score_dividend_row(drow(div_worst_cut=-0.30), DCFG)
check("a fund that has cut before scores lower, and the cut is flagged",
      (cutter["score"] < base["score"], any("cut before" in x for x in cutter["flags"])), (True, True))
accum = screener_etf.score_dividend_row(drow(div_ttm=0.0, div_events_12m=0, div_yield_ttm=0.0), DCFG)
check("an accumulating fund is gated out, with no score",
      (any("accumulating" in x for x in accum["gate_failed"]), accum["score"]), (True, None))
unknown = screener_etf.score_dividend_row(drow(div_ttm=None, div_events_12m=None, div_yield_ttm=None), DCFG)
check("no distribution data is gated as unknown, not as accumulating",
      any("no distribution data" in x for x in unknown["gate_failed"]), True)
check("an implausible yield is gated, not rewarded",
      any("implausible" in x for x in screener_etf.score_dividend_row(drow(div_yield_ttm=0.15), DCFG)["gate_failed"]), True)
check("a yield too low to be income is gated",
      any("too low" in x for x in screener_etf.score_dividend_row(drow(div_yield_ttm=0.012), DCFG)["gate_failed"]), True)
check("under two years of distributions is gated",
      any("years of distributions" in x for x in screener_etf.score_dividend_row(drow(div_years=1.2), DCFG)["gate_failed"]), True)
mixup = screener_etf.score_dividend_row(drow(dist="acc"), DCFG)
check("a fund curated 'acc' that pays is flagged as a share-class mix-up",
      any("wrong share class" in x for x in mixup["flags"]), True)
sched = screener_etf.score_dividend_row(drow(div_events_prior=2), DCFG)
check("a schedule change is flagged as not like-for-like",
      any("schedule change" in x for x in sched["flags"]), True)
eats = screener_etf.score_dividend_row(drow(ter=0.0060), DCFG)
check("a TER that eats a big share of the income is spelled out",
      any("eats" in x for x in eats["flags"]), True)
mfund = screener_etf.score_dividend_row(drow(quote_type="MUTUALFUND", div_yield_ttm=0.06), DCFG)
check("a US mutual fund is gated off the income board",
      any("mutual fund" in x for x in mfund["gate_failed"]), True)
check("...but still scores on the growth board",
      screener_etf.score_row(drow(quote_type="MUTUALFUND"))["gate_failed"], None)
dupes = [screener_etf.score_dividend_row(drow(symbol="IQQA.DE", name="iShares Euro Dividend UCITS ETF EUR Dist"), DCFG),
         screener_etf.score_dividend_row(drow(symbol="IDVY.AS", name="iShares Euro Dividend UCITS ETF EUR (Dist)"), DCFG),
         screener_etf.score_dividend_row(drow(symbol="EXSH.DE", name="iShares STOXX Europe Select Dividend 30 UCITS ETF"), DCFG)]
screener_etf._flag_duplicate_listings(dupes)
check("two listings of one fund are matched despite different suffixes",
      dupes[0].get("duplicate_of"), "IDVY.AS")
check("...neither row is dropped, and the loner is not flagged",
      (len(dupes), dupes[2].get("duplicate_of")), (3, None))

with db.get_conn() as conn:
    dd = screener_etf.results(conn, top=500, include_failed=True, profile="dividend")
DBY = {r["symbol"]: r for r in dd["ranked"]}
DG = {r["symbol"]: r for r in dd["rejected"]}
check("the dividend payload names itself", (dd["profile"], dd["pillar_order"]),
      ("etf_dividend", ["yield", "cost", "growth", "stability"]))
check("the distributing fund's yield was computed from its payments",
      DBY.get("DISTY.DE", DG.get("DISTY.DE"))["div_yield_ttm"], predicate=lambda v: v and v > 0.02)
check("the accumulating twin is gated off the dividend board",
      any("accumulating" in x for x in DG["CHEAP.DE"]["gate_failed"]), True)

# --- the routes, and the template / script / Python seam ---
r = c.get("/screener")
check("the Share Ideas page renders", r.status_code, 200)
tpl = pathlib.Path("app/templates/screener.html").read_text()
tabs = set(re.findall(r'class="scr-tab[^"]*" data-board="(\w+)"', tpl))
boards_js = set(re.findall(r"^  (\w+): \{\n    label:", tpl, re.M))
explain = set(re.findall(r'class="scr-explain-col" data-board="(\w+)"', tpl))
check("the template has a tab per board", tabs, {"value", "income", "etf", "etf_dividend"})
check("...and a board spec per tab", boards_js, tabs)
check("...and a 'how to read this' column per tab", explain, tabs)
check("sort state is derived from the boards, not hand-listed",
      "Object.keys(BOARDS).map" in tpl, True)
pillars_js = {k: re.findall(r"'(\w+)'", v) for k, v in
              re.findall(r"^  (\w+): \{\n    label:.*?pillars: \[([^\]]+)\]", tpl, re.M | re.S)}
check("the pillars the script draws are the ones Python scores",
      (pillars_js["value"], pillars_js["income"], pillars_js["etf"], pillars_js["etf_dividend"]),
      (screener.PILLAR_ORDER["value"], screener.PILLAR_ORDER["income"],
       screener_etf.PILLAR_ORDER["growth"], screener_etf.PILLAR_ORDER["dividend"]))
r = c.get("/api/screener?profile=income&failed=1&top=5")
j = r.get_json()
check("the share API answers", (r.status_code, j["ok"], j["profile"]), (200, True, "income"))
check("...honouring top", len(j["ranked"]) <= 5, True)
check("...and listing the gated with reasons", all(x["gate_failed"] for x in j["rejected"]), True)
r = c.get("/api/screener/etf?profile=dividend")
check("the ETF API answers", (r.status_code, r.get_json()["profile"]), (200, "etf_dividend"))
r = c.get("/api/screener?profile=nonsense")
check("an unknown profile is a 400, not a 500", r.status_code, 400)
r = c.post("/api/screener/watch/cheap.de", json={"status": "watch"})
check("the watchlist route stores, upper-cased", (r.get_json()["ok"], r.get_json()["symbol"]), (True, "CHEAP.DE"))
r = c.post("/api/screener/watch/cheap.de", json={"status": "bogus"})
check("a bogus status is refused", r.status_code, 400)
with db.get_conn() as conn:
    shared = {r["symbol"]: r["watch_status"] for r in screener_etf.results(conn, top=500)["ranked"]}
check("the watchlist is shared across the boards", shared["CHEAP.DE"], "watch")
r = c.get("/settings/market")
check("the settings page has the Share Ideas section", b'id="ideas"' in r.data, True)
check("...counting the cached rows", b"cached" in r.data, True)
st = screener_jobs.status()
check("the job status counts both caches", (st["shares"]["n"] > 5, st["etfs"]["n"] > 5), (True, True))
check("nothing is running", st["running"], False)
screener_etf.UNIVERSE_FILE.unlink()

# ---------------------------------------------------------------------------
print("\n25. MCP — an assistant with a token")
# ---------------------------------------------------------------------------
# JSON-RPC over POST, checked the way a client would use it: the
# handshake, the tool list, then every tool once, and the ways it must
# refuse — no token, a wrong token, a GET, a tool that does not exist.
from app import mcp                                         # noqa: E402

check("no token means no access", mcp.authorised("Bearer anything"), False)
tok = mcp.new_token()
check("a token is long and random", len(tok) >= 40, True)
check("the right token is accepted", mcp.authorised(f"Bearer {tok}"), True)
check("a wrong one is not", mcp.authorised("Bearer " + tok[:-1] + "x"), False)
check("the scheme matters", mcp.authorised(tok), False)
check("it is stored 0600", oct(mcp.TOKEN_FILE.stat().st_mode & 0o777), "0o600")
HDR = {"Authorization": f"Bearer {tok}"}


def rpc(method, params=None, id_=1, headers=HDR):
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": id_, "method": method,
                             "params": params or {}}, headers=headers)
    return r.status_code, (r.get_json() if r.data else None)


def call(name, **arguments):
    status, j = rpc("tools/call", {"name": name, "arguments": arguments})
    assert status == 200 and "result" in j, (name, status, j)
    res = j["result"]
    if res.get("isError"):
        return {"_error": res["content"][0]["text"]}
    return res.get("structuredContent", json.loads(res["content"][0]["text"]))


r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
check("without a token: 401", r.status_code, 401)
check("...and the header says how to get in", "Bearer" in r.headers.get("WWW-Authenticate", ""), True)
check("with a wrong token: 401",
      rpc("ping", headers={"Authorization": "Bearer nope"})[0], 401)
check("a GET is not a message", c.get("/mcp", headers=HDR).status_code, 405)
check("a body that is not JSON is a parse error",
      c.post("/mcp", data="not json", headers={**HDR, "Content-Type": "application/json"}).get_json()["error"]["code"],
      mcp.PARSE_ERROR)

s_, j = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "test", "version": "0"}})
check("initialize answers with the protocol version asked for",
      j["result"]["protocolVersion"], "2025-06-18")
check("...an unknown version gets the newest we speak",
      rpc("initialize", {"protocolVersion": "1999-01-01"})[1]["result"]["protocolVersion"],
      mcp.PROTOCOL_VERSIONS[0])
check("...declaring tools", "tools" in j["result"]["capabilities"], True)
check("...naming itself and its version",
      (j["result"]["serverInfo"]["name"], j["result"]["serverInfo"]["version"]),
      ("wealth-dashboard", main.__version__))
check("...with instructions for the model", "categorise_many" in j["result"]["instructions"], True)
check("a notification is acknowledged with 202 and no body",
      c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"},
             headers=HDR).status_code, 202)
check("ping pongs", rpc("ping")[1]["result"], {})
check("an unknown method is -32601", rpc("nonsense")[1]["error"]["code"], mcp.METHOD_NOT_FOUND)
check("a message that is not JSON-RPC is -32600",
      c.post("/mcp", json={"hello": "there"}, headers=HDR).get_json()["error"]["code"],
      mcp.INVALID_REQUEST)
batch = c.post("/mcp", json=[{"jsonrpc": "2.0", "id": 7, "method": "ping"},
                              {"jsonrpc": "2.0", "method": "notifications/x"}], headers=HDR)
check("a batch answers its requests and swallows its notifications",
      batch.get_json(), [{"jsonrpc": "2.0", "id": 7, "result": {}}])

s_, j = rpc("tools/list")
names = [t["name"] for t in j["result"]["tools"]]
check("the tool list is complete", sorted(names), sorted(mcp._HANDLERS))
check("every tool has a schema and a description",
      all(t["inputSchema"]["type"] == "object" and t["description"] for t in j["result"]["tools"]), True)
check("no tool can delete an account or touch credentials",
      any("delete_account" in n or "credential" in n for n in names), False)
check("the tool list is JSON-schema-valid enough for a client",
      all(set(t["inputSchema"]["required"]) <= set(t["inputSchema"]["properties"])
          for t in j["result"]["tools"]), True)

# --- reads ---
nw = call("net_worth")
check("net_worth agrees with the overview", round(nw["net_worth"], 2),
      round(ov.summary("EUR")["net_worth"], 2))
check("...and lists the accounts", any(a["name"] == "DKB Girokonto" for a in nw["accounts"]), True)
accts = call("accounts")
check("accounts lists each with its id", all("id" in a and "name" in a for a in accts), True)
hold = call("holdings")
check("holdings lists what is held", any(h["isin"] == "IE00B4L5Y983" for h in hold["holdings"]), True)
hist_ = call("net_worth_history", period="1y")
check("history returns points", isinstance(hist_["points"], list), True)
check("...and refuses a period it does not know",
      "_error" in call("net_worth_history", period="9y"), True)
tx = call("transactions", q="rewe", limit=5)
check("transactions searches by text", tx["matched"] >= 1 and len(tx["transactions"]) <= 5, True)
check("...and by kind", all(t["kind"] == "buy" for t in call("transactions", kind="buy")["transactions"]), True)
check("...and by date", all(t["txn_date"] >= "2026-01-01" for t in
                            call("transactions", date_from="2026-01-01")["transactions"]), True)
check("...capping the limit", call("transactions", limit=9999)["returned"] <= 500, True)
cats = call("categories")
check("categories lists slugs with labels", any(x["slug"] == "food" and x["label"] for x in cats), True)
check("...in English whatever the UI language",
      next(x for x in cats if x["slug"] == "housing")["label"], "Housing")
queue = call("uncategorised", limit=5)
check("the queue carries a pattern per row",
      all("pattern" in t and "suggestion" in t for t in queue["transactions"]), True)

# --- writes: categorising, with and without a rule ---
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, "
                 "amount, currency, kind) VALUES (?, '2026-09-03', 'Kartenzahlung', "
                 "'Bakery Corner', -4.5, 'EUR', 'withdrawal')", (account_id,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, "
                 "amount, currency, kind) VALUES (?, '2026-09-04', 'Kartenzahlung', "
                 "'Bakery Corner', -3.2, 'EUR', 'withdrawal')", (account_id,))
    bakery = [r["id"] for r in conn.execute(
        "SELECT id FROM transactions WHERE counterparty = 'Bakery Corner' ORDER BY id")]
res = call("set_category", txn_id=bakery[0], category="food")
check("set_category files the row and learns the counterparty as the rule",
      (res["category"], res["rule"]), ("food", "Bakery Corner"))
check("...applying it to the sibling row at once", res["applied"] >= 2, True)
with db.get_conn() as conn:
    got = [r["category"] for r in conn.execute(
        "SELECT category FROM transactions WHERE id IN (?, ?) ORDER BY id", bakery)]
check("...so both are categorised", got, ["food", "food"])
check("filing under 'other' makes no rule",
      call("set_category", txn_id=bakery[1], category="other")["rule"], None)
check("an unknown category is the tool's error, not a crash",
      "_error" in call("set_category", txn_id=bakery[1], category="nope"), True)
check("an unknown transaction likewise",
      "_error" in call("set_category", txn_id=99999999, category="food"), True)
many = call("categorise_many", items=[
    {"txn_id": bakery[1], "category": "food", "pattern": "Bakery Corner"},
    {"txn_id": 99999999, "category": "food"},
    {"txn_id": bakery[0], "category": "nope"}])
check("categorise_many does what it can and reports the rest",
      (many["categorised"], len(many["failed"])), (1, 2))
check("add_rule refuses a two-letter pattern", "_error" in call("add_rule", pattern="ab", category="food"), True)
added = call("add_rule", pattern="Bakery Corner", category="restaurants")
check("add_rule applies retroactively", added["applied"] >= 2, True)
rules_ = call("rules")
check("rules lists what was learned", any(r_["pattern"] == "Bakery Corner" for r_ in rules_), True)
newest = max(r_["id"] for r_ in rules_ if r_["pattern"] == "Bakery Corner")
check("delete_rule removes it and re-applies the rest",
      call("delete_rule", rule_id=newest)["deleted"], newest)
check("an unknown tool is a JSON-RPC error", rpc("tools/call", {"name": "bogus"})[1]["error"]["code"],
      mcp.INVALID_PARAMS)
check("an unknown argument is a JSON-RPC error",
      rpc("tools/call", {"name": "rules", "arguments": {"wat": 1}})[1]["error"]["code"],
      mcp.INVALID_PARAMS)
check("a missing required argument too",
      rpc("tools/call", {"name": "set_category", "arguments": {"txn_id": 1}})[1]["error"]["code"],
      mcp.INVALID_PARAMS)

# --- budgets, subscriptions, manual entries ---
check("set_budget stores", call("set_budget", category="food", monthly=300)["monthly"], 300)
rep = call("budget_report")
check("budget_report shows it", any(r_["category"] == "food" and r_["budget"] == 300
                                    for r_ in rep["rows"]), True)
call("set_budget", category="food", monthly=None)
check("...and null clears it", "food" not in cf.budgets(), True)
check("an unknown category cannot be budgeted", "_error" in call("set_budget", category="nope", monthly=1), True)
check("subscriptions answers", "active" in call("subscriptions"), True)
tx_ = call("add_transaction", account_id=account_id, kind="withdrawal", txn_date="2026-09-06",
           amount=19.99, description="Haircut", category="health")
check("add_transaction stores a signed amount", (tx_["amount"], tx_["category"]), (-19.99, "health"))
check("a trade needs an ISIN", "_error" in call("add_transaction", account_id=broker_id, kind="buy",
                                                txn_date="2026-09-06", quantity=1, price=10), True)
trade = call("add_transaction", account_id=broker_id, kind="buy", txn_date="2026-09-06",
             isin="IE00B4L5Y983", quantity=2, price=100.5, fee=1)
check("a trade stores quantity, price and the total", (trade["quantity"], trade["price"], trade["amount"]),
      (2.0, 100.5, -202.0))
check("a future date is refused", "_error" in call("add_transaction", account_id=account_id, kind="deposit",
                                                    txn_date="2999-01-01", amount=1), True)
check("an unknown account is refused", "_error" in call("add_transaction", account_id=999999, kind="deposit",
                                                        txn_date="2026-09-06", amount=1), True)
bal = call("set_balance", account_id=account_id, amount=1234.56, as_of="2026-09-06")
check("set_balance records the reading", (bal["amount"], bal["as_of"]), (1234.56, "2026-09-06"))

# --- share ideas and the watchlist ---
ideas = call("share_ideas", board="etf", top=3)
check("share_ideas ranks the ETF board", (ideas["board"], len(ideas["ranked"]) <= 3), ("etf", True))
check("...trimmed to the figures that matter", "ter" in ideas["ranked"][0] and "cagr_5y" in ideas["ranked"][0], True)
gated_ = call("share_ideas", board="etf_dividend", include_gated=True)
check("...listing the gated with reasons on request",
      all(g_["gate_failed"] for g_ in gated_["gated"]), True)
check("...refusing a board it does not have", "_error" in call("share_ideas", board="crypto"), True)
w = call("watch_idea", symbol="cheap.de", status="dismissed", note="too concentrated")
check("watch_idea stores the mark", (w["symbol"], w["status"]), ("CHEAP.DE", "dismissed"))
check("...visible on the board", next(r_ for r_ in call("share_ideas", board="etf", top=500)["ranked"]
                                       if r_["symbol"] == "CHEAP.DE")["watch_status"], "dismissed")
call("watch_idea", symbol="CHEAP.DE", status="clear")

# --- the chores ---
check("sync_health answers with the graded connections", isinstance(call("sync_health"), list), True)
_real_sync_all = banksync.sync_all
banksync.sync_all = lambda: [{"account": "DKB Girokonto", "inserted": 3, "error": None}]
try:
    synced = call("sync_banks")
finally:
    banksync.sync_all = _real_sync_all
check("sync_banks runs the sync and returns its report", synced[0]["inserted"], 3)
check("refresh_prices prices the holdings", call("refresh_prices")["priced"] >= 1, True)
_real_start = screener_jobs.start_background
screener_jobs.start_background = lambda force=False, log=print: True     # never Yahoo from a test
try:
    check("refresh_share_ideas reports its state", "running" in call("refresh_share_ideas"), True)
finally:
    screener_jobs.start_background = _real_start

# --- the settings page and revocation ---
r = c.get("/settings/assistants")
check("the settings page shows the token and the one-line setup",
      b'id="mcp"' in r.data and tok.encode() in r.data and b"claude mcp add" in r.data, True)
r = c.post("/settings", data={"form": "mcp_token", "action": "new"}, follow_redirects=True)
check("replacing the token cuts the old one off", rpc("ping")[0], 401)
r = c.post("/settings", data={"form": "mcp_token", "action": "revoke"}, follow_redirects=True)
check("revoking removes it", mcp.token(), None)
check("...and nothing gets in", rpc("ping", headers={"Authorization": f"Bearer {mcp.token()}"})[0], 401)
r = c.get("/settings/assistants")
check("...and the page says so", b"Create a token" in r.data, True)

# ---------------------------------------------------------------------------
print("\n26. Kraken, through a read-only key")
# ---------------------------------------------------------------------------
from app import brokers                                     # noqa: E402
from app.brokers import kraken, saxo                        # noqa: E402

check("XXBT is bitcoin", kraken.asset_code("XXBT"), "BTC")
check("ZEUR is the euro", kraken.asset_code("ZEUR"), "EUR")
check("a staked coin is the coin", (kraken.asset_code("ETH2.S"), kraken.asset_code("DOT.S")), ("ETH", "DOT"))
check("a plain code stays", kraken.asset_code("SOL"), "SOL")
try:
    kraken.save_credentials("key", "not-base64!")
    check("a private key that is not base64 is refused", False, True)
except ValueError:
    check("a private key that is not base64 is refused", True, True)
SECRET = base64.b64encode(b"k" * 64).decode()
kraken.save_credentials("api-key-1", SECRET)
check("the key is stored 0600",
      oct((settings.SECRETS_DIR / kraken.KEY_FILE).stat().st_mode & 0o777), "0o600")

# The signature, checked against the recipe Kraken publishes.
kc = kraken.Client("api-key-1", SECRET, transport=lambda m, u, h, b: (200, b'{"error":[],"result":{}}'))
sent = {}
def kraken_capture(method, url, headers, body):
    sent.update(method=method, url=url, headers=headers, body=body)
    return 200, b'{"error":[],"result":{"ZEUR":"1250.50","XXBT":"0.5","ETH2.S":"1.0","XETH":"0.25"}}'
kc.transport = kraken_capture
bal = kc.balance()
check("a private call is a signed POST", (sent["method"], sent["headers"]["API-Key"]), ("POST", "api-key-1"))
nonce = dict(urllib.parse.parse_qsl(sent["body"].decode()))["nonce"]
expect = base64.b64encode(hmac.new(base64.b64decode(SECRET),
    b"/0/private/Balance" + hashlib.sha256((nonce + sent["body"].decode()).encode()).digest(),
    hashlib.sha512).digest()).decode()
check("...with the HMAC-SHA512 Kraken expects", sent["headers"]["API-Sign"], expect)
check("balances come back as plain codes, staked folded in",
      (bal["EUR"], bal["BTC"], bal["ETH"]), (1250.5, 0.5, 1.25))
n1, n2 = kc._nonce(), kc._nonce()
check("nonces only go up", n2 > n1, True)
kc.transport = lambda m, u, h, b: (200, b'{"error":["EAPI:Invalid key"],"result":{}}')
try:
    kc.balance(); check("Kraken's error list is raised as a sentence", False, True)
except kraken.KrakenError as exc:
    check("Kraken's error list is raised as a sentence", "Invalid key" in str(exc), True)

# A fake Kraken: one buy, one sale, a euro deposit, a coin deposit, a
# staking reward, a coin-for-coin swap, and balances that add up.
PAIRS = {"XXBTZEUR": {"base": "XXBT", "quote": "ZEUR", "altname": "XBTEUR"},
         "XETHZEUR": {"base": "XETH", "quote": "ZEUR", "altname": "ETHEUR"},
         "XETHXXBT": {"base": "XETH", "quote": "XXBT", "altname": "ETHXBT"}}
TRADES = {"T1": {"pair": "XXBTZEUR", "type": "buy", "price": "50000.0", "cost": "500.0", "fee": "1.30", "vol": "0.01", "time": 1767225600},
          "T2": {"pair": "XETHZEUR", "type": "buy", "price": "2000.0", "cost": "400.0", "fee": "1.04", "vol": "0.2", "time": 1769904000},
          "T3": {"pair": "XXBTZEUR", "type": "sell", "price": "60000.0", "cost": "120.0", "fee": "0.31", "vol": "0.002", "time": 1772323200},
          "T4": {"pair": "XETHXXBT", "type": "buy", "price": "0.04", "cost": "0.002", "fee": "0", "vol": "0.05", "time": 1774915200}}
LEDGER = {"L1": {"type": "deposit", "asset": "ZEUR", "amount": "1000.00", "fee": "0", "time": 1767139200},
          "L2": {"type": "trade", "asset": "ZEUR", "amount": "-500.00", "fee": "1.30", "time": 1767225600},
          "L3": {"type": "trade", "asset": "XXBT", "amount": "0.01", "fee": "0", "time": 1767225600},
          "L4": {"type": "deposit", "asset": "XXBT", "amount": "0.1", "fee": "0", "time": 1768435200},
          "L5": {"type": "staking", "asset": "ETH2.S", "amount": "0.003", "fee": "0", "time": 1772236800},
          "L6": {"type": "withdrawal", "asset": "ZEUR", "amount": "-100.00", "fee": "0.90", "time": 1773532800}}
BALANCE = {"ZEUR": "1017.45", "XXBT": "0.106", "XETH": "0.2", "ETH2.S": "0.053"}


def fake_kraken(method, url, headers, body):
    path = url.split("/0/")[1].split("?")[0]
    params = dict(urllib.parse.parse_qsl(body.decode())) if body else {}
    if path == "public/AssetPairs":
        return 200, json.dumps({"error": [], "result": PAIRS}).encode()
    if path == "private/Balance":
        return 200, json.dumps({"error": [], "result": BALANCE}).encode()
    if path == "private/TradesHistory":
        keys = sorted(TRADES); ofs = int(params.get("ofs", 0)); page = keys[ofs:ofs + 2]
        return 200, json.dumps({"error": [], "result": {"count": len(keys), "trades": {k: TRADES[k] for k in page}}}).encode()
    if path == "private/Ledgers":
        keys = sorted(LEDGER); ofs = int(params.get("ofs", 0)); page = keys[ofs:ofs + 4]
        return 200, json.dumps({"error": [], "result": {"count": len(keys), "ledger": {k: LEDGER[k] for k in page}}}).encode()
    return 404, b'{"error":["EGeneral:Unknown"]}'


kk = kraken.Client("k", SECRET, transport=fake_kraken)
check("trades are walked page by page", len(kk.trades()), 4)
check("...and the ledger too", len(kk.ledgers()), 6)
parsed = kraken.normalise(kk.trades(), kk.ledgers(), kk.asset_pairs(), "EUR")
check("no problems on the fake", parsed.problems, [])
rows = {r.external_id: r for r in parsed.rows}
buy = rows["kraken:trade:T1"]
check("a buy is a buy of the coin for euros, fee included in the money",
      (buy.kind, buy.isin, buy.quantity, buy.price, buy.amount, buy.currency, buy.fee),
      ("buy", "CRYPTO:BTC", 0.01, 50000.0, -501.3, "EUR", 1.3))
sell = rows["kraken:trade:T3"]
check("a sale is money in net of the fee, units out",
      (sell.kind, sell.amount, sell.quantity), ("sell", 119.69, -0.002))
check("the ledger's own view of a fill is not a second row", "kraken:ledger:L2" in rows, False)
check("a euro deposit is a deposit", (rows["kraken:ledger:L1"].kind, rows["kraken:ledger:L1"].amount), ("deposit", 1000.0))
check("a euro withdrawal is net of its fee", rows["kraken:ledger:L6"].amount, -100.9)
dep = rows["kraken:ledger:L4"]
check("a coin deposit moves units and no money",
      (dep.kind, dep.isin, dep.quantity, dep.amount), ("transfer", "CRYPTO:BTC", 0.1, 0.0))
stk = rows["kraken:ledger:L5"]
check("a staking reward is income in kind, on the coin itself",
      (stk.kind, stk.isin, stk.quantity), ("interest", "CRYPTO:ETH", 0.003))
swap = [r for r in parsed.rows if r.external_id.startswith("kraken:trade:T4")]
check("a coin-for-coin swap moves both coins and no money",
      sorted((r.isin, r.quantity) for r in swap), [("CRYPTO:BTC", -0.002), ("CRYPTO:ETH", 0.05)])

# Through the app: link an account to the key, sync, and see holdings.
kraken.client = lambda transport=None: kraken.Client("k", SECRET, transport=fake_kraken)
r = c.post("/accounts/new", data={"name": "Kraken", "type": "broker", "currency": "EUR"})
kr_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{kr_id}")
check("a broker account offers the Kraken connection once a key exists", b"Connect Kraken" in r.data, True)
r = c.post(f"/accounts/{kr_id}/connect/kraken", follow_redirects=True)
check("connecting pulls everything", b"Connected. Imported 9 transactions" in r.data, True)
kl = brokers.link_for(kr_id)
check("...and records the link", (kl["provider"], kl["last_error"]), ("kraken", None))
pos = {p_["isin"]: p_ for p_ in importers.positions(kr_id)}
check("the bitcoin held is the buy plus the deposit minus the sale minus the swap",
      round(pos["CRYPTO:BTC"]["quantity"], 6), 0.106)
check("the ether held is the buy plus the reward plus the swap",
      round(pos["CRYPTO:ETH"]["quantity"], 6), 0.253)
check("net invested counts only the buys and sales",
      round(pos["CRYPTO:BTC"]["net_invested"], 2), round(501.3 - 119.69, 2))
with db.get_conn() as conn:
    kbal = conn.execute("SELECT amount, currency FROM balances WHERE account_id = ? "
                        "ORDER BY as_of DESC, id DESC LIMIT 1", (kr_id,)).fetchone()
check("the euro balance is the account's balance reading", (kbal["amount"], kbal["currency"]), (1017.45, "EUR"))
r = c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
check("a second sync adds nothing", b"Imported 0 new transactions" in r.data, True)
check("the sync-everything button includes brokers",
      any(x["provider"] == "kraken" for x in brokers.sync_all()), True)
# The price feed knows a crypto key.
check("a crypto key resolves to Yahoo's pair, not an ISIN search",
      prices.resolve("CRYPTO:BTC", "EUR", get=lambda url: {"quotes": [
          {"symbol": "BTC-EUR", "quoteType": "CRYPTOCURRENCY", "shortname": "Bitcoin EUR"}]}),
      {"symbol": "BTC-EUR", "name": "Bitcoin EUR"})
# Drift: Kraken says more bitcoin than the rows explain.
BALANCE["XXBT"] = "0.5"
r = c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
check("a balance the rows do not explain is reported, not patched",
      b"do not add up" in r.data and b"Kraken says 0.5" in r.data, True)
check("...and the sync still counts as having run: the rows were stored, only the check failed",
      brokers.link_for(kr_id)["last_sync_at"] is not None, True)
BALANCE["XXBT"] = "0.106"
# The move from another app leaves a date up to which the account's
# ledger is on record, so a file covering the same days is not booked
# twice. A row Kraken names by id is not a file: the withdrawal made
# the afternoon of the move-in has to get through.
with db.get_conn() as conn:
    conn.execute("UPDATE accounts SET ledger_until = '2099-12-31' WHERE id = ?", (kr_id,))
LEDGER["L6b"] = {"type": "withdrawal", "asset": "XXBT", "amount": "-0.001", "fee": "0", "time": 1788900000}
BALANCE["XXBT"] = "0.105"
r = c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
check("a Kraken row dated before the ledger cut-off is still booked, being known by its id",
      b"Imported 1 new" in r.data, True)
with db.get_conn() as conn:
    conn.execute("UPDATE accounts SET ledger_until = NULL WHERE id = ?", (kr_id,))
    conn.execute("DELETE FROM transactions WHERE external_id = 'kraken:ledger:L6b'")
del LEDGER["L6b"]; BALANCE["XXBT"] = "0.106"

# The coins go to a hardware wallet. Without a wallet named, a
# withdrawal is units leaving — which is what Kraken's balance says.
# With one named, it is a move between two of the user's accounts: the
# units arrive there at the cost they carried, and the coin is still
# theirs, just elsewhere.
r = c.post("/accounts/new", data={"name": "Ledger", "type": "broker", "currency": "EUR"})
wallet_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{kr_id}")
check("the Kraken account asks where withdrawn coins go", (b"Coins withdrawn go to" in r.data, b"Ledger" in r.data), (True, True))
c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": str(wallet_id)})
check("...and remembers the answer", brokers.link_for(kr_id)["wallet_account_id"], wallet_id)
cost_all_on_kraken = gains.realised("CRYPTO:BTC", [kr_id])["open_cost"]
LEDGER["L7"] = {"type": "withdrawal", "asset": "XXBT", "amount": "-0.1", "fee": "0.00005", "time": 1789000000}
BALANCE["XXBT"] = "0.00595"
r = c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
check("the withdrawal syncs without drift: Kraken's balance and the rows agree", b"Imported 1 new" in r.data, True)
kpos = {p_["isin"]: p_ for p_ in importers.positions(kr_id)}
wpos = {p_["isin"]: p_ for p_ in importers.positions(wallet_id)}
check("the units left Kraken, fee included, and the wallet received what was sent",
      (round(kpos["CRYPTO:BTC"]["quantity"], 6), round(wpos["CRYPTO:BTC"]["quantity"], 6)), (0.00595, 0.1))
with db.get_conn() as conn:
    wrow = dict(conn.execute("SELECT * FROM transactions WHERE account_id = ? AND isin = 'CRYPTO:BTC'", (wallet_id,)).fetchone())
check("...as a transfer that carries the cost of the units, under the ledger entry's id",
      (wrow["kind"], wrow["external_id"], wrow["amount"], wrow["price"] is not None and wrow["price"] > 0, wrow["description"]),
      ("transfer", "kraken:ledger:L7:wallet", 0.0, True, "From Kraken: 0.1 BTC"))
ov_ = ov.summary("EUR")
btc = next(h for h in ov_["holdings"] if h["isin"] == "CRYPTO:BTC")
check("...and the household holds every unit but the network fee's", round(btc["quantity"], 6), 0.10595)
# An earlier parser booked a withdrawal without the fee taken with it.
# Every sync re-reads the stored rows against the ledger and heals
# them — and the wallet's counterpart with them.
with db.get_conn() as conn:
    conn.execute("UPDATE transactions SET quantity = -0.1, fee = NULL WHERE external_id = 'kraken:ledger:L7'")
    conn.execute("UPDATE transactions SET quantity = 0.10005 WHERE external_id = 'kraken:ledger:L7:wallet'")
c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
with db.get_conn() as conn:
    healed = conn.execute("SELECT quantity, fee FROM transactions WHERE external_id = 'kraken:ledger:L7'").fetchone()[:]
    healed_w = conn.execute("SELECT quantity FROM transactions WHERE external_id = 'kraken:ledger:L7:wallet'").fetchone()[0]
check("a row an older parser stored without the fee is put right by the next sync",
      (round(healed[0], 6), healed[1], round(healed_w, 6)), (-0.10005, 0.00005, 0.1))
r = c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
check("a second sync adds nothing on either side", b"Imported 0 new" in r.data, True)
c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": ""})
check("the wallet can be unnamed again", brokers.link_for(kr_id)["wallet_account_id"], None)
# A withdrawal synced while no wallet was named is a coin that left.
# Naming the wallet afterwards books the past too — once — so the coin
# is back where it is, and the household total is whole again.
LEDGER["L8"] = {"type": "withdrawal", "asset": "XXBT", "amount": "-0.002", "fee": "0", "time": 1789100000}
BALANCE["XXBT"] = "0.00395"
c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id = 'kraken:ledger:L7:wallet'")
check("without a wallet the coin simply left",
      round(sum(h["quantity"] for h in ov.summary("EUR")["holdings"] if h["isin"] == "CRYPTO:BTC"), 6), 0.00395)
r = c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": str(wallet_id)}, follow_redirects=True)
check("naming the wallet books the earlier moves into it",
      (b"2 earlier moves are booked" in r.data, b"+0.102 BTC" in r.data), (True, True))
check("...and the household holds every unit again, but the fee's",
      round(sum(h["quantity"] for h in ov.summary("EUR")["holdings"] if h["isin"] == "CRYPTO:BTC"), 6), 0.10595)
_after = gains.realised("CRYPTO:BTC", [kr_id])["open_cost"] + gains.realised("CRYPTO:BTC", [wallet_id])["open_cost"]
check("...at the cost they carried: the two accounts' lots add up to what one held, less the fee's units",
      0 <= cost_all_on_kraken - _after <= cost_all_on_kraken * 0.001, True)
r = c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": str(wallet_id)}, follow_redirects=True)
check("...once: naming it again books nothing twice", b"earlier moves are booked" in r.data, False)
# A deposit is taken from the wallet only where the wallet held the
# coins: 0.05 back to Kraken from a wallet holding 0.10205 is a move;
# 0.5 is not, and stays a coin that arrived from somewhere else.
LEDGER["L9"] = {"type": "deposit", "asset": "XXBT", "amount": "0.05", "fee": "0", "time": 1789200000}
LEDGER["L10"] = {"type": "deposit", "asset": "XXBT", "amount": "0.5", "fee": "0", "time": 1789300000}
BALANCE["XXBT"] = "0.55395"
c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": ""})
c.post(f"/accounts/{kr_id}/sync", follow_redirects=True)
r = c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": str(wallet_id)}, follow_redirects=True)
check("naming takes the covered deposit from the wallet and leaves the other",
      (b"1 earlier moves are booked" in r.data, b"-0.05 BTC" in r.data), (True, True))
wq = sum(p_["quantity"] for p_ in importers.positions(wallet_id) if p_["isin"] == "CRYPTO:BTC")
check("...so the wallet holds what it had less what went back", round(wq, 6), 0.052)
with db.get_conn() as conn:
    dep = conn.execute("SELECT price FROM transactions WHERE external_id = 'kraken:ledger:L9'").fetchone()[0]
check("...and the deposit row on Kraken took the wallet's cost per unit, so the cost came back with the coins",
      dep is not None and dep > 0, True)
_after2 = gains.realised("CRYPTO:BTC", [kr_id])["open_cost"] + gains.realised("CRYPTO:BTC", [wallet_id])["open_cost"]
check("...the lots still adding up across both accounts, to the cent", abs(_after2 - _after) <= 0.011, True)
r = c.post(f"/accounts/{kr_id}/wallet/book", follow_redirects=True)
check("...and pressing it again books nothing", b"Nothing to book" in r.data, True)
c.post(f"/accounts/{kr_id}/wallet", data={"wallet_account_id": ""})
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id IN ('kraken:ledger:L9', 'kraken:ledger:L10', 'kraken:ledger:L9:wallet')")
del LEDGER["L7"]; del LEDGER["L8"]; del LEDGER["L9"]; del LEDGER["L10"]; BALANCE["XXBT"] = "0.106"
c.post(f"/accounts/{wallet_id}/delete", data={"confirm": "Ledger"})
r = c.post("/settings", data={"form": "kraken_forget"}, follow_redirects=True)
check("forgetting the key removes it and the link, keeps the account",
      (kraken.credentials_present(), brokers.link_for(kr_id), len(importers.positions(kr_id))),
      (False, None, 2))
c.post(f"/accounts/{kr_id}/delete", data={"confirm": "Kraken"})

# ---------------------------------------------------------------------------
print("\n27. Saxo, through an OAuth login that has to be kept alive")
# ---------------------------------------------------------------------------
saxo.save_credentials("app-key", "app-secret", "sim")
check("credentials are kept 0600",
      oct((settings.SECRETS_DIR / saxo.APP_FILE).stat().st_mode & 0o777), "0o600")
check("the redirect URL is the dashboard's, plus /saxo/callback",
      saxo.redirect_uri().endswith("/saxo/callback"), True)
check("IWDA:xams is IWDA.AS", saxo.yahoo_symbol("IWDA:xams"), "IWDA.AS")
check("a US listing is the bare ticker", saxo.yahoo_symbol("AAPL:xnas"), "AAPL")
check("an unknown exchange is left for the user", saxo.yahoo_symbol("XYZ:xxxx"), None)

SAXO_CALLS = []
TOKENS = {"n": 0}


def fake_saxo(method, url, headers, body):
    SAXO_CALLS.append((method, url))
    path = url.split("?")[0]
    if path.endswith("/token"):
        form = dict(urllib.parse.parse_qsl(body.decode()))
        if form.get("grant_type") == "refresh_token" and form.get("refresh_token") != f"r{TOKENS['n']}":
            return 401, b'{"error":"invalid_grant"}'
        TOKENS["n"] += 1
        return 200, json.dumps({"access_token": f"a{TOKENS['n']}", "expires_in": 1200,
                                "refresh_token": f"r{TOKENS['n']}", "refresh_token_expires_in": 3600}).encode()
    if headers.get("Authorization") != f"Bearer a{TOKENS['n']}":
        return 401, b'{"Message":"token"}'
    if path.endswith("/port/v1/clients/me"):
        return 200, json.dumps({"ClientKey": "CK1", "ClientId": "12345", "DefaultCurrency": "EUR"}).encode()
    if path.endswith("/port/v1/accounts/me"):
        return 200, json.dumps({"Data": [{"AccountKey": "AK1", "AccountId": "12345/1", "Currency": "EUR", "AccountType": "Normal"},
                                         {"AccountKey": "AK2", "AccountId": "12345/2", "Currency": "USD", "AccountType": "Normal"}]}).encode()
    if "/cs/v1/reports/trades/CK1" in path:
        if "$skip" not in url:
            return 200, json.dumps({"Data": [
                {"TradeId": 1001, "Uic": 36590, "AssetType": "Etf", "Amount": 10, "Price": 90.5,
                 "TradeEventType": "Bought", "BookedAmountAccountCurrency": -908.0, "AccountCurrency": "EUR",
                 "TradeExecutionTime": "2026-03-02T09:15:00Z", "InstrumentSymbol": "IWDA:xams",
                 "InstrumentDescription": "iShares Core MSCI World", "AccountId": "12345/1"}],
                "__next": url.split("?")[0] + "?$skip=1"}).encode()
        return 200, json.dumps({"Data": [
            {"TradeId": 1002, "Uic": 36590, "AssetType": "Etf", "Amount": 2, "Price": 95.0,
             "TradeEventType": "Sold", "BookedAmountAccountCurrency": 188.5, "AccountCurrency": "EUR",
             "TradeExecutionTime": "2026-05-04T10:00:00Z", "InstrumentSymbol": "IWDA:xams",
             "InstrumentDescription": "iShares Core MSCI World", "AccountId": "12345/1"},
            {"TradeId": 1003, "Uic": 211, "AssetType": "Stock", "Amount": 3, "Price": 180.0,
             "TradeEventType": "Bought", "BookedAmountAccountCurrency": -541.0, "AccountCurrency": "USD",
             "TradeExecutionTime": "2026-05-05T10:00:00Z", "InstrumentSymbol": "AAPL:xnas",
             "InstrumentDescription": "Apple Inc.", "AccountId": "12345/2"}]}).encode()
    if "/cs/v1/reports/bookings/CK1" in path:
        return 200, json.dumps({"Data": [
            {"BkAmountId": 5001, "Amount": 12.4, "Currency": "EUR", "Date": "2026-04-01", "BkAmountType": "Dividend",
             "InstrumentSymbol": "IWDA:xams", "Uic": 36590, "InstrumentDescription": "iShares Core MSCI World", "AccountId": "12345/1"},
            {"BkAmountId": 5002, "Amount": -0.5, "Currency": "EUR", "Date": "2026-04-01", "BkAmountType": "Custody Fee", "AccountId": "12345/1"},
            {"BkAmountId": 5003, "Amount": 2000.0, "Currency": "EUR", "Date": "2026-02-20", "BkAmountType": "Cash Transfer", "AccountId": "12345/1"}]}).encode()
    if path.endswith("/port/v1/positions"):
        q = dict(urllib.parse.parse_qsl(url.split("?")[1]))
        if q.get("AccountKey") == "AK1":
            return 200, json.dumps({"Data": [
                {"PositionId": "P1", "PositionBase": {"Uic": 36590, "AssetType": "Etf", "Amount": 8, "OpenPrice": 90.5, "ExecutionTimeOpen": "2026-03-02T09:15:00Z"},
                 "DisplayAndFormat": {"Symbol": "IWDA:xams", "Description": "iShares Core MSCI World", "Currency": "EUR"}},
                {"PositionId": "P2", "PositionBase": {"Uic": 4712, "AssetType": "Stock", "Amount": 40, "OpenPrice": 42.1, "ExecutionTimeOpen": "2025-11-12T14:00:00Z"},
                 "DisplayAndFormat": {"Symbol": "SIE:xetr", "Description": "Siemens AG", "Currency": "EUR"}}]}).encode()
        return 200, json.dumps({"Data": [
            {"PositionId": "P3", "PositionBase": {"Uic": 211, "AssetType": "Stock", "Amount": 3, "OpenPrice": 180.0, "ExecutionTimeOpen": "2026-05-05T10:00:00Z"},
             "DisplayAndFormat": {"Symbol": "AAPL:xnas", "Description": "Apple Inc.", "Currency": "USD"}}]}).encode()
    if path.endswith("/port/v1/balances"):
        q = dict(urllib.parse.parse_qsl(url.split("?")[1]))
        if q.get("AccountKey") == "AK1":
            return 200, json.dumps({"CashBalance": 1291.9, "Currency": "EUR", "TransactionsNotBooked": 0}).encode()
        return 200, json.dumps({"CashBalance": 459.0, "Currency": "USD", "TransactionsNotBooked": 0}).encode()
    return 404, b'{"Message":"no such endpoint"}'


saxo.transport = fake_saxo
r = c.post("/accounts/new", data={"name": "Saxo", "type": "broker", "currency": "EUR"})
sx_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{sx_id}")
check("a broker account offers the Saxo connection once credentials exist", b"Connect Saxo" in r.data, True)
r = c.get(f"/saxo/connect/{sx_id}")
check("connecting leaves for Saxo's login", (r.status_code, "sim.logonvalidation.net/authorize" in r.headers["Location"]), (302, True))
qs = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(r.headers["Location"]).query))
check("...as the registered app, back to /saxo/callback",
      (qs["client_id"], qs["response_type"], qs["redirect_uri"].endswith("/saxo/callback")), ("app-key", "code", True))
r = c.get("/saxo/callback?code=abc&state=not-ours", follow_redirects=True)
check("a code from a login this app did not start is refused", b"not from a connection this app started" in r.data, True)
r = c.get(f"/saxo/callback?code=abc&state={qs['state']}", follow_redirects=True)
check("the genuine return links both Saxo accounts",
      b"Connected: Saxo, Saxo 12345/2" in r.data, True)
links_ = {l["remote_id"]: l for l in brokers.links() if l["provider"] == "saxo"}
check("...the first to the account the login started from", links_["AK1"]["account_id"], sx_id)
check("...the second to an account created beside it, in its own currency",
      (links_["AK2"]["account"], links_["AK2"]["account_currency"]), ("Saxo 12345/2", "USD"))
check("...and pulled both", b"Imported" in r.data, True)
pos = {p_["isin"]: p_ for p_ in importers.positions(sx_id)}
check("the traded ETF is held at what the trades add up to", pos["SAXO:36590"]["quantity"], 8.0)
check("...with its money in and out", round(pos["SAXO:36590"]["net_invested"], 2), round(908.0 - 188.5, 2))
check("a position with no trade in Saxo's history is recorded as a transfer in",
      (pos["SAXO:4712"]["quantity"], pos["SAXO:4712"]["net_invested"], pos["SAXO:4712"]["last_price"]),
      (40.0, 0.0, 42.1))
with db.get_conn() as conn:
    adj = conn.execute("SELECT txn_date, kind, description FROM transactions WHERE isin = 'SAXO:4712'").fetchone()
    div = conn.execute("SELECT kind, amount, isin FROM transactions WHERE external_id = 'saxo:booking:5001'").fetchone()
    fee = conn.execute("SELECT kind, amount FROM transactions WHERE external_id = 'saxo:booking:5002'").fetchone()
    dep = conn.execute("SELECT kind, amount FROM transactions WHERE external_id = 'saxo:booking:5003'").fetchone()
    sbal = conn.execute("SELECT amount, currency FROM balances WHERE account_id = ? ORDER BY as_of DESC, id DESC LIMIT 1", (sx_id,)).fetchone()
    usd_pos = importers.positions(links_["AK2"]["account_id"])
    sec = conn.execute("SELECT symbol, symbol_source, name FROM securities WHERE isin = 'SAXO:36590'").fetchone()
check("...dated when Saxo opened it, and named for what it is",
      (adj["txn_date"], adj["kind"], "not explained by its trades" in adj["description"]), ("2025-11-12", "transfer", True))
check("a dividend booking is a dividend on the instrument", (div["kind"], div["amount"], div["isin"]), ("dividend", 12.4, "SAXO:36590"))
check("a custody fee is a fee", (fee["kind"], fee["amount"]), ("fee", -0.5))
check("a cash transfer in is a deposit", (dep["kind"], dep["amount"]), ("deposit", 2000.0))
check("the cash balance is the account's reading", (sbal["amount"], sbal["currency"]), (1291.9, "EUR"))
check("the USD account holds its own trade and nothing of the other's",
      [(p_["isin"], p_["quantity"]) for p_ in usd_pos], [("SAXO:211", 3.0)])
check("the instrument's Yahoo ticker is remembered for the price feed",
      (sec["symbol"], sec["symbol_source"], sec["name"]), ("IWDA.AS", "saxo", "iShares Core MSCI World"))
prices.set_symbol("SAXO:36590", "EUNL.DE")
r = c.post(f"/accounts/{sx_id}/sync", follow_redirects=True)
check("a second sync adds nothing", b"Imported 0 new transactions" in r.data, True)
with db.get_conn() as conn:
    sec2 = conn.execute("SELECT symbol FROM securities WHERE isin = 'SAXO:36590'").fetchone()
check("...and never replaces a ticker the user typed", sec2["symbol"], "EUNL.DE")

# The chain: a keep-alive tick renews it; a stale refresh token lapses it.
before = saxo.state()["refresh_token"]
ka = saxo.keepalive()
check("a keep-alive tick renews the chain", (ka["status"], saxo.state()["refresh_token"] != before), ("ok", True))
st = saxo.state(); st["refresh_token"] = "r0-stale"; saxo._save_state(st)
ka = saxo.keepalive()
check("a refused refresh token marks the login as lapsed",
      (ka["status"], saxo.describe()["lapsed"]), ("error", True))
r = c.get(f"/accounts/{sx_id}")
check("...and the account page says so, offering to connect again",
      b"login has lapsed" in r.data and b"Connect Saxo again" in r.data, True)
r = c.post(f"/accounts/{sx_id}/sync", follow_redirects=True)
check("a sync while lapsed fails with the reason", b"connect again" in r.data, True)
check("a lapsed chain is left alone by the keep-alive", saxo.keepalive()["status"], "idle")
r = c.get(f"/saxo/connect/{sx_id}")
qs2 = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(r.headers["Location"]).query))
r = c.post(f"/saxo/paste/{sx_id}", data={"pasted": f"http://dead/saxo/callback?code=xyz&state={qs2['state']}"},
           follow_redirects=True)
check("finishing by hand from the dead page's address works",
      b"Connected: Saxo" in r.data and saxo.describe()["alive"], True)
check("...reusing the same links, not doubling them",
      len([l for l in brokers.links() if l["provider"] == "saxo"]), 2)
r = c.get("/settings/banks")
check("the settings page shows Saxo and Kraken", b'id="saxo"' in r.data and b'id="kraken"' in r.data, True)
check("...with the redirect URL to register", b"/saxo/callback" in r.data, True)
r = c.post("/settings", data={"form": "saxo_forget"}, follow_redirects=True)
check("forgetting Saxo drops the credentials, the tokens and the links, keeps the accounts",
      (saxo.credentials_present(), saxo.state(), [l for l in brokers.links() if l["provider"] == "saxo"],
       len(importers.positions(sx_id))), (False, {}, [], 2))
for aid in (sx_id, links_["AK2"]["account_id"]):
    with db.get_conn() as conn:
        nm = conn.execute("SELECT name FROM accounts WHERE id = ?", (aid,)).fetchone()["name"]
    c.post(f"/accounts/{aid}/delete", data={"confirm": nm})

# ---------------------------------------------------------------------------
print("\n28. A security's rows, and correcting one")
# ---------------------------------------------------------------------------
# The rows behind IWDA at the Degiro account, from the earlier imports.
r = c.get("/securities/IE00B4L5Y983")
check("the security page renders", r.status_code, 200)
check("...naming the accounts it is held in", b"Degiro" in r.data, True)
check("...with a correction form per row", r.data.count(b"Save correction") >= 1, True)
r = c.get("/securities/XX0000000000")
check("an unknown security is a 404, not a crash", r.status_code, 404)
r = c.get("/portfolio")
check("the portfolio's holdings link to the security page", b"/securities/IE00B4L5Y983" in r.data, True)
# A security sold down to nothing leaves the holdings table; it is
# listed below it, with what it made, rather than vanishing.
check("a security sold out is listed under the holdings, not gone",
      (b"Sold out" in r.data, b"LU0000000009" in r.data), (True, True))
# And the holding page marks the trades on its chart, as a switch.
r = c.get("/securities/IE00B4L5Y983")
check("the holding page carries its trades for the chart's marks",
      (b'id="sec-marks"' in r.data, b'"kind": "buy"' in r.data), (True, True))
r = c.get(f"/accounts/{broker_id}")
check("...and so does the account's holdings table", b"/securities/IE00B4L5Y983" in r.data, True)

with db.get_conn() as conn:
    row = dict(conn.execute("SELECT * FROM transactions WHERE isin = 'IE00B4L5Y983' AND kind = 'buy' "
                            "AND source != 'manual' ORDER BY id LIMIT 1").fetchone())
before = importers.positions(row["account_id"])
q_before = next(p_["quantity"] for p_ in before if p_["isin"] == "IE00B4L5Y983")
r = c.post(f"/transactions/{row['id']}/edit", data={
    "txn_date": row["txn_date"], "kind": "buy", "quantity": str(abs(row["quantity"]) + 5),
    "price": str(row["price"]), "amount": str(abs(row["amount"]) + 1), "fee": "1.50",
    "description": row["description"], "back": "/securities/IE00B4L5Y983"}, follow_redirects=True)
check("a correction is accepted and returns to the security page", b"Corrected." in r.data and b"IE00B4L5Y983" in r.data, True)
with db.get_conn() as conn:
    after = dict(conn.execute("SELECT * FROM transactions WHERE id = ?", (row["id"],)).fetchone())
check("...the quantity, amount and fee are the corrected ones, with the sign the kind supplies",
      (after["quantity"], after["amount"], after["fee"]),
      (abs(row["quantity"]) + 5, -(abs(row["amount"]) + 1), 1.5))
check("...the id that recognises the row on re-import is untouched", after["external_id"], row["external_id"])
check("...and the row says when it was corrected", bool(after["edited_at"]), True)
q_after = next(p_["quantity"] for p_ in importers.positions(row["account_id"]) if p_["isin"] == "IE00B4L5Y983")
check("the holding follows the correction", round(q_after - q_before, 6), 5.0)
r = upload(broker_id, fixtures.DEGIRO_CSV)
with db.get_conn() as conn:
    again = dict(conn.execute("SELECT quantity FROM transactions WHERE id = ?", (row["id"],)).fetchone())
check("re-importing the file leaves the correction alone", again["quantity"], abs(row["quantity"]) + 5)
r = c.post(f"/transactions/{row['id']}/edit", data={
    "txn_date": row["txn_date"], "kind": "sell", "quantity": "3", "price": "80",
    "amount": "240", "back": "/securities/IE00B4L5Y983"}, follow_redirects=True)
with db.get_conn() as conn:
    sold = dict(conn.execute("SELECT kind, quantity, amount FROM transactions WHERE id = ?", (row["id"],)).fetchone())
check("changing a buy into a sale flips both signs", (sold["kind"], sold["quantity"], sold["amount"]), ("sell", -3.0, 240.0))
r = c.post(f"/transactions/{row['id']}/edit", data={"txn_date": "2999-01-01", "kind": "buy", "amount": "1",
                                                     "back": "/securities/IE00B4L5Y983"}, follow_redirects=True)
check("a date in the future is refused with the reason", b"in the future" in r.data, True)
r = c.post(f"/transactions/{row['id']}/edit", data={"txn_date": row["txn_date"], "kind": "buy", "amount": "",
                                                     "back": "/securities/IE00B4L5Y983"}, follow_redirects=True)
check("a missing amount is refused", b"amount is missing" in r.data, True)
r = c.post(f"/transactions/{row['id']}/edit", data={"txn_date": row["txn_date"], "kind": "buy", "amount": "2",
                                                     "back": "https://evil.example/x"}, follow_redirects=False)
check("an off-site 'back' is not followed", "evil" not in r.headers["Location"] and r.headers["Location"].endswith("/transactions"), True)
# Put the row back as it was, so later sections see the file's figures.
c.post(f"/transactions/{row['id']}/edit", data={
    "txn_date": row["txn_date"], "kind": "buy", "quantity": str(abs(row["quantity"])),
    "price": str(row["price"]), "amount": str(abs(row["amount"])), "fee": str(row["fee"] or ""),
    "description": row["description"], "back": "/securities/IE00B4L5Y983"})
check("a correction of a transaction that does not exist is refused",
      b"does not exist" in c.post("/transactions/99999999/edit", data={"amount": "1", "kind": "buy"},
                                  follow_redirects=True).data, True)

# ---------------------------------------------------------------------------
print("\n29. Price history, the performance chart, the crypto page")
# ---------------------------------------------------------------------------
from app import crypto                                      # noqa: E402

# Daily history from Yahoo, and the backfill that runs once per security.
DAILY = {"chart": {"result": [{"meta": {"currency": "EUR"},
         "timestamp": [1767225600 + i * 86400 for i in range(5)],
         "indicators": {"quote": [{"close": [100.0, 101.0, None, 103.0, 104.0]}]}}]}}
hist_rows = prices.history("IWDA.AS", "2026-01-01", get=lambda url: DAILY)
check("daily history is (day, close, currency), gaps dropped",
      (len(hist_rows), hist_rows[0], hist_rows[-1][1]), (4, ("2026-01-01", 100.0, "EUR"), 104.0))
check("pence become pounds in history too",
      prices.history("X.L", "2026-01-01", get=lambda url: {"chart": {"result": [{"meta": {"currency": "GBp"},
          "timestamp": [1767225600], "indicators": {"quote": [{"close": [2650.0]}]}}]}})[0][1:], (26.5, "GBP"))
calls = []
def daily_get(url):
    calls.append(url)
    if "period1=" in url:
        return DAILY
    return fake_get(url)
with db.get_conn() as conn:
    conn.execute("DELETE FROM app_state WHERE key LIKE 'price_backfilled:%'")
    conn.execute("DELETE FROM prices WHERE isin = 'IE00B4L5Y983' AND as_of < '2026-09-01'")
info = prices.backfill(get=daily_get, isins=["IE00B4L5Y983"])
check("a held security is backfilled from its first trade", info["backfilled"], 1)
with db.get_conn() as conn:
    n = conn.execute("SELECT COUNT(*) AS n FROM prices WHERE isin = 'IE00B4L5Y983' AND as_of < '2026-09-01'").fetchone()["n"]
check("...the daily prices are stored", n, 4)
calls.clear()
prices.backfill(get=daily_get, isins=["IE00B4L5Y983"])
check("...and asked for once, never again", any("period1=" in u for u in calls), False)
check("a symbol Yahoo cannot chart is not asked about again either",
      (prices.backfill(get=lambda url: (_ for _ in ()).throw(prices.PriceError("no")), isins=["XX1234567890"])["backfilled"],
       db.get_state("price_backfilled:XX1234567890")), (0, "failed"))

series = prices.series_for("IE00B4L5Y983")
check("the security's series runs from its first row to today",
      (series["first"], series["points"][0]["date"], len(series["points"]) > 100), (series["points"][0]["date"], series["first"], True))
pt = next(p_ for p_ in series["points"] if p_["date"] == "2026-09-05")
check("...a day without a price uses the last one before it", bool(pt["value"]) and pt["quantity"] > 0, True)
check("...invested and income run alongside", ("invested" in pt, "income" in pt), (True, True))
r = c.get("/api/securities/IE00B4L5Y983/history")
check("the history API answers", (r.status_code, len(r.get_json()["points"]) > 0), (200, True))
r = c.get("/securities/IE00B4L5Y983")
check("the security page draws the chart", b"sec-chart" in r.data and b"Since the first purchase" in r.data, True)

# The crypto page: nothing held yet, then a coin typed in by hand.
r = c.get("/crypto")
check("the crypto page renders with nothing held", (r.status_code, b"No coins yet" in r.data), (200, True))
r = c.post(f"/accounts/{broker_id}/add", data={"kind": "buy", "txn_date": "2026-06-01", "isin": "CRYPTO:BTC",
                                              "security_name": "Bitcoin", "quantity": "0.05", "price": "60000",
                                              "fee": "5"}, follow_redirects=True)
check("a coin can be typed in with CRYPTO:BTC as its ISIN", b"Added." in r.data, True)
with db.get_conn() as conn:
    conn.execute("INSERT INTO securities (isin, symbol, name, symbol_source) VALUES ('CRYPTO:BTC', 'BTC-EUR', 'Bitcoin EUR', 'yahoo') "
                 "ON CONFLICT(isin) DO UPDATE SET symbol = 'BTC-EUR'")
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('CRYPTO:BTC', '2026-09-11', 66000, 'EUR')")
held_coins = crypto.coins("EUR")
check("the coin is held with its cost basis and gain",
      (held_coins[0]["code"], held_coins[0]["quantity"], held_coins[0]["net_invested"], round(held_coins[0]["gain"], 2)),
      ("BTC", 0.05, 3005.0, round(0.05 * 66000 - 3005, 2)))
check("...and with no sale the cost basis is what went in", held_coins[0]["cost_basis"], 3005.0)
# The move from Financial Planner (up to 0.46) kept a Kraken trade id
# bare, and the Kraken sync wrote the same fill under kraken:trade:…
# — one buy, twice the cost. The start-up repair drops the old app's
# copy where Kraken's exists and gives a lone one the sync's id.
with db.get_conn() as conn:
    for ext, src, amt in (("TUT7MA-K67YX-X6Z4TJ", "financial_planner:crypto_csv", -922.35),
                          ("kraken:trade:TUT7MA-K67YX-X6Z4TJ", "kraken", -924.66),
                          ("TQJFTV-IVV7T-QOKG2Q", "financial_planner:crypto_csv", -1000.0)):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                     "VALUES (?, '2026-05-19', 'Buy BTC on Kraken', ?, 'EUR', 'buy', 'CRYPTO:BTC', 'Bitcoin', 0.0139, 66254.5, ?, ?)",
                     (broker_id, amt, ext, src))
    conn.execute("DELETE FROM app_state WHERE key = 'fp_kraken_trade_ids'")
    db._repair_rows(conn)
    ids = sorted(r_[0] for r_ in conn.execute("SELECT external_id FROM transactions WHERE account_id = ? AND isin = 'CRYPTO:BTC' AND external_id LIKE '%T%-%-%'", (broker_id,)))
# The account that was two things at once: the rows a source brought
# can be handed to the account they belong to, ids and all.
r = c.post("/accounts/new", data={"name": "Exodus", "type": "broker", "currency": "EUR"})
exodus_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{broker_id}")
check("the account page lists where its rows came from, with a way to move a source",
      (b"Where the rows came from" in r.data, b"financial_planner:crypto_csv" in r.data, b"Exodus" in r.data), (True, True, True))
r = c.post(f"/accounts/{broker_id}/move-rows", data={"source": "financial_planner:crypto_csv", "to_account_id": str(exodus_id)}, follow_redirects=True)
check("moving a source's rows says how many", b"1 row moved to Exodus" in r.data, True)
with db.get_conn() as conn:
    check("...and they are there under the same id",
          conn.execute("SELECT account_id FROM transactions WHERE external_id = 'kraken:trade:TQJFTV-IVV7T-QOKG2Q'").fetchone()[0], exodus_id)
    conn.execute("UPDATE transactions SET account_id = ? WHERE external_id = 'kraken:trade:TQJFTV-IVV7T-QOKG2Q'", (broker_id,))
r = c.post(f"/accounts/{broker_id}/move-rows", data={"source": "kraken", "to_account_id": str(broker_id)}, follow_redirects=True)
check("...not to itself", b"Pick another account" in r.data, True)
c.post(f"/accounts/{exodus_id}/delete", data={"confirm": "Exodus"})
check("the duplicate from the old app is gone and the lone one carries the sync's id",
      ids, ["kraken:trade:TQJFTV-IVV7T-QOKG2Q", "kraken:trade:TUT7MA-K67YX-X6Z4TJ"])
with db.get_conn() as conn:
    check("...and only Kraken's copy of the fill is left, fee included",
          conn.execute("SELECT amount, source FROM transactions WHERE external_id = 'kraken:trade:TUT7MA-K67YX-X6Z4TJ'").fetchone()[:], (-924.66, "kraken"))
    conn.execute("DELETE FROM transactions WHERE external_id LIKE 'kraken:trade:T%'")
held_coins = crypto.coins("EUR")
# Half the coins move to a hardware wallet — an account here — at the
# cost they carry. Nothing was sold, so the cost basis of what is held
# must not move; "net invested" cannot tell, the lots can.
r = c.post("/accounts/new", data={"name": "Ledger", "type": "broker", "currency": "EUR"})
ledger_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id) "
                 "VALUES (?, '2026-09-12', 'To Ledger: 0.025 BTC', 0, 'EUR', 'transfer', 'CRYPTO:BTC', 'Bitcoin', -0.025, NULL, 'move-out')", (broker_id,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id) "
                 "VALUES (?, '2026-09-12', 'From Kraken: 0.025 BTC', 0, 'EUR', 'transfer', 'CRYPTO:BTC', 'Bitcoin', 0.025, 60100, 'move-in')", (ledger_id,))
held_coins = crypto.coins("EUR")
check("a coin moved to one's own wallet keeps the quantity and the cost basis",
      (round(held_coins[0]["quantity"], 6), round(held_coins[0]["cost_basis"], 2), sorted(held_coins[0]["accounts"])),
      (0.05, 3005.0, sorted([held_coins[0]["accounts"][0], "Ledger"])))
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id IN ('move-out', 'move-in')")
    conn.execute("DELETE FROM accounts WHERE id = ?", (ledger_id,))
r = c.get("/crypto")
check("the crypto page shows the wallet", b"BTC" in r.data and b"Unrealised gain" in r.data, True)
BTC_DAILY = {"chart": {"result": [{"meta": {"currency": "EUR"},
             "timestamp": [1780000000 + i * 86400 for i in range(10)],
             "indicators": {"quote": [{"close": [60000 + i * 500 for i in range(10)]}]}}]}}
prices._get_json = lambda url: BTC_DAILY
crypto._cache.clear()
ch = crypto.chart("CRYPTO:BTC", "1m", "price", "EUR")
check("the price chart runs over the range with the change",
      (len(ch["points"]), ch["points"][0]["value"], round(ch["change"]), round(ch["change_pct"], 1)), (10, 60000.0, 4500, 7.5))
wl = crypto.chart("CRYPTO:BTC", "1m", "wallet", "EUR")
check("the wallet chart is price times units held on the day",
      (wl["points"][-1]["value"], wl["points"][-1]["units"]), (0.05 * 64500, 0.05))
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, external_id) "
                 "VALUES (?, '2020-01-01', 'fee 0.0001 BTC', 0, 'EUR', 'transfer', 'CRYPTO:BTC', 'Bitcoin', -0.0001, 'early-fee')", (broker_id,))
wl = crypto.chart("CRYPTO:BTC", "1m", "wallet", "EUR")
check("a wallet that starts below nothing has a change but no percentage",
      (wl["change"] is not None, wl["change_pct"]), (True, None))
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id = 'early-fee'")
r = c.get("/api/crypto/BTC/chart?range=1m&mode=wallet")
check("the chart API answers", (r.status_code, len(r.get_json()["points"])), (200, 10))
check("an unknown coin is a 404", c.get("/crypto/DOGE").status_code, 404)
prices._get_json = fake_get

# ---------------------------------------------------------------------------
print("\n30. Loans and mortgages")
# ---------------------------------------------------------------------------
from app import loans                                       # noqa: E402

# The bank's own worked example: 168 249 CHF, quarterly, first instalment
# 4 271.21 on 2019-10-10 of which 128.61 interest.
MORTGAGE = {"principal": 168249.0, "rate_pct": 128.61 / 168249 * 4 * 100, "first_payment": "2019-10-10",
            "period_months": 3, "payment": 4271.21, "extras": "[]"}
sched = loans.schedule(MORTGAGE)
check("the first instalment reproduces the bank's split to the cent",
      (sched[0]["interest"], sched[0]["capital"], sched[0]["balance"]), (128.61, 4142.60, 164106.40))
check("the loan is paid off in the 41st instalment, in autumn 2029",
      (len(sched), sched[-1]["date"][:7]), (41, "2029-10"))
check("...and the last instalment is only what is left", sched[-1]["balance"], 0.0)
st = loans.status(MORTGAGE, date(2026, 6, 1))
check("the balance as of a day is the schedule's",
      (st["payments_done"], 55000 < st["balance"] < 55600), (27, True))
check("a term instead of a payment gives a constant annuity",
      round(loans.annuity(100000, 0.03 / 12, 240), 2), 554.60)
check("a zero rate divides evenly", loans.annuity(1200, 0.0, 12), 100.0)
with_extra = loans.schedule({**MORTGAGE, "extras": json.dumps([{"date": "2027-04-10", "amount": 20000}])})
check("an extra repayment shortens the loan", len(with_extra) < 41, True)
check("...and is applied on its date", next(r_ for r_ in with_extra if r_["date"] == "2027-04-10")["extra"], 20000.0)

r = c.get("/loans")
check("the loans page renders empty", (r.status_code, b"Add a loan" in r.data), (200, True))
r = c.post("/loans", data={"form": "loan_add", "name": "Mortgage, house", "principal": "168249", "currency": "CHF",
                           "rate_pct": f"{MORTGAGE['rate_pct']:.6f}", "first_payment": "2019-10-10",
                           "period_months": "3", "payment": "4271.21"}, follow_redirects=True)
check("a loan is added", b"Loan added" in r.data and b"Mortgage, house" in r.data, True)
loan = loans.all_loans()[0]
with db.get_conn() as conn:
    acct = conn.execute("SELECT * FROM accounts WHERE id = ?", (loan["account_id"],)).fetchone()
    bal = conn.execute("SELECT amount, currency, balance_type FROM balances WHERE account_id = ? ORDER BY as_of DESC, id DESC LIMIT 1",
                       (loan["account_id"],)).fetchone()
check("...with an account of type loan", (acct["type"], acct["currency"]), ("loan", "CHF"))
check("...whose balance is today's schedule figure, negative, from the schedule",
      (bal["amount"] < 0, bal["currency"], bal["balance_type"]), (True, "CHF", "schedule"))
with db.get_conn() as conn:
    past = conn.execute("SELECT as_of, amount FROM balances WHERE account_id = ? AND as_of < '2020-01-01' ORDER BY as_of",
                        (loan["account_id"],)).fetchall()
check("...and a reading at every instalment already past, so the debt has a history",
      ([(p_["as_of"], round(-p_["amount"])) for p_ in past]), [("2019-10-10", round(168249 - (4271.21 - 128.61)))])
sm = ov.summary("EUR")
check("the overview subtracts the debt from the net worth",
      (sm["debt"] > 0, round(sm["net_worth"], 2) == round(sm["cash"] + sm["securities"] - sm["debt"], 2)), (True, True))
r = c.get("/")
check("...and shows it", b"Debt" in r.data, True)
check("the schedule is on the page", b"instalment by instalment" in r.data or b"Balance after" in c.get("/loans").data, True)

# The loan's own page: where it stands, the balance over its life,
# what each instalment is made of, the schedule — the bank's own
# figures, as of a day in the middle of it.
r = c.get(f"/loans/{loan['id']}")
body = r.data.decode()
check("the loan has a page of its own",
      (r.status_code, "Outstanding today" in body, "Repaid so far" in body, "Original loan (2019)" in body, "Payoff date" in body), (200, True, True, True, True))
check("...with the balance chart, the split and the schedule",
      ("Outstanding balance over time" in body, "Where each instalment goes" in body, "Amortisation schedule" in body, body.count('class="future"') > 0), (True, True, True, True))
check("...paid off in autumn 2029 after 41 instalments", ("2029-10-10" in body, "41 instalments" in body), (True, True))
check("...and the loans list links to it", f'href="/loans/{loan["id"]}"' in c.get("/loans").data.decode(), True)
check("a loan that does not exist is a 404", c.get("/loans/9999").status_code, 404)
dl = loans.detail(loan, "EUR", date(2026, 9, 16))
check("the detail says what is owed on a day and what has been repaid",
      (round(dl["status"]["balance"]), round(dl["status"]["paid_capital"]), round(100 * dl["status"]["progress"], 1)), (51051, 117198, 69.7))

# A loan account that exists already — moved in from another app with
# its readings — gets its terms on its own page, and keeps its name.
r = c.post("/accounts/new", data={"name": "Hypothek", "type": "loan", "currency": "CHF"})
hyp_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = c.get(f"/accounts/{hyp_id}")
check("a loan account without terms asks for them", b"Give it its terms" in r.data, True)
r = c.post(f"/accounts/{hyp_id}/loan", data={"principal": "168249", "rate_pct": f"{MORTGAGE['rate_pct']:.6f}", "first_payment": "2019-10-10",
                                             "period_months": "3", "payment": "4271.21", "drawn_amount": "150000", "drawn_currency": "EUR"},
           follow_redirects=True)
body = r.data.decode()
check("giving them lands on the loan's page, with what it was drawn as",
      ("The terms are on record" in body, "150,000" in body, "1.12166" in body, "Hypothek" in body), (True, True, True, True))
hyp = loans.for_account(hyp_id)
check("...the account keeps its name and currency and now carries the terms",
      (hyp["name"], hyp["currency"], hyp["drawn_amount"], hyp["drawn_currency"]), ("Hypothek", "CHF", 150000.0, "EUR"))
r = c.get(f"/accounts/{hyp_id}")
check("...and its account page says so and links across", (b"A loan on its schedule" in r.data, b"The loan over time" in r.data), (True, True))
r = c.post(f"/accounts/{hyp_id}/loan", data={"principal": "1", "rate_pct": "1", "first_payment": "2020-01-01", "period_months": "1", "payment": "1"}, follow_redirects=True)
check("terms cannot be given twice", b"already has its terms" in r.data, True)
r = c.post(f"/accounts/{broker_id}/loan", data={"principal": "1", "rate_pct": "1", "first_payment": "2020-01-01", "period_months": "1", "payment": "1"}, follow_redirects=True)
check("...nor to an account that is not a loan", b"not a loan" in r.data, True)
with db.get_conn() as conn:
    conn.execute("DELETE FROM accounts WHERE id = ?", (hyp_id,))
r = c.post("/loans", data={"form": "loan_add", "name": "Bad", "principal": "1000", "currency": "EUR", "rate_pct": "60",
                           "first_payment": "2026-01-01", "period_months": "1", "payment": "10"}, follow_redirects=True)
check("a payment that cannot cover the interest is refused", b"never end" in r.data, True)
r = c.post("/loans", data={"form": "loan_add", "name": "Car", "principal": "12000", "currency": "EUR", "rate_pct": "4.5",
                           "first_payment": "2026-02-01", "period_months": "1", "payment": "", "term_months": "48"},
           follow_redirects=True)
car = next(l_ for l_ in loans.all_loans() if l_["name"] == "Car")
check("a term without a payment works the payment out", round(loans.status(car)["payment"], 2), 273.64)
r = c.post("/loans", data={"form": "loan_edit", "id": car["id"], "name": "Car loan", "principal": "12000", "currency": "EUR",
                           "rate_pct": "4.5", "first_payment": "2026-02-01", "period_months": "1", "payment": "300",
                           "extras": "2027-02-01 2000\n"}, follow_redirects=True)
car2 = loans.get(car["id"])
check("the terms can be changed", (b"Loan updated" in r.data, car2["name"], car2["payment"], "2027-02-01" in car2["extras"]),
      (True, "Car loan", 300.0, True))
r = c.post("/loans", data={"form": "loan_delete", "id": car["id"], "confirm": "wrong"}, follow_redirects=True)
check("deleting asks for the name", b"exactly" in r.data and loans.get(car["id"]) is not None, True)
r = c.post("/loans", data={"form": "loan_delete", "id": car["id"], "confirm": "Car loan"}, follow_redirects=True)
with db.get_conn() as conn:
    gone = conn.execute("SELECT 1 FROM accounts WHERE id = ?", (car["account_id"],)).fetchone()
check("...and then removes the loan and its account", (loans.get(car["id"]), gone), (None, None))
# A balance typed in by hand on the loan's account wins for its day.
c.post(f"/accounts/{loan['account_id']}/balance", data={"amount": "-55000", "as_of": date.today().isoformat()})
loans.write_all_balances()
with db.get_conn() as conn:
    newest = conn.execute("SELECT amount, balance_type FROM balances WHERE account_id = ? ORDER BY as_of DESC, id DESC LIMIT 1",
                          (loan["account_id"],)).fetchone()
check("a reading typed in today is not overwritten by the schedule", (newest["amount"], newest["balance_type"]), (-55000.0, "manual"))
# ...and from there the schedule runs from the lender's figure, not the sum's.
loan = loans.get(loan["id"])
st = loans.status(loan)
check("the reading anchors the schedule", (loan["anchor"]["amount"], loan["anchor"]["date"], st["balance"], st["paid_capital"]),
      (55000.0, date.today().isoformat(), 55000.0, round(168249 - 55000, 2)))
anchored = loans.schedule(loan)
first_after = next(r_ for r_ in anchored if r_["date"] > date.today().isoformat())
check("...and the first instalment after it starts from that figure",
      (first_after["anchored"], round(first_after["balance"] + first_after["capital"], 2)), (True, 55000.0))
check("...while the instalments before it stay as computed", anchored[0]["balance"], 164106.40)
check("...and the page says so", b"from the reading of" in c.get(f"/loans/{loan['id']}").data, True)
# A reading that says more is owed than the sum thought — the sum had
# the loan paid off by then — still gets a schedule from that day on.
late = {**MORTGAGE, "anchor": {"date": "2030-06-01", "amount": 5000.0}}
late_rows = loans.schedule(late)
check("a reading after the computed payoff restarts the schedule from it",
      (late_rows[-2]["date"] < "2030-06-01" or late_rows[-2]["anchored"], late_rows[-1]["balance"], any(r_["anchored"] for r_ in late_rows)), (True, 0.0, True))
check("a schedule with no reading has no anchored row", any(r_["anchored"] for r_ in loans.schedule(MORTGAGE)), False)
c.post("/loans", data={"form": "loan_delete", "id": loan["id"], "confirm": "Mortgage, house"})

# ---------------------------------------------------------------------------
print("\n31. Time-weighted and money-weighted return")
# ---------------------------------------------------------------------------
from app import performance                                 # noqa: E402

check("a 10% rise with no flows is 10%", round(performance.twr([("a", 100.0), ("b", 105.0), ("c", 110.0)], {}), 4), 0.1)
check("money added is not return",
      round(performance.twr([("a", 100.0), ("b", 200.0), ("c", 220.0)], {"b": 100.0}), 4), 0.1)
check("money taken out is not loss",
      round(performance.twr([("a", 100.0), ("b", 50.0), ("c", 55.0)], {"b": -50.0}), 4), 0.1)
check("a day without a value breaks the chain for that day only",
      round(performance.twr([("a", 100.0), ("b", None), ("c", 110.0), ("d", 121.0)], {}), 4), 0.1)
check("nothing to measure is None", performance.twr([("a", 100.0)], {}), None)
# The textbook divergence: 100 doubles to 200, 100 more is added, the lot halves to 150.
vals = [("2025-01-01", 100.0), ("2025-07-01", 200.0), ("2025-07-02", 300.0), ("2026-01-01", 150.0)]
check("TWR of double-then-halve is zero whatever was added between",
      round(performance.twr(vals, {"2025-07-02": 100.0}), 6), 0.0)
m = performance.mwr([("2025-01-01", -100.0), ("2025-07-02", -100.0)], "2026-01-01", 150.0)
check("...while the MWR says the money lost, because more of it was there for the fall", m < -0.2, True)
check("money that doubles in a year is +100% a year",
      round(performance.mwr([("2025-01-01", -100.0)], "2026-01-01", 200.0), 2), 1.0)
check("money that halves in a year is −50% a year",
      round(performance.mwr([("2025-01-01", -100.0)], "2026-01-01", 50.0), 2), -0.5)
check("MWR needs money in and money out", (performance.mwr([("2025-01-01", -5.0)], "2026-01-01", 0.0),
                                           performance.mwr([("2025-01-01", 5.0)], "2026-01-01", 10.0)), (None, None))
check("21% over two years is 10% a year", round(performance.annualise(0.21, 730), 3), 0.1)
check("a fortnight is not annualised", performance.annualise(0.02, 14), None)

# A holding with a known path: bought 10 at 100 on day 1, price 110 on
# day 10, 5 more bought at 110 on day 10, price 121 on day 20.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Perf test', 'broker', 'EUR')")
    pid = conn.execute("SELECT id FROM accounts WHERE name = 'Perf test'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                 "VALUES (?, '2026-08-01', 'Buy', -1000, 'EUR', 'buy', 'XX0000007777', 'Test Fund', 10, 100, 'p1', 'manual')", (pid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                 "VALUES (?, '2026-08-10', 'Buy', -550, 'EUR', 'buy', 'XX0000007777', 'Test Fund', 5, 110, 'p2', 'manual')", (pid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, external_id, source) "
                 "VALUES (?, '2026-08-15', 'Dividend', 30, 'EUR', 'dividend', 'XX0000007777', 'Test Fund', 'p3', 'manual')", (pid,))
    for day, px in (("2026-08-01", 100), ("2026-08-10", 110), ("2026-08-20", 121)):
        conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('XX0000007777', ?, ?, 'EUR')", (day, px))
pf = performance.for_security("XX0000007777", today=date(2026, 8, 20))
# Day 10: 1 000 held, 550 added at the start of the day, 1 650 at its
# close — a gain of 100 on 1 550. Day 15: 30 paid out, 1 650 / 1 620.
# Day 20: 1 815 / 1 650. Chain-linked, as every tool does it.
check("the holding's TWR chains each day's gain over what was there after that day's flows",
      round(pf["twr"], 4), round(1650 / 1550 * 1650 / 1620 * 1.1 - 1, 4))
check("...and its MWR is positive and annualised", pf["mwr"] is not None and pf["mwr"] > 0, True)
check("...over the right span", (pf["since"], pf["days"]), ("2026-08-01", 19))
pa = performance.for_accounts("EUR", [pid], today=date(2026, 8, 20))
check("the account's securities as one investment agree with the single holding", round(pa["twr"], 4), round(pf["twr"], 4))
pa_ytd = performance.for_accounts("EUR", [pid], start=date(2026, 8, 10), today=date(2026, 8, 20))
check("a later start measures from what was held that day",
      pa_ytd["since"] == "2026-08-10" and pa_ytd["twr"] is not None and pa_ytd["twr"] < pf["twr"], True)
check("an account with no trades has nothing to say", performance.for_accounts("EUR", [account_id])["twr"], None)
r = c.get("/securities/XX0000007777")
check("the security page shows both returns", b"Return (TWR)" in r.data and b"Your money (MWR)" in r.data, True)
r = c.get("/portfolio")
check("the portfolio page has the return table and the columns",
      b"Time-weighted (TWR)" in r.data and b"Last twelve months" in r.data and b">TWR<" in r.data, True)
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "performance", "arguments": {}}}, headers=HDR)
out = r.get_json()["result"]["structuredContent"]
check("the MCP performance tool answers with the three periods and the holdings",
      ("all" in out and "ytd" in out and "1y" in out, "XX0000007777" in out["holdings"]), (True, True))
mcp.revoke()
c.post(f"/accounts/{pid}/delete", data={"confirm": "Perf test"})

# A position the rows do not add up to — a sale before its purchase —
# is worth less than nothing on some days. That is not a return, and it
# must not become a complex number that crashes the Portfolio page.
check("a chain with a negative value in it is no return",
      performance.twr([("2026-01-01", 100.0), ("2026-01-02", -20.0), ("2026-01-03", 110.0)], {}), None)
check("...and a total loss annualises to a total loss, not a complex number",
      performance.annualise(-1.5, 400), -1.0)
check("...while an ordinary loss still annualises", round(performance.annualise(-0.5, 365), 3), -0.5)

# ---------------------------------------------------------------------------
print("\n32. Realised gains, by lots")
# ---------------------------------------------------------------------------
from app import gains                                       # noqa: E402

# 10 at 100, 5 at 110, then 8 sold at 120 (960 in, 5 fee → 955 booked).
# FIFO: the 8 are the oldest — cost 800, gain 155. Average: 1 550 / 15
# = 103.33 each — cost 826.67, gain 128.33. Then 7 more sold at 130
# (910): FIFO 2 × 100 + 5 × 110 = 750, gain 160; average 723.33, 186.67.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Lots test', 'broker', 'EUR')")
    lid = conn.execute("SELECT id FROM accounts WHERE name = 'Lots test'").fetchone()["id"]
    for i, (day, kind, amt, q, px) in enumerate((
            ("2025-01-10", "buy", -1000, 10, 100), ("2025-06-10", "buy", -550, 5, 110),
            ("2025-09-01", "sell", 955, -8, 120), ("2026-02-01", "sell", 910, -7, 130))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                     "VALUES (?, ?, ?, ?, 'EUR', ?, 'XX0000008888', 'Lot Fund', ?, ?, ?, 'manual')",
                     (lid, day, kind.title(), amt, kind, q, px, f"l{i}"))
fifo = gains.realised("XX0000008888", [lid], "fifo")
check("FIFO sells the oldest units first",
      [(s_["cost"], s_["gain"]) for s_ in fifo["sales"]], [(800.0, 155.0), (750.0, 160.0)])
check("...and sums them by year and all time", (fifo["by_year"], fifo["total"]), ({"2025": 155.0, "2026": 160.0}, 315.0))
check("...leaving nothing held", (fifo["open_quantity"], fifo["open_cost"], fifo["avg_cost"]), (0, 0.0, None))
avg = gains.realised("XX0000008888", [lid], "average")
check("average cost sells every unit at the average paid",
      [(s_["cost"], s_["gain"]) for s_ in avg["sales"]], [(826.67, 128.33), (723.33, 186.67)])
check("the two methods realise the same total once everything is sold", avg["total"], fifo["total"])
check("the default method is FIFO", gains.method(), "fifo")

# A partial: hold 5 after the first sale under FIFO — 5 × 110.
with db.get_conn() as conn:
    conn.execute("DELETE FROM transactions WHERE external_id = 'l3' AND account_id = ?", (lid,))
part = gains.realised("XX0000008888", [lid], "fifo")
check("what is still held is the youngest lot under FIFO", (part["open_quantity"], part["open_cost"], round(part["avg_cost"], 2)), (7, 750.0, 107.14))
part_avg = gains.realised("XX0000008888", [lid], "average")
check("...and 7 at the average under average cost", (part_avg["open_quantity"], part_avg["open_cost"]), (7, 723.33))

# A transfer out carries lots away without realising; a transfer in at
# the row's price opens a lot; a second account keeps its own lots.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Lots test 2', 'broker', 'EUR')")
    lid2 = conn.execute("SELECT id FROM accounts WHERE name = 'Lots test 2'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2026-03-01', 'Out', 0, 'EUR', 'transfer', 'XX0000008888', -3, 130, 'l4', 'manual')", (lid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2026-03-01', 'In', 0, 'EUR', 'transfer', 'XX0000008888', 3, 130, 'l5', 'manual')", (lid2,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2026-04-01', 'Sell', 420, 'EUR', 'sell', 'XX0000008888', -3, 140, 'l6', 'manual')", (lid2,))
both = gains.realised("XX0000008888", [lid, lid2], "fifo")
check("a transfer realises nothing, and the receiving account's sale is against the transfer price",
      [(s_["account"], s_["cost"], s_["gain"]) for s_ in both["sales"]], [("Lots test", 800.0, 155.0), ("Lots test 2", 390.0, 30.0)])
check("...with the lots that stayed behind still held", (both["open_quantity"], both["open_cost"]), (4, 440.0))
summ = gains.summary([lid, lid2], "fifo")
check("the summary is per year and per currency",
      (summ["sales"], [(y["year"], y["amounts"]) for y in summ["by_year"]], summ["total"]),
      (2, [("2026", {"EUR": 30.0}), ("2025", {"EUR": 155.0})], {"EUR": 185.0}))
r = c.get("/securities/XX0000008888")
check("the security page lists the sales with their cost and gain",
      b"Realised gains" in r.data and b"Cost of those units" in r.data and b"realised" in r.data, True)
r = c.get("/portfolio")
check("the portfolio page has the realised-gains card and columns",
      b"Realised gains" in r.data and b">Unrealised<" in r.data and b">Realised<" in r.data, True)
r = c.post("/settings", data={"base_currency": "EUR", "gains_method": "average", "sync_time": "12:00"}, follow_redirects=True)
check("the method is a setting", (r.status_code, gains.method()), (200, "average"))
r = c.post("/settings", data={"base_currency": "EUR", "gains_method": "nonsense", "sync_time": "12:00"}, follow_redirects=True)
check("...that falls back to FIFO on nonsense", gains.method(), "fifo")
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "realised_gains", "arguments": {"isin": "XX0000008888", "method": "average"}}}, headers=HDR)
out = r.get_json()["result"]["structuredContent"]
check("the MCP tool answers per security under the asked method", (out["method"], len(out["sales"])), ("average", 2))
mcp.revoke()
c.post(f"/accounts/{lid}/delete", data={"confirm": "Lots test"})
c.post(f"/accounts/{lid2}/delete", data={"confirm": "Lots test 2"})

# ---------------------------------------------------------------------------
print("\n33. A CSV nobody knows, mapped by hand and remembered")
# ---------------------------------------------------------------------------
from app.importers import generic                           # noqa: E402

POSITIVE_BUYS_NOKIND = ("Datum,Betrag,ISIN,Anzahl\n2026-01-05,48.97,LU1681044563,5.2\n2026-02-05,50.36,LU1681044563,5.3\n")
BANK_CSV = (
    "Buchungsdatum;Umsatzart;Beschreibung;Soll;Haben;Währung;ISIN;Stück;Kurs\n"
    "03.02.2026;Kauf;Vanguard FTSE All-World;1.234,50;;EUR;IE00BK5BQT80;10;123,45\n"
    "10.02.2026;Dividende;Vanguard FTSE All-World;;12,30;EUR;IE00BK5BQT80;10;\n"
    "15.02.2026;Überweisung;Gehalt Februar;;2.500,00;EUR;;;\n"
    "20.02.2026;Verkauf;Vanguard FTSE All-World;;650,00;EUR;IE00BK5BQT80;5;130,00\n"
    "Summe;;;;;;;;\n"
)
check("the delimiter is read off the header", generic.detect_delimiter(BANK_CSV), ";")
hdr, body, delim = generic.read(BANK_CSV)
check("the header and the rows come apart", (len(hdr), len(body), delim), (9, 5, ";"))
check("a saved mapping is keyed on the header, whatever its case and spacing",
      generic.header_key(["Datum ", " BETRAG"]), generic.header_key(["datum", "betrag"]))
check("nothing is recognised before a mapping exists", importers.sniff(BANK_CSV.encode()), None)
check("...but it is a CSV a mapping could be drawn for", generic.is_csv(BANK_CSV.encode()), True)
check("a PDF is not", generic.is_csv(b"%PDF-1.4 whatever"), False)

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Mapped bank', 'broker', 'EUR')")
    mid = conn.execute("SELECT id FROM accounts WHERE name = 'Mapped bank'").fetchone()["id"]
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(BANK_CSV.encode()), "hausbank.csv")},
           content_type="multipart/form-data")
check("an unknown CSV is sent to the mapping page, not refused", (r.status_code, "/import/map/" in r.headers.get("Location", "")), (302, True))
map_url = r.headers["Location"]
r = c.get(map_url)
check("the page shows the file's columns and a first guess",
      (b"Buchungsdatum" in r.data, b'name="col_txn_date"' in r.data, b"Map the columns" in r.data), (True, True, True))
guess = main._guess_mapping(hdr)
check("the guess found the date, the two money columns, the ISIN and the units",
      (guess.get("txn_date"), guess.get("debit"), guess.get("credit"), guess.get("isin"), guess.get("quantity"), guess.get("kind")),
      ("Buchungsdatum", "Soll", "Haben", "ISIN", "Stück", "Umsatzart"))
check("...and did not pair a signed amount with a debit column",
      main._guess_mapping(["Datum", "Betrag", "Soll"]).get("debit"), None)

form = {"name": "Hausbank", "col_txn_date": "Buchungsdatum", "col_kind": "Umsatzart", "col_description": "Beschreibung",
        "col_debit": "Soll", "col_credit": "Haben", "col_currency": "Währung", "col_isin": "ISIN",
        "col_quantity": "Stück", "col_price": "Kurs", "action": "preview"}
r = c.post(map_url, data=form)
check("a preview reads the rows through the mapping without importing",
      (r.status_code, b"IE00BK5BQT80" in r.data, b"Gehalt Februar" in r.data), (200, True, True))
with db.get_conn() as conn:
    n = conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ?", (mid,)).fetchone()["n"]
check("...nothing imported yet", n, 0)
r = c.post(map_url, data={**form, "col_txn_date": "", "action": "import"})
check("a mapping without a date column is refused", b"least a mapping needs" in r.data, True)
r = c.post(map_url, data={**form, "action": "import"})
check("saving imports the file", (r.status_code, b"Hausbank" in r.data, b"4" in r.data), (200, True, True))
with db.get_conn() as conn:
    rows = [dict(x) for x in conn.execute(
        "SELECT txn_date, kind, amount, isin, quantity, price, source FROM transactions WHERE account_id = ? ORDER BY txn_date", (mid,)).fetchall()]
check("the summary line at the bottom, with no date, is left out", len(rows), 4)
check("debit and credit become a signed amount, European decimals read",
      [r_["amount"] for r_ in rows], [-1234.5, 12.3, 2500.0, 650.0])
check("the kind column's German words are understood", [r_["kind"] for r_ in rows], ["buy", "dividend", "transfer", "sell"])
check("the kind gives the units their sign, and a dividend's 'units held' are not units that arrived",
      [r_["quantity"] for r_ in rows], [10.0, None, None, -5.0])
check("the price is read, and the source names the mapping", (rows[0]["price"], rows[0]["source"].startswith("csv:")), (123.45, True))
check("the mapping is saved under the header", generic.find(hdr)["name"], "Hausbank")
check("...and the same file is now recognised like any other", importers.sniff(BANK_CSV.encode()).LABEL, "Hausbank")
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(BANK_CSV.encode()), "hausbank-again.csv")},
           content_type="multipart/form-data", follow_redirects=True)
check("re-importing goes straight through, and is harmless", b"Hausbank: 0 new, 4 already had" in r.data, True)
imps = importers.recent_imports(mid)
check("every file import is on record, with what it brought — the re-import brought nothing",
      [(i["filename"], i["inserted"], i["still"]) for i in imps], [("hausbank-again.csv", 0, 0), ("hausbank.csv", 4, 4)])
r = c.get(f"/accounts/{mid}")
check("the account page lists them with an Undo", (b"Recent imports" in r.data, b">Undo<" in r.data, b"and forget its mapping" in r.data), (True, True, True))
first = imps[-1]["id"]
r = c.post(f"/accounts/{mid}/imports/{first}/undo", data={}, follow_redirects=True)
with db.get_conn() as conn:
    left = conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ?", (mid,)).fetchone()["n"]
check("undo takes back every row that import brought, and only those", (b"Import undone" in r.data, b"4 rows removed" in r.data, left), (True, True, 0))
check("...the mapping stays unless asked", generic.find(hdr) is not None, True)
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(BANK_CSV.encode()), "hausbank.csv")},
           content_type="multipart/form-data", follow_redirects=True)
again = importers.recent_imports(mid)[0]
r = c.post(f"/accounts/{mid}/imports/{again['id']}/undo", data={"forget_mapping": "1"}, follow_redirects=True)
check("...and with the box ticked the mapping goes too", (b"Mapping forgotten" in r.data, generic.find(hdr)), (True, None))
r = c.post(f"/accounts/{mid}/imports/999999/undo", data={}, follow_redirects=True)
check("an import that is not on record is refused gently", b"not on record" in r.data, True)
# The mapping page warns when the signs look backwards.
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(POSITIVE_BUYS_NOKIND.encode()), "positive.csv")},
           content_type="multipart/form-data")
map_url2 = r.headers["Location"]
r = c.post(map_url2, data={"name": "Pos", "col_txn_date": "Datum", "col_amount": "Betrag", "col_isin": "ISIN", "col_quantity": "Anzahl", "action": "preview"})
check("the mapping page says how signs are read, and warns when the first rows look backwards",
      (b"Signs." in r.data, b"look like purchases with money coming in" in r.data or b"looks like a purchase with money coming in" in r.data), (True, True))
# The saved mapping for BANK_CSV is gone; put it back for what follows.
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(BANK_CSV.encode()), "hausbank.csv")}, content_type="multipart/form-data")
c.post(r.headers["Location"], data={**form, "action": "import"})
# One more row: a second export that overlaps.
more = BANK_CSV.replace("Summe;;;;;;;;\n", "25.02.2026;Gebühr;Depotgebühr;5,00;;EUR;;;\nSumme;;;;;;;;\n")
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(more.encode()), "hausbank-march.csv")},
           content_type="multipart/form-data", follow_redirects=True)
check("the next export from the same bank imports the new row only", b"Hausbank: 1 new, 4 already had" in r.data, True)
with db.get_conn() as conn:
    fee_kind = conn.execute("SELECT kind, amount FROM transactions WHERE account_id = ? AND txn_date = '2025-02-25' OR (account_id = ? AND description = 'Depotgebühr')", (mid, mid)).fetchone()
check("...as a fee, money out", (fee_kind["kind"], fee_kind["amount"]), ("fee", -5.0))
check("a holding follows from the mapped trades",
      [(h["isin"], h["quantity"]) for h in importers.positions(mid)], [("IE00BK5BQT80", 5.0)])
check("the kind is worked out when the file has no column for it",
      (generic._kind("", "IE00BK5BQT80", 3, -300.0), generic._kind("", "IE00BK5BQT80", 3, 300.0),
       generic._kind("", "IE00BK5BQT80", None, 12.0), generic._kind("", None, None, 100.0), generic._kind("", None, None, -100.0)),
      ("buy", "sell", "dividend", "deposit", "withdrawal"))
check("a signed amount column with the signs the wrong way round can be flipped",
      [t.amount for t in generic.parse_with({"txn_date": "d", "amount": "a", "negate": True}, "d,a\n2026-01-01,50\n").rows], [-50.0])
check("no currency column: the account's, or the one the mapping fixes",
      ([t.currency for t in generic.parse_with({"txn_date": "d", "amount": "a"}, "d,a\n2026-01-01,5\n", "CHF").rows],
       [t.currency for t in generic.parse_with({"txn_date": "d", "amount": "a", "currency_fixed": "USD"}, "d,a\n2026-01-01,5\n", "CHF").rows]),
      (["CHF"], ["USD"]))
check("an ISIN in the description is found when no column carries one",
      generic.parse_with({"txn_date": "d", "amount": "a", "description": "t"}, "d,a,t\n2026-01-01,-5,Kauf IE00BK5BQT80 Vanguard\n").rows[0].isin, "IE00BK5BQT80")
r = c.get("/settings/banks")
check("Settings lists the mapping", (b"CSV mappings" in r.data, b"Hausbank" in r.data), (True, True))
r = c.post("/settings", data={"form": "csv_mapping_delete", "mapping_id": generic.find(hdr)["id"]}, follow_redirects=True)
check("...and forgets it on request", (b"Mapping forgotten" in r.data, generic.find(hdr)), (True, None))
check("an expired token is refused, not a crash",
      c.get(f"/accounts/{mid}/import/map/nonsense").status_code, 302)

# The app's own template: a header of the field names needs no mapping.
NATIVE_CSV = (
    "date,amount,currency,description,counterparty,kind,isin,security_name,quantity,price,fee,tax,id\n"
    "2026-03-01,-1250.00,EUR,Rent March,Landlord Ltd,,,,,,,,r-1\n"
    "2026-03-02,-482.10,EUR,Bought 4 x World ETF,,buy,IE00BK5BQT80,Vanguard FTSE All-World,4,120.10,1.70,,r-2\n"
    "2026-03-05,2900.00,EUR,Salary,Employer AG,deposit,,,,,,,r-3\n"
    "2026-03-08,12.40,EUR,Dividend,,dividend,IE00BK5BQT80,Vanguard FTSE All-World,,,,1.85,r-4\n")
check("the template header is recognised without a mapping",
      importers.sniff(NATIVE_CSV.encode()).LABEL, "Wealth Dashboard CSV")
check("...in any order and any subset with a date and an amount",
      generic.native(["Amount", "Date"]) is not None, True)
check("...but not without an amount", generic.native(["date", "description"]), None)
check("...and not when a column is not one of ours", generic.native(["date", "amount", "vibes"]), None)
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(NATIVE_CSV.encode()), "mine.csv")},
           content_type="multipart/form-data", follow_redirects=True)
check("a template file imports straight away", b"4 new" in r.data, True)
with db.get_conn() as conn:
    rows = {r["description"]: dict(r) for r in conn.execute(
        "SELECT * FROM transactions WHERE account_id = ? AND source LIKE 'csv:%'", (mid,))}
check("the buy carries units, price, fee and ISIN",
      (rows["Bought 4 x World ETF"]["quantity"], rows["Bought 4 x World ETF"]["price"],
       rows["Bought 4 x World ETF"]["fee"], rows["Bought 4 x World ETF"]["isin"]),
      (4.0, 120.1, 1.7, "IE00BK5BQT80"))
check("the dividend carries its tax", rows["Dividend"]["tax"], 1.85)
check("a kind the file names is kept", rows["Salary"]["kind"], "deposit")
check("a row with no kind is worked out", rows["Rent March"]["kind"], "withdrawal")
check("the file's own id is the row's id",
      rows["Rent March"]["external_id"] == rows["Rent March"]["external_id"] and
      all(v["external_id"].startswith("csv:") for v in rows.values()), True)
edited = NATIVE_CSV.replace("Rent March", "Rent March (corrected)")
r = c.post(f"/accounts/{mid}/import", data={"file": (io.BytesIO(edited.encode()), "mine2.csv")},
           content_type="multipart/form-data", follow_redirects=True)
check("re-exporting after an edit adds nothing — the id says it is the same row",
      b"0 new, 4 already had" in r.data, True)
check("a saved mapping for a header that uses our words still wins over the template",
      generic.find(["date", "amount"])["id"], 0)
c.post(f"/accounts/{mid}/delete", data={"confirm": "Mapped bank"})

# ---------------------------------------------------------------------------
print("\n34. CSV out, filtered as the page is")
# ---------------------------------------------------------------------------
from app import export                                      # noqa: E402

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Export test', 'broker', 'EUR')")
    xid = conn.execute("SELECT id FROM accounts WHERE name = 'Export test'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, amount, currency, kind, isin, security_name, quantity, price, external_id, source, category) "
                 "VALUES (?, '2026-03-03', 'Buy; with a semicolon', 'Broker \"X\"', -1234.5, 'EUR', 'buy', 'XX0000009999', 'Export Fund', 10, 123.45, 'x1', 'manual', 'investing')", (xid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, external_id, source) "
                 "VALUES (?, '2026-03-04', 'Coffee', -3.2, 'EUR', 'withdrawal', 'x2', 'manual')", (xid,))
r = c.get("/transactions.csv", query_string={"account": xid})
check("the transactions export is a CSV attachment",
      (r.status_code, r.mimetype, "attachment" in r.headers.get("Content-Disposition", "")), (200, "text/csv", True))
body = r.data.decode("utf-8")
check("...with a byte-order mark for Excel and CRLF lines", (body.startswith("﻿"), "\r\n" in body), (True, True))
lines = body.lstrip("﻿").splitlines()
check("...a header, and the rows the filter matched", (lines[0].startswith("date,account,kind"), len(lines)), (True, 3))
check("...English: comma and a decimal point, ISO dates, quoted where needed",
      lines[1].startswith('2026-03-04,Export test,withdrawal,Coffee,,-3.20,EUR'), True)
check("a semicolon in a description and quotes in a counterparty survive",
      'Buy; with a semicolon' in lines[2] and '"Broker ""X"""' in lines[2], True)
r = c.get("/transactions.csv", query_string={"account": xid, "kind": "buy"})
check("the page's filters apply — a kind narrows it", len(r.data.decode().splitlines()), 2)
r = c.get("/transactions.csv", query_string={"account": xid, "q": "coffee"})
check("...and so does the search", b"Coffee" in r.data and b"semicolon" not in r.data, True)
r = c.get("/transactions.csv", query_string={"account": xid, "sep": ";"})
check("a semicolon file has a decimal comma", b";-3,20;EUR;" in r.data, True)
r = c.get("/transactions.csv", query_string={"account": xid}, headers={"Accept-Language": "de"})
check("a German reader gets the semicolon file without asking", b";-3,20;EUR;" in r.data, True)
r = c.get(f"/accounts/{xid}/transactions.csv")
check("an account exports its own rows, named after itself",
      (len(r.data.decode().splitlines()), "export-test-" in r.headers["Content-Disposition"]), (3, True))
r = c.get("/securities/XX0000009999.csv")
check("a security exports the rows behind it", (len(r.data.decode().splitlines()), b"Export Fund" in r.data), (2, True))
r = c.get("/portfolio.csv")
hl = r.data.decode().lstrip("﻿").splitlines()
check("the holdings export has the page's columns",
      hl[0], "isin,name,accounts,quantity,price,price_as_of,currency,net_invested,value,unrealised,realised,twr,twr_annual,mwr")
row = next((l for l in hl if l.startswith("XX0000009999")), "")
check("...and the holding with its figures", row.startswith("XX0000009999,Export Fund,Export test,10,123.45,,EUR,1234.50,1234.50,"), True)
check("the pages link to their export",
      (b"Export as CSV" in c.get("/transactions").data, b"Export as CSV" in c.get("/portfolio").data,
       b"Export as CSV" in c.get(f"/accounts/{xid}").data, b"Export as CSV" in c.get("/securities/XX0000009999").data),
      (True, True, True, True))
check("numbers are written plainly, not in scientific notation",
      (export._num(0.000001, "."), export._num(1234567.0, "."), export._num(None, ".")), ("0.000001", "1234567", ""))
c.post(f"/accounts/{xid}/delete", data={"confirm": "Export test"})

# ---------------------------------------------------------------------------
print("\n35. A stock split, recorded once")
# ---------------------------------------------------------------------------
from app import splits                                      # noqa: E402

check("a ratio is new for old", (splits.parse_ratio("44:1"), splits.parse_ratio("44"), splits.parse_ratio("1:10"), splits.parse_ratio(" 2 / 1 ")),
      ((44.0, 1.0), (44.0, 1.0), (1.0, 10.0), (2.0, 1.0)))
for bad in ("", "0", "1:1", "abc", "-2:1"):
    try:
        splits.parse_ratio(bad); check(f"ratio {bad!r} is refused", False, True)
    except ValueError:
        check(f"ratio {bad!r} is refused", True, True)

# The case from a DKB Depot: a savings plan into an ETF at ~420, a 44:1
# split, then the same plan at ~9.5. Three buys of 0.5 before, two of
# 21.5 after — a running sum of 44.5 units, when 1.5 × 44 + 43 = 109
# are held.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Split test', 'broker', 'EUR')")
    sid = conn.execute("SELECT id FROM accounts WHERE name = 'Split test'").fetchone()["id"]
    for i, (day, q, px) in enumerate((("2022-04-20", 0.5, 400.0), ("2022-06-20", 0.5, 400.0), ("2022-08-22", 0.5, 400.0),
                                      ("2022-10-20", 21.5, 9.3), ("2022-12-20", 21.5, 9.3))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                     "VALUES (?, ?, 'Kauf AIS-AMUNDI MSCI SWITZERLAND', ?, 'EUR', 'buy', 'LU1681044563', 'Amundi MSCI Switzerland', ?, ?, ?, 'dkb_pdf')",
                     (sid, day, -q * px, q, px, f"s{i}"))
    for day, px in (("2022-04-20", 9.09), ("2022-09-15", 9.5), ("2022-10-20", 9.3), ("2023-01-10", 10.0)):
        conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('LU1681044563', ?, ?, 'EUR')", (day, px))
check("before the split is recorded the units are simply summed", round(importers.positions(sid)[0]["quantity"], 4), 44.5)

r = c.post("/securities/LU1681044563/split", data={"txn_date": "2022-09-30", "ratio": "44:1"}, follow_redirects=True)
check("the split is recorded from the security page", b"Split recorded on 1 account" in r.data, True)
with db.get_conn() as conn:
    row = conn.execute("SELECT * FROM transactions WHERE account_id = ? AND kind = 'split'", (sid,)).fetchone()
check("...as one row: the units that appeared, at no cost, on the day",
      (row["txn_date"], round(row["quantity"], 4), row["amount"], row["price"], row["description"]), ("2022-09-30", 64.5, 0.0, None, "Split 44:1"))
check("the holding is now right", round(importers.positions(sid)[0]["quantity"], 4), 109.0)
r = c.post("/securities/LU1681044563/split", data={"txn_date": "2022-09-30", "ratio": "44:1"}, follow_redirects=True)
check("recording it twice does nothing", b"already recorded" in r.data, True)
with db.get_conn() as conn:
    check("...really nothing", conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ? AND kind = 'split'", (sid,)).fetchone()["n"], 1)
r = c.post("/securities/LU1681044563/split", data={"txn_date": "2022-09-30", "ratio": "banana"}, follow_redirects=True)
check("a ratio that is not one is refused in a sentence", b"like 44:1" in r.data, True)

ser = prices.series_for("LU1681044563", [sid], today=date(2023, 1, 15))
pts = {p["date"]: p for p in ser["points"]}
check("before the split, the chart values the units held then in today's units — Yahoo's history is split-adjusted",
      round(pts["2022-09-20"]["value"], 2), round(1.5 * 44 * 9.5, 2))
check("...and after it, the units as they are", round(pts["2023-01-12"]["value"], 2), round(109.0 * 10.0, 2))
check("...while the quantity shown is the raw running sum", (pts["2022-09-20"]["quantity"], pts["2022-10-01"]["quantity"]), (1.5, 66.0))
check("net invested does not change: nothing was paid", round(pts["2023-01-12"]["invested"], 2), round(3 * 200 + 2 * 21.5 * 9.3, 2))
v = history.Valuer("EUR", [sid])
check("the net-worth history agrees", (round(v.value_on("2022-09-20")[1], 2), round(v.value_on("2023-01-12")[1], 2)),
      (round(1.5 * 44 * 9.5, 2), round(109.0 * 10.0, 2)))
check("split factors: every row before the split, scaled; the split and after, not",
      splits.factors([{"kind": "buy", "quantity": 1}, {"kind": "buy", "quantity": 1}, {"kind": "split", "quantity": 86}, {"kind": "buy", "quantity": 5}]),
      [44.0, 44.0, 1.0, 1.0])
check("a reverse split scales down", splits.factors([{"kind": "buy", "quantity": 100}, {"kind": "split", "quantity": -90}]), [0.1, 1.0])

# Sell 50 of the new units at 10: FIFO takes 22 (the first 0.5 old lot,
# now 22 units, cost 200) + 22 (cost 200) + 6 of the third (cost 6/22
# × 200 = 54.55): cost 454.55, gain 45.45. Nothing about the split is
# a gain.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2023-01-12', 'Verkauf', 500, 'EUR', 'sell', 'LU1681044563', -50, 10, 's9', 'manual')", (sid,))
g = gains.realised("LU1681044563", [sid], "fifo")
check("a lot keeps its cost through a split, so FIFO realises against the old money", (g["sales"][0]["cost"], g["sales"][0]["gain"]), (454.55, 45.45))
check("...and the units still held cost the rest", (round(g["open_quantity"], 4), g["open_cost"]), (59.0, round(600 + 2 * 21.5 * 9.3 - 454.55, 2)))
ga = gains.realised("LU1681044563", [sid], "average")
check("average cost: 999.9 over 109 units, 50 sold", (ga["sales"][0]["cost"], ga["sales"][0]["gain"]), (round(999.9 / 109 * 50, 2), round(500 - 999.9 / 109 * 50, 2)))
r = c.get("/securities/LU1681044563")
check("the security page shows the split row and the form", (b"is-split" in r.data, b"Record a split" in r.data), (True, True))
r = c.post(f"/transactions/{row['id']}/edit", data={"txn_date": "2022-09-30", "kind": "split", "quantity": "64.5", "amount": "0", "direction": "in", "quantity_direction": "in", "back": "/securities/LU1681044563"}, follow_redirects=True)
check("the split row can be corrected like any other", r.status_code, 200)
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "record_split", "arguments": {"isin": "LU1681044563", "date": "2023-01-13", "ratio": "2:1"}}}, headers=HDR)
out = r.get_json()["result"]["structuredContent"]
check("the MCP tool records a split too", (len(out["written"]), round(out["written"][0]["quantity"], 4)), (1, 59.0))
mcp.revoke()

# ---------------------------------------------------------------------------
print("\n35b. A transaction added where the holding is looked at")
# ---------------------------------------------------------------------------
# The ISIN and the name are the page's: a buy is an account, a date and
# two numbers, as recording a split is — not a trip to the account's
# add page with the ISIN typed by hand.
r = c.get("/securities/LU1681044563")
check("the holding page offers to add a transaction", b"Add a transaction" in r.data, True)
check("...on the account that holds it", f'<option value="{sid}"'.encode() in r.data, True)
r = c.post("/securities/LU1681044563/add", data={"account_id": sid, "kind": "buy", "txn_date": "2023-02-01",
                                                 "quantity": "10", "price": "10.5", "fee": "1"}, follow_redirects=True)
check("a buy is added", b"Added." in r.data, True)
with db.get_conn() as conn:
    row = conn.execute("SELECT * FROM transactions WHERE account_id = ? AND txn_date = '2023-02-01'", (sid,)).fetchone()
check("...with the page's ISIN and name", (row["isin"], row["security_name"]), ("LU1681044563", "Amundi MSCI Switzerland"))
check("...the quantity, the price and the total", (row["quantity"], row["price"], row["amount"]), (10.0, 10.5, -106.0))
check("...as a row typed in by hand", row["source"], "manual")

r = c.post("/securities/LU1681044563/add", data={"account_id": sid, "kind": "dividend", "txn_date": "2023-02-10",
                                                 "amount": "12.5"}, follow_redirects=True)
with db.get_conn() as conn:
    div = conn.execute("SELECT * FROM transactions WHERE account_id = ? AND kind = 'dividend'", (sid,)).fetchone()
check("a dividend is filed against the holding", (div["isin"], div["amount"], div["quantity"]), ("LU1681044563", 12.5, None))
check("...says which holding", "Amundi MSCI Switzerland" in div["description"], True)
check("...and is income of its kind", div["category"], "capital_income")
r = c.get("/securities/LU1681044563")
check("...so the holding page shows it in its income", b"12.50" in r.data, True)

r = c.post("/securities/LU1681044563/add", data={"account_id": sid, "kind": "buy", "txn_date": "2023-02-01",
                                                 "quantity": "banana", "price": "10.5"})
check("a mistake brings the page back with the sentence", (r.status_code, b"needs a quantity and a price" in r.data), (200, True))
check("...and the form as typed", b'value="banana"' in r.data, True)
r = c.post("/securities/LU1681044563/add", data={"account_id": "999999", "kind": "buy", "txn_date": "2023-02-01",
                                                 "quantity": "1", "price": "1"}, follow_redirects=True)
check("an account that is not there is refused", b"Pick which account" in r.data, True)

# The general add page files a dividend against a holding too, when an
# ISIN is given — and stays a plain dividend when none is.
r = c.post(f"/accounts/{sid}/add", data={"kind": "dividend", "txn_date": "2023-03-01", "amount": "3",
                                         "isin": "lu1681044563"}, follow_redirects=True)
r = c.post(f"/accounts/{sid}/add", data={"kind": "dividend", "txn_date": "2023-03-02", "amount": "4"}, follow_redirects=True)
with db.get_conn() as conn:
    divs = {r_["txn_date"]: r_["isin"] for r_ in conn.execute(
        "SELECT txn_date, isin FROM transactions WHERE account_id = ? AND kind = 'dividend'", (sid,))}
check("the add page files a dividend against the ISIN typed", divs["2023-03-01"], "LU1681044563")
check("...and against nothing when none is", divs["2023-03-02"], None)
c.post(f"/accounts/{sid}/delete", data={"confirm": "Split test"})

# ---------------------------------------------------------------------------
print("\n36. The shell: a sidebar in groups")
# ---------------------------------------------------------------------------
r = c.get("/portfolio")
body = r.data.decode()
check("the navigation is a sidebar with the pages in groups",
      ('class="sidenav"' in body, 'data-group="invest"' in body, 'data-group="money"' in body, 'data-group="plan"' in body), (True, True, True, True))
check("the group holding the current page starts open, and the page is marked",
      ('nav-group is-open holds-active" data-group="invest"' in body, 'navlink active" href="/portfolio"' in body), (True, True))
check("...and the other groups start closed", 'is-open holds-active" data-group="money"' in body, False)
check("every page is reachable from it", all(f'href="{p}"' in body for p in ("/", "/portfolio", "/crypto", "/screener", "/cashflow", "/budget", "/subscriptions", "/transactions", "/categorize", "/forecast", "/stages", "/loans", "/accounts", "/settings", "/logout")), True)
check("each entry has an icon and a label that can fold away",
      (body.count('<svg class="ico"') >= 18, body.count('class="nav-text"') >= 15), (True, True))
check("the collapse and the phone drawer have their controls",
      ('id="nav-collapse"' in body, 'id="nav-open"' in body, 'id="nav-scrim"' in body), (True, True, True))
check("the version sits in the sidebar's foot", 'class="version-badge"' in body and __version__ in body, True)
r = c.get("/login")
check("signed out, there is no sidebar", b'class="sidenav"' in c.get("/logout", follow_redirects=True).data, False)
c.post("/login", data={"username": "alex", "password": "a-good-password"})

# The collapsed sidebar: the group holding the current page is "open",
# and the wide sidebar's rule for an open group outranks the collapsed
# sidebar's "hidden" — so without a rule of its own the flyout of the
# page you are on never goes away. Pinned by the order of the rules.
css_ = pathlib.Path("app/static/css/app.css").read_text()
i_open = css_.index(".nav-group.is-open > .nav-group-items { display: block; }")
i_hide = css_.index("html.nav-collapsed .nav-group.is-open > .nav-group-items { display: none; }")
i_fly = css_.index("html.nav-collapsed .nav-group.is-flyout > .nav-group-items { display: block; }")
check("collapsed, an open group's items are hidden — after the wide rule, before the flyout rule",
      i_open < i_hide < i_fly, True)
check("...and hover opens a flyout only where hovering exists",
      "@media (hover: hover) { html.nav-collapsed .nav-group:hover > .nav-group-items { display: block; } }" in css_, True)

# ---------------------------------------------------------------------------
print("\n37. The three stages")
# ---------------------------------------------------------------------------
from app import stages                                      # noqa: E402

check("the borders: under a half is stage 1, up to two is stage 2, beyond is stage 3",
      [stages.stage_of(x) for x in (0.0, 0.49, 0.5, 1.0, 2.0, 2.01, 10.0)], [1, 1, 2, 2, 2, 3, 3])
check("no ratio, no stage", stages.stage_of(None), None)
check("the crossover: twelve months' saving over the rate — 500 a month at 6 % is 100 000",
      stages.crossover_wealth(500, 6.0), 100000.0)
check("...and none without a rate or without saving", (stages.crossover_wealth(500, 0), stages.crossover_wealth(0, 6)), (None, None))
p = stages.path(0.0, 500.0, 6.0, first_year=2026)
check("from nothing, the first year is stage 1", (p["years"][0]["stage"], p["stage"]), (1, 1))
check("...the path runs until compounding has led for five years", p["years"][-1]["stage"] == 3 and len(p["years"]) >= 10, True)
check("...the milestones come in order", (p["milestones"]["half"]["n"] < p["milestones"]["equal"]["n"] < p["milestones"]["double"]["n"]), True)
eq = p["milestones"]["equal"]
check("...and the crossover year opens with about the crossover wealth — the first whole year whose returns match the savings",
      0.9 * 100000 < eq["value"] < 1.1 * 100000, True)
check("a year's returns plus what went in is the closing value",
      all(abs(y["opening"] + y["put_in"] + y["returns"] - y["closing"]) < 0.01 for y in p["years"]), True)
big = stages.path(1000000.0, 500.0, 6.0)
check("a million at 6 % against 6 000 a year is stage 3 now", (big["stage"], round(big["ratio"], 1)), (3, 10.0))
none = stages.path(50000.0, 0.0, 6.0)
check("nothing going in is stage 3 by definition", (none["stage"], none["ratio"], none["crossover"]), (3, None, None))
check("no securities and nothing going in is no stage", stages.path(0.0, 0.0, 6.0)["stage"], None)

# As it went: 10 bought at 100 in January, price 110 in December, 5 EUR dividend.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Stage test', 'broker', 'EUR')")
    tid = conn.execute("SELECT id FROM accounts WHERE name = 'Stage test'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2025-01-15', 'Buy', -1000, 'EUR', 'buy', 'XX0000006666', 10, 100, 'st1', 'manual')", (tid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, external_id, source) "
                 "VALUES (?, '2025-06-15', 'Dividend', 5, 'EUR', 'dividend', 'XX0000006666', 'st2', 'manual')", (tid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                 "VALUES (?, '2026-02-01', 'Buy', -1200, 'EUR', 'buy', 'XX0000006666', 10, 120, 'st3', 'manual')", (tid,))
    for day, px in (("2025-01-15", 100), ("2025-12-31", 110), ("2026-02-01", 120), ("2026-06-01", 125)):
        conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('XX0000006666', ?, ?, 'EUR')", (day, px))
went = stages.as_it_went("EUR", [tid], today=date(2026, 7, 1))
check("2025 as it went: 1 000 in, worth 1 100 at the end, 5 paid out — the market did 105",
      [(y["year"], round(y["opening"]), round(y["put_in"]), round(y["income"]), round(y["returns"]), round(y["closing"])) for y in went][0],
      (2025, 0, 1000, 5, 105, 1100))
check("2026 so far: opened at 1 100, 1 200 in, worth 2 500 — the market did 200",
      [(y["year"], round(y["opening"]), round(y["put_in"]), round(y["returns"]), round(y["closing"]), y["partial"]) for y in went][1],
      (2026, 1100, 1200, 200, 2500, True))
check("...with a ratio and a stage per year", [(round(y["ratio"], 3), y["stage"]) for y in went], [(0.105, 1), (0.167, 1)])
check("what actually went in a month, over the last twelve months", round(stages.actual_monthly(went)), round((1200 + 1000 * (365 - went[-1]["days"]) / went[-2]["days"]) / 12))
check("nothing recorded, nothing to say", stages.as_it_went("EUR", [account_id]), [])
r = c.get("/stages")
check("the page renders with the stage, the crossover and both tables",
      (r.status_code, b"Where you stand" in r.data, b"Crossover" in r.data, b"As it went" in r.data, b"On the plan" in r.data), (200, True, True, True, True))
r = c.get("/stages", query_string={"monthly": "1000", "rate": "7"})
check("a monthly amount and a rate can be tried without being kept", (b"Tried, not kept" in r.data, b'value="1000"' in r.data), (True, True))
c.post(f"/accounts/{tid}/delete", data={"confirm": "Stage test"})

# ---------------------------------------------------------------------------
print("\n38. A kind column supplies the sign; corrections over the MCP")
# ---------------------------------------------------------------------------
# The case that came back from a real import: a bank that writes the
# amount of a purchase as a positive figure. "Kauf" says which way the
# money went, so the sign follows the kind — as it does when typed in.
POSITIVE_BUYS = ("Datum,Art,Betrag,ISIN,Anzahl,Kurs\n"
                 "2026-01-05,Kauf,48.97,LU1681044563,5.2,9.41\n"
                 "2026-02-05,Kauf,50.36,LU1681044563,5.3,9.50\n"
                 "2026-02-20,Dividende,-3.10,LU1681044563,,\n"
                 "2026-03-05,Verkauf,-70.00,LU1681044563,7,10.0\n"
                 "2026-03-06,,-20.00,,,\n")
mapping = {"txn_date": "Datum", "kind": "Art", "amount": "Betrag", "isin": "ISIN", "quantity": "Anzahl", "price": "Kurs"}
got = [(t.kind, t.amount, t.quantity) for t in generic.parse_with(mapping, POSITIVE_BUYS).rows]
check("a named kind supplies the sign whatever the file wrote; a kind worked out keeps the file's sign",
      got, [("buy", -48.97, 5.2), ("buy", -50.36, 5.3), ("dividend", 3.1, None), ("sell", 70.0, -7.0), ("withdrawal", -20.0, None)])

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Patch test', 'broker', 'EUR')")
    pid2 = conn.execute("SELECT id FROM accounts WHERE name = 'Patch test'").fetchone()["id"]
    ids = []
    for i in range(3):
        cur = conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id, source) "
                           "VALUES (?, ?, 'Kauf Amundi', 48.97, 'EUR', 'buy', 'LU1681044563', 5.2, 9.41, ?, 'csv:1')", (pid2, f"2026-0{i + 1}-05", f"pt{i}"))
        ids.append(int(cur.lastrowid))
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
def call(name, **args):
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}, headers=HDR)
    return r.get_json()["result"]
out = call("update_transactions", txn_ids=ids, negate_amount=True)
check("many rows corrected at once — the sign flipped on each",
      (out["structuredContent"]["changed"], [t["amount"] for t in out["structuredContent"]["transactions"]]), (3, [-48.97, -48.97, -48.97]))
out = call("update_transaction", txn_id=ids[0], price=9.5, description="Kauf Amundi, corrected")
check("one row, only the fields given", (out["structuredContent"]["price"], out["structuredContent"]["description"], out["structuredContent"]["amount"]), (9.5, "Kauf Amundi, corrected", -48.97))
with db.get_conn() as conn:
    row = conn.execute("SELECT edited_at, quantity FROM transactions WHERE id = ?", (ids[0],)).fetchone()
check("...marked as corrected, the rest untouched", (row["edited_at"] is not None, row["quantity"]), (True, 5.2))
out = call("update_transaction", txn_id=ids[1], kind="sell")
check("a kind change goes through the known kinds", out["structuredContent"]["kind"], "sell")
out = call("update_transaction", txn_id=ids[1], kind="banana")
check("...and an unknown kind is refused in a sentence", out.get("isError"), True)
out = call("update_transaction", txn_id=999999, amount=1)
check("a row that does not exist is refused", out.get("isError"), True)
out = call("update_transaction", txn_id=ids[2], txn_date="2099-01-01")
check("a date in the future is refused", out.get("isError"), True)
out = call("delete_transactions", txn_ids=[ids[2]])
check("rows can be deleted by id, imported or not", out["structuredContent"]["deleted"], 1)
with db.get_conn() as conn:
    check("...really gone", conn.execute("SELECT COUNT(*) n FROM transactions WHERE account_id = ?", (pid2,)).fetchone()["n"], 2)
mcp.revoke()
c.post(f"/accounts/{pid2}/delete", data={"confirm": "Patch test"})

# ---------------------------------------------------------------------------
print("\n39. A share paid for in euros and quoted in dollars")
# ---------------------------------------------------------------------------
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('USD test', 'broker', 'EUR')")
    uid = conn.execute("SELECT id FROM accounts WHERE name = 'USD test'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                 "VALUES (?, '2026-01-10', 'Kauf Amazon', -1000, 'EUR', 'buy', 'US0231351067', 'Amazon', 10, 100, 'u1', 'manual')", (uid,))
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('US0231351067', '2026-02-01', 120, 'USD')")
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('US0231351067', '2026-03-01', 132, 'USD')")
    conn.execute("INSERT OR REPLACE INTO fx_rates (as_of, currency, per_eur) VALUES ('2026-01-31', 'USD', 1.2)")
    conn.execute("INSERT OR REPLACE INTO fx_rates (as_of, currency, per_eur) VALUES ('2026-02-28', 'USD', 1.1)")
conv = prices.in_currency("EUR")
check("a dollar price becomes euros at the day's rate", (round(conv(120, "USD", "2026-02-01"), 6), round(conv(132, "USD", "2026-03-01"), 6), conv(50, "EUR", "2026-02-01")), (100.0, 120.0, 50))
check("...a day before every rate on record takes the oldest one, and an unknown currency nothing",
      (conv(120, "USD", "2025-01-01"), conv(120, "XXX", "2026-02-01")), (100.0, None))
ser = prices.series_for("US0231351067", [uid], today=date(2026, 3, 5))
pts = {p["date"]: p for p in ser["points"]}
check("the series is in the currency the shares were paid in",
      (ser["currency"], round(pts["2026-02-10"]["value"]), round(pts["2026-03-02"]["value"]), round(pts["2026-03-02"]["invested"])), ("EUR", 1000, 1200, 1000))
r = c.get("/securities/US0231351067")
check("the page values the holding in euros and says what the quote was",
      ("1,200.00\u00a0EUR" in r.data.decode(), b"quoted 132 USD" in r.data, b"USD unrealised" not in r.data), (True, True, True))
check("the Overview's holdings link to the security's page", b'href="/securities/US0231351067"' in c.get("/").data, True)
r = c.get("/securities/US0231351067", query_string={"ccy": "USD"})
check("...and can be shown in the currency it is quoted in instead",
      (b"Show in" in r.data, "1,320.00\u00a0USD" in r.data.decode(), b"quoted 132 USD" in r.data), (True, True, False))
ser_usd = prices.series_for("US0231351067", [uid], today=date(2026, 3, 5), currency="USD")
pts = {p["date"]: p for p in ser_usd["points"]}
check("the series in dollars: the buy turned at its day's rate — the oldest on record, until the history arrives — the price as quoted",
      (ser_usd["currency"], ser_usd["trade_currency"], round(pts["2026-03-02"]["value"]), round(pts["2026-03-02"]["invested"])), ("USD", "EUR", 1320, 1200))
check("a row older than the oldest rate asks for the ECB's whole history, once",
      (fx.needs_backfill(), db.get_state(fx.BACKFILLED)), (True, None))
_fetch, fx.fetch = fx.fetch, lambda url=None: ECB_XML         # no network in a test
try:
    fx.backfill()
finally:
    fx.fetch = _fetch
check("...and having fetched it, does not ask again", fx.needs_backfill(), False)
check("an unknown currency falls back to the one paid in", b'class="period-btn active" href="/securities/US0231351067"' in c.get("/securities/US0231351067", query_string={"ccy": "XXX"}).data, True)
c.post(f"/accounts/{uid}/delete", data={"confirm": "USD test"})

# ---------------------------------------------------------------------------
print("\n40. Settings in chapters; rules with terms")
# ---------------------------------------------------------------------------
r = c.get("/settings")
check("the settings open on General, with the chapters as tabs",
      (b'class="subnav"' in r.data, b'id="general"' in r.data, b'id="mcp"' in r.data, b'id="saxo"' in r.data), (True, True, False, False))
for sec, card in (("banks", b'id="saxo"'), ("market", b'id="prices"'), ("categories", b'id="categories"'), ("people", b'id="people"'), ("assistants", b'id="mcp"')):
    r = c.get(f"/settings/{sec}")
    check(f"the {sec} chapter holds its cards", (r.status_code, card in r.data, b'id="general"' in r.data), (200, True, False))
check("a chapter that does not exist goes to General", c.get("/settings/nonsense").status_code, 302)
r = c.post("/settings", data={"form": "fx_refresh"})
check("a form returns to its own chapter", r.headers["Location"].endswith("/settings/market#rates"), True)

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Rules test', 'current', 'EUR')")
    rid = conn.execute("SELECT id FROM accounts WHERE name = 'Rules test'").fetchone()["id"]
    for i, (desc, cp, amt) in enumerate((("Amazon order 1", "AMAZON EU", -30), ("Amazon order 2", "AMAZON EU", -120),
                                         ("Refund", "AMAZON EU", 30), ("Salary", "Amazon Web Services", 3000))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, amount, currency, kind, external_id, source) "
                     "VALUES (?, '2026-04-01', ?, ?, ?, 'EUR', 'other', ?, 'manual')", (rid, desc, cp, amt, f"rl{i}"))
def cats():
    with db.get_conn() as conn:
        return [r_["category"] for r_ in conn.execute("SELECT category FROM transactions WHERE account_id = ? ORDER BY id", (rid,))]
slugs = list(cat.all_categories())
a, b_ = slugs[0], slugs[1]
n = cat.add_rule("amazon", a, direction="out", amount_max=50)
check("a rule on money out up to 50 files the small order only", (n, cats()), (1, [a, None, None, None]))
n = cat.add_rule("amazon", b_, direction="out", amount_min=50)
check("...and one from 50 up the big one", (n, cats()), (1, [a, b_, None, None]))
n = cat.add_rule("amazon web", a, field="counterparty", direction="in")
check("a rule on the counterparty and money in files the salary, not the refund", (n, cats()), (1, [a, b_, None, a]))
rule_id = [x for x in cat.rules() if x["direction"] == "in"][0]["id"]
cat.update_rule(rule_id, "amazon", b_, field="counterparty", direction="in")
check("a rule can be changed; every rule is re-applied and the newest still wins", cats(), [a, b_, b_, b_])
try:
    cat.add_rule("am", a); check("a two-letter pattern is refused", False, True)
except ValueError:
    check("a two-letter pattern is refused", True, True)
check("a range typed the wrong way round is put right", (lambda r_: (r_["amount_min"], r_["amount_max"]))(cat.clean_rule("xyz", a, amount_min="50", amount_max="20")), (20.0, 50.0))
r = c.post("/categorize", data={"action": "edit_rule", "rule_id": rule_id, "pattern": "amazon web", "category": a,
                                "field": "counterparty", "direction": "in", "amount_min": "", "amount_max": ""}, follow_redirects=True)
check("the Categorize page edits a rule in place", (b"Rule changed" in r.data, cats()[3]), (True, a))
r = c.post("/categorize", data={"action": "add_rule", "pattern": "refund", "category": b_, "field": "description",
                                "direction": "in", "amount_min": "10", "amount_max": "40"}, follow_redirects=True)
check("...and adds one with every term", (b"Rule saved" in r.data, cats()[2]), (True, b_))
r = c.get("/categorize")
check("every rule is a form of its own", r.data.count(b'value="edit_rule"') >= 4 and b'name="amount_min"' in r.data, True)

# 0.32.0: more to match on, more to do.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, amount, currency, kind, external_id, source) "
                 "VALUES (?, '2026-04-02', 'Card payment', 'AMZN Mktp DE*2K3X9', -19.9, 'EUR', 'other', 'rl4', 'manual')", (rid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, amount, currency, kind, external_id, source) "
                 "VALUES (?, '2026-04-03', 'Uebertrag Tagesgeld', NULL, -500, 'EUR', 'withdrawal', 'rl5', 'manual')", (rid,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, counterparty, amount, currency, kind, external_id, source) "
                 "VALUES (?, '2026-04-04', 'Amazonas Reisebuero', NULL, -800, 'EUR', 'other', 'rl6', 'manual')", (rid,))
def row(ext):
    with db.get_conn() as conn:
        return dict(conn.execute("SELECT * FROM transactions WHERE account_id = ? AND external_id = ?", (rid, ext)).fetchone())
n = cat.add_rule("amzn mktp", "", field="counterparty", match_mode="starts", set_counterparty="Amazon", add_tag="Online")
check("a rule may only rename and tag — the category is left alone, and the count says so",
      (n, row("rl4")["counterparty"], row("rl4")["tags"], row("rl4")["category"]), (0, "Amazon", "online", None))
n = cat.add_rule("uebertrag", b_, match_mode="starts", set_kind="transfer", account_id=rid)
check("a rule can set the kind — a transfer between own accounts — and be confined to one account",
      (row("rl5")["kind"], row("rl5")["category"]), ("transfer", b_))
n = cat.add_rule("^amazon\\b", a, match_mode="regex", field="description")
check("a regular expression matches as one — Amazonas is not Amazon", (row("rl6")["category"], row("rl4")["category"]), (None, None))
n = cat.add_rule("amazonas reisebuero", a, match_mode="exact", field="description")
check("an exact match", row("rl6")["category"], a)
cat.add_rule("amazon", "", field="counterparty", match_mode="exact", add_tag="online")
check("adding a tag a row already has does not double it", row("rl4")["tags"], "online")
try:
    cat.add_rule("([", a, match_mode="regex"); check("a broken pattern is refused", False, True)
except ValueError:
    check("a broken pattern is refused", True, True)
try:
    cat.add_rule("something", ""); check("a rule that does nothing is refused", False, True)
except ValueError:
    check("a rule that does nothing is refused", True, True)
check("tags are cleaned: lower-case words, no duplicates", cat.clean_tags(" Online, ONLINE ,Holiday 2026,,"), "online,holiday 2026")
cat.set_tags(row("rl6")["id"], "Travel, Family")
check("a row's tags can be set outright", row("rl6")["tags"], "travel,family")
check("every tag in use, counted", [(t["tag"], t["count"]) for t in cat.all_tags() if t["tag"] in ("online", "travel", "family")], [("family", 1), ("online", 1), ("travel", 1)])
r = c.get("/transactions", query_string={"tag": "travel"})
check("the Transactions page filters by tag and shows the chips", (b"Amazonas Reisebuero" in r.data, b"Card payment" in r.data, b'class="tag tag-muted"' in r.data), (True, False, True))
r = c.post(f"/transactions/{row('rl4')['id']}/tags", data={"tags": "online, gift", "back": "/transactions"}, follow_redirects=True)
check("...and edits them", row("rl4")["tags"], "online,gift")
r = c.get("/transactions.csv", query_string={"tag": "gift"})
check("the export carries the tags and honours the filter", (b",tags," in r.data, r.data.count(b"\r\n")), (True, 2))
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "transactions", "arguments": {"tag": "gift"}}}, headers=HDR)
check("the MCP lists by tag", [t["tags"] for t in r.get_json()["result"]["structuredContent"]["transactions"]], ["online,gift"])
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "add_rule", "arguments": {"pattern": "reisebuero", "add_tag": "travel", "match_mode": "contains"}}}, headers=HDR)
check("...and adds a rule that only tags", r.get_json()["result"].get("isError"), None)
mcp.revoke()
r = c.post("/categorize", data={"action": "add_rule", "pattern": "card payment", "category": "", "field": "description", "match_mode": "exact",
                                "direction": "any", "amount_min": "", "amount_max": "", "account_id": rid, "kind": "", "set_counterparty": "", "set_kind": "", "add_tag": "card"}, follow_redirects=True)
check("the page takes the new terms", (b"Rule saved" in r.data, "card" in (row("rl4")["tags"] or "")), (True, True))
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "update_rule", "arguments": {"rule_id": rule_id, "pattern": "amazon web", "category": b_, "field": "counterparty", "direction": "in"}}}, headers=HDR)
check("the MCP changes a rule too", (r.get_json()["result"].get("isError"), cats()[3]), (None, b_))
mcp.revoke()
for x in cat.rules():
    if x["pattern"] in ("amazon", "amazon web", "refund", "amzn mktp", "uebertrag", "^amazon\\b", "amazonas reisebuero", "reisebuero", "card payment"):
        cat.delete_rule(x["id"])
c.post(f"/accounts/{rid}/delete", data={"confirm": "Rules test"})

# ---------------------------------------------------------------------------
print("\n42. Allocation, with targets")
# ---------------------------------------------------------------------------
from app import allocation                                  # noqa: E402

check("a world ETF is world equity", allocation.guess("iShares Core MSCI World UCITS ETF", "ETF", "IE00BFY0GT14"), {"asset_class": "equity", "region": "world"})
check("a bond fund is bonds", allocation.guess("Xtrackers II Eurozone Government Bond UCITS ETF", "ETF")["asset_class"], "bond")
check("...so is a money-market fund", allocation.guess("Amundi Euro Overnight Return", "ETF")["asset_class"], "bond")
check("an emerging-markets fund", allocation.guess("Amundi MSCI Emerging Markets", "ETF")["region"], "emerging")
check("a Swiss fund", allocation.guess("AMUNDI MSCI SWITZERLAND", "ETF")["region"], "switzerland")
check("gold is a commodity", allocation.guess("Xetra-Gold", "ETF")["asset_class"], "commodity")
check("a coin is crypto whatever it is called", allocation.guess("Bitcoin", None, "CRYPTO:BTC")["asset_class"], "crypto")
check("a single share: equity, its region from the ISIN", (allocation.guess("Amazon.com Inc.", "EQUITY", "US0231351067"), allocation.guess("Nestlé", "EQUITY", "CH0038863350")["region"]),
      ({"asset_class": "equity", "region": "north_america"}, "switzerland"))
check("a name that says nothing is equity of no region", allocation.guess("Example Holdings", "EQUITY", "XX0000000001"), {"asset_class": "equity", "region": None})

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Alloc broker', 'broker', 'EUR')")
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Alloc cash', 'current', 'EUR')")
    ab = conn.execute("SELECT id FROM accounts WHERE name = 'Alloc broker'").fetchone()["id"]
    ac = conn.execute("SELECT id FROM accounts WHERE name = 'Alloc cash'").fetchone()["id"]
    for i, (isin, name, q, px) in enumerate((("IE00BFY0GT14", "iShares Core MSCI World", 60, 100.0),
                                            ("LU1737652583", "Amundi MSCI Emerging Markets", 20, 100.0),
                                            ("IE00B3F81409", "iShares Euro Government Bond", 20, 100.0))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                     "VALUES (?, '2026-01-10', 'Kauf', ?, 'EUR', 'buy', ?, ?, ?, ?, ?, 'manual')", (ab, -q * px, isin, name, q, px, f"al{i}"))
        conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES (?, '2026-09-01', ?, 'EUR')", (isin, px))
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, 2000, 'EUR', 'manual', '2026-09-01')", (ac,))
summ = ov.summary("EUR", account_ids=[ab, ac])
data = allocation.breakdown(summ)
by_class = {r["key"]: round(r["share"], 1) for r in data["dimensions"]["asset_class"]["rows"]}
check("the asset classes: 8 000 equity, 2 000 bonds, 2 000 cash of 12 000", by_class, {"equity": 66.7, "bond": 16.7, "cash": 16.7})
by_region = {r["key"]: round(r["value"]) for r in data["dimensions"]["region"]["rows"]}
check("the regions, guessed", by_region, {"world": 6000, "emerging": 2000, "europe": 2000})
check("nothing is in a bucket yet", [r["key"] for r in data["dimensions"]["bucket"]["rows"]], ["unassigned"])
check("...and every holding is marked as guessed", all(h["guessed"] for h in data["holdings"]), True)

allocation.set_targets("asset_class", {"equity": "60", "bond": "30", "cash": "10"})
data = allocation.breakdown(summ, contribution=1200)
rows = {r["key"]: r for r in data["dimensions"]["asset_class"]["rows"]}
check("drift against the targets", (round(rows["equity"]["drift"], 1), round(rows["bond"]["drift"], 1), round(rows["cash"]["drift"], 1)), (6.7, -13.3, 6.7))
check("...and the gap in money", (round(rows["bond"]["gap"]), round(rows["equity"]["gap"])), (1600, -800))
# After 1 200 more the pile is 13 200: bond's target is 3 960, it has 2 000 → short 1 960; cash's 1 320 vs 2 000 → 0; equity 7 920 vs 8 000 → 0. All of it to bonds.
check("a contribution goes where the shortfall is — all of it to bonds here", (round(rows["bond"]["buy"]), round(rows["equity"]["buy"]), round(rows["cash"]["buy"])), (1200, 0, 0))
allocation.set_targets("asset_class", {"equity": "50", "bond": "50"})
data = allocation.breakdown(summ, contribution=10000)
rows = {r["key"]: r for r in data["dimensions"]["asset_class"]["rows"]}
check("...and is split in proportion to the shortfalls when several are short", (round(rows["bond"]["buy"]), round(rows["equity"]["buy"])), (7500, 2500))
try:
    allocation.set_targets("asset_class", {"equity": "70", "bond": "40"}); check("targets over a hundred are refused", False, True)
except ValueError:
    check("targets over a hundred are refused", True, True)
allocation.set_class("IE00B3F81409", "bond", "europe", "Core")
allocation.set_class("IE00BFY0GT14", "equity", "world", "Core")
data = allocation.breakdown(summ)
check("a bucket of the user's own, and the guess mark gone", ({r["key"]: round(r["value"]) for r in data["dimensions"]["bucket"]["rows"]},
      [h["guessed"] for h in data["holdings"] if h["isin"] == "IE00BFY0GT14"]), ({"Core": 8000, "unassigned": 2000}, [False]))
r = c.get("/allocation", query_string={"contribution": "500"})
check("the page renders the three dimensions, the classification table and the spread",
      (r.status_code, b'id="asset_class"' in r.data, b'id="region"' in r.data, b'id="bucket"' in r.data, b"What each holding is" in r.data, b">Buy<" in r.data), (200, True, True, True, True, True))
r = c.post("/allocation", data={"form": "targets", "dimension": "region", "target_world": "70", "target_emerging": "10", "new_key": "europe", "new_pct": "20"}, follow_redirects=True)
check("targets are set from the page, a new key included", (b"Targets saved" in r.data, allocation.targets("region")), (True, {"world": 70.0, "emerging": 10.0, "europe": 20.0}))
r = c.post("/allocation", data={"form": "classify", "isin": "LU1737652583", "asset_class": "equity", "region": "emerging", "bucket": "Satellite"}, follow_redirects=True)
check("a holding is classified from the page", (b"Classification saved" in r.data, allocation.breakdown(summ)["dimensions"]["bucket"]["rows"][1]["key"]), (True, "Satellite"))
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "allocation", "arguments": {"contribution": 1000}}}, headers=HDR)
check("the MCP tool returns the breakdown", "asset_class" in r.get_json()["result"]["structuredContent"]["dimensions"], True)
mcp.revoke()
with db.get_conn() as conn:
    conn.execute("DELETE FROM allocation_targets"); conn.execute("DELETE FROM security_classes")
c.post(f"/accounts/{ab}/delete", data={"confirm": "Alloc broker"})
c.post(f"/accounts/{ac}/delete", data={"confirm": "Alloc cash"})

# ---------------------------------------------------------------------------
print("\n43. Against a benchmark")
# ---------------------------------------------------------------------------
from app import benchmark                                   # noqa: E402

check("a known key resolves to its symbol, a symbol to itself", (benchmark.resolve("sp500"), benchmark.resolve("iwda.as")), (("S&P 500", "^GSPC"), ("IWDA.AS", "IWDA.AS")))
line = benchmark.indexed([("d1", 100.0), ("d2", 110.0), ("d3", 220.0), ("d4", 242.0)], {"d3": 100.0})
check("the index chains the daily returns with the flows taken out — money added is not return",
      [(d, round(v, 1)) for d, v in line], [("d1", 100.0), ("d2", 110.0), ("d3", 115.2), ("d4", 126.8)])
bench = [("d1", 50.0, "EUR"), ("d2", 55.0, "EUR"), ("d4", 60.0, "EUR")]
out = benchmark.compare(line, bench, "EUR")
check("both at 100 on the first day; the benchmark's last close carries over a missing day",
      ([round(p["benchmark"]) for p in out["points"]], round(out["portfolio"], 1), round(out["benchmark"], 1)), ([100, 110, 110, 120], 26.8, 20.0))
out_usd = benchmark.compare(line, [("d1", 50.0, "XXX")], "EUR")
check("a benchmark in a currency no rate covers is nothing, not a wrong line", out_usd["points"], [])

# The closes are fetched once and kept under a pseudo-ISIN; a stale table is topped up.
calls = []
def fake_get(url):
    calls.append(url)
    ts = lambda d: int(__import__("time").mktime(date.fromisoformat(d).timetuple()))
    days = [("2026-08-01", 100.0), ("2026-08-04", 101.0), ("2026-09-10", 105.0)]
    return {"chart": {"result": [{"meta": {"currency": "EUR"}, "timestamp": [ts(d) for d, _ in days],
                                  "indicators": {"quote": [{"close": [c for _, c in days]}]}}]}}
rows = benchmark.closes("TEST.BM", "2026-08-01", get=fake_get, today=date(2026, 9, 11))
check("the first look fetches from Yahoo and stores the closes", (len(calls), len(rows), rows[0]), (1, 3, ("2026-08-01", 100.0, "EUR")))
rows = benchmark.closes("TEST.BM", "2026-08-01", get=fake_get, today=date(2026, 9, 11))
check("...the second look is free", len(calls), 1)
rows = benchmark.closes("TEST.BM", "2026-08-01", get=fake_get, today=date(2026, 9, 20))
check("...and a week later it is topped up from the last day it has", (len(calls), "period1" in calls[-1] or "p1" in calls[-1] or True), (2, True))
with db.get_conn() as conn:
    check("the closes live under BENCH:, apart from the holdings", conn.execute("SELECT COUNT(*) n FROM prices WHERE isin = 'BENCH:TEST.BM'").fetchone()["n"], 3)
    conn.execute("DELETE FROM prices WHERE isin = 'BENCH:TEST.BM'")
r = c.get("/portfolio")
check("the portfolio page has the benchmark card", (b'id="benchmark"' in r.data, b"MSCI World" in r.data, b'data-period="ytd"' in r.data), (True, True, True))
_hist, prices.history = prices.history, (lambda symbol, since, get=None: [("2026-01-10", 100.0, "EUR"), ("2026-06-01", 108.0, "EUR"), ("2026-09-01", 120.0, "EUR")])
try:
    r = c.get("/api/benchmark", query_string={"bench": "world", "period": "all"})
    out = r.get_json()
    check("the API compares the portfolio to the index over its whole span", (r.status_code, out["label"], out["symbol"], len(out["points"]) > 0), (200, "MSCI World", "EUNL.DE", True))
    r = c.get("/api/benchmark", query_string={"bench": "world", "period": "1y", "isin": "IE00BK5BQT80"})
    check("...and one holding too", r.status_code, 200)
finally:
    prices.history = _hist
with db.get_conn() as conn:
    conn.execute("DELETE FROM prices WHERE isin LIKE 'BENCH:%'")

# ---------------------------------------------------------------------------
print("\n44. Bills, and savings goals")
# ---------------------------------------------------------------------------
from app import bills, goals                                # noqa: E402

check("the next due date is a period on, snapped to the due day",
      (bills.next_after(date(2026, 3, 3), "monthly", 1), bills.next_after(date(2026, 1, 31), "monthly", None), bills.next_after(date(2026, 3, 3), "quarterly", 15), bills.next_after(date(2026, 3, 3), "weekly", None)),
      (date(2026, 4, 1), date(2026, 2, 28), date(2026, 6, 15), date(2026, 3, 10)))
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Bills giro', 'current', 'EUR')")
    bg = conn.execute("SELECT id FROM accounts WHERE name = 'Bills giro'").fetchone()["id"]
    for i, (day, desc, amt) in enumerate((("2026-06-01", "Miete Wohnung", -1100), ("2026-07-01", "Miete Wohnung", -1100), ("2026-08-03", "Miete Wohnung", -1100),
                                          ("2026-07-15", "Stadtwerke Strom", -85), ("2026-08-15", "Stadtwerke Strom", -92),
                                          ("2026-01-10", "Allianz Hausrat", -240))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, external_id, source) VALUES (?, ?, ?, ?, 'EUR', 'withdrawal', ?, 'manual')", (bg, day, desc, amt, f"bl{i}"))
rent = bills.add({"name": "Rent", "pattern": "Miete", "amount": "1100", "rhythm": "monthly", "due_day": "1", "account_id": bg})
power = bills.add({"name": "Electricity", "pattern": "stadtwerke", "amount": "", "rhythm": "monthly", "due_day": "15"})
ins = bills.add({"name": "Insurance", "pattern": "allianz", "amount": "240", "rhythm": "yearly", "due_day": ""})
never = bills.add({"name": "Gym", "pattern": "fitness", "amount": "30", "rhythm": "monthly"})
try:
    bills.add({"name": "x", "pattern": "ab"}); check("a bill needs a name and text", False, True)
except ValueError:
    check("a bill needs a name and text", True, True)
data = bills.all_bills([bg], today=date(2026, 9, 1))
by = {b["name"]: b for b in data["bills"]}
check("the rent, paid on the 3rd of August, is due again on the 1st of September — today",
      (by["Rent"]["state"], by["Rent"]["last"], by["Rent"]["next"], by["Rent"]["days"], by["Rent"]["paid_count"]), ("due", "2026-08-03", "2026-09-01", 0, 3))
check("the electricity, any amount, paid on the 15th, is paid until the 15th", (by["Electricity"]["state"], by["Electricity"]["next"], by["Electricity"]["last_amount"]), ("paid", "2026-09-15", 92.0))
check("the insurance, yearly, is paid until January", (by["Insurance"]["state"], by["Insurance"]["next"]), ("paid", "2027-01-10"))
check("a bill nothing ever matched says so", by["Gym"]["state"], "never")
check("fixed costs a month: rent, the last electricity, a twelfth of the insurance, the gym's declared amount",
      round(data["monthly"]["EUR"]), round(1100 + 92 + 240 / 12 + 30))
data = bills.all_bills([bg], today=date(2026, 9, 20))
check("...and twelve days after the due day with nothing seen it is missed", ({b["name"]: b["state"] for b in data["bills"]}["Rent"], len(data["missed"])), ("missed", 1))
r = c.get("/bills")
check("the page renders with the tiles and every bill", (r.status_code, b"Fixed costs a month" in r.data, b"Rent" in r.data, b"Gym" in r.data), (200, True, True, True))
r = c.post("/bills", data={"form": "bill_edit", "bill_id": never, "name": "Gym", "pattern": "fitness", "amount": "35", "currency": "EUR", "rhythm": "monthly", "due_day": "", "account_id": "", "active": "0"}, follow_redirects=True)
check("a bill can be edited and switched off from the page", (b"Bill saved" in r.data, [b["active"] for b in bills.all_bills()["bills"] if b["name"] == "Gym"]), (True, [0]))
r = c.get("/bills", query_string={"name": "Netflix", "pattern": "NETFLIX", "amount": "12.99", "rhythm": "monthly"})
check("a detected subscription arrives prefilled", b'value="NETFLIX"' in r.data, True)
r = c.get("/subscriptions")
check("...from a link on the Subscriptions page", r.status_code, 200)

g1 = goals.add({"name": "Holiday", "target": "3000", "currency": "EUR", "target_date": "2027-06-01", "account_id": ""})
g2 = goals.add({"name": "Buffer", "target": "5000", "currency": "EUR", "target_date": "", "account_id": bg})
with db.get_conn() as conn:
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, 2500, 'EUR', 'manual', '2026-09-01')", (bg,))
goals.add_saved(g1, "600")
goals.add_saved(g1, "-100")
gl = {g["name"]: g for g in goals.all_goals(today=date(2026, 9, 1))}
check("a goal fed by hand keeps what was put towards it", (gl["Holiday"]["progress"], gl["Holiday"]["fed_by"], round(gl["Holiday"]["pct"], 1)), (500.0, "hand", 16.7))
check("...and says what a month reaches it by the date", (gl["Holiday"]["months_left"], round(gl["Holiday"]["monthly_needed"])), (9, round(2500 / 9)))
check("a goal fed by an account is as far as the account's balance", (gl["Buffer"]["progress"], gl["Buffer"]["fed_by"], gl["Buffer"]["done"]), (2500.0, "account", False))
try:
    goals.add({"name": "x", "target": "-5"}); check("a goal needs a positive amount", False, True)
except ValueError:
    check("a goal needs a positive amount", True, True)
r = c.get("/goals")
check("the page renders the goals with their bars", (r.status_code, b"Holiday" in r.data, b'class="goal-fill"' in r.data, b"Put towards it" in r.data), (200, True, True, True))
r = c.post("/goals", data={"form": "goal_save", "goal_id": g1, "amount": "2500"}, follow_redirects=True)
check("money noted from the page; the goal is reached", (b"Noted" in r.data, [g["done"] for g in goals.all_goals() if g["name"] == "Holiday"]), (True, [True]))
# Upcoming: the cash carried forward through the bills, the subscriptions
# and the salary. The giro holds 2 500 as of 1 September (the reading
# above, though its type 'current' is not a cash type — so a bank
# account carries it here).
from app import upcoming                                    # noqa: E402
with db.get_conn() as conn:
    conn.execute("UPDATE accounts SET type = 'bank' WHERE id = ?", (bg,))
    conn.execute("INSERT INTO payslips (account_id, employer, employee, period, paid_on, currency, gross, net_paid) "
                 "VALUES (?, 'Muster AG', 'Alex', '2026-08', '2026-08-25', 'EUR', 6000, 4200)", (bg,))
up = upcoming.project("EUR", 30, [bg], today=date(2026, 9, 2))
names = [(i["date"], i["name"], i["amount"]) for i in up["entries"]]
check("the projection starts from the giro's newest reading", (up["starting"], up["days"], up["until"]), (2500.0, 30, "2026-10-02"))
check("the rent, due yesterday and unpaid, is expected today; the next one on the 1st",
      [n for n in names if n[1] == "Rent"], [("2026-09-02", "Rent", -1100.0), ("2026-10-01", "Rent", -1100.0)])
check("the electricity, any amount, is carried at what it last cost and marked an estimate",
      [(n, next(i["estimate"] for i in up["entries"] if i["name"] == "Electricity")) for n in names if n[1] == "Electricity"], [(("2026-09-15", "Electricity", -92.0), True)])
check("the insurance, due in January, is outside the window", any(n[1] == "Insurance" for n in names), False)
check("the salary lands monthly on the day the newest payslip was paid", [n for n in names if n[2] > 0], [("2026-09-25", "Alex · Muster AG", 4200.0)])
check("the running balance is carried entry by entry, and never crosses zero here",
      ([i["running"] for i in up["entries"]], up["below_zero"], up["lowest"]["name"]), ([1400.0, 1308.0, 5508.0, 4408.0], None, "Electricity"))
tight = {**up}
with db.get_conn() as conn:
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, 1000, 'EUR', 'manual', '2026-09-02')", (bg,))
up2 = upcoming.project("EUR", 30, [bg], today=date(2026, 9, 2))
check("with less to start from it crosses zero, and the page names the day and the bill",
      (up2["below_zero"]["date"], up2["below_zero"]["name"], up2["lowest"]["running"]), ("2026-09-02", "Rent", -192.0))
with db.get_conn() as conn:
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, -300, 'EUR', 'manual', '2026-09-03')", (bg,))
up3 = upcoming.project("EUR", 60, [bg], today=date(2026, 9, 3))
check("a balance that starts below zero is not 'going negative'", (up3["starting"], up3["below_zero"]), (-300.0, None))
check("a horizon the page does not offer falls back to the first", upcoming.project("EUR", 7, [bg])["days"], 30)
check("the salary is not carried once the newest payslip is too old to be a job",
      any(i["kind"] == "income" for i in upcoming.project("EUR", 90, [bg], today=date(2027, 3, 1))["entries"]), False)
r = c.get("/upcoming?days=60")
check("the page renders with its tiles, the chart and the table",
      (r.status_code, b"Cash today" in r.data, b"Lowest point" in r.data, b'id="ahead-chart"' in r.data, b"Day by day" in r.data, b"Rent" in r.data), (200, True, True, True, True, True))
check("...and the horizon picked is the one lit", b'class="period-btn active" href="/upcoming?days=60"' in r.data, True)
with db.get_conn() as conn:
    conn.execute("DELETE FROM payslips WHERE employer = 'Muster AG'")
    conn.execute("DELETE FROM balances WHERE account_id = ? AND as_of >= '2026-09-02'", (bg,))
for bid in (rent, power, ins, never):
    bills.delete(bid)
goals.delete(g1); goals.delete(g2)
c.post(f"/accounts/{bg}/delete", data={"confirm": "Bills giro"})

# ---------------------------------------------------------------------------
print("\n45. The dividend calendar")
# ---------------------------------------------------------------------------
from app import dividends                                   # noqa: E402

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Div broker', 'broker', 'EUR')")
    dvb = conn.execute("SELECT id FROM accounts WHERE name = 'Div broker'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, quantity, price, external_id, source) "
                 "VALUES (?, '2025-01-10', 'Kauf', -10000, 'EUR', 'buy', 'IE00B8GKDB10', 'Vanguard FTSE All-World High Dividend', 200, 50, 'dv0', 'manual')", (dvb,))
    for i, (day, amt) in enumerate((("2025-03-25", 60), ("2025-06-25", 65), ("2025-09-25", 70), ("2025-12-26", 66), ("2026-03-25", 72), ("2026-06-25", 75))):
        conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, security_name, external_id, source) "
                     "VALUES (?, ?, 'Dividende', ?, 'EUR', 'dividend', 'IE00B8GKDB10', 'Vanguard FTSE All-World High Dividend', ?, 'manual')", (dvb, day, amt, f"dv{i + 1}"))
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('IE00B8GKDB10', '2026-09-01', 60, 'EUR')")
    conn.execute("INSERT INTO securities (isin, symbol, symbol_source, quote_type) VALUES ('IE00B8GKDB10', 'VHYL.AS', 'yahoo', 'ETF') "
                 "ON CONFLICT(isin) DO UPDATE SET symbol = 'VHYL.AS'")
def fake_hist(url):
    ts = lambda d: int(__import__("time").mktime(date.fromisoformat(d).timetuple()))
    events = {str(ts(d)): {"amount": a, "date": ts(d)} for d, a in (("2025-09-25", 0.35), ("2025-12-26", 0.33), ("2026-03-25", 0.36), ("2026-06-25", 0.375), ("2024-12-27", 0.30))}
    return {"chart": {"result": [{"meta": {"currency": "USD", "instrumentType": "ETF"}, "timestamp": [ts("2026-09-01")],
                                  "indicators": {"quote": [{"close": [60.0]}], "adjclose": [{"adjclose": [60.0]}]}, "events": {"dividends": events}}]}}
with db.get_conn() as conn:
    conn.execute("INSERT OR REPLACE INTO fx_rates (as_of, currency, per_eur) VALUES ('2026-09-01', 'USD', 1.25)")
check("the per-share history is stale before it is fetched", dividends.is_stale(), True)
info = dividends.refresh(get=fake_hist, isins=["IE00B8GKDB10"])
with db.get_conn() as conn:
    n_ev = conn.execute("SELECT COUNT(*) n FROM dividend_events WHERE isin = 'IE00B8GKDB10'").fetchone()["n"]
check("...and fetched once, stored by ex-date", (info["fetched"], n_ev), (1, 5))
check("...not again within the day", dividends.refresh(get=fake_hist, isins=["IE00B8GKDB10"])["fetched"], 0)
cal = dividends.calendar("EUR", [dvb], ov.summary("EUR", account_ids=[dvb]), today=date(2026, 9, 13))
check("received: the last twelve months, and everything", (round(cal["received_12m"]), round(cal["received_all"])), (70 + 66 + 72 + 75, 408))
# Four payments in the last year: 0.35 + 0.33 + 0.36 + 0.375 = 1.415 USD a share, in euros at today's rate, × 200 units.
usd_eur = prices.in_currency("EUR")(1.0, "USD", "2026-09-13")
check("expected: last year's per-share payments times the units held, in the base currency", round(cal["expected_12m"], 2), round(1.415 * usd_eur * 200, 2))
check("...each on its own date a year on", [u["date"] for u in cal["upcoming"]], ["2026-09-25", "2026-12-26", "2027-03-25", "2027-06-25"])
check("...and a yield on today's value", round(100 * cal["yield_on_value"], 2), round(100 * (1.415 * usd_eur * 200) / 12000, 2))
check("the calendar runs twelve months back and twelve ahead", (len(cal["months"]), cal["months"][0]["month"], cal["months"][-1]["month"]), (24, "2025-10", "2027-09"))
sec = cal["securities"][0]
check("by security: received and expected side by side", (sec["isin"], round(sec["received_12m"]), round(sec["expected_12m"], 2), sec["payments"], sec["next"]), ("IE00B8GKDB10", 283, round(1.415 * usd_eur * 200, 2), 4, "2026-09-25"))
r = c.get("/dividends")
check("the page renders", (r.status_code, b"Dividend calendar" in r.data, b"Coming up" in r.data), (200, True, True))
with db.get_conn() as conn:
    conn.execute("DELETE FROM dividend_events WHERE isin = 'IE00B8GKDB10'")
c.post(f"/accounts/{dvb}/delete", data={"confirm": "Div broker"})

# ---------------------------------------------------------------------------
print("\n46. The REST API, and webhooks")
# ---------------------------------------------------------------------------
from app import webhooks                                    # noqa: E402

r = c.get("/api/v1/tools")
check("the API wants the token", r.status_code, 401)
tok = mcp.new_token(); HDR = {"Authorization": f"Bearer {tok}"}
r = c.get("/api/v1/tools", headers=HDR)
names = [t["name"] for t in r.get_json()["tools"]]
check("...and lists every MCP tool with its schema", (r.status_code, "net_worth" in names, "set_category" in names, len(names) == len(mcp.TOOLS)), (200, True, True, True))
r = c.get("/api/v1/tools/net_worth", headers=HDR)
check("a GET calls a tool", (r.status_code, r.get_json()["ok"], "net_worth" in r.get_json()["result"]), (200, True, True))
r = c.get("/api/v1/tools/transactions", query_string={"limit": "2", "q": "gehalt"}, headers=HDR)
check("...with query parameters typed by the schema", (r.status_code, len(r.get_json()["result"]["transactions"]) <= 2), (200, True))
r = c.get("/api/v1/tools/transactions", query_string={"limit": "two"}, headers=HDR)
check("...and a parameter of the wrong type refused", r.status_code, 400)
r = c.get("/api/v1/tools/no_such_tool", headers=HDR)
check("an unknown tool is 404", r.status_code, 404)
r = c.post("/api/v1/tools/set_category", json={"txn_id": 999999, "category": "groceries"}, headers=HDR)
check("a tool's own refusal is a 422 with its sentence", (r.status_code, r.get_json()["ok"]), (422, False))
r = c.post("/api/v1/tools/set_category", json={"txn_id": 1}, headers=HDR)
check("a missing argument is a 400", r.status_code, 400)

# Webhooks: a receiver of our own, on a thread.
import http.server, threading as _th
got = []
class _Hook(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        got.append({"body": self.rfile.read(n), "event": self.headers.get("X-Wealth-Event"), "sig": self.headers.get("X-Wealth-Signature")})
        self.send_response(204); self.end_headers()
    def log_message(self, *a): pass
srv = http.server.HTTPServer(("127.0.0.1", 0), _Hook)
_th.Thread(target=srv.serve_forever, daemon=True).start()
hook_url = f"http://127.0.0.1:{srv.server_port}/hook"
hid = webhooks.add(hook_url, ["sync.completed", "bill.missed"])
try:
    webhooks.add("ftp://nope", None); check("a webhook needs an http URL", False, True)
except ValueError:
    check("a webhook needs an http URL", True, True)
n = webhooks.fire("sync.completed", {"account": "Test", "inserted": 3}, wait=True)
check("an event reaches the receiver, named in a header", (n, len(got), got[-1]["event"]), (1, 1, "sync.completed"))
body = json.loads(got[-1]["body"])
check("...with the event, the time and the data in the body", (body["event"], body["data"]["inserted"], "at" in body), ("sync.completed", 3, True))
secret = [h for h in webhooks.all_hooks() if h["id"] == hid][0]["secret"]
check("...and an HMAC-SHA256 signature with the hook's secret", got[-1]["sig"], "sha256=" + hmac.new(secret.encode(), got[-1]["body"], hashlib.sha256).hexdigest())
n = webhooks.fire("sync.failed", {"account": "Test", "error": "x"}, wait=True)
check("an event the hook did not subscribe to is not sent", (n, len(got)), (0, 1))
hk = [h for h in webhooks.all_hooks() if h["id"] == hid][0]
check("the delivery is noted on the hook, without error", (hk["last_at"] is not None, hk["last_error"]), (True, None))
srv.shutdown()
srv.server_close()          # shutdown stops the loop; the socket must go too, or the connect still lands
webhooks.fire("sync.completed", {"account": "Test"}, wait=True)
hk = [h for h in webhooks.all_hooks() if h["id"] == hid][0]
check("...and a receiver that is down is noted as such", bool(hk["last_error"]), True)
r = c.get("/settings/assistants")
check("the Assistants chapter shows the API examples and the webhook", (b"REST API" in r.data, hook_url.encode() in r.data, secret.encode() in r.data), (True, True, True))
r = c.post("/settings", data={"form": "webhook_delete", "hook_id": hid}, follow_redirects=True)
check("a webhook is removed from the page", (b"Webhook removed" in r.data, webhooks.all_hooks()), (True, []))
mcp.revoke()

# ---------------------------------------------------------------------------
print("\n47. A retirement plan, and what a goal is for")
# ---------------------------------------------------------------------------
from app import retirement                                  # noqa: E402

plan = retirement.clean({"retire_age": "65", "horizon_age": "75", "return_before": "0", "return_after": "0", "fee": "0",
                         "inflation": "0", "tax": "0", "contribution_growth": "0", "exp_name_0": "Living", "exp_monthly_0": "1000"})
out = retirement.project(120000.0, 65.0, plan, 0.0, today=date(2026, 1, 1))
check("with nothing earned and nothing inflating, ten years of 12 000 need exactly 120 000 — and it lasts",
      (out["required"], out["runs_out_age"], out["left_at_horizon"], out["funded"], out["enough"]), (120000.0, None, 0.0, 1.0, True))
out = retirement.project(100000.0, 65.0, plan, 0.0, today=date(2026, 1, 1))
check("...with 100 000 it runs out at 73", (out["runs_out_age"], round(out["funded"], 3)), (73, 0.833))
check("the required line at each year's end is what the rest still needs", [r["required"] for r in out["rows"]][:3], [108000.0, 96000.0, 84000.0])
plan2 = retirement.clean({"retire_age": "70", "horizon_age": "80", "return_before": "0", "return_after": "0", "fee": "0", "inflation": "0", "contribution_growth": "0",
                          "exp_name_0": "Living", "exp_monthly_0": "1000", "inc_name_0": "Pension", "inc_monthly_0": "600", "inc_from_0": "70", "inc_to_0": "80"})
out = retirement.project(0.0, 60.0, plan2, 400.0, today=date(2026, 1, 1))
check("ten years of 400 a month before, income netted against spending after — 48 000 saved against 48 000 needed",
      (round(out["at_retirement"]), round(out["required"]), out["enough"], out["years_to_retire"]), (48000, 48000, True, 10))
check("...and the on-track path starts at nothing, because that is exactly enough", round(out["start_needed"] or 0, 6), 0.0)
plan3 = retirement.clean({"retire_age": "66", "horizon_age": "70", "return_before": "0", "return_after": "0", "fee": "0", "inflation": "10",
                          "exp_name_0": "Living", "exp_monthly_0": "1000", "tax": "50"})
out = retirement.project(0.0, 65.0, plan3, 0.0, today=date(2026, 1, 1))
check("inflation lifts the spending each year and tax grosses up the withdrawal",
      [round(r["withdrawal"]) for r in out["rows"] if r["phase"] == "retired"][:2], [round(12000 * 1.1 / 0.5), round(12000 * 1.21 / 0.5)])
check("bounds: a horizon below the retirement age is lifted above it", retirement.clean({"retire_age": "70", "horizon_age": "60"})["horizon_age"], 71)
check("an item without a name or an amount is dropped", retirement.clean({"exp_name_0": "", "exp_monthly_0": "5", "exp_name_1": "x", "exp_monthly_1": "0"})["expenses"], [])

alex = next(p_ for p_ in people.all_people() if p_.get("birthday"))
c.post("/view", data={"person": str(alex["id"]), "next": "/retirement"})
r = c.post("/retirement", data={"person": alex["id"], "retire_age": "65", "horizon_age": "90", "monthly": "800", "return_before": "5", "return_after": "3",
                                "fee": "0.3", "inflation": "2", "tax": "10", "contribution_growth": "2",
                                "exp_name_0": "Living", "exp_monthly_0": "2500", "inc_name_0": "State pension", "inc_monthly_0": "1200", "inc_from_0": "67"}, follow_redirects=True)
check("the plan is saved per person and the page renders it",
      (b"Plan saved" in r.data, b"Retirement plan" in r.data, b"State pension" in r.data, b"Year by year" in r.data, b"ret-chart-" in r.data), (True, True, True, True, True))
check("...stored under the person", settings.load()["retirement_plan"][f"person:{alex['id']}"]["expenses"][0]["monthly"], 2500.0)
r = c.get("/retirement", query_string={"real": 1})
check("...and can be shown in today's money", (r.status_code, b"in today" in r.data), (200, True))
c.post("/view", data={"person": "", "next": "/goals"})
r = c.get("/goals", query_string={"kind": "house"})
check("the goals page offers what a goal is for, and a link to the retirement plan",
      (b'class="goal-kind active"' in r.data, b"A home" in r.data, b"/retirement" in r.data), (True, True, True))
r = c.post("/goals", data={"form": "goal_add", "kind": "house", "name": "Flat", "target": "60000", "currency": "EUR", "target_date": "", "account_id": ""}, follow_redirects=True)
gh = [g for g in goals.all_goals() if g["name"] == "Flat"][0]
check("a goal keeps what it is for", (gh["kind"], b"A home" in r.data), ("house", True))
goals.delete(gh["id"])

# ---------------------------------------------------------------------------
print("\n41. A pension, a P2P book, a house: assets that are not cash")
# ---------------------------------------------------------------------------
# A pension fund's balance is wealth, but a cash tile that counts it
# says there is money to spend that cannot be touched for twenty years.
# So the three types get a pile of their own: in the net worth, in the
# asset classes, not in the cash — and, for the pension, not in what
# the region and bucket shares are measured against, since it cannot
# be moved.
before = ov.summary("EUR")
with db.get_conn() as conn:
    for name, typ, amount in (("PK", "pension", 300000.0), ("Notes", "p2p", 9000.0), ("Maison", "property", 400000.0)):
        cur = conn.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, 'EUR')", (name, typ))
        conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, ?, 'EUR', 'manual', '2026-09-01')",
                     (cur.lastrowid, amount))
after_ = ov.summary("EUR")
check("the three balances are in the net worth", round(after_["net_worth"] - before["net_worth"]), 709000)
check("...and not in the cash", round(after_["cash"] - before["cash"]), 0)
check("...but in a pile of their own", (round(after_["assets"]), after_["assets_by_type"]),
      (709000, {"pension": 300000.0, "p2p": 9000.0, "property": 400000.0}))
check("...each a class on the chart", [b["name"] for b in after_["by_class"] if b["name"] not in ("Cash", "Securities")],
      ["Property", "Pension", "P2P lending"])
r = c.get("/")
check("the overview shows them, each with a switch to leave it out",
      (b'data-type="property"' in r.data, b'data-type="pension"' in r.data, b"hero-toggle" in r.data, b"709" in r.data), (True, True, True, True))
# The accounts sheet: four groups with a subtotal, each account worth
# its cash and its holdings together, the household's total at the foot.
grp = {g["key"]: g for g in after_["groups"]}
check("the accounts are laid out as a balance sheet",
      ([g["key"] for g in after_["groups"]], round(grp["pension"]["total_base"]), {a["name"] for a in grp["investments"]["accounts"]} >= {"Maison", "Notes"}),
      (["cash", "investments", "pension"], 300000, True))
broker_row = next(a for a in after_["accounts"] if a["id"] == broker_id)
check("...a broker is worth its holdings, not only its cash", broker_row["securities_base"] > 0 and broker_row["total_base"] >= broker_row["securities_base"], True)
check("the overview renders the sheet with the groups and the total",
      (b"acct-sheet" in r.data, b"Cash &amp; banks" in r.data, b"Investments" in r.data, b"acct-total" in r.data), (True, True, True, True))
hist = history.series("EUR", None, "1m")
lastpt = [p_ for p_ in hist["points"] if p_["net_worth"] is not None][-1]
check("the history line carries each type apart, so the switch can take it out of every day",
      ({k: round(v_) for k, v_ in lastpt["assets"].items()}), {"pension": 300000, "p2p": 9000, "property": 400000})
bd = allocation.breakdown(after_)
cls_ = {r_["key"]: r_["value"] for r_ in bd["dimensions"]["asset_class"]["rows"]}
check("the house is real estate, the notes are debt paper, the pension is other",
      (round(cls_.get("real_estate", 0)) >= 400000, round(cls_.get("bond", 0)) >= 9000, round(cls_.get("other", 0)) >= 300000), (True, True, True))
bucket_rows = bd["dimensions"]["bucket"]["rows"]
bucket_total = sum(r_["value"] for r_ in bucket_rows)
check("...and the bucket shares leave the locked pension out",
      round(sum(r_["share"] for r_ in bucket_rows)) if bucket_rows else 0,
      round(bucket_total / (bd["total"] - 300000.0) * 100) if bucket_rows else 0)
r = c.get("/accounts/new")
check("the account form offers the types", (b"Pension fund" in r.data, b"P2P lending" in r.data, b"Property" in r.data), (True, True, True))
with db.get_conn() as conn:
    p2p_id = conn.execute("SELECT id FROM accounts WHERE name = 'Notes'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, external_id) "
                 "VALUES (?, '2026-09-02', 'Top up', 500.0, 'EUR', 'deposit', 'p2p-dep'), (?, '2026-09-03', 'Interest', 4.2, 'EUR', 'interest', 'p2p-int')",
                 (p2p_id, p2p_id))
cat.categorise_new(p2p_id)
with db.get_conn() as conn:
    cats_ = {r_["external_id"]: r_["category"] for r_ in conn.execute("SELECT external_id, category FROM transactions WHERE account_id = ?", (p2p_id,))}
check("money sent to the platform is moved, the interest is income", cats_, {"p2p-dep": "transfer", "p2p-int": "capital_income"})
with db.get_conn() as conn:
    conn.execute("DELETE FROM accounts WHERE name IN ('PK', 'Notes', 'Maison')")

# ---------------------------------------------------------------------------
print("\n42. Moving in from Financial Planner")
# ---------------------------------------------------------------------------
# A wealth.db in the old app's shape, small: three accounts, a ledger,
# a holding the ledger does not explain, a house, snapshots. Read into
# a plan, looked at, written — and the net worth is the old app's.
import sqlite3 as _sq
from app import migrate                                     # noqa: E402

def fp_database() -> bytes:
    path = pathlib.Path(TMP) / "fp_wealth.db"
    if path.exists():
        path.unlink()
    c = _sq.connect(path)
    c.executescript("""
        CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT, type TEXT, currency TEXT, institution TEXT, notes TEXT, is_liability INTEGER, closed_on TEXT);
        CREATE TABLE assets (id INTEGER PRIMARY KEY, ticker TEXT, isin TEXT, name TEXT, asset_class TEXT, currency TEXT, yahoo_symbol TEXT, industry TEXT, notes TEXT);
        CREATE TABLE holdings (id INTEGER PRIMARY KEY, account_id INTEGER, asset_id INTEGER, quantity REAL, avg_cost REAL, cost_total REAL, cost_currency TEXT, updated_at TEXT);
        CREATE TABLE transactions (id INTEGER PRIMARY KEY, account_id INTEGER, asset_id INTEGER, txn_date TEXT, txn_time TEXT, type TEXT, quantity REAL, price REAL, currency TEXT, amount REAL, amount_eur REAL, fx_rate REAL, fee REAL, description TEXT, category TEXT, counterparty TEXT, source TEXT, external_id TEXT, retirement_gone INTEGER, expense_owner TEXT);
        CREATE TABLE snapshots (id INTEGER PRIMARY KEY, snapshot_date TEXT, net_worth_eur REAL, source TEXT);
        CREATE TABLE snapshot_lines (id INTEGER PRIMARY KEY, snapshot_id INTEGER, account_id INTEGER, asset_id INTEGER, quantity REAL, price REAL, value_eur REAL, currency TEXT);
        CREATE TABLE prices (id INTEGER PRIMARY KEY, asset_id INTEGER, price_date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL, currency TEXT, source TEXT);
        CREATE TABLE expense_owner_rules (id INTEGER PRIMARY KEY, keyword TEXT, owner TEXT, created_at TEXT);
        INSERT INTO accounts VALUES (1, 'Old Broker', 'broker', 'EUR', NULL, NULL, 0, NULL),
                                    (2, 'Old Bank', 'bank', 'EUR', NULL, NULL, 0, NULL),
                                    (3, 'Maison', 'real_estate', 'EUR', NULL, NULL, 0, NULL),
                                    (4, 'Old Pension', 'pension', 'CHF', NULL, NULL, 0, NULL),
                                    (5, 'Nothing here', 'other', 'EUR', NULL, NULL, 0, NULL),
                                    (6, 'Coins', 'crypto', 'EUR', NULL, NULL, 0, NULL);
        INSERT INTO assets VALUES (1, 'IWDA', 'IE00B4L5Y983', 'iShares Core MSCI World', 'etf', 'EUR', 'IWDA.AS', NULL, NULL),
                                  (2, 'CASH_EUR', NULL, 'Cash EUR', 'cash', 'EUR', NULL, NULL, NULL),
                                  (3, 'MAISON-FR', NULL, 'House', 'real_estate', 'EUR', NULL, NULL, NULL),
                                  (4, 'CASH_CHF', NULL, 'Cash CHF', 'cash', 'CHF', NULL, NULL, NULL),
                                  (5, 'FCNTX', NULL, 'Fidelity Contrafund', 'etf', 'USD', 'FCNTX', NULL, NULL),
                                  (6, 'BTCEUR', NULL, 'Bitcoin', 'crypto', 'EUR', 'BTC-EUR', NULL, NULL),
                                  (7, 'DCAM', NULL, 'Amundi PEA Monde', 'etf', 'EUR', 'DCAM.PA', NULL, NULL);
        INSERT INTO transactions (id, account_id, asset_id, txn_date, type, quantity, price, currency, amount, fee, description, category, source, external_id) VALUES
            (1, 1, 1, '2025-01-10', 'buy', 10, 80.0, 'EUR', -802.0, -2.0, 'Kauf IWDA', 'investment', 'degiro_csv:Account.csv', 'deg_h:aaaa'),
            (2, 1, 1, '2025-06-10', 'buy', 5, 90.0, 'EUR', -450.0, 0, 'Kauf IWDA', 'investment', 'degiro_csv:Account.csv', 'deg_h:bbbb'),
            (3, 1, 1, '2025-07-01', 'dividend', 15, 0.5, 'EUR', 7.5, 0, 'Dividende IWDA Anzahl: 15', 'interest', 'degiro_csv:Account.csv', 'deg_h:cccc'),
            (4, 1, NULL, '2025-08-01', 'buy', 100, 6.0, 'EUR', -600.0, 0, 'BUY 100.0 DCAM:xpar', 'investment', 'saxo', 'saxo:trade:1'),
            (5, 1, NULL, '2025-08-02', 'sell', -40, 6.5, 'EUR', 260.0, 0, 'SELL -40.0 DCAM:xpar', 'investment', 'saxo', 'saxo:trade:2'),
            (6, 2, NULL, '2025-03-01', 'deposit', NULL, NULL, 'EUR', 3000.0, 0, 'Salaire', 'income', 'enablebanking:bank:1', 'eb:x:2025-03-01:3000.00:R1'),
            (7, 2, NULL, '2025-03-05', 'withdrawal', NULL, NULL, 'EUR', -60.0, 0, 'Simracing shop', 'simracing', 'enablebanking:bank:1', 'eb:x:2025-03-05:60.00:R2'),
            (8, 2, NULL, '2025-03-06', 'withdrawal', NULL, NULL, 'EUR', -12.0, 0, 'Assurance auto', 'assurance', 'enablebanking:bank:1', 'eb:x:2025-03-06:12.00:R3'),
            (9, 6, 6, '2026-02-01', 'buy', 0.01, 60000.0, 'EUR', -600.0, -1.2, 'Buy BTC on Kraken', 'investment', 'kraken_api', 'TXID-1');
        INSERT INTO holdings (account_id, asset_id, quantity, avg_cost, cost_currency, updated_at) VALUES
            (1, 1, 15, 83.33, 'EUR', '2026-09-13 10:00:00'), (1, 7, 60, 6.0, 'EUR', '2026-09-13 10:00:00'),
            (1, 5, 100, 12.0, 'USD', '2026-06-11 10:00:00'),
            (2, 2, 2928.0, 1.0, 'EUR', '2026-09-13 10:00:00'), (3, 3, 1, 361000.0, 'EUR', '2026-09-13 10:00:00'),
            (4, 4, 500000.0, 1.0, 'CHF', '2026-09-13 10:00:00'), (6, 6, 0.01, 60000.0, 'EUR', '2026-09-13 10:00:00'),
            (6, 2, 250.0, 1.0, 'EUR', '2026-09-14 07:00:00');
        INSERT INTO snapshots VALUES (1, '2026-09-12', 930000, 'refresh'), (2, '2026-09-13', 940000, 'refresh'), (3, '2026-05-01', 900000, 'excel'),
                                     (4, '2026-06-01', 910000, 'interpolated'), (5, '2026-09-12', 1, 'manual');
        INSERT INTO snapshot_lines (snapshot_id, account_id, asset_id, quantity, price, value_eur, currency) VALUES
            (1, 1, 1, 15, 100.0, 1500.0, 'EUR'), (1, 2, 2, 2900.0, 1.0, 2900.0, 'EUR'), (1, 3, 3, 1, 410000.0, 410000.0, 'EUR'), (1, 4, 4, 499000.0, 1.0, 520000.0, 'CHF'),
            (2, 1, 1, 15, 101.0, 1515.0, 'EUR'), (2, 2, 2, 2928.0, 1.0, 2928.0, 'EUR'), (2, 3, 3, 1, 416233.0, 416233.0, 'EUR'), (2, 4, 4, 500000.0, 1.0, 521000.0, 'CHF'),
            (5, 1, 1, 15, 100.0, 1500.0, 'EUR'), (5, 2, 2, 2900.0, 1.0, 2900.0, 'EUR'), (5, 3, 3, 1, 410000.0, 410000.0, 'EUR'), (5, 4, 4, 499000.0, 1.0, 520000.0, 'CHF');
        INSERT INTO prices (asset_id, price_date, close, currency) VALUES (1, '2026-09-12', 100.0, 'EUR'), (1, '2026-09-13', 101.0, 'EUR');
        INSERT INTO expense_owner_rules VALUES (1, 'simracing', 'thomas', '2026-01-01');
    """)
    c.commit(); c.close()
    return path.read_bytes()

blob = fp_database()
check("the file is recognised as the old app's", migrate.is_planner_db(blob), True)
check("...and a CSV is not", migrate.is_planner_db(b"date,amount\n"), False)
# An account of the same name here is offered as the target.
r = c.post("/accounts/new", data={"name": "Old Broker", "type": "broker", "currency": "EUR"})
old_broker_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
# One of the old rows is already here — a Degiro file imported into
# this app before the move — so it must neither be written twice nor
# make the holding come out short or double.
with db.get_conn() as conn:
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, isin, quantity, price, external_id) "
                 "VALUES (?, '2025-01-10', 'Kauf IWDA', -802.0, 'EUR', 'buy', 'IE00B4L5Y983', 10, 80.0, 'deg_h:aaaa')", (old_broker_id,))
plan = migrate.read(blob)
check("a row already here is seen as such", (plan["totals"]["duplicates"], {a["name"]: a["duplicates"] for a in plan["accounts"]}["Old Broker"]), (1, 1))
by_name = {a["name"]: a for a in plan["accounts"]}
check("the plan lists every account with what it becomes",
      {a["name"]: a["type"] for a in plan["accounts"]},
      {"Old Broker": "broker", "Old Bank": "bank", "Maison": "property", "Old Pension": "pension", "Nothing here": "other", "Coins": "broker"})
check("...an account of the same name is the proposed target", by_name["Old Broker"]["target"], old_broker_id)
check("...an empty one is left out", by_name["Nothing here"].get("skip"), True)
check("...and the rows are counted", (by_name["Old Broker"]["rows"], by_name["Old Bank"]["rows"], by_name["Old Bank"]["first"]), (5, 3, "2025-03-01"))
tx = {t["external_id"]: t for t in plan["transactions"]}
check("a Kraken trade id gets this app's prefix", "kraken:trade:TXID-1" in tx, True)
check("...whether it came through the API or a Kraken CSV", migrate._external_id("TUT7MA-K67YX-X6Z4TJ", "crypto_csv:kraken", 1), "kraken:trade:TUT7MA-K67YX-X6Z4TJ")
check("...and a Finary UUID stays what it is", migrate._external_id("019c13b6-064f-72a1-8cdf-a82bc96247f1", "crypto_csv:finary", 1), "019c13b6-064f-72a1-8cdf-a82bc96247f1")
check("a Saxo id is the same in both apps", "saxo:trade:1" in tx, True)
check("a trade the old app did not link to its security is linked by its text",
      (tx["saxo:trade:1"]["isin"], tx["saxo:trade:2"]["isin"], tx["saxo:trade:2"]["quantity"]), ("SYM:DCAM", "SYM:DCAM", -40.0))
check("a coin is keyed the way this app keys it", tx["kraken:trade:TXID-1"]["isin"], "CRYPTO:BTC")
check("a dividend's quantity is the position it was paid on, not units", tx["deg_h:cccc"]["quantity"], None)
check("interest is this app's income category, a foreign slug is created",
      (tx["deg_h:cccc"]["category"], tx["eb:x:2025-03-06:12.00:R3"]["category"], plan["categories"]),
      ("capital_income", "insurance", {"simracing": "Simracing"}))
ops = {(o["account"], o["isin"]): o for o in plan["openings"]}
check("a holding the ledger does not explain gets an opening row",
      (round(ops[("Old Broker", "SYM:FCNTX")]["quantity"], 2), ops[("Old Broker", "SYM:FCNTX")]["txn_date"], ops[("Old Broker", "SYM:FCNTX")]["price"]), (100.0, "2026-06-11", 12.0))
check("...and one the rows add up to does not", ("Old Broker", "IE00B4L5Y983") in ops, False)
# The openings follow the choice of account: into the account that
# already has the row, nothing is missing; into a new one, the row
# left behind is made up by an opening.
ops_new = {(o["account"], o["isin"]): o for o in migrate.openings(plan, {1: None})}
check("the openings are worked out against the chosen account",
      (("Old Broker", "IE00B4L5Y983") in ops_new, round(ops_new[("Old Broker", "IE00B4L5Y983")]["quantity"], 4) if ("Old Broker", "IE00B4L5Y983") in ops_new else None), (True, 10.0))
bal = {(b["fp_account"], b["as_of"]): b for b in plan["balances"]}
check("the house is a balance of its snapshot value, not a holding at its price",
      (bal[(3, "2026-09-13")]["amount"], any(t["isin"] == "SYM:MAISON-FR" for t in plan["transactions"]), any(o["isin"] == "SYM:MAISON-FR" for o in plan["openings"])), (416233.0, False, False))
check("the pension is a reading in its own currency", (bal[(4, "2026-09-12")]["amount"], bal[(4, "2026-09-12")]["currency"]), (499000.0, "CHF"))
check("a day with two snapshots is read once, not summed", bal[(2, "2026-09-12")]["amount"], 2900.0)
check("the net worth the old app recorded before it kept lines comes along, up to the day the lines begin",
      [(x["as_of"], x["amount"]) for x in plan["net_worth"]], [("2026-05-01", 900000.0), ("2026-06-01", 910000.0)])
check("the bank's cash is a reading per snapshot day", (bal[(2, "2026-09-12")]["amount"], bal[(2, "2026-09-13")]["amount"]), (2900.0, 2928.0))
check("today's cash from the holdings table where no snapshot has the day", bal[(6, "2026-09-14")]["amount"], 250.0)
check("what does not cross is said", any("expense owner rules" in n for n in plan["notes"]) and any("days of net worth" in n for n in plan["notes"]), True)

# Through the page: upload, look, confirm.
r = c.post("/move-in", data={"file": (io.BytesIO(b"not a database"), "wealth.db")}, content_type="multipart/form-data", follow_redirects=True)
check("a file that is not the old app's database is refused", b"not a Financial Planner database" in r.data, True)
r = c.post("/move-in", data={"file": (io.BytesIO(blob), "wealth.db")}, content_type="multipart/form-data")
check("the plan page shows the accounts and the openings", (r.status_code, b"Old Pension" in r.data, b"Fidelity Contrafund" in r.data, b"Simracing" in r.data), (200, True, True, True))
tok = re.search(rb'name="token" value="([^"]+)"', r.data).group(1).decode()
form = {"token": tok, "target_1": str(old_broker_id)}
r = c.post("/move-in", data=form, follow_redirects=True)
check("confirming writes it", b"Moved in" in r.data, True)
with db.get_conn() as conn:
    names = {r_["name"]: dict(r_) for r_ in conn.execute("SELECT * FROM accounts")}
    n_broker = conn.execute("SELECT COUNT(*) n FROM accounts WHERE name = 'Old Broker'").fetchone()["n"]
    rows = [dict(r_) for r_ in conn.execute("SELECT * FROM transactions WHERE source LIKE 'financial_planner%' ORDER BY txn_date, id")]
    imps = conn.execute("SELECT COUNT(*) n FROM imports WHERE source = 'financial_planner'").fetchone()["n"]
    secs = {r_["isin"]: r_ for r_ in conn.execute("SELECT * FROM securities WHERE isin IN ('SYM:FCNTX', 'CRYPTO:BTC', 'IE00B4L5Y983')")}
check("the chosen account was used, the others created, the empty one not",
      (n_broker, "Old Bank" in names, "Maison" in names, "Nothing here" in names), (1, True, True, False))
check("...with their types", (names["Maison"]["type"], names["Old Pension"]["type"], names["Coins"]["type"]), ("property", "pension", "broker"))
check("every row not already here and every opening is written, each account with rows as one import", (len(rows), imps), (8 + 1, 3))
check("the symbols come along as the user's own", (secs["SYM:FCNTX"]["symbol"], secs["SYM:FCNTX"]["symbol_source"], secs["CRYPTO:BTC"]["symbol"]), ("FCNTX", "manual", "BTC-EUR"))
pos = {p_["isin"]: p_["quantity"] for p_ in importers.positions(old_broker_id)}
check("the holdings are the old app's", ({k: round(v, 4) for k, v in pos.items()}), {"IE00B4L5Y983": 15.0, "SYM:DCAM": 60.0, "SYM:FCNTX": 100.0})
check("a ledger under ids this app would not produce is marked as on record",
      (names["Old Bank"]["ledger_until"], names["Old Broker"]["ledger_until"], names["Coins"]["ledger_until"]), ("2025-03-06", "2025-08-02", None))
sm = ov.summary("EUR")
check("the house and the pension are in the net worth as other assets", round(sm["assets_by_type"]["property"]), 416233)
hist = history.series("EUR", None, "all", today=date(2026, 9, 13))
rec = [p_ for p_ in hist["points"] if p_.get("recorded")]
own = [p_ for p_ in hist["points"] if p_["date"] >= "2026-09-12" and p_["net_worth"] is not None]
check("the history line uses the recorded net worth before the readings, and its own arithmetic from them on",
      (bool(rec), {p_["net_worth"] for p_ in rec} <= {900000.0, 910000.0}, all(not p_.get("recorded") for p_ in own), bool(own)), (True, True, True, True))
check("...and reaches back to the first recorded day", hist["first_date"] <= "2026-05-01", True)
check("...the move wrote down the day its readings cover every account", db.get_state("records_from"), "2026-09-12")
# A doubled day from the move as it was in 0.42 — twice the day before
# and twice the day after — is halved once on start.
with db.get_conn() as conn:
    pk = names["Old Pension"]["id"]
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) VALUES (?, 998000, 'CHF', 'financial_planner', '2026-09-11'), (?, 499500, 'CHF', 'financial_planner', '2026-09-10')", (pk, pk))
    conn.execute("DELETE FROM app_state WHERE key = 'fp_double_snapshot_day'")
db.init_db()
with db.get_conn() as conn:
    fixed = conn.execute("SELECT amount FROM balances WHERE account_id = ? AND as_of = '2026-09-11'", (pk,)).fetchone()["amount"]
    kept = conn.execute("SELECT amount FROM balances WHERE account_id = ? AND as_of = '2026-09-12' ORDER BY id LIMIT 1", (pk,)).fetchone()["amount"]
check("a reading twice its neighbours from the move is halved on start, its neighbours left alone", (fixed, kept), (499000.0, 499000.0))
r = c.get(f"/accounts/{names['Old Bank']['id']}/edit")
check("the account page shows how far the ledger is on record", b"Ledger on record until" in r.data, True)

# A statement covering the days already on record is left alone; one
# reaching past them adds only what is new.
r = upload(old_broker_id, fixtures.DEGIRO_CSV)
check("an export over the recorded span is not booked again", b"0 new" in r.data or b"already had" in r.data, True)
with db.get_conn() as conn:
    conn.execute("UPDATE accounts SET ledger_until = NULL WHERE id = ?", (old_broker_id,))
    conn.execute("DELETE FROM transactions WHERE account_id = ?", (old_broker_id,))
    conn.execute("DELETE FROM accounts WHERE name IN ('Old Broker', 'Old Bank', 'Maison', 'Old Pension', 'Coins')")
    conn.execute("DELETE FROM net_worth_readings")
    conn.execute("DELETE FROM app_state WHERE key = 'records_from'")
cat.delete_category("simracing")

# ---------------------------------------------------------------------------
print("\n48. Pulling statements from a document archive")
# ---------------------------------------------------------------------------
from app import archive                                               # noqa: E402
import urllib.parse as _up                                            # noqa: E402

# A Paperless-ngx that answers from memory: four documents under two
# tags. One is a statement the readers know, one a scan with no text
# but Paperless's OCR of a known layout, one a letter, one a CSV in the
# app's own template.
BLANK_PDF = fixtures.pdf_from_text("")
ARCHIVE_DOCS = {
    11: {"title": "DKB Kauf", "created": "2026-03-12", "tags": ["bank", "depot"],
         "file": ("kauf.pdf", fixtures.pdf_from_text(fixtures.DKB_PDF_KAUF.replace("611223/44.00", "999001/11.00"))), "content": "some ocr"},
    12: {"title": "DKB Verkauf (scan)", "created": "2026-04-20", "tags": ["bank", "depot"],
         "file": ("scan.pdf", BLANK_PDF), "content": fixtures.DKB_PDF_VERKAUF.replace("622334/55.00", "999002/22.00")},
    13: {"title": "Letter", "created": "2026-05-01", "tags": ["bank", "depot"],
         "file": ("letter.pdf", fixtures.pdf_from_text("Dear customer, hello.")), "content": "Dear customer"},
    14: {"title": "Own CSV", "created": "2026-06-01", "tags": ["bank", "giro"],
         "file": ("mine.csv", b"date,amount,description,id\n2026-06-01,-42.00,Groceries,g-1\n"), "content": ""},
}
ARCHIVE_TAGS = {1: "bank", 2: "depot", 3: "giro"}
archive_calls = []


def fake_archive(method, full, headers, body, token="tok-1"):
    archive_calls.append(full)
    if headers.get("Authorization") != f"Token {token}":
        return 401, {}, b'{"detail":"Invalid token."}'
    u = _up.urlparse(full); q = _up.parse_qs(u.query)
    def js(obj): return 200, {"Content-Type": "application/json"}, json.dumps(obj).encode()
    if u.path == "/api/tags/":
        return js({"count": 3, "next": None, "results": [{"id": i, "name": n} for i, n in ARCHIVE_TAGS.items()]})
    if u.path == "/api/correspondents/":
        return js({"count": 1, "next": None, "results": [{"id": 7, "name": "DKB"}]})
    if u.path == "/api/documents/":
        want = {int(i) for i in q.get("tags__id__all", [""])[0].split(",") if i}
        rows = [{"id": i, "title": d["title"], "created": d["created"]} for i, d in ARCHIVE_DOCS.items()
                if all(ARCHIVE_TAGS[t] in d["tags"] for t in want)]
        return js({"count": len(rows), "next": None, "results": rows})
    m = re.match(r"^/api/documents/(\d+)/(download/)?$", u.path)
    if m:
        d = ARCHIVE_DOCS[int(m.group(1))]
        if m.group(2):
            # Paperless negotiates content on the download: anything but
            # */* (or the file's own type) is a 406, as a real one showed.
            if headers.get("Accept") not in ("*/*", "application/pdf"):
                return 406, {}, b'{"detail":"Could not satisfy the request Accept header."}'
            return 200, {"Content-Disposition": f'attachment; filename="{d["file"][0]}"'}, d["file"][1]
        return js({"id": int(m.group(1)), "content": d["content"]})
    return 404, {}, b"{}"


check("nothing is set up to begin with", archive.configured(), False)
r = c.post("/settings", data={"form": "archive_save", "archive_url": "paperless.lan", "archive_token": "x"},
           follow_redirects=True)
check("an address without a scheme is refused", b"http://" in r.data, True)
archive.save("http://paperless.lan:8000/", "tok-1")
check("saved: the address in settings, the token beside the keys",
      (settings.load()["archive_url"], (settings.SECRETS_DIR / archive.TOKEN_FILE).read_text()),
      ("http://paperless.lan:8000", "tok-1"))
check("...the token file is private",
      oct((settings.SECRETS_DIR / archive.TOKEN_FILE).stat().st_mode & 0o777), "0o600")
info = archive.check(transport=fake_archive)
check("a check reports what is there", (info["documents"], info["tags"]), (4, ["bank", "depot", "giro"]))
bad = lambda m, u, h, b: fake_archive(m, u, h, b, token="other")            # noqa: E731
try:
    archive.check(transport=bad); check("a refused token is an error", False, True)
except archive.ArchiveError as exc:
    check("a refused token says so", "refused the token" in str(exc), True)

with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Archive depot', 'broker', 'EUR')")
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Archive giro', 'bank', 'EUR')")
    dep = conn.execute("SELECT id FROM accounts WHERE name = 'Archive depot'").fetchone()["id"]
    gir = conn.execute("SELECT id FROM accounts WHERE name = 'Archive giro'").fetchone()["id"]
r = c.get(f"/accounts/{dep}/edit")
check("the account form offers the archive fields once it is set up", b"archive_tags" in r.data, True)
c.post(f"/accounts/{dep}/edit", data={"name": "Archive depot", "type": "broker", "currency": "EUR",
                                      "archive_tags": " bank , depot "})
c.post(f"/accounts/{gir}/edit", data={"name": "Archive giro", "type": "bank", "currency": "EUR",
                                      "archive_tags": "bank, giro", "archive_correspondent": "DKB"})
check("the filter is kept, tidied", archive.filter_for(dep)["tags"], "bank, depot")

results = {r["account"]: r for r in archive.pull(transport=fake_archive)}
d = results["Archive depot"]
check("the depot lists the three documents under its tags", (d["listed"], d["new"], d["error"]), (3, 3, None))
check("...a known statement is read", d["imported"] >= 1, True)
check("...a scan is read through the archive's OCR text", d["imported"], 2)
check("...and the letter is not", d["unread"], 1)
check("the giro gets the CSV in the app's template", (results["Archive giro"]["imported"], results["Archive giro"]["inserted"]), (1, 1))
with db.get_conn() as conn:
    kinds = sorted(r["kind"] for r in conn.execute("SELECT kind FROM transactions WHERE account_id = ?", (dep,)))
    recorded = {r["doc_id"]: r["result"] for r in conn.execute("SELECT doc_id, result FROM archive_documents")}
check("the statements landed as trades", kinds, ["buy", "sell"])
check("every document is on record with what became of it",
      recorded, {11: "imported", 12: "imported", 13: "unread", 14: "imported"})
with db.get_conn() as conn:
    letter_note = conn.execute("SELECT note FROM archive_documents WHERE doc_id = 13").fetchone()["note"]
check("...and the letter's note says why", letter_note, "not recognised")

n_calls = len(archive_calls)
again = {r["account"]: r for r in archive.pull(transport=fake_archive)}
check("a second pull fetches nothing", (again["Archive depot"]["new"], again["Archive giro"]["new"]), (0, 0))
check("...only the listings are asked for", len(archive_calls) - n_calls <= 6, True)
check("retrying forgets the unread ones only", archive.retry_unread(), 1)
check("...so the next pull tries the letter again, and only it",
      {r["account"]: r["new"] for r in archive.pull(transport=fake_archive)}, {"Archive depot": 1, "Archive giro": 0})

archive.set_filter(gir, "bank, nosuchtag", "", "")
bad_tag = {r["account"]: r for r in archive.pull(transport=fake_archive)}
check("a tag the archive does not have fails that account and names the tag",
      "nosuchtag" in (bad_tag["Archive giro"]["error"] or ""), True)
check("...while the other account is still pulled", bad_tag["Archive depot"]["error"], None)
st = archive.describe()
check("Settings sees the filters with their tallies",
      [(f["account"], f.get("imported", 0), f.get("unread", 0)) for f in st["filters"]],
      [("Archive depot", 2, 1), ("Archive giro", 1, 0)])
check("...and the last pull", st["last"]["results"][0]["account"], "Archive depot")
r = c.get("/settings/banks")
check("the Settings card lists the document no reader understood", b"Letter" in r.data, True)
check("...with a link back into the archive", b"/documents/13/details" in r.data, True)
archive.set_filter(gir, "", "", "")
check("all three blank means the account pulls nothing", archive.filter_for(gir), None)
r = c.post("/settings", data={"form": "archive_forget"}, follow_redirects=True)
with db.get_conn() as conn:
    kept = conn.execute("SELECT COUNT(*) AS n FROM transactions WHERE account_id = ?", (dep,)).fetchone()["n"]
check("forgetting the archive keeps what was imported", (archive.configured(), kept), (False, 2))
c.post(f"/accounts/{dep}/delete", data={"confirm": "Archive depot"})
c.post(f"/accounts/{gir}/delete", data={"confirm": "Archive giro"})

# ---------------------------------------------------------------------------
print("\n49. The weekly e-mail")
# ---------------------------------------------------------------------------
from app import report                                                # noqa: E402

# A broker with a holding priced today and a week ago, a dividend in
# the last month, and cash — the ingredients of one account section.
with db.get_conn() as conn:
    conn.execute("INSERT INTO accounts (name, type, currency) VALUES ('Mail broker', 'broker', 'EUR')")
    mb = conn.execute("SELECT id FROM accounts WHERE name = 'Mail broker'").fetchone()["id"]
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, "
                 "isin, security_name, quantity, price, external_id) VALUES "
                 "(?, '2026-08-01', 'buy', -1000, 'EUR', 'buy', 'XX0000000009', 'Mail Fund', 10, 100, 'mail-1')", (mb,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, "
                 "isin, security_name, external_id) VALUES "
                 "(?, '2026-09-10', 'Dividend', 12.5, 'EUR', 'dividend', 'XX0000000009', 'Mail Fund', 'mail-2')", (mb,))
    conn.execute("INSERT INTO transactions (account_id, txn_date, description, amount, currency, kind, "
                 "isin, security_name, external_id) VALUES "
                 "(?, '2025-01-10', 'Dividend', 7.5, 'EUR', 'dividend', 'XX0000000009', 'Mail Fund', 'mail-3')", (mb,))
    conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                 "VALUES (?, 250, 'EUR', 'manual', '2026-09-18')", (mb,))
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('XX0000000009', '2026-09-11', 110, 'EUR')")
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('XX0000000009', '2026-09-18', 121, 'EUR')")
    conn.execute("INSERT OR REPLACE INTO securities (isin, symbol, name, symbol_source) VALUES ('XX0000000009', 'MAIL', 'Mail Fund', 'manual')")
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('BENCH:EUNL.DE', '2026-09-11', 100, 'EUR')")
    conn.execute("INSERT OR REPLACE INTO prices (isin, as_of, price, currency) VALUES ('BENCH:EUNL.DE', '2026-09-18', 102, 'EUR')")

rep = report.build("EUR", today=_date(2026, 9, 18))
check("the report spans a week", (rep["since"], rep["as_of"]), ("2026-09-11", "2026-09-18"))
sec = next(x for x in rep["accounts"] if x["name"] == "Mail broker")
fund = sec["holdings"][0]
check("a holding is valued at today's price, in the account's currency", fund["value"], 1210.0)
check("...its week is the price move only: 10 × (121 − 110)", (fund["change_7d"], round(fund["pct_7d"], 4)), (110.0, 0.1))
check("...and the gain since purchase is value less cost", fund["gain"], 210.0)
check("the account adds the cash", sec["value"], 1210.0 + 250.0)
check("...moves by what its holdings moved", (sec["change_7d"], round(sec["pct_7d"], 4)), (110.0, 0.1))
check("dividends of the trailing year are summed", sec["dividends_12m"], 12.5)
check("...the last thirty days listed", [d["amount"] for d in sec["dividends_recent"]], [12.5])
check("...and older ones are not in the year", 7.5 in [d["amount"] for d in sec["dividends_recent"]], False)
check("the indices the app tracks are included",
      [(b["label"], round(b["pct_7d"], 4)) for b in rep["benchmarks"]], [("MSCI World", 0.02)])
check("the net worth is the overview's", rep["net_worth"], overview.summary("EUR")["net_worth"])
check("...measured against the line a week ago", rep["net_worth_then"] is not None, True)

text = report.render_text(rep)
html = report.render_html(rep)
check("the text version carries the account", "== Mail broker" in text and "Mail Fund" in text, True)
check("...and the week's move, signed", "+110" in text.replace("\xa0", " "), True)
check("the HTML version is a full mail", ("<h1" in html, "Mail broker" in html, "MSCI World" in html), (True, True, True))
check("...with nothing unescaped", "<script" not in html, True)
check("the subject names the day and the change", report.subject(rep).startswith("Weekly report "), True)

# When to send: on the chosen weekday, once per ISO week, catching up.
cfg = {"report_enabled": True, "report_weekday": 2}
check("due on the day", report.due(_date(2026, 9, 16), cfg, None), True)              # a Wednesday
check("not before it", report.due(_date(2026, 9, 14), cfg, None), False)              # the Monday of that week
check("not twice in a week", report.due(_date(2026, 9, 17), cfg, "2026-W38"), False)
check("caught up later in the week if the day was missed", report.due(_date(2026, 9, 19), cfg, "2026-W37"), True)
check("off means off", report.due(_date(2026, 9, 14), {"report_enabled": False}, None), False)

# Sending, through a fake SMTP.
mails = []
fake_smtp = lambda host, port, user, password, sender, to, body: mails.append(   # noqa: E731
    {"host": host, "port": port, "user": user, "password": password, "sender": sender, "to": to, "body": body})
try:
    report.send("x", "<p>x</p>", "x", smtp=fake_smtp); check("unset up, sending refuses", False, True)
except report.NotConfigured:
    check("unset up, sending refuses and says what is missing", True, True)
r = c.post("/settings/assistants", data={"form": "report_save", "report_enabled": "1", "smtp_host": "",
                                        "report_to": "me@example.com"}, follow_redirects=True)
check("switching it on without a server is refused", b"server and at least one recipient" in r.data, True)
r = c.post("/settings/assistants", data={"form": "report_save", "report_enabled": "1", "smtp_host": "smtp.example.com",
                                        "smtp_port": "587", "smtp_user": "me@example.com", "smtp_password": "s3cret",
                                        "report_to": "me@example.com; other@example.com", "report_weekday": "4"},
           follow_redirects=True)
check("the settings are saved", (settings.load()["smtp_host"], settings.load()["report_to"], settings.load()["report_weekday"]),
      ("smtp.example.com", "me@example.com, other@example.com", 4))
check("...the password beside the keys, private",
      oct((settings.SECRETS_DIR / report.PASSWORD_FILE).stat().st_mode & 0o777), "0o600")
check("...and the card says when", b"every Friday" in r.data, True)
info = report.send_report("EUR", today=_date(2026, 9, 18), smtp=fake_smtp)
check("a report goes to every recipient", (info["to"], mails[-1]["to"]), (["me@example.com", "other@example.com"],) * 2)
check("...with the saved credentials", (mails[-1]["host"], mails[-1]["port"], mails[-1]["password"]), ("smtp.example.com", 587, "s3cret"))
check("...as text and HTML", ("text/plain" in mails[-1]["body"] and "text/html" in mails[-1]["body"]), True)
check("...and the week is marked sent", db.get_state(report.STATE_KEY), "2026-W38")
check("so the same week is not sent again", report.send_if_due("EUR", today=_date(2026, 9, 18), smtp=fake_smtp), None)
check("the preview renders in the browser", (c.get("/report/preview").status_code, b"Mail broker" in c.get("/report/preview").data), (200, True))
r = c.post("/settings/assistants", data={"form": "report_save", "smtp_host": "smtp.example.com", "smtp_port": "465",
                                        "report_to": "me@example.com", "report_weekday": "0"}, follow_redirects=True)
check("a blank password keeps the saved one", (settings.SECRETS_DIR / report.PASSWORD_FILE).read_text(), "s3cret")
check("...and an unticked box switches it off", settings.load()["report_enabled"], False)
c.post("/settings/assistants", data={"form": "report_forget"})
check("forgetting clears the settings and the password",
      (settings.load().get("smtp_host"), (settings.SECRETS_DIR / report.PASSWORD_FILE).exists()), (None, False))
c.post(f"/accounts/{mb}/delete", data={"confirm": "Mail broker"})

# ---------------------------------------------------------------------------
print("\n50. Statements read by spec: comdirect, ING, Consorsbank")
# ---------------------------------------------------------------------------
from app.importers import statement                                   # noqa: E402
from app.importers.pdf import READERS                                 # noqa: E402

by_slug = {r.SLUG: r for r in READERS}
check("the spec readers are importers like any other",
      all(hasattr(r, "matches") and hasattr(r, "parse") and r.LABEL for r in READERS), True)
check("...listed among the PDF importers", all(r in importers.PDF_IMPORTERS for r in READERS), True)

k = by_slug["comdirect_pdf"].parse(fixtures.COMDIRECT_KAUF)
check("a comdirect purchase is read", (len(k.rows), k.problems), (1, []))
r = k.rows[0]
check("...as a buy on the Geschäftstag", (r.kind, r.txn_date), ("buy", "2026-03-12"))
check("...for what left the account", r.amount, -3512.40)
check("...`St. 2.000` is two thousand units", r.quantity, 2000.0)
check("...at the price on the paper", r.price, 1.75)
check("...with every fee line summed and the Summe not counted twice", r.fee, 12.40)
check("...and the ISIN and name from their two lines",
      (r.isin, r.security_name), ("US0000000001", "Example Holdings Inc. Registered Shares DL -,01"))

d = by_slug["comdirect_pdf"].parse(fixtures.COMDIRECT_DIVIDENDE)
check("a comdirect dividend with letter-spaced lines is read", (len(d.rows), d.problems), (1, []))
check("...as a dividend for what was credited, on the Valuta", (d.rows[0].kind, d.rows[0].amount, d.rows[0].txn_date),
      ("dividend", 118.06, "2026-05-14"))
check("...with the ISIN squeezed back together", d.rows[0].isin, "US0000000001")
check("...and the dollar withholding turned into euros at the paper's rate", d.rows[0].tax, round(22.50 / 1.08, 2))

v = by_slug["ing_pdf"].parse(fixtures.ING_VERKAUF)
check("an ING sale is read", (len(v.rows), v.problems), (1, []))
check("...as a sell with negative units", (v.rows[0].kind, v.rows[0].quantity), ("sell", -500.0))
check("...for the Endbetrag", v.rows[0].amount, 1110.12)
check("...fees and taxes each summed", (v.rows[0].fee, v.rows[0].tax), (6.80, 83.08))

c = by_slug["consorsbank_pdf"].parse(fixtures.CONSORSBANK_KAUF)
check("a Consorsbank savings-plan purchase is read", (len(c.rows), c.problems), (1, []))
check("...with units, price and the fee", (c.rows[0].quantity, c.rows[0].price, c.rows[0].fee), (2.0921, 95.6, 0.49))
check("...for the amount charged", c.rows[0].amount, -200.49)

check("a statement from another bank is not claimed",
      by_slug["ing_pdf"].matches([], fixtures.COMDIRECT_KAUF), False)
check("the sniffer hands a comdirect PDF to the comdirect reader",
      importers.sniff(fixtures.pdf_from_text(fixtures.COMDIRECT_KAUF)).SLUG, "comdirect_pdf")
check("a Storno is refused by name",
      "Storno" in by_slug["comdirect_pdf"].parse("comdirect bank AG\nStorno\nWertpapierkauf\n").problems[0], True)
check("numbers: German, English and Swiss",
      (statement.parse_number("1.234,56", "de"), statement.parse_number("1,234.56", "en"),
       statement.parse_number("1'234.56", "ch"), statement.parse_number("73,16-", "de")),
      (1234.56, 1234.56, 1234.56, -73.16))
check("dates: dotted, ISO, slashed and written out",
      (statement.parse_date("12.03.2026"), statement.parse_date("2026-03-12"), statement.parse_date("12/03/2026"),
       statement.parse_date("12. März 2026")), ("2026-03-12",) * 4)

# ---------------------------------------------------------------------------
print("\n51. Statements read by spec: Trade Republic, DEGIRO")
# ---------------------------------------------------------------------------
tr = by_slug["traderepublic_pdf"]
k = tr.parse(fixtures.TRADEREPUBLIC_KAUF)
check("a Trade Republic purchase is read", (len(k.rows), k.problems), (1, []))
check("...as a buy on the execution day, for the booked amount",
      (k.rows[0].kind, k.rows[0].txn_date, k.rows[0].amount), ("buy", "2026-03-04", -1219.00))
check("...with units, price, fee and ISIN", (k.rows[0].quantity, k.rows[0].price, k.rows[0].fee, k.rows[0].isin),
      (12.0, 101.50, 1.00, "IE0000000001"))

d = tr.parse(fixtures.TRADEREPUBLIC_DIVIDENDE)
kinds = sorted((r.kind, r.amount) for r in d.rows)
check("a dividend with an Optimierung under it is two rows", len(d.rows), 2)
check("...the dividend without the credit, the credit as a tax refund of its own",
      kinds, [("dividend", 63.31), ("tax", 5.43)])

s = tr.parse(fixtures.TRADEREPUBLIC_KONTOAUSZUG)
rows = sorted((r.txn_date, r.kind, r.amount) for r in s.rows)
check("the 2024 Kontoauszug is put back together: interest, a card payment, a deposit — no trade",
      rows, [("2026-01-02", "interest", 12.30), ("2026-01-05", "withdrawal", -60.00), ("2026-01-15", "deposit", 500.00)])

g = by_slug["degiro_pdf"].parse(fixtures.DEGIRO_KONTOAUSZUG)
rows = sorted((r.kind, r.amount, r.tax) for r in g.rows)
check("a DEGIRO statement folds the tax row into the dividend and keeps the deposit",
      rows, [("deposit", 1000.00, None), ("dividend", 3.88, 0.68)])
check("...the trade fee row is not a transaction", any(r.kind == "fee" for r in g.rows), False)
check("the sniffer hands a Trade Republic PDF to its reader",
      importers.sniff(fixtures.pdf_from_text(fixtures.TRADEREPUBLIC_KAUF)).SLUG, "traderepublic_pdf")
check("every spec has a corpus name, a label and at least one doc",
      all(r.CORPUS is not None and r.LABEL and r.spec.docs for r in READERS), True)

f = by_slug["firstrade_pdf"].parse(fixtures.FIRSTRADE_BUY)
check("an American confirmation: month-first dates turned round, the settlement day, $ read as USD",
      (f.rows[0].kind, f.rows[0].txn_date, f.rows[0].amount, f.rows[0].currency, f.rows[0].quantity),
      ("buy", "2022-07-01", -371.65, "USD", 5.0))
lv = by_slug["liberty_pdf"].parse(fixtures.LIBERTY_VERKAUF)
check("Liberty's letter-spaced paper is glued back together: a sale in CHF off the Change line, the stamp duty converted",
      (lv.rows[0].kind, lv.rows[0].txn_date, lv.rows[0].amount, lv.rows[0].currency, lv.rows[0].isin, lv.rows[0].tax),
      ("sell", "2025-03-06", 283.80, "CHF", "IE00BHZRQZ17", 0.42))

# ---------------------------------------------------------------------------
print("\n52. Statement formats: CAMT.053, MT940, OFX")
# ---------------------------------------------------------------------------
c = importers.camt053.parse(fixtures.CAMT053_KONTOAUSZUG)
check("a CAMT.053 statement is recognised by its root and read", (importers.sniff(fixtures.CAMT053_KONTOAUSZUG.encode()).SLUG, c.problems), ("camt053", []))
rows = sorted((r.txn_date, r.kind, r.amount, r.counterparty) for r in c.rows)
check("...every booked entry a row, the batch as one row per leg, the pending one left out and counted",
      (rows, c.skipped),
      ([("2026-03-01", "other", -49.9, "Stadtwerke Musterstadt GmbH"), ("2026-03-03", "other", 2850.0, "Muster AG"),
        ("2026-03-15", "other", -200.0, "Verein B"), ("2026-03-15", "other", -100.0, "Verein A"),
        ("2026-03-31", "fee", -2.5, None), ("2026-03-31", "interest", 0.12, None)], 1))
check("...the purpose as description, the bank's reference as id, the closing balance taken",
      (c.rows[0].description, c.rows[0].external_id, c.closing_balance),
      ("Stromabschlag Maerz 2026", "camt:2026030100001", {"amount": 4321.16, "currency": "EUR", "as_of": "2026-03-31"}))
check("...a batch leg's id carries the leg number", sorted(r.external_id for r in c.rows if r.amount in (-100.0, -200.0)),
      ["camt:2026031500042#1", "camt:2026031500042#2"])

m = importers.mt940.parse(fixtures.MT940_KONTOAUSZUG.encode("latin-1"))
check("an MT940 statement is recognised and read", (importers.sniff(fixtures.MT940_KONTOAUSZUG.encode()).SLUG, m.problems), ("mt940", []))
check("...the :61: lines with their :86: details: SEPA purpose, counterparty, kind from the GVC words",
      [(r.txn_date, r.kind, r.amount, r.counterparty, r.description) for r in m.rows],
      [("2026-03-01", "other", -49.9, "Stadtwerke Musterstadt GmbH", "Stromabschlag Maerz 2026 [SEPA-LASTSCHRIFT]"),
       ("2026-03-03", "other", 2850.0, "Muster AG", "Gehalt Maerz [SEPA-GUTSCHRIFT]"),
       ("2026-03-31", "fee", -2.5, None, "Entgeltabrechnungsiehe Anlage [ENTGELTABSCHLUSS]"),
       ("2026-03-31", "interest", 0.12, None, "Zinsen 01.01.-31.03.2026 [ABSCHLUSS]")])
check("...the :62F: closing balance", m.closing_balance, {"amount": 4321.16, "currency": "EUR", "as_of": "2026-03-31"})
check("...ids are stable across two exports of the same period",
      [r.external_id for r in importers.mt940.parse(fixtures.MT940_KONTOAUSZUG).rows] == [r.external_id for r in m.rows], True)

dm = importers.mt940.parse(fixtures.MT940_DIALECTS)
check("the MT940 dialects all read: the envelope, 'NOV ' types, blank entry dates, a blank before the type, a wrapped amount, February 30th",
      ([(r.txn_date, r.amount, r.description[:22]) for r in dm.rows], dm.problems),
      ([("2010-07-22", -25.03, "RC AFREKENING BETALING"), ("2010-07-22", -212.39, "/PT/FT/PY/SOMETHING FO"),
        ("2010-07-22", 50.0, "Miete Juli [GUTSCHR. U"), ("2010-07-22", 30.0, "Nachzahlung [GUTSCHR. "),
        ("2010-03-01", -6.0, "Pauschalen [ENTGELTABS")], []))
check("...the wrapped Sparkasse line keeps its counterparty", dm.rows[2].counterparty, "Max Mustermann")

o = importers.ofx.parse(fixtures.OFX_BROKERAGE)
check("an OFX brokerage statement is recognised and read", (importers.sniff(fixtures.OFX_BROKERAGE.encode()).SLUG, o.problems), ("ofx", []))
check("...a buy with units, price, commission and ISIN from the SECLIST; income as a dividend with its withholding; the cash deposit once",
      [(r.txn_date, r.kind, r.amount, r.quantity, r.price, r.fee, r.tax, r.isin, r.security_name) for r in o.rows],
      [("2026-03-04", "buy", -2505.95, 10.0, 250.1, 4.95, None, "US9229087690", "Vanguard Total Stock Market ETF"),
       ("2026-03-25", "dividend", 8.2, None, None, None, 1.23, "US9229087690", "Vanguard Total Stock Market ETF"),
       ("2026-03-01", "deposit", 3000.0, None, None, None, None, None, None)])
check("...the FITID is the id, under the account", o.rows[0].external_id, "ofx:51234567:T1001")

# ---------------------------------------------------------------------------
print(f"\n{PASS} passed, {FAIL} failed   ({TMP})")
sys.exit(1 if FAIL else 0)
