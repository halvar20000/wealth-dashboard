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
- [x] CSV import (Degiro, Trade Republic, DKB) and DKB Depot PDFs, recognised by content
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
- [x] Exchange rates from the ECB, with the publication date shown
      beside every total built from them.
- [x] Packaged as an Unraid app: multi-arch image on GHCR, a
      Community Applications template, and an install guide.
- [x] Transactions and balances typed in by hand, for the accounts no
      file and no API will describe — trades included, so a holding can
      exist without an export.
- [x] Market prices from Yahoo Finance, resolved from the ISIN once per
      security, with a manual ticker override and a labelled fallback to
      the last trade.
- [x] DKB Depot statements read from the Wertpapierabrechnung PDFs, many
      at once or as a ZIP, since the Depot's CSV has no quantities.
- [x] People: each account belongs to one, several or none of the
      household, and a switch in the header shows everyone's picture or
      one person's on every page.
- [x] Forecast: a savings plan or a goal, projected from today's balance
      with deposits and returns shown apart.
- [x] Connected accounts synced automatically once a day.
- [x] Net worth over time, rebuilt from the records; bank connections
      graded on the overview; a retirement outlook per person.
- [x] Share Ideas: four ranked boards — value, dividends, ETFs, dividend
      ETFs — over a nightly Yahoo cache the app fills itself.

## Next

**1. Price history.** `prices` already keeps every reading with its day.
Once the app has been running a while, "what did the assets earn by
themselves" becomes answerable from it.

**2. The pages that are still blocked.** Each waits on one thing:

| Page | Needs |
|---|---|
| Monthly Gains | enough price history — see 1. |
| Why It Moved | daily per-holding snapshots; there is no history to decompose until the app has been running |
| Income | a payslip importer, which is employer-specific in a way no generic parser fixes |
| Expenses | a per-transaction owner — accounts now have people, transactions do not yet |

**3. Balance history.** *(Done in 0.17.0 as far as the records reach.)*
`balances` already stores every reading with its date. A chart over time
is nearly free once there is more than one point, and it is the first
screen that rewards using the app for a month.

**4. Scheduled sync.** *(Done in 0.16.0: daily, at a time set under Settings.)*
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
