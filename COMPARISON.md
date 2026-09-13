# How this compares — Portfolio Performance, Wealthfolio, Firefly III

Three open-source tools people reach for when they want their money on
their own machine. Each is good at what it set out to do, and none set
out to do the same thing. This page says where Wealth Dashboard stands
beside them, feature by feature, as of September 2026 — what each has
today, not how old it is or how many people use it. Where the others
have something this app does not, the table says so.

**In one sentence each.** *Portfolio Performance* is the reference
desktop tool for a securities portfolio: the deepest performance
analysis of the four, the longest list of PDF statement parsers, no
bank API and no household finance. *Wealthfolio* is a privacy-first
desktop portfolio tracker with a clean interface, CSV import with
saved mappings, and a growing add-on system. *Firefly III* is a
self-hosted personal-finance manager — budgets, categories, a rules
engine, bank sync through its data importer — with no notion of a
security or a price. *Wealth Dashboard* is the one that does both
halves — the portfolio and the household money — in one self-hosted
page, pulls from banks and brokers by API, and can be driven by an
assistant.

## The table

✔ has it · ◐ partly, or through an add-on / separate tool · — not there

| | Wealth Dashboard | Portfolio Performance | Wealthfolio | Firefly III |
|---|:-:|:-:|:-:|:-:|
| **Runs as** | self-hosted web app, one container | desktop app (Java) | desktop app (Tauri), mobile in progress | self-hosted web app (PHP) + separate importer |
| Your data stays on your machine | ✔ | ✔ | ✔ | ✔ |
| Languages | en, de, fr, es | many | several | many |
| **Getting data in** | | | | |
| Bank sync by API (PSD2 / open banking) | ✔ Enable Banking, 2 500+ EU banks | — | — | ◐ via Data Importer (GoCardless — closed to new sign-ups since 2025 — or Salt Edge, which does not take private persons) |
| Broker sync by API | ✔ Saxo, Kraken | — | — | — |
| Broker CSV importers | ✔ Degiro, Trade Republic, DKB, Crédit Agricole (Suisse) | ✔ many | ◐ generic | — |
| PDF statement parsers | ✔ DKB Depot, Swissquote, Yuh | ✔ dozens of brokers, the reference | — | — |
| Any CSV, with a mapping saved by header | ✔ | ✔ | ✔ | ✔ (importer) |
| Entries typed in by hand | ✔ | ✔ | ✔ | ✔ |
| Re-import is harmless (rows carry ids) | ✔ | ✔ | ◐ | ✔ |
| Corrections survive the next import | ✔ | ✔ | — | ✔ |
| Export as CSV | ✔ | ✔ | ✔ | ✔ |
| **The portfolio** | | | | |
| Holdings from the trades, across brokers | ✔ | ✔ | ✔ | — |
| Market prices, free, without a key | ✔ Yahoo | ✔ several sources | ✔ Yahoo | — |
| Daily price history backfilled | ✔ | ✔ | ✔ | — |
| Time-weighted return (TWR) | ✔ | ✔ | ✔ | — |
| Money-weighted return (IRR / MWR) | ✔ | ✔ | ✔ | — |
| Realised gains by lots, FIFO | ✔ | ✔ | ✔ | — |
| …and by average cost (PMP) | ✔ | ✔ | ◐ | — |
| Fees and taxes per trade | ✔ | ✔ | ✔ | — |
| Dividends and interest as income | ✔ | ✔ | ✔ | ◐ as plain income |
| Stock splits | ✔ | ✔ | ◐ | — |
| A page per security with every row, correctable | ✔ | ✔ | ✔ | — |
| Multi-currency, ECB rates, history since 1999 | ✔ | ✔ | ✔ (Yahoo rates) | ✔ |
| A holding shown in the currency paid, quoted, or base | ✔ | ✔ | ◐ | — |
| Crypto, priced | ✔ | ✔ | ✔ | — |
| Asset allocation by class, region and own buckets, with targets | ✔ and a contribution spread | ✔ taxonomies, the reference | ✔ classes and sectors | — |
| Benchmark comparison | ✔ eleven indices or any symbol | ✔ | ◐ | — |
| Dividend calendar / forecast | ✔ received and next twelve months | ✔ | ✔ | — |
| Watchlist | ◐ via Share Ideas stars | ✔ | ✔ | — |
| Share screener (value, dividend, ETF boards) | ✔ | — | — | — |
| Tax reports | — | ◐ | — | — |
| **Household money** | | | | |
| Net worth, cash and securities together, over time | ✔ | ✔ | ✔ | ✔ cash only |
| Categories with a rules engine | ✔ text (contains, starts, exact, regex), field, direction, amount, account, kind → category, rename, kind, tag | — | — | ✔ the reference: more triggers and actions still |
| Budgets against spending | ✔ | — | — | ✔ |
| Cash flow by month | ✔ | — | — | ✔ |
| Subscriptions detected, and bills declared (paid, due, missed) | ✔ both | — | — | ◐ bills, declared by hand |
| Loans and mortgages with a computed schedule | ✔ | — | — | ◐ liabilities, no schedule |
| Savings goals | ✔ fed by an account or by hand | — | ✔ | ✔ piggy banks |
| Several people in one household, each with a view | ✔ | — | — | ◐ user groups |
| **Planning** | | | | |
| Forecast from today's balance | ✔ | ◐ investment plan | — | — |
| Retirement outlook (4 % rule) | ✔ | — | — | — |
| The three stages of building wealth | ✔ | — | — | — |
| **Automation** | | | | |
| Daily sync without a human | ✔ | — | — | ✔ importer on a schedule |
| An assistant can read and act (MCP) | ✔ 35 tools | — | ◐ add-ons | ◐ REST API |
| REST API / webhooks | ✔ the tools as URLs; hooks on sync and missed bills | — | — | ✔ |
| **Engineering** | | | | |
| Dependencies | 4 Python packages | JVM | Rust + Node toolchain | PHP stack + database |
| Database | one SQLite file | XML / binary file | SQLite | MySQL / PostgreSQL / SQLite |
| Tests that run offline | ✔ 1 580+ | ✔ | ✔ | ✔ |

