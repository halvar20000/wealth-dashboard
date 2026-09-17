# Wealth Dashboard

The add-on is the whole app: a small Python web server and a SQLite file.
There is **no database add-on, no API key and no account anywhere** — install,
start, open it from the sidebar and create your login in the browser.

Bank sync is optional and set up **inside the app afterwards**. Everything else
— manual accounts, broker CSV import, holdings, cash flow, budgets,
subscriptions, categories — works without it.

## Install

1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**, add
   `https://github.com/halvar20000/wealth-dashboard` and close the dialog.
2. Find **Wealth Dashboard** in the store (reload the page if it is not there
   yet) and **Install**. Nothing is built on your machine: it pulls the same
   image Docker and Unraid users run, for `amd64` and `aarch64`.
3. Turn on **Show in sidebar**, then **Start**.
4. Click **Open Web UI**, or **Wealth** in the sidebar.

The first page asks you to **create your user**. That account is the only one,
it lives in your database, and there is no password reset — see
[Back this up](#back-this-up). It is a second login, after Home Assistant's,
on purpose: the page holds your finances, and the add-on does not assume that
everyone who may operate your lights may also read your bank statements.

The app speaks **English, German, French and Spanish** and follows your
browser; pin one under **Settings** if you would rather it did not.

## Nothing to configure

The **Configuration** tab is empty, and that is not an omission:

- **Data** lives in the add-on's own persistent folder, `/data`.
- **Timezone** — which decides when a month rolls over on the cash flow and
  budget pages — is Home Assistant's, passed in automatically.
- **Base currency, redirect URL, consent length** are set in the app under
  **Settings**, where they can be checked, rather than pinned from outside
  where a change in the app would be overwritten on the next restart.

## Back this up

Everything you own is in the add-on's data folder, and a normal Home
Assistant **backup** of the add-on includes it:

```
/data/
├── wealth.db          your accounts, transactions, holdings, categories
├── settings.json      base currency, redirect URL, consent length
├── backups/           wealth.db as it was before each upgrade, the last five
├── options.json       written by Home Assistant; empty, and not yours
└── secrets/
    ├── flask_secret                 signs your login session
    ├── enablebanking_app_id         your Enable Banking application, if
    └── enablebanking_private.key    you set one up — the bank credential
```

Two things follow from "that is the whole list":

- **There is no password reset.** Nobody else has a copy of the database, so
  nobody can send you a link. Lose the folder and lose the data.
- **The backup is the bank credential too.** Anyone who can read
  `secrets/enablebanking_private.key` can ask your bank for your transactions
  until the consent expires. Treat a copy of the backup the way you would
  treat the key file you downloaded from Enable Banking.

## Bank sync, and the redirect URL

Nothing in the app waits on this. Set it up when you want it, under
**Settings → Enable Banking**; the walkthrough is in the
[README](https://github.com/halvar20000/wealth-dashboard#connecting-a-bank--worked-example-dkb).

One thing is specific to Home Assistant. Through ingress the dashboard has no
address of its own that a bank can send you back to — the ingress URL is
behind your Home Assistant login. So, either:

- **Finish by hand.** Register any redirect URL with Enable Banking (for
  example `https://example.org/callback`; many providers insist on `https`
  anyway). After authorising, the bank leaves you on a page that does not
  load. Copy the whole address from the address bar, open
  **Connect → finish by hand** in the app, and paste it. It links and syncs
  exactly as the automatic callback does. Nothing to open, nothing to expose.
- **Or open the port.** Under **Network** in the add-on's configuration,
  give port `8000` a host port, restart, and register
  `http://<your-home-assistant-ip>:8000/connect/callback` — set the same
  string in the app under **Settings**. The dashboard is then also reachable
  on that port *without* Home Assistant's login in front, protected only by
  its own password. Keep it on your LAN.

Consent at a European bank lasts at most 90 days; the app warns you before it
expires rather than after. Re-connecting is the same three clicks.

## MCP and the API

**Settings → MCP** shows the URL an assistant would connect to. Through ingress
that URL is inside Home Assistant's login and an assistant cannot use it; open
the port as above and use the direct address instead.

## Updating

The add-on's version is the app's version, and Home Assistant shows an update
when a new one is tagged. Data survives updates: it is in `/data`, and the
image holds none of it. Every page links to the changelog in its header, and
the same history is on the add-on's **Changelog** tab.

## Security

The dashboard holds your finances and has one password. Through ingress it
sits behind Home Assistant's login as well, which is the recommended way to
use it. If you open the port, do not forward it to the internet: there is no
two-factor and no lockout beyond a short throttle.

## Licence

AGPL-3.0-or-later. Source, issues and the full documentation:
<https://github.com/halvar20000/wealth-dashboard>.
