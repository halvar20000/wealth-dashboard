# Changelog

Everything that changed, and why. The same history is readable inside the app —
click the version in the header.

The format follows [Keep a Changelog](https://keepachangelog.com/) and versions
follow [Semantic Versioning](https://semver.org/). While the major is `0`, a
minor bump is a feature and a patch is a fix; nothing here is a stable API yet.

> Versions up to 0.7.0 were reconstructed from the commit history when the
> changelog was introduced. They are accurate about what changed and rounded to
> the day, not the hour.

## [0.68.1] — 2026-09-20

### Changed
- Connecting Trade Republic is one card now, **Settings → Banks → Trade
  Republic**, in three numbered steps — phone and PIN, log in (approve
  in the app or type the code, then Finish), connect — the last one
  offering a new account called Trade Republic or a broker account you
  have. 0.68.0 had split it between Settings and the account page, and
  nothing said where the second half was.

## [0.68.0] — 2026-09-20

### Added
- **Interactive Brokers**, through the Flex Web Service: a token and a
  Flex Query id under Settings, no login and no app of your own; the
  app asks IBKR to generate the statement and fetches it once it is
  ready. Trades at execution level net of commission, dividends with
  their withholding tax folded in, interest, deposits and fees; the
  positions IBKR reports are checked against the rows. The same Flex
  XML, downloaded by hand for any period, is read on the import page
  (`importers/ibkr_flex.py`) — same reader, same ids.
- **Trading 212**, through its public API: a read-only key pair under
  Settings, live or practice account. Filled orders with their wallet
  impact and the fees and stamp duty beside it, dividends net with the
  tax as the gap to the gross, deposits, withdrawals, fees, interest on
  free cash; the positions checked against the rows. The client follows
  the cursor pages and waits out the six-calls-a-minute limit by the
  `x-ratelimit-*` headers.
- **Trade Republic**, through the unofficial interface its web app
  uses — phone number and PIN, the app's approval or a code, then the
  WebSocket protocol (`connect`, `sub`, deltas), spoken with a WebSocket
  client of some sixty lines in the standard library rather than a
  dependency. Order and savings-plan executions, dividends, interest,
  deposits, withdrawals, card payments and tax refunds off the timeline,
  with units, price, fee and tax from each event's detail; paging stops
  at the newest event already known. Marked unofficial everywhere it
  appears: it may stop working any day, and the statement PDFs always
  read.
- The broker connection card on an account page knows all five, and the
  daily sync and *Sync everything* run them like the rest.

## [0.67.4] — 2026-09-20

### Added
- **Pull from Paperless** on the account page, next to *Import a file*:
  this one account against the archive, now, rather than every account
  from the Settings page or waiting for the daily sync. Shown once an
  archive is set up; an account that has not yet said which documents
  are its is sent to its edit page to say so.

### Changed
- The account page's *Import a broker CSV* button is *Import a file* —
  it has taken PDFs, ZIPs and the statement formats for a while.

## [0.67.3] — 2026-09-19

### Added
- The Banks & formats page asks for what it lacks: a bank not on the
  list — or one that reads a figure wrong — is a redacted sample away
  from a reader, and the page says so, with what to black out (name,
  address, account number, IBAN) and what to keep (dates, amounts,
  ISINs, every printed label), and a button that opens a GitHub issue
  form made for it, with a place to attach the file.

## [0.67.2] — 2026-09-19

### Changed
- **Banks & formats** is a page of its own now, in the menu next to
  Accounts and a button on the Accounts page: every bank, broker and
  format the app reads, sorted, with a search box. 0.67.1 had put the
  list at the foot of an account's import page, which is not where
  anyone looks before they have an account to import into.

## [0.67.1] — 2026-09-19

### Changed
- The import page now answers "is my bank read?": a card listing every
  bank, broker and format the app reads — one line each, sorted, with
  its papers (Wertpapierabrechnung PDF, transaction export, Kontoauszug)
  and whether that is a PDF, a CSV or a statement format — with a search
  box over it. It replaces the run of 150 names in a sentence that
  nobody could find anything in.

## [0.67.0] — 2026-09-19

### Added
- **Cash and card statements read by their columns**: DBS / POSB, OCBC,
  UOB, Standard Chartered, Trust, HSBC, Citibank and American Express in
  Singapore, Maybank in Malaysia, Bank of America, and Zürcher
  Kantonalbank's Kontoauszug. These statements say withdrawal or
  deposit, charge or payment, by the column a figure sits in, which the
  word-by-word reading of every other spec throws away — so a spec can
  now ask for the PDF with its layout kept (`Spec.layout`), and a table
  description (`app/importers/pdf/layout.py`) turns the columns into
  rows: two money columns placed by their headers, or one amount column
  with CR, brackets or a sign marking the credits; the statement's own
  date lending its year to rows without one, December before a January
  statement; a booking's further lines joined to its description;
  balance and total lines left out. Scored against the synthetic
  statements of the monopoly project: 117 of 117 rows.

## [0.66.1] — 2026-09-19

### Fixed
- MT940 in its dialects. Run against some eighty real statements from
  the wolph/mt940 and jejik-mt940 test corpora (ABN AMRO, ING, Rabobank,
  Knab, SNS, Triodos, PostFinance, Sparkassen, Volksbanken, Commerzbank,
  Deutsche Bank, LBBW, OLB, mBank, Citi, Sberbank, Raiffeisen), the
  importer had five things to learn: the SWIFT envelope's `{4:` opener
  on a line of its own, an entry date left as four blanks, a blank
  between the amount and the type, a type such as `NOV ` or `MCI0`, a
  Sparkasse wrapping the amount onto the next line — and the 30th of
  February, which one bank books. `:86:` continuation lines are joined
  without a blank, as the fixed width means them to be, so a `?` field
  marker split across two lines is whole again. Every one of the eighty
  now reads.

## [0.66.0] — 2026-09-19

### Added
- **The statement formats every bank writes alike: CAMT.053, MT940 and
  OFX.** Not one bank's file but a standard, so no mapping and no
  bank-specific reader: drop in what the banking portal offers under
  "Export", "Kontoauszug als XML", "SWIFT MT940" or "Download to
  Quicken". CAMT.053 / CAMT.052 (ISO 20022, every European
  online-banking portal) is read in all its versions, namespace or not,
  with the counterparty's name and IBAN, the SEPA end-to-end and
  mandate references, a batch booking as one row per leg, pending
  entries left out and counted, the bank's own entry reference as the
  id and the booked closing balance taken. MT940 (`.sta`, the older
  portals and business banking) with the German `?`-structured `:86:`
  details and the SEPA markers inside them, reversals with their sign,
  the `:62F:` balance. OFX / QFX (North American and British banks and
  brokers) in its SGML and XML dialects, bank statements by `FITID`, and
  brokerage statements — buys, sells, income, reinvestments, cash
  movements — with units, price, commission, withholding and the
  security named through the SECLIST. Interest, fees and taxes are told
  from the bank's own codes where the format carries them, from the
  words otherwise.

## [0.65.0] — 2026-09-19

### Added
- **Statement PDFs of fifty-two more banks and brokers — every bank in
  Portfolio Performance's corpus now has a reader**, 132 in all. apoBank,
  Solaris, V-Bank, Bank11, Audi Bank and Volkswagen Bank, Ford Money,
  Bigbank, Advanzia, Suresse, Ayvens, Sberbank Europe, ABN AMRO / MoneYou,
  Orange Bank and Nordax (Raisin), Anadi Bank, Bundesschatz, Ginmon's fee
  invoice, the BAWAG card statement, BSDEX and Debitum, Crowdestor,
  Modena; Revolut, Trading 212, Whitebox; in Switzerland Liberty Vorsorge
  (whose PDFs come out with blanks inside every word), St. Galler,
  Thurgauer, Basellandschaftliche and Freiburger Kantonalbank, radicant,
  VZ Depotbank, Simpel / own360; in the UK and Ireland AJ Bell, Hargreaves
  Lansdown, Aviva, Fidelity; Openbank in Spain, Directa in Italy,
  MeDirect and vdk bank in Belgium, Crédit Mutuel / Suravenir in France;
  Firstrade, Alpaca, E*TRADE, Score Priority and Lime Trading,
  Computershare in the US; Wealthsimple in Canada, Stake and CommSec in
  Australia, cetesdirecto in Mexico, KFintech / CAMS's Indian Consolidated
  Account Statement. The engine takes `$` and `£` as currencies and
  completes `dd-mm` dates from a statement's year as it did `dd.mm.`.

### Changed
- The corpus scoreboard now covers 2,679 documents (every folder has a
  reader to run) and reads 68 % of them to the cent.

## [0.64.0] — 2026-09-19

### Added
- **Statement PDFs of forty-three more banks and brokers**, which with
  0.63.0 makes some eighty. Trade Republic in all five of its languages —
  Wertpapierabrechnung, Sparplan, Dividende, Zinsabrechnung,
  Vorabpauschale, Steuerabrechnung, and both Kontoauszug layouts, the
  2024 one put back on one line per row from a table that breaks its
  dates over three lines and its sign into two columns. DEGIRO's
  Transaktionsübersicht and Kontoauszug in nine languages, the
  withholding tax and the currency exchange folded into the dividend they
  belong to. DekaBank (Depot-Tagesauszug and Quartalsbericht), ebase / FNZ,
  FIL Fondsbank, Quirin Privatbank / quirion, Tradegate, OLB, Vanguard
  Invest, Sunrise, UniCredit / HypoVereinsbank, Raisin and Upvest in their
  own layout; the cash and card statements of N26, C24, Renault Bank
  direkt, J&T Direktbank, akf bank and Barclays; BISON, Bondora and
  Estateguru; in Austria 3 Banken and Schelhammer; in Switzerland and
  Liechtenstein WIR Bank / VIAC, findependent, neon, Hypothekarbank
  Lenzburg, Bank SLM, Saxo Bank, Credit Suisse, LGT, Liechtensteinische
  Landesbank / wiLLBe, Pictet, and a spec for the Swissquote paper the
  hand-written readers do not know; BoursoBank and Bourse Direct in
  France, BBVA in Spain, Sydbank in Denmark, Questrade in Canada,
  SelfWealth in Australia, Tiger Brokers in Singapore.
- The engine learned what these needed: a `refund` group for banks that
  print charges with a minus and credits bare; `split` rows for a tax
  credit or fee rebate the booked total already held; a `transfer` regex
  and `skip` kind; a tax page without an after-tax figure taking its
  taxes off the gross; a credit printing gross beside net getting the
  difference as tax; Spanish, Italian and French month abbreviations and
  `05-Dez-2024` dates; Swiss apostrophes in any notation.

### Changed
- The scoreboard reads Portfolio Performance's assertions in both of
  their spellings — a quarter of them had been skipped — so the corpus
  is 2,529 documents now and the honest score of the 0.63.0 readers is
  53 %, not the 60 % claimed; with this batch the whole corpus reads at
  66 %. It also prefers the row of the asserted kind and units when a day
  has several, counts a repeated assertion once, and runs every reader a
  bank has.

## [0.63.0] — 2026-09-19

### Added
- **Statement PDFs of thirty-seven more banks and brokers.** comdirect
  (even the letter-spaced Steuermitteilungen), Commerzbank (letter-spaced
  throughout), Deutsche Bank, TARGOBANK, ING, Consorsbank, Baader
  Bank (Scalable Capital to 2024, finanzen.net zero, Smartbroker+ — German
  and English paper), Scalable Capital's own, flatex / FinTech Group Bank,
  DAB BNP Paribas, onvista, S Broker and the Sparkassen, Postbank, the
  Volksbanken and Raiffeisenbanken, 1822direkt, GenoBroker, MLP, Merkur
  Privatbank, Santander, UmweltBank, Weberbank, NORD/LB, NIBC and Sutor
  Bank; in Austria easybank, DADAT, Hello bank! and Erste Bank / Brokerjet;
  in Switzerland PostFinance E-Trading, Zürcher Kantonalbank and UBS; in
  Belgium and France Keytrade, KBC and Arkéa/Fortuneo (first passes).
  Purchases, sales, dividends, interest, Vorabpauschalen,
  Sammelabrechnungen, and the Giro or Verrechnungskonto statements where
  the layout allows. Under the hood a new engine reads any bank from a
  spec — a few dozen anchors per bank in `app/importers/pdf/` — and two
  shared layouts (dwpbank's, which most German banks print, and DAB's)
  cover a dozen banks each with one spec, plus a catch-all for any bank on
  the same paper. Every spec is scored against Portfolio Performance's
  corpus of some 2,700 real, anonymised statements with
  `tools/statement_scoreboard.py`; this batch reads 60 % of 1,635 such
  documents to the cent, the rest being old layouts, bank-statement pages
  and edge cases the scoreboard lists by name. The corpus stays out of the
  repository; the specs are this project's own.

## [0.62.1] — 2026-09-19

### Fixed
- Pulling from Paperless-ngx fetched the listing but every download
  answered **406**: the file was asked for as `application/octet-stream`,
  which Paperless's content negotiation refuses. Asked for as `*/*` now.
  Documents recorded as failed by the first pull are fetched by the next
  one after *Try the unread ones again*. Found by the first person to try
  it, on Swissquote statements.

## [0.62.0] — 2026-09-19

### Added
- **The weekly e-mail.** Once a week, on the weekday you pick, a mail
  with the week: net worth and its seven-day change, then every broker
  and crypto account with its value, the week's price move, the gain since
  purchase, the holdings with their own week, the dividends of the last
  thirty days and the trailing year — and the indices the app tracks, so
  a move sits beside what the market did. Set up under Settings →
  Assistants with your own SMTP server (Gmail with an app password
  works); *Send a test mail* proves the wiring and *Preview today's mail*
  shows it in the browser first. It goes out after the daily sync, once
  per ISO week, catching up a day the machine slept through. The week's
  move is the price effect only — a deposit during the week is not a
  gain — and every figure is the one the pages show, never re-priced for
  the mail. The password is kept beside the bank key. This is the one
  thing the app sends anywhere but your bank: to your own mailbox.

## [0.61.0] — 2026-09-19

### Added
- **Statements pulled from Paperless-ngx.** Under Settings → Banks &
  brokers → *Document archive*, give the app the archive's address and an
  API token; on each account's edit page, say which documents are its — by
  tag, correspondent or search query. Every new document is fetched on the
  daily sync, or with *Pull now*, and run through exactly the readers an
  upload goes through. Each one is remembered — imported, not read, or
  failed to fetch — so a pull lists once and imports nothing twice, and a
  document no reader understood is listed with a link back into Paperless
  rather than skipped in silence; *Try the unread ones again* after a new
  reader ships. A scanned statement, which is only an image to the PDF
  readers, gets Paperless's own OCR text offered to them before it is given
  up on. The archive is read, never written. Asked for in the first
  feedback the app received.

## [0.60.0] — 2026-09-19

### Added
- **A CSV template of the app's own.** Anyone making a file themselves —
  from a spreadsheet, a script, a document archive — now has a target to
  aim at: name the columns `date, amount, currency, description,
  counterparty, kind, isin, security_name, quantity, price, fee, tax, id`
  (any order, any subset with a date and an amount) and the file is
  recognised outright, with no mapping page in the way. Documented in the
  README with an example. Asked for by the first person to write in.
- **A row id column**, for the template and for any mapped CSV. A bank's
  own reference — or yours — identifies the row, so a re-export after a
  corrected description is still the same row rather than a second one.
  Without it a row is identified by what it says, as before.

## [0.59.0] — 2026-09-17

### Added
- **Upcoming.** Every other page looks back; this one carries today's
  cash forward through what is known to be coming — the bills as
  declared on the Bills page, the subscriptions the app has detected
  and nobody declared, the salary as the newest payslip had it, on
  the day it was paid — and says where that leaves the balance over
  30, 60 or 90 days: the lowest it gets, and the day it would cross
  zero, named with the bill that does it. Income lands before bills
  on the same day, because that is what a paycheck is for; a balance
  that starts below zero — an overdraft, a card — is not "going
  negative", so the alert only fires when the line is crossed; a bill
  without a fixed amount is carried at what it last cost and marked
  as an estimate; a missed bill is expected today. Under Money, after
  Bills. Loan instalments count only when declared as a bill: the app
  knows what a loan costs, not which account pays it.

## [0.58.2] — 2026-09-17

### Fixed
- **The versions agree again.** 0.58.1 reached PyPI without its
  changelog entry, and its image was refused for the same reason.
  Nothing else changed.

## [0.58.1] — 2026-09-17

### Fixed
- **The favicon in the container.** `app/static/icon.png` is a link
  to the icon at the repository root, which the image never carried —
  so every page in every container so far named an icon that was a
  404. The first run of the smoke test found it and refused to
  publish 0.58.0; the image now ships the file.

## [0.58.0] — 2026-09-17

### Added
- **A loan follows the lender's figure.** A balance on a loan account
  that did not come from the schedule — typed in from the bank's
  letter, synced, or moved in with the account — now anchors the
  schedule from that day on: the first instalment after the reading
  starts from what the lender said, not from what the sum said, and
  the arithmetic carries it forward from there. A rate change, a fee,
  a rounding rule nobody wrote down all show up in that one number
  and in nothing else, and until now the schedule overwrote it the
  next morning. The rows before the reading stay as computed, so the
  history keeps its line; the loan's page says which reading it runs
  from and marks the row where it takes over, and "repaid so far" is
  what the lender has been paid off, not what the sum expected.
- **A copy before an upgrade.** The first start of a new version
  copies the database aside — `backups/wealth-<old version>-<date>.db`
  next to the live file, made through SQLite's own backup call so the
  write-ahead log is in it — before a single column is added. The
  last five are kept. Migrations here only go forward, so "install
  the old version" was only half a rollback; the other half is now on
  disk, and the install guide says how to use it.
- **The container is not root.** The image now starts through an
  entrypoint that gives `/data` to `PUID:PGID` (`1000` unless told;
  the Unraid template says `99:100`, like the other containers) and
  drops to that user before the app runs — so a folder Docker made as
  root on the first start works without a chown step, and the process
  holding your finances is not root. `--user` skips all of it;
  `PUID=0` keeps root for a mount that will not take a chown.
- **The image is run before it is published.** The build now starts
  the container four ways — Unraid's, the defaults, `--user`, and
  root — waits for it to answer, checks the first-run page and every
  stylesheet and script it names, the version it reports, the user it
  runs as and who owns the database it wrote, and reads its log for
  tracebacks. A `latest` that fails any of that no longer reaches
  every Unraid install by lunchtime.

## [0.57.0] — 2026-09-17

### Added
- **Any payslip, mapped once.** A payslip PDF no parser here was
  written for is no longer a dead end: the app lists every line that
  carries an amount, a month or a date, suggests what each one means
  from a catalogue of what payslips call things — Bruttolohn, salaire
  brut, gross pay; Quellensteuer, prélèvement à la source, PAYE; AHV,
  URSSAF, National Insurance; BVG, LPP, pension — in the languages
  they are printed in, and you confirm, once. The mapping is kept
  under the sheet's own markers, the employer and the earner, so next
  month's sheet is recognised by itself, the way a Degiro file is.
  Deductions are stored as money out whichever way the sheet prints
  them, the numbers are read the German, Swiss, French or English
  way from the sheet itself, and a glued sheet with a printed O for a
  zero still splits into basis, rate and amount. The preview says
  whether gross less every deduction is the net — the one check that
  catches a missed line. Mappings are listed under Settings › Banks,
  beside the CSV ones, and can be forgotten there.

## [0.56.0] — 2026-09-16

### Added
- **Payslips, and an Income page.** A Swiss Lohnabrechnung as a PDF
  imports into the account the net salary lands in — two layouts are
  read: the SAP sheet of a large employer, with its wage codes and
  employer block, and the small employer's sheet with Bruttolohn,
  AHV, ALV, BVG and Nettolohn, even when its text arrives with the
  spaces gone and an O where a zero was printed. The sheet is kept
  whole, and what the bank never sees is booked onto the account,
  zero-sum: the tax at source and each side's pension contribution,
  grossed up as salary and then paid as tax or moved as investment.
  The Income page shows every earner the sheets name — the earner
  comes from the sheet, not from a setting — with net, tax at source,
  the pension on both sides and the employer's cost, a bar per month
  and a table per year, and says where the employer's side is only
  the statutory floor because the sheet prints none.

## [0.55.0] — 2026-09-16

### Added
- **A loan has a page of its own.** Where it stands today — outstanding,
  repaid so far as a share of the original, the original loan and what
  it was drawn as, the payoff date and the instalments left — over the
  balance across its whole life with *today* and *paid off* marked on
  it, a bar per instalment split into interest and capital, and the
  full amortisation schedule with the future faded. A loan in another
  currency than the base one has a switch to see every figure at
  today's rate. The loans list links each loan to its page.
- **A loan account that already exists can be given its terms.** An
  account moved in from another app arrives as a loan with its
  readings and nothing else; its page now asks for the principal,
  rate, first instalment, rhythm and payment — and, optionally, what
  the loan was drawn as in another currency (€150 000 for a CHF
  mortgage) — and from then on the balance follows the schedule.

## [0.54.2] — 2026-09-16

### Fixed
- **A coin's move to the wallet is priced from the lots as they are
  now, not as they were when it was first booked.** The counterpart
  of a withdrawal used to keep the cost it was given the day it was
  created — and rows moved between accounts since, or a deposit
  priced since, had changed what the lots say, leaving a cost basis
  of €5,980 on coins that cost €12,580. The catch-up now re-prices
  every move in date order on every run — the button, and every
  sync — and a second run changes nothing.
- **The network fee of a withdrawal leaves with the coins.** An
  earlier parser booked a withdrawal without the fee Kraken took with
  it, a few satoshi a time — the reason a balance that should agree
  to the satoshi did not. Every sync now re-reads its stored ledger
  rows against Kraken and puts the quantity and the fee right, and
  the wallet receives what was sent: the fee's units are gone.

## [0.54.1] — 2026-09-16

### Fixed
- **A Kraken withdrawal made on the day of the move-in was never
  booked.** The move from Financial Planner leaves an account a date
  up to which its ledger is on record, so a file covering the same
  days is not booked twice — and that cut-off also stopped the rows
  Kraken names by id, which are never booked twice anyway. A wallet
  read 0.024 BTC where Kraken had 0.0015, and the sync said so every
  day. Rows under this app's own ids — Kraken, Saxo, Trade Republic,
  Crédit Agricole — now pass the cut-off; the next sync books the
  missing withdrawal, and into the wallet if one is named.
- **"Last sync: never" over a page of synced rows.** A balance that
  does not add up is a finding, not a failed sync: the rows were
  fetched and stored. The sync's time is recorded, and the finding
  shown beside it.

## [0.54.0] — 2026-09-16

### Added
- **An account's rows can move to the account they belong to.** The
  account page lists where its rows came from — the move-in from
  another app, an exchange's sync, a file — and each source can be
  handed to another account whole. For the account that was two
  things at once: a wallet's history moved in from the old app,
  landing in the account an exchange is linked to, so the exchange's
  balance check could never agree. The rows keep their ids, so
  nothing is imported twice afterwards.
- **"Book earlier moves into the wallet"**, a button on the exchange
  account, and deposits now count too where the wallet held the
  coins: a deposit is taken from the wallet only if the wallet had
  that many units on that day, so it can never take coins it never
  held. The cost travels with the units in both directions — exactly
  what the lots gave up, under FIFO or average cost — so the two
  accounts' cost bases add up to what one would have held. Nothing
  is booked twice, so the button can be pressed again after rows
  have moved.

## [0.53.0] — 2026-09-16

### Fixed
- **A Kraken fill moved in from Financial Planner is no longer counted
  twice.** Up to 0.46 the move-in kept a Kraken trade's id bare —
  `TUT7MA-K67YX-X6Z4TJ` — where the Kraken sync writes
  `kraken:trade:TUT7MA-K67YX-X6Z4TJ`, so the same buy arrived once
  from each and the coin's cost basis counted it double: €3,201 too
  much on one wallet. On the first start after this update the old
  app's copy goes wherever Kraken's exists (Kraken's carries the fee
  the way this app books a buy), and a copy on its own takes the id
  the sync would give it. Rows edited by hand are left alone.

### Added
- **Naming a wallet books the coins that already left.** A withdrawal
  synced before a wallet was named was a coin that simply left; naming
  the wallet later did not bring it back. It does now, once: every
  earlier withdrawal without a counterpart is booked into the wallet
  at the cost it carried, and the page says how many and how much.
  Withdrawals only — where a coin withdrawn went is what the field
  says; where an earlier deposit came from is not known.

## [0.52.1] — 2026-09-16

### Fixed
- **The crypto page's cost basis is what the coins still held cost.**
  It was "net invested" — buys minus sales — which is the same number
  until a coin is sold or moved to another wallet, and then carries a
  realised gain, or the cost of units no longer there, and calls it
  unrealised. It is now the lots, under the method chosen in Settings
  (FIFO or average cost), as the securities pages already did; where
  the two differ the card says what net invested is too.
- **A wallet chart that starts below nothing has no percentage.** The
  rows of a wallet can begin with units leaving — a fee taken in the
  coin before the first buy in the export — and the change "of
  −45 204 %" that produced was arithmetic, not information.

## [0.52.0] — 2026-09-16

### Changed
- **The overview reads like a statement.** The net worth stands alone
  at the top — `€1,027,527`, symbol first, no cents — over *Assets ·
  Liabilities* and the parts below them; the change since the start
  of the range is a pill beside it with its arrow, its percentage and
  the range it refers to; the line is green on a warmer card. Under
  it, four tiles: *Liquid + investments*, the other assets (or the
  debt), *This month* against thirty days ago and *YTD* against
  1 January — each change coloured by its sign, and "no reading to
  compare with yet" where there is none. Then two donuts, *by asset
  class* and *by account*, each with its total in the middle. The
  bank connections moved below the accounts; the transaction count
  and the largest holding left the page.
- **English groups thousands with a comma** — `1,234.50 EUR` — as
  English does; German, Spanish and French keep their dot and space.

## [0.51.0] — 2026-09-15

### Added
- **It says when there is a newer version.** Once a day the app asks
  PyPI which version is the newest — one small request for a public
  page, with nothing about you in it — and when the answer is newer
  than what is running, the version in the menu gets a dot and, on
  the changelog page, one sentence with the one thing to do: `pipx
  upgrade` for a pipx install, update the container, update the
  add-on. Unraid and Home Assistant already told you; a pipx install
  had nobody to. A switch under Settings, on by default.

## [0.50.0] — 2026-09-15

### Added
- **`wealth-dashboard install`: an icon, and running after a reboot.**
  One command puts Wealth Dashboard in the applications menu and on
  the desktop and starts it at login — a systemd user service on
  Linux (an autostart entry where there is no systemd), a LaunchAgent
  and a small app bundle on macOS, Start Menu, desktop and Startup
  shortcuts on Windows — all per user, nothing needing an
  administrator. Flags given to `install` are kept by the shortcut.
  `wealth-dashboard uninstall` removes them; the data stays.
- **Starting it twice opens it.** A second `wealth-dashboard` on a
  port where one is already answering opens the browser on the
  running copy instead of dying with "address in use" — so the icon
  always ends on the dashboard, service or no service.
- **A favicon.** The icon in the tab, and in the shortcut.

## [0.49.0] — 2026-09-15

### Added
- **`pipx install wealth-dashboard`.** The app is a Python package on
  PyPI, for Linux, macOS and Windows: one command installs it, one
  starts it, and it opens in your browser. Installed this way its
  data lives in your user folder — `~/.local/share/wealth-dashboard`,
  `~/Library/Application Support/wealth-dashboard`,
  `%LOCALAPPDATA%\wealth-dashboard` — where the next upgrade will not
  touch it; a checkout keeps `data/` beside the repo as before.
- **A command line.** `wealth-dashboard --help`: `--port`, `--host`
  for the LAN, `--data DIR`, `--no-browser`, `--version`. The
  environment variables still work, because that is how a container
  is told the same things.

## [0.48.0] — 2026-09-14

### Added
- **A Home Assistant add-on.** Add this repository under *Add-on Store →
  Repositories* and the dashboard installs like any other add-on: the
  same image Docker and Unraid run, opened from the sidebar through
  ingress, behind Home Assistant's login, with its data in the add-on's
  folder where a Home Assistant backup picks it up. Nothing to
  configure — the timezone is Home Assistant's and everything else is
  set in the app. The add-on's version is the app's, so a release tag
  is what makes it appear as an update.
- **Runs under a path prefix.** A reverse proxy that mounts the app at
  `/wealth/` — nginx or Traefik with `X-Forwarded-Prefix`, Home
  Assistant's ingress with `X-Ingress-Path` — now gets every link,
  form, chart request and redirect with the prefix on. Before, the
  first click left the app.
- **Balance over time, on the account page.** Every account with more
  than one reading draws them: a pension statement by statement, a
  loan instalment by instalment, a cash account sync by sync. The
  newest reading of a day stands for the day; between readings the
  last one holds. The page used to show the newest figure alone.

### Changed
- **The session cookie is called `wealth_session`**, not `session`.
  Behind ingress every add-on shares one origin, and two apps both
  naming their cookie `session` sign each other out. Updating signs
  you out once.

## [0.47.0] — 2026-09-14

### Added
- **A coin sent to your own wallet is still yours.** On a Kraken
  account, name the wallet — an account of type Broker — and a
  withdrawal becomes a move between the two: the units leave Kraken
  and arrive in the wallet at the cost they carried, so the holding,
  its cost basis and the household's total survive the trip; a coin
  sent back in is the same the other way round. Without a wallet
  named the units simply leave, which is what Kraken's balance says.
- **A loan has a history from its first instalment.** Adding or
  editing a loan writes a reading at every instalment date already
  past, from the schedule, so the debt has a line on the history
  chart rather than a single figure from the day it was typed in.

### Fixed
- **Moving in: a Kraken trade from a Kraken CSV kept its bare id** and
  was booked a second time by the Kraken sync under this app's — the
  eight rows counted twice, and an opening row to make the holding
  agree made the cost basis meaningless. Any Kraken trade id now gets
  this app's prefix, whichever file it came through.

## [0.46.1] — 2026-09-14

### Changed
- **The move-in plan says which accounts already hold rows** — beside
  each name in the dropdown — and says outright to pick the account
  you already have for a bank rather than a second one, and what
  happens when the picked account has rows of its own from a file:
  the old app's rows of the same days are booked beside them unless
  the ids match, and the import can be undone on that account.

## [0.46.0] — 2026-09-14

### Added
- **The accounts on the overview read like a balance sheet.** Four
  groups — Cash & banks, Investments, Pension, Liabilities — each with
  its subtotal, every account worth its cash and its holdings together
  (a broker is what it holds, not the cash left in it), in its own
  currency where everything in it is in that currency and in the base
  currency always, and the net worth at the foot. What the pie chart
  said only on hover.

## [0.45.0] — 2026-09-14

### Added
- **Finary's crypto transaction export imports.** A buy is a buy of
  the coin at the fiat sent per unit; a swap is a sale of the coin sent
  and a buy of the coin received, both at the euro value, so the
  disposal and the new cost basis are both on record; a withdrawal to
  a wallet of your own is no row, since the coins are still yours.
  Rows carry Finary's own ids, the same ones the move from Financial
  Planner brought, so the export can be imported over them.

## [0.44.1] — 2026-09-14

### Fixed
- **The Portfolio page crashed on a holding the rows do not add up to.**
  A sale before its purchase puts the position below zero for a while;
  the chain-linked return then came out below −100 %, annualising it
  took a root of a negative number, and the page died on a complex
  number. Such a chain is no return now (—), and a total loss
  annualises to a total loss.

## [0.44.0] — 2026-09-14

### Added
- **Leave the house out — or the pension.** A switch on the overview's
  headline per asset that is wealth but not money: property, pension
  fund, P2P lending. Off, the figure, the line and the change since
  the start of the range are drawn without it, and a line says what
  the whole is. Remembered per browser.
- **The history line reaches back to the old app's records.** Moving
  in brings the net worth Financial Planner recorded on the days before
  it kept per-position lines — 142 days, for the household this was
  written for — and the line uses them up to the day the readings
  cover every account, then this app's own arithmetic. Before the
  first recorded day the line is not drawn: what this app can work out
  for those days is a fraction, and a fraction draws a step.

### Fixed
- **A day the old app snapshotted twice came through doubled.** The
  move summed the lines of every snapshot of a day, and a manual
  snapshot beside the nightly one doubled every balance-only account
  for that day — a spike of a million in the line. The move reads one
  snapshot per day now, and a reading from the move that is twice both
  its neighbours is halved once on start.

## [0.43.1] — 2026-09-14

### Fixed
- **The collapsed sidebar's flyout stayed open on the page it led to.**
  The group holding the current page is "open", and the wide sidebar's
  rule for an open group outranked the collapsed sidebar's "hidden" —
  so the flyout of the page you had just chosen sat beside the sidebar
  for good. Collapsed, only a hover or a tap opens a flyout now.

## [0.43.0] — 2026-09-14

### Added
- **The trades on the holding's chart.** A mark per buy, sale,
  dividend and split on the day it happened, at that day's value, with
  what it was in the tooltip. A switch beside the chart, remembered:
  on by itself up to a dozen marks, off beyond — a savings plan is
  forty marks a year and would bury the line.
- **Sold out**, under the holdings on the Portfolio page: every
  security with rows and no units left — sold, delisted, exchanged
  away — with what went in, what came out, its income and what it
  made by lots. A position sold down to nothing used to vanish from
  the page, and its gain with it.
- **Any row can be removed, and stays removed.** Until now only a row
  typed in by hand could go, because an imported one would come back
  with the next import of the file. Now its id is remembered, and an
  import or a sync leaves it out. "Remove this row" sits under the
  correction form on the holding page and beside every row on the
  account page, and asks once.

### Fixed
- **The collapsed sidebar's flyout could not be closed on a touch
  screen.** It opened on hover, a tap on a tablet is a hover that never
  ends, and the click did nothing. A tap now opens it, a second tap or
  one anywhere else closes it; hover still works where there is a
  pointer that hovers.

## [0.42.1] — 2026-09-14

### Fixed
- **Moving in: the opening positions follow the account you pick.**
  They were worked out against the account the plan proposed; choosing
  another in the dropdown — the Trade Republic already synced here,
  say — could have written an opening row on top of rows that account
  already holds. They are now worked out again on confirmation, for the
  accounts chosen, with what those accounts already hold counted in.

## [0.42.0] — 2026-09-14

### Added
- **Move in from Financial Planner** — Accounts › "Move in". Upload
  the old app's wealth.db, look at the plan — every account and what
  it becomes, where its rows go (a new account, or one already here of
  the same name), the opening positions, what is left behind — and
  confirm. Then it is all here: the accounts by type (a crypto wallet
  as a broker holding `CRYPTO:` coins, the mortgage as a loan, the
  pension, the P2P books and the house as themselves), every row of
  the ledger under its old id, the holdings — with an opening row where
  the ledger did not add up to them, at the old app's cost — the daily
  balance snapshots as readings, so the history chart reaches back to
  them, the price history, each security's symbol, and the categories
  only the old app had. On the household this was written for, the
  net worth after the move is the old app's to 0.006 %.
- **"Ledger on record until"** on an account: rows moved in from
  another app carry its ids, which this app's importer would not
  produce, so an export or a bank sync covering those days would book
  them again. The move sets the date on the accounts where that
  applies; an import or a sync leaves that span alone; the account's
  edit page shows it and can clear it.

### Fixed
- **A bank row's id now carries its day and amount.** Crédit Agricole
  sends base64 of the description as the entry reference, identical for
  every recurring payment, so a sync trusting it kept the first "ECH
  PRET" of the year and silently dropped the rest as duplicates. Rows
  already synced get the new shape on start.

## [0.41.0] — 2026-09-14

### Added
- **Three more account types: Pension fund, P2P lending, Property.**
  Their balance is wealth but not cash — a pension cannot be touched
  for twenty years, a house cannot be spent — so the overview keeps
  them in a pile of their own, "Other assets", beside cash and
  securities, and the net worth counts all three. In the allocation a
  property is real estate, a P2P book is debt paper, a pension fund is
  its own thing; and the pension is left out of what the region and
  bucket shares are measured against, since it cannot be moved. Money
  sent to a platform or a pension is filed as moved, not spent.

## [0.40.0] — 2026-09-14

### Added
- **Add a transaction on the holding's own page.** A card beside
  "Record a split": pick the account, what happened, the date and the
  numbers — the ISIN and the name are the page's. Until now a row for
  one holding meant the account's add page and the ISIN typed by hand.
- **A dividend, a fee or a tax can belong to a holding.** Added from
  the holding page it is filed against that ISIN, so it shows among the
  holding's rows and in its income — as an imported dividend does. The
  account's add page offers the ISIN for those kinds too, optionally.

## [0.39.0] — 2026-09-14

### Added
- **Income has categories.** Cash Flow counted one category, "Income",
  and a category of your own could only be spending or not — so a
  salary, the rent a flat brings in and the interest on a savings
  account were one green bar, or invisible. Categories now have a
  third group, *income*: three come ready — Salary, Rental income,
  Interest & dividends — and any category can be set to count as
  income under Settings. Cash Flow adds up everything in the group,
  the income bar is stacked by category in its own colours, and the
  breakdown table says where it comes from. Dividends and interest
  are filed under Interest & dividends from now on, and the rows
  already filed as plain income move there once, on the first start.

### Changed
- The benchmark card says plainly that investing bit by bit does not
  put you behind the index there: the line is time-weighted, every
  deposit counts from the day it arrived, and the return that feels
  the timing is the money-weighted one on the Portfolio page.

## [0.38.1] — 2026-09-14

### Fixed
- **A Trade Republic dividend grew the position.** The export fills
  `shares` and `price` on a dividend row — the position it was paid on
  and the amount per share — and the importer stored them as a
  quantity and a price, so everything that sums quantities counted the
  whole holding again on every payout: a hundred shares with eleven
  dividends showed as twelve hundred, and the net worth with them. Only
  a row that changes what is held — a buy, a sale, a transfer, a split
  — keeps its shares now, and rows imported the old way are put right
  when the app starts, unless you corrected them by hand.

## [0.38.0] — 2026-09-14

### Added
- **Disconnect**, on the account page of a connected bank account. The
  link goes — and the consent is ended at Enable Banking too — while
  the account, its balances and its history stay. Until now the only
  way to end a connection was to delete the account with everything in
  it, or to wait for the consent to run out and live with the error.

### Fixed
- **A renewed consent replaced the connection instead of adding one.**
  Every bank account gets a new Enable Banking uid per session, so
  re-connecting after the ninety days put a second link on the account,
  and the page, "Sync now" and the nightly job kept finding the dead
  one. Worse: had the bank's identification hash changed between the
  two, every booking would have arrived twice under two ids. Now an
  account has one link, and a renewal moves it to the new session; a
  bank account that comes back with a different hash on the same IBAN
  keeps the namespace its bookings are already stored under; and the
  further accounts a consent covers — a savings account beside the
  current one — are created once, not once per renewal. A leftover
  second link from before is dropped by the next renewal.

## [0.37.1] — 2026-09-14

### Fixed
- **The Portfolio page took ten to twenty seconds** once the full ECB
  history was on record. Every holding's prices are turned into its
  own currency, and the converter read the whole rate table — two
  hundred thousand rows since 1999 — from the database twice per
  holding, and the return figures three more times. The table is now
  read once and kept, and re-read only when it has changed: after a
  refresh, a backfill, a restored backup. Same figures, under a second.

## [0.37.0] — 2026-09-13

### Added
- **A retirement plan**, under Planning, per person. The Forecast's
  outlook says what the pile supports at 4 %; this one has the
  retirement in it: what goes in until you stop, growing a little a
  year; what you will spend each month from then on, item by item,
  each with the ages it runs from and to; what will still come in — a
  state pension, a rent; a return before and after, fees, inflation,
  tax on withdrawals. Walked a year at a time to a horizon, it says
  the pile at retirement, the capital required, how far along that is,
  and the age the money runs out or what is left — with a chart of
  the projection against the required line (from retirement, what
  funds the rest; before it, the on-track path), a year-by-year table,
  and a switch between nominal and today's money.
- **What a goal is for.** The Goals page opens with a row of cards —
  a home, a car, education, a wedding, an emergency fund, a trip,
  something else — that pre-set the form, and a card that leads to
  the retirement plan; each goal shows what it is for.

## [0.36.1] — 2026-09-13

### Added
- **Undo an import.** Every file import is on record — the file, the
  importer, when, how many rows it brought — and the account page
  lists the recent ones with an *Undo* that takes back every row that
  import brought and only those; a row a re-import found already
  there stays with the import that first brought it. For a CSV that
  came through a mapping, a tick forgets the mapping too, so the same
  file asks again instead of repeating the mistake. Forty rows edited
  by hand was the wrong answer to a wrong mapping. (Dominique.)
- The mapping page now says, above the sign box, how signs are read
  — a named kind decides, otherwise the file's sign stands — and
  warns when the first rows look like purchases with money coming in,
  which is nearly always the signs the wrong way round.

## [0.36.0] — 2026-09-13

### Added
- **A REST API.** Every MCP tool is also a URL — `GET /api/v1/tools`
  lists them with their schemas, `GET` or `POST /api/v1/tools/<name>`
  calls one with query parameters or a JSON body — behind the same
  bearer token, from the same registry, so a script or an automation
  that speaks no MCP gets the same answers. Examples under Settings →
  Assistants.
- **Webhooks.** A POST to a URL of yours on `sync.completed`,
  `sync.failed` and `bill.missed` — JSON body, the event in a header,
  an HMAC-SHA256 signature with the hook's secret. Home Assistant,
  n8n, a bot. One attempt, five seconds; the list under Settings says
  when a receiver last failed, and a test event is one click.

## [0.35.0] — 2026-09-13

### Added
- **A dividend calendar**, under Investing. What the holdings paid
  out, month by month and by security, in the base currency; and
  what is due in the next twelve months — each holding's per-share
  payments of the last year, as Yahoo lists them by ex-date, times
  the units held today, each on its own date a year on. Received
  and expected on one chart, twelve months back and twelve ahead; the
  yield on today's value; the coming ex-dates. Per-share history is
  fetched once a day in the background, and on a first visit.

## [0.34.0] — 2026-09-13

### Added
- **Bills**, under Money. A subscription is found; a bill is declared
  — the rent, the insurance, the electricity: a name, the text that
  identifies it, an amount if fixed, a rhythm, the day it is usually
  taken, an account if only one. Matched against the rows as they
  arrive, each bill says *paid* until the next date, *due* within a
  week of it, *missed* more than a week past it with nothing seen, or
  *never seen*. Fixed costs per month at the top, the missed and the
  due counted, and a *make it a bill* link on every detected
  subscription.
- **Savings goals**, under Planning. An amount by a date, fed either
  by an account — whose balance is the progress, nothing to type — or
  by hand, an amount at a time. A bar, the percentage, what a month
  reaches it by the date, and whether that is more than the Forecast's
  monthly amount.

## [0.33.0] — 2026-09-13

### Added
- **Against a benchmark.** On the Portfolio page and on every
  security's page, the time-weighted return drawn day by day against
  an index over the same span, both at 100 on the first day, with the
  two figures and the gap in points at the top. Eleven benchmarks by
  name — MSCI World, FTSE All-World, S&P 500, Nasdaq 100, Euro Stoxx
  50, DAX, SMI, MSCI Emerging Markets, euro government bonds, gold,
  bitcoin — and any Yahoo symbol typed in; YTD, one, three, five
  years or everything. The index is turned into the portfolio's
  currency at each day's ECB rate. Its closes are fetched once from
  Yahoo, kept under a pseudo-ISIN, and topped up when a day is
  missing; the choice is remembered per browser.

## [0.32.0] — 2026-09-13

### Added
- **Rules that do more.** Beyond text, direction and amount, a rule
  can be confined to one account or one kind, and match its text as a
  start, an exact value or a regular expression. Beyond the category,
  it can rename the counterparty (*AMZN Mktp DE\*2K3* becomes
  *Amazon*), set the kind (a transfer between your own accounts, which
  the cash flow then leaves out), and add a tag; the category may be
  left alone, so a rule can be a rename or a tag and nothing else.
  Renames, kinds and tags are re-applied on every sync.
- **Tags.** Any number of words on a transaction beside its one
  category — *holiday 2026*, *tax-deductible*, *family*. Set on the
  Transactions page in a field under the row, by a rule, or over MCP
  (`set_tags`, `tags`, and `transactions` filters by tag); the page
  filters by tag and shows the chips; the CSV export carries them.

## [0.31.0] — 2026-09-13

### Added
- **Allocation, with targets.** A page under Investing that cuts the
  portfolio three ways — by asset class (equity, bonds, real estate,
  commodities, cash, crypto), by region (world, Europe, North America,
  emerging markets, Asia Pacific, Switzerland, Germany) and by buckets
  of your own (Core and Satellite, whatever you think in) — each with
  a donut and a table of value and share. Every holding is classified
  once, guessed from its name, its ISIN and what Yahoo says it is, and
  marked as a guess until you confirm or change it in the table at the
  bottom. Set a target per key and the page shows the drift and the
  money to target; type the amount you are about to invest and it says
  how to spread it so the drift shrinks — buying only, the keys below
  target in proportion to their shortfall, because selling has tax
  consequences the app does not know. MCP: `allocation`,
  `set_security_class`, `set_allocation_targets`.

## [0.30.0] — 2026-09-13

### Added
- **Rules with terms, editable.** A categorisation rule can say where
  its text is looked for — anywhere, the description, or the
  counterparty — which way the money went, and a range of amount
  sizes: *"Amazon", money out, 0 to 50 → Household; over 50 →
  Electronics*. Every rule on the Categorize page is a form of its
  own: change it, save, and every rule is re-applied oldest first.
  Rules made from a correction keep the old shape (text anywhere, any
  direction, any amount) until edited. MCP: `add_rule` takes the
  terms, `update_rule` is new.

### Changed
- **Settings in chapters.** The page had grown to a dozen cards; it
  is six pages now, with tabs at the top — General, Banks & brokers,
  Prices & rates, Categories, People, Assistants — and every form
  returns to the chapter it belongs to. (Both from Dominique.)

## [0.29.1] — 2026-09-13

### Fixed
- The holdings table on the Overview, and the securities list under
  Settings → Market prices, did not link to the security's page as the
  Portfolio and account pages do. Every place a security is named is
  a link now. (Dominique.)

## [0.29.0] — 2026-09-13

### Added
- **A currency switch on the security page.** A share paid for in
  euros and quoted in dollars can be looked at in either — or in the
  dashboard's base currency — with pills above the tiles: *EUR paid
  in · USD quoted in*. Every amount is turned at its own day's ECB
  rate and today's price at today's, so net invested, income, value,
  the chart and the returns are all in the chosen currency; the rows
  below stay as booked. The default is the currency the shares were
  paid in. For that the ECB's whole rate history since 1999 is fetched
  once, when a row in the books is older than the ninety days the
  daily feed carries.

## [0.28.3] — 2026-09-13

### Fixed
- A share paid for in euros but quoted by Yahoo in dollars — Amazon at
  a German broker — had its security page in two currencies at once:
  the value in dollars against euros invested, a dollar "unrealised
  gain" that was a subtraction across currencies, a chart with a
  dollar line over a euro line, and returns measured across the rate.
  The price is now turned into the currency the shares were paid in,
  at each day's ECB rate, for the value, the chart, the gains and the
  returns; the page says what the quote was. (Found by Dominique.)
- A DKB Wertpapierabrechnung whose cost line carries a label the
  parser had never seen lost that cost: the amount was right, the fee
  column not. The statement's arithmetic is now checked — Kurswert
  plus every cost is the amount — and whatever is left over is
  counted as fee and named in the import report, so a cost is never
  lost whatever the bank calls it. More of the labels DKB uses are
  known outright. The security page now says what was paid in fees
  and tax beside the income.

## [0.28.2] — 2026-09-13

### Changed
- The MCP card under Settings, and the README, now print the Claude
  Desktop configuration block — `mcp-remote` with `--transport
  http-only` — and say the two things that cost an afternoon: behind
  a reverse proxy the URL is the `https://` one the browser uses, and
  without `http-only` mcp-remote tries SSE first and reports a
  connection failure that is not one.

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
