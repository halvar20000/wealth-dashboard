# Changelog

Everything that changed, and why. The same history is readable inside the app —
click the version in the header.

The format follows [Keep a Changelog](https://keepachangelog.com/) and versions
follow [Semantic Versioning](https://semver.org/). While the major is `0`, a
minor bump is a feature and a patch is a fix; nothing here is a stable API yet.

> Versions up to 0.7.0 were reconstructed from the commit history when the
> changelog was introduced. They are accurate about what changed and rounded to
> the day, not the hour.

## [0.28.1] — 2026-09-13

### Added
- **Corrections over the MCP.** `update_transaction` changes only the
  fields given on one row — imported or typed, and the correction
  survives the next import; `update_transactions` does the same on
  many ids at once, with `negate_amount` to flip the sign of each;
  `delete_transactions` removes rows by id (an imported one comes back
  with the next import of the same file, so a correction is the
  better tool where one will do).

### Fixed
- A CSV mapped by hand whose kind column says *Kauf* but whose amount
  is written positive imported the purchase as money in. A kind the
  file names now supplies the sign, as it does for a row typed in — a
  buy, a fee, a tax or a withdrawal is money out whichever way the
  bank wrote the figure; a sale, a dividend, interest or a deposit
  money in. Only a kind worked out from the row keeps the row's sign.
  (Found by Dominique, on 47 Amundi purchases.)

## [0.28.0] — 2026-09-13

### Added
- **The three stages**, under Planning. Early on, what you put in is
  what grows the pile; later saving and returns pull together; later
  still compounding carries it. One ratio tells them apart — what the
  market does in a year against what you put in in a year — with the
  borders at a half and at two. The page says which stage you are in
  on the Forecast page's monthly amount and expected return (or on
  figures tried in place), the crossover wealth at which a year of
  returns pays a year of savings, the year each border falls, a chart
  of put-in against market-did year by year, and — *as it went* — the
  same ratio for every calendar year the app has records of, computed
  from what actually went into securities and what they were actually
  worth.

### Changed
- **The navigation moved to the left.** A sidebar in place of the top
  bar: Overview, then *Investing* (Portfolio, Crypto, Share Ideas),
  *Money* (Cash Flow, Budget, Subscriptions, Transactions,
  Categorize), *Planning* (Forecast, Stages, Loans), Accounts,
  Settings, with the user, sign-out and the version at the foot.
  Every entry has an icon; the sidebar collapses to icons alone for
  more room, with a group opening as a flyout on hover; groups fold,
  and the one holding the current page starts open. Both are
  remembered per browser. On a phone the sidebar is a drawer behind a
  menu button. The whose-accounts switch sits above the page.

## [0.27.0] — 2026-09-12

### Added
- **Stock splits.** A split — 44 new units for 1 old, the money
  unchanged — is the one event that makes every earlier row of a
  holding look wrong: 0.4753 units at 420 before, 21.57 at 9.27 after,
  and a running sum that adds the two. The brokers' exports do not
  carry it, so it is recorded once on the security's page (date, and
  the ratio as new for old; `1:10` for a reverse split). It becomes a
  `split` row per account holding the security that day — the units
  that appeared, at no cost — so the quantity is right from then on;
  it can be corrected or removed like any other row. Earlier rows keep
  the units and prices of their day; the chart and the net-worth
  history value them in today's units, as Yahoo's split-adjusted
  history is; a lot keeps its cost through the split, so a later sale
  realises the same gain it would have in the old units. MCP:
  `record_split`. (Reported by Dominique, on an Amundi ETF in a DKB
  Depot.)

## [0.26.0] — 2026-09-12

### Added
- **Any bank's CSV, mapped once.** A CSV no importer knows is no
  longer refused: the import page shows its columns and the first
  rows, guesses which is the date, the amount, the description, the
  ISIN and so on — in English, German, French or Spanish headings —
  and lets you correct the guess, preview the rows as they would be
  read, and import. The mapping is saved under the file's header, so
  the next export from the same bank is recognised by itself, like a
  Degiro file is. Debit and credit columns, a signed amount with the
  signs the wrong way round, a fixed currency, a kind column in any of
  the four languages, and a kind worked out from the row when there is
  none — a trade from an ISIN and units, a dividend from an ISIN and
  money in — are all handled. Saved mappings are listed under Settings
  and can be forgotten. The built-in importers still come first.
