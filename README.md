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
- **Broker CSV import** — Degiro and Trade Republic. The file is
  recognised by its columns, so there is nothing to choose, and
  re-importing an overlapping period is harmless.
- **Holdings**, computed from the trades in those files: what you own,
  how much, and what you put in.
- **An overview**: net worth, cash against securities, where it sits, and
  the latest activity across every account.

## What is not here yet

Net worth across accounts, currency conversion, live prices,
categorisation, charts, forecasting. See [ROADMAP.md](ROADMAP.md).

---

## Install

### Unraid

**Apps** → search **wealth-dashboard** → **Install**. Set a port, leave the
Data path on appdata, apply, open the WebUI. Nothing else is required: no
database container, no API key. The
[install guide](docs/INSTALL.md) covers backups, exposing it safely and the
redirect URL, and the container template is in
[`templates/`](templates/wealth-dashboard.xml).

### Docker, anywhere

```bash
docker run -d --name wealth-dashboard -p 8000:8000 --restart unless-stopped \
  -v /srv/wealth-dashboard:/data \
  -e TZ=Europe/Berlin \
  ghcr.io/halvar20000/wealth-dashboard:latest
```

One volume holds everything, credentials included — see *Where your data
lives* for keeping those separate.

### From source

```bash
git clone <this repo> wealth-dashboard
cd wealth-dashboard
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Then open <http://localhost:8000>.

### From source, with compose

```bash
docker compose up -d
```

The compose file builds the image locally and mounts `./data` for the
database and `./secrets` for credentials — two mounts, so a backup of the
data folder does not carry your bank key with it. Keep them on real
storage — see *Where your data lives*.

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

1. Create an account at <https://enablebanking.com> and add an application
   in the Control Panel. Environment **Production** — "restricted mode" is
   a state of a production application, not a separate environment, and it
   skips the manual review. Placeholders are fine for the privacy and
   terms URLs.

2. When it asks about the key, the easy answer is **Generate**: your
   browser downloads a file called `<application-id>.pem`.
   **That file is your private key.** There is nothing to run yourself.

   The alternative is to supply your own, in which case:

   ```bash
   openssl genrsa -out enablebanking_private.key 4096
   openssl rsa -in enablebanking_private.key -pubout -out enablebanking_public.pem
   ```

   Upload `enablebanking_public.pem` to them; keep the other one.

3. Register your **redirect URL**. Many providers only accept `https`, and
   an app on your own network cannot have one — so if `http://…/connect/callback`
   is refused, register a URL that goes nowhere (for example
   `https://example.org/callback`) and use the paste route described below.

4. **Link your bank accounts to the application** in the Control Panel
   ("Activate by linking accounts"). Skipping this is what produces "no
   accounts returned" later, which reads like a bug in this app and is not.

5. In this app: **Settings → Enable Banking**.
   - *Application ID* — shown on the application's page in the Control
     Panel. It is also the filename of the key you downloaded, minus
     `.pem`.
   - *Private key* — open `<application-id>.pem` in a text editor and paste
     everything, including the `-----BEGIN` and `-----END` lines.

   Do **not** paste `enablebanking_public.pem`, or anything you uploaded
   *to* Enable Banking — that is the public half. They have it; you need
   the other one.

   Saving checks the credentials immediately and shows which redirect URLs
   are actually registered on your application. Compare them with the
   Redirect URL field, character for character.

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

### If the bank leaves you on a page that will not load

Expected, when your redirect URL points somewhere that does not exist.
The authorisation code is in the address bar of that dead page. Copy the
whole address, open **Connect → finish by hand** (`/connect/paste`), and
paste it. It links and syncs exactly as the automatic callback does.

### Test with a sandbox first

Enable Banking flags its test banks, and this app sorts them to the top of
the bank list with a `sandbox` tag. A sandbox walks the identical path —
redirect, consent, session, balances, transactions — with the provider's
own test credentials, and creates no consent at a real bank. Use one to
find out whether your redirect URL is registered correctly, rather than
spending an authorisation you depend on.

A PSD2 consent belongs to the licensed TPP, and Enable Banking is the TPP
for every application under it. Whether a second authorisation for the
same bank sits beside your first one or replaces it is the bank's choice,
not this app's — so do not find out on an account you rely on.

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

## Versions

The version is in the header of every page and links to the changelog, rendered
inside the app. `/healthz` reports it as well.

[CHANGELOG.md](CHANGELOG.md) is the history, newest first. Releases are tagged
`vX.Y.Z` and published to GHCR under that number as well as `latest`, so
`:0.8.0` is a version you can pin and stay on. Cutting one is
[three files that must agree](docs/RELEASING.md), and the build refuses a tag
where they do not.

## Languages

English, German, French and Spanish. Set it under **Settings**, or leave it
on *Follow my browser* — a fresh install opened in a German browser is in
German before anybody goes looking for the setting.

The language also decides how numbers and dates are written: `1.234,56 EUR`
and `08.09.2026` in German, `1 234,56 EUR` and `08/09/2026` in French,
`1 234.56 EUR` and ISO dates in English. What your bank sent is left alone —
a transaction the bank described in German stays in German, in every language.

Built-in category names are translated; one you renamed is yours and is shown
exactly as you typed it. Translations are plain Python dicts in
[`app/lang/`](app/lang/) keyed on the English string, so fixing a wording or
adding a language is editing one file — there is no gettext toolchain and
nothing to compile. A missing entry falls back to English rather than
breaking the page.

## Configuration

| Variable | Default | What it is |
|---|---|---|
| `WD_DATA_DIR` | `./data` (or `/data` in a container) | Database and settings |
| `WD_SECRETS_DIR` | `$WD_DATA_DIR/secrets` | Credentials |
| `WD_HOST` | `127.0.0.1` | Bind address — `0.0.0.0` to reach it from your LAN |
| `WD_PORT` | `8000` | Port |
| `WD_SECRET_KEY` | generated and stored | Session signing key |
| `WD_BASE_CURRENCY` | `EUR` | Reporting currency |
| `WD_REDIRECT_URL` | `http://localhost:8000/connect/callback` | Where the bank sends you back |
| `TZ` | `UTC` in the image | Which day it is, for the monthly pages |

Language is a Settings-page choice only, deliberately: it has no environment
variable to be pinned by, so the picker in the app always wins.

`WD_BASE_CURRENCY` and `WD_REDIRECT_URL` are also settable in the app under
Settings — and when the variable is set, it wins on every start. Set one or
the other, not both, or a change made in Settings will appear to save and
then be overwritten by the next restart.

## Security

The app holds a complete picture of your finances. It binds to localhost
by default on purpose. Before exposing it to your LAN, set a strong
password; do not expose it to the internet without a reverse proxy and
TLS in front of it. It serves over plain HTTP through waitress — a real
server, but one with no rate limiting, no lockout and no second factor in
front of the single password, so the reverse proxy is doing the work that
matters on anything reachable from outside.

Your Enable Banking private key is the credential. Anyone who can read it
and knows your Application ID can act as your application. It is stored
0600 and belongs outside any folder you sync or back up casually.

## Tests

```bash
python3 tests/test_all.py
```

319 checks, no network, no pytest, no credentials. The whole bank flow —
JWT signing, pagination, normalisation, connect, sync, dedupe, consent
expiry — runs against a fake, so it works on a NAS with an unhelpful
Python and no internet.

## Licence

[AGPL-3.0-or-later](LICENSE). Run it, change it, share it. If you run a
modified version as a service for other people, you must offer them the
source.

## This is not financial advice

It shows you your own numbers. What you do about them is yours.
