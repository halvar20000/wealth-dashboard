# Roadmap

Built in the order a user meets it, not in the order the code is
interesting. Each step has to leave the app working and honest about what
it does not do yet.

## Done — v0.1

- [x] Installable server: `python -m app`, or Docker.
- [x] First run creates a user (username + password).
- [x] Create an account by hand.
- [x] Connect an account to a bank via Enable Banking (DKB as the worked
      example): pick bank → bank's own login → session → link.
- [x] Pull balance and transactions; re-syncing is idempotent.
- [x] Consent expiry surfaced before it bites, not after.
- [x] Broker CSV import (Degiro, Trade Republic), recognised by columns
      rather than chosen from a list.
- [x] Holdings computed from imported trades.
- [x] Overview page: net worth, cash vs securities, breakdown charts,
      holdings across accounts, latest activity.
- [x] Edit and delete an account.
- [x] Portfolio, Cash Flow, Budget, Subscriptions, Transactions and
      Categorize pages.
- [x] Categories with learned rules that apply retroactively.
- [x] Categories the user owns: add, rename, recolour and delete them
      under Settings.
- [x] 319 offline checks covering the whole flow.
- [x] English, German, French and Spanish, with the number and date
      shapes that go with each.
- [x] Deleting an account asks only when there is something to lose.
- [x] A version the app can state, a changelog it renders itself, and
      a build that refuses a tag disagreeing with either.
- [x] Packaged as an Unraid app: multi-arch image on GHCR, a
      Community Applications template, and an install guide.

## Next

**1. Exchange rates.** The most visible gap. A balance or holding in a
currency other than the base one is reported beside the total rather
than inside it, because adding 100 USD to 100 EUR is wrong in a way
nobody can see. The ECB publishes daily reference rates free and without
a key; that, plus a decision about which day's rate a historical balance
is worth, closes it.

**2. The pages that are still blocked.** Each waits on one thing:

| Page | Needs |
|---|---|
| Monthly Gains | a price feed — "what did the assets earn by themselves" is unanswerable without prices you did not pay |
| Why It Moved | daily per-holding snapshots; there is no history to decompose until the app has been running |
| Share Ideas | a fundamentals source and a nightly refresh job; independent of everything else here |
| Income | a payslip importer, which is employer-specific in a way no generic parser fixes |
| Expenses | more than one household member, and a per-transaction owner |

**3. Balance history.**
`balances` already stores every reading with its date. A chart over time
is nearly free once there is more than one point, and it is the first
screen that rewards using the app for a month.

**4. Live prices.**
Holdings are valued at the price of your last trade, which is honest and
not much use after a month. A price source keyed on ISIN, and a manual
balance for the accounts no file and no API will ever describe.

**5. Scheduled sync.**
A consent lasts 90 days; a sync should not need a human. In-container,
so there is no crontab to edit.

## Deliberately not planned

- **A hosted version.** The moment there is a server holding other
  people's bank consents, this is a different product with different
  obligations.
- **Anything jurisdiction-specific** in the core — one country's tax
  rules, one employer's pension. If it arrives it goes behind a flag,
  off by default, because it is only correct for one person and probably
  not you.
- **Write access to a bank.** Read-only consent is enough for a
  dashboard. Payment initiation is a different scope, a different
  licence, and a different class of bug.