- **Export as CSV**, on the Transactions page (every row the filters
  match, not just the four hundred shown), on an account, on a
  security's page, and on the Portfolio page for the holdings with
  every figure on them — price, value, unrealised and realised gain,
  TWR and MWR. The file follows the language: semicolons and a decimal
  comma for German, French and Spanish, as their Excel expects; commas
  and a point for English; `?sep=,` or `?sep=;` to force either. ISO
  dates, a byte-order mark so Excel gets the encoding right. The
  app reads its own export back through a mapping.

## [0.25.0] — 2026-09-12

### Added
- **Realised gains, by lots.** Every sale is set against the cost of
  the units it sold — the oldest first under **FIFO** (Germany's rule,
  the default), every unit at the average paid under **average cost**
  (France's *prix moyen pondéré*); the choice is a setting under
  General, and switching recomputes everything. Lots live per account,
  so a unit bought at one broker is never sold at another; a transfer
  carries its lots along without realising. The security page lists
  each sale with its proceeds, cost and gain, totals per year, and
  says what the units still held cost; the Portfolio page has a
  realised-gains card by year and per currency, and per holding an
  *Unrealised* column (value minus the cost of the open lots) and a
  *Realised* one. The MCP tool `realised_gains` returns the same,
  per security or as a summary.

## [0.24.0] — 2026-09-12

### Added
- **Time-weighted and money-weighted return.** TWR — chain-linked day
  by day, with the timing of your own money taken out — is the return
  of the investment itself, the figure that compares one holding to
  another. MWR — the internal rate of return, annual — is the return of
  your money, timing included, the figure a statement means by
  "performance". Both are on every security's page (since the first
  purchase, TWR also annualised) and on the Portfolio page for the
  securities as one investment since the first trade, this year and
  the last twelve months, with a TWR and MWR column per holding. Cash
  is left out of the portfolio figure on purpose. Nothing is stored:
  a corrected row or a backfilled price changes the number on the
  next page load. The MCP tool `performance` returns the same figures.

### Changed
- The net-worth history's daily valuation now lives in a reusable
  `Valuer`, which the returns use as well; the line it draws is unchanged.

## [0.23.0] — 2026-09-12

### Added
- **Performance since the first purchase**, on every security's page: a
  chart of what the holding was worth against what went in, day by day,
  with dividends and interest as their own line and the gain in money
  and in percent at the top. To draw it the price feed now **backfills
  daily prices** back to each security's first trade, once per security
  from Yahoo — which also makes the net-worth line on the overview true
  for the time before the app was installed.
- **A Crypto page**: every coin held, with the wallet's value, the
  price, the cost basis with the average per coin, and the unrealised
  gain; a price chart over 1M · 3M · 1Y · 5Y · All that can also show
  the wallet's value over the range — the price times the units held on
  each day, so a purchase is a step up; and the latest rows. A coin can
  be typed in by hand with `CRYPTO:BTC` as its ISIN.
- **Loans and mortgages**: a page to enter each loan's terms — principal,
  rate, first instalment, how often, the instalment or the term — and
  see the amortisation schedule, what is still owed today, what was
  paid and how much of it was interest, the payoff date, and the
  balance over time. Dated extra repayments shorten the schedule. Each
  loan is an account of type *loan*, so it belongs to people, its
  balance is written from the schedule every day, and the overview
  subtracts the debt from the net worth and shows it as its own tile. A
  balance typed in by hand on the loan's account still wins on its day.
  The arithmetic reproduces a bank's own instalment split to the cent.

## [0.22.1] — 2026-09-12

