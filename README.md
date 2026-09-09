# Wealth Dashboard

Self-hosted net worth tracking. One SQLite file on your own machine, no
account with anybody, no telemetry, no cloud component. Where a bank has
a PSD2 API it connects directly, with credentials that are yours.

> **v0.1 — early.** Today it does one loop well: create a user, create an
> account, connect it to a European bank, and pull the balance and
> transaction history. Net worth, categorisation and forecasting are not
> here yet. It is a foundation to build on rather than a finished
> dashboard, and it is honest about which is which.

---

## What works today

- **Your own login.** Username and password, stored PBKDF2-hashed in your
  own database. There is no password reset because there is nobody to
  reset it — that is the trade for having no account anywhere.
- **Accounts.** Created by hand, with a name, type and currency. An
  account exists whether or not a bank is ever connected to it, because
  most of a net worth is things no API will tell you about.
- **Bank connections via [Enable Banking](https://enablebanking.com).**
  One registration covers a few thousand banks across the EEA. Balances
  and transactions are pulled straight from the bank into your database.

## What is not here yet

Net worth across accounts, currency conversion, categorisation, charts,
CSV/PDF import, forecasting. See [ROADMAP.md](ROADMAP.md).

---

## Install

### From source

```bash
git clone <this repo> wealth-dashboard
cd wealth-dashboard
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Then open <http://localhost:8000>.

### Docker

```bash
docker compose up -d
```

The compose file mounts `./data` for the database and `./secrets` for
credentials. Keep them on real storage — see *Where your data lives*.

---

## First run

1. Open the app. It asks you to **create your user** — this is the only
   one, and it lives in your database.
2. **Add an account** (`DKB Girokonto`, say).
3. Optionally **connect it to your bank**, below.

---

## Connecting a bank — worked example: DKB

Enable Banking is the PSD2 aggregator this app speaks to. You register
your own application with them, so the bank consent is between you and
your bank; nothing passes through a server belonging to whoever wrote
this app.

### Once, to set up

1. Create an account at <https://enablebanking.com> and add an
   application in the Control Panel.
2. Generate a key pair and upload the **public** half there:

   ```bash
   openssl genrsa -out enablebanking_private.key 4096
   openssl rsa -in enablebanking_private.key -pubout -out enablebanking_public.pem
   ```

3. Register your **redirect URL** in the Control Panel. It must match the
   one in Settings *character for character*:

   ```
   http://localhost:8000/connect/callback
   ```

   If you reach the app on a LAN address instead of localhost, register
   that URL and set it in Settings. A mismatch here is the single most
   common failure, and the error the bank shows names nothing useful.

4. In the app: **Settings → Enable Banking**. Paste the Application ID
   and the **private** key. It is written to your secrets folder with
   permissions 0600 and never leaves the machine — it is only ever used
   to sign your own requests. Use **Test them** to confirm.

### Every time you connect an account

1. Open the account → **Connect a bank**.
2. Country `DE`, search `DKB`, press **Connect**.
3. You land on DKB's own login. **This app never sees your banking
   password.** You approve read-only access to the accounts you tick.
4. DKB sends you back; the app creates the session, links the account and
   pulls the history immediately.

If the consent covers several accounts, the first is linked to the
account you started from and the rest are created alongside it — two
balances added together is not a balance.

### Consent expires

PSD2 caps bank consent at **90 days** and most banks grant exactly that.
When it lapses, syncing stops until you reconnect. The account page shows
the days remaining and says so before it happens rather than after. Your
history is not affected: the connection expires, the data does not.

---

## Where your data lives

```
data/
  wealth.db              your database — this is the thing to back up
  settings.json
  secrets/               Application ID, private key, session key (0600)
```

**Back up `data/`.** RAID and snapshots protect against a disk dying, not
against a bad import or a mistaken delete.

**Do not put `wealth.db` in a folder a sync client watches.** Dropbox,
Nextcloud and iCloud will replace a SQLite journal mid-write, and the
result looks fine until the day you need it. Sync the backups, not the
live file. For the same reason, keep it off a network share — SQLite's
write-ahead log needs real filesystem locking.

**Run one instance.** SQLite allows one writer. Two copies pointed at one
file will corrupt it; the app refuses to start rather than let that
happen.

To keep credentials out of your data backups, point them elsewhere:

```bash
WD_SECRETS_DIR=/etc/wealth-dashboard/secrets python -m app
```

## Configuration

| Variable | Default | What it is |
|---|---|---|
| `WD_DATA_DIR` | `./data` (or `/data` in a container) | Database and settings |
| `WD_SECRETS_DIR` | `$WD_DATA_DIR/secrets` | Credentials |
| `WD_HOST` | `127.0.0.1` | Bind address — `0.0.0.0` to reach it from your LAN |
| `WD_PORT` | `8000` | Port |
| `WD_SECRET_KEY` | generated and stored | Session signing key |
| `WD_BASE_CURRENCY` | `EUR` | Reporting currency |

## Security

The app holds a complete picture of your finances. It binds to localhost
by default on purpose. Before exposing it to your LAN, set a strong
password; do not expose it to the internet without a reverse proxy and
TLS in front of it. The bundled server is Flask's development server —
fine for one user on a home network, not a production web server.

Your Enable Banking private key is the credential. Anyone who can read it
and knows your Application ID can act as your application. It is stored
0600 and belongs outside any folder you sync or back up casually.

## Tests

```bash
python3 tests/test_all.py
```

83 checks, no network, no pytest, no credentials. The whole bank flow —
JWT signing, pagination, normalisation, connect, sync, dedupe, consent
expiry — runs against a fake, so it works on a NAS with an unhelpful
Python and no internet.

## Licence

[AGPL-3.0-or-later](LICENSE). Run it, change it, share it. If you run a
modified version as a service for other people, you must offer them the
source.

## This is not financial advice

It shows you your own numbers. What you do about them is yours.
