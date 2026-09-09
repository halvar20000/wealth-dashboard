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
- [x] 182 offline checks covering the whole flow.

## Next

**1. More than one account, meaningfully.**
Net worth across accounts needs currency conversion — an account in CHF
and one in EUR cannot be added. That means an FX rate source (the ECB
daily reference rates are free and need no key) and a decision about
which day's rate a historical balance is worth.

**2. Balance history.**
`balances` already stores every reading with its date. A chart over time
is nearly free once there is more than one point, and it is the first
screen that rewards using the app for a month.

**3. Categorisation.**
Transactions arrive with a description and a counterparty and nothing
else. Rules the user can correct, where a correction becomes a rule that
applies to past *and* future imports — otherwise the same shop has to be
fixed every month.

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
