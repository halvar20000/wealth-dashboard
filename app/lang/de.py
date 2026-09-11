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
    "across {n} account with a balance": "über {n} Konto mit Saldo",
    "across {n} accounts with a balance": "über {n} Konten mit Saldo",
    "{n} holding": "{n} Bestand",
    "{n} holdings": "{n} Bestände",
    "{n} with no price": "{n} ohne Preis",
    "imported and synced": "importiert und abgeglichen",
    "Largest holding": "Größter Bestand",
    "import a broker export to see holdings":
        "Broker-Export importieren, um Bestände zu sehen",
    "Cash vs securities": "Barmittel gegen Wertpapiere",
    "Where it is": "Wo es liegt",
    "by account": "nach Konto",
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
    "CSV file": "CSV-Datei",
    "Drop in a CSV your broker exported. The file is recognised by its "
    "columns, so there is nothing to choose — and re-importing a period you "
    "already loaded is harmless, because every row carries an id.":
        "Wirf eine CSV hinein, die dein Broker exportiert hat. Die Datei wird "
        "an ihren Spalten erkannt, du musst also nichts auswählen — und einen "
        "Zeitraum noch einmal zu importieren schadet nicht, weil jede Zeile "
        "eine ID trägt.",
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
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exportiere einen Zeitraum, der sich mit dem bereits importierten "
        "überschneidet. Überschneidung kostet nichts, eine Lücke kostet dich "
        "Transaktionen.",
    "Choose a CSV file first.": "Wähle zuerst eine CSV-Datei.",
    "That file is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "Diese Datei ist größer als {mb} MB. Ein Transaktionsexport ist viel "
        "kleiner — ist es die richtige Datei?",
    "That file's columns do not match any importer here. Supported: {list}":
        "Die Spalten dieser Datei passen zu keinem Importer hier. "
        "Unterstützt: {list}",
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
    "When the text contains": "Wenn der Text enthält",
    "Added": "Hinzugefügt",
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
    "broker and it is not.":
        "Eine Kategorie wird intern über den Namen erkannt, mit dem sie "
        "angelegt wurde — Umbenennen oder Umfärben sortiert deshalb nie eine "
        "Transaktion um: die Lebensmittel, die du schon sortiert hast, bleiben "
        "sortiert, wie immer du sie nennst. „Zählt als“ entscheidet, ob "
        "Cashflow und Budget das Geld als ausgegeben behandeln oder nur als "
        "verschoben: das Mittagessen ist eine Ausgabe, 500 € zu deinem Broker "
        "sind es nicht.",
    "Colour for {name}": "Farbe für {name}",
    "Name of {name}": "Name von {name}",
    "Cash Flow knows this one by name — it is never counted as spending.":
        "Der Cashflow kennt diese hier beim Namen — sie zählt nie als Ausgabe.",
    "not spending": "keine Ausgabe",
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
    "Removed.": "Entfernt.",
    "Only a transaction typed in by hand can be removed. An imported one would only come back with the next import.":
        "Nur eine von Hand eingetragene Transaktion lässt sich entfernen. Eine importierte käme mit dem nächsten Import einfach wieder.",
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
}