### Changed
- The security page groups its rows by **year and month**, newest first,
  each level a header that opens and closes and carries what happened
  in it — rows, bought, sold, paid out — so twelve identical savings-plan
  buys read as "6 rows · 1 200 bought" rather than a flat list. Only the
  current year and month start open; *Expand all* opens the rest, and a
  kind filter shows only the buys, the sales, the dividends or the
  transfers. Each row shows its kind as a badge, the quantity as a chip
  beside the price, and the quantity as it ran after that row.

## [0.22.0] — 2026-09-12

### Added
- **A page per security**, reached by clicking a holding on the Portfolio
  page or on an account: what is held, what was invested, what it paid,
  what it is worth — and every row behind it across every account, oldest
  first, with the quantity as it ran. Each row can be **corrected** in
  place: date, kind, quantity, price, amount, fee, tax, description.
  Sizes are typed unsigned and the kind supplies the sign, so turning a
  buy into a sale flips both. A correction stays — the next import
  recognises the row by its id and leaves it alone — and the row says
  when it was corrected. An imported row still cannot be removed (it
  would only come back), but it can be corrected to a quantity of zero;
  a row typed in by hand can be removed from here as well.

## [0.21.0] — 2026-09-12

### Added
- **Saxo Bank, by API.** Register an application of your own in Saxo's
  developer portal (Live, or Simulation to try it on Saxo's demo
  account), paste its AppKey and AppSecret under Settings, press
  *Connect Saxo* on an account: Saxo's login, then straight back, with
  one dashboard account per Saxo account. Every fill of the last 400
  days becomes a buy or a sale with quantity and price; dividends,
  interest, fees, taxes and cash movements come from the bookings; the
  cash is the balance reading; and a position Saxo holds that its trade
  history does not explain — one transferred in from another broker —
  is recorded as a transfer at Saxo's average open price, so the holding
  is right. Saxo's tokens die within the hour and the refresh token is
  single-use, so the app renews the chain every five minutes while it
  runs; when it cannot, the account page says the login has lapsed and
  connecting again is one click. Saxo does not hand out ISINs, so its
  instruments are keyed by Saxo's own id and given the Yahoo ticker
  their symbol and exchange imply, correctable under Settings.
- **Kraken, by API key.** Create a key on kraken.com with only *Query
  Funds*, *Query Closed Orders & Trades* and *Query Ledger Entries*,
  paste it under Settings — the app checks it and shows the balances —
  and press *Connect Kraken* on an account. Every fill is a buy or a sale
  of the coin for the currency it settled in, fee included; coin
  deposits and withdrawals move units without money; staking rewards
  are income in kind; and a coin-for-coin swap moves both. Kraken's own
  balances are checked against what the rows add up to, and a gap is
  reported rather than papered over. Requests are signed with the
  private key, which never leaves the machine and is kept 0600 beside
  the bank key.
- A coin has no ISIN: crypto holdings are keyed `CRYPTO:BTC` and the
  price feed quotes them as Yahoo's `BTC-EUR` pair.
- Broker connections sync with the daily sync and with *Sync everything*.

### Changed
- A holding's quantity now counts every row that moves units — a
  transfer in from another broker, a staking reward — not only buys
  and sales. Money in and out still counts for buys and sales alone, so
  a position transferred in has a quantity and no cost here, which is
  the truth. DKB's Depotbuchung transfers now count as well.

## [0.20.0] — 2026-09-12

### Added
- **Swissquote and Yuh**, from their statements. Switzerland is outside
  PSD2, so no aggregator reaches a Swiss account; Swissquote's monthly
  **Kontoauszug** PDF and the web portal's **Transaktionsaufstellung**
  export (a different layout since July 2026) are both read, section by
  currency: deposits, payments, card payments named by merchant, currency
  exchanges as transfers, fees, dividends net of the tax withheld, and
  every trade with its ISIN, quantity, price, commission and stamp duty —
  so holdings are computed from statements alone. The old layout prints
  amounts unsigned; the direction is read off the running balance. Yuh's
  statements are the same document with a different letterhead and come
  through the same parser. The **Transaktionsbeleg** receipt Swissquote
  mails after each trade is read too, for the month that has no statement
  yet; it produces the same id as the statement's row, so importing both
  adds nothing twice. Validated against every statement and receipt on
  hand: each one reconciles to the cent with its own opening and closing
  balance.
