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

import base64
import json
import os
import sys
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
check("a public key pasted by mistake is caught", rejected, True)

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
      b"Connect a <strong>sandbox</strong> bank first" in r.data, True)
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
check("the account list shows the balance", b"1428.55" in r.data, True)

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
print(f"\n{PASS} passed, {FAIL} failed   ({TMP})")
sys.exit(1 if FAIL else 0)
