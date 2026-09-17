# Installing Wealth Dashboard on Unraid

The container is the whole app: a small Python web server and a SQLite file.
There is **no database container, no API key and no account anywhere** — set a
port, give it a folder, start it, and create your login in the browser.

Bank sync is optional and set up **inside the app afterwards**. Everything else
— manual accounts, broker CSV import, holdings, cash flow, budgets,
subscriptions, categories — works without it.

---

## Community Applications

1. **Apps** → search for **wealth-dashboard** → **Install**.
2. Set **WebUI Port** if `8000` is already taken on your server.
3. Leave the **Data** path pointing at its default appdata folder.
4. Set **Timezone** to yours (it decides when a month rolls over).
5. **Apply**, then click the container's **WebUI**.

The app speaks **English, German, French and Spanish** and follows your
browser, so it is probably already in your language. Pin one under
**Settings** if you would rather it did not follow.

The first page asks you to **create your user**. That account is the only one,
it lives in your database, and there is no password reset — see
[Back this up](#back-this-up).

## Without Community Applications

**Docker** → **Add Container** → **Template: none**, then:

| Field | Value |
|---|---|
| Name | `wealth-dashboard` |
| Repository | `ghcr.io/halvar20000/wealth-dashboard:latest` (or pin one, e.g. `:0.8.0`) |
| Network Type | `Bridge` |
| WebUI | `http://[IP]:[PORT:8000]` |
| Port | container `8000` → host `8000` |
| Path | container `/data` → host `/mnt/user/appdata/wealth-dashboard` |
| Variable | `TZ` → e.g. `Europe/Berlin` |
| Variable | `PUID` → `99`, `PGID` → `100` |

Or from the command line:

```bash
docker run -d --name wealth-dashboard -p 8000:8000 --restart unless-stopped \
  -v /mnt/user/appdata/wealth-dashboard:/data \
  -e TZ=Europe/Berlin -e PUID=99 -e PGID=100 \
  ghcr.io/halvar20000/wealth-dashboard:latest
```

`PUID`/`PGID` are the user the app runs as — `99`/`100` is `nobody:users`,
the same as the other containers on the server. The folder is given to that
user on every start, so a folder Docker created as root on the first start
works too, and the process holding your finances is not root. Leave them out
and it runs as `1000:1000`; set `PUID=0` only for a mount that will not take
a chown.

---

## Back this up

Everything you own is in the mapped folder:

```
/mnt/user/appdata/wealth-dashboard/
├── wealth.db          your accounts, transactions, holdings, categories
├── settings.json      base currency, redirect URL, consent length
├── backups/           a copy of wealth.db from before each upgrade (the last five)
└── secrets/
    ├── flask_secret                 signs your login session
    ├── enablebanking_app_id         your Enable Banking application, if
    └── enablebanking_private.key    you set one up — the bank credential
```

That is the whole list, which is what makes *"back up that folder"* a complete
instruction. It also means:

- **There is no password reset.** Nobody else has a copy of the database, so
  nobody can send you a link. Lose the folder and lose the data.
- **The folder is the bank credential too.** Anyone who can read
  `secrets/enablebanking_private.key` can ask your bank for your transactions until the
  consent expires. Treat a backup of it the way you would treat the key file
  you downloaded from Enable Banking.

> **Keeping the credentials out of your backups.** If you would rather your
> appdata backup did *not* contain the bank key, add a second path — container
> `/secrets` → host somewhere your backup does not cover — and a variable
> `WD_SECRETS_DIR` = `/secrets`. Set both or neither: the variable without the
> path puts your credentials in the container's own filesystem, where the next
> update destroys them. While the credentials sit inside the data folder, the
> app's Settings page says so; once they are outside it, the warning is gone
> and the page shows where the key actually is.

---

## Exposing it, and not

It holds your finances and it has one password. The sane setups are, in order:

1. **LAN only.** Nothing to do — this is what the template gives you.
2. **A reverse proxy with your own access control** in front of it (SWAG,
   Nginx Proxy Manager, Cloudflare Access, Tailscale). The app speaks plain
   HTTP; terminate TLS at the proxy.
3. **Not port-forwarded to the internet.** There is no rate limiting, no
   two-factor, and no lockout. Do not put it on a public address on its own.

If you reach it through a proxy on a different hostname, that hostname is also
what the bank has to send the user back to — see the redirect URL below.

---

## Bank sync (optional, later)

Nothing in the app waits on this. Set it up when you want it, under
**Settings → Enable Banking**.

The full walkthrough — registering the free application, what the private key
is and where it comes from, why "activate by linking accounts" matters, and the
paste route for when your bank's provider refuses a plain `http` redirect —
is in the [README](../README.md#connecting-a-bank--worked-example-dkb).

There is also an illustrated version with a screenshot of every screen, in
[English](guides/Enable-Banking-Setup-EN.docx),
[German](guides/Enable-Banking-Setup-DE.docx),
[French](guides/Enable-Banking-Setup-FR.docx) and
[Spanish](guides/Enable-Banking-Setup-ES.docx).

Two things that are specific to running it here:

- **The Redirect URL has to match, exactly.** Set it in the app under
  **Settings** to the address *you* reach the app on — for example
  `http://192.168.1.10:8000/connect/callback`, or your proxy's hostname if you
  use one — and register that same string in the Enable Banking Control Panel.
  Reaching the app on `localhost` and on the server's IP produces two different
  strings, and only the registered one works.
- **Change the WebUI port later and it breaks.** The port is part of that URL.
  Update both sides if you move it.

Consent at a European bank lasts at most 90 days; the app warns you before it
expires rather than after. Re-connecting is the same three clicks.

---

## Updating

`latest` follows the default branch, and the image is built for amd64 and
arm64. Unraid's **Check for Updates** sees new versions normally — the image is
published as a plain Docker manifest for exactly that reason.

Your data is in the mapped folder, so an update never touches it. The database
upgrades itself on start: an older schema is migrated in place rather than
refused — and before it is, the first start of a new version copies the file
aside to `backups/wealth-<old version>-<date>.db`. The last five copies are
kept.

To stay on a known version, pin a tag (`:0.8.0`) instead of `latest` in the
container's **Repository** field. Which version you are running is shown in
the app's header, and clicking it lists what changed in each one.

**Going back.** Migrations only go forward, so the old version may not open
a file the new one has changed. Stop the container, pin the previous tag in
**Repository**, copy the matching file from `backups/` over `wealth.db`
(delete `wealth.db-wal` and `wealth.db-shm` beside it if they exist), and
start. Anything entered since that copy was made is gone with it — the copy
is from the moment the new version first started.

---

## Something is wrong

- **The WebUI does nothing / connection refused.** Check the container log
  (Unraid: click the container → **Logs**). A healthy start prints the address,
  the data folder and the secrets folder.
- **"Cannot start:" in the log.** The database could not be opened or migrated
  — usually a permissions problem on the mapped folder. Check that the host
  path exists and is writable.
- **It asks me to create a user again.** The `/data` mapping changed or was
  lost; the app is looking at an empty folder. Point it back at the old one
  rather than creating a second account.
- **"No accounts returned" after connecting a bank.** Nearly always the
  *"Activate by linking accounts"* step in the Enable Banking Control Panel,
  not this app. The README's bank section covers it.
- **A month starts on the wrong day.** Set `TZ`.

Anything else: <https://github.com/halvar20000/wealth-dashboard/issues>.
