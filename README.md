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
- **Net worth over time** — rebuilt from the readings, prices and rates as
  of each day, so it goes back as far as the records do.
- **Categories, rules and tags.** A correction becomes a rule; a rule can
  match text (anywhere, a field, a start, an exact value, a pattern), a
  direction, an amount range, an account, a kind — and file under a
  category, rename the counterparty, set the kind, add a tag. Budgets
  against the categories, cash flow by month, subscriptions detected,
  **bills** declared and marked paid, due or missed, **savings goals**
  fed by an account or by hand — and **Upcoming**: today's cash carried
  forward through the bills, the subscriptions and the salary, with the
  lowest point and the day it would cross zero, before it does.
- **Retirement outlook** per person — from their birthday and their own
  accounts to a retire age, and what the sum supports a month — and a
  **retirement plan** with the retirement in it: spending and income
  item by item, returns before and after, fees, inflation, tax; will it
  last, and if not, until when.
- **Forecast** — a monthly amount and a return, or a goal and a year, from
  today's balance; deposits and returns drawn apart, year by year.
- **The three stages** — whether what you save or what the market does is
  growing the pile: the ratio of the two, the crossover wealth, the year
  compounding takes over, and the same ratio for every year so far.
- **Daily bank sync** at a time you choose, plus a sync-everything button.
- **People** — the household's members, each account ticked for one, several
  or none of them, and a switch in the header between everyone's picture and
  one person's. Every page adds up accordingly.
- **CSV and PDF import** — Degiro and Trade Republic exports, DKB's
  Girokonto, Tagesgeld and Visa CSVs, DKB's Wertpapierabrechnung PDFs
  for the Depot, Swissquote's and Yuh's statement PDFs and Swissquote's
  trade receipts, Crédit Agricole next bank (Suisse)'s Buchungsliste
  CSV, and Finary's crypto transaction export (many at once, or a ZIP). Each file is recognised by what is in it,
  so there is nothing to choose, and re-importing what you already loaded
  is harmless. **Any other bank's CSV** is mapped once — which column is
  the date, the amount, the ISIN — and recognised by its header from then
  on. Everything can be **exported as CSV** again, filtered as the page is.
- **Entries by hand**, for the account no bank and no export describes: a
  pension, a share plan, an exchange with no CSV. Purchases, sales,
  dividends, interest, fees and tax on a broker account; deposits,
  withdrawals and the rest on any other; and a balance, dated. They land
  beside the imported rows and count the same way.
- **Holdings**, computed from the trades — imported or typed in: what you
  own, how much, and what you put in. Click one and every row behind it
  is listed and can be corrected in place; a correction survives the
  next import. A stock split is recorded once and read into every
  earlier row. Each has a chart of its performance since the first
  purchase — value against what went in, with the income drawn apart —
  and its **time-weighted and money-weighted return**; the Portfolio
  page has both for the securities as one investment, and both pages
  draw the return **against a benchmark** — the world index, the S&P,
  the DAX, the SMI, or any symbol. Sales are set
  against the cost of the units they sold — **FIFO or average cost**,
  a setting — for the realised gain per sale, per year and per holding.
- **A dividend calendar** — received month by month, and what is due in
  the next twelve from each holding's payments of the last year.
- **Allocation** — by asset class, region and buckets of your own,
  each holding classified once (guessed, then yours), with targets, the
  drift, and how to spread the next contribution so the drift shrinks.
- **Crypto** — every coin held, its price and the wallet's value over
  time, from Kraken or typed in by hand.
- **Loans and mortgages** — the terms in, the amortisation schedule out:
  what is owed today, computed, and subtracted from the net worth.
- **Saxo Bank by API** — an application of your own in Saxo's developer
  portal, one login, and every trade, dividend, fee and balance arrives
  on its own; the app keeps Saxo's short-lived login alive while it runs.
  **Kraken by API key** — a read-only key, and every fill, deposit and
  staking reward is pulled, with the balances checked against the rows.
- **Market prices** from Yahoo Finance — free, no key. Every holding is
  valued at its last market price and every total names the day; a
  holding no price could be found for is valued at your last trade, and
  the page says so. The ticker is resolved from the ISIN once and can be
  overridden under Settings.
- **An overview**: net worth, cash against securities, where it sits, and
  the latest activity across every account.
- **Share Ideas** — four ranked boards over a nightly Yahoo cache: shares
  that have fallen and are cheap, shares paying a high dividend that is
  still growing, ETFs with strong past growth at a low TER, and dividend
  ETFs paying a high yield at a low TER. Every score shows its inputs, says
  how thin its data was, and lists what it excluded and why. What you hold
  is folded in and marked. A shortlist to research, not advice.

