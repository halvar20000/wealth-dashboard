# Changelog

Everything that changed, and why. The same history is readable inside the app —
click the version in the header.

The format follows [Keep a Changelog](https://keepachangelog.com/) and versions
follow [Semantic Versioning](https://semver.org/). While the major is `0`, a
minor bump is a feature and a patch is a fix; nothing here is a stable API yet.

> Versions up to 0.7.0 were reconstructed from the commit history when the
> changelog was introduced. They are accurate about what changed and rounded to
> the day, not the hour.

## [0.8.0] — 2026-09-10

### Added
- **The app says which version it is.** The version sits in the header and links
  to this changelog, rendered inside the app — no going to GitHub to find out
  whether the container you are running has the fix you read about.
- `/healthz` reports the version too, so a monitor can see a container that
  never restarted after an update.
- Releases are tagged `vX.Y.Z`, and the image is published under that version as
  well as `latest`. Pin `:0.8.0` if you would rather updates were a decision.

### Changed
- The build refuses a release tag whose number does not match `__version__` or
  has no entry here. A version that means nothing is worse than no version.

## [0.7.0] — 2026-09-10

### Added
- **English, German, French and Spanish** — the whole interface, including how
  numbers and dates are written: `1.234,56 EUR` and `08.09.2026` in German,
  `1 234,56 EUR` and `08/09/2026` in French, ISO dates in English. Set it under
  Settings, or leave it following your browser, which is the default.
- Built-in category names are translated. One you renamed stays exactly as you
  typed it, in whatever language you typed it.

### Changed
- **Deleting an account only asks when there is something to lose.** An account
  with no transactions, no balance readings and no bank connection goes on one
  click. One holding anything still has to be typed out, and now says what goes
  with it, counted and in the right number.
- Delete is reachable from the accounts list. It was only behind Edit, which is
  where a delete goes to not be found.

### Fixed
- Whether an account is empty is decided from the database, never from the
  submitted form.

## [0.6.0] — 2026-09-10

### Added
- **Installable from the Unraid Apps tab** — a Community Applications template,
  an install guide, and a multi-architecture image (amd64 and arm64) published
  to GitHub Container Registry on every push.

### Changed
- Serves through **waitress** rather than Flask's development server, which says
  on every start that it is not for production and is right.
- The image carries `tzdata` and honours `TZ`, so "this month" on the cash flow
  and budget pages rolls over at your midnight rather than UTC's.

### Fixed
- The image is published as a plain Docker schema-2 manifest, without provenance
  or SBOM attestations. Unraid's update checker cannot read GHCR's default OCI
  index and sat on "up to date" against a newer image.

## [0.5.0] — 2026-09-10

### Added
- **Categories you own.** Add, rename, recolour and delete them under Settings.
  The built-in list is a set of defaults, not a fixed menu.
- A category can be moved between counting as spending and not, which is what
  Cash Flow and Budget read.

### Changed
- A category is identified by the name it was created with, so renaming or
  recolouring one never re-files a transaction.
- Deleting a category in use moves its transactions to Uncategorised and says
  how many before it does it. The four the app reasons about by name cannot be
  deleted, because nothing would replace them.

## [0.4.0] — 2026-09-09

### Added
- **Six pages**: Portfolio, Cash Flow, Budget, Subscriptions, Transactions and
  Categorize.
- **Categories with rules that learn.** A correction becomes a rule, and a rule
  applies to what is already imported as well as to what arrives next.
- **Subscription detection** — three occurrences, a rhythm the gaps cluster
  around, and a tight spread of amounts. Anything that repeats but wanders is
  listed separately as "possibly recurring" rather than counted.
- **Budgets** measured against how far through the month you are, not against
  the whole month.

### Fixed
- A deposit into a broker is your own money arriving from your own bank, and was
  being counted as income — inflating income by everything ever invested while
  double-counting the bank side. On the real Degiro export the figure went from
  3,873/month "income" to 39.80, which is the dividends and interest actually
  earned.
- A category rule can no longer touch a buy or a sell. A share purchase is not
  shopping, and a spending rule claiming it would double it against the holding
  it already built.

## [0.3.0] — 2026-09-09

### Added
- **The overview**: net worth, cash against securities, two breakdown charts,
  holdings aggregated by ISIN across every account, and the latest activity —
  all computed on the way out, so no cached total can disagree with the accounts
  it came from.
- Edit and delete an account.
- Degiro's running balance is taken as the account's cash balance. A broker has
  no API here, and it is the only balance the app will ever get for one.

### Changed
- The dark theme: navy ground, green for gain, red for loss, gold kept for the
  one number on a page that is an answer rather than an input.
- **Currencies are never added together.** There is no rate source yet, so an
  amount in another currency sits beside the total rather than inside it, with a
  line saying why.
- **Securities are valued at the price of your last trade**, not a market price,
  and every page that shows one says so.

### Fixed
- A rewritten base template had no `scripts` block, so the overview's chart code
  was silently dropped — a perfectly rendered page where nothing happened. There
  is now a test that every block a template defines exists in the base.

## [0.2.0] — 2026-09-09

### Added
- **Broker CSV import** for Degiro and Trade Republic. The file is recognised by
  its columns rather than chosen from a list, because asking somebody to pick
  the parser for a file that names its broker on every line is asking them to
  get it wrong — and the wrong parser does not fail, it produces a confident
  mess.
- **Holdings computed from those trades**: what you own, how much, and what you
  put in. Re-importing an overlapping period is harmless.

### Fixed
- A database made by 0.1.0 refused to start against the new schema:
  `CREATE TABLE IF NOT EXISTS` is a no-op on a table that already exists, so the
  older columns stayed. Tables, then columns, then indexes — an older database
  is now migrated in place rather than rejected.

## [0.1.0] — 2026-09-09

### Added
- **The first loop, end to end**: install it, create your user, add an account,
  connect it to a European bank through Enable Banking, and pull the balance and
  transaction history. Re-syncing is idempotent.
- **Your own login**, PBKDF2-hashed in your own database. There is no password
  reset because there is nobody to reset it.
- **Finish a connection by hand** when the bank cannot redirect to a LAN
  address: paste the URL from the dead page it left you on. A self-hosted
  dashboard has no business demanding a public hostname and a certificate before
  it will read a bank balance.
- **Sandbox banks are flagged and sorted first**, with the page saying to use
  one first. Walking the identical flow with the provider's test credentials is
  how you find out a redirect URL is registered wrongly — instead of finding out
  by spending a consent at a bank you depend on.
- Consent expiry is surfaced before it bites.
- Docker image and compose file.

[0.8.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.8.0
[0.7.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.7.0
[0.6.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.6.0
[0.5.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.5.0
[0.4.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.4.0
[0.3.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.3.0
[0.2.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.2.0
[0.1.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.1.0
