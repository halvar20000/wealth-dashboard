"""Deutsch.

Geduzt, nicht gesiezt: das hier läuft auf dem eigenen Server, für einen
selbst. Zahlen und Datum kommen aus i18n.FORMATS, nicht von hier.

Ein fehlender Eintrag ist kein Fehler — dann steht dort das englische
Original. Siehe app/i18n.py.
"""

STRINGS: dict[str, str] = {

    # ─── Navigation und Rahmen ───────────────────────────────────────
    "Overview": "Übersicht",
    "Portfolio": "Portfolio",
    "Cash Flow": "Cashflow",
    "Budget": "Budget",
    "Subscriptions": "Abos",
    "Transactions": "Transaktionen",
    "Categorize": "Kategorisieren",
    "Accounts": "Konten",
    "Settings": "Einstellungen",
    "Sign in": "Anmelden",
    "Sign out": "Abmelden",
    "Runs on your machine. Your data never leaves it, except to your own bank.":
        "Läuft auf deinem Rechner. Deine Daten verlassen ihn nie — außer zu "
        "deiner eigenen Bank.",
    "Not found": "Nicht gefunden",
    "No such page.": "Diese Seite gibt es nicht.",
    "Back to accounts": "Zurück zu den Konten",

    # ─── Anmelden und Einrichten ─────────────────────────────────────
    "Username": "Benutzername",
    "Password": "Passwort",
    "Password again": "Passwort wiederholen",
    "at least 8 characters": "mindestens 8 Zeichen",
    "Create account": "Konto anlegen",
    "Create your account": "Lege deinen Zugang an",
    "This is the only account on this installation, and it lives in your own "
    "database. Nothing is sent anywhere, so there is no email to confirm and "
    "no way for anyone to reset it for you — choose a password you will keep.":
        "Das ist der einzige Zugang zu dieser Installation, und er liegt in "
        "deiner eigenen Datenbank. Nichts wird irgendwohin geschickt: es gibt "
        "keine E-Mail zu bestätigen und niemanden, der dein Passwort "
        "zurücksetzen könnte — nimm eines, das du behältst.",
    "Too many attempts. Wait a few minutes.":
        "Zu viele Versuche. Warte ein paar Minuten.",
    "Wrong username or password.": "Benutzername oder Passwort stimmt nicht.",
    "A username is required.": "Ein Benutzername muss sein.",
    "The password must be at least {n} characters.":
        "Das Passwort muss mindestens {n} Zeichen lang sein.",
    "The username “{name}” is already taken.":
        "Den Benutzernamen „{name}“ gibt es schon.",

    # ─── Konten ──────────────────────────────────────────────────────
    "Account": "Konto",
    "Add an account": "Konto hinzufügen",
    "New account": "Neues Konto",
    "Name": "Name",
    "Type": "Art",
    "Currency": "Währung",
    "Source": "Quelle",
    "Balance": "Saldo",
    "As of": "Stand",
    "Edit": "Bearbeiten",
    "Delete": "Löschen",
    "Save": "Speichern",
    "connected": "verbunden",
    "imported file": "Datei importiert",
    "nothing yet": "noch nichts",
    "An account exists whether or not a bank is ever connected to it. Name it "
    "something you will recognise — you can connect it to your bank on the "
    "next screen, or type the balance in yourself and never connect it at all.":
        "Ein Konto existiert auch ohne Bankverbindung. Gib ihm einen Namen, "
        "den du wiedererkennst — verbinden kannst du es auf dem nächsten "
        "Bildschirm, oder du trägst den Saldo selbst ein und verbindest es nie.",
    "The account needs a name.": "Das Konto braucht einen Namen.",
    "Account updated.": "Konto aktualisiert.",
    "That account does not exist.": "Dieses Konto gibt es nicht.",
    "Bank account": "Girokonto",
    "Savings": "Sparkonto",
    "Credit card": "Kreditkarte",
    "Pension fund": "Pensionskasse",
    "P2P lending": "P2P-Kredite",
    "Property": "Immobilie",
    "Other assets": "Sonstige Vermögenswerte",
    "Broker": "Broker",
    "Other": "Sonstiges",

    # ─── Konto löschen ───────────────────────────────────────────────
    "Delete this account": "Dieses Konto löschen",
    "This account holds nothing — no transactions, no balance readings, no "
    "bank connection. There is nothing to lose by removing it.":
        "Auf diesem Konto liegt nichts — keine Transaktionen, keine "
        "Saldostände, keine Bankverbindung. Beim Löschen geht nichts verloren.",
    "This cannot be undone.": "Das lässt sich nicht rückgängig machen.",
    "Deleting {name} also removes {what}.":
        "Mit {name} verschwinden auch {what}.",
    "Deleting {name} removes everything on it.":
        "Mit {name} verschwindet alles, was darauf liegt.",
    "{n} transaction": "{n} Transaktion",
    "{n} transactions": "{n} Transaktionen",
    "{n} balance reading": "{n} Saldostand",
    "{n} balance readings": "{n} Saldostände",
    "{a} and {b}": "{a} und {b}",
    "The bank connection goes with it. The consent itself stays alive at your "
    "bank until it expires or you revoke it there, and re-connecting means "
    "going through your bank's login again.":
        "Die Bankverbindung geht mit. Die Zustimmung selbst bleibt bei deiner "
        "Bank bestehen, bis sie abläuft oder du sie dort widerrufst — neu "
        "verbinden heißt, noch einmal durch den Login deiner Bank zu gehen.",
    "There is no undo and no copy of this anywhere else.":
        "Es gibt kein Rückgängig und sonst nirgends eine Kopie.",
    "Type {name} to confirm": "Tippe {name}, um es zu bestätigen",
    "Delete permanently": "Endgültig löschen",
    "Type the account name exactly to confirm the deletion.":
        "Tippe den Kontonamen genau so, um das Löschen zu bestätigen.",
    "Deleted {name}.": "{name} gelöscht.",

    # ─── Kontoseite ──────────────────────────────────────────────────
    "Bank connection": "Bankverbindung",
    "reported": "gemeldet",
    "as of {date}": "Stand {date}",
    "nothing reported yet": "noch nichts gemeldet",
    "Last sync: {when}.": "Letzter Abgleich: {when}.",
    "never": "nie",
    "Consent valid for {n} more day.": "Zustimmung noch {n} Tag gültig.",
    "Consent valid for {n} more days.": "Zustimmung noch {n} Tage gültig.",
    "Consent expires in {n} day — reconnect soon.":
        "Zustimmung läuft in {n} Tag ab — bald neu verbinden.",
    "Consent expires in {n} days — reconnect soon.":
        "Zustimmung läuft in {n} Tagen ab — bald neu verbinden.",
    "Consent expired. Reconnect to resume syncing.":
        "Zustimmung abgelaufen. Verbinde neu, damit wieder abgeglichen wird.",
    "Sync now": "Jetzt abgleichen",
    "Reconnect or change bank": "Neu verbinden oder Bank wechseln",
    "Add a transaction": "Transaktion hinzufügen",
    "for this holding — the ISIN and the name are filled in":
        "für diese Position — ISIN und Name sind schon eingetragen",
    "Price per unit": "Preis je Stück",
    "In the account's currency. A dividend, a fee or a tax added here is filed "
    "against this holding, so it shows among its rows and in its income above. "
    "Sizes are typed unsigned — whether the money went in or out follows from "
    "what happened.":
        "In der Währung des Kontos. Eine Dividende, eine Gebühr oder eine Steuer, "
        "die hier hinzukommt, wird dieser Position zugeordnet und erscheint unter "
        "ihren Zeilen und in ihren Erträgen oben. Beträge ohne Vorzeichen eintippen "
        "— ob das Geld rein- oder rausging, folgt aus dem, was passiert ist.",
    "There is no broker account to add it to — create one under Accounts first.":
        "Es gibt kein Depotkonto, dem sie zugeordnet werden könnte — lege erst "
        "eines unter Konten an.",
    "Pick which account it happened in.": "Wähle, in welchem Konto es passiert ist.",
    "optional — given, the row is filed against that holding":
        "optional — angegeben, wird die Zeile dieser Position zugeordnet",
    "Disconnect": "Trennen",
    "The account and its history stay; the syncing ends.":
        "Konto und Historie bleiben; der Abgleich endet.",
    "Disconnect this account from the bank? The account, its balances and its "
    "history stay; only the connection goes.":
        "Dieses Konto von der Bank trennen? Konto, Salden und Historie bleiben; "
        "nur die Verbindung geht.",
    "Disconnected {name} from its bank. The history stays.":
        "{name} von der Bank getrennt. Die Historie bleibt.",
    "This account is not connected to a bank. Connecting it pulls the balance "
    "and the transaction history straight from the bank, with your own Enable "
    "Banking credentials.":
        "Dieses Konto ist mit keiner Bank verbunden. Verbunden holt es Saldo "
        "und Umsätze direkt von der Bank — mit deinen eigenen Enable-Banking-"
        "Zugangsdaten.",
    "Connect a bank": "Bank verbinden",
    "Started one already and landed on a dead page? {paste}.":
        "Schon angefangen und auf einer toten Seite gelandet? {paste}.",
    "Paste the code here": "Füge den Code hier ein",
    "Add your Enable Banking Application ID and private key in {settings} first.":
        "Trage zuerst deine Enable-Banking-Application-ID und deinen privaten "
        "Schlüssel unter {settings} ein.",
    "Import a broker CSV": "Broker-CSV importieren",
    "Edit or delete": "Bearbeiten oder löschen",
    "Recent transactions": "Letzte Transaktionen",
    "No transactions yet.": "Noch keine Transaktionen.",
    "Showing the {shown} most recent of {total}.":
        "Die {shown} neuesten von {total}.",
    "That account is not connected to a bank.":
        "Dieses Konto ist mit keiner Bank verbunden.",
    "Sync failed: {reason}": "Abgleich fehlgeschlagen: {reason}",
    "Imported {n} new transaction.": "{n} neue Transaktion importiert.",
    "Imported {n} new transactions.": "{n} neue Transaktionen importiert.",

    # ─── Bestände ────────────────────────────────────────────────────
    "Holdings": "Bestände",
    "Security": "Wertpapier",
    "ISIN": "ISIN",
    "Quantity": "Anzahl",
    "Net invested": "Netto investiert",
    "Last traded at": "Letzter Handelspreis",
    "At that price": "Zu diesem Preis",
    "Value": "Wert",
    "Difference": "Differenz",
    "Where": "Wo",
    "largest first": "größte zuerst",
    "{n} trade": "{n} Order",
    "{n} trades": "{n} Orders",
    "last {date}": "zuletzt {date}",
    "last trade {date}": "letzte Order {date}",
    "export starts too late": "Export beginnt zu spät",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export a period that starts when you "
    "opened the account and re-import — overlap is free.":
        "Eine negative Anzahl ist keine Short-Position: es ist ein Verkauf, "
        "dessen Kauf älter ist als die importierte Datei. Exportiere ab der "
        "Kontoeröffnung und importiere neu — Überschneidung kostet nichts.",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export from the account opening and "
    "re-import — overlap is free.":
        "Eine negative Anzahl ist keine Short-Position: es ist ein Verkauf, "
        "dessen Kauf älter ist als die importierte Datei. Exportiere ab der "
        "Kontoeröffnung und importiere neu — Überschneidung kostet nichts.",
    "Quantities are the running sum of every buy and sell, imported or typed in. The last "
    "two columns use the price of your most recent trade, not a market price — "
    "this app has no price feed yet, and a stale number presented as a "
    "valuation is worse than none.":
        "Die Anzahl ist die laufende Summe aller Käufe und Verkäufe, importiert "
        "oder von Hand eingetragen. Die letzten beiden Spalten rechnen mit dem Preis deiner "
        "jüngsten Order, nicht mit einem Marktpreis — diese App hat noch keine "
        "Kursquelle, und eine veraltete Zahl als Bewertung ist schlimmer als "
        "gar keine.",
    "{n} position": "{n} Position",
    "{n} positions": "{n} Positionen",
    "across all accounts": "über alle Konten",
    "what you put in, {currency} positions":
        "was du eingezahlt hast, Positionen in {currency}",
    "No holdings yet.": "Noch keine Bestände.",
    "Import a broker export from an account and the positions are computed "
    "from its trades.":
        "Importiere einen Broker-Export in ein Konto, und die Positionen "
        "werden aus dessen Orders berechnet.",

    # ─── Übersicht ───────────────────────────────────────────────────
    "Net worth": "Nettovermögen",
    "Cash": "Barmittel",
    "Securities": "Wertpapiere",
    "{n} connected to a bank": "{n} mit einer Bank verbunden",
    "no price": "kein Preis",
    "Latest activity": "Neueste Bewegungen",
    "Date": "Datum",
    "Description": "Beschreibung",
    "Kind": "Art",
    "Amount": "Betrag",
    "Counterparty": "Zahlungspartner",
    "Nothing here yet.": "Hier ist noch nichts.",
    "Add an account, then connect it to your bank or import a broker export. "
    "Both routes end in the same place.":
        "Lege ein Konto an und verbinde es mit deiner Bank oder importiere "
        "einen Broker-Export. Beide Wege enden am selben Ort.",

    # ─── Import ──────────────────────────────────────────────────────
    "Import": "Importieren",
    "Import into {name}": "In {name} importieren",
    "Rows read": "Zeilen gelesen",
    "Imported": "Importiert",
    "Already had": "Schon vorhanden",
    "No cash movement, skipped": "Keine Geldbewegung, übersprungen",
    "{n} line could not be read.": "{n} Zeile war nicht lesbar.",
    "{n} lines could not be read.": "{n} Zeilen waren nicht lesbar.",
    "Everything else was imported. These are listed rather than counted so you "
    "can see whether they matter:":
        "Alles andere wurde importiert. Sie werden aufgezählt statt gezählt, "
        "damit du siehst, ob sie wichtig sind:",
    "…and {n} more.": "…und {n} weitere.",
    "See the account": "Zum Konto",
    "Where to get the file": "Woher die Datei kommt",
    "Inbox → Account statement → choose the period → export CSV. That is the "
    "cash ledger: deposits, trades, dividends and fees. Set the start date "
    "back to when you opened the account and you get the whole history in one "
    "go.":
        "Postfach → Kontoauszug → Zeitraum wählen → CSV exportieren. Das ist "
        "das Geldkonto: Einzahlungen, Orders, Dividenden und Gebühren. Setze "
        "das Startdatum auf die Kontoeröffnung zurück, dann bekommst du die "
        "ganze Historie auf einmal.",
    "Profile → Transactions → export.": "Profil → Transaktionen → Export.",
    "Drop in a CSV your broker exported, or the statement PDFs from your bank's "
    "mailbox — as many as you like, or a ZIP of them. Each file is recognised by "
    "what is in it, so there is nothing to choose — and re-importing what you "
    "already loaded is harmless, because every row carries an id.":
        "Wirf eine CSV deines Brokers hinein oder die Abrechnungs-PDFs aus dem "
        "Postfach deiner Bank — so viele du willst, oder als ZIP. Jede Datei "
        "wird an ihrem Inhalt erkannt, es gibt also nichts auszuwählen — und "
        "noch einmal importieren, was du schon geladen hast, schadet nicht, weil "
        "jede Zeile eine Kennung trägt.",
    "CSV or PDF files":
        "CSV- oder PDF-Dateien",
    "Files":
        "Dateien",
    "Postfach → filter by the Depot → download the Wertpapierabrechnungen as PDF "
    "and drop them all in here at once. The Depot's CSV says only what money "
    "moved; the PDFs say how many units, at what price, with what fee. Orders, "
    "fund purchases, dividends, interest, the Vorabpauschale and the half-year "
    "Sparplan overview are all read. A Storno is skipped and named.":
        "Postfach → nach dem Depot filtern → die Wertpapierabrechnungen als PDF "
        "herunterladen und alle auf einmal hier hineinwerfen. Die CSV des Depots "
        "sagt nur, welches Geld geflossen ist; die PDFs sagen wie viele Stücke, zu "
        "welchem Kurs, mit welcher Gebühr. Orders, Fondskäufe, Dividenden, Zinsen, "
        "die Vorabpauschale und die Halbjahresabrechnung Sparplan werden alle "
        "gelesen. Ein Storno wird übersprungen und benannt.",
    "Open the account or the Visa card → Umsätze → choose the period → "
    "CSV-Export. Girokonto, Tagesgeld and Visa all work, and so do files from "
    "the old portal. Pending (vorgemerkt) rows are left out until they are "
    "booked.":
        "Konto oder Visa-Karte öffnen → Umsätze → Zeitraum wählen → CSV-Export. "
        "Girokonto, Tagesgeld und Visa funktionieren alle, ebenso Dateien aus dem "
        "alten Portal. Vorgemerkte Umsätze bleiben außen vor, bis sie gebucht sind.",
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exportiere einen Zeitraum, der sich mit dem bereits importierten "
        "überschneidet. Überschneidung kostet nichts, eine Lücke kostet dich "
        "Transaktionen.",
    "Choose a CSV or PDF file first.": "Wähle zuerst eine CSV- oder PDF-Datei.",
    "{name} is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "{name} ist größer als {mb} MB. Ein Transaktionsexport ist viel "
        "kleiner — ist es die richtige Datei?",
    "None of those files match an importer here. Supported: {list}":
        "Keine dieser Dateien passt zu einem Importer hier. "
        "Unterstützt: {list}",
    "not recognised, left out": "nicht erkannt, ausgelassen",
    "{importer}: {new} new, {had} already had.":
        "{importer}: {new} neu, {had} schon vorhanden.",

    # ─── Bank verbinden ──────────────────────────────────────────────
    "You will be sent to your bank's own login page. This app never sees your "
    "banking password — the bank gives it read-only access to the account you "
    "tick, for {days} days at a time, and you can revoke it at your bank.":
        "Du wirst zur Login-Seite deiner Bank geschickt. Diese App sieht dein "
        "Bankpasswort nie — die Bank gibt ihr nur Lesezugriff auf das Konto, "
        "das du ankreuzt, für jeweils {days} Tage, und du kannst das bei "
        "deiner Bank widerrufen.",
    "If your bank leaves you on a page that will not load, that is expected "
    "with an https-only redirect URL — {by_hand}.":
        "Wenn deine Bank dich auf einer Seite zurücklässt, die nicht lädt, ist "
        "das bei einer https-only-Redirect-URL normal — {by_hand}.",
    "finish the connection by hand": "schließe die Verbindung von Hand ab",
    "Country": "Land",
    "Search": "Suche",
    "Show banks": "Banken anzeigen",
    "{n} bank in {country}": "{n} Bank in {country}",
    "{n} banks in {country}": "{n} Banken in {country}",
    "including {n} sandbox": "davon {n} Sandbox",
    "including {n} sandboxes": "davon {n} Sandboxen",
    "Connect a sandbox bank first.": "Verbinde zuerst eine Sandbox-Bank.",
    "It walks the identical flow — redirect, consent, session, balances, "
    "transactions — with the provider's own test credentials, and creates no "
    "consent at a real bank. If your redirect URL is registered wrongly, you "
    "find out here instead of by spending an authorisation you rely on.":
        "Sie geht denselben Weg — Redirect, Zustimmung, Sitzung, Salden, "
        "Umsätze — mit den Testzugangsdaten des Anbieters und erzeugt keine "
        "Zustimmung bei einer echten Bank. Wenn deine Redirect-URL falsch "
        "hinterlegt ist, merkst du es hier, statt eine Autorisierung zu "
        "verbrauchen, auf die du angewiesen bist.",
    "Bank": "Bank",
    "Connect": "Verbinden",
    "sandbox": "Sandbox",
    "No banks matched. Try a shorter search, or check the country code.":
        "Keine Bank gefunden. Suche kürzer, oder prüfe das Länderkürzel.",
    "Connected: {accounts}": "Verbunden: {accounts}",
    "Connected, but the first sync failed: {reason}":
        "Verbunden, aber der erste Abgleich ist fehlgeschlagen: {reason}",
    "Imported {n} transaction.": "{n} Transaktion importiert.",
    "Imported {n} transactions.": "{n} Transaktionen importiert.",
    "The bank refused the authorisation: {reason}":
        "Die Bank hat die Autorisierung abgelehnt: {reason}",
    "The bank sent us back without an authorisation code.":
        "Die Bank hat uns ohne Autorisierungscode zurückgeschickt.",

    # ─── Verbindung von Hand abschließen ─────────────────────────────
    "Finish connecting": "Verbindung abschließen",
    "Finish connecting by hand": "Verbindung von Hand abschließen",
    "Some providers only accept an https redirect URL, which an app on your "
    "own network cannot have. Then the bank sends you to a page that does not "
    "exist — and that is fine. The authorisation code is in the address bar of "
    "that dead page. Copy the whole address and paste it here.":
        "Manche Anbieter akzeptieren nur eine https-Redirect-URL, die eine App "
        "in deinem eigenen Netz nicht haben kann. Dann schickt dich die Bank "
        "auf eine Seite, die es nicht gibt — das ist in Ordnung. Der "
        "Autorisierungscode steht in der Adresszeile dieser toten Seite. "
        "Kopiere die ganze Adresse und füge sie hier ein.",
    "Waiting to be finished": "Wartet auf den Abschluss",
    "Started": "Begonnen",
    "One connection is in progress, so pasting just the code works too — but "
    "the whole URL is easier and always right.":
        "Es läuft nur eine Verbindung, deshalb reicht auch der bloße Code — "
        "die ganze URL ist aber einfacher und immer richtig.",
    "The address the bank sent you to":
        "Die Adresse, auf die dich die Bank geschickt hat",
    "Nothing is fetched from this address — it is only read for the code and "
    "state it carries.":
        "Von dieser Adresse wird nichts abgerufen — sie wird nur nach dem Code "
        "und dem State darin gelesen.",
    "No connection is waiting to be finished.":
        "Es wartet keine Verbindung auf den Abschluss.",
    "Start one from an account, then come back here if the bank leaves you on "
    "a page that will not load.":
        "Starte eine von einem Konto aus und komm hierher zurück, wenn die "
        "Bank dich auf einer Seite zurücklässt, die nicht lädt.",
    "No authorisation code in that. Paste the whole URL from the address bar, "
    "including the ?code=… part.":
        "Da ist kein Autorisierungscode drin. Füge die ganze URL aus der "
        "Adresszeile ein, samt dem Teil ?code=….",
    "That code could belong to any of several connections in progress. Paste "
    "the full URL, which carries the state.":
        "Dieser Code könnte zu mehreren laufenden Verbindungen gehören. Füge "
        "die vollständige URL ein, die den State enthält.",
    # ─── Cashflow ────────────────────────────────────────────────────
    "Money in against money out, per month. Internal transfers are excluded — "
    "moving money between your own accounts is not income and not spending, "
    "and counting it would inflate both by the same amount. Investment is "
    "separated for the same reason: a month you invested €3,000 is not a month "
    "you overspent.":
        "Geld rein gegen Geld raus, pro Monat. Interne Umbuchungen bleiben "
        "draußen — Geld zwischen deinen eigenen Konten zu schieben ist weder "
        "Einnahme noch Ausgabe, und es mitzuzählen würde beide um denselben "
        "Betrag aufblähen. Investitionen stehen aus demselben Grund für sich: "
        "ein Monat, in dem du 3.000 € angelegt hast, ist kein Monat, in dem du "
        "zu viel ausgegeben hast.",
    "Income": "Einnahmen",
    "Spending": "Ausgaben",
    "Invested": "Angelegt",
    "Kept": "Übrig",
    "a month": "im Monat",
    "a month, over {n} month": "im Monat, über {n} Monat",
    "a month, over {n} months": "im Monat, über {n} Monate",
    "over the period": "im Zeitraum",
    "income less spending": "Einnahmen minus Ausgaben",
    "By month": "Nach Monat",
    "Where it goes": "Wohin es geht",
    "By category": "Nach Kategorie",
    "per month on average": "im Schnitt pro Monat",
    "Category": "Kategorie",
    "Per month": "Pro Monat",
    "Total": "Gesamt",
    "Assets": "Vermögen",
    "No transactions in the base currency yet.":
        "Noch keine Transaktionen in der Basiswährung.",
    "Connect a bank or import a statement, then categorise on the {page} page "
    "— until things have categories, this page has nothing to add up.":
        "Verbinde eine Bank oder importiere einen Auszug und kategorisiere "
        "dann auf der Seite {page} — solange nichts eine Kategorie hat, hat "
        "diese Seite nichts zu addieren.",

    # ─── Budget ──────────────────────────────────────────────────────
    "Measured against how far through the month you are, not against the whole "
    "month. Halfway through, everyone is under budget — the useful question is "
    "whether you are ahead of the pace.":
        "Gemessen daran, wie weit der Monat ist, nicht am ganzen Monat. Zur "
        "Monatsmitte liegt jeder unter Budget — die nützliche Frage ist, ob du "
        "schneller bist als das Tempo.",
    "No budgets set yet — fill some in below.":
        "Noch kein Budget gesetzt — trage unten eines ein.",
    "Monthly budget per category": "Monatsbudget je Kategorie",
    "leave blank for no budget": "leer lassen heißt kein Budget",
    "Spent": "Ausgegeben",
    "Typical": "Üblich",
    "Pace": "Tempo",
    "over budget": "über Budget",
    "ahead of pace": "schneller als das Tempo",
    "on track": "im Plan",
    "{pct}% used": "{pct}% verbraucht",
    "Save budget": "Budget speichern",
    "Budget saved.": "Budget gespeichert.",

    # ─── Abos ────────────────────────────────────────────────────────
    "Charges that repeat on a recognisable rhythm, at a stable amount, at "
    "least three times. Deliberately cautious: the failure that matters is not "
    "missing one, it is calling three unrelated payments a €400 commitment — "
    "which makes the whole page untrustworthy.":
        "Abbuchungen, die sich in erkennbarem Rhythmus wiederholen, in "
        "stabiler Höhe, mindestens dreimal. Bewusst vorsichtig: der Fehler, "
        "auf den es ankommt, ist nicht eine übersehene — es ist, drei "
        "zusammenhanglose Zahlungen eine Verpflichtung über 400 € zu nennen, "
        "womit die ganze Seite unglaubwürdig wird.",
    "Per year": "Pro Jahr",
    "{n} active": "{n} aktiv",
    "at the current rhythm": "beim aktuellen Rhythmus",
    "Possibly recurring": "Vielleicht wiederkehrend",
    "repeated, but not on a clear rhythm":
        "wiederholt sich, aber ohne klaren Rhythmus",
    "Recurring": "Wiederkehrend",
    "What": "Was",
    "Rhythm": "Rhythmus",
    "Each": "Jeweils",
    "Paid so far": "Bisher gezahlt",
    "Last seen": "Zuletzt",
    "{n} payment since {date}": "{n} Zahlung seit {date}",
    "{n} payments since {date}": "{n} Zahlungen seit {date}",
    "probably ended": "wahrscheinlich beendet",
    "{n} day ago": "vor {n} Tag",
    "{n} days ago": "vor {n} Tagen",
    "Nothing detected yet.": "Noch nichts erkannt.",
    "A charge has to appear at least three times, on a recognisable rhythm, at "
    "a stable amount. Import a longer history and it will find more.":
        "Eine Abbuchung muss mindestens dreimal auftauchen, in erkennbarem "
        "Rhythmus und stabiler Höhe. Importiere eine längere Historie, dann "
        "findet sie mehr.",
    "repeats, but the rhythm or the amount wanders":
        "wiederholt sich, aber Rhythmus oder Betrag wandern",
    "Times": "Anzahl",

    # ─── Transaktionen und Kategorisieren ────────────────────────────
    "merchant or text": "Händler oder Text",
    "any": "alle",
    "Filter": "Filtern",
    "Clear": "Zurücksetzen",
    "net {amount}": "netto {amount}",
    "showing the {n} most recent": "die {n} neuesten",
    "Nothing matches those filters.": "Zu diesen Filtern passt nichts.",
    "Correcting a transaction here can leave a rule behind. A rule applies to "
    "what is already imported as well as to what arrives next — otherwise the "
    "same shop has to be fixed every month for a year before it stops asking.":
        "Wenn du hier eine Transaktion korrigierst, kann daraus eine Regel "
        "werden. Eine Regel gilt für das schon Importierte genauso wie für "
        "das, was als Nächstes kommt — sonst korrigierst du denselben Laden "
        "ein Jahr lang jeden Monat, bevor er aufhört zu fragen.",
    "Waiting": "Offen",
    "largest amounts first": "größte Beträge zuerst",
    "Rules": "Regeln",
    "applied to past and future": "gilt für Vergangenheit und Zukunft",
    "Quick start": "Schnellstart",
    "Categorise what is obvious": "Kategorisiere das Offensichtliche",
    "fees, interest, dividends, known merchants":
        "Gebühren, Zinsen, Dividenden, bekannte Händler",
    "The queue": "Die Warteschlange",
    "clear “remember as” to correct this one row without making a rule":
        "„Merken als“ leeren, um nur diese Zeile zu korrigieren — ohne Regel",
    "Remember as": "Merken als",
    "text to match, optional": "Text zum Erkennen, optional",
    "Apply": "Übernehmen",
    "Nothing waiting.": "Nichts offen.",
    "Every transaction has a category. Import more, or adjust one from the "
    "{page} page.":
        "Jede Transaktion hat eine Kategorie. Importiere mehr, oder ändere "
        "eine auf der Seite {page}.",
    "newest wins where two match": "bei zwei Treffern gewinnt die neuere",
    "Rule saved — {n} transaction matched “{pattern}”.":
        "Regel gespeichert — {n} Transaktion passte auf „{pattern}“.",
    "Rule saved — {n} transactions matched “{pattern}”.":
        "Regel gespeichert — {n} Transaktionen passten auf „{pattern}“.",
    "Changing a category here also makes a rule from the merchant, and applies it to every transaction that matches. To correct a single row without a rule, use the Categorize page and clear “remember as”.":
        "Wer hier eine Kategorie ändert, legt damit auch eine Regel für den Händler an, und die gilt für jede passende Transaktion. Um nur eine einzelne Zeile zu korrigieren, nimm die Seite Kategorisieren und leere „Merken als“.",
    "A rule needs at least three characters to match on — anything shorter will catch transactions you did not mean.":
        "Eine Regel braucht mindestens drei Zeichen zum Erkennen — alles Kürzere trifft Transaktionen, die du nicht gemeint hast.",
    "{n} transaction categorised from what the importer already knew.":
        "{n} Transaktion kategorisiert aus dem, was der Importer schon wusste.",
    "{n} transactions categorised from what the importer already knew.":
        "{n} Transaktionen kategorisiert aus dem, was der Importer schon "
        "wusste.",
    "Rule deleted and the remaining rules re-applied.":
        "Regel gelöscht und die übrigen Regeln neu angewendet.",

    # ─── Einstellungen ───────────────────────────────────────────────
    "General": "Allgemein",
    "Language": "Sprache",
    "Follow my browser": "Meinem Browser folgen",
    "Changes the language of the app, and with it how numbers and dates are "
    "written. It does not touch what your bank sent: a transaction described "
    "in German stays in German.":
        "Ändert die Sprache der App und damit auch, wie Zahlen und Datum "
        "geschrieben werden. Was deine Bank geschickt hat, bleibt unberührt: "
        "ein auf Deutsch beschriebener Umsatz bleibt auf Deutsch.",
    "Base currency": "Basiswährung",
    "Redirect URL": "Redirect-URL",
    "Where your bank sends you back after you authorise. This exact string "
    "must also be registered in the Enable Banking Control Panel — if the two "
    "differ by so much as a trailing slash, the bank refuses the handover and "
    "the error it shows names nothing useful.":
        "Wohin deine Bank dich nach der Freigabe zurückschickt. Genau diese "
        "Zeichenkette muss auch im Enable-Banking-Control-Panel hinterlegt "
        "sein — unterscheiden sich die beiden auch nur um einen Schrägstrich "
        "am Ende, verweigert die Bank die Übergabe, und der Fehler, den sie "
        "zeigt, nennt nichts Brauchbares.",
    "Settings saved.": "Einstellungen gespeichert.",

    # ─── Kategorien ──────────────────────────────────────────────────
    "Categories": "Kategorien",
    "renaming one keeps every transaction it holds":
        "Umbenennen behält jede Transaktion darin",
    "A category is identified internally by the name it was created with, so "
    "renaming or recolouring one never re-files a transaction — the Groceries "
    "you already sorted stay sorted whatever you call them. What “counts as” "
    "decides is whether Cash Flow and Budget treat the money as spent, or "
    "merely as moved: pay for lunch and it is spending, move €500 to your "
    "broker and it is not — or as income, which Cash Flow adds up by "
    "category, so a salary, a rent coming in and interest each show as "
    "their own.":
        "Eine Kategorie wird intern über den Namen erkannt, mit dem sie "
        "angelegt wurde — Umbenennen oder Umfärben sortiert deshalb nie eine "
        "Transaktion um: die Lebensmittel, die du schon sortiert hast, bleiben "
        "sortiert, wie immer du sie nennst. „Zählt als“ entscheidet, ob "
        "Cashflow und Budget das Geld als ausgegeben behandeln oder nur als "
        "verschoben: das Mittagessen ist eine Ausgabe, 500 € zu deinem Broker "
        "sind es nicht — oder als Einnahme, die der Cashflow nach Kategorie "
        "aufsummiert, sodass Gehalt, Mieteinnahmen und Zinsen je für sich "
        "erscheinen.",
    "Colour for {name}": "Farbe für {name}",
    "Name of {name}": "Name von {name}",
    "Cash Flow knows this one by name — it is never counted as spending.":
        "Der Cashflow kennt diese hier beim Namen — sie zählt nie als Ausgabe.",
    "not spending": "keine Ausgabe",
    "income": "Einnahme",
    "Salary": "Gehalt",
    "Rental income": "Mieteinnahmen",
    "Interest & dividends": "Zinsen & Dividenden",
    "Where it comes from": "Woher es kommt",
    "What {name} counts as": "Wofür {name} zählt",
    "Not spending": "Keine Ausgaben",
    "{n} rule": "{n} Regel",
    "{n} rules": "{n} Regeln",
    "Delete this category? {n} transaction moves to Uncategorised.":
        "Diese Kategorie löschen? {n} Transaktion wandert zu Nicht "
        "kategorisiert.",
    "Delete this category? {n} transactions move to Uncategorised.":
        "Diese Kategorie löschen? {n} Transaktionen wandern zu Nicht "
        "kategorisiert.",
    "{n} rule is deleted with it.": "{n} Regel wird mit gelöscht.",
    "{n} rules are deleted with it.": "{n} Regeln werden mit gelöscht.",
    "The app tells spending from moving your own money by this category, so it "
    "cannot be removed.":
        "An dieser Kategorie unterscheidet die App Ausgeben von Umschichten "
        "deines eigenen Geldes — deshalb lässt sie sich nicht entfernen.",
    "needed": "gebraucht",
    "Colour": "Farbe",
    "New category": "Neue Kategorie",
    "Childcare": "Kinderbetreuung",
    "Counts as": "Zählt als",
    "Add category": "Kategorie hinzufügen",
    "Category “{name}” added.": "Kategorie „{name}“ hinzugefügt.",
    "Category updated.": "Kategorie aktualisiert.",
    "“{name}” deleted.": "„{name}“ gelöscht.",
    "“{name}” deleted — {n} transaction moved to Uncategorised, and its rules "
    "were removed with it.":
        "„{name}“ gelöscht — {n} Transaktion ist zu Nicht kategorisiert "
        "gewandert, und die Regeln dazu sind mit weg.",
    "“{name}” deleted — {n} transactions moved to Uncategorised, and its rules "
    "were removed with it.":
        "„{name}“ gelöscht — {n} Transaktionen sind zu Nicht kategorisiert "
        "gewandert, und die Regeln dazu sind mit weg.",
    "A category needs a name.": "Eine Kategorie braucht einen Namen.",
    "Keep the name under 40 characters — it has to fit in a table cell and a "
    "chart legend.":
        "Halte den Namen unter 40 Zeichen — er muss in eine Tabellenzelle und "
        "in eine Diagrammlegende passen.",
    "{given} is not a colour like #a78bfa.":
        "{given} ist keine Farbe wie #a78bfa.",
    "That": "Das",
    "That name has no letters or digits in it, and the name is what the "
    "internal id is made from.":
        "In diesem Namen stecken weder Buchstaben noch Ziffern, und aus dem "
        "Namen wird die interne ID gebaut.",
    "“{name}” already uses that name.": "„{name}“ heißt schon so.",
    "There is already a category called “{name}”.":
        "Es gibt schon eine Kategorie namens „{name}“.",

    # ─── Enable Banking ──────────────────────────────────────────────
    "Your own application, your own key. Nothing here is shared with anyone — "
    "the key never leaves this machine and is only used to sign your own "
    "requests.":
        "Deine eigene Anwendung, dein eigener Schlüssel. Nichts davon wird "
        "geteilt — der Schlüssel verlässt diesen Rechner nie und signiert nur "
        "deine eigenen Anfragen.",
    "Create an application": "Lege eine Anwendung an",
    "at {control_panel}.": "unter {control_panel}.",
    "Environment Production — restricted mode is a state of a production app, "
    "not a separate environment.":
        "Umgebung Production — „restricted mode“ ist ein Zustand einer "
        "Production-Anwendung, keine eigene Umgebung.",
    "Find your Application ID.": "Finde deine Application ID.",
    "It is on the application's page in the Control Panel — a UUID like "
    "{example}.":
        "Sie steht auf der Seite der Anwendung im Control Panel — eine UUID "
        "wie {example}.",
    "If you chose Generate for the key, it is also the filename of the file "
    "your browser downloaded: {file}.":
        "Wenn du beim Schlüssel „Generate“ gewählt hast, ist sie auch der "
        "Dateiname der Datei, die dein Browser geladen hat: {file}.",
    "Find your private key.": "Finde deinen privaten Schlüssel.",
    "Which file depends on the choice you made when creating the application:":
        "Welche Datei es ist, hängt davon ab, wie du die Anwendung angelegt "
        "hast:",
    "You chose “Generate”": "Du hast „Generate“ gewählt",
    "the usual case": "der Normalfall",
    "your browser downloaded {file}.": "dein Browser hat {file} geladen.",
    "That file is the private key.": "Diese Datei ist der private Schlüssel.",
    "Open it in a text editor and copy everything, including the BEGIN and END "
    "lines. There is nothing to generate yourself.":
        "Öffne sie in einem Texteditor und kopiere alles, samt der BEGIN- und "
        "END-Zeilen. Du musst nichts selbst erzeugen.",
    "You provided your own key": "Du hast deinen eigenen Schlüssel geliefert",
    "then you already ran the commands below and want {file}.":
        "dann hast du die Befehle unten schon ausgeführt und brauchst {file}.",
    "Do not paste enablebanking_public.pem, or anything you uploaded to Enable "
    "Banking. That is the public half; they have it, you need the other one.":
        "Füge nicht enablebanking_public.pem ein, und auch nichts, was du zu "
        "Enable Banking hochgeladen hast. Das ist die öffentliche Hälfte — die "
        "haben sie, du brauchst die andere.",
    "Paste both below": "Füge beides unten ein",
    "and save. The app checks them immediately against Enable Banking and "
    "tells you what it finds.":
        "und speichere. Die App prüft sie sofort bei Enable Banking und sagt "
        "dir, was sie findet.",
    "Only if you want to supply your own key instead of letting the Control "
    "Panel generate one":
        "Nur wenn du deinen eigenen Schlüssel liefern willst, statt ihn vom "
        "Control Panel erzeugen zu lassen",
    "Upload enablebanking_public.pem in the Control Panel; paste "
    "enablebanking_private.key below.":
        "Lade enablebanking_public.pem im Control Panel hoch; füge "
        "enablebanking_private.key unten ein.",
    "The key is stored at {path} with permissions 0600.":
        "Der Schlüssel liegt unter {path} mit den Rechten 0600.",
    "Your credentials live inside the data folder, so every backup of that "
    "folder carries your bank key with it. Set WD_SECRETS_DIR to a folder "
    "outside it if that matters to you.":
        "Deine Zugangsdaten liegen im Datenordner — jedes Backup dieses "
        "Ordners trägt also deinen Bankschlüssel mit sich. Setze "
        "WD_SECRETS_DIR auf einen Ordner außerhalb, wenn dir das wichtig ist.",
    "Application ID": "Application ID",
    "stored — paste again to replace":
        "gespeichert — zum Ersetzen neu einfügen",
    "Private key (PEM)": "Privater Schlüssel (PEM)",
    "Save credentials": "Zugangsdaten speichern",
    "Credentials saved. Checking them with Enable Banking…":
        "Zugangsdaten gespeichert. Sie werden gerade bei Enable Banking "
        "geprüft…",
    "Credentials are stored. {test} — this makes one live call to Enable "
    "Banking.":
        "Die Zugangsdaten sind gespeichert. {test} — das ist ein echter Aufruf "
        "bei Enable Banking.",
    "Test them": "Teste sie",
    "Working. Registered redirect URLs:":
        "Funktioniert. Hinterlegte Redirect-URLs:",
    "none": "keine",

    # ─── Wechselkurse ────────────────────────────────────────────────
    "Exchange rates": "Wechselkurse",
    "European Central Bank": "Europäische Zentralbank",
    "The ECB publishes euro reference rates every business day — free, "
    "without a key and without an account. They are what converts an amount in "
    "another currency into your base currency, and every total built from them "
    "names the day they were published.":
        "Die EZB veröffentlicht an jedem Geschäftstag Euro-Referenzkurse — "
        "kostenlos, ohne Schlüssel und ohne Konto. Sie rechnen einen Betrag in "
        "einer anderen Währung in deine Basiswährung um, und jede Summe, die "
        "darauf beruht, nennt den Tag, an dem sie veröffentlicht wurden.",
    "{n} currency, published {date}.": "{n} Währung, veröffentlicht am {date}.",
    "{n} currencies, published {date}.":
        "{n} Währungen, veröffentlicht am {date}.",
    "The ECB does not publish at the weekend, so this is Friday's — which is "
    "also the newest rate there is.":
        "Am Wochenende veröffentlicht die EZB nichts, das ist also der Kurs "
        "vom Freitag — und zugleich der neueste, den es gibt.",
    "No rates yet, so amounts in another currency are reported beside your "
    "totals rather than inside them. Fetching them needs this machine to reach "
    "the internet once.":
        "Noch keine Kurse — Beträge in anderen Währungen stehen deshalb neben "
        "deinen Summen statt darin. Zum Holen muss dieser Rechner einmal ins "
        "Internet kommen.",
    "Update rates now": "Kurse jetzt aktualisieren",
    "Also updated on start-up, at most once a day, in the background. Nothing "
    "waits on it: a page renders whether or not the rates arrived.":
        "Wird auch beim Start aktualisiert, höchstens einmal am Tag, im "
        "Hintergrund. Nichts wartet darauf: eine Seite wird angezeigt, ob die "
        "Kurse ankamen oder nicht.",
    "{n} exchange rate fetched, published {date}.":
        "{n} Wechselkurs geholt, veröffentlicht am {date}.",
    "{n} exchange rates fetched, published {date}.":
        "{n} Wechselkurse geholt, veröffentlicht am {date}.",
    "Includes {amounts}, converted at the ECB rate of {date}.":
        "Enthält {amounts}, umgerechnet zum EZB-Kurs vom {date}.",
    "Not included, because no rate here covers them:":
        "Nicht enthalten, weil kein Kurs hier sie abdeckt:",
    "Amounts in another currency are in the totals above, converted at the ECB "
    "reference rate — a published mid-market rate, not one your broker would "
    "give you.":
        "Beträge in anderen Währungen stecken in den Summen oben, umgerechnet "
        "zum EZB-Referenzkurs — einem veröffentlichten Mittelkurs, nicht dem, "
        "den dein Broker dir geben würde.",
    "Rates of {date}.": "Kurse vom {date}.",
    "These are not in the totals above, because no rate here covers them:":
        "Diese stecken nicht in den Summen oben, weil kein Kurs hier sie "
        "abdeckt:",

    # ─── Änderungen ──────────────────────────────────────────────────
    "What changed": "Was sich geändert hat",
    "You are running version {version}.": "Du läufst auf Version {version}.",
    "Release notes are written once, in English, and are not translated — a "
    "translation of a note about a fix is one more thing that can be wrong "
    "about the fix.":
        "Die Versionshinweise werden einmal geschrieben, auf Englisch, und "
        "nicht übersetzt — die Übersetzung einer Notiz über einen Fix ist noch "
        "eine Sache, die an diesem Fix falsch sein kann.",
    "you are here": "du bist hier",
    "Added [changelog]": "Neu",
    "Changed [changelog]": "Geändert",
    "Fixed [changelog]": "Behoben",
    "Removed [changelog]": "Entfernt",
    "No changelog shipped with this build.":
        "Mit diesem Build kam keine Änderungsliste mit.",
    "CHANGELOG.md is not inside the image — it is in the repository, which is "
    "where this page reads it from when you run from source.":
        "CHANGELOG.md steckt nicht im Image — die Datei liegt im Repository, "
        "und von dort liest diese Seite sie, wenn du aus dem Quellcode "
        "startest.",

    # ─── Kategorienamen der Grundausstattung ─────────────────────────
    "Housing": "Wohnen",
    "Groceries": "Lebensmittel",
    "Restaurants & bars": "Restaurants & Bars",
    "Transport": "Verkehr",
    "Car": "Auto",
    "Travel": "Reisen",
    "Shopping": "Einkäufe",
    "Health": "Gesundheit",
    "Insurance": "Versicherung",
    "Education": "Bildung",
    "Entertainment": "Unterhaltung",
    "Fees": "Gebühren",
    "Tax": "Steuern",
    "Cash withdrawal": "Bargeldabhebung",
    "Uncategorised": "Nicht kategorisiert",
    "Investment": "Investition",
    "Internal transfer": "Interne Umbuchung",

    # ─── Transaktionsarten ───────────────────────────────────────────
    "deposit [kind]": "Einzahlung",
    "withdrawal [kind]": "Auszahlung",
    "buy [kind]": "Kauf",
    "sell [kind]": "Verkauf",
    "dividend [kind]": "Dividende",
    "interest [kind]": "Zinsen",
    "fee [kind]": "Gebühr",
    "tax [kind]": "Steuer",
    "transfer [kind]": "Umbuchung",
    "other [kind]": "Sonstiges",

    # ─── Rhythmen ────────────────────────────────────────────────────
    "weekly [rhythm]": "wöchentlich",
    "monthly [rhythm]": "monatlich",
    "quarterly [rhythm]": "vierteljährlich",
    "half-yearly [rhythm]": "halbjährlich",
    "yearly [rhythm]": "jährlich",

    # ─── Von Hand eingetragen ─────────────────────────────────────────
    "typed in": "von Hand eingetragen",
    "Balance in {currency}": "Saldo in {currency}",
    "Record balance": "Saldo eintragen",
    "Balance recorded: {amount} as of {date}.":
        "Saldo eingetragen: {amount}, Stand {date}.",
    "The balance is missing.": "Der Saldo fehlt.",
    "Add by hand": "Von Hand eintragen",
    "Add to {name} by hand": "In {name} von Hand eintragen",
    "For an account no bank connection and no export will describe. What you type in lands beside the imported rows and counts the same way: a purchase becomes part of the holding, a dividend is income, a fee is a fee.":
        "Für ein Konto, das keine Bankverbindung und kein Export beschreibt. Was du hier eintippst, steht neben den importierten Zeilen und zählt genauso: ein Kauf wird Teil der Position, eine Dividende ist Einkommen, eine Gebühr eine Gebühr.",
    "What happened": "Was ist passiert",
    "Fee": "Gebühr",
    "optional": "optional",
    "optional, but it is what the holding will be called":
        "optional, aber so wird die Position heißen",
    "Price per unit, in {currency}": "Preis pro Stück, in {currency}",
    "Total on the statement": "Gesamtbetrag laut Abrechnung",
    "optional — otherwise quantity × price, plus the fee and tax on a purchase and minus them on a sale":
        "optional — sonst Stückzahl × Preis, beim Kauf plus Gebühr und Steuer, beim Verkauf minus",
    "Amount, in {currency}": "Betrag, in {currency}",
    "as a size — whether it is money in or out follows from what happened":
        "als Größe — ob Geld rein- oder rausgeht, folgt aus dem, was passiert ist",
    "Direction": "Richtung",
    "Money out of this account": "Geld geht von diesem Konto ab",
    "Money into this account": "Geld kommt auf dieses Konto",
    "optional — the shop, the employer, the other account":
        "optional — der Laden, der Arbeitgeber, das andere Konto",
    "decide from the kind and my rules":
        "aus der Art und meinen Regeln ableiten",
    "Stay on this page to add another":
        "Auf dieser Seite bleiben und noch eine eintragen",
    "Add": "Eintragen",
    "Back to the account": "Zurück zum Konto",
    "Added.": "Eingetragen.",
    "Remove": "Entfernen",
    "Connect a bank, import a CSV, or {add}.":
        "Verbinde eine Bank, importiere eine CSV, oder {add}.",
    "Pick what kind of entry this is.":
        "Wähle, um was für einen Eintrag es sich handelt.",
    "The date needs to be a real day, written year-month-day.":
        "Das Datum muss ein echter Tag sein, geschrieben als Jahr-Monat-Tag.",
    "That date is in the future. A transaction is something that happened.":
        "Das Datum liegt in der Zukunft. Eine Transaktion ist etwas, das passiert ist.",
    "A trade needs the security's ISIN — two letters and ten characters, like IE00B4L5Y983. It is on the order confirmation, and it is how the same fund at two brokers is recognised as one holding.":
        "Ein Handel braucht die ISIN des Wertpapiers — zwei Buchstaben und zehn Zeichen, etwa IE00B4L5Y983. Sie steht auf der Orderabrechnung, und an ihr erkennt die App denselben Fonds bei zwei Brokern als eine Position.",
    "The quantity": "Die Stückzahl",
    "The price": "Der Preis",
    "The fee": "Die Gebühr",
    "The tax": "Die Steuer",
    "The total": "Der Gesamtbetrag",
    "The amount": "Der Betrag",
    "{what} cannot be zero.": "{what} darf nicht null sein.",
    "A trade needs a quantity and a price per unit.":
        "Ein Handel braucht eine Stückzahl und einen Preis pro Stück.",
    "The amount is missing.": "Der Betrag fehlt.",
    "Bought {qty} × {name}": "Kauf {qty} × {name}",
    "Sold {qty} × {name}": "Verkauf {qty} × {name}",
    "Includes {amounts}, converted at ECB rates — each month at its own rate, and months older than the rates on file at the oldest.":
        "Enthält {amounts}, umgerechnet zu EZB-Kursen — jeder Monat zu seinem eigenen Kurs, Monate vor den gespeicherten Kursen zum ältesten.",
    "Not counted, because no rate here covers them:":
        "Nicht mitgezählt, weil kein Kurs hier sie abdeckt:",
    "Fetch rates under {settings}.":
        "Kurse unter {settings} abrufen.",
    "Budgeted": "Budgetiert",
    "Spent so far": "Bisher ausgegeben",
    "Remaining": "Übrig",
    "for {month}": "für {month}",
    "day {day} of {days} · {pct}% through the month":
        "Tag {day} von {days} · {pct} % des Monats",
    "budget less spending": "Budget minus Ausgaben",
    "Budget against spent": "Budget gegen Ausgaben",
    "this month, per category — the chart follows the fields below as you type":
        "diesen Monat, pro Kategorie — das Diagramm folgt den Feldern unten beim Tippen",
    "in {currency}": "in {currency}",
    "Everything you hold, aggregated by ISIN across accounts — the same fund at two brokers is one position from where you are standing. Values use the last market price, and each one names its day; a holding no price could be found for uses the price of your last trade, and says so.":
        "Alles, was du hältst, über alle Konten nach ISIN zusammengefasst — derselbe Fonds bei zwei Brokern ist von deinem Standpunkt aus eine Position. Bewertet zum letzten Marktpreis, und jeder nennt seinen Tag; eine Position, für die sich kein Kurs finden ließ, nimmt den Preis deines letzten Handels und sagt das auch.",
    "Every holding is valued at its last market price — free, without a key — and every total built from prices names their day. A broker export gives an ISIN and a price source wants a ticker, so the ticker is looked up once and kept. Where the lookup fails or picks the wrong exchange, type the ticker Yahoo uses, like IWDA.AS; what you type is never replaced by a lookup.":
        "Jede Position wird zum letzten Marktpreis bewertet — kostenlos, ohne Schlüssel — und jede Summe aus Kursen nennt deren Tag. Ein Broker-Export liefert eine ISIN, eine Kursquelle will ein Tickersymbol; deshalb wird das Symbol einmal nachgeschlagen und gemerkt. Wo die Suche scheitert oder die falsche Börse wählt, trag das Symbol ein, das Yahoo verwendet, etwa IWDA.AS; was du einträgst, ersetzt keine Suche je.",
    "Also updated on start-up and every few hours in the background. A holding no price could be found for is valued at your last trade, and the pages say so.":
        "Außerdem beim Start und alle paar Stunden im Hintergrund aktualisiert. Eine Position ohne auffindbaren Kurs wird zu deinem letzten Handelspreis bewertet, und die Seiten sagen das.",
    "Nothing to price yet — holdings appear here once a broker export or a trade typed in by hand has given you one.":
        "Noch nichts zu bewerten — Positionen erscheinen hier, sobald ein Broker-Export oder ein von Hand eingetragener Handel eine ergeben hat.",
    "Market prices": "Marktpreise",
    "Yahoo Finance": "Yahoo Finance",
    "Price": "Kurs",
    "Ticker": "Symbol",
    "Ticker for {name}": "Symbol für {name}",
    "Update prices now": "Kurse jetzt aktualisieren",
    "Priced.": "Bewertet.",
    "at market prices of {date}": "zu Marktpreisen vom {date}",
    "last trade, no market price": "letzter Handel, kein Marktpreis",
    "{n} holding at its last traded price":
        "{n} Position zum letzten Handelspreis",
    "{n} holdings at their last traded price":
        "{n} Positionen zum letzten Handelspreis",
    "{n} holding priced.": "{n} Position bewertet.",
    "{n} holdings priced.": "{n} Positionen bewertet.",
    "{ok} of {held} holdings priced. Could not price: {failed}.":
        "{ok} von {held} Positionen bewertet. Kein Kurs für: {failed}.",

    # ─── Personen ────────────────────────────────────────────────────
    "A person needs a name.":
        "Eine Person braucht einen Namen.",
    "Add person":
        "Person hinzufügen",
    "Add the people in your household, then tick on each account who it belongs to — one person, or several for a joint account. A switch appears in the header: Everyone shows the whole household, a name shows only that person's accounts on every page. An account ticked for nobody shows under Everyone only. This is a lens, not a lock: anyone who can sign in can flip it.":
        "Trage die Personen deines Haushalts ein und hake bei jedem Konto an, wem es gehört — einer Person, oder mehreren bei einem Gemeinschaftskonto. In der Kopfzeile erscheint ein Schalter: „Alle“ zeigt den ganzen Haushalt, ein Name zeigt auf jeder Seite nur die Konten dieser Person. Ein Konto ohne Haken erscheint nur unter „Alle“. Das ist eine Brille, kein Schloss: wer sich anmelden kann, kann umschalten.",
    "Alex":
        "Alex",
    "Everyone":
        "Alle",
    "New person":
        "Neue Person",
    "No people yet. Add the household under Settings → People, and each account can be somebody's.":
        "Noch keine Personen. Lege den Haushalt unter Einstellungen → Personen an, dann kann jedes Konto jemandem gehören.",
    "Only {name}'s accounts are counted on this page.":
        "Auf dieser Seite zählen nur die Konten von {name}.",
    "People":
        "Personen",
    "Remove {name}? Their accounts stay.":
        "{name} entfernen? Die Konten bleiben.",
    "Removed. Their accounts stay; they just belong to one person fewer.":
        "Entfernt. Die Konten bleiben; sie gehören nur einer Person weniger.",
    "The budget itself is the household's; the spending measured against it here is {name}'s alone.":
        "Das Budget gehört dem Haushalt; die Ausgaben, die hier daran gemessen werden, sind allein die von {name}.",
    "There is already somebody called {name}.":
        "Es gibt schon jemanden namens {name}.",
    "Tick one person, or several for a joint account. Nobody ticked means it shows only under Everyone.":
        "Hake eine Person an, oder mehrere bei einem Gemeinschaftskonto. Ohne Haken erscheint es nur unter „Alle“.",
    "Whose":
        "Wessen",
    "Whose accounts":
        "Wessen Konten",
    "Whose is it":
        "Wem gehört es",
    "nobody yet":
        "noch niemandem",
    "whose accounts are whose":
        "wem welches Konto gehört",
    "{n} account":
        "{n} Konto",
    "{n} accounts":
        "{n} Konten",
    "{n} more account belongs to somebody else, or to nobody yet — switch to Everyone to see it.":
        "{n} weiteres Konto gehört jemand anderem oder noch niemandem — schalte auf „Alle“, um es zu sehen.",
    "{n} more accounts belong to somebody else, or to nobody yet — switch to Everyone to see them.":
        "{n} weitere Konten gehören jemand anderem oder noch niemandem — schalte auf „Alle“, um sie zu sehen.",
    "Belongs to {names}.":
        "Gehört {names}.",
    "Belongs to nobody yet, so it shows under Everyone only.":
        "Gehört noch niemandem und erscheint deshalb nur unter „Alle“.",
    "Change":
        "Ändern",

    # ─── Prognose und Bankabgleich ───────────────────────────────────
    "A goal to mark, in {currency}":
        "Ein Ziel zum Einzeichnen, in {currency}",
    "Amounts in a currency with no rate on file are not in that figure.":
        "Beträge in einer Währung ohne hinterlegten Kurs sind in dieser Zahl nicht enthalten.",
    "At":
        "Um",
    "Automatic sync is off.":
        "Der automatische Abgleich ist aus.",
    "Average return per year, in %":
        "Durchschnittliche Rendite pro Jahr, in %",
    "Bank sync":
        "Bankabgleich",
    "Before inflation. Broad stock-market funds have averaged around 6–8 % a year over long periods, savings accounts far less; a cautious plan uses a lower number than history did.":
        "Vor Inflation. Breite Aktienfonds haben über lange Zeiträume im Schnitt etwa 6–8 % im Jahr gebracht, Sparkonten weit weniger; ein vorsichtiger Plan rechnet mit weniger, als die Vergangenheit brachte.",
    "Calculate":
        "Berechnen",
    "Forecast":
        "Prognose",
    "Goal":
        "Ziel",
    "Goal, in {currency}":
        "Ziel, in {currency}",
    "I have a goal":
        "Ich habe ein Ziel",
    "I save a fixed amount":
        "Ich spare einen festen Betrag",
    "In {year}":
        "Im Jahr {year}",
    "Last automatic sync: {when}.":
        "Letzter automatischer Abgleich: {when}.",
    "Local time of the machine this runs on. A day that was slept through — the machine was off at that hour — is caught up as soon as it is next awake.":
        "Ortszeit des Rechners, auf dem das hier läuft. Ein verschlafener Tag — der Rechner war zu der Stunde aus — wird nachgeholt, sobald er wieder wach ist.",
    "No account is connected to a bank yet.":
        "Noch kein Konto ist mit einer Bank verbunden.",
    "No automatic sync has run yet.":
        "Es lief noch kein automatischer Abgleich.",
    "Returns":
        "Rendite",
    "Returns earn":
        "Die Rendite bringt",
    "Save per month":
        "Monatlich sparen",
    "Saved per month, in {currency}":
        "Gespart pro Monat, in {currency}",
    "Show as a table":
        "Als Tabelle zeigen",
    "Starting from {amount}: what {who} adds up to today across {n} accounts.":
        "Ausgehend von {amount}: das, was {who} heute über {n} Konten hinweg ausmacht.",
    "Sync all accounts now":
        "Alle Konten jetzt abgleichen",
    "Sync connected accounts automatically every day":
        "Verbundene Konten jeden Tag automatisch abgleichen",
    "The goal is already met — nothing more is needed.":
        "Das Ziel ist schon erreicht — es braucht nichts mehr.",
    "The next one is at {time}.":
        "Der nächste ist um {time}.",
    "What to work out":
        "Was berechnet werden soll",
    "Where the money is heading, starting from what the accounts add up to today. The return is your assumption, not a prediction — the page only does the arithmetic, and shows how much of the result is your own deposits.":
        "Wohin das Geld sich entwickelt, ausgehend von dem, was die Konten heute ergeben. Die Rendite ist deine Annahme, keine Vorhersage — die Seite rechnet nur, und zeigt, wie viel vom Ergebnis deine eigenen Einzahlungen sind.",
    "With returns":
        "Mit Rendite",
    "Year":
        "Jahr",
    "Year by year":
        "Jahr für Jahr",
    "Years from now":
        "Jahre ab heute",
    "You put in":
        "Du zahlst ein",
    "and want to know what it takes a month":
        "und will wissen, was es im Monat braucht",
    "and want to see where it leads":
        "und will sehen, wohin das führt",
    "at {rate} % a year, compounding monthly":
        "bei {rate} % im Jahr, monatlich verzinst",
    "the goal is not reached in this time":
        "das Ziel wird in dieser Zeit nicht erreicht",
    "the goal is reached in {year}":
        "das Ziel ist {year} erreicht",
    "the household":
        "der Haushalt",
    "to reach {target} by {year}":
        "um {target} bis {year} zu erreichen",
    "today's {start} plus {monthly} a month":
        "die heutigen {start} plus {monthly} im Monat",
    "{n} account connected":
        "{n} Konto verbunden",
    "{n} accounts connected":
        "{n} Konten verbunden",
    "{n} new transaction across {accounts} accounts.":
        "{n} neue Transaktion über {accounts} Konten.",
    "{n} new transactions across {accounts} accounts.":
        "{n} neue Transaktionen über {accounts} Konten.",
    "{n} year from now":
        "in {n} Jahr",
    "{n} years from now":
        "in {n} Jahren",
    "{ok} of {total} accounts synced. Failed: {names}.":
        "{ok} von {total} Konten abgeglichen. Fehlgeschlagen: {names}.",

    # ─── Verlauf, Verbindungen, Ruhestand ────────────────────────────
    "A birthday is optional; with one, the Forecast page adds a retirement outlook for that person.":
        "Ein Geburtstag ist freiwillig; mit ihm bekommt die Prognose-Seite einen Ruhestands-Ausblick für diese Person.",
    "Add the people in your household under Settings → People, each with a birthday, and this page will say where each of them stands for retirement.":
        "Lege die Personen deines Haushalts unter Einstellungen → Personen an, jede mit Geburtstag, und diese Seite sagt, wo jede von ihnen für den Ruhestand steht.",
    "Age":
        "Alter",
    "All":
        "Alle",
    "At {age}, in {year}":
        "Mit {age}, im Jahr {year}",
    "Bank connections":
        "Bankverbindungen",
    "Birthday of {name}":
        "Geburtstag von {name}",
    "Birthday — what the retirement outlook counts from":
        "Geburtstag — davon rechnet der Ruhestands-Ausblick",
    "Consent expired — reconnect.":
        "Einwilligung abgelaufen — neu verbinden.",
    "Last sync failed: {error}":
        "Letzter Abgleich fehlgeschlagen: {error}",
    "Last sync {n} days ago.":
        "Letzter Abgleich vor {n} Tagen.",
    "Last sync {n} hours ago.":
        "Letzter Abgleich vor {n} Stunden.",
    "Never synced.":
        "Noch nie abgeglichen.",
    "No birthday on file for {names}. Add one under Settings → People and the outlook appears here.":
        "Kein Geburtstag hinterlegt für {names}. Trage einen unter Einstellungen → Personen ein, dann erscheint der Ausblick hier.",
    "No dated readings yet — the line starts with the first balance or trade.":
        "Noch keine datierten Stände — die Linie beginnt mit dem ersten Kontostand oder Handel.",
    "Overrides the Forecast plan's {amount}; clear the field to follow it again.":
        "Überschreibt die {amount} des Prognose-Plans; leere das Feld, um ihm wieder zu folgen.",
    "Records go back to {date}; the line fills in with every daily sync.":
        "Die Aufzeichnungen reichen bis {date} zurück; mit jedem täglichen Abgleich füllt sich die Linie.",
    "Retire at":
        "In Rente mit",
    "Retirement outlook":
        "Ruhestands-Ausblick",
    "Return per year, %":
        "Rendite pro Jahr, %",
    "Saved per month, {currency}":
        "Gespart pro Monat, {currency}",
    "Saved.":
        "Gespeichert.",
    "Supports, per month":
        "Trägt, pro Monat",
    "Synced {n} hours ago":
        "Abgeglichen vor {n} Stunden",
    "The birthday needs to be a date.":
        "Der Geburtstag muss ein Datum sein.",
    "The monthly amount is taken from this person's Forecast plan; type one to override it.":
        "Der Monatsbetrag stammt aus dem Prognose-Plan dieser Person; tippe einen ein, um ihn zu überschreiben.",
    "Time range":
        "Zeitraum",
    "at a 4 % yearly withdrawal — the usual rule of thumb, before tax and pension":
        "bei 4 % Entnahme im Jahr — die übliche Faustregel, vor Steuern und Rente",
    "consent for {n} more days":
        "Einwilligung noch {n} Tage",
    "since the start of the range":
        "seit Beginn des Zeitraums",
    "{age} today · {n} accounts · {amount}":
        "heute {age} · {n} Konten · {amount}",
    "{name} is already {age} — past the retirement age set here.":
        "{name} ist schon {age} — über dem hier gesetzten Rentenalter.",
    "{n} connected account":
        "{n} verbundenes Konto",
    "{n} connected accounts":
        "{n} verbundene Konten",
    "{part} of it returns":
        "davon {part} Rendite",

    # ─── Aktienideen ─────────────────────────────────────────────────
    "Share Ideas": "Aktienideen",
    "Four boards over the same nightly Yahoo cache: shares that have fallen and are cheap, shares paying a high dividend that is still growing, ETFs with strong past growth at a low TER, and dividend ETFs paying a high yield at a low TER. A shortlist to research, never a recommendation to buy.":
        "Vier Tafeln über denselben nächtlichen Yahoo-Cache: Aktien, die gefallen und günstig sind, Aktien mit hoher und weiter wachsender Dividende, ETFs mit starkem bisherigem Wachstum bei niedriger TER, und Dividenden-ETFs mit hoher Ausschüttung bei niedriger TER. Eine Liste zum Nachforschen, nie eine Kaufempfehlung.",
    "Value [board]": "Substanz",
    "fallen · cheap · quality · pays": "gefallen · günstig · Qualität · zahlt",
    "Dividends": "Dividenden",
    "high yield that is still growing": "hohe Rendite, die noch wächst",
    "ETFs": "ETFs",
    "high growth · low TER": "hohes Wachstum · niedrige TER",
    "Dividend ETFs": "Dividenden-ETFs",
    "high yield · low TER": "hohe Rendite · niedrige TER",
    "The board": "Die Tafel",
    "Loading…": "Lädt…",
    "Names that pass every hard gate and therefore carry a score.":
        "Titel, die jede harte Hürde bestehen und daher eine Punktzahl tragen.",
    "Ranked candidates": "Gereihte Kandidaten",
    "Scored 70 or above out of 100 on this board.":
        "Auf dieser Tafel mit 70 oder mehr von 100 bewertet.",
    "Strong (70+)": "Stark (70+)",
    "Can sit inside a French PEA. For shares this is inferred from the country of incorporation; for ETFs it is a curated fact, because no data source publishes it.":
        "Kann in einem französischen PEA liegen. Bei Aktien aus dem Sitzland abgeleitet, bei ETFs von Hand gepflegt, weil keine Datenquelle es veröffentlicht.",
    "PEA-eligible": "PEA-fähig",
    "Excluded before scoring, with the reason kept. Listed at the bottom of the page.":
        "Vor der Bewertung ausgeschlossen, mit Grund. Unten auf der Seite aufgeführt.",
    "Gated out": "Ausgeschlossen",
    "The screen is transparent on purpose — every column below is an input to the score, not an output of it.":
        "Das Sieb ist absichtlich durchsichtig — jede Spalte unten ist eine Zutat der Punktzahl, kein Ergebnis davon.",
    "PEA-eligible only": "Nur PEA-fähige",
    "Hide what I already own": "Ausblenden, was ich schon halte",
    "Hide dismissed": "Verworfene ausblenden",
    "Watchlist only": "Nur Watchlist",
    "Sector": "Sektor",
    "Min score": "Mindestpunktzahl",
    "Show": "Zeigen",
    "all": "alle",
    "Candidates": "Kandidaten",
    "Click a row for the full breakdown.": "Eine Zeile anklicken für die ganze Aufschlüsselung.",
    "Excluded before scoring, and why. Shown because an absence you cannot explain is worse than no screen at all.":
        "Vor der Bewertung ausgeschlossen, und warum. Gezeigt, weil ein unerklärtes Fehlen schlimmer ist als gar kein Sieb.",
    "Symbol": "Symbol",
    "Group": "Gruppe",
    "Reason": "Grund",
    "Close": "Schließen",
    "How to read this": "Wie man das liest",
    "Value 25% · cheapness 25% · quality 30% · dividend 20%. It finds shares that have fallen a long way from their own 52-week high and are cheap on earnings while still earning well and paying a covered dividend.":
        "Substanz 25 % · Günstigkeit 25 % · Qualität 30 % · Dividende 20 %. Findet Aktien, die weit unter ihrem eigenen 52-Wochen-Hoch stehen und gemessen am Gewinn günstig sind, dabei aber weiter gut verdienen und eine gedeckte Dividende zahlen.",
    "The flag that matters most is “near its 52-week low”. “40% off the high” and “still falling” are the same fact seen from two ends, and only the second tells you the market has not finished selling.":
        "Der wichtigste Hinweis ist „nahe am 52-Wochen-Tief“. „40 % unter dem Hoch“ und „fällt noch“ sind dieselbe Tatsache von zwei Seiten, und nur die zweite sagt dir, dass der Markt mit dem Verkaufen nicht fertig ist.",
    "Yield 35% · growth 30% · safety 20% · quality 15%. Yield and growth carry most of it, as they should on an income board — but not all of it, because a ranking on yield alone puts the next dividend cut at the top of the list every single time. The growth pillar blends dividend growth (the forward annual rate against the last twelve months' actual), revenue growth and earnings growth.":
        "Rendite 35 % · Wachstum 30 % · Sicherheit 20 % · Qualität 15 %. Rendite und Wachstum tragen den größten Teil, wie es sich für eine Einkommens-Tafel gehört — aber nicht alles, denn eine Reihung allein nach Rendite setzt jedes Mal die nächste Dividendenkürzung ganz oben hin. Die Wachstumssäule mischt Dividendenwachstum (die angekündigte Jahresdividende gegen die der letzten zwölf Monate), Umsatzwachstum und Gewinnwachstum.",
    "A yield above 12% is gated out rather than rewarded: on a large cap that is the market pricing a cut, not an opportunity. So is a payout ratio above 90%, and a business whose revenue is shrinking. The free-cash-flow payout is the column to look at when two names have the same yield — earnings can be flattered, cash cannot, and a dividend costing more than 100% of free cash flow is being paid out of the balance sheet.":
        "Eine Rendite über 12 % wird ausgeschlossen statt belohnt: bei einem Großkonzern preist der Markt damit eine Kürzung ein, keine Gelegenheit. Ebenso eine Ausschüttungsquote über 90 % und ein schrumpfender Umsatz. Die Free-Cashflow-Ausschüttung ist die Spalte, auf die man schaut, wenn zwei Titel dieselbe Rendite haben — Gewinne lassen sich schönen, Cash nicht, und eine Dividende, die mehr als 100 % des freien Cashflows kostet, wird aus der Bilanz bezahlt.",
    "Growth 40% · cost 30% · risk 20% · size 10%. Growth is the compound annual total return in euros, computed from the adjusted price history rather than read from a field — Yahoo leaves its own return fields empty for almost every European UCITS listing, and the raw price of a distributing fund understates its return by roughly its yield every year.":
        "Wachstum 40 % · Kosten 30 % · Risiko 20 % · Größe 10 %. Wachstum ist die jährliche Gesamtrendite in Euro, aus der bereinigten Kurshistorie berechnet statt aus einem Feld gelesen — Yahoo lässt seine eigenen Renditefelder für fast jede europäische UCITS-Notierung leer, und der rohe Kurs eines ausschüttenden Fonds unterschätzt dessen Rendite jedes Jahr um ungefähr die Ausschüttung.",
    "The growth column is the past and the TER is the future. Five years that contained one of the strongest US equity runs on record will rank concentration highly for reasons that have already happened. The TER is charged every year whatever the market does — which is why cost carries 30% of a board whose headline is growth.":
        "Die Wachstumsspalte ist die Vergangenheit, die TER die Zukunft. Fünf Jahre mit einer der stärksten US-Aktienrallys aller Zeiten reihen Konzentration aus Gründen weit oben, die schon passiert sind. Die TER wird jedes Jahr abgezogen, egal was der Markt tut — deshalb tragen die Kosten 30 % auf einer Tafel, deren Überschrift Wachstum heißt.",
    "The universe is UCITS-only on purpose: without a PRIIPs KID a US-listed ETF cannot be bought at a European broker at all, so ranking one would be ranking something unbuyable. PEA eligibility is a curated fact, not an inferred one — it depends on the fund's holdings and wrapper, and a synthetic MSCI World qualifies where a physical one does not.":
        "Das Universum ist absichtlich nur UCITS: ohne PRIIPs-KID lässt sich ein US-notierter ETF bei einem europäischen Broker gar nicht kaufen, eine Reihung wäre also eine Reihung von Unkaufbarem. PEA-Fähigkeit ist von Hand gepflegt, nicht abgeleitet — sie hängt von den Beständen und der Hülle des Fonds ab, und ein synthetischer MSCI World qualifiziert sich, wo ein physischer es nicht tut.",
    "Yield 35% · cost 25% · growth 20% · stability 20%. The yield is computed from the distributions the fund actually paid over the last twelve months, not read from a field — Yahoo populates its own yield for barely one European listing in six, so a board that trusted it would be blank for five funds out of every six it ranks.":
        "Rendite 35 % · Kosten 25 % · Wachstum 20 % · Stabilität 20 %. Die Rendite wird aus den Ausschüttungen berechnet, die der Fonds in den letzten zwölf Monaten tatsächlich gezahlt hat, nicht aus einem Feld gelesen — Yahoo füllt seine eigene Rendite für kaum jede sechste europäische Notierung, eine Tafel, die ihr traute, bliebe bei fünf von sechs Fonds leer.",
    "It will read lower than the yield on the factsheet. The numerator is the past year's payments and the denominator is today's price, so a fund that has risen shows a smaller ratio than the “indicated” yield a provider quotes. Both are honest; this one is backward-looking on purpose, because a forward yield is an estimate and there are enough estimates on this page already.":
        "Sie fällt niedriger aus als die Rendite im Factsheet. Der Zähler sind die Zahlungen des vergangenen Jahres, der Nenner der heutige Kurs, ein gestiegener Fonds zeigt also ein kleineres Verhältnis als die „indikative“ Rendite eines Anbieters. Beide sind ehrlich; diese hier blickt absichtlich zurück, denn eine Vorausrendite ist eine Schätzung, und Schätzungen gibt es auf dieser Seite schon genug.",
    "Yield is only 35% for the same reason it is on the share board, and the reason bites harder here: an index that selects on yield mechanically buys whatever has just fallen. Worse, a fund has no payout ratio and no balance sheet you can interrogate — so the only evidence that its income is durable is whether it has ever collapsed. That is the Worst cut column, and it carries most of the stability pillar.":
        "Die Rendite wiegt nur 35 %, aus demselben Grund wie auf der Aktientafel, und hier beißt er härter: ein Index, der nach Rendite auswählt, kauft mechanisch, was gerade gefallen ist. Schlimmer noch, ein Fonds hat keine Ausschüttungsquote und keine Bilanz, die man befragen könnte — der einzige Beleg für dauerhaftes Einkommen ist, ob es je eingebrochen ist. Das ist die Spalte „Schlimmste Kürzung“, und sie trägt den größten Teil der Stabilitätssäule.",
    "Cost is 25% because the TER comes out of the same cash the distribution does. At a 3.5% yield a 0.45% TER is not “half a percent” — it is 13% of your income, every year, guaranteed. The Net column does that subtraction. Accumulating share classes are gated out: they pay nothing, which does not make them bad funds, only not income ones.":
        "Kosten wiegen 25 %, weil die TER aus demselben Geld kommt wie die Ausschüttung. Bei 3,5 % Rendite ist eine TER von 0,45 % nicht „ein halbes Prozent“ — es sind 13 % deines Einkommens, jedes Jahr, garantiert. Die Spalte „Netto“ rechnet das ab. Thesaurierende Anteilsklassen werden ausgeschlossen: sie zahlen nichts, was sie nicht zu schlechten Fonds macht, nur nicht zu Einkommensfonds.",
    "Every score is a sorting device for a research queue, not a valuation and not advice. Fundamentals come from Yahoo and are refreshed once a day in the background; they can be wrong, stale, or reported in a currency other than the price. Verify the two or three names you actually care about at the source before doing anything.":
        "Jede Punktzahl ist ein Sortierwerkzeug für eine Recherche-Liste, keine Bewertung und kein Rat. Die Kennzahlen kommen von Yahoo und werden einmal am Tag im Hintergrund aktualisiert; sie können falsch, veraltet oder in einer anderen Währung als der Kurs gemeldet sein. Prüfe die zwei oder drei Titel, die dich wirklich interessieren, an der Quelle, bevor du irgendetwas tust.",

    # Spalten und Kürzel
    "Score": "Punkte",
    "Pillars": "Säulen",
    "Off high": "Unter Hoch",
    "P/E": "KGV",
    "Yield": "Rendite",
    "Payout": "Ausschüttung",
    "ROE": "EK-Rendite",
    "Debt/Eq": "Verschuldung",
    "Div growth": "Div.-Wachstum",
    "Rev growth": "Umsatzwachstum",
    "EPS growth": "Gewinnwachstum",
    "FCF payout": "FCF-Ausschüttung",
    "5y p.a.": "5 J. p. a.",
    "3y p.a.": "3 J. p. a.",
    "1y": "1 J.",
    "Vol": "Vola",
    "Max DD": "Max. Rückgang",
    "Policy": "Art",
    "Size": "Größe",
    "Net": "Netto",
    "Worst cut": "Schlimmste Kürzung",
    "Pays": "Zahlt",
    "Region": "Region",
    "no data": "keine Daten",
    "held": "im Depot",
    "Already in the portfolio": "Schon im Depot",
    "Can sit in a French PEA.": "Kann in einem französischen PEA liegen.",
    "watching": "beobachtet",
    "dismissed": "verworfen",
    "Add to watchlist": "Auf die Watchlist",
    "Dismiss": "Verwerfen",
    "☆ Watch": "☆ Beobachten",
    "✕ Dismiss": "✕ Verwerfen",
    "Clear mark": "Markierung löschen",
    "Open on Yahoo ↗": "Bei Yahoo öffnen ↗",
    "Nothing matches these filters.": "Nichts passt zu diesen Filtern.",
    "Nothing gated out.": "Nichts ausgeschlossen.",
    "Gated out:": "Ausgeschlossen:",
    "Last fetch error:": "Letzter Abruffehler:",
    "data coverage": "Datenabdeckung",
    "mkt cap": "Marktkap.",
    "yes": "ja",
    "no": "nein",
    "yes (EU/EEA seat)": "ja (Sitz in EU/EWR)",
    "no — outside a PEA only": "nein — nur außerhalb eines PEA",
    "never fell": "nie gefallen",
    "× a year": "× im Jahr",
    "Failed to load": "Laden fehlgeschlagen",
    "Loaded, but failed to render — see the console":
        "Geladen, aber nicht darstellbar — siehe Konsole",
    "{n} screened · last refresh {date}": "{n} geprüft · zuletzt aktualisiert {date}",
    "This cache is empty. The first refresh starts a minute after start-up and takes a few minutes; there is also a button under Settings.":
        "Dieser Cache ist leer. Die erste Aktualisierung beginnt eine Minute nach dem Start und dauert ein paar Minuten; unter Einstellungen gibt es auch einen Knopf dafür.",
    "Data was last refreshed {days} days ago. Every price-derived figure below is that old.":
        "Die Daten wurden vor {days} Tagen zuletzt aktualisiert. Jede kursabhängige Zahl unten ist so alt.",
    "{n} symbol(s) failed their last fetch and are showing older figures.":
        "{n} Symbol(e) konnten zuletzt nicht abgerufen werden und zeigen ältere Zahlen.",
    "Hide": "Verbergen",
    "A hollow bar means there was no data for that pillar — the score is then a mean over the pillars that do have data, which is why thin rows carry a “thin data” flag.":
        "Ein hohler Balken heißt: keine Daten für diese Säule — die Punktzahl ist dann der Mittelwert der Säulen mit Daten, weshalb dünne Zeilen den Hinweis „dünne Daten“ tragen.",
    "Trailing where there is a trailing profit, otherwise the forward estimate (marked ƒ).":
        "Rückblickend, wo es einen Gewinn der letzten zwölf Monate gibt, sonst die Vorausschätzung (mit ƒ markiert).",
    "Yahoo’s figure, not the KID’s": "Zahl von Yahoo, nicht aus dem KID",
    "value": "Substanz",
    "cheap": "günstig",
    "quality": "Qualität",
    "dividend": "Dividende",
    "yield": "Rendite",
    "growth": "Wachstum",
    "safety": "Sicherheit",
    "cost": "Kosten",
    "risk": "Risiko",
    "size": "Größe",
    "stability": "Stabilität",
    "Ongoing charge per year. Curated from the fund KID where we have it; Yahoo otherwise, which is then flagged.":
        "Laufende Kosten pro Jahr. Aus dem KID des Fonds, wo wir es haben; sonst von Yahoo, was dann markiert wird.",

    # Die vier Tafeln
    "Cheap and beaten down": "Günstig und abgestraft",
    "Shares that have fallen from their own 52-week high, trade on a low P/E, still earn well, and pay a dividend their earnings cover.":
        "Aktien, die von ihrem eigenen 52-Wochen-Hoch gefallen sind, ein niedriges KGV haben, weiter gut verdienen und eine Dividende zahlen, die ihre Gewinne decken.",
    "Pillar bars are, left to right: value (how far it has fallen), cheap (P/E and price-to-book), quality (ROE, operating margin, leverage, liquidity), dividend (yield, and whether earnings cover it).":
        "Die Säulen sind, von links nach rechts: Substanz (wie weit gefallen), günstig (KGV und Kurs-Buchwert), Qualität (Eigenkapitalrendite, operative Marge, Verschuldung, Liquidität), Dividende (Rendite, und ob die Gewinne sie decken).",
    "How far below its own 52-week high the price sits.":
        "Wie weit der Kurs unter dem eigenen 52-Wochen-Hoch liegt.",
    "Share of earnings paid out as dividend. Sweet spot 25–60%.":
        "Anteil des Gewinns, der als Dividende ausgezahlt wird. Ideal 25–60 %.",
    "Ratio, not percent. Above 2.0 is flagged.": "Verhältnis, nicht Prozent. Über 2,0 wird markiert.",
    "High dividend, still growing": "Hohe Dividende, die noch wächst",
    "The highest yields that are not warning you about themselves: the dividend must be growing, covered by earnings AND by free cash flow, on a business that is not shrinking.":
        "Die höchsten Renditen, die nicht vor sich selbst warnen: die Dividende muss wachsen, durch Gewinn UND freien Cashflow gedeckt sein, in einem Geschäft, das nicht schrumpft.",
    "Pillar bars are, left to right: yield (what it pays today), growth (dividend, revenue and earnings growth), safety (payout ratio, free-cash-flow cover, leverage, liquidity), quality (ROE and margins). Dividend growth is the forward annual rate against the last twelve months actually paid, so a declared cut shows up here the day it is announced rather than a year later.":
        "Die Säulen sind, von links nach rechts: Rendite (was heute gezahlt wird), Wachstum (Dividende, Umsatz und Gewinn), Sicherheit (Ausschüttungsquote, Deckung durch freien Cashflow, Verschuldung, Liquidität), Qualität (Eigenkapitalrendite und Margen). Dividendenwachstum ist die angekündigte Jahresdividende gegen die in den letzten zwölf Monaten tatsächlich gezahlte, eine erklärte Kürzung erscheint hier also am Tag der Ankündigung statt ein Jahr später.",
    "Forward annual dividend against the last twelve months actually paid. Negative = a cut has been declared.":
        "Angekündigte Jahresdividende gegen die der letzten zwölf Monate. Negativ = eine Kürzung ist erklärt.",
    "Share of EARNINGS paid out.": "Anteil des GEWINNS, der ausgeschüttet wird.",
    "Share of FREE CASH FLOW paid out. Above 100% the dividend is coming out of the balance sheet.":
        "Anteil des FREIEN CASHFLOWS, der ausgeschüttet wird. Über 100 % kommt die Dividende aus der Bilanz.",
    "High growth, low TER": "Hohes Wachstum, niedrige TER",
    "UCITS ETFs ranked on compound annual total return in EUR against what they charge for it. Growth is the past; the TER is the only column here that is a fact about the future.":
        "UCITS-ETFs gereiht nach jährlicher Gesamtrendite in EUR gegen das, was sie dafür verlangen. Wachstum ist die Vergangenheit; die TER ist hier die einzige Spalte, die eine Tatsache über die Zukunft ist.",
    "Pillar bars are, left to right: growth (5-year and 3-year CAGR in EUR, total return), cost (TER), risk (return per unit of volatility, and the worst peak-to-trough fall in the window), size (fund assets — a small fund can close, and trades on a wider spread). Returns are converted to euros before they are measured: a USD-quoted UCITS ETF and its EUR-quoted twin are the same fund, and comparing their raw returns would rank the dollar.":
        "Die Säulen sind, von links nach rechts: Wachstum (5- und 3-Jahres-Rendite p. a. in EUR, Gesamtrendite), Kosten (TER), Risiko (Rendite je Einheit Volatilität und der schlimmste Rückgang vom Hoch zum Tief im Zeitfenster), Größe (Fondsvolumen — ein kleiner Fonds kann schließen und handelt mit weiterem Spread). Renditen werden vor der Messung in Euro umgerechnet: ein in USD notierter UCITS-ETF und sein EUR-Zwilling sind derselbe Fonds, und rohe Renditen zu vergleichen würde den Dollar reihen.",
    "Compound annual total return over five years, in EUR.":
        "Jährliche Gesamtrendite über fünf Jahre, in EUR.",
    "Annualised standard deviation of weekly returns over the last year.":
        "Annualisierte Standardabweichung der Wochenrenditen im letzten Jahr.",
    "Worst peak-to-trough fall within the cached history.":
        "Schlimmster Rückgang vom Hoch zum Tief innerhalb der gespeicherten Historie.",
    "acc = accumulating (nothing is paid out, nothing is taxed until you sell). dist = distributing.":
        "acc = thesaurierend (nichts wird ausgezahlt, nichts besteuert, bis du verkaufst). dist = ausschüttend.",
    "High yield, low TER": "Hohe Rendite, niedrige TER",
    "Distributing UCITS ETFs ranked on the income they actually paid over the last twelve months against what they charge for it — and on whether that income is growing rather than being cut. Accumulating share classes are excluded: they pay nothing.":
        "Ausschüttende UCITS-ETFs gereiht nach dem Einkommen, das sie in den letzten zwölf Monaten tatsächlich gezahlt haben, gegen das, was sie dafür verlangen — und danach, ob dieses Einkommen wächst statt gekürzt zu werden. Thesaurierende Anteilsklassen sind ausgeschlossen: sie zahlen nichts.",
    "Pillar bars are, left to right: yield (distributions paid over the last twelve months, divided by today’s price), cost (TER), growth (this year’s distributions against last year’s, plus the price return as a check that the income is not just capital coming back), stability (the worst year-on-year fall in the distribution on record, and the worst peak-to-trough price fall). The yield is computed from the distributions themselves, not read from a field — Yahoo populates its own yield for barely one European listing in six. Because the numerator is the past year and the denominator is today’s price, it reads lower than a provider’s “indicated yield” whenever the fund has risen.":
        "Die Säulen sind, von links nach rechts: Rendite (Ausschüttungen der letzten zwölf Monate, geteilt durch den heutigen Kurs), Kosten (TER), Wachstum (die Ausschüttungen dieses Jahres gegen die des Vorjahres, plus die Kursrendite als Prüfung, dass das Einkommen nicht bloß zurückfließendes Kapital ist), Stabilität (der schlimmste Jahresrückgang der Ausschüttung und der schlimmste Kursrückgang vom Hoch zum Tief). Die Rendite wird aus den Ausschüttungen selbst berechnet, nicht aus einem Feld gelesen — Yahoo füllt seine eigene Rendite für kaum jede sechste europäische Notierung. Weil der Zähler das vergangene Jahr und der Nenner der heutige Kurs ist, fällt sie niedriger aus als die „indikative Rendite“ eines Anbieters, sobald der Fonds gestiegen ist.",
    "Distributions actually paid over the last 12 months, divided by the current price.":
        "In den letzten 12 Monaten tatsächlich gezahlte Ausschüttungen, geteilt durch den aktuellen Kurs.",
    "Yield minus TER — the income that reaches you before tax. Shown, never ranked on: a high net yield can come from paying a lot or from costing little, and those are different funds.":
        "Rendite minus TER — das Einkommen, das vor Steuern bei dir ankommt. Angezeigt, nie zum Reihen benutzt: eine hohe Nettorendite kann aus viel Zahlen oder aus wenig Kosten kommen, und das sind verschiedene Fonds.",
    "Distributions of the last 12 months against the 12 before. Negative = the payout is shrinking.":
        "Ausschüttungen der letzten 12 Monate gegen die 12 davor. Negativ = die Ausschüttung schrumpft.",
    "The deepest year-on-year fall in the distribution across the years on record. “none” means every year on record was at least as big as the one before. Blank means there is not enough history to say.":
        "Der tiefste Jahresrückgang der Ausschüttung über alle erfassten Jahre. „keine“ heißt: jedes erfasste Jahr war mindestens so groß wie das davor. Leer heißt: zu wenig Historie, um es zu sagen.",
    "Compound annual TOTAL return in EUR — price plus distributions reinvested. A high yield beside a poor total return means capital is being handed back.":
        "Jährliche GESAMTRENDITE in EUR — Kurs plus wiederangelegte Ausschüttungen. Eine hohe Rendite neben einer schwachen Gesamtrendite heißt: hier wird Kapital zurückgegeben.",
    "Distributions in the last 12 months: 1 = annual, 2 = semi-annual, 4 = quarterly, 12 = monthly.":
        "Ausschüttungen in den letzten 12 Monaten: 1 = jährlich, 2 = halbjährlich, 4 = vierteljährlich, 12 = monatlich.",

    # Die Detailansicht
    "Trailing yield": "Rendite (12 Monate)",
    "Distributions paid over the last 12 months divided by the current price. Computed from the payments themselves — Yahoo’s own yield field is populated for barely one European listing in six.":
        "Ausschüttungen der letzten 12 Monate geteilt durch den aktuellen Kurs. Aus den Zahlungen selbst berechnet — Yahoos eigenes Renditefeld ist für kaum jede sechste europäische Notierung gefüllt.",
    "Charged out of the same cash the distribution comes from.":
        "Wird aus demselben Geld abgezogen, aus dem die Ausschüttung kommt.",
    "Net yield": "Nettorendite",
    "Yield minus TER, before any tax. Shown but never ranked on — a high net yield can come from paying a lot or from costing little.":
        "Rendite minus TER, vor Steuern. Angezeigt, aber nie zum Reihen benutzt — eine hohe Nettorendite kann aus viel Zahlen oder aus wenig Kosten kommen.",
    "TER as a share of income": "TER als Anteil des Einkommens",
    "What proportion of the income the fund keeps. Half a percent sounds small until it is 13% of a 3.5% yield.":
        "Welchen Teil des Einkommens der Fonds behält. Ein halbes Prozent klingt klein, bis es 13 % von 3,5 % Rendite sind.",
    "Distributions, last 12m": "Ausschüttungen, letzte 12 M.",
    "In the listing currency. A yield is a ratio, so it needs no currency conversion.":
        "In der Notierungswährung. Eine Rendite ist ein Verhältnis und braucht keine Umrechnung.",
    "Distributions, 12m before": "Ausschüttungen, 12 M. davor",
    "Distribution growth": "Ausschüttungswachstum",
    "This year’s total against last year’s.": "Die Summe dieses Jahres gegen die des Vorjahres.",
    "Worst year on record": "Schlimmstes erfasstes Jahr",
    "The deepest year-on-year fall in the distribution across the years available. An index fund has no payout ratio to interrogate, so this is the only evidence that its income is durable.":
        "Der tiefste Jahresrückgang der Ausschüttung über die verfügbaren Jahre. Ein Indexfonds hat keine Ausschüttungsquote, die man befragen könnte, das hier ist also der einzige Beleg, dass sein Einkommen dauerhaft ist.",
    "A change in frequency makes one year’s total incomparable with the next.":
        "Ein Wechsel des Rhythmus macht die Jahressumme mit der nächsten unvergleichbar.",
    "Last distribution": "Letzte Ausschüttung",
    "Distribution history": "Ausschüttungshistorie",
    "5-year total return": "5-Jahres-Gesamtrendite",
    "Price plus distributions reinvested, in EUR. A high yield beside a weak total return means capital is being returned rather than earned.":
        "Kurs plus wiederangelegte Ausschüttungen, in EUR. Eine hohe Rendite neben einer schwachen Gesamtrendite heißt: Kapital wird zurückgegeben, nicht verdient.",
    "Max drawdown": "Max. Rückgang",
    "Fund size": "Fondsvolumen",
    "Policy (curated)": "Art (gepflegt)",
    "Cross-checked against the distributions actually observed; a disagreement is flagged rather than resolved silently.":
        "Gegen die tatsächlich beobachteten Ausschüttungen geprüft; ein Widerspruch wird markiert statt still aufgelöst.",
    "Provider": "Anbieter",
    "Matters more on an income holding than on an accumulating one: outside a PEA every distribution is taxed the year it is paid, so the headline yield is not the net one.":
        "Wiegt bei einer Einkommensposition schwerer als bei einer thesaurierenden: außerhalb eines PEA wird jede Ausschüttung im Jahr der Zahlung besteuert, die Bruttorendite ist also nicht die Nettorendite.",
    "In the portfolio": "Im Depot",
    "Data fetched": "Daten abgerufen",
    "Curated from the fund KID where we have it — Yahoo has no expense ratio for most European listings, and reports it in two different units when it does.":
        "Aus dem KID des Fonds, wo wir es haben — Yahoo hat für die meisten europäischen Notierungen keine Kostenquote, und wenn doch, meldet es sie in zwei verschiedenen Einheiten.",
    "Yahoo’s TER": "TER laut Yahoo",
    "Kept as a cross-check. A disagreement usually means a different share class.":
        "Als Gegenprobe behalten. Ein Widerspruch heißt meist: eine andere Anteilsklasse.",
    "5-year CAGR": "5-Jahres-Rendite p. a.",
    "Compound annual total return in EUR, from the dividend-adjusted price history.":
        "Jährliche Gesamtrendite in EUR, aus der dividendenbereinigten Kurshistorie.",
    "3-year CAGR": "3-Jahres-Rendite p. a.",
    "1-year return": "1-Jahres-Rendite",
    "Volatility (1y)": "Volatilität (1 J.)",
    "Annualised standard deviation of weekly returns.":
        "Annualisierte Standardabweichung der Wochenrenditen.",
    "Worst peak-to-trough fall inside the cached history — measured on weekly closes, so it is a floor on the real figure.":
        "Schlimmster Rückgang vom Hoch zum Tief in der gespeicherten Historie — auf Wochenschlusskursen gemessen, also eine Untergrenze der echten Zahl.",
    "Return per unit of vol": "Rendite je Einheit Vola",
    "3-year CAGR divided by volatility. Not a Sharpe ratio — no risk-free rate is subtracted.":
        "3-Jahres-Rendite p. a. geteilt durch Volatilität. Keine Sharpe-Ratio — kein risikofreier Zins wird abgezogen.",
    "A small fund can be closed and merged, and trades on a wider spread.":
        "Ein kleiner Fonds kann geschlossen und verschmolzen werden und handelt mit weiterem Spread.",
    "Distribution policy": "Ausschüttungsart",
    "acc = accumulating. Outside a tax wrapper, a distributing fund is taxed on each distribution in the year it is paid.":
        "acc = thesaurierend. Ohne steuerliche Hülle wird ein ausschüttender Fonds auf jede Ausschüttung im Jahr der Zahlung besteuert.",
    "History used": "Verwendete Historie",
    "A curated fact, not an inferred one: it depends on the fund’s holdings and wrapper, and no data source publishes it.":
        "Von Hand gepflegt, nicht abgeleitet: es hängt von den Beständen und der Hülle des Fonds ab, und keine Datenquelle veröffentlicht es.",
    "Dividend yield": "Dividendenrendite",
    "5-year average yield": "5-Jahres-Durchschnittsrendite",
    "A yield far above its own average is often a falling price, not a rising dividend.":
        "Eine Rendite weit über dem eigenen Durchschnitt ist oft ein fallender Kurs, keine steigende Dividende.",
    "Payout ratio": "Ausschüttungsquote",
    "Share of earnings paid out.": "Anteil des Gewinns, der ausgeschüttet wird.",
    "Trailing where there is a trailing profit, else forward.":
        "Rückblickend, wo es einen Gewinn gibt, sonst vorausschauend.",
    "Trailing / forward P/E": "KGV rückblickend / voraus",
    "Price / book": "Kurs / Buchwert",
    "Return on equity": "Eigenkapitalrendite",
    "Operating margin": "Operative Marge",
    "Profit margin": "Gewinnmarge",
    "Debt / equity": "Verschuldung / Eigenkapital",
    "Ratio, not percent.": "Verhältnis, nicht Prozent.",
    "Current ratio": "Liquidität 3. Grades",
    "Revenue growth": "Umsatzwachstum",
    "Earnings growth": "Gewinnwachstum",
    "Off 52-week high": "Unter 52-Wochen-Hoch",
    "Above 52-week low": "Über 52-Wochen-Tief",
    "Small = the market may not have finished selling.":
        "Klein = der Markt ist mit dem Verkaufen vielleicht nicht fertig.",
    "Beta": "Beta",
    "Indicative, from the reported country of incorporation. Confirm with the broker.":
        "Indikativ, aus dem gemeldeten Sitzland. Beim Broker bestätigen.",
    "Fundamentals fetched": "Kennzahlen abgerufen",
    "Dividend growth": "Dividendenwachstum",
    "Forward annual dividend against the last twelve months actually paid.":
        "Angekündigte Jahresdividende gegen die in den letzten zwölf Monaten tatsächlich gezahlte.",
    "Forward / trailing dividend": "Dividende voraus / rückblickend",
    "Per share, in the reporting currency. Their ratio is the growth figure above.":
        "Je Aktie, in der Berichtswährung. Ihr Verhältnis ist die Wachstumszahl oben.",
    "Free-cash-flow payout": "Free-Cashflow-Ausschüttung",
    "Dividends as a share of free cash flow. Earnings can be flattered; cash cannot.":
        "Dividenden als Anteil des freien Cashflows. Gewinne lassen sich schönen, Cash nicht.",
    "Free cash flow": "Freier Cashflow",

    # Einstellungen
    "refreshing now": "wird gerade aktualisiert",
    "last refreshed {when}": "zuletzt aktualisiert {when}",
    "never refreshed": "noch nie aktualisiert",
    "The four boards under Share Ideas rank a fixed list of shares and ETFs on figures fetched from Yahoo — free, without a key. The cache is refreshed once a day in the background; the first refresh runs a minute after start-up. A refresh is a few hundred requests with a pause between them and takes a few minutes, so it runs on its own and the boards fill in as it goes.":
        "Die vier Tafeln unter Aktienideen reihen eine feste Liste von Aktien und ETFs nach Kennzahlen von Yahoo — kostenlos, ohne Schlüssel. Der Cache wird einmal am Tag im Hintergrund aktualisiert; die erste Aktualisierung läuft eine Minute nach dem Start. Eine Aktualisierung sind ein paar hundert Anfragen mit Pausen dazwischen und dauert ein paar Minuten, deshalb läuft sie für sich, und die Tafeln füllen sich nach und nach.",
    "Shares: {n} cached, {errors} with a fetch error.":
        "Aktien: {n} im Cache, {errors} mit Abruffehler.",
    "ETFs: {n} cached, {errors} with a fetch error.":
        "ETFs: {n} im Cache, {errors} mit Abruffehler.",
    "To screen more names, or to correct an ETF's TER, edit screener_universe.json and screener_etf_universe.json in the data folder; thresholds live in screener.json beside them. All three are read on every page load.":
        "Um mehr Titel zu prüfen oder die TER eines ETFs zu korrigieren, bearbeite screener_universe.json und screener_etf_universe.json im Datenordner; die Schwellen stehen daneben in screener.json. Alle drei werden bei jedem Seitenaufruf gelesen.",
    "Refresh share ideas now": "Aktienideen jetzt aktualisieren",
    "everything, not only what is older than a day":
        "alles, nicht nur, was älter als ein Tag ist",
    "Refreshing the share ideas in the background. It takes a few minutes; the boards fill in as it goes.":
        "Die Aktienideen werden im Hintergrund aktualisiert. Das dauert ein paar Minuten; die Tafeln füllen sich nach und nach.",
    "A refresh is already running.": "Eine Aktualisierung läuft schon.",

    # Hürden und Hinweise, vom Server formuliert
    "not a share ({type})": "keine Aktie ({type})",
    "no market cap": "keine Marktkapitalisierung",
    "too small ({bn}bn)": "zu klein ({bn} Mrd.)",
    "no positive earnings": "kein positiver Gewinn",
    "P/E too high ({pe})": "KGV zu hoch ({pe})",
    "pays no dividend": "zahlt keine Dividende",
    "token dividend ({pct}%)": "Alibi-Dividende ({pct} %)",
    "dividend not covered ({pct}% payout)": "Dividende nicht gedeckt ({pct} % Ausschüttung)",
    "near its 52-week low — still falling?": "nahe am 52-Wochen-Tief — fällt noch?",
    "payout ratio above 90% — dividend barely covered":
        "Ausschüttungsquote über 90 % — Dividende kaum gedeckt",
    "yield far above its own 5-year average — possible yield trap":
        "Rendite weit über dem eigenen 5-Jahres-Schnitt — mögliche Renditefalle",
    "no trailing profit — P/E is the forward estimate":
        "kein Gewinn der letzten zwölf Monate — KGV ist die Vorausschätzung",
    "earnings down {pct}% year on year": "Gewinn {pct} % unter Vorjahr",
    "leveraged ({ratio}x debt/equity)": "verschuldet ({ratio}× Fremd-/Eigenkapital)",
    "thin data — score built on few figures": "dünne Daten — Punktzahl aus wenigen Zahlen",
    "yield too low for income ({pct}%)": "Rendite zu niedrig für Einkommen ({pct} %)",
    "yield says distress ({pct}%)": "Rendite signalisiert Not ({pct} %)",
    "payout leaves no headroom ({pct}%)": "Ausschüttung lässt keinen Spielraum ({pct} %)",
    "revenue shrinking ({pct}%)": "Umsatz schrumpft ({pct} %)",
    "forward dividend {pct}% BELOW the trailing one — a cut is already declared":
        "angekündigte Dividende {pct} % UNTER der bisherigen — eine Kürzung ist schon erklärt",
    "dividend rate moved more than 50% — likely a special, or a change of payment frequency, not real growth":
        "Dividende um mehr als 50 % verändert — wohl eine Sonderausschüttung oder ein neuer Rhythmus, kein echtes Wachstum",
    "yield well above its own 5-year average — the price fell, the dividend did not rise":
        "Rendite deutlich über dem eigenen 5-Jahres-Schnitt — der Kurs fiel, die Dividende stieg nicht",
    "dividend costs {pct}% of free cash flow — paid out of the balance sheet, not out of the business":
        "Dividende kostet {pct} % des freien Cashflows — aus der Bilanz bezahlt, nicht aus dem Geschäft",
    "payout ratio {pct}% — little room for a bad year":
        "Ausschüttungsquote {pct} % — wenig Luft für ein schlechtes Jahr",
    "near its 52-week low — the market is still selling":
        "nahe am 52-Wochen-Tief — der Markt verkauft noch",
    "not a fund ({type})": "kein Fonds ({type})",
    "leveraged or inverse — a multi-year CAGR is meaningless":
        "gehebelt oder invers — eine Mehrjahresrendite ist bedeutungslos",
    "no TER known — add it to screener_etf_universe.json":
        "keine TER bekannt — in screener_etf_universe.json eintragen",
    "too expensive ({pct}% a year)": "zu teuer ({pct} % im Jahr)",
    "no price history": "keine Kurshistorie",
    "only {years} years of history": "nur {years} Jahre Historie",
    "fund too small ({m}m)": "Fonds zu klein ({m} Mio.)",
    "our TER {ours}% vs Yahoo's {theirs}% — likely a different share class; check the ISIN":
        "unsere TER {ours} % gegen Yahoos {theirs} % — wohl eine andere Anteilsklasse; ISIN prüfen",
    "TER is Yahoo's, not the KID's — verify before ranking on it":
        "TER stammt von Yahoo, nicht aus dem KID — prüfen, bevor man danach reiht",
    "returns are in {ccy}, not EUR — the FX series could not be fetched, so this row is not comparable with the rest":
        "Renditen in {ccy}, nicht EUR — die Wechselkurse ließen sich nicht abrufen, diese Zeile ist mit den anderen nicht vergleichbar",
    "under 5 years of history — growth is the 3-year figure alone":
        "unter 5 Jahre Historie — Wachstum ist allein die 3-Jahres-Zahl",
    "distributing — outside a tax wrapper each distribution is taxed in the year it is paid, so it compounds slower":
        "ausschüttend — ohne steuerliche Hülle wird jede Ausschüttung im Jahr der Zahlung besteuert, der Zinseszins ist also langsamer",
    "fell {pct}% peak to trough within this window":
        "fiel in diesem Zeitfenster {pct} % vom Hoch zum Tief",
    "volatile ({pct}% a year)": "volatil ({pct} % im Jahr)",
    "single theme or sector — a concentrated bet, not a core holding":
        "ein einzelnes Thema oder ein Sektor — eine konzentrierte Wette, keine Kernposition",
    "fund size unknown — Yahoo reports none for this listing":
        "Fondsvolumen unbekannt — Yahoo meldet für diese Notierung keines",
    "US mutual fund — its annual distribution is mostly realised capital gains, not income":
        "US-Investmentfonds — seine Jahresausschüttung ist überwiegend realisierter Kursgewinn, kein Einkommen",
    "leveraged or inverse — not an income holding": "gehebelt oder invers — keine Einkommensposition",
    "no distribution data — the fetch has not run yet":
        "keine Ausschüttungsdaten — der Abruf ist noch nicht gelaufen",
    "accumulating — reinvests internally and pays no income":
        "thesaurierend — legt intern wieder an und zahlt kein Einkommen",
    "yield too low for an income holding ({pct}%)":
        "Rendite zu niedrig für eine Einkommensposition ({pct} %)",
    "implausible yield ({pct}%) — a special distribution, a return of capital, or a stale price":
        "unplausible Rendite ({pct} %) — eine Sonderausschüttung, Kapitalrückzahlung oder ein veralteter Kurs",
    "only {years} years of price history": "nur {years} Jahre Kurshistorie",
    "only {years} years of distributions — too short to tell a rising payout from a lucky one":
        "nur {years} Jahre Ausschüttungen — zu kurz, um eine steigende Ausschüttung von einer glücklichen zu unterscheiden",
    "listed as accumulating but has paid distributions — the universe entry is probably the wrong share class":
        "als thesaurierend geführt, hat aber ausgeschüttet — der Eintrag im Universum ist wohl die falsche Anteilsklasse",
    "listed as distributing but has paid nothing in 12 months — probably the accumulating share class of the same fund":
        "als ausschüttend geführt, hat aber in 12 Monaten nichts gezahlt — wohl die thesaurierende Anteilsklasse desselben Fonds",
    "our trailing yield {ours}% vs Yahoo's {theirs}% — check for a special distribution":
        "unsere Rendite {ours} % gegen Yahoos {theirs} % — auf eine Sonderausschüttung prüfen",
    "paid {now} times this year vs {before} last — a schedule change, so the growth figure is not like-for-like":
        "dieses Jahr {now}-mal gezahlt gegen {before}-mal im Vorjahr — ein neuer Rhythmus, die Wachstumszahl vergleicht also nicht Gleiches mit Gleichem",
    "has cut before — worst year was {pct}%": "hat schon gekürzt — das schlimmste Jahr war {pct} %",
    "distribution is shrinking ({pct}% year on year)": "Ausschüttung schrumpft ({pct} % zum Vorjahr)",
    "the TER eats {pct}% of the income": "die TER frisst {pct} % des Einkommens",
    "PEA-eligible — distributions inside a PEA are not taxed in the year they are paid, which matters more on an income holding than on an accumulating one":
        "PEA-fähig — Ausschüttungen in einem PEA werden nicht im Jahr der Zahlung besteuert, was bei einer Einkommensposition schwerer wiegt als bei einer thesaurierenden",
    "not PEA-eligible — in a plain broker account each distribution is taxed the year it is paid, so the headline yield is not the net one":
        "nicht PEA-fähig — in einem gewöhnlichen Depot wird jede Ausschüttung im Jahr der Zahlung besteuert, die Bruttorendite ist also nicht die Nettorendite",
    "single sector — a concentrated bet, not a core income holding":
        "ein einzelner Sektor — eine konzentrierte Wette, keine Kern-Einkommensposition",
    "the same fund is also listed as {others} — pick the listing your broker offers, they are not separate holdings":
        "derselbe Fonds ist auch als {others} notiert — nimm die Notierung, die dein Broker anbietet, es sind keine getrennten Positionen",

    # ─── MCP ─────────────────────────────────────────────────────────
    'An assistant that speaks MCP can read this dashboard and do the chores that are slow by hand — categorise the queue and teach the rules, set budgets, type in a transaction, star a share idea, start a sync. It cannot delete an account, change settings, or see your bank credentials. Access is by a token, which stands in for your password: keep it as private, and revoke it here the moment you are unsure.':
        'Ein Assistent, der MCP spricht, kann dieses Dashboard lesen und die Arbeiten erledigen, die von Hand langsam sind — die Warteschlange kategorisieren und die Regeln beibringen, Budgets setzen, eine Transaktion eintippen, eine Aktienidee markieren, eine Synchronisierung anstoßen. Er kann kein Konto löschen, keine Einstellungen ändern und deine Bankzugangsdaten nicht sehen. Der Zugang läuft über ein Token, das deinem Passwort gleichkommt: halte es genauso geheim, und widerrufe es hier, sobald du unsicher bist.',
    'Claude and other assistants (MCP)': 'Claude und andere Assistenten (MCP)',
    'Create a token': 'Token erstellen',
    'For Claude Code on your network, this is the whole setup:': 'Für Claude Code in deinem Netz ist das die ganze Einrichtung:',
    'Replace the token': 'Token ersetzen',
    'Revoke': 'Widerrufen',
    'Token created. Any earlier token stopped working.': 'Token erstellt. Ein früheres Token funktioniert nicht mehr.',
    'Token revoked. Anything connected with it is cut off.': 'Token widerrufen. Alles, was damit verbunden war, ist abgeschnitten.',
    'a token exists': 'ein Token ist vorhanden',
    'off — no token': 'aus — kein Token',

    # ─── Saxo und Kraken ───────────────────────────────────────────────
    'API key': 'API-Schlüssel',
    'Add your Kraken API key under Settings first.': 'Trag zuerst deinen Kraken-API-Schlüssel unter Einstellungen ein.',
    "At developer.saxo → Apps, create an application: Live (or Simulation, to try it against Saxo's demo account), grant type Authorization Code, and this exact redirect URL:":
        'Lege unter developer.saxo → Apps eine Anwendung an: Live (oder Simulation, um es am Saxo-Demokonto auszuprobieren), Grant-Typ Authorization Code, und genau diese Redirect-URL:',
    'Broker connection': 'Broker-Verbindung',
    'Connect Kraken': 'Kraken verbinden',
    'Connect Saxo': 'Saxo verbinden',
    'Connect Saxo again': 'Saxo erneut verbinden',
    'Connected. Imported {n} transaction.': 'Verbunden. {n} Transaktion importiert.',
    'Connected. Imported {n} transactions.': 'Verbunden. {n} Transaktionen importiert.',
    'Environment': 'Umgebung',
    'Finish by hand': 'Von Hand abschließen',
    'Forget Saxo': 'Saxo vergessen',
    'Forget the Kraken key': 'Kraken-Schlüssel vergessen',
    "It is your dashboard's address plus /saxo/callback, taken from the redirect URL above. If Saxo will not accept it, register it anyway and use “Finish by hand” on the account page.":
        'Das ist die Adresse deines Dashboards plus /saxo/callback, abgeleitet aus der Redirect-URL oben. Nimmt Saxo sie nicht an, trag sie trotzdem ein und nutze „Von Hand abschließen“ auf der Kontoseite.',
    'Kraken key forgotten. The account and its history stay.': 'Kraken-Schlüssel vergessen. Das Konto und seine Historie bleiben.',
    'Kraken key works. Balances: {assets}. Now connect an account from its page.':
        'Der Kraken-Schlüssel funktioniert. Bestände: {assets}. Verbinde jetzt ein Konto von seiner Seite aus.',
    'Kraken needs an API key of your own: kraken.com → Settings → API → Add key. Give it only Query Funds, Query Closed Orders & Trades and Query Ledger Entries — nothing that can trade, withdraw or stake. A key that can only read cannot lose you a coin. Paste the key and the private key here; the private key is shown once when the key is created and is kept 0600 beside the bank key.':
        'Kraken braucht einen eigenen API-Schlüssel: kraken.com → Settings → API → Add key. Gib ihm nur Query Funds, Query Closed Orders & Trades und Query Ledger Entries — nichts, was handeln, auszahlen oder staken kann. Ein Schlüssel, der nur lesen darf, kann dich keinen Coin kosten. Füge hier den Schlüssel und den privaten Schlüssel ein; der private wird beim Anlegen einmal gezeigt und liegt mit Rechten 0600 neben dem Bankschlüssel.',
    'Kraken: link this account to the API key under Settings and pull every trade, deposit and reward.':
        'Kraken: verknüpfe dieses Konto mit dem API-Schlüssel unter Einstellungen und hole jeden Trade, jede Einzahlung und jede Belohnung.',
    'Landed on a dead page after the Saxo login? Paste its address here.':
        'Nach der Saxo-Anmeldung auf einer toten Seite gelandet? Füge ihre Adresse hier ein.',
    'No code and state in that. Paste the whole address, including the ?code=… part.':
        'Darin steckt kein Code und kein State. Füge die ganze Adresse ein, samt dem Teil ?code=…',
    'Open a broker account here and press Connect Saxo.': 'Öffne hier ein Broker-Konto und drücke „Saxo verbinden“.',
    'Paste the AppKey and the AppSecret below.': 'Füge AppKey und AppSecret unten ein.',
    'Private key': 'Privater Schlüssel',
    'Read-only key; syncs with the daily sync.': 'Nur-Lese-Schlüssel; wird mit der täglichen Synchronisierung abgeglichen.',
    'Save Saxo credentials': 'Saxo-Zugangsdaten speichern',
    'Save and check the key': 'Speichern und Schlüssel prüfen',
    'Saxo Bank: log in at Saxo and this account becomes your first Saxo account; any others are created beside it.':
        'Saxo Bank: melde dich bei Saxo an, und dieses Konto wird dein erstes Saxo-Konto; weitere werden daneben angelegt.',
    'Saxo credentials saved. Now connect an account from its page.':
        'Saxo-Zugangsdaten gespeichert. Verbinde jetzt ein Konto von seiner Seite aus.',
    'Saxo forgotten. The accounts and their history stay.': 'Saxo vergessen. Die Konten und ihre Historie bleiben.',
    'Saxo refused the login: {reason}': 'Saxo hat die Anmeldung abgelehnt: {reason}',
    'Saxo sent us back without a code. Paste the address bar on the account page.':
        'Saxo hat uns ohne Code zurückgeschickt. Füge die Adresszeile auf der Kontoseite ein.',
    "Saxo's OpenAPI is OAuth: you register an application of your own in Saxo's developer portal, paste its AppKey and AppSecret here, and connect an account from its page — Saxo's login, then straight back. The tokens Saxo hands out die within the hour, so the app renews them every five minutes while it runs; if it was down for longer, the account page says so and connecting again is one click.":
        'Saxos OpenAPI ist OAuth: du registrierst eine eigene Anwendung in Saxos Entwicklerportal, fügst hier ihren AppKey und AppSecret ein und verbindest ein Konto von seiner Seite aus — Saxos Anmeldung, dann direkt zurück. Die Tokens, die Saxo ausgibt, laufen innerhalb einer Stunde ab, deshalb erneuert die App sie alle fünf Minuten, solange sie läuft; war sie länger aus, sagt es die Kontoseite, und erneut verbinden ist ein Klick.',
    'Simulation': 'Simulation',
    'The Saxo login has lapsed — connect again to resume syncing.': 'Die Saxo-Anmeldung ist abgelaufen — verbinde erneut, um weiter zu synchronisieren.',
    'The login is being kept alive.': 'Die Anmeldung wird am Leben gehalten.',
    'account {id}': 'Konto {id}',
    'connected · client {id}': 'verbunden · Kunde {id}',
    'credentials saved, nothing connected yet': 'Zugangsdaten gespeichert, noch nichts verbunden',
    'key saved': 'Schlüssel gespeichert',
    'login lapsed': 'Anmeldung abgelaufen',
    'not set up': 'nicht eingerichtet',
    'simulation': 'Simulation',

    # ─── Die Zeilen eines Wertpapiers ─────────────────────────────────
    'Amount in {currency}': 'Betrag in {currency}',
    'Click a security to see, and correct, every row behind it.': 'Klicke auf ein Wertpapier, um jede Zeile dahinter zu sehen und zu korrigieren.',
    'Correct': 'Korrigieren',
    'Corrected.': 'Korrigiert.',
    'Every row behind this holding': 'Jede Zeile hinter dieser Position',
    'Held': 'Bestand',
    'If a figure is wrong — a quantity a statement read badly, a price in the wrong currency — correct it here. A correction stays: the next import recognises the row and leaves it alone. Sizes are typed unsigned; the kind supplies the sign. The amount is the whole cash effect as the broker booked it, fees and taxes included.':
        'Stimmt eine Zahl nicht — eine falsch gelesene Stückzahl, ein Kurs in der falschen Währung — korrigiere sie hier. Eine Korrektur bleibt: der nächste Import erkennt die Zeile und lässt sie in Ruhe. Größen werden ohne Vorzeichen eingegeben; die Art liefert das Vorzeichen. Der Betrag ist die gesamte Geldbewegung, wie der Broker sie gebucht hat, samt Gebühren und Steuern.',
    'No transaction carries that security.': 'Keine Transaktion trägt dieses Wertpapier.',
    'Remove this row': 'Diese Zeile entfernen',
    'Save correction': 'Korrektur speichern',
    'Security name': 'Name des Wertpapiers',
    'That transaction does not exist.': 'Diese Transaktion gibt es nicht.',
    'Units': 'Stücke',
    'at {price} on {date}': 'zu {price} am {date}',
    'buys minus sales, fees included': 'Käufe minus Verkäufe, samt Gebühren',
    'corrected {date}': 'korrigiert am {date}',
    'dividends and interest': 'Dividenden und Zinsen',
    'in': 'rein',
    'no market price yet': 'noch kein Marktpreis',
    'out': 'raus',
    'the running sum of every row below': 'die laufende Summe aller Zeilen unten',
    'Collapse all': 'Alle einklappen',
    'Expand all': 'Alle ausklappen',
    'by year and month, newest first': 'nach Jahr und Monat, neueste zuerst',
    'everything': 'alles',
    'fee': 'Gebühr',
    'tax': 'Steuer',
    'the quantity as it ran': 'der Bestand danach',
    '{amount} bought': '{amount} gekauft',
    '{amount} paid out': '{amount} ausgeschüttet',
    '{amount} sold': '{amount} verkauft',
    '{n} row': '{n} Zeile',
    '{n} rows': '{n} Zeilen',

    # ─── Krypto, Kredite, Wertpapierseite ─────────────────────────────
    'Add a loan': 'Kredit hinzufügen',
    'Add the loan': 'Kredit anlegen',
    'Balance after': 'Restschuld danach',
    'Capital': 'Tilgung',
    'Change the terms, or delete': 'Konditionen ändern oder löschen',
    'Connect Kraken under Settings, or add a buy by hand on a broker account with CRYPTO:BTC as the ISIN.':
        'Verbinde Kraken unter Einstellungen, oder trag auf einem Broker-Konto einen Kauf von Hand ein, mit CRYPTO:BTC als ISIN.',
    'Cost basis': 'Einstandswert',
    'Crypto': 'Krypto',
    'Debt': 'Schulden',
    'Every': 'Alle',
    "Every coin you hold, at today's price, with the wallet's value over time. Coins arrive from Kraken or from a row typed in by hand with the code as its ISIN — CRYPTO:BTC — and are priced from Yahoo like everything else.":
        'Jeder Coin, den du hältst, zum heutigen Kurs, mit dem Wert des Wallets über die Zeit. Coins kommen von Kraken oder aus einer von Hand eingetippten Zeile mit dem Code als ISIN — CRYPTO:BTC — und werden wie alles andere über Yahoo bewertet.',
    'Extra': 'Sondertilgung',
    'Extra repayments': 'Sondertilgungen',
    'First instalment': 'Erste Rate',
    'Instalment': 'Rate',
    'Interest': 'Zinsen',
    'Interest over the whole loan': 'Zinsen über die ganze Laufzeit',
    'Latest rows': 'Neueste Zeilen',
    'Loan added. Its balance is on the overview, and its history runs from the first instalment.': 'Kredit hinzugefügt. Sein Saldo steht in der Übersicht, seine Historie läuft ab der ersten Rate.',
    'Loan deleted, with its account.': 'Kredit gelöscht, samt Konto.',
    'Loan or mortgage': 'Kredit oder Hypothek',
    'Loan updated.': 'Kredit aktualisiert.',
    'Loans': 'Kredite',
    'Loans and mortgages': 'Kredite und Hypotheken',
    'Mortgage, house': 'Hypothek, Haus',
    'No coins yet.': 'Noch keine Coins.',
    'No such coin is held.': 'Dieser Coin wird nicht gehalten.',
    'Notes': 'Notizen',
    'Of': 'Von',
    'Owed today': 'Heute geschuldet',
    'Paid off': 'Abbezahlt',
    'Price chart': 'Kursverlauf',
    "Price: Yahoo's daily close of the pair, in the base currency. Wallet: that price times the units held on each day, from the rows below — so a purchase shows as a step up and a sale as a step down.":
        'Kurs: Yahoos Tagesschlusskurs des Paares in der Basiswährung. Wallet: dieser Kurs mal die an jedem Tag gehaltenen Einheiten, aus den Zeilen unten — ein Kauf zeigt sich als Stufe nach oben, ein Verkauf als Stufe nach unten.',
    'Principal': 'Darlehensbetrag',
    'Rate, % per year': 'Zins, % pro Jahr',
    'Save the terms': 'Konditionen speichern',
    'Since the first purchase': 'Seit dem ersten Kauf',
    'Still owed': 'Noch geschuldet',
    'Term, months': 'Laufzeit, Monate',
    "The instalment is the figure on the contract. Leave it blank and give the term instead, and it is worked out as a constant annuity — the usual shape of a mortgage. Interest is rounded to the cent each period, the way a bank does it, so the schedule reproduces the bank's own figures.":
        'Die Rate ist die Zahl aus dem Vertrag. Lass sie leer und gib stattdessen die Laufzeit an, dann wird sie als konstante Annuität berechnet — die übliche Form einer Hypothek. Zinsen werden je Periode auf den Rappen gerundet, wie eine Bank es tut, damit der Plan die Zahlen der Bank reproduziert.',
    'The schedule, instalment by instalment': 'Der Tilgungsplan, Rate für Rate',
    "Type the loan's name exactly to confirm the deletion.": 'Tipp den Namen des Kredits genau ein, um das Löschen zu bestätigen.',
    'Type “{name}” to delete this loan and its account': 'Tipp „{name}“ ein, um diesen Kredit und sein Konto zu löschen',
    'Unrealised gain': 'Unrealisierter Gewinn',
    'Value is the units held times the price of the day — the market price where the app has one, the last price paid before that. Invested is buys minus sales, fees included. Dividends and interest are drawn as their own line, because they are return that never shows in the value.':
        'Wert ist die gehaltene Stückzahl mal der Kurs des Tages — der Marktkurs, wo die App einen hat, davor der zuletzt gezahlte Preis. Investiert sind Käufe minus Verkäufe, samt Gebühren. Dividenden und Zinsen bekommen ihre eigene Linie, weil sie Rendite sind, die im Wert nie auftaucht.',
    'Wallet': 'Wallet',
    "What you owe, computed from the terms rather than typed in: the schedule gives the balance as of today, the overview subtracts it from the net worth, and nothing needs updating month by month. A balance typed in on the loan's account page — from the bank's letter — still wins on the day it is typed.":
        'Was du schuldest, aus den Konditionen berechnet statt eingetippt: der Tilgungsplan liefert die Restschuld per heute, die Übersicht zieht sie vom Nettovermögen ab, und nichts muss Monat für Monat nachgetragen werden. Ein auf der Kontoseite des Kredits eingetippter Saldo — aus dem Brief der Bank — gewinnt trotzdem an dem Tag, an dem er eingetippt wird.',
    'a mortgage, a car loan, a consumer credit — anything paid off in instalments':
        'eine Hypothek, ein Autokredit, ein Konsumkredit — alles, was in Raten abbezahlt wird',
    'all instalments, as a monthly figure': 'alle Raten, auf den Monat gerechnet',
    'avg {price} per {code}': 'Ø {price} je {code}',
    'every row, and corrections': 'jede Zeile, und Korrekturen',
    'loans and mortgages': 'Kredite und Hypotheken',
    'never at this payment': 'bei dieser Rate nie',
    'next {date}': 'nächste {date}',
    'no price history yet — it arrives with the next price refresh':
        'noch keine Kurshistorie — sie kommt mit der nächsten Kursaktualisierung',
    'no price yet — it arrives with the next price refresh': 'noch kein Kurs — er kommt mit der nächsten Kursaktualisierung',
    'no prices for this range': 'keine Kurse für diesen Zeitraum',
    'one per line: date and amount': 'eine je Zeile: Datum und Betrag',
    'or leave blank': 'oder leer lassen',
    'over the range': 'über den Zeitraum',
    'repaid': 'getilgt',
    'the account': 'das Konto',
    'value plus income, against what went in, since {date}': 'Wert plus Erträge gegen das Investierte, seit {date}',
    'wallet value over the range — units bought or sold count too': 'Wallet-Wert über den Zeitraum — gekaufte oder verkaufte Einheiten zählen mit',
    'what it was worth against what went in, day by day': 'was es wert war gegen das, was hineinfloss, Tag für Tag',
    '{code} price': '{code}-Kurs',
    '{interest} of it interest': 'davon {interest} Zinsen',
    '{n} instalment left': 'noch {n} Rate',
    '{n} instalments left': 'noch {n} Raten',
    '{n} loan': '{n} Kredit',
    '{n} loans': '{n} Kredite',
    'Extra repayment {line}: write the date and the amount, like 2027-04-10 20000.':
        'Sondertilgung {line}: schreib Datum und Betrag, etwa 2027-04-10 20000.',
    'Give the payment per period, or the term in months to work it out.':
        'Gib die Rate je Periode an, oder die Laufzeit in Monaten, um sie zu berechnen.',
    'Payments are monthly, quarterly, half-yearly or yearly.': 'Raten sind monatlich, vierteljährlich, halbjährlich oder jährlich.',
    'That loan does not exist.': 'Diesen Kredit gibt es nicht.',
    'That payment does not even cover the interest — the loan would never end.':
        'Diese Rate deckt nicht einmal die Zinsen — der Kredit würde nie enden.',
    'The first payment needs a date, written year-month-day.': 'Die erste Rate braucht ein Datum, geschrieben als Jahr-Monat-Tag.',
    'The loan needs a name.': 'Der Kredit braucht einen Namen.',
    'The principal must be a positive amount.': 'Der Darlehensbetrag muss positiv sein.',
    'The rate is a percentage per year, like 3.2.': 'Der Zins ist ein Prozentsatz pro Jahr, etwa 3.2.',
    'Last twelve months': 'Letzte zwölf Monate',
    "Measured from {date}, day by day, on the prices the app has — backfilled to each security's first trade. A dash means there is nothing to measure yet.":
        'Gemessen ab {date}, Tag für Tag, auf den Kursen, die die App hat — bis zum ersten Trade jedes Wertpapiers nachgeladen. Ein Strich heißt: noch nichts zu messen.',
    'Money-weighted (MWR), a year': 'Geldgewichtet (MWR), pro Jahr',
    'Money-weighted, a year.': 'Geldgewichtet, pro Jahr.',
    'Money-weighted, the internal rate of return: the annual rate your own money earned, timing included — what a savings account would have had to pay.':
        'Geldgewichtet, der interne Zinsfuß: der Jahreszins, den dein eigenes Geld verdient hat, Zeitpunkte eingerechnet — was ein Sparkonto hätte zahlen müssen.',
    'Return': 'Rendite',
    'Return (TWR)': 'Rendite (TWR)',
    'Since the first trade': 'Seit dem ersten Trade',
    'This year': 'Dieses Jahr',
    'Time-weighted (TWR)': 'Zeitgewichtet (TWR)',
    'Time-weighted, since the first purchase; a year when it is longer than one.':
        'Zeitgewichtet, seit dem ersten Kauf; pro Jahr, wenn es länger als eines ist.',
    'Time-weighted: the return of the investment itself, with the timing of your own money taken out — what compares one holding to another.':
        'Zeitgewichtet: die Rendite der Anlage selbst, ohne den Einfluss davon, wann dein Geld kam — das, was eine Position mit einer anderen vergleichbar macht.',
    'Your money (MWR)': 'Dein Geld (MWR)',
    'a year': 'pro Jahr',
    'a year, on what went in and came out': 'pro Jahr, auf das, was hinein- und herausfloss',
    'since {date}': 'seit {date}',
    'the securities as one investment, in the base currency; cash left out on purpose':
        'die Wertpapiere als eine Anlage, in der Basiswährung; Bargeld absichtlich ausgelassen',
    '{pct} % a year': '{pct} % pro Jahr',
    '{pct} % a year, since {date}': '{pct} % pro Jahr, seit {date}',
    # Realised gains, by lots (0.25.0)
    'All time': 'Gesamt',
    'Average cost — every unit costs the average paid': 'Durchschnittskosten — jedes Stück kostet den bezahlten Durchschnitt',
    'Cost of those units': 'Kosten dieser Stücke',
    'Each sale against the cost of the units it sold — the oldest units first under FIFO, every unit at the average paid under average cost. Proceeds and costs as the broker booked them, fees included; a position closed years ago still counts. Kept per currency: a gain in dollars is not a gain in euros without a rate, and this is the figure a tax form asks for.': 'Jeder Verkauf gegen die Kosten der verkauften Stücke — nach FIFO die ältesten zuerst, nach Durchschnittskosten jedes Stück zum bezahlten Durchschnitt. Erlös und Kosten, wie der Broker sie gebucht hat, Gebühren eingeschlossen; eine vor Jahren geschlossene Position zählt weiterhin. Je Währung geführt: ein Gewinn in Dollar ist ohne Kurs kein Gewinn in Euro, und das ist die Zahl, nach der ein Steuerformular fragt.',
    'Each sale against the cost of the units it sold, lots kept per account — a unit bought at one broker is never sold at another. Under FIFO the oldest units go first, which is how Germany taxes; under average cost every unit costs the average paid, the French prix moyen pondéré. Units that arrived without a purchase — a transfer in — cost what their row says, or nothing; units that left without a sale realise nothing.': 'Jeder Verkauf gegen die Kosten der verkauften Stücke, Tranchen je Konto — ein bei einem Broker gekauftes Stück wird nie bei einem anderen verkauft. Nach FIFO gehen die ältesten Stücke zuerst, so besteuert Deutschland; nach Durchschnittskosten kostet jedes Stück den bezahlten Durchschnitt, der französische prix moyen pondéré. Stücke, die ohne Kauf kamen — ein Übertrag herein — kosten, was ihre Zeile sagt, oder nichts; Stücke, die ohne Verkauf gingen, realisieren nichts.',
    'FIFO': 'FIFO',
    'FIFO — the oldest units are sold first': 'FIFO — die ältesten Stücke werden zuerst verkauft',
    'Gain': 'Gewinn',
    'Proceeds': 'Erlös',
    'Realised': 'Realisiert',
    'Realised gains': 'Realisierte Gewinne',
    'Realised gains, by': 'Realisierte Gewinne nach',
    'Units sold': 'Verkaufte Stücke',
    'Unrealised': 'Unrealisiert',
    'Value minus what the units still held cost, by lots; minus net invested when there is no price by lots.': 'Wert minus Kosten der noch gehaltenen Stücke, nach Tranchen; minus Nettoinvestition, wo es keinen Preis nach Tranchen gibt.',
    'What the sales of this security made, by lots.': 'Was die Verkäufe dieses Wertpapiers gebracht haben, nach Tranchen.',
    'Which units a sale sells decides what it made. FIFO is what Germany taxes on and what Portfolio Performance shows; average cost is the French prix moyen pondéré. Switzerland taxes no private capital gain, so a Swiss reader may pick either. Nothing is stored: switching recomputes every figure.': 'Welche Stücke ein Verkauf verkauft, entscheidet, was er gebracht hat. FIFO ist, wonach Deutschland besteuert und was Portfolio Performance zeigt; Durchschnittskosten sind der französische prix moyen pondéré. Die Schweiz besteuert private Kapitalgewinne nicht, ein Schweizer Leser kann also beides wählen. Nichts wird gespeichert: ein Wechsel rechnet jede Zahl neu.',
    'average cost': 'Durchschnittskosten',
    'change': 'ändern',
    'cost {amount}': 'Kosten {amount}',
    'units held cost {amount}, {avg} each': 'gehaltene Stücke kosteten {amount}, {avg} je Stück',
    'what the sales made, by lots': 'was die Verkäufe gebracht haben, nach Tranchen',
    '{amount} realised': '{amount} realisiert',
    '{amount} unrealised': '{amount} unrealisiert',
    '{n} sale': '{n} Verkauf',
    '{n} sales': '{n} Verkäufe',
    # A CSV mapped by hand (0.26.0)
    'A date column and an amount column — or a debit and a credit column — are the least a mapping needs.': 'Eine Datumsspalte und eine Betragsspalte — oder eine Soll- und eine Haben-Spalte — sind das Mindeste, was eine Zuordnung braucht.',
    'A file with one of these headers is imported through its mapping without asking. Forget one and the next such file asks again — the rows already imported stay.': 'Eine Datei mit einer dieser Kopfzeilen wird ohne Nachfrage über ihre Zuordnung importiert. Vergiss eine, und die nächste solche Datei fragt wieder — die bereits importierten Zeilen bleiben.',
    'Amount, signed': 'Betrag, mit Vorzeichen',
    'Any other bank': 'Jede andere Bank',
    'Blank means the ISIN is looked for in the description.': 'Leer heißt: die ISIN wird in der Beschreibung gesucht.',
    "Blank means the account's currency, or the one typed in below.": 'Leer heißt: die Währung des Kontos, oder die unten eingetragene.',
    'Buy, sell, dividend, interest, fee, tax, deposit, withdrawal or transfer — in English, German, French or Spanish. Left blank, the kind is worked out from the row: an ISIN and units is a trade, an ISIN and money in a dividend, plain money a deposit or a withdrawal.': 'Kauf, Verkauf, Dividende, Zinsen, Gebühr, Steuer, Einzahlung, Auszahlung oder Übertrag — auf Englisch, Deutsch, Französisch oder Spanisch. Leer gelassen, wird die Art aus der Zeile abgeleitet: ISIN und Stücke ist ein Trade, ISIN und Geldeingang eine Dividende, bloßes Geld eine Ein- oder Auszahlung.',
    'CSV mappings': 'CSV-Zuordnungen',
    'Call this mapping': 'Diese Zuordnung heißt',
    'Cancel': 'Abbrechen',
    'Columns': 'Spalten',
    'Credit (money in)': 'Haben (Geldeingang)',
    'Currency when the file has no column for it': 'Währung, wenn die Datei keine Spalte dafür hat',
    'Debit (money out)': 'Soll (Geldausgang)',
    "Export the transactions as CSV and drop the file in. If no importer knows it you are asked, once, which column is the date, the amount and so on; the mapping is remembered under the file's header, so the next export from that bank goes straight in.": 'Exportiere die Umsätze als CSV und lege die Datei hier ab. Kennt kein Importer sie, wirst du einmal gefragt, welche Spalte das Datum, der Betrag und so weiter ist; die Zuordnung wird unter der Kopfzeile der Datei gemerkt, der nächste Export dieser Bank geht direkt hinein.',
    'Forget': 'Vergessen',
    'If a kind, a sign or a date looks wrong here it will be wrong in the account: change the mapping and look again before importing. Every row is imported; a row without a readable date is listed and left out.': 'Sieht hier eine Art, ein Vorzeichen oder ein Datum falsch aus, ist es im Konto falsch: ändere die Zuordnung und schau vor dem Import noch einmal. Jede Zeile wird importiert; eine Zeile ohne lesbares Datum wird aufgeführt und ausgelassen.',
    'Map the columns': 'Spalten zuordnen',
    'Mapping forgotten. The next file with that header asks again.': 'Zuordnung vergessen. Die nächste Datei mit dieser Kopfzeile fragt wieder.',
    'Money in positive, money out negative. If the file has one column for each, leave this blank and map the two below.': 'Geldeingang positiv, Geldausgang negativ. Hat die Datei je eine Spalte dafür, lass dies leer und ordne die beiden darunter zu.',
    "No importer here knows this file, and it does not need to: say which column is which, once. The mapping is kept under the file's header, so the next export from the same bank is recognised by itself — like a Degiro file is.": 'Kein Importer hier kennt diese Datei, und das muss er nicht: sag einmal, welche Spalte was ist. Die Zuordnung wird unter der Kopfzeile der Datei behalten, der nächste Export derselben Bank wird von selbst erkannt — wie eine Degiro-Datei.',
    'Not one row could be read through that mapping.': 'Keine einzige Zeile ließ sich über diese Zuordnung lesen.',
    'Nothing readable yet — the date or the amount column is not the right one.': 'Noch nichts lesbar — die Datums- oder die Betragsspalte ist nicht die richtige.',
    'Only when there is no signed amount column.': 'Nur, wenn es keine Betragsspalte mit Vorzeichen gibt.',
    'Read through this mapping': 'Gelesen über diese Zuordnung',
    'Save the mapping and import': 'Zuordnung speichern und importieren',
    'Show me the first rows': 'Zeig mir die ersten Zeilen',
    'Since': 'Seit',
    'That upload has expired — choose the file again.': 'Dieser Upload ist abgelaufen — wähle die Datei noch einmal.',
    'The file': 'Die Datei',
    'The file writes money out as positive — flip every sign': 'Die Datei schreibt Geldausgänge positiv — jedes Vorzeichen umdrehen',
    "The kind gives the sign: a buy's units come in, a sale's go out.": 'Die Art gibt das Vorzeichen: die Stücke eines Kaufs kommen herein, die eines Verkaufs gehen hinaus.',
    'The mapping is saved as {name}; the next file with this header is recognised by itself.': 'Die Zuordnung ist als {name} gespeichert; die nächste Datei mit dieser Kopfzeile wird von selbst erkannt.',
    'What the row says; the counterparty stands in when this is blank.': 'Was die Zeile sagt; die Gegenpartei springt ein, wenn dies leer ist.',
    'Which column is which': 'Welche Spalte was ist',
    'Who paid or was paid.': 'Wer zahlte oder bezahlt wurde.',
    'Written year-month-day, day.month.year or day/month/year. A US month-first date is not guessed.': 'Geschrieben als Jahr-Monat-Tag, Tag.Monat.Jahr oder Tag/Monat/Jahr. Ein US-Datum mit dem Monat zuerst wird nicht geraten.',
    'columns': 'Spalten',
    'saved as {name} — this changes it': 'gespeichert als {name} — dies ändert sie',
    'separated by {delimiter}': 'getrennt durch {delimiter}',
    'the bank, say': 'etwa die Bank',
    'the first rows, as they would be imported': 'die ersten Zeilen, wie sie importiert würden',
    '{n} file layout you mapped yourself': '{n} Dateiformat, das du selbst zugeordnet hast',
    '{n} file layouts you mapped yourself': '{n} Dateiformate, die du selbst zugeordnet hast',
    # CSV export (0.26.0)
    'Every row these filters match, not just the ones shown, in a file a spreadsheet opens right.': 'Jede Zeile, auf die diese Filter passen, nicht nur die gezeigten, in einer Datei, die eine Tabellenkalkulation richtig öffnet.',
    'Export as CSV': 'Als CSV exportieren',
    'This table with every figure on it — price, value, gains, TWR and MWR — in a file a spreadsheet opens right.': 'Diese Tabelle mit jeder Zahl darauf — Kurs, Wert, Gewinne, TWR und MWR — in einer Datei, die eine Tabellenkalkulation richtig öffnet.',
    # Stock splits (0.27.0)
    "A split adds a row per account — the units that appeared, at no cost — so the quantity above is right from that day on. Earlier rows keep the units and prices of their day; the chart values them in today's units, as Yahoo's history is, and a lot keeps its cost, so a later sale realises the same gain it would have in the old units. Write 1:10 for a reverse split.": 'Ein Split fügt je Konto eine Zeile hinzu — die Stücke, die dazukamen, ohne Kosten — damit die Menge oben ab diesem Tag stimmt. Frühere Zeilen behalten die Stücke und Kurse ihres Tages; der Chart bewertet sie in heutigen Stücken, wie Yahoos Historie es tut, und eine Tranche behält ihre Kosten, sodass ein späterer Verkauf denselben Gewinn realisiert wie in alten Stücken. Schreibe 1:10 für einen Reverse-Split.',
    'New for old': 'Neu für alt',
    'Nothing was held on that day — or that split is already recorded.': 'An diesem Tag wurde nichts gehalten — oder dieser Split ist schon erfasst.',
    'Record a split': 'Einen Split erfassen',
    'Record the split': 'Split erfassen',
    'Split recorded on {n} account.': 'Split auf {n} Konto erfasst.',
    'Split recorded on {n} accounts.': 'Split auf {n} Konten erfasst.',
    'split [kind]': 'Split',
    'when the units changed and the money did not': 'wenn sich die Stücke änderten und das Geld nicht',
    'Write the split as new for old, like 44:1 — or 1:10 for a reverse split.': 'Schreibe den Split als neu für alt, etwa 44:1 — oder 1:10 für einen Reverse-Split.',
    # Sidebar navigation and the three stages (0.28.0)
    'A month, in {currency}': 'Pro Monat, in {currency}',
    'A year of returns and a year of savings are of the same order — anywhere from half to twice each other. The crossover, where they are equal, is here. Both levers matter now, and a bad year can undo a year of saving.': 'Ein Jahr Rendite und ein Jahr Sparen sind von derselben Größenordnung — irgendwo zwischen der Hälfte und dem Doppelten voneinander. Der Kreuzungspunkt, an dem sie gleich sind, liegt hier. Jetzt zählen beide Hebel, und ein schlechtes Jahr kann ein Jahr Sparen zunichtemachen.',
    'A year of returns is less than half of what you put in. The monthly amount is the lever; the return barely moves the needle yet. Keep it boring and keep it up.': 'Ein Jahr Rendite ist weniger als die Hälfte dessen, was du einzahlst. Der Monatsbetrag ist der Hebel; die Rendite bewegt die Nadel noch kaum. Halte es langweilig und halte durch.',
    'A year of returns is more than twice what you put in. The pile carries itself; what you add is a rounding error against what the market does. From here on, the risk you carry matters more than the amount you save.': 'Ein Jahr Rendite ist mehr als das Doppelte dessen, was du einzahlst. Der Haufen trägt sich selbst; was du dazulegst, ist ein Rundungsfehler gegen das, was der Markt tut. Von hier an zählt das Risiko, das du trägst, mehr als der Betrag, den du sparst.',
    'As it went': 'Wie es lief',
    'Back to the plan': 'Zurück zum Plan',
    'Close the menu': 'Menü schließen',
    'Collapse the menu': 'Menü einklappen',
    'Compounding carries it': 'Der Zinseszins trägt es',
    'Crossover': 'Kreuzungspunkt',
    'Early on, what you put in is what grows the pile. Later the two pull together. Later still the return on what is there outweighs anything you could add, and the pile carries itself. One ratio tells them apart: what the market does in a year against what you put in in a year.': 'Am Anfang ist das, was du einzahlst, das, was den Haufen wachsen lässt. Später ziehen beide gemeinsam. Noch später überwiegt die Rendite auf das Vorhandene alles, was du dazulegen könntest, und der Haufen trägt sich selbst. Ein Verhältnis unterscheidet sie: was der Markt in einem Jahr tut, gegen das, was du in einem Jahr einzahlst.',
    'End of year': 'Jahresende',
    'Expected return, % a year': 'Erwartete Rendite, % pro Jahr',
    'Investing': 'Anlegen',
    'Market did': 'Der Markt tat',
    'Market did is the value at the end of the year minus the value at the start minus what went in, plus the dividends and interest paid out — everything the money did that you did not do. A single year says little: a bad year in stage 3 looks like stage 1, and that is the point of stage 3.': '„Der Markt tat“ ist der Wert am Jahresende minus dem Wert am Jahresanfang minus dem, was eingezahlt wurde, plus den ausgezahlten Dividenden und Zinsen — alles, was das Geld tat, was du nicht getan hast. Ein einzelnes Jahr sagt wenig: ein schlechtes Jahr in Stufe 3 sieht aus wie Stufe 1, und genau das ist der Punkt von Stufe 3.',
    'Money': 'Geld',
    "Monthly compounding at the rate given, contributions at the end of each month — the same arithmetic as the Forecast. A rate is an assumption, not a promise: the world's stock market has averaged about 7 % a year over a century, with decades on either side of it.": 'Monatliche Verzinsung zum angegebenen Satz, Einzahlungen am Monatsende — dieselbe Rechnung wie die Prognose. Ein Satz ist eine Annahme, kein Versprechen: der Weltaktienmarkt hat über ein Jahrhundert etwa 7 % pro Jahr gebracht, mit Jahrzehnten auf beiden Seiten davon.',
    'Navigation': 'Navigation',
    'No securities records yet.': 'Noch keine Wertpapierdaten.',
    'No securities yet. The stages begin with the first purchase.': 'Noch keine Wertpapiere. Die Stufen beginnen mit dem ersten Kauf.',
    "Nothing goes in a month, so everything the pile does from here is the market's — stage 3 by definition, but of a pile that only grows if the market does.": 'Es geht nichts im Monat hinein, also ist alles, was der Haufen von hier an tut, Sache des Marktes — Stufe 3 per Definition, aber von einem Haufen, der nur wächst, wenn der Markt es tut.',
    'On the plan, year by year': 'Nach Plan, Jahr für Jahr',
    'Open the menu': 'Menü öffnen',
    'Paid out': 'Ausgezahlt',
    'Planning': 'Planen',
    'Put in': 'Eingezahlt',
    'Ratio': 'Verhältnis',
    'Returns equal your savings — the crossover': 'Die Rendite erreicht deine Sparrate — der Kreuzungspunkt',
    'Returns reach half your savings': 'Die Rendite erreicht die Hälfte deiner Sparrate',
    'Returns reach twice your savings — compounding takes over': 'Die Rendite erreicht das Doppelte deiner Sparrate — der Zinseszins übernimmt',
    'Saving and returns pull together': 'Sparen und Rendite ziehen gemeinsam',
    'Saving builds it': 'Das Sparen baut es auf',
    'Stage': 'Stufe',
    'Stage {n}': 'Stufe {n}',
    'Stages': 'Stufen',
    'Start of year': 'Jahresanfang',
    'The last twelve months, {amount} a month actually went into securities.': 'In den letzten zwölf Monaten gingen tatsächlich {amount} im Monat in Wertpapiere.',
    "The plan's figures come from the Forecast page, so they are set once.": 'Die Zahlen des Plans kommen von der Prognose-Seite, damit sie einmal gesetzt sind.',
    'The three stages': 'Die drei Stufen',
    'Tried, not kept.': 'Probiert, nicht gespeichert.',
    'Try it': 'Ausprobieren',
    'Where you stand': 'Wo du stehst',
    'every year the app has records of — what you put in against what the market did': 'jedes Jahr, von dem die App Daten hat — was du eingezahlt hast, gegen das, was der Markt tat',
    'in {year}, at about {value}': 'im Jahr {year}, bei etwa {value}',
    'not within fifty years on these figures': 'nicht innerhalb von fünfzig Jahren mit diesen Zahlen',
    'over {x}×': 'über {x}×',
    'returns under {x}× savings': 'Rendite unter {x}× Sparrate',
    'so far': 'bisher',
    "the wealth at which a year of returns pays a year of savings — twelve months' saving divided by the rate": 'das Vermögen, bei dem ein Jahr Rendite ein Jahr Sparen bezahlt — zwölf Monate Sparen geteilt durch den Satz',
    'what goes in against what the market does, until compounding has been in charge for five years': 'was hineingeht gegen das, was der Markt tut, bis der Zinseszins fünf Jahre lang das Sagen hatte',
    '{a}× to {b}×': '{a}× bis {b}×',
    '{value} in securities at {rate} % expected is {returns} a year; {monthly} a month is {saved} a year — a ratio of {ratio}.': '{value} in Wertpapieren bei {rate} % erwartet sind {returns} im Jahr; {monthly} im Monat sind {saved} im Jahr — ein Verhältnis von {ratio}.',
    # Corrections over the MCP (0.28.1)
    'Nothing to change.': 'Nichts zu ändern.',
    'Transaction {id} does not exist.': 'Transaktion {id} gibt es nicht.',
    '{what} cannot be changed here.': '{what} lässt sich hier nicht ändern.',
    '{what} is not a number.': '{what} ist keine Zahl.',
    # MCP setup notes (0.28.2)
    'For Claude Desktop, which only speaks to local processes, the mcp-remote bridge carries the same URL and header. This goes into claude_desktop_config.json under mcpServers:': 'Für Claude Desktop, das nur mit lokalen Prozessen spricht, trägt die mcp-remote-Brücke dieselbe URL und denselben Header. Das kommt in die claude_desktop_config.json unter mcpServers:',
    "Two things that cost people an afternoon. The URL is the one the browser reaches the dashboard at: behind a reverse proxy that is the https:// address, not the container's http:// one — the address above is what this page was opened at, so it is right if this page was. And --transport http-only matters: without it mcp-remote first tries the older SSE transport, which this endpoint does not speak, and reports a connection failure that is not one.": 'Zwei Dinge, die Leute einen Nachmittag kosten. Die URL ist die, unter der der Browser das Dashboard erreicht: hinter einem Reverse-Proxy ist das die https://-Adresse, nicht die http://-Adresse des Containers — die Adresse oben ist die, unter der diese Seite geöffnet wurde, also stimmt sie, wenn diese Seite stimmt. Und --transport http-only ist wichtig: ohne das probiert mcp-remote zuerst den älteren SSE-Transport, den dieser Endpunkt nicht spricht, und meldet einen Verbindungsfehler, der keiner ist.',
    # A share quoted in another currency (0.28.3)
    'quoted {price} {currency}': 'notiert {price} {currency}',
    "A price quoted in another currency than the shares were paid in is turned into theirs at the day's ECB rate, so the lines are one currency.": 'Ein Kurs in einer anderen Währung als der, in der die Stücke bezahlt wurden, wird zum EZB-Kurs des Tages in diese umgerechnet, damit die Linien eine Währung haben.',
    'fees {fees}, tax {taxes} paid': '{fees} Gebühren, {taxes} Steuern gezahlt',
    # Currency switch on the security page (0.29.0)
    'Show in': 'Anzeigen in',
    'base': 'Basis',
    "every amount at its own day's ECB rate; today's price at today's. The rows below stay as booked, in {currency}.": 'jeder Betrag zum EZB-Kurs seines Tages; der heutige Kurs zum heutigen. Die Zeilen unten bleiben wie gebucht, in {currency}.',
    'paid in': 'bezahlt in',
    'quoted in': 'notiert in',
    # Settings in chapters, rules with terms (0.30.0)
    'Add the rule': 'Regel hinzufügen',
    'Assistants': 'Assistenten',
    'Banks & brokers': 'Banken & Broker',
    'Prices & rates': 'Kurse & Wechselkurse',
    'Rule changed and every rule re-applied, oldest first.': 'Regel geändert und jede Regel neu angewandt, älteste zuerst.',
    'Settings chapters': 'Kapitel der Einstellungen',
    'That rule does not exist.': 'Diese Regel gibt es nicht.',
    'The text is matched anywhere in the description or the counterparty, or in one of them; the amounts are sizes — 20 to 50 catches a payment of 30 whichever way it went, and the direction says which way. Blank means no limit. A rule applies to what is already imported as well as to what arrives next.': 'Der Text wird irgendwo in der Beschreibung oder der Gegenpartei gesucht, oder in einer von beiden; die Beträge sind Größen — 20 bis 50 trifft eine Zahlung von 30, egal in welche Richtung, und die Richtung sagt, in welche. Leer heißt keine Grenze. Eine Regel gilt für das schon Importierte wie für das, was als Nächstes kommt.',
    'When': 'Wenn',
    'and the money is': 'und das Geld ist',
    'contains': 'enthält',
    'from': 'von',
    'in or out': 'ein- oder ausgehend',
    'money in': 'Geldeingang',
    'money out': 'Geldausgang',
    'the counterparty': 'die Gegenpartei',
    'the description': 'die Beschreibung',
    'the text anywhere': 'der Text irgendwo',
    'to': 'bis',
    # Allocation (0.31.0)
    'About to invest, in {currency}': 'Gleich anlegen, in {currency}',
    'Allocation': 'Allokation',
    'Asset class': 'Anlageklasse',
    'Bucket': 'Topf',
    'Buy': 'Kaufen',
    'Buying only: the keys below their target get the amount in proportion to how far below they are.': 'Nur Käufe: die Schlüssel unter ihrem Ziel bekommen den Betrag im Verhältnis dazu, wie weit sie darunter liegen.',
    'By asset class': 'Nach Anlageklasse',
    'By bucket': 'Nach Topf',
    'By region': 'Nach Region',
    "Cash is every account balance; the rest is each holding's class.": 'Bargeld ist jeder Kontostand; der Rest ist die Klasse jeder Position.',
    'Classification saved.': 'Einordnung gespeichert.',
    'Drift': 'Abweichung',
    'Key': 'Schlüssel',
    'Nothing to allocate yet — no holdings and no cash balance.': 'Noch nichts zu verteilen — keine Positionen und kein Kontostand.',
    'Save targets': 'Ziele speichern',
    'Share': 'Anteil',
    'Spread it': 'Verteilen',
    'Target': 'Ziel',
    'Targets saved.': 'Ziele gespeichert.',
    'What each holding is': 'Was jede Position ist',
    'Where a fund invests, or where a share is listed — guessed from the name and the ISIN, yours to correct.': 'Wo ein Fonds anlegt oder wo eine Aktie notiert — aus Name und ISIN geraten, von dir zu korrigieren.',
    'Where the money is by what it is — asset class, region, and buckets of your own — against where you meant it to be. Set a target per key and the page shows the drift; give it the amount you are about to invest and it says how to spread it so the drift shrinks, without selling anything.': 'Wo das Geld ist, nach dem, was es ist — Anlageklasse, Region und eigene Töpfe — gegen das, wo es sein sollte. Setze ein Ziel je Schlüssel, und die Seite zeigt die Abweichung; gib ihr den Betrag, den du gleich anlegst, und sie sagt, wie du ihn verteilst, damit die Abweichung schrumpft, ohne etwas zu verkaufen.',
    'Your own taxonomy — Core and Satellite, Safe and Play, whatever you think in. Nothing is guessed here.': 'Deine eigene Einteilung — Core und Satellite, Sicher und Spiel, was immer du denkst. Hier wird nichts geraten.',
    'a bucket, like Core': 'ein Topf, etwa Core',
    'add a target for…': 'Ziel hinzufügen für…',
    'Asia Pacific [region]': 'Asien-Pazifik',
    'Bonds [class]': 'Anleihen',
    'Cash [class]': 'Bargeld',
    'Commodities [class]': 'Rohstoffe',
    'Crypto [class]': 'Krypto',
    'Emerging markets [region]': 'Schwellenländer',
    'Equity [class]': 'Aktien',
    'Europe [region]': 'Europa',
    'Germany [region]': 'Deutschland',
    'guessed': 'geraten',
    "guessed from the name and Yahoo's type; a guess is marked until you confirm it": 'aus Name und Yahoos Typ geraten; eine Vermutung ist markiert, bis du sie bestätigst',
    'no targets yet': 'noch keine Ziele',
    'North America [region]': 'Nordamerika',
    'Other [class]': 'Sonstiges',
    'Other [region]': 'Sonstige',
    'Real estate [class]': 'Immobilien',
    'Switzerland [region]': 'Schweiz',
    'targets set for {pct} %': 'Ziele gesetzt für {pct} %',
    'unassigned': 'nicht zugeordnet',
    'World [region]': 'Welt',
    '{amount} to target': '{amount} bis zum Ziel',
    '{total} in total — {cash} of it cash.': '{total} insgesamt — davon {cash} Bargeld.',
    'A target is a percentage between 0 and 100.': 'Ein Ziel ist ein Prozentsatz zwischen 0 und 100.',
    'The targets add up to more than a hundred percent.': 'Die Ziele ergeben zusammen mehr als hundert Prozent.',
    # Rules that do more, and tags (0.32.0)
    'A rule can also rename the counterparty — AMZN Mktp DE*2K3 becomes Amazon — set the kind, to mark a transfer between your own accounts, say, and add a tag; those three are applied on every sync, so they win over a correction by hand.': 'Eine Regel kann auch die Gegenpartei umbenennen — aus AMZN Mktp DE*2K3 wird Amazon —, die Art setzen, etwa um einen Übertrag zwischen deinen eigenen Konten zu markieren, und ein Tag hinzufügen; diese drei werden bei jeder Synchronisation angewandt und gewinnen daher gegen eine Korrektur von Hand.',
    'A rule has to do something: file under a category, rename the counterparty, set the kind, or add a tag.': 'Eine Regel muss etwas tun: unter einer Kategorie ablegen, die Gegenpartei umbenennen, die Art setzen oder ein Tag hinzufügen.',
    'Tag': 'Tag',
    'Tags': 'Tags',
    'That pattern is not a valid regular expression: {error}': 'Dieses Muster ist kein gültiger regulärer Ausdruck: {error}',
    'add the tag': 'Tag hinzufügen',
    'is exactly': 'ist genau',
    'leave the category': 'Kategorie belassen',
    'matches the pattern': 'passt auf das Muster',
    'of kind': 'der Art',
    'on account': 'auf Konto',
    'rename the counterparty to': 'Gegenpartei umbenennen in',
    'set the kind to': 'Art setzen auf',
    'starts with': 'beginnt mit',
    'tags, comma-separated': 'Tags, durch Komma getrennt',
    'then file under': 'dann ablegen unter',
    # Benchmark (0.33.0)
    'Against a benchmark': 'Gegen einen Vergleichsindex',
    'Nothing to compare yet.': 'Noch nichts zu vergleichen.',
    "The portfolio line is the time-weighted return: every deposit counts from the day it arrived and every withdrawal stops counting the day it left, so investing bit by bit does not put you behind the index here — what is compared is how the investments did, not when your money came. The return that does feel the timing is the money-weighted one on the Portfolio page. The index is turned into the portfolio's currency at each day's rate; where Yahoo has no clean index in euros an accumulating ETF stands in. Nothing is stored but the index's daily closes.": 'Die Portfoliolinie ist die zeitgewichtete Rendite: jede Einzahlung zählt ab dem Tag, an dem sie kam, jede Auszahlung ab dem Tag, an dem sie ging, nicht mehr — wer nach und nach investiert, liegt hier deshalb nicht hinter dem Index zurück. Verglichen wird, wie die Anlagen liefen, nicht wann das Geld kam. Die Rendite, die das Timing spürt, ist die geldgewichtete auf der Portfolio-Seite. Der Index wird zum Kurs jedes Tages in die Währung des Portfolios umgerechnet; wo Yahoo keinen sauberen Index in Euro hat, steht ein thesaurierender ETF ein. Gespeichert werden nur die Tagesschlusskurse des Index.',
    'Yahoo has no history for {symbol} over this span.': 'Yahoo hat für {symbol} keine Historie über diesen Zeitraum.',
    'You': 'Du',
    'ahead by {pct} points': '{pct} Punkte voraus',
    'another symbol…': 'anderes Symbol…',
    'behind by {pct} points': '{pct} Punkte zurück',
    'time-weighted, both at 100 on the first day': 'zeitgewichtet, beide bei 100 am ersten Tag',
    'you': 'du',
    # Bills and goals (0.34.0)
    'A bill needs a name and at least three characters of text to recognise it by.': 'Eine Rechnung braucht einen Namen und mindestens drei Zeichen Text, an denen sie zu erkennen ist.',
    'A goal needs a name and a positive amount.': 'Ein Ziel braucht einen Namen und einen positiven Betrag.',
    'Active': 'Aktiv',
    'Add a bill': 'Rechnung hinzufügen',
    'Add a goal': 'Ziel hinzufügen',
    'Add the bill': 'Rechnung anlegen',
    'Add the goal': 'Ziel anlegen',
    'An amount by a date, and how it is going. A goal is fed by an account — the holiday account, whose balance is the progress — or by hand, an amount at a time, for a goal that lives inside a bigger account.': 'Ein Betrag bis zu einem Datum, und wie es läuft. Ein Ziel wird von einem Konto gespeist — dem Urlaubskonto, dessen Saldo der Fortschritt ist — oder von Hand, Betrag für Betrag, für ein Ziel, das in einem größeren Konto lebt.',
    'Bill added.': 'Rechnung hinzugefügt.',
    'Bill removed.': 'Rechnung entfernt.',
    'Bill saved.': 'Rechnung gespeichert.',
    'Bills': 'Rechnungen',
    'By': 'Bis',
    'Change the goal': 'Ziel ändern',
    'Due day': 'Fälligkeitstag',
    'Due within a week': 'Fällig innerhalb einer Woche',
    'Every bill': 'Alle Rechnungen',
    'Fed by an account': 'Von einem Konto gespeist',

    # ─── Upcoming ───
    'Upcoming': 'Demnächst',
    "Today's cash, carried forward through what is known to be coming: the bills as declared, the subscriptions the app has found, the salary as the newest payslip had it. Where the balance gets lowest, and the day it would cross zero — before it does, not after.": 'Das Geld von heute, fortgeschrieben durch das, was bekanntermaßen kommt: die Rechnungen wie angelegt, die Abos, die die App gefunden hat, das Gehalt wie auf der neuesten Abrechnung. Wo der Stand am tiefsten ist, und der Tag, an dem er unter null ginge — vorher, nicht hinterher.',
    'Cash today': 'Geld heute',
    '{n} cash account': '{n} Geldkonto',
    '{n} cash accounts': '{n} Geldkonten',
    'newest reading each': 'jeweils der neueste Stand',
    'In {n} days': 'In {n} Tagen',
    '{inflow} in, {outflow} out': '{inflow} rein, {outflow} raus',
    'Lowest point': 'Tiefster Punkt',
    'below zero on {date}, after {name}': 'unter null am {date}, nach {name}',
    'on {date}, after {name}': 'am {date}, nach {name}',
    'starts below zero — an overdraft or a card, not a crossing': 'beginnt unter null — ein Dispo oder eine Karte, kein Unterschreiten',
    'nothing scheduled': 'nichts geplant',
    'Scheduled': 'Geplant',
    '{bills} bills, {subs} subscriptions, {income} pay days': '{bills} Rechnungen, {subs} Abos, {income} Zahltage',
    'No exchange rate for {currencies}; what is in them is left out of the figures above.': 'Kein Wechselkurs für {currencies}; was darin steht, fehlt in den Zahlen oben.',
    'Balance ahead': 'Stand voraus',
    '{n} days': '{n} Tage',
    'Nothing is scheduled in this window. Declare a bill, or import a payslip, and the line starts moving.': 'In diesem Zeitraum ist nichts geplant. Leg eine Rechnung an oder importiere eine Gehaltsabrechnung, und die Linie bewegt sich.',
    'Bills →': 'Rechnungen →',
    'Day by day': 'Tag für Tag',
    'income lands before bills on the same day · ~ an amount carried from what it last cost': 'Einkommen kommt am selben Tag vor den Rechnungen · ~ ein Betrag, übernommen von dem, was es zuletzt gekostet hat',
    'bill': 'Rechnung',
    'subscription': 'Abo',
    'missed — expected today': 'versäumt — heute erwartet',
    'Starting from': 'Ausgangspunkt',
    'No cash account yet.': 'Noch kein Geldkonto.',
    'Loan instalments count only when declared as a bill: the app knows what a loan costs, not which account pays it.': 'Kreditraten zählen nur, wenn sie als Rechnung angelegt sind: die App weiß, was ein Kredit kostet, nicht, welches Konto ihn zahlt.',

    'Fixed costs a month': 'Fixkosten im Monat',
    'Goal added.': 'Ziel hinzugefügt.',
    'Goal removed.': 'Ziel entfernt.',
    'Goal saved.': 'Ziel gespeichert.',
    'Goals': 'Ziele',
    'Missed': 'Versäumt',
    'No goals yet.': 'Noch keine Ziele.',
    'Note it': 'Vermerken',
    'Noted.': 'Vermerkt.',
    'Put towards it': 'Dazulegen',
    'Savings goals': 'Sparziele',
    'Text that identifies it': 'Text, an dem sie zu erkennen ist',
    'That bill does not exist.': 'Diese Rechnung gibt es nicht.',
    'That goal does not exist.': 'Dieses Ziel gibt es nicht.',
    'The text is looked for in the counterparty and the description of money going out; an amount, if given, allows a fifth either way — utilities vary. The due day snaps the next date to the day of the month the bill is usually taken.': 'Der Text wird in Gegenpartei und Beschreibung ausgehender Zahlungen gesucht; ein Betrag, falls angegeben, darf um ein Fünftel abweichen — Nebenkosten schwanken. Der Fälligkeitstag setzt das nächste Datum auf den Monatstag, an dem die Rechnung üblicherweise abgeht.',
    'What is expected to leave the account, and whether it did. A subscription is found; a bill is declared — the rent, the insurance, the electricity — and matched against the rows as they arrive, so this page can say paid, due, or missed.': 'Was das Konto verlassen sollte, und ob es das tat. Ein Abo wird gefunden; eine Rechnung wird angelegt — die Miete, die Versicherung, der Strom — und mit den ankommenden Zeilen abgeglichen, damit diese Seite sagen kann: bezahlt, fällig oder versäumt.',
    'by hand': 'von Hand',
    'by {date}': 'bis {date}',
    'due': 'fällig',
    'fed by hand': 'von Hand gespeist',
    'fed by {account}': 'gespeist von {account}',
    'last {date}, {amount}': 'zuletzt {date}, {amount}',
    'make it a bill': 'als Rechnung anlegen',
    'missed': 'versäumt',
    'more than the {plan} a month of your plan': 'mehr als die {plan} im Monat deines Plans',
    'never seen': 'nie gesehen',
    'next {date}, in {n} days': 'nächste {date}, in {n} Tagen',
    'next: {name}, {date}': 'nächste: {name}, {date}',
    'no payment matched yet': 'noch keine Zahlung zugeordnet',
    'or adopt one the app detected': 'oder eine erkannte übernehmen',
    'paid': 'bezahlt',
    'past due by more than a week, nothing seen since': 'seit mehr als einer Woche überfällig, seither nichts gesehen',
    'reached': 'erreicht',
    'the date has passed': 'das Datum ist vorbei',
    'was due {date}, {n} days ago': 'war fällig {date}, vor {n} Tagen',
    '{amount} a month for {n} months reaches it': '{amount} im Monat über {n} Monate erreicht es',
    '{amount} to go': 'noch {amount}',
    '{n} active bill': '{n} aktive Rechnung',
    '{n} active bills': '{n} aktive Rechnungen',
    '{n} payment seen': '{n} Zahlung gesehen',
    '{n} payments seen': '{n} Zahlungen gesehen',
    # Dividend calendar (0.35.0)
    'By security': 'Nach Wertpapier',
    'By year': 'Nach Jahr',
    'Coming up': 'Demnächst',
    'Dividend calendar': 'Dividendenkalender',
    'Ex-date': 'Ex-Tag',
    'Expected': 'Erwartet',
    'Expected, 12 months': 'Erwartet, 12 Monate',
    'Expected, next twelve months': 'Erwartet, nächste zwölf Monate',
    'Month by month': 'Monat für Monat',
    'Next ex-date': 'Nächster Ex-Tag',
    'No dividends received yet, and nothing expected — either no holding pays out, or Yahoo has not been asked yet.': 'Noch keine Dividenden erhalten und nichts erwartet — entweder schüttet keine Position aus, oder Yahoo wurde noch nicht gefragt.',
    'Per month, expected': 'Pro Monat, erwartet',
    'Per share': 'Je Aktie',
    'Per share, a year': 'Je Aktie, pro Jahr',
    'Received': 'Erhalten',
    'Received, 12 months': 'Erhalten, 12 Monate',
    'Received, all': 'Erhalten, gesamt',
    'Received, last twelve months': 'Erhalten, letzte zwölf Monate',
    "What the holdings paid out, month by month, and what is due in the next twelve: each holding's payments of the last year, times the units held today, a year on. A calendar, not a forecast — it assumes every payer keeps paying what it paid.": 'Was die Positionen ausgeschüttet haben, Monat für Monat, und was in den nächsten zwölf ansteht: die Zahlungen jeder Position im letzten Jahr, mal die heute gehaltenen Stücke, ein Jahr weiter. Ein Kalender, keine Prognose — er nimmt an, dass jeder Zahler weiterzahlt, was er gezahlt hat.',
    "Yield on today's value": 'Rendite auf den heutigen Wert',
    'averaged over the year': 'über das Jahr gemittelt',
    "by ex-date, from last year's dates": 'nach Ex-Tag, aus den Terminen des Vorjahres',
    'from {n} payer': 'von {n} Zahler',
    'from {n} payers': 'von {n} Zahlern',
    'no longer held': 'nicht mehr gehalten',
    'on {value}': 'auf {value}',
    'refresh from Yahoo': 'bei Yahoo aktualisieren',
    'twelve months back, twelve ahead': 'zwölf Monate zurück, zwölf voraus',
    '{n} holding has no distribution data at Yahoo.': '{n} Position hat bei Yahoo keine Ausschüttungsdaten.',
    '{n} holdings have no distribution data at Yahoo.': '{n} Positionen haben bei Yahoo keine Ausschüttungsdaten.',
    '{n} payment': '{n} Zahlung',
    '{n} payments': '{n} Zahlungen',
    '{total} since the records begin': '{total} seit Beginn der Aufzeichnungen',
    # REST API and webhooks (0.36.0)
    "A POST to a URL of yours when something happened: a sync ran or failed, a bill is past due. Home Assistant, n8n, a bot, a script. The body is JSON — event, time, data — and the X-Wealth-Signature header is an HMAC-SHA256 of it with the receiver's secret, so it can tell this app from anyone who found the URL. One attempt, five seconds; a receiver that is down misses that event and the list says so.": 'Ein POST an eine URL von dir, wenn etwas passiert ist: eine Synchronisation lief oder schlug fehl, eine Rechnung ist überfällig. Home Assistant, n8n, ein Bot, ein Skript. Der Body ist JSON — Ereignis, Zeit, Daten — und der Header X-Wealth-Signature ist ein HMAC-SHA256 darüber mit dem Secret des Empfängers, damit er diese App von jedem unterscheiden kann, der die URL gefunden hat. Ein Versuch, fünf Sekunden; ein Empfänger, der nicht erreichbar ist, verpasst dieses Ereignis, und die Liste sagt es.',
    'Add the webhook': 'Webhook hinzufügen',
    'Create a token above and the examples appear here.': 'Erzeuge oben einen Token, dann erscheinen hier die Beispiele.',
    'Events': 'Ereignisse',
    'Every tool the assistant has is also a URL, for a script or an automation that speaks no MCP — the same token, the same answers, one registry. GET lists the tools with their schemas; GET or POST calls one, arguments as query parameters or a JSON body.': 'Jedes Werkzeug, das der Assistent hat, ist auch eine URL — für ein Skript oder eine Automation, die kein MCP spricht: derselbe Token, dieselben Antworten, ein Register. GET listet die Werkzeuge mit ihren Schemas; GET oder POST ruft eines auf, Argumente als Query-Parameter oder JSON-Body.',
    'Last': 'Zuletzt',
    'REST API': 'REST-API',
    'Secret': 'Secret',
    'Send a test event': 'Testereignis senden',
    'Test event sent to {n} webhook.': 'Testereignis an {n} Webhook gesendet.',
    'Test event sent to {n} webhooks.': 'Testereignis an {n} Webhooks gesendet.',
    'Webhook added. Its secret is shown in the list; give it to the receiver to check the signature.': 'Webhook hinzugefügt. Sein Secret steht in der Liste; gib es dem Empfänger, damit er die Signatur prüfen kann.',
    'Webhook removed.': 'Webhook entfernt.',
    'Webhooks': 'Webhooks',
    'the same tools over plain HTTP': 'dieselben Werkzeuge über schlichtes HTTP',
    '{n} receiver': '{n} Empfänger',
    '{n} receivers': '{n} Empfänger',
    # Undoing an import (0.36.1)
    "A named kind decides the sign: a Kauf is money out whichever way the bank wrote the figure, a Dividende money in. Without a kind column the sign is the file's — so if your bank writes a purchase as a positive amount and has no kind column, tick the box below, or the buys come in as money received.": 'Eine benannte Art entscheidet das Vorzeichen: ein Kauf ist Geldausgang, wie auch immer die Bank die Zahl geschrieben hat, eine Dividende Geldeingang. Ohne Art-Spalte gilt das Vorzeichen der Datei — schreibt deine Bank einen Kauf also positiv und hat keine Art-Spalte, setze unten den Haken, sonst kommen die Käufe als Geldeingang herein.',
    'An import can be taken back as one thing — every row it brought, and only those; a row a re-import found already there belongs to the import that first brought it. Wrong signs from a mapping: undo, forget the mapping, import again.': 'Ein Import lässt sich als Ganzes zurücknehmen — jede Zeile, die er gebracht hat, und nur diese; eine Zeile, die ein erneuter Import schon vorfand, gehört zum Import, der sie zuerst brachte. Falsche Vorzeichen aus einer Zuordnung: rückgängig, Zuordnung vergessen, neu importieren.',
    'File': 'Datei',
    'Import undone — {n} row removed.': 'Import rückgängig gemacht — {n} Zeile entfernt.',
    'Import undone — {n} rows removed.': 'Import rückgängig gemacht — {n} Zeilen entfernt.',
    'Recent imports': 'Letzte Importe',
    'Remove every row this import brought?': 'Jede Zeile entfernen, die dieser Import gebracht hat?',
    'Rows brought': 'Zeilen gebracht',
    'Signs.': 'Vorzeichen.',
    'That import is not on record.': 'Dieser Import ist nicht verzeichnet.',
    'That is usually the signs the wrong way round.': 'Das sind meist die Vorzeichen verkehrt herum.',
    'Through': 'Über',
    'Undo': 'Rückgängig',
    'and forget its mapping': 'und seine Zuordnung vergessen',
    'nothing left of it': 'nichts mehr davon übrig',
    'of {n}': 'von {n}',
    '{n} of the first rows look like purchases with money coming in.': '{n} der ersten Zeilen sehen aus wie Käufe mit Geldeingang.',
    '{n} of the first rows looks like a purchase with money coming in.': '{n} der ersten Zeilen sieht aus wie ein Kauf mit Geldeingang.',
    # Retirement plan and goal kinds (0.37.0)
    'A car': 'Ein Auto',
    'A deposit for a place of your own.': 'Eine Anzahlung für ein eigenes Zuhause.',
    'A home': 'Ein Zuhause',
    'A month until then': 'Pro Monat bis dahin',
    'A trip': 'Eine Reise',
    'A wedding': 'Eine Hochzeit',
    'An amount by a date, for whatever it is.': 'Ein Betrag bis zu einem Datum, wofür auch immer.',
    'An emergency fund': 'Ein Notgroschen',
    "An item with no ages runs from retirement to the horizon; clear its name to remove it. Amounts are in today's money and inflate with the rate above; what the pile has to cover is spending minus income, grossed up for the tax on withdrawals.": 'Ein Posten ohne Alter läuft vom Ruhestand bis zum Horizont; lösche seinen Namen, um ihn zu entfernen. Beträge sind in heutigem Geld und steigen mit der Inflationsrate oben; was der Haufen decken muss, sind Ausgaben minus Einkommen, hochgerechnet um die Steuer auf Entnahmen.',
    'Fees, % a year': 'Gebühren, % pro Jahr',
    'Fees, books and courses.': 'Gebühren, Bücher und Kurse.',
    'For': 'Für',
    'Funded': 'Gedeckt',
    "Income in retirement, a month, in today's money": 'Einkommen im Ruhestand, pro Monat, in heutigem Geld',
    'Inflation, %': 'Inflation, %',
    'Lasts to {age}': 'Reicht bis {age}',
    'Life after work — and whether it lasts. A plan of its own.': 'Das Leben nach der Arbeit — und ob es reicht. Ein Plan für sich.',
    'Living, health, travel…': 'Leben, Gesundheit, Reisen…',
    'Nominal': 'Nominal',
    'On these assumptions the pile is {value} when {name} retires at {retire} in {year}, against {required} needed — the money runs out at {age}, {years} years before the horizon.': 'Unter diesen Annahmen ist der Haufen {value}, wenn {name} mit {retire} im Jahr {year} in Rente geht, gegenüber {required} Bedarf — das Geld geht mit {age} aus, {years} Jahre vor dem Horizont.',
    'On these assumptions the pile is {value} when {name} retires at {retire} in {year}, against {required} needed, and {left} is still there at {horizon}.': 'Unter diesen Annahmen ist der Haufen {value}, wenn {name} mit {retire} im Jahr {year} in Rente geht, gegenüber {required} Bedarf, und mit {horizon} sind noch {left} da.',
    'Plan saved.': 'Plan gespeichert.',
    'Plan to age': 'Planen bis Alter',
    'Projected': 'Prognostiziert',
    'Required': 'Erforderlich',
    'Required is, from retirement on, the capital that funds the rest of the plan from that year at the return after retirement; before it, the path that would reach the required capital exactly with the same contributions — the projection above it means ahead of plan. Projections rest on your assumptions; outcomes will differ. Not financial advice.': 'Erforderlich ist ab dem Ruhestand das Kapital, das den Rest des Plans ab diesem Jahr zur Rendite nach dem Ruhestand finanziert; davor der Pfad, der das erforderliche Kapital mit denselben Einzahlungen genau erreichen würde — die Prognose darüber heißt: dem Plan voraus. Projektionen beruhen auf deinen Annahmen; die Wirklichkeit weicht ab. Keine Finanzberatung.',
    'Retired already': 'Schon im Ruhestand',
    'Retirement': 'Ruhestand',
    'Retirement plan': 'Ruhestandsplan',
    'Return after, %': 'Rendite danach, %',
    'Return before, %': 'Rendite davor, %',
    'Runs out at {age}': 'Geht aus mit {age}',
    'Save the plan': 'Plan speichern',
    'Something I am saving for': 'Etwas, wofür ich spare',
    "Spending in retirement, a month, in today's money": 'Ausgaben im Ruhestand, pro Monat, in heutigem Geld',
    'State pension, rent, a part-time job…': 'Gesetzliche Rente, Miete, ein Nebenjob…',
    'Tax on withdrawals, %': 'Steuer auf Entnahmen, %',
    'The day itself.': 'Der Tag selbst.',
    'The next car, paid for rather than financed.': 'Das nächste Auto, bezahlt statt finanziert.',
    'The one you keep putting off.': 'Die, die du immer verschiebst.',
    'The plan': 'Der Plan',
    'Three to six months of spending, untouched.': 'Drei bis sechs Monate Ausgaben, unangetastet.',
    "Today's money": 'Heutiges Geld',
    "Will the money last — and if not, until when. What goes in until you stop, what you will spend each month from then on, what will still come in, a return before and after, fees, inflation, tax on what is withdrawn: walked a year at a time to a horizon. The Forecast page's outlook is the first answer; this is the one with the retirement in it.": 'Reicht das Geld — und wenn nicht, bis wann? Was bis zum Aufhören hineingeht, was du danach jeden Monat ausgibst, was noch hereinkommt, eine Rendite davor und danach, Gebühren, Inflation, Steuer auf Entnahmen: Jahr für Jahr bis zu einem Horizont durchgerechnet. Der Ausblick auf der Prognose-Seite ist die erste Antwort; dies ist die mit dem Ruhestand darin.',
    'Withdrawn': 'Entnommen',
    'age {age}': 'Alter {age}',
    'every rate is yours; the page predicts nothing': 'jeder Satz ist deiner; die Seite prognostiziert nichts',
    'from age': 'ab Alter',
    'from the Forecast plan': 'aus dem Prognose-Plan',
    'from {value} today across {n} accounts, {monthly} a month{plan}': 'ab {value} heute auf {n} Konten, {monthly} im Monat{plan}',
    "in today's money": 'in heutigem Geld',
    'nominal': 'nominal',
    'retired': 'im Ruhestand',
    'saving': 'Sparen',
    'to age': 'bis Alter',
    '{monthly} a month needed at retirement, in the money of that day': '{monthly} im Monat bei Rentenbeginn nötig, im Geld jenes Tages',
    '…growing % a year': '…wachsend % pro Jahr',
    # Moving in from Financial Planner (0.42.0)
    'Move in': 'Umziehen',
    'Move in from Financial Planner': 'Aus Financial Planner umziehen',
    'Moved in': 'Umgezogen',
    'Bring the books of the Financial Planner app over in one go: its accounts, every row of its ledger, its holdings, the daily balances it snapshotted and the price history it kept. Upload its wealth.db, look at what will be written, then confirm — nothing is touched until you do.': 'Hol die Bücher der Financial-Planner-App in einem Zug herüber: ihre Konten, jede Zeile ihres Journals, ihre Positionen, die täglichen Salden ihrer Snapshots und ihre Kurshistorie. Lade ihre wealth.db hoch, sieh dir an, was geschrieben wird, und bestätige — bis dahin wird nichts angefasst.',
    'Accounts created': 'Konten angelegt',
    'Rows': 'Zeilen',
    'Rows already here': 'Zeilen schon vorhanden',
    'Opening positions': 'Eröffnungspositionen',
    'Balance readings': 'Saldenstände',
    'Price days': 'Kurstage',
    'Categories created': 'Kategorien angelegt',
    "Each account's rows are one import, so an account page can undo its share. Refresh the prices and the rates next — Settings › Market — and compare the overview with the old app's.": 'Die Zeilen jedes Kontos sind ein Import, sodass eine Kontoseite ihren Anteil zurücknehmen kann. Aktualisiere als Nächstes Kurse und Wechselkurse — Einstellungen › Markt — und vergleiche die Übersicht mit der alten App.',
    'To the overview': 'Zur Übersicht',
    'What will be written': 'Was geschrieben wird',
    '{rows} rows across {accounts} accounts, {balances} balance readings, {openings} opening positions, {prices} price days, {cats} new categories.': '{rows} Zeilen über {accounts} Konten, {balances} Saldenstände, {openings} Eröffnungspositionen, {prices} Kurstage, {cats} neue Kategorien.',
    '{n} rows are already here and are left alone.': '{n} Zeilen sind schon da und bleiben unberührt.',
    'Old account': 'Altes Konto',
    'From — to': 'Von — bis',
    'Readings': 'Stände',
    'Goes into': 'Kommt in',
    'closed': 'geschlossen',
    'left out — holds nothing': 'bleibt draußen — enthält nichts',
    'a new account': 'ein neues Konto',
    'Where the rows do not add up to what the old app held — a position set from a statement, a sale whose purchase predates the ledger — a row dated before the first one makes up the difference, at the cost the old app carried.': 'Wo die Zeilen nicht ergeben, was die alte App hielt — eine Position aus einem Auszug, ein Verkauf, dessen Kauf vor dem Journal liegt —, gleicht eine Zeile vor der ersten die Differenz aus, zu den Kosten, die die alte App führte.',
    'held {held}, rows give {rows}': 'gehalten {held}, Zeilen ergeben {rows}',
    'New categories:': 'Neue Kategorien:',
    'Worth knowing': 'Gut zu wissen',
    "Rows keep the ids the old app gave them. Where this app's own importer would give the same row a different id, the account remembers how far its ledger is on record, and an export or a sync covering those days leaves them alone — so an export from before today need not be imported again, and a later one is safe.": 'Zeilen behalten die IDs der alten App. Wo der Importer dieser App derselben Zeile eine andere ID gäbe, merkt sich das Konto, bis wohin sein Journal erfasst ist, und ein Export oder Abgleich über diese Tage lässt sie in Ruhe — ein Export von vor heute muss also nicht noch einmal importiert werden, ein späterer ist unbedenklich.',
    'The wealth.db file': 'Die Datei wealth.db',
    'Read it': 'Einlesen',
    "Take a copy of the old app's wealth.db while it is not running, and upload the copy. Nothing is written until you have seen the plan and confirmed it.": 'Kopiere die wealth.db der alten App, während sie nicht läuft, und lade die Kopie hoch. Geschrieben wird nichts, bevor du den Plan gesehen und bestätigt hast.',
    'That upload has expired — start again.': 'Dieser Upload ist abgelaufen — fang noch einmal an.',
    'Moved in: {rows} rows, {balances} balance readings, {accounts} accounts created.': 'Umgezogen: {rows} Zeilen, {balances} Saldenstände, {accounts} Konten angelegt.',
    'That is not a Financial Planner database — it should be the wealth.db file.': 'Das ist keine Financial-Planner-Datenbank — es sollte die Datei wealth.db sein.',
    'Could not read the file: {reason}': 'Die Datei ließ sich nicht lesen: {reason}',
    'Ledger on record until': 'Journal erfasst bis',
    'Rows up to this day were moved in from another app under its own ids. An import or a sync covering those days leaves them alone, so nothing is booked twice. Clear it to let everything in.': 'Zeilen bis zu diesem Tag kamen aus einer anderen App mit deren IDs herüber. Ein Import oder Abgleich über diese Tage lässt sie in Ruhe, damit nichts doppelt gebucht wird. Leer lassen, um alles hereinzulassen.',
    'Worked out for the accounts proposed above, and again for the ones you pick when you confirm: rows already in a chosen account count towards its holding.': 'Berechnet für die oben vorgeschlagenen Konten, und beim Bestätigen noch einmal für die, die du wählst: Zeilen, die in einem gewählten Konto schon liegen, zählen zu dessen Bestand.',
    # Trades on the chart, sold-out list, removing a row (0.43.0)
    'A correction survives the next import: the row is recognised by its id and left as you set it. So does a removal — the id is remembered, and an import or a sync leaves that row out.': 'Eine Korrektur überlebt den nächsten Import: die Zeile wird an ihrer ID erkannt und bleibt, wie du sie gesetzt hast. Ein Entfernen ebenso — die ID wird gemerkt, und ein Import oder Abgleich lässt diese Zeile draußen.',
    "A position sold down to nothing leaves the table above; it is kept here so what it made does not vanish with it. Its rows are on its page, like any other's.": 'Eine ganz verkaufte Position verlässt die Tabelle oben; hier bleibt sie stehen, damit nicht mit ihr verschwindet, was sie gebracht hat. Ihre Zeilen stehen auf ihrer Seite wie bei jeder anderen.',
    'Bought': 'Gekauft',
    'Dividend': 'Dividende',
    'Mark the trades': 'Käufe und Verkäufe markieren',
    'Remove this row? An import or a sync will not bring it back.': 'Diese Zeile entfernen? Ein Import oder Abgleich bringt sie nicht zurück.',
    'Removed. An import or a sync will not bring it back.': 'Entfernt. Ein Import oder Abgleich bringt sie nicht zurück.',
    'Sold': 'Verkauft',
    'Sold out': 'Ganz verkauft',
    'Split': 'Split',
    'That row is not there.': 'Diese Zeile gibt es nicht.',
    'newest first': 'neueste zuerst',
    '{n} securities no longer held': '{n} Wertpapiere nicht mehr gehalten',
    '{n} security no longer held': '{n} Wertpapier nicht mehr gehalten',
    'Without {what}: the whole is {total}.': 'Ohne {what}: das Ganze ist {total}.',
    'incl.': 'inkl.',
    'Cash & banks': 'Cash & Banken',
    'Investments': 'Investments',
    'Pension': 'Vorsorge',
    'Liabilities': 'Verbindlichkeiten',
    'In its currency': 'In seiner Währung',
    'what each is worth, cash and holdings together': 'was jedes wert ist, Cash und Positionen zusammen',
    '{n} row here': '{n} Zeile hier',
    '{n} rows here': '{n} Zeilen hier',
    'Pick the account you already have for the same bank or broker, never a second one:': 'Wähle das Konto, das du für dieselbe Bank oder denselben Broker schon hast, nie ein zweites:',
    "a duplicate account carries the same balance twice. And where the account you pick already has rows from a file of its own, the old app's rows of the same days are booked beside them unless the ids match — they match for Trade Republic, Saxo, Kraken and Crédit Agricole next bank, not for the rest; for those, undo the move's import on that account afterwards, or leave that account out by giving it no rows of its own first.": 'ein doppeltes Konto zählt denselben Saldo zweimal. Und wo das gewählte Konto schon Zeilen aus einer eigenen Datei hat, werden die Zeilen der alten App derselben Tage daneben gebucht, sofern die IDs nicht übereinstimmen — sie stimmen bei Trade Republic, Saxo, Kraken und Crédit Agricole next bank überein, beim Rest nicht; dort den Import des Umzugs auf diesem Konto danach zurücknehmen.',
    'Coins withdrawn go to': 'Abgehobene Coins gehen an',
    'nowhere — they simply leave': 'nirgendwohin — sie gehen einfach',
    'A coin sent to a wallet of your own is still yours. Name the wallet — an account of type Broker, created under Accounts — and a withdrawal becomes a move between the two, at the cost the units carried; a coin sent back in is the same the other way round.': 'Ein Coin, den du an eine eigene Wallet schickst, gehört weiter dir. Benenne die Wallet — ein Konto vom Typ Broker, unter Konten angelegt — und eine Abhebung wird zu einer Umbuchung zwischen beiden, zu den Kosten, die die Einheiten trugen; ein zurückgeschickter Coin ebenso in die andere Richtung.',
    'Saved. A coin withdrawn from now on arrives there, at the cost it carried.': 'Gespeichert. Ein ab jetzt abgehobener Coin kommt dort an, zu den Kosten, die er trug.',
    'Saved. A coin withdrawn simply leaves.': 'Gespeichert. Ein abgehobener Coin geht einfach.',
    'Balance over time': 'Saldo im Zeitverlauf',
    '{n} reading since {date}': '{n} Stand seit {date}',
    '{n} readings since {date}': '{n} Stände seit {date}',
    "Each point is a reading of the balance on that day — from a sync, a statement, the loan's schedule, or typed in above. The newest reading of a day stands for the day; between readings the last one holds.": 'Jeder Punkt ist ein Saldenstand dieses Tages — aus einem Abgleich, einem Auszug, dem Tilgungsplan oder oben eingetippt. Der neueste Stand eines Tages steht für den Tag; zwischen zwei Ständen gilt der letzte.',

    # ─── Updates ─────────────────────────────────────────────────────
    'Update with: pipx upgrade wealth-dashboard — then start it again.': 'Aktualisieren mit: pipx upgrade wealth-dashboard — dann neu starten.',
    'Update the container; your data is in the volume.': 'Aktualisiere den Container; deine Daten liegen im Volume.',
    'Update the add-on in Home Assistant.': 'Aktualisiere das Add-on in Home Assistant.',
    'git pull, then restart.': 'git pull, dann neu starten.',
    'Version {version} is available. {how}': 'Version {version} ist verfügbar. {how}',
    'What is new': 'Was neu ist',
    'Check for a newer version once a day': 'Einmal am Tag nach einer neueren Version sehen',
    'Asks PyPI which version is the newest — one small request for a public page, with nothing about you in it. When there is a newer one, the version in the menu gets a dot and says what to do.': 'Fragt PyPI, welche Version die neueste ist — eine kleine Anfrage nach einer öffentlichen Seite, ohne etwas über dich. Gibt es eine neuere, bekommt die Version im Menü einen Punkt und sagt, was zu tun ist.',

    # ─── Overview tiles ──────────────────────────────────────────────
    'By account': 'Nach Konto',
    'Liquid + investments': 'Liquide + Anlagen',
    'This month': 'Dieser Monat',
    'YTD': 'Seit Jahresbeginn',
    'cash and {n} holding': 'Cash und {n} Position',
    'cash and {n} holdings': 'Cash und {n} Positionen',
    'excludes pension, P2P, property': 'ohne Vorsorge, P2P, Immobilien',
    'last 30 days': 'letzte 30 Tage',
    'no reading to compare with yet': 'noch kein Stand zum Vergleichen',
    'since 1 January': 'seit 1. Januar',

    # ─── Crypto cost basis ───────────────────────────────────────────
    'what the coins still held cost, fees included': 'was die noch gehaltenen Coins gekostet haben, samt Gebühren',
    'net invested {amount}': 'netto investiert {amount}',
    'Saved. {n} earlier moves are booked into the wallet too: {units}. A coin withdrawn from now on arrives there as well, at the cost it carried.': 'Gespeichert. {n} frühere Bewegungen sind nun ebenfalls in der Wallet verbucht: {units}. Ein ab jetzt abgehobener Coin kommt auch dort an, zu den Kosten, die er trug.',

    # ─── Rows between accounts, wallet catch-up ─────────────────────
    "An account that holds two things at once — the rows of a wallet moved in from another app beside the ones an exchange syncs — can hand one source's rows to the account they belong to. The rows keep their ids, so nothing is imported twice afterwards.": 'Ein Konto, das zwei Dinge zugleich ist — die aus einer anderen App übernommenen Zeilen einer Wallet neben denen, die eine Börse abgleicht — kann die Zeilen einer Quelle an das Konto abgeben, zu dem sie gehören. Die Zeilen behalten ihre Ids, danach wird nichts doppelt importiert.',
    'Book earlier moves into the wallet': 'Frühere Bewegungen in die Wallet buchen',
    'For the withdrawals synced before the wallet was named, and the deposits the wallet held the coins for. Nothing is booked twice, so it can be pressed again after rows have moved.': 'Für die Abhebungen, die vor dem Benennen der Wallet abgeglichen wurden, und die Einzahlungen, für die die Wallet die Coins hatte. Nichts wird doppelt gebucht — nach dem Verschieben von Zeilen kann man es also erneut drücken.',
    'From': 'Von',
    'Move': 'Verschieben',
    'To': 'Bis',
    'Move every row from this source to the chosen account?': 'Alle Zeilen dieser Quelle auf das gewählte Konto verschieben?',
    'Name a wallet first.': 'Benenne zuerst eine Wallet.',
    'Nothing to book: every earlier move already has its counterpart.': 'Nichts zu buchen: jede frühere Bewegung hat schon ihr Gegenstück.',
    'Pick another account to move them to.': 'Wähle ein anderes Konto, auf das sie verschoben werden.',
    'Where the rows came from': 'Woher die Zeilen stammen',
    '{n} earlier moves booked into the wallet: {units}.': '{n} frühere Bewegungen in die Wallet gebucht: {units}.',
    '{n} row moved to {name}.': '{n} Zeile nach {name} verschoben.',
    '{n} rows moved to {name}.': '{n} Zeilen nach {name} verschoben.',

    # ─── The loan's own page ─────────────────────────────────────────
    'A loan on its schedule: {balance} still owed, paid off {date}.': 'Ein Kredit auf seinem Tilgungsplan: noch {balance} offen, abbezahlt am {date}.',
    "A {currency} loan on its fixed {rhythm} schedule from the first instalment of {first} until it is paid off. Every figure is computed from the terms — a constant annuity, interest rounded to the cent each period, the way a bank does it — and reproduces the bank's own breakdown.": 'Ein Kredit in {currency} auf seinem festen Tilgungsplan ({rhythm}) von der ersten Rate am {first} bis zur vollständigen Rückzahlung. Jede Zahl ist aus den Konditionen berechnet — eine konstante Annuität, Zinsen je Periode auf den Rappen gerundet, wie es eine Bank tut — und gibt die Aufstellung der Bank wieder.',
    'Amortisation schedule': 'Tilgungsplan',
    'At this rate the loan is overwhelmingly principal from day one — the interest bars are barely visible, which is exactly why the balance falls almost linearly.': 'Bei diesem Zinssatz besteht der Kredit vom ersten Tag an fast nur aus Kapital — die Zinsbalken sind kaum zu sehen, und genau deshalb sinkt der Saldo nahezu linear.',
    'Drawn as': 'Aufgenommen als',
    'Every payment is a fixed annuity: interest, shrinking, against capital repaid.': 'Jede Zahlung ist eine feste Annuität: Zinsen, schrumpfend, gegen getilgtes Kapital.',
    'From {amount} at drawdown to zero on {date}.': 'Von {amount} bei Auszahlung auf null am {date}.',
    'Original loan ({year})': 'Ursprünglicher Kredit ({year})',
    'Outstanding': 'Offen',
    'Outstanding balance over time': 'Offener Saldo im Zeitverlauf',
    "From the reading of {date} the schedule runs from {amount}, the lender's figure, not the sum's — a rate change, a fee, a rounding rule all live in that number. Record a newer balance on the account and it takes over from there.": 'Ab der Ablesung vom {date} läuft der Plan von {amount} aus — der Zahl der Bank, nicht der Summe der Rechnung; eine Zinsänderung, eine Gebühr, eine Rundungsregel stecken alle in dieser einen Zahl. Trag auf dem Konto einen neueren Stand ein, und er übernimmt ab dort.',
    'from the reading of {date}': 'ab der Ablesung vom {date}',
    'From here the schedule runs from the reading of {date}.': 'Ab hier läuft der Plan von der Ablesung vom {date} aus.',
    'reading': 'Ablesung',
    'Outstanding today': 'Heute offen',
    'Payment': 'Zahlung',
    'Payoff date': 'Abbezahlt am',
    'Repaid so far': 'Bisher getilgt',
    'Show amounts in:': 'Beträge anzeigen in:',
    'That account already has its terms.': 'Dieses Konto hat seine Konditionen schon.',
    'That account is not a loan.': 'Dieses Konto ist kein Kredit.',
    'The dashed markers show today and the final payoff. The balance steps down on each payment date; because the interest share shrinks as the balance falls, the curve gently accelerates toward zero.': 'Die gestrichelten Marken zeigen heute und die letzte Rate. Der Saldo fällt an jedem Zahltag eine Stufe; weil der Zinsanteil mit sinkendem Saldo schrumpft, beschleunigt die Kurve sanft gegen null.',
    "The loan is in {currency}; {base} is shown for reference only, at today's rate.": 'Der Kredit läuft in {currency}; {base} wird nur zur Orientierung gezeigt, zum heutigen Kurs.',
    'The loan over time →': 'Der Kredit im Zeitverlauf →',
    'The terms are on record: the balance follows the schedule from here, and its history runs from the first instalment.': 'Die Konditionen sind hinterlegt: der Saldo folgt ab jetzt dem Tilgungsplan, und seine Historie beginnt mit der ersten Rate.',
    'This is a loan. Give it its terms': 'Das ist ein Kredit. Gib ihm seine Konditionen',
    'Today': 'Heute',
    'Total interest over the whole life of the loan: {amount}.': 'Zinsen über die gesamte Laufzeit: {amount}.',
    'Where each instalment goes': 'Wohin jede Rate geht',
    'and its balance follows the schedule, with the page a mortgage deserves': 'und sein Saldo folgt dem Tilgungsplan, mit der Seite, die eine Hypothek verdient',
    "at today's rate of {rate} {base} per {currency}": 'zum heutigen Kurs von {rate} {base} je {currency}',
    'change the terms': 'Konditionen ändern',
    'faded rows are still in the future': 'blasse Zeilen liegen noch in der Zukunft',
    'the loan is denominated in {currency}': 'der Kredit lautet auf {currency}',
    '{amount} @ {rate} on drawdown': '{amount} @ {rate} bei Auszahlung',
    '{currency} (loan currency)': '{currency} (Kreditwährung)',
    "{currency} (today's rate)": '{currency} (heutiger Kurs)',
    '{name} — loan over time': '{name} — Kredit im Zeitverlauf',
    '{n} instalment': '{n} Rate',
    '{n} instalments': '{n} Raten',
    '{n} left': '{n} übrig',
    '{pct} % of the original': '{pct} % des ursprünglichen Betrags',
    '{rate} % per year': '{rate} % pro Jahr',
    'The instalment is the figure on the contract; the rate the nominal one per year. “Drawn as” is what the loan was worth in another currency the day it began — a CHF mortgage taken out as €150 000 — and stays on the page as the reference it is.': 'Die Rate ist der Betrag aus dem Vertrag, der Zinssatz der nominale pro Jahr. „Aufgenommen als“ ist, was der Kredit am ersten Tag in einer anderen Währung wert war — eine CHF-Hypothek, aufgenommen als 150 000 € — und bleibt als Referenz auf der Seite.',

    # ─── Income: payslips ────────────────────────────────────────────
    "A payslip is imported into the account the net salary lands in: open that account, Import a file, choose the PDF — several at once is fine. The sheet is kept whole here, and what the bank never sees is booked onto the account, zero-sum: the tax at source and each side's pension contribution, grossed up and then paid or invested. The net itself is left to the bank.": 'Eine Lohnabrechnung wird in das Konto importiert, auf dem der Nettolohn ankommt: das Konto öffnen, Datei importieren, das PDF wählen — mehrere auf einmal sind in Ordnung. Die Abrechnung bleibt hier vollständig erhalten, und was die Bank nie sieht, wird auf dem Konto verbucht, in Summe null: die Quellensteuer und die Pensionsbeiträge beider Seiten, hochgerechnet und dann gezahlt oder angelegt. Der Nettolohn selbst bleibt der Bank überlassen.',
    'Adding a payslip': 'Eine Lohnabrechnung hinzufügen',
    'Bonus': 'Bonus',
    'Employer pension': 'Pension Arbeitgeber',
    "Employer's cost": 'Kosten des Arbeitgebers',
    'Gross': 'Brutto',
    'Month': 'Monat',
    'Net paid': 'Netto ausbezahlt',
    'Payslip removed, with the rows it had booked.': 'Lohnabrechnung entfernt, samt der Zeilen, die sie verbucht hatte.',
    'Pension, both sides': 'Pension, beide Seiten',
    'Remove this payslip and the rows it booked?': 'Diese Lohnabrechnung und die Zeilen, die sie verbucht hat, entfernen?',
    'Social': 'Sozialabzüge',
    'Tax at source': 'Quellensteuer',
    'That payslip is not there.': 'Diese Lohnabrechnung gibt es nicht.',
    "The household's payslips: gross pay, what was taken at source, the pension on both sides, the bonuses — per earner. The bank saw the net arrive; the sheet saw the rest, and that is what a tax return and a retirement forecast ask for.": 'Die Lohnabrechnungen des Haushalts: Bruttolohn, was an der Quelle abgezogen wurde, die Pension beider Seiten, die Boni — je Verdiener. Die Bank hat den Nettolohn ankommen sehen; die Abrechnung den Rest, und genau den fragen Steuererklärung und Rentenprognose ab.',
    "Two layouts are read: the SAP Lohnabrechnung of a large employer, with wage codes, and the small employer's sheet with Bruttolohn, AHV, ALV, BVG and Nettolohn. The earner's name is taken from the sheet, so one household's payslips sort themselves.": 'Zwei Layouts werden gelesen: die SAP-Lohnabrechnung eines grossen Arbeitgebers mit Lohnarten, und der Zettel des kleinen Arbeitgebers mit Bruttolohn, AHV, ALV, BVG und Nettolohn. Der Name des Verdieners kommt von der Abrechnung, so sortieren sich die Lohnabrechnungen eines Haushalts von selbst.',
    'Your accounts a salary could land in:': 'Deine Konten, auf denen ein Lohn ankommen könnte:',
    'bonus {amount}': 'Bonus {amount}',
    "gross plus the employer's contributions": 'Brutto plus die Beiträge des Arbeitgebers',
    'gross {amount}': 'brutto {amount}',
    'of {gross} gross': 'von {gross} brutto',
    'paid {date}': 'ausbezahlt am {date}',
    'pension inflow {amount}': 'Pensionszufluss {amount}',
    'tax {pct} %': 'Steuer {pct} %',
    'the statutory floor — the sheet prints no employer block': 'das gesetzliche Minimum — die Abrechnung druckt keinen Arbeitgeberblock',
    "{mine} yours, {theirs} the employer's": '{mine} von dir, {theirs} vom Arbeitgeber',
    '{n} month': '{n} Monat',
    '{n} months': '{n} Monate',
    '{pct} % of gross': '{pct} % vom Brutto',

    # ─── The payslip mapper ──────────────────────────────────────────
    'A sheet naming one of these employers and earners is read through its mapping without asking. Forget one and the next such sheet asks again — the payslips already imported stay.': 'Eine Abrechnung, die einen dieser Arbeitgeber und Verdiener nennt, wird ohne Nachfrage über ihre Zuordnung gelesen. Vergiss eine, und die nächste solche Abrechnung fragt wieder — die schon importierten Lohnabrechnungen bleiben.',
    'Allowance': 'Zulage',
    'Amounts': 'Beträge',
    'Base salary': 'Grundgehalt',
    "Both names must appear on the sheet as written here — spaces and case do not matter — because that is how the next sheet is recognised. The earner's name is what the Income page groups by.": 'Beide Namen müssen so auf der Abrechnung stehen, wie sie hier geschrieben sind — Leerzeichen und Gross-/Kleinschreibung spielen keine Rolle —, denn daran wird die nächste Abrechnung erkannt. Nach dem Namen des Verdieners gruppiert die Einkommensseite.',
    'Earner': 'Verdiener',
    'Employer': 'Arbeitgeber',
    "Employer's side": 'Seite des Arbeitgebers',
    'Label': 'Bezeichnung',
    'Lines': 'Zeilen',
    'Map the payslip': 'Die Lohnabrechnung zuordnen',
    'Mapping forgotten. The next sheet from that employer asks again.': 'Zuordnung vergessen. Die nächste Abrechnung dieses Arbeitgebers fragt wieder.',
    'Means': 'Bedeutet',
    "No importer here knows this sheet, and it does not need to: say which line is which, once. The mapping is kept under the sheet's own markers — the employer and the earner — so next month's sheet from the same employer is recognised by itself. The suggestions come from a catalogue of what payslips call things in the languages they are printed in; what is remembered is what you confirm.": 'Kein Importer hier kennt diese Abrechnung, und das muss er auch nicht: sag einmal, welche Zeile was ist. Die Zuordnung wird unter den eigenen Merkmalen der Abrechnung gespeichert — Arbeitgeber und Verdiener —, sodass die Abrechnung des nächsten Monats vom selben Arbeitgeber von selbst erkannt wird. Die Vorschläge kommen aus einem Katalog dessen, wie Lohnabrechnungen die Dinge nennen, in den Sprachen, in denen sie gedruckt werden; gemerkt wird, was du bestätigst.',
    'On a line with several amounts the last one is the amount; the ones before it are the basis and the rate. Deductions are stored as money out whichever way the sheet prints them — a French bulletin prints its retenues positive, an SAP sheet with a trailing minus — because what a line means settles the sign. Several lines may mean the same thing: AHV and ALV are both social deductions. Lines left at — are kept as detail and count for nothing.': 'Auf einer Zeile mit mehreren Beträgen ist der letzte der Betrag; die davor sind Basis und Satz. Abzüge werden als Abgang gespeichert, wie auch immer die Abrechnung sie druckt — ein französischer Bulletin druckt seine Retenues positiv, eine SAP-Abrechnung mit nachgestelltem Minus —, denn was eine Zeile bedeutet, entscheidet über das Vorzeichen. Mehrere Zeilen können dasselbe bedeuten: AHV und ALV sind beide Sozialabzüge. Zeilen, die auf — bleiben, werden als Detail behalten und zählen nichts.',
    'Other deduction': 'Sonstiger Abzug',
    'Paid on': 'Ausbezahlt am',
    'Payslip mappings': 'Zuordnungen von Lohnabrechnungen',
    "Pension, the employer's": 'Pension, Arbeitgeber',
    'Pension, yours': 'Pension, deine',
    'Rate': 'Satz',
    'Read it through this mapping': 'Über diese Zuordnung lesen',
    'Read through the mapping': 'Über die Zuordnung gelesen',
    'Social deduction': 'Sozialabzug',
    "Social, the employer's": 'Sozialbeitrag, Arbeitgeber',
    'Taken at source': 'An der Quelle abgezogen',
    'The gross and the net paid, the employer and the earner — that is the least a payslip mapping needs.': 'Brutto und Netto ausbezahlt, Arbeitgeber und Verdiener — weniger braucht eine Zuordnung nicht.',
    'The lines': 'Die Zeilen',
    'The mapping is saved as {name}; the next sheet from this employer is recognised by itself.': 'Die Zuordnung ist als {name} gespeichert; die nächste Abrechnung dieses Arbeitgebers wird von selbst erkannt.',
    'The month': 'Der Monat',
    'This is not a payslip': 'Das ist keine Lohnabrechnung',
    'Whose sheet': 'Wessen Abrechnung',
    'amounts written the {fmt} way': 'Beträge geschrieben wie {fmt}',
    'base {amount}': 'Grund {amount}',
    'gross less every deduction is the net: the mapping caught every line': 'Brutto minus alle Abzüge ergibt das Netto: die Zuordnung hat jede Zeile erfasst',
    'gross less the deductions differs from the net by {gap} — a line is missing or mapped twice': 'Brutto minus Abzüge weicht um {gap} vom Netto ab — eine Zeile fehlt oder ist doppelt zugeordnet',
    "nothing mapped as the employer's — the sheet may print none": 'nichts als Arbeitgeberseite zugeordnet — die Abrechnung druckt vielleicht keine',
    'pension {pension} · social {social}': 'Pension {pension} · Sozial {social}',
    'tax {tax} · social {social} · pension {pension} · other {other}': 'Steuer {tax} · Sozial {social} · Pension {pension} · Sonstiges {other}',
    '{n} line with an amount, a month or a date': '{n} Zeile mit einem Betrag, einem Monat oder einem Datum',
    '{n} lines with an amount, a month or a date': '{n} Zeilen mit einem Betrag, einem Monat oder einem Datum',
    '{n} payslip layout you mapped yourself': '{n} selbst zugeordnetes Lohnabrechnungs-Layout',
    '{n} payslip layouts you mapped yourself': '{n} selbst zugeordnete Lohnabrechnungs-Layouts',
    "Row id":
        "Zeilen-ID",
    "The bank's own id for the row, if it has one. With it, a row whose text changed between two exports is still the same row.":
        "Die eigene ID der Bank für die Zeile, falls es eine gibt. Mit ihr bleibt eine Zeile, deren Text sich zwischen zwei Exporten geändert hat, dieselbe Zeile.",
}