- **Crédit Agricole next bank (Suisse)**, from its Buchungsliste CSV:
  Latin-1, one line per booking, the bank's own Auftragsnummer as the id,
  and the running balance taken as the account's balance.

## [0.19.2] — 2026-09-12

### Fixed
- **Trade Republic, second attempt.** 0.19.1 asked for the next page with
  the continuation key alone, which the connector calls a "wrong
  continuation key": the key is bound to the strategy as well, and the
  one thing the connector refuses is our `BOOK` status. So on the
  connector's complaint the page is now asked for with the original
  parameters and no status, then with `BOTH`; pending rows that arrive
  are dropped on normalisation as they always were. Other banks are
  still asked once, as before.

## [0.19.1] — 2026-09-12

### Fixed
- **Trade Republic over Enable Banking stopped after the first page of
  transactions** with `422: transactionStatus in request is not the same
  as in continuationKey`. The connector hands back a continuation key
  stamped with a transaction status of its own choosing and then refuses
  the follow-up request that repeats the parameters of the first — which
  is what every other bank requires. On exactly that error the page is
  asked for again with the key alone; any other 422 is still an error,
  and banks that accept the repeat are asked the same way as before.

## [0.19.0] — 2026-09-11

### Added
- **An MCP endpoint**, so Claude — or any assistant that speaks MCP —
  can read the dashboard and do the chores that are slow by hand. Twenty-
  three tools: net worth, accounts, holdings, history, a transaction
  search, the uncategorised queue with the app's own guess and pattern per
  row, categories, rules, budgets, subscriptions, share ideas and sync
  health to read; `set_category` and `categorise_many` (which learn a
  rule per merchant and apply it retroactively), `add_rule`,
  `delete_rule`, `set_budget`, `add_transaction`, `set_balance`,
  `watch_idea`, and sync / price / ideas refresh to write. Nothing that
  deletes an account, edits settings or touches credentials. Every write
  goes through the same function the page uses, so an assistant's change
  is one the UI could have made.
- Access is by a bearer token created under **Settings → Claude and
  other assistants**, stored 0600 beside the bank key and revocable
  there; the page shows the one-line `claude mcp add` for Claude Code on
  your network. The endpoint is JSON-RPC over POST at `/mcp` — the
  Streamable-HTTP transport, written here in ~200 lines rather than
  pulling the SDK and its dependencies into a four-line requirements
  file. Answers are in English whatever the UI language, because the
  reader is a program.

## [0.18.0] — 2026-09-11

### Added
- **Share Ideas** — a new page with four ranked boards over one nightly
  Yahoo cache. *Value*: shares that have fallen from their 52-week high,
  trade on a low P/E, still earn well and pay a covered dividend.
  *Dividends*: the highest yields that are still growing — covered by
  earnings *and* by free cash flow, on a business that is not shrinking,
  with a yield above 12 % gated out rather than rewarded. *ETFs*: UCITS
  funds ranked on five-year total return in euros against their TER, the
  return computed from the adjusted price history because Yahoo leaves
  its own return fields empty for European listings, and converted to
  euros first so a USD-quoted fund and its EUR twin score the same.
  *Dividend ETFs*: distributing funds on the income they actually paid
  over twelve months, computed from the distributions themselves, with
  the worst year-on-year cut on record standing in for the payout ratio
  a fund does not have. Every score is a documented blend of linear ramps
  over published figures; the page shows the inputs beside the output,
  renormalises rather than scoring a gap as zero and says how thin the
  data was, and lists what it excluded and why. Star or dismiss a name;
  the list is shared across the four boards. What you already hold is
  folded in — shares onto the share boards, funds onto the fund boards —
  and marked. A ~360-share and ~80-ETF universe ships with the app;
  `screener_universe.json`, `screener_etf_universe.json` and
  `screener.json` in the data folder extend, correct and tune it and are
  read on every page load.
- No new dependency for any of this: Yahoo's fundamentals endpoint wants
  a session cookie and a crumb, and the app does that handshake itself
  rather than pulling a library with pandas behind it into a four-line
  requirements file.