## What is not here yet

More PDF parsers, as statements arrive. See
[ROADMAP.md](ROADMAP.md) — and [COMPARISON.md](COMPARISON.md) for where
this stands beside Portfolio Performance, Wealthfolio and Firefly III,
feature by feature.

## Brokers by API — Saxo Bank and Kraken

Two brokers connect directly, each with credentials that are yours.

**Saxo Bank** speaks OAuth. Once: at
[developer.saxo](https://www.developer.saxo/openapi/appmanagement) create an
application — environment *Live* (or *Simulation*, to try it against Saxo's
demo account first; a switch under Settings picks which), grant type
*Authorization Code*, and as redirect URL the one the Settings page shows
you, which is your dashboard's address plus `/saxo/callback`. Paste the
AppKey and AppSecret under **Settings → Saxo Bank**. Then open an account
of type broker and press **Connect Saxo**: Saxo's login, then straight
back. A client with several Saxo accounts gets one dashboard account each,
because two balances added together is not a balance.

Saxo's tokens are short-lived — the access token twenty minutes, the
refresh token about an hour and single-use — so the app renews the chain
every five minutes for as long as it runs. If it was down for longer, the
account page says the login has lapsed and *Connect Saxo again* is one
click; the history stays. If Saxo will not accept a LAN redirect URL, use
*Finish by hand* on the account page with the address of the dead page
the browser lands on, exactly as with a bank.

Saxo does not hand out ISINs, so a Saxo instrument is keyed by Saxo's own
id and given the Yahoo ticker its symbol and exchange imply
(`IWDA:xams` → `IWDA.AS`), which the price feed then quotes; correct it
under Settings like any other ticker. A position that was transferred in
from another broker has no purchase in Saxo's history; it is recorded as a
transfer at Saxo's average open price, so the holding is right.

**Kraken** needs an API key: kraken.com → Settings → API → Add key, with
only *Query Funds*, *Query Closed Orders & Trades* and *Query Ledger
Entries* ticked — nothing that can trade, withdraw or stake. Paste the key
and the private key under **Settings → Kraken**; the app checks the key
and shows the balances. Then **Connect Kraken** on a broker account. Every
fill is a buy or a sale of the coin for the currency it settled in, coin
deposits and withdrawals move units without money, staking rewards are
income in kind, and Kraken's balances are checked against what the rows
add up to — a gap is reported, never patched. A coin has no ISIN: it is
keyed `CRYPTO:BTC` and priced as Yahoo's `BTC-EUR`.

Both sync with the daily sync and with *Sync everything*.

## Swiss accounts — Swissquote, Yuh, Crédit Agricole (Suisse)

Switzerland is outside PSD2, so no bank aggregator reaches a Swiss account
— the "Swissquote Bank Luxembourg" you may see in Enable Banking's list is
a different, EU-licensed bank. Swiss accounts are file imports:

- **Swissquote**: the monthly *Kontoauszug* PDF the bank emails, or the
  *Transaktionsaufstellung* PDF exported from the web portal for any
  period. Both carry every trade with its ISIN, quantity and price, so
  holdings are computed from statements alone. For the current month,
  before the statement exists, drop in the *Transaktionsbeleg* receipts
  the bank mails after each trade — a receipt and the statement it later
  appears in are recognised as the same trade. Two Swissquote accounts
  (Trading and Invest Easy, say) are two accounts here: import each
  account's statements into its own.
- **Yuh**: the same statement with a different letterhead; the Yuh app's
  yearly and monthly *Kontoauszug* PDFs import the same way.
- **Crédit Agricole next bank (Suisse)**: the *Buchungsliste* CSV from the
  e-banking, for each account.

## Share Ideas

The four boards rank a shipped universe — about 360 EU, Swiss, UK and US
large caps and about 80 UCITS ETFs — on figures fetched from Yahoo with no
key and no account, the same source the prices come from. The cache is
refreshed once a day by the app itself (the first time a minute after
start-up; a button under Settings does it now) and the page only ever reads
it, so it renders whether or not Yahoo answered.

Scoring is deliberately auditable: each pillar is a linear ramp over one or
two published figures, blended with fixed weights, and the row carries the
inputs beside the output. A missing figure is not scored as zero — the
weights renormalise over what is present and the row says how much was —
and a name that fails a hard gate (no dividend, no positive earnings, under
a billion of market cap, a yield that says distress) stays listed with the
reason rather than vanishing.

Three files in the data folder are yours, read on every page load:

```
screener_universe.json       {"symbols": ["XYZ.PA"], "exclude": ["TTE.PA"]}
screener_etf_universe.json   {"etfs": [{"symbol": "IWDA.AS", "ter": 0.002}], "exclude": []}
screener.json                thresholds and weights, per board
```

An ETF's TER is curated, never trusted from Yahoo — Yahoo has none for most
European listings and reports it in two units when it does — so a fund with
no known TER is gated out with that as the reason, which is the nudge to
put the KID figure in the override file. The override merges field by
field: correcting a TER does not require restating the rest of the entry.

Two things it does not do. It cannot buy anything — the page ends at a
shortlist. And it does not know your tax rules: the PEA eligibility it shows
is the French one, inferred from the country of incorporation for shares
and curated for funds, and is a hint for the shortlist rather than a fact
to act on.

## Claude, and other assistants (MCP)

The app has an MCP endpoint at `/mcp`, so an assistant can read the
dashboard and do the chores that are slow by hand — above all categorising:
it reads the uncategorised queue, files each transaction, and teaches the
app a rule per merchant that applies to every past and future transaction
that matches. It can also set budgets, type in a transaction or a balance,
star a share idea, and start a sync. It cannot delete an account, change
settings, or see your bank credentials.

Under **Settings → Claude and other assistants**, create a token. The page
then shows the whole setup for Claude Code on your network:

```bash
claude mcp add --transport http wealth http://<your-host>:8000/mcp \
  --header "Authorization: Bearer <token>"
```

Claude Desktop only speaks to local processes, so the `mcp-remote` bridge
carries the same URL and header. In `claude_desktop_config.json`, under
`mcpServers`:

```json
"wealth": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "https://<your-host>/mcp", "--transport", "http-only",
           "--header", "Authorization: Bearer <token>"]
}
```

Two things that cost people an afternoon. The URL is the one the browser
reaches the dashboard at: behind a reverse proxy that is the `https://`
address, not the container's `http://` one — the Settings page prints the
address it was opened at, which is the right one. And `--transport
http-only` matters: without it `mcp-remote` first tries the older SSE
transport, which this endpoint does not speak, and reports a connection
failure that is not one.

The endpoint is reachable wherever the dashboard is and nowhere else —
nothing is published to the internet — which means the claude.ai website
and phone apps cannot reach it unless you put the app behind a public
HTTPS proxy, which this README does not recommend.

The token stands in for your password. Keep it as private, and revoke or
replace it on the same page the moment you are unsure; anything connected
with the old one is cut off at once.

## REST API and webhooks

Every MCP tool is also a URL, behind the same token:

```bash
curl -H "Authorization: Bearer <token>" http://<your-host>:8000/api/v1/tools
curl -H "Authorization: Bearer <token>" "http://<your-host>:8000/api/v1/tools/net_worth"
curl -H "Authorization: Bearer <token>" -X POST -H "Content-Type: application/json" \
     -d '{"txn_id": 123, "category": "groceries"}' http://<your-host>:8000/api/v1/tools/set_category
```

`GET` takes arguments as query parameters, typed by the tool's schema;
`POST` takes a JSON object. A tool's own refusal is a 422 with its
sentence; a wrong argument a 400.

Webhooks, under Settings → Assistants: a URL of yours receives a JSON
POST on `sync.completed`, `sync.failed` and `bill.missed`, with the
event in `X-Wealth-Event` and an HMAC-SHA256 of the body in
`X-Wealth-Signature`, keyed with the secret the list shows.

## Exchange rates

Amounts in another currency are converted at **ECB euro reference rates** —
free, no key, no account — and every total built from them names the day they
were published. Fetched on start-up, at most once a day, in the background;
there is a button under Settings for doing it now. Ninety days of history are
kept, so a weekend falls back to Friday's rate rather than to a gap.

Two things this deliberately does not do. It does not use a rate your bank or
broker would give you — reference rates are mid-market, and the page says so.
And it does not convert what it has no rate for: an amount in a currency the
ECB does not publish stays beside the total instead of being folded into it, the
same as before there were any rates at all.

---

## Install

### Unraid

**Apps** → search **wealth-dashboard** → **Install**. Set a port, leave the
Data path on appdata, apply, open the WebUI. Nothing else is required: no
database container, no API key. The [install guide](docs/INSTALL.md) covers
backups, exposing it safely and the redirect URL.

Not in Community Applications yet, or you would rather not wait? **Docker → Add
Container → Template**, and paste the template URL:

```
https://raw.githubusercontent.com/halvar20000/wealth-dashboard/main/templates/wealth-dashboard.xml
```

The template itself is [`templates/wealth-dashboard.xml`](templates/wealth-dashboard.xml).

### Home Assistant

**Settings → Add-ons → Add-on Store → ⋮ → Repositories**, add

```
https://github.com/halvar20000/wealth-dashboard
```

then install **Wealth Dashboard** from the store, start it and open it from
the sidebar. It runs behind Home Assistant's login through ingress, keeps its
data where a Home Assistant backup picks it up, and has nothing to configure.
The [add-on guide](homeassistant/wealth-dashboard/DOCS.md) covers backups and
the one thing ingress changes for bank sync.

### Linux, macOS, Windows

With Python 3.10 or newer and [pipx](https://pipx.pypa.io/) installed:

```bash
pipx install wealth-dashboard
wealth-dashboard
```

It starts on <http://127.0.0.1:8000>, opens it in your browser, and keeps
its data in your user folder — `~/.local/share/wealth-dashboard` on Linux,
`~/Library/Application Support/wealth-dashboard` on macOS,
`%LOCALAPPDATA%\wealth-dashboard` on Windows; the path is printed on start.

Then, once, so that a terminal is never needed again:

```bash
wealth-dashboard install
```

That puts **Wealth Dashboard** in your applications menu and on your desktop,
and starts it at login — a systemd user service on Linux, a LaunchAgent on
macOS, a Startup-folder shortcut on Windows. After a reboot it is simply
running; the icon opens it in the browser, whether or not it already was.
Flags given to `install` are kept by the shortcut (`wealth-dashboard install
--port 8001`). `wealth-dashboard uninstall` removes the three again; your
data stays.

`wealth-dashboard --help` lists the flags: `--port`, `--host 0.0.0.0` for
the LAN, `--data DIR` to keep it somewhere else, `--no-browser`. Update with
`pipx upgrade wealth-dashboard` — the shortcut and the service pick up the
new version on their next start. You will know when: the app asks PyPI once
a day for the newest version (a switch under Settings) and the version in the
menu gets a dot when there is one.

Until the first PyPI release, or to run the newest commit, the same
command works straight from the repository:

```bash
pipx install git+https://github.com/halvar20000/wealth-dashboard
```

### Docker, anywhere

```bash
docker run -d --name wealth-dashboard -p 8000:8000 --restart unless-stopped \
  -v /srv/wealth-dashboard:/data \
  -e TZ=Europe/Berlin -e PUID=$(id -u) -e PGID=$(id -g) \
  ghcr.io/halvar20000/wealth-dashboard:latest
```

One volume holds everything, credentials included — see *Where your data
lives* for keeping those separate. The app runs as `PUID:PGID` (`1000:1000`
when unset), never as root, and the volume is given to that user on start.

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

## Connecting a bank — the illustrated guide

The walkthrough above is the short version. There is also a step-by-step guide
with screenshots of every screen, from registering with Enable Banking to the
first sync, including the mistakes that cost an hour — the redirect URL that has
to match exactly, and the linking step whose absence looks like a bug here.

| | |
|---|---|
| English | [Enable-Banking-Setup-EN.docx](https://raw.githubusercontent.com/halvar20000/wealth-dashboard/main/docs/guides/Enable-Banking-Setup-EN.docx) |
| Deutsch | [Enable-Banking-Setup-DE.docx](https://raw.githubusercontent.com/halvar20000/wealth-dashboard/main/docs/guides/Enable-Banking-Setup-DE.docx) |
| Français | [Enable-Banking-Setup-FR.docx](https://raw.githubusercontent.com/halvar20000/wealth-dashboard/main/docs/guides/Enable-Banking-Setup-FR.docx) |
| Español | [Enable-Banking-Setup-ES.docx](https://raw.githubusercontent.com/halvar20000/wealth-dashboard/main/docs/guides/Enable-Banking-Setup-ES.docx) |

The screenshots are of the English interface in every version, because that is
what a screenshot is a picture of. Where the app has a translated label, the
text gives both.

## Your own CSV — the template

Any bank's CSV can be mapped once on the import page. But if you make
the file yourself — from a spreadsheet, a script, a document archive —
there is a header that needs no mapping at all. Name the columns like
this, in any order, and the file is recognised as the app's own:

```
date,amount,currency,description,counterparty,kind,isin,security_name,quantity,price,fee,tax,id
2026-03-01,-1250.00,EUR,Rent March,Landlord Ltd,,,,,,,,r-1
2026-03-02,-482.10,EUR,Bought 4 x World ETF,,buy,IE00BK5BQT80,Vanguard FTSE All-World,4,120.10,1.70,,r-2
2026-03-05,2900.00,EUR,Salary,Employer AG,deposit,,,,,,,r-3
2026-03-08,12.40,EUR,Dividend,,dividend,IE00BK5BQT80,Vanguard FTSE All-World,,,,1.85,r-4
```

Only `date` and `amount` are required; leave out any column you have
nothing for. What each one means:

| Column | Meaning |
|---|---|
| `date` | `2026-03-01`, `01.03.2026` or `01/03/2026`. A US month-first date is not guessed. |
| `amount` | Signed: money in positive, money out negative. Or two columns `debit` and `credit` instead. |
| `currency` | ISO code. Blank means the account's currency. |
| `description` | What the row says. |
| `counterparty` | Who paid or was paid — what the category rules match on. |
| `kind` | `buy`, `sell`, `dividend`, `interest`, `fee`, `tax`, `deposit`, `withdrawal` or `transfer` (also in German, French or Spanish). Blank: worked out from the row — an ISIN and units is a trade, an ISIN and money in is a dividend, plain money a deposit or a withdrawal. A kind you name also fixes the sign of the amount. |
| `isin`, `security_name` | For anything that is a holding. The ISIN is the key that joins the same fund across brokers. |
| `quantity`, `price` | Units and price per unit for a buy or a sale. Units are always written positive; the kind gives them their sign. |
| `fee`, `tax` | Positive amounts, kept apart from the price. |
| `id` | Your own id for the row, if you have one. With it, a row whose text you corrected between two exports is still the same row; without it, the row is identified by what it says. |

Separator can be `,`, `;`, tab or `|`; decimals can be `1234.56` or
`1.234,56`; a file that Excel wrapped in quotes is unwrapped. Re-importing
a file you already loaded adds nothing twice.

## Where your data lives

```
data/
  wealth.db              your database — this is the thing to back up
  settings.json
  screener*.json         your additions and corrections to the Share Ideas lists
  backups/               wealth.db as it was before each upgrade, the last five
  secrets/               bank, Saxo and Kraken credentials, session key, MCP token (0600)
```

**Back up `data/`.** RAID and snapshots protect against a disk dying, not
against a bad import or a mistaken delete. The copies in `backups/` are for
one thing only: the first start of a new version makes one before it
migrates the database, so if the new version turns out wrong you can pin
the old one and put the copy back.

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
| `PUID`, `PGID` | `1000` in the image | The user the container runs as; `/data` is given to it on start |

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

A proxy may mount it under a path rather than a host of its own: send
`X-Forwarded-Prefix: /wealth` (nginx, Traefik) and every link and redirect
carries the prefix. Home Assistant's ingress does the same with
`X-Ingress-Path`, which is how the add-on works.

Your Enable Banking private key is the credential. Anyone who can read it
and knows your Application ID can act as your application. It is stored
0600 and belongs outside any folder you sync or back up casually.

## Tests

```bash
python3 tests/test_all.py
```

1306 checks, no network, no pytest, no credentials. The whole bank flow —
JWT signing, pagination, normalisation, connect, sync, dedupe, consent
expiry — runs against a fake, so it works on a NAS with an unhelpful
Python and no internet.

## Feedback and ideas

This is used daily by its author, but one household is a narrow test. If your
bank, your currency or your way of saving does not fit, that is exactly what
is worth hearing.

* **Wrong number, failed sync, broken page?**
  [Open a bug report](https://github.com/halvar20000/wealth-dashboard/issues/new?template=bug_report.yml)
  — version (click it in the header), which page, what you expected. Redact
  anything personal from logs; the numbers are yours, not needed here.
* **Want something?** Say so in
  [Discussions → Ideas](https://github.com/halvar20000/wealth-dashboard/discussions/categories/ideas),
  or 👍 an idea already there. The [**roadmap** thread](https://github.com/halvar20000/wealth-dashboard/discussions/1) lists what is
  being considered, and the votes decide the order.
* **A bank that will not connect, or a setup question?**
  [Discussions → Q&A](https://github.com/halvar20000/wealth-dashboard/discussions/categories/q-a).
  Name the bank and country; the thread helps the next person with the same one.

## Licence

[AGPL-3.0-or-later](LICENSE). Run it, change it, share it. If you run a
modified version as a service for other people, you must offer them the
source.

## This is not financial advice

It shows you your own numbers. What you do about them is yours.
