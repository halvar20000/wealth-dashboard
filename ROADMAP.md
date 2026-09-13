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
- [x] CSV import (Degiro, Trade Republic, DKB, Crédit Agricole Suisse) and
      statement PDFs (DKB Depot, Swissquote, Yuh), recognised by content
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
- [x] An MCP endpoint with a revocable token, so an assistant can
      categorise, budget, and read everything the pages show.
- [x] Saxo Bank by OAuth, with the token chain kept alive in-app, and
      Kraken by a read-only API key.
- [x] A page per security with every row behind it, correctable, and its
      performance since the first purchase; daily prices backfilled.
- [x] A Crypto page, and loans and mortgages with a computed schedule.
- [x] Time-weighted and money-weighted return, per security and for the
      portfolio.
- [x] Realised gains by lots, FIFO or average cost.
- [x] Stock splits, recorded once on the security's page.
- [x] A sidebar navigation in groups, collapsible to icons.
- [x] The three stages of building wealth, on the plan and as it went.
- [x] A generic CSV importer with a saved column mapping, recognised by
      the file's header.
- [x] CSV export of transactions and holdings, filtered as the page is.
- [x] Allocation by asset class, region and bucket, with targets and a
      contribution spread.
- [x] Rules engine: more triggers (account, kind, match mode) and actions
      (rename, set kind, tag).
- [ ] Benchmark comparison on the portfolio and security pages.
- [ ] Bills (expected recurring payments, due, missed) and savings goals.
- [ ] A dividend calendar: paid so far, and what is due next.
- [x] Tags on transactions.
- [ ] A REST API over the MCP tools, and webhooks on sync.

## Next

**1. Price history.** *(Done in 0.23.0: daily prices are backfilled from
each security's first trade, so the question is answerable from day one.)*

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