- The cache is refreshed once a day by a background thread — the first
  time a minute after start-up — with a button under Settings to do it
  now. A refresh is a few hundred requests with a pause between them and
  takes a few minutes; a symbol that fails keeps its old row with the
  error on it, so a Yahoo hiccup makes a name stale, never gone.
- The price feed now records whether Yahoo calls a holding an equity or a
  fund, which is what routes it to the right board.

## [0.17.0] — 2026-09-11

### Added
- **Net worth over time**, in the overview. A line under the headline,
  with 1M · 3M · 6M · YTD · 1Y · All and the change over the range beside
  the account count. Nothing is snapshotted: the line is rebuilt from the
  balance readings, the trades, the prices and the ECB rates as of each day
  drawn, so it cannot disagree with the pages beside it — and it goes back
  exactly as far as the records do, which the caption says. The daily sync
  is what fills it in.
- **Bank connections**, graded, on the overview. Each connected account
  with a dot: red for an expired consent, a failed or never-run sync, or
  two days of silence; yellow for a consent expiring within two weeks or a
  day without a sync; green otherwise. A consent that lapsed overnight is
  noticed the next morning rather than weeks later in a total that stopped
  moving.
- **Retirement outlook**, on the Forecast page, one per person. Give a
  person a birthday under Settings → People and the page projects their own
  accounts from their age today to the age they mean to stop — retire age
  and return are theirs to set, the monthly amount is taken from their
  Forecast plan unless they type another — and says what the sum at the end
  supports a month at a 4 % withdrawal, labelled as the rule of thumb it is.
  No spending, no lump-sum tax, no volatility: one clean line.

### Changed
- The forecast now compounds at the monthly rate that makes "6 % a year"
  exactly 6 % after twelve months, rather than 6 %/12 a month.

## [0.16.1] — 2026-09-11

### Fixed
- The forecast's inputs are kept **per person**. Under a name in the
  header, the monthly amount, return, years and goal are that person's own,
  and the household's plan under Everyone is a separate one — until now a
  single plan was shared, so one person's goal quietly became the next
  person's the moment they flipped the switch. A plan saved by 0.16.0
  becomes the household's; a removed person's plan goes with them.

## [0.16.0] — 2026-09-11

### Added
- **Forecast.** Where the money is heading, from what the accounts add up
  to today. Two questions: *I save this much a month at this return — where
  am I in N years?* and its inverse, *I want this much by then — what does
  it take a month?* A chart year by year with the deposits and the returns
  drawn apart, so "€600k in twenty-five years" is seen for what it is when
  a third of it is your own money; an optional goal line; a table for the
  numbers. The inputs are kept, so next month the same question is answered
  from next month's balance, and under a person in the header the forecast
  starts from theirs. The return is the user's assumption, and the page
  says so.
- **Automatic bank sync.** Every connected account is pulled once a day at
  a time set under Settings (12:00 by default), and a day the machine slept
  through is caught up when it wakes. Until now a sync happened only when
  the button was pressed. Settings also gained a **Sync all accounts now**
  button and shows when the last automatic run was.

## [0.15.0] — 2026-09-11

### Added
- **People.** A household's money is not one pile, and now the app knows
  whose is whose. Under Settings → People, add the people in the household;
  on each account, tick who it belongs to — one person, or several for a
  joint account. A switch appears in the header: **Everyone** shows the whole
  household, a name shows only that person's accounts, on every page —
  Overview, Portfolio, Cash Flow, Budget, Subscriptions, Transactions,
  Categorize and Accounts all add up only what is theirs, and say so under
  the heading. An account ticked for nobody shows under Everyone only, so a
  child's savings do not land in both parents' net worth. The choice sticks
  for the session, and a new account made while looking at one person starts
  as theirs. Removing a person leaves their accounts where they are. This is
  a lens, not a lock: anyone who can sign in can flip it.

## [0.14.0] — 2026-09-11