## What that means, honestly

**If the portfolio is all you care about**, Portfolio Performance still
goes deeper in places: its taxonomies nest, its PDF parsers cover
nearly every German-speaking broker, its reports are older and more
numerous. Wealth Dashboard now has the returns, the lots, the splits,
the currencies, allocation with targets, a benchmark line and a
dividend calendar — the analysis most people actually open — and it
does not plan to have tax reports.

**If the household money is all you care about**, Firefly III's rules
engine still has more triggers and actions, and it has tags on
everything, not only transactions. Wealth Dashboard's categories,
budgets, cash flow, rules (text, field, direction, amount, account,
kind → category, rename, kind, tag), bills and goals cover what most
people use of that, over a REST API and webhooks of its own — and it
knows what a security is, which Firefly does not.

**What none of the three has** is the combination: a bank *and* a
broker synced by API into the same net worth; a household of several
people with one picture and one each; loans with a real amortisation
schedule next to the portfolio; the three stages of building wealth;
and an assistant that can categorise the queue, correct a row, record
a split or read the returns over MCP. That is the ground this app was
built for.

**A note on bank aggregators, because it decides what is possible.**
Enable Banking is, in 2026, about the last PSD2 aggregator that lets a
private person register an application and use it for their own
accounts. GoCardless Bank Account Data (the former Nordigen, which
Firefly III's importer was built around) closed its free tier to new
sign-ups in 2025 and moved existing users to business pricing; Salt
Edge, Tink, TrueLayer, Yapily and finAPI do not take private persons
at all. Any tool's "bank sync" column is only as
good as the aggregator behind it still being open — which is why this
app also imports every CSV and PDF it can, and why Enable Banking is
worth the twenty minutes of setup.

**And what it deliberately is not.** Not hosted — the moment a server
holds other people's bank consents it is a different product. Not a
mobile app. Not a tax tool: it computes what a tax form asks for and
leaves the form to you.

## Sources

The columns for the other three are from their own documentation and
release notes as of September 2026 — [portfolio-performance.info](https://www.portfolio-performance.info),
[wealthfolio.app](https://wealthfolio.app), [firefly-iii.org](https://www.firefly-iii.org).
A mark that has gone stale is a mistake, not a claim: open an issue
and it will be fixed.