### Added
- **DKB Depot statements, from the PDFs.** DKB's Depot export is a cash
  ledger: it says what money left the account, not how many units were
  bought or at what price. The Wertpapierabrechnungen in the Postfach say
  exactly that, and now they can be dropped onto the import page — all of
  them at once, or as a ZIP, since there is one per order. Purchases, sales,
  fund issues and redemptions, bond redemptions, dividends, interest, the
  Vorabpauschale, the half-year Sparplan overview and a Depot transfer are
  read, with quantity, price, fee and tax each in its own column. A bond is
  kept as nominal ÷ 100 units at a per-cent price, so a market quote times
  the quantity is its value. A Storno is skipped and named; a Kontoauszug
  PDF is turned away with a pointer to the CSV. The text anchors follow
  Portfolio Performance's DKB extractor, and the parser was checked against
  its corpus of some sixty real (anonymised) statements from 2014 to 2025.
- **Several files per upload.** The import page takes any number of CSVs
  and PDFs, and ZIPs of them, in one go. Each file is recognised on its own;
  one it cannot read is named in the report and the rest are imported around
  it, rather than one stray document failing the lot.

### Changed
- `pypdf` is a new dependency — pure Python, nothing to compile — for
  reading the statement PDFs.

## [0.13.0] — 2026-09-11

### Added
- **DKB CSV import.** The Umsätze export of a Girokonto, Tagesgeld or Visa
  card — Umsätze → period → CSV-Export — drops into a bank account like a
  broker file drops into a broker one. All four layouts are recognised: the
  current portal's files and the pre-2023 ones, which are still what an
  archived download looks like, in their own Latin-1 encoding. The balance
  printed above the column header is recorded as the account's balance,
  because for an account without a bank connection this is the only balance
  the app will ever get. Salary is filed as a deposit and so becomes income,
  interest and fees as what they are, the monthly card settlement as a
  transfer between your own accounts. A row still marked *vorgemerkt* is
  left out and listed, not counted: it changes when it books, and importing
  it now would bring it back as a second row later. Two identical lines on
  one day — two coffees at the same counter — are two transactions, and
  re-importing an overlapping export still adds nothing twice.

## [0.12.0] — 2026-09-11

### Added
- **Market prices.** Holdings are valued at their last market price, from
  Yahoo Finance — free, no key, no account — and every total built from them
  names the day. Until now a holding was valued at the price you last traded
  it at, which is why a portfolio that had risen showed a net worth well below
  what the broker said. The hard half, turning an ISIN into the ticker a price
  source wants, is done once per security and kept; under Settings each
  holding shows the ticker it resolved to, its price and its day, and a field
  to type a different ticker in — one you type is never replaced by a lookup.
  A quote in another currency (a London listing in dollars or pence) is
  converted at the ECB rate. Refreshed on start-up and every six hours in the
  background, and there is an **Update prices now** button.
- A holding no price could be found for is still valued at your last trade,
  and the Portfolio and Overview pages say how many holdings are at market
  and how many at their last trade — the two are never mixed silently.

## [0.11.0] — 2026-09-11

### Added
- **Budget against spent, as a chart.** The Budget page opens with three
  figures — budgeted, spent so far, remaining — and a bar chart with two bars
  per category, the budget and this month's spending, for every category that
  has either. The budget bars follow the fields below as you type, so "what if
  groceries were 400" is answered before Save is pressed. Each row's pace
  column is now a bar with a marker at today's position in the month: the
  question is whether the fill is past the marker, not whether it is full.

## [0.10.1] — 2026-09-11

### Fixed
- **Spending in another currency was missing from Budget and Cash Flow.** Both
  pages summed the base currency only, so a categorised purchase on a dollar
  or franc account never reached its category — and nothing on the page said
  so. Every currency is counted now, converted at the ECB rate of its month
  (or the oldest rate on file for months older than the ninety days kept),
  and both pages say what they converted. An amount in a currency no rate
  covers is still left out, but is now named rather than silently dropped.

## [0.10.0] — 2026-09-11

### Added
- **Entries by hand.** Every account page has an **Add by hand** button for
  the account no bank connection and no export will describe — a pension, a
  share plan at work, an exchange with no CSV. A broker account takes a
  purchase or sale (ISIN, quantity, price, fee, tax, and the statement's total
  if it differs from the arithmetic), a dividend, interest, a fee, tax, a
  deposit, a withdrawal or a transfer; any other account takes everything but
  the trades. The sign is never typed: a fee is money out and a dividend is
  money in, and only a transfer or an "other" row asks for a direction. What
  is typed lands beside the imported rows and counts the same way — a
  purchase is part of the holding, a dividend is income — and can be removed
  again, which an imported row cannot, since it would only come back.
- **A balance, typed in.** An account with no bank connection has a small form
  under its balance: an amount and the day it was true. The overview adds it
  up like any reported balance and says when it was read. The "Add an account"
  page had promised this since v0.1.

### Fixed
- **Rules now apply to what arrives, not only to what was already there.**
  The Categorize page has always said a rule "applies to what is already
  imported as well as to what arrives next" — but nothing ran the rules on a
  bank sync or a CSV import, so a rule only reached new rows once you pressed
  "Categorise what is obvious". New rows now get their category on arrival:
  from the kind where the kind settles it (a fee is a fee, a dividend is
  income), then from your rules. Only rows with no category yet are touched,
  so a correction you made by hand is never overwritten, and the built-in
  guesses stay behind the button, because a guess is something to ask for.

## [0.9.1] — 2026-09-11

### Fixed
- **Every spending category has a row on the Budget page.** A category only got
  a row once something had been booked to it or a budget already existed — so a
  category you had just created under Settings, or one nothing had matched yet,
  had nowhere to type a budget in. Every category that counts as spending is
  listed now, whether it has been used or not. Income, Investment and Internal
  transfer are still left out: nothing is ever spent there, so a budget against
  them would only ever read zero.
- **Changing a category on the Transactions page now leaves a rule behind.**
  The dropdown there set the one row and forgot it, so the same shop came back
  uncategorised with the next import. It now makes a rule from the merchant
  and applies it to every matching transaction, as the Categorize page always
  did — and says how many it reached. Filing something under Uncategorised
  makes no rule.
- The Categorize page's **remember as** field is pre-filled even when the bank
  sent no counterparty: the merchant is picked out of the description, without
  the booking date, card number and reference that the next payment will not
  share. Clear the field to correct a single row without a rule.

## [0.9.0] — 2026-09-10

### Added
- **Exchange rates, from the European Central Bank.** An amount in another
  currency is now inside your net worth rather than beside it, converted at the
  ECB euro reference rate — free, no key, no account. Every total built from
  them names the day they were published, because a number converted at a rate
  nobody can see fails the same way as one that was never converted at all.
- Ninety days of rates are kept, not just today's, so a Sunday falls back to
  Friday's rate rather than to a gap — and so a balance chart has a series
  waiting for it when there is one.
- Rates refresh in the background on start-up, at most once a day, and there is
  an **Update rates now** button under Settings. Nothing waits on either: a page
  renders whether or not the rates arrived.

### Changed
- The charts on the overview include converted amounts. A chart that quietly
  omitted the dollar account while the total above it did not is a chart that
  disagrees with its own page.
- An amount the ECB publishes no rate for — or any amount at all before the
  rates have ever been fetched — still sits beside the total and says so. That
  was the behaviour before this release and it is the behaviour whenever a rate
  is missing.

## [0.8.1] — 2026-09-10

### Fixed
- **The version check did not actually gate the build.** 0.8.0 added a job that
  compares the tag, `__version__` and this file, and said it refused a release
  where they disagree — but the publish step did not wait for it, so it ran
  alongside and the image would have gone out regardless. It is a dependency of
  the publish step now, with the condition that lets an ordinary push to `main`
  through, where that check does not apply.

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

[0.9.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.9.0
[0.8.1]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.8.1
[0.8.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.8.0
[0.7.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.7.0
[0.6.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.6.0
[0.5.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.5.0
[0.4.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.4.0
[0.3.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.3.0
[0.2.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.2.0
[0.1.0]: https://github.com/halvar20000/wealth-dashboard/releases/tag/v0.1.0
