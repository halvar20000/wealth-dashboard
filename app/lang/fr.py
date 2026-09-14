"""Français.

On tutoie : cette application tourne sur ton propre serveur, pour toi.
Les nombres et les dates viennent de i18n.FORMATS, pas d'ici.

Une entrée manquante n'est pas une erreur — l'anglais d'origine s'affiche
alors à sa place. Voir app/i18n.py.
"""

STRINGS: dict[str, str] = {

    # ─── Navigation et cadre ─────────────────────────────────────────
    "Overview": "Vue d'ensemble",
    "Portfolio": "Portefeuille",
    "Cash Flow": "Flux de trésorerie",
    "Budget": "Budget",
    "Subscriptions": "Abonnements",
    "Transactions": "Transactions",
    "Categorize": "Catégoriser",
    "Accounts": "Comptes",
    "Settings": "Réglages",
    "Sign in": "Se connecter",
    "Sign out": "Se déconnecter",
    "Runs on your machine. Your data never leaves it, except to your own bank.":
        "Tourne sur ta machine. Tes données n'en sortent jamais, sauf vers ta "
        "propre banque.",
    "Not found": "Introuvable",
    "No such page.": "Cette page n'existe pas.",
    "Back to accounts": "Retour aux comptes",

    # ─── Connexion et installation ───────────────────────────────────
    "Username": "Identifiant",
    "Password": "Mot de passe",
    "Password again": "Mot de passe, à nouveau",
    "at least 8 characters": "au moins 8 caractères",
    "Create account": "Créer le compte",
    "Create your account": "Crée ton accès",
    "This is the only account on this installation, and it lives in your own "
    "database. Nothing is sent anywhere, so there is no email to confirm and "
    "no way for anyone to reset it for you — choose a password you will keep.":
        "C'est le seul accès à cette installation, et il vit dans ta propre "
        "base de données. Rien n'est envoyé nulle part : pas d'e-mail à "
        "confirmer, et personne pour réinitialiser ton mot de passe à ta "
        "place — choisis-en un que tu garderas.",
    "Too many attempts. Wait a few minutes.":
        "Trop de tentatives. Attends quelques minutes.",
    "Wrong username or password.": "Identifiant ou mot de passe incorrect.",
    "A username is required.": "Il faut un identifiant.",
    "The password must be at least {n} characters.":
        "Le mot de passe doit faire au moins {n} caractères.",
    "The username “{name}” is already taken.":
        "L'identifiant « {name} » est déjà pris.",

    # ─── Comptes ─────────────────────────────────────────────────────
    "Account": "Compte",
    "Add an account": "Ajouter un compte",
    "New account": "Nouveau compte",
    "Name": "Nom",
    "Type": "Type",
    "Currency": "Devise",
    "Source": "Source",
    "Balance": "Solde",
    "As of": "Au",
    "Edit": "Modifier",
    "Delete": "Supprimer",
    "Save": "Enregistrer",
    "connected": "connecté",
    "imported file": "fichier importé",
    "nothing yet": "rien pour l'instant",
    "An account exists whether or not a bank is ever connected to it. Name it "
    "something you will recognise — you can connect it to your bank on the "
    "next screen, or type the balance in yourself and never connect it at all.":
        "Un compte existe qu'une banque y soit reliée ou non. Donne-lui un nom "
        "que tu reconnaîtras — tu pourras le connecter à ta banque à l'écran "
        "suivant, ou saisir le solde toi-même et ne jamais le connecter.",
    "The account needs a name.": "Le compte a besoin d'un nom.",
    "Account updated.": "Compte mis à jour.",
    "That account does not exist.": "Ce compte n'existe pas.",
    "Bank account": "Compte courant",
    "Savings": "Épargne",
    "Credit card": "Carte de crédit",
    "Pension fund": "Caisse de pension",
    "P2P lending": "Prêts P2P",
    "Property": "Immobilier",
    "Other assets": "Autres actifs",
    "pension, P2P, property": "pension, P2P, immobilier",
    "Broker": "Courtier",
    "Other": "Autre",

    # ─── Supprimer un compte ─────────────────────────────────────────
    "Delete this account": "Supprimer ce compte",
    "This account holds nothing — no transactions, no balance readings, no "
    "bank connection. There is nothing to lose by removing it.":
        "Ce compte ne contient rien — aucune transaction, aucun relevé de "
        "solde, aucune connexion bancaire. Le supprimer ne fait rien perdre.",
    "This cannot be undone.": "C'est irréversible.",
    "Deleting {name} also removes {what}.":
        "Supprimer {name} enlève aussi {what}.",
    "Deleting {name} removes everything on it.":
        "Supprimer {name} enlève tout ce qu'il contient.",
    "{n} transaction": "{n} transaction",
    "{n} transactions": "{n} transactions",
    "{n} balance reading": "{n} relevé de solde",
    "{n} balance readings": "{n} relevés de solde",
    "{a} and {b}": "{a} et {b}",
    "The bank connection goes with it. The consent itself stays alive at your "
    "bank until it expires or you revoke it there, and re-connecting means "
    "going through your bank's login again.":
        "La connexion bancaire part avec. Le consentement lui-même reste actif "
        "chez ta banque jusqu'à son expiration ou jusqu'à ce que tu le "
        "révoques là-bas, et te reconnecter veut dire repasser par la page de "
        "connexion de ta banque.",
    "There is no undo and no copy of this anywhere else.":
        "Il n'y a pas d'annulation, et aucune copie ailleurs.",
    "Type {name} to confirm": "Tape {name} pour confirmer",
    "Delete permanently": "Supprimer définitivement",
    "Type the account name exactly to confirm the deletion.":
        "Tape le nom du compte exactement pour confirmer la suppression.",
    "Deleted {name}.": "{name} supprimé.",

    # ─── Page du compte ──────────────────────────────────────────────
    "Bank connection": "Connexion bancaire",
    "reported": "déclaré",
    "as of {date}": "au {date}",
    "nothing reported yet": "rien de déclaré pour l'instant",
    "Last sync: {when}.": "Dernière synchro : {when}.",
    "never": "jamais",
    "Consent valid for {n} more day.":
        "Consentement valable encore {n} jour.",
    "Consent valid for {n} more days.":
        "Consentement valable encore {n} jours.",
    "Consent expires in {n} day — reconnect soon.":
        "Le consentement expire dans {n} jour — reconnecte-toi bientôt.",
    "Consent expires in {n} days — reconnect soon.":
        "Le consentement expire dans {n} jours — reconnecte-toi bientôt.",
    "Consent expired. Reconnect to resume syncing.":
        "Consentement expiré. Reconnecte-toi pour reprendre la synchro.",
    "Sync now": "Synchroniser",
    "Reconnect or change bank": "Reconnecter ou changer de banque",
    "Add a transaction": "Ajouter une transaction",
    "for this holding — the ISIN and the name are filled in":
        "pour cette position — l'ISIN et le nom sont déjà remplis",
    "Price per unit": "Prix unitaire",
    "In the account's currency. A dividend, a fee or a tax added here is filed "
    "against this holding, so it shows among its rows and in its income above. "
    "Sizes are typed unsigned — whether the money went in or out follows from "
    "what happened.":
        "Dans la devise du compte. Un dividende, des frais ou un impôt ajoutés ici "
        "sont rattachés à cette position : ils figurent parmi ses lignes et dans "
        "ses revenus ci-dessus. Les montants se saisissent sans signe — que l'argent "
        "soit entré ou sorti découle de ce qui s'est passé.",
    "There is no broker account to add it to — create one under Accounts first.":
        "Aucun compte-titres où l'ajouter — crée-en un d'abord sous Comptes.",
    "Pick which account it happened in.": "Choisis le compte où cela s'est passé.",
    "optional — given, the row is filed against that holding":
        "facultatif — s'il est donné, la ligne est rattachée à cette position",
    "Disconnect": "Déconnecter",
    "The account and its history stay; the syncing ends.":
        "Le compte et son historique restent ; la synchro s'arrête.",
    "Disconnect this account from the bank? The account, its balances and its "
    "history stay; only the connection goes.":
        "Déconnecter ce compte de la banque ? Le compte, ses soldes et son "
        "historique restent ; seule la connexion disparaît.",
    "Disconnected {name} from its bank. The history stays.":
        "{name} déconnecté de sa banque. L'historique reste.",
    "This account is not connected to a bank. Connecting it pulls the balance "
    "and the transaction history straight from the bank, with your own Enable "
    "Banking credentials.":
        "Ce compte n'est relié à aucune banque. Une fois connecté, il récupère "
        "le solde et l'historique directement auprès de la banque, avec tes "
        "propres identifiants Enable Banking.",
    "Connect a bank": "Connecter une banque",
    "Started one already and landed on a dead page? {paste}.":
        "Déjà commencé et atterri sur une page morte ? {paste}.",
    "Paste the code here": "Colle le code ici",
    "Add your Enable Banking Application ID and private key in {settings} first.":
        "Renseigne d'abord ton Application ID et ta clé privée Enable Banking "
        "dans {settings}.",
    "Import a broker CSV": "Importer un CSV de courtier",
    "Edit or delete": "Modifier ou supprimer",
    "Recent transactions": "Transactions récentes",
    "No transactions yet.": "Aucune transaction pour l'instant.",
    "Showing the {shown} most recent of {total}.":
        "Les {shown} plus récentes sur {total}.",
    "That account is not connected to a bank.":
        "Ce compte n'est relié à aucune banque.",
    "Sync failed: {reason}": "Échec de la synchro : {reason}",
    "Imported {n} new transaction.": "{n} nouvelle transaction importée.",
    "Imported {n} new transactions.": "{n} nouvelles transactions importées.",

    # ─── Positions ───────────────────────────────────────────────────
    "Holdings": "Positions",
    "Security": "Titre",
    "ISIN": "ISIN",
    "Quantity": "Quantité",
    "Net invested": "Investi net",
    "Last traded at": "Dernier prix traité",
    "At that price": "À ce prix",
    "Value": "Valeur",
    "Difference": "Écart",
    "Where": "Où",
    "largest first": "les plus grosses d'abord",
    "{n} trade": "{n} ordre",
    "{n} trades": "{n} ordres",
    "last {date}": "dernier le {date}",
    "last trade {date}": "dernier ordre le {date}",
    "export starts too late": "l'export commence trop tard",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export a period that starts when you "
    "opened the account and re-import — overlap is free.":
        "Une quantité négative n'est pas une position vendeuse : c'est une "
        "vente dont l'achat est plus ancien que le fichier importé. Exporte "
        "une période qui commence à l'ouverture du compte et réimporte — le "
        "recouvrement ne coûte rien.",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export from the account opening and "
    "re-import — overlap is free.":
        "Une quantité négative n'est pas une position vendeuse : c'est une "
        "vente dont l'achat est plus ancien que le fichier importé. Exporte "
        "depuis l'ouverture du compte et réimporte — le recouvrement ne coûte "
        "rien.",
    "Quantities are the running sum of every buy and sell, imported or typed in. The last "
    "two columns use the price of your most recent trade, not a market price — "
    "this app has no price feed yet, and a stale number presented as a "
    "valuation is worse than none.":
        "Les quantités sont la somme courante de tous les achats et ventes, "
        "importés ou saisis à la main. Les deux dernières colonnes utilisent le prix de ton ordre "
        "le plus récent, pas un prix de marché — cette application n'a pas "
        "encore de source de cours, et un chiffre périmé présenté comme une "
        "valorisation est pire que rien.",
    "{n} position": "{n} position",
    "{n} positions": "{n} positions",
    "across all accounts": "sur tous les comptes",
    "what you put in, {currency} positions":
        "ce que tu as mis, positions en {currency}",
    "No holdings yet.": "Aucune position pour l'instant.",
    "Import a broker export from an account and the positions are computed "
    "from its trades.":
        "Importe un export de courtier dans un compte, et les positions sont "
        "calculées à partir de ses ordres.",

    # ─── Vue d'ensemble ──────────────────────────────────────────────
    "Net worth": "Patrimoine net",
    "Cash": "Liquidités",
    "Securities": "Titres",
    "{n} connected to a bank": "{n} relié à une banque",
    "across {n} account with a balance": "sur {n} compte avec un solde",
    "across {n} accounts with a balance": "sur {n} comptes avec un solde",
    "{n} holding": "{n} position",
    "{n} holdings": "{n} positions",
    "{n} with no price": "{n} sans prix",
    "imported and synced": "importées et synchronisées",
    "Largest holding": "Plus grosse position",
    "import a broker export to see holdings":
        "importe un export de courtier pour voir les positions",
    "Cash vs securities": "Liquidités contre titres",
    "Where it is": "Où c'est",
    "by account": "par compte",
    "no price": "pas de prix",
    "Latest activity": "Dernière activité",
    "Date": "Date",
    "Description": "Libellé",
    "Kind": "Type",
    "Amount": "Montant",
    "Counterparty": "Contrepartie",
    "Nothing here yet.": "Rien ici pour l'instant.",
    "Add an account, then connect it to your bank or import a broker export. "
    "Both routes end in the same place.":
        "Ajoute un compte, puis connecte-le à ta banque ou importe un export "
        "de courtier. Les deux chemins mènent au même endroit.",

    # ─── Import ──────────────────────────────────────────────────────
    "Import": "Importer",
    "Import into {name}": "Importer dans {name}",
    "Rows read": "Lignes lues",
    "Imported": "Importées",
    "Already had": "Déjà présentes",
    "No cash movement, skipped": "Aucun mouvement d'espèces, ignorées",
    "{n} line could not be read.": "{n} ligne n'a pas pu être lue.",
    "{n} lines could not be read.": "{n} lignes n'ont pas pu être lues.",
    "Everything else was imported. These are listed rather than counted so you "
    "can see whether they matter:":
        "Tout le reste a été importé. Elles sont listées plutôt que comptées "
        "pour que tu voies si elles comptent :",
    "…and {n} more.": "…et {n} de plus.",
    "See the account": "Voir le compte",
    "Where to get the file": "Où trouver le fichier",
    "Inbox → Account statement → choose the period → export CSV. That is the "
    "cash ledger: deposits, trades, dividends and fees. Set the start date "
    "back to when you opened the account and you get the whole history in one "
    "go.":
        "Boîte de réception → Relevé de compte → choisir la période → exporter "
        "en CSV. C'est le journal des espèces : dépôts, ordres, dividendes et "
        "frais. Remets la date de début à l'ouverture du compte et tu obtiens "
        "tout l'historique d'un coup.",
    "Profile → Transactions → export.": "Profil → Transactions → exporter.",
    "Drop in a CSV your broker exported, or the statement PDFs from your bank's "
    "mailbox — as many as you like, or a ZIP of them. Each file is recognised by "
    "what is in it, so there is nothing to choose — and re-importing what you "
    "already loaded is harmless, because every row carries an id.":
        "Dépose un CSV exporté par ton courtier, ou les PDF d'avis d'opéré de la "
        "messagerie de ta banque — autant que tu veux, ou un ZIP. Chaque fichier "
        "est reconnu à son contenu, il n'y a donc rien à choisir — et réimporter "
        "ce que tu as déjà chargé est sans risque, car chaque ligne porte un "
        "identifiant.",
    "CSV or PDF files":
        "Fichiers CSV ou PDF",
    "Files":
        "Fichiers",
    "Postfach → filter by the Depot → download the Wertpapierabrechnungen as PDF "
    "and drop them all in here at once. The Depot's CSV says only what money "
    "moved; the PDFs say how many units, at what price, with what fee. Orders, "
    "fund purchases, dividends, interest, the Vorabpauschale and the half-year "
    "Sparplan overview are all read. A Storno is skipped and named.":
        "Postfach → filtrer sur le Depot → télécharger les Wertpapierabrechnungen en "
        "PDF et les déposer toutes ici d'un coup. Le CSV du Depot dit seulement "
        "quel argent a bougé ; les PDF disent combien de parts, à quel prix, avec "
        "quels frais. Ordres, achats de fonds, dividendes, intérêts, la "
        "Vorabpauschale et le récapitulatif semestriel du Sparplan sont tous lus. "
        "Un Storno est ignoré et nommé.",
    "Open the account or the Visa card → Umsätze → choose the period → "
    "CSV-Export. Girokonto, Tagesgeld and Visa all work, and so do files from "
    "the old portal. Pending (vorgemerkt) rows are left out until they are "
    "booked.":
        "Ouvre le compte ou la carte Visa → Umsätze → choisis la période → "
        "CSV-Export. Girokonto, Tagesgeld et Visa fonctionnent tous, comme les "
        "fichiers de l'ancien portail. Les lignes en attente (vorgemerkt) sont "
        "laissées de côté jusqu'à ce qu'elles soient comptabilisées.",
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exporte une période qui recouvre ce que tu as déjà importé. Le "
        "recouvrement ne coûte rien ; un trou te coûte des transactions.",
    "Choose a CSV or PDF file first.": "Choisis d'abord un fichier CSV ou PDF.",
    "{name} is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "{name} dépasse {mb} Mo. Un export de transactions est bien plus "
        "petit — est-ce le bon fichier ?",
    "None of those files match an importer here. Supported: {list}":
        "Aucun de ces fichiers ne correspond à un importateur ici. "
        "Pris en charge : {list}",
    "not recognised, left out": "non reconnu, laissé de côté",
    "{importer}: {new} new, {had} already had.":
        "{importer} : {new} nouvelles, {had} déjà présentes.",

    # ─── Connecter une banque ────────────────────────────────────────
    "You will be sent to your bank's own login page. This app never sees your "
    "banking password — the bank gives it read-only access to the account you "
    "tick, for {days} days at a time, and you can revoke it at your bank.":
        "Tu vas être envoyé sur la page de connexion de ta banque. Cette "
        "application ne voit jamais ton mot de passe bancaire — la banque lui "
        "donne un accès en lecture seule au compte que tu coches, pour {days} "
        "jours à la fois, et tu peux le révoquer chez ta banque.",
    "If your bank leaves you on a page that will not load, that is expected "
    "with an https-only redirect URL — {by_hand}.":
        "Si ta banque te laisse sur une page qui ne charge pas, c'est normal "
        "avec une URL de redirection en https seulement — {by_hand}.",
    "finish the connection by hand": "termine la connexion à la main",
    "Country": "Pays",
    "Search": "Recherche",
    "Show banks": "Afficher les banques",
    "{n} bank in {country}": "{n} banque en {country}",
    "{n} banks in {country}": "{n} banques en {country}",
    "including {n} sandbox": "dont {n} bac à sable",
    "including {n} sandboxes": "dont {n} bacs à sable",
    "Connect a sandbox bank first.":
        "Connecte d'abord une banque bac à sable.",
    "It walks the identical flow — redirect, consent, session, balances, "
    "transactions — with the provider's own test credentials, and creates no "
    "consent at a real bank. If your redirect URL is registered wrongly, you "
    "find out here instead of by spending an authorisation you rely on.":
        "Elle suit exactement le même parcours — redirection, consentement, "
        "session, soldes, transactions — avec les identifiants de test du "
        "fournisseur, et ne crée aucun consentement dans une vraie banque. Si "
        "ton URL de redirection est mal enregistrée, tu l'apprends ici plutôt "
        "qu'en dépensant une autorisation dont tu as besoin.",
    "Bank": "Banque",
    "Connect": "Connecter",
    "sandbox": "bac à sable",
    "No banks matched. Try a shorter search, or check the country code.":
        "Aucune banque trouvée. Essaie une recherche plus courte, ou vérifie "
        "le code pays.",
    "Connected: {accounts}": "Connecté : {accounts}",
    "Connected, but the first sync failed: {reason}":
        "Connecté, mais la première synchro a échoué : {reason}",
    "Imported {n} transaction.": "{n} transaction importée.",
    "Imported {n} transactions.": "{n} transactions importées.",
    "The bank refused the authorisation: {reason}":
        "La banque a refusé l'autorisation : {reason}",
    "The bank sent us back without an authorisation code.":
        "La banque nous a renvoyés sans code d'autorisation.",

    # ─── Terminer la connexion à la main ─────────────────────────────
    "Finish connecting": "Terminer la connexion",
    "Finish connecting by hand": "Terminer la connexion à la main",
    "Some providers only accept an https redirect URL, which an app on your "
    "own network cannot have. Then the bank sends you to a page that does not "
    "exist — and that is fine. The authorisation code is in the address bar of "
    "that dead page. Copy the whole address and paste it here.":
        "Certains fournisseurs n'acceptent qu'une URL de redirection en https, "
        "ce qu'une application sur ton propre réseau ne peut pas avoir. La "
        "banque t'envoie alors sur une page qui n'existe pas — et c'est très "
        "bien. Le code d'autorisation est dans la barre d'adresse de cette "
        "page morte. Copie l'adresse entière et colle-la ici.",
    "Waiting to be finished": "En attente d'être terminée",
    "Started": "Commencée",
    "One connection is in progress, so pasting just the code works too — but "
    "the whole URL is easier and always right.":
        "Une seule connexion est en cours : coller juste le code marche aussi "
        "— mais l'URL entière est plus simple et toujours juste.",
    "The address the bank sent you to":
        "L'adresse sur laquelle la banque t'a envoyé",
    "Nothing is fetched from this address — it is only read for the code and "
    "state it carries.":
        "Rien n'est récupéré depuis cette adresse — elle est seulement lue "
        "pour le code et le state qu'elle porte.",
    "No connection is waiting to be finished.":
        "Aucune connexion n'attend d'être terminée.",
    "Start one from an account, then come back here if the bank leaves you on "
    "a page that will not load.":
        "Lances-en une depuis un compte, puis reviens ici si la banque te "
        "laisse sur une page qui ne charge pas.",
    "No authorisation code in that. Paste the whole URL from the address bar, "
    "including the ?code=… part.":
        "Pas de code d'autorisation là-dedans. Colle l'URL entière depuis la "
        "barre d'adresse, y compris la partie ?code=….",
    "That code could belong to any of several connections in progress. Paste "
    "the full URL, which carries the state.":
        "Ce code pourrait appartenir à plusieurs connexions en cours. Colle "
        "l'URL complète, qui porte le state.",

    # ─── Flux de trésorerie ──────────────────────────────────────────
    "Money in against money out, per month. Internal transfers are excluded — "
    "moving money between your own accounts is not income and not spending, "
    "and counting it would inflate both by the same amount. Investment is "
    "separated for the same reason: a month you invested €3,000 is not a month "
    "you overspent.":
        "L'argent qui entre contre l'argent qui sort, par mois. Les virements "
        "internes sont exclus — déplacer de l'argent entre tes propres comptes "
        "n'est ni un revenu ni une dépense, et le compter gonflerait les deux "
        "du même montant. L'investissement est séparé pour la même raison : un "
        "mois où tu as placé 3 000 € n'est pas un mois où tu as trop dépensé.",
    "Income": "Revenus",
    "Spending": "Dépenses",
    "Invested": "Investi",
    "Kept": "Restant",
    "a month": "par mois",
    "a month, over {n} month": "par mois, sur {n} mois",
    "a month, over {n} months": "par mois, sur {n} mois",
    "over the period": "sur la période",
    "income less spending": "revenus moins dépenses",
    "By month": "Par mois",
    "Where it goes": "Où ça part",
    "By category": "Par catégorie",
    "per month on average": "par mois en moyenne",
    "Category": "Catégorie",
    "Per month": "Par mois",
    "Total": "Total",
    "No transactions in the base currency yet.":
        "Aucune transaction dans la devise de référence pour l'instant.",
    "Connect a bank or import a statement, then categorise on the {page} page "
    "— until things have categories, this page has nothing to add up.":
        "Connecte une banque ou importe un relevé, puis catégorise sur la page "
        "{page} — tant que rien n'a de catégorie, cette page n'a rien à "
        "additionner.",

    # ─── Budget ──────────────────────────────────────────────────────
    "Measured against how far through the month you are, not against the whole "
    "month. Halfway through, everyone is under budget — the useful question is "
    "whether you are ahead of the pace.":
        "Mesuré par rapport à l'avancement du mois, pas au mois entier. À "
        "mi-parcours, tout le monde est sous son budget — la vraie question "
        "est de savoir si tu vas plus vite que l'allure.",
    "No budgets set yet — fill some in below.":
        "Aucun budget défini — remplis-en un ci-dessous.",
    "Monthly budget per category": "Budget mensuel par catégorie",
    "leave blank for no budget": "laisse vide pour aucun budget",
    "Spent": "Dépensé",
    "Typical": "Habituel",
    "Pace": "Allure",
    "over budget": "hors budget",
    "ahead of pace": "en avance sur l'allure",
    "on track": "dans les clous",
    "{pct}% used": "{pct}% utilisé",
    "Save budget": "Enregistrer le budget",
    "Budget saved.": "Budget enregistré.",

    # ─── Abonnements ─────────────────────────────────────────────────
    "Charges that repeat on a recognisable rhythm, at a stable amount, at "
    "least three times. Deliberately cautious: the failure that matters is not "
    "missing one, it is calling three unrelated payments a €400 commitment — "
    "which makes the whole page untrustworthy.":
        "Des prélèvements qui reviennent à un rythme reconnaissable, pour un "
        "montant stable, au moins trois fois. Volontairement prudent : "
        "l'erreur qui compte n'est pas d'en rater un, c'est d'appeler trois "
        "paiements sans rapport un engagement de 400 € — ce qui rend toute la "
        "page suspecte.",
    "Per year": "Par an",
    "{n} active": "{n} actif",
    "at the current rhythm": "au rythme actuel",
    "Possibly recurring": "Peut-être récurrent",
    "repeated, but not on a clear rhythm":
        "se répète, mais sans rythme clair",
    "Recurring": "Récurrent",
    "What": "Quoi",
    "Rhythm": "Rythme",
    "Each": "Chaque",
    "Paid so far": "Payé à ce jour",
    "Last seen": "Vu le",
    "{n} payment since {date}": "{n} paiement depuis le {date}",
    "{n} payments since {date}": "{n} paiements depuis le {date}",
    "probably ended": "probablement terminé",
    "{n} day ago": "il y a {n} jour",
    "{n} days ago": "il y a {n} jours",
    "Nothing detected yet.": "Rien de détecté pour l'instant.",
    "A charge has to appear at least three times, on a recognisable rhythm, at "
    "a stable amount. Import a longer history and it will find more.":
        "Un prélèvement doit apparaître au moins trois fois, à un rythme "
        "reconnaissable et pour un montant stable. Importe un historique plus "
        "long et il en trouvera davantage.",
    "repeats, but the rhythm or the amount wanders":
        "se répète, mais le rythme ou le montant dérive",
    "Times": "Fois",

    # ─── Transactions et catégorisation ──────────────────────────────
    "merchant or text": "commerçant ou texte",
    "any": "toutes",
    "Filter": "Filtrer",
    "Clear": "Effacer",
    "net {amount}": "net {amount}",
    "showing the {n} most recent": "les {n} plus récentes",
    "Nothing matches those filters.": "Rien ne correspond à ces filtres.",
    "Correcting a transaction here can leave a rule behind. A rule applies to "
    "what is already imported as well as to what arrives next — otherwise the "
    "same shop has to be fixed every month for a year before it stops asking.":
        "Corriger une transaction ici peut laisser une règle derrière. Une "
        "règle s'applique à ce qui est déjà importé comme à ce qui arrivera "
        "ensuite — sinon il faut corriger le même magasin tous les mois "
        "pendant un an avant qu'il arrête de demander.",
    "Waiting": "En attente",
    "largest amounts first": "les plus gros montants d'abord",
    "Rules": "Règles",
    "applied to past and future": "appliquées au passé et au futur",
    "Quick start": "Démarrage rapide",
    "Categorise what is obvious": "Catégoriser ce qui est évident",
    "fees, interest, dividends, known merchants":
        "frais, intérêts, dividendes, commerçants connus",
    "The queue": "La file",
    "clear “remember as” to correct this one row without making a rule":
        "vide « retenir comme » pour corriger cette seule ligne, sans créer de règle",
    "Remember as": "Retenir comme",
    "text to match, optional": "texte à reconnaître, facultatif",
    "Apply": "Appliquer",
    "Nothing waiting.": "Rien en attente.",
    "Every transaction has a category. Import more, or adjust one from the "
    "{page} page.":
        "Chaque transaction a une catégorie. Importes-en d'autres, ou modifie "
        "une catégorie depuis la page {page}.",
    "newest wins where two match":
        "en cas d'égalité, la plus récente l'emporte",
    "Rule saved — {n} transaction matched “{pattern}”.":
        "Règle enregistrée — {n} transaction correspondait à « {pattern} ».",
    "Rule saved — {n} transactions matched “{pattern}”.":
        "Règle enregistrée — {n} transactions correspondaient à « {pattern} ».",
    "Changing a category here also makes a rule from the merchant, and applies it to every transaction that matches. To correct a single row without a rule, use the Categorize page and clear “remember as”.":
        "Changer une catégorie ici crée aussi une règle à partir du commerçant, appliquée à toutes les transactions qui correspondent. Pour corriger une seule ligne sans règle, passe par la page Catégoriser et vide « retenir comme ».",
    "A rule needs at least three characters to match on — anything shorter will catch transactions you did not mean.":
        "Une règle a besoin d’au moins trois caractères à reconnaître — plus court, elle attraperait des transactions que tu ne visais pas.",
    "{n} transaction categorised from what the importer already knew.":
        "{n} transaction catégorisée à partir de ce que l'importateur savait "
        "déjà.",
    "{n} transactions categorised from what the importer already knew.":
        "{n} transactions catégorisées à partir de ce que l'importateur savait "
        "déjà.",
    "Rule deleted and the remaining rules re-applied.":
        "Règle supprimée et les règles restantes réappliquées.",

    # ─── Réglages ────────────────────────────────────────────────────
    "General": "Général",
    "Language": "Langue",
    "Follow my browser": "Suivre mon navigateur",
    "Changes the language of the app, and with it how numbers and dates are "
    "written. It does not touch what your bank sent: a transaction described "
    "in German stays in German.":
        "Change la langue de l'application, et avec elle l'écriture des "
        "nombres et des dates. Cela ne touche pas à ce que ta banque a envoyé "
        "— une transaction libellée en allemand reste en allemand.",
    "Base currency": "Devise de référence",
    "Redirect URL": "URL de redirection",
    "Where your bank sends you back after you authorise. This exact string "
    "must also be registered in the Enable Banking Control Panel — if the two "
    "differ by so much as a trailing slash, the bank refuses the handover and "
    "the error it shows names nothing useful.":
        "L'endroit où ta banque te renvoie après ton autorisation. Cette "
        "chaîne exacte doit aussi être enregistrée dans le Control Panel "
        "d'Enable Banking — si les deux diffèrent ne serait-ce que d'une barre "
        "oblique finale, la banque refuse le passage, et l'erreur affichée ne "
        "nomme rien d'utile.",
    "Settings saved.": "Réglages enregistrés.",

    # ─── Catégories ──────────────────────────────────────────────────
    "Categories": "Catégories",
    "renaming one keeps every transaction it holds":
        "renommer garde toutes les transactions qu'elle contient",
    "A category is identified internally by the name it was created with, so "
    "renaming or recolouring one never re-files a transaction — the Groceries "
    "you already sorted stay sorted whatever you call them. What “counts as” "
    "decides is whether Cash Flow and Budget treat the money as spent, or "
    "merely as moved: pay for lunch and it is spending, move €500 to your "
    "broker and it is not — or as income, which Cash Flow adds up by "
    "category, so a salary, a rent coming in and interest each show as "
    "their own.":
        "Une catégorie est identifiée en interne par le nom sous lequel elle a "
        "été créée : la renommer ou la recolorier ne reclasse donc jamais une "
        "transaction — les Courses que tu as déjà triées restent triées, quel "
        "que soit le nom que tu leur donnes. Ce que « compte comme » décide, "
        "c'est si Flux de trésorerie et Budget traitent l'argent comme dépensé "
        "ou simplement déplacé : payer le déjeuner est une dépense, virer "
        "500 € vers ton courtier n'en est pas une — ou comme un revenu, que "
        "Flux de trésorerie additionne par catégorie, pour que salaire, "
        "loyers perçus et intérêts apparaissent chacun pour soi.",
    "Colour for {name}": "Couleur de {name}",
    "Name of {name}": "Nom de {name}",
    "Cash Flow knows this one by name — it is never counted as spending.":
        "Flux de trésorerie connaît celle-ci par son nom — elle n'est jamais "
        "comptée comme une dépense.",
    "not spending": "pas une dépense",
    "income": "revenu",
    "Salary": "Salaire",
    "Rental income": "Revenus locatifs",
    "Interest & dividends": "Intérêts & dividendes",
    "Where it comes from": "D'où ça vient",
    "What {name} counts as": "Ce que {name} compte comme",
    "Not spending": "Pas une dépense",
    "{n} rule": "{n} règle",
    "{n} rules": "{n} règles",
    "Delete this category? {n} transaction moves to Uncategorised.":
        "Supprimer cette catégorie ? {n} transaction passe dans Non catégorisé.",
    "Delete this category? {n} transactions move to Uncategorised.":
        "Supprimer cette catégorie ? {n} transactions passent dans Non "
        "catégorisé.",
    "{n} rule is deleted with it.": "{n} règle est supprimée avec elle.",
    "{n} rules are deleted with it.": "{n} règles sont supprimées avec elle.",
    "The app tells spending from moving your own money by this category, so it "
    "cannot be removed.":
        "C'est à cette catégorie que l'application distingue dépenser de "
        "déplacer ton propre argent : elle ne peut pas être supprimée.",
    "needed": "nécessaire",
    "Colour": "Couleur",
    "New category": "Nouvelle catégorie",
    "Childcare": "Garde d'enfants",
    "Counts as": "Compte comme",
    "Add category": "Ajouter la catégorie",
    "Category “{name}” added.": "Catégorie « {name} » ajoutée.",
    "Category updated.": "Catégorie mise à jour.",
    "“{name}” deleted.": "« {name} » supprimée.",
    "“{name}” deleted — {n} transaction moved to Uncategorised, and its rules "
    "were removed with it.":
        "« {name} » supprimée — {n} transaction est passée dans Non catégorisé, "
        "et ses règles sont parties avec.",
    "“{name}” deleted — {n} transactions moved to Uncategorised, and its rules "
    "were removed with it.":
        "« {name} » supprimée — {n} transactions sont passées dans Non "
        "catégorisé, et ses règles sont parties avec.",
    "A category needs a name.": "Une catégorie a besoin d'un nom.",
    "Keep the name under 40 characters — it has to fit in a table cell and a "
    "chart legend.":
        "Garde le nom sous 40 caractères — il doit tenir dans une cellule de "
        "tableau et dans une légende de graphique.",
    "{given} is not a colour like #a78bfa.":
        "{given} n'est pas une couleur comme #a78bfa.",
    "That": "Ça",
    "That name has no letters or digits in it, and the name is what the "
    "internal id is made from.":
        "Ce nom ne contient ni lettre ni chiffre, et c'est du nom qu'est "
        "fabriqué l'identifiant interne.",
    "“{name}” already uses that name.": "« {name} » porte déjà ce nom.",
    "There is already a category called “{name}”.":
        "Il existe déjà une catégorie appelée « {name} ».",

    # ─── Enable Banking ──────────────────────────────────────────────
    "Your own application, your own key. Nothing here is shared with anyone — "
    "the key never leaves this machine and is only used to sign your own "
    "requests.":
        "Ta propre application, ta propre clé. Rien ici n'est partagé avec "
        "qui que ce soit — la clé ne quitte jamais cette machine et ne sert "
        "qu'à signer tes propres requêtes.",
    "Create an application": "Crée une application",
    "at {control_panel}.": "sur {control_panel}.",
    "Environment Production — restricted mode is a state of a production app, "
    "not a separate environment.":
        "Environnement Production — le « restricted mode » est un état d'une "
        "application de production, pas un environnement à part.",
    "Find your Application ID.": "Trouve ton Application ID.",
    "It is on the application's page in the Control Panel — a UUID like "
    "{example}.":
        "Il est sur la page de l'application dans le Control Panel — un UUID "
        "comme {example}.",
    "If you chose Generate for the key, it is also the filename of the file "
    "your browser downloaded: {file}.":
        "Si tu as choisi « Generate » pour la clé, c'est aussi le nom du "
        "fichier téléchargé par ton navigateur : {file}.",
    "Find your private key.": "Trouve ta clé privée.",
    "Which file depends on the choice you made when creating the application:":
        "Quel fichier dépend du choix que tu as fait en créant l'application :",
    "You chose “Generate”": "Tu as choisi « Generate »",
    "the usual case": "le cas habituel",
    "your browser downloaded {file}.":
        "ton navigateur a téléchargé {file}.",
    "That file is the private key.": "Ce fichier est la clé privée.",
    "Open it in a text editor and copy everything, including the BEGIN and END "
    "lines. There is nothing to generate yourself.":
        "Ouvre-le dans un éditeur de texte et copie tout, y compris les lignes "
        "BEGIN et END. Tu n'as rien à générer toi-même.",
    "You provided your own key": "Tu as fourni ta propre clé",
    "then you already ran the commands below and want {file}.":
        "alors tu as déjà lancé les commandes ci-dessous et il te faut {file}.",
    "Do not paste enablebanking_public.pem, or anything you uploaded to Enable "
    "Banking. That is the public half; they have it, you need the other one.":
        "Ne colle pas enablebanking_public.pem, ni quoi que ce soit que tu as "
        "envoyé à Enable Banking. C'est la moitié publique ; eux l'ont, toi il "
        "te faut l'autre.",
    "Paste both below": "Colle les deux ci-dessous",
    "and save. The app checks them immediately against Enable Banking and "
    "tells you what it finds.":
        "et enregistre. L'application les vérifie aussitôt auprès d'Enable "
        "Banking et te dit ce qu'elle trouve.",
    "Only if you want to supply your own key instead of letting the Control "
    "Panel generate one":
        "Seulement si tu veux fournir ta propre clé au lieu de laisser le "
        "Control Panel en générer une",
    "Upload enablebanking_public.pem in the Control Panel; paste "
    "enablebanking_private.key below.":
        "Envoie enablebanking_public.pem dans le Control Panel ; colle "
        "enablebanking_private.key ci-dessous.",
    "The key is stored at {path} with permissions 0600.":
        "La clé est stockée dans {path} avec les permissions 0600.",
    "Your credentials live inside the data folder, so every backup of that "
    "folder carries your bank key with it. Set WD_SECRETS_DIR to a folder "
    "outside it if that matters to you.":
        "Tes identifiants vivent dans le dossier de données : chaque "
        "sauvegarde de ce dossier emporte donc ta clé bancaire. Pointe "
        "WD_SECRETS_DIR vers un dossier en dehors si cela compte pour toi.",
    "Application ID": "Application ID",
    "stored — paste again to replace":
        "enregistré — recolle pour remplacer",
    "Private key (PEM)": "Clé privée (PEM)",
    "Save credentials": "Enregistrer les identifiants",
    "Credentials saved. Checking them with Enable Banking…":
        "Identifiants enregistrés. Vérification auprès d'Enable Banking…",
    "Credentials are stored. {test} — this makes one live call to Enable "
    "Banking.":
        "Les identifiants sont enregistrés. {test} — cela fait un vrai appel à "
        "Enable Banking.",
    "Test them": "Teste-les",
    "Working. Registered redirect URLs:":
        "Ça marche. URL de redirection enregistrées :",
    "none": "aucune",

    # ─── Taux de change ──────────────────────────────────────────────
    "Exchange rates": "Taux de change",
    "European Central Bank": "Banque centrale européenne",
    "The ECB publishes euro reference rates every business day — free, "
    "without a key and without an account. They are what converts an amount in "
    "another currency into your base currency, and every total built from them "
    "names the day they were published.":
        "La BCE publie des taux de référence de l'euro chaque jour ouvré — "
        "gratuitement, sans clé et sans compte. Ce sont eux qui convertissent "
        "un montant dans une autre devise vers ta devise de référence, et "
        "chaque total qui en découle nomme le jour de leur publication.",
    "{n} currency, published {date}.": "{n} devise, publiée le {date}.",
    "{n} currencies, published {date}.": "{n} devises, publiées le {date}.",
    "The ECB does not publish at the weekend, so this is Friday's — which is "
    "also the newest rate there is.":
        "La BCE ne publie pas le week-end : c'est donc le taux de vendredi — "
        "et c'est aussi le plus récent qui existe.",
    "No rates yet, so amounts in another currency are reported beside your "
    "totals rather than inside them. Fetching them needs this machine to reach "
    "the internet once.":
        "Pas encore de taux : les montants dans une autre devise sont donc "
        "affichés à côté de tes totaux plutôt que dedans. Les récupérer "
        "demande que cette machine atteigne internet une fois.",
    "Update rates now": "Mettre les taux à jour",
    "Also updated on start-up, at most once a day, in the background. Nothing "
    "waits on it: a page renders whether or not the rates arrived.":
        "Mis à jour aussi au démarrage, au plus une fois par jour, en arrière-"
        "plan. Rien ne l'attend : une page s'affiche que les taux soient "
        "arrivés ou non.",
    "{n} exchange rate fetched, published {date}.":
        "{n} taux de change récupéré, publié le {date}.",
    "{n} exchange rates fetched, published {date}.":
        "{n} taux de change récupérés, publiés le {date}.",
    "Includes {amounts}, converted at the ECB rate of {date}.":
        "Comprend {amounts}, converti au taux BCE du {date}.",
    "Not included, because no rate here covers them:":
        "Non compris, faute d'un taux qui les couvre :",
    "Amounts in another currency are in the totals above, converted at the ECB "
    "reference rate — a published mid-market rate, not one your broker would "
    "give you.":
        "Les montants dans une autre devise sont dans les totaux ci-dessus, "
        "convertis au taux de référence de la BCE — un taux médian publié, pas "
        "celui que ton courtier te donnerait.",
    "Rates of {date}.": "Taux du {date}.",
    "These are not in the totals above, because no rate here covers them:":
        "Ceux-ci ne sont pas dans les totaux ci-dessus, faute d'un taux qui "
        "les couvre :",

    # ─── Nouveautés ──────────────────────────────────────────────────
    "What changed": "Ce qui a changé",
    "You are running version {version}.": "Tu es en version {version}.",
    "Release notes are written once, in English, and are not translated — a "
    "translation of a note about a fix is one more thing that can be wrong "
    "about the fix.":
        "Les notes de version sont écrites une fois, en anglais, et ne sont "
        "pas traduites — la traduction d'une note sur un correctif est une "
        "chose de plus qui peut être fausse à propos de ce correctif.",
    "you are here": "tu es ici",
    "Added [changelog]": "Ajouté",
    "Changed [changelog]": "Modifié",
    "Fixed [changelog]": "Corrigé",
    "Removed [changelog]": "Retiré",
    "No changelog shipped with this build.":
        "Aucune liste de changements n'accompagne cette version.",
    "CHANGELOG.md is not inside the image — it is in the repository, which is "
    "where this page reads it from when you run from source.":
        "CHANGELOG.md n'est pas dans l'image — le fichier est dans le dépôt, "
        "et c'est là que cette page le lit quand tu lances depuis les sources.",

    # ─── Noms des catégories fournies ────────────────────────────────
    "Housing": "Logement",
    "Groceries": "Courses",
    "Restaurants & bars": "Restaurants & bars",
    "Transport": "Transport",
    "Car": "Voiture",
    "Travel": "Voyages",
    "Shopping": "Achats",
    "Health": "Santé",
    "Insurance": "Assurance",
    "Education": "Éducation",
    "Entertainment": "Loisirs",
    "Fees": "Frais",
    "Tax": "Impôts",
    "Cash withdrawal": "Retrait d'espèces",
    "Uncategorised": "Non catégorisé",
    "Investment": "Investissement",
    "Internal transfer": "Virement interne",

    # ─── Types de transaction ────────────────────────────────────────
    "deposit [kind]": "dépôt",
    "withdrawal [kind]": "retrait",
    "buy [kind]": "achat",
    "sell [kind]": "vente",
    "dividend [kind]": "dividende",
    "interest [kind]": "intérêts",
    "fee [kind]": "frais",
    "tax [kind]": "impôt",
    "transfer [kind]": "virement",
    "other [kind]": "autre",

    # ─── Rythmes ─────────────────────────────────────────────────────
    "weekly [rhythm]": "hebdomadaire",
    "monthly [rhythm]": "mensuel",
    "quarterly [rhythm]": "trimestriel",
    "half-yearly [rhythm]": "semestriel",
    "yearly [rhythm]": "annuel",

    # ─── Saisi à la main ─────────────────────────────────────────
    "typed in": "saisi à la main",
    "Balance in {currency}": "Solde en {currency}",
    "Record balance": "Enregistrer le solde",
    "Balance recorded: {amount} as of {date}.":
        "Solde enregistré : {amount} au {date}.",
    "The balance is missing.": "Le solde manque.",
    "Add by hand": "Ajouter à la main",
    "Add to {name} by hand": "Ajouter à {name} à la main",
    "For an account no bank connection and no export will describe. What you type in lands beside the imported rows and counts the same way: a purchase becomes part of the holding, a dividend is income, a fee is a fee.":
        "Pour un compte qu'aucune connexion bancaire ni aucun export ne décrit. Ce que tu saisis ici prend place à côté des lignes importées et compte de la même façon : un achat entre dans la position, un dividende est un revenu, des frais sont des frais.",
    "What happened": "Ce qui s'est passé",
    "Fee": "Frais",
    "optional": "facultatif",
    "optional, but it is what the holding will be called":
        "facultatif, mais c'est le nom que portera la position",
    "Price per unit, in {currency}": "Prix unitaire, en {currency}",
    "Total on the statement": "Total sur le relevé",
    "optional — otherwise quantity × price, plus the fee and tax on a purchase and minus them on a sale":
        "facultatif — sinon quantité × prix, plus frais et impôt sur un achat, moins sur une vente",
    "Amount, in {currency}": "Montant, en {currency}",
    "as a size — whether it is money in or out follows from what happened":
        "en valeur absolue — que l'argent entre ou sorte découle de ce qui s'est passé",
    "Direction": "Sens",
    "Money out of this account": "Argent qui sort de ce compte",
    "Money into this account": "Argent qui entre sur ce compte",
    "optional — the shop, the employer, the other account":
        "facultatif — le commerce, l'employeur, l'autre compte",
    "decide from the kind and my rules":
        "déduire du type et de mes règles",
    "Stay on this page to add another":
        "Rester sur cette page pour en ajouter une autre",
    "Add": "Ajouter",
    "Back to the account": "Retour au compte",
    "Added.": "Ajouté.",
    "Remove": "Retirer",
    "Connect a bank, import a CSV, or {add}.":
        "Connecte une banque, importe un CSV, ou {add}.",
    "Pick what kind of entry this is.":
        "Choisis de quel type d'écriture il s'agit.",
    "The date needs to be a real day, written year-month-day.":
        "La date doit être un vrai jour, écrit année-mois-jour.",
    "That date is in the future. A transaction is something that happened.":
        "Cette date est dans le futur. Une transaction, c'est quelque chose qui a eu lieu.",
    "A trade needs the security's ISIN — two letters and ten characters, like IE00B4L5Y983. It is on the order confirmation, and it is how the same fund at two brokers is recognised as one holding.":
        "Une opération a besoin de l'ISIN du titre — deux lettres et dix caractères, comme IE00B4L5Y983. Il figure sur l'avis d'opéré, et c'est par lui que le même fonds chez deux courtiers est reconnu comme une seule position.",
    "The quantity": "La quantité",
    "The price": "Le prix",
    "The fee": "Les frais",
    "The tax": "L'impôt",
    "The total": "Le total",
    "The amount": "Le montant",
    "{what} cannot be zero.": "{what} ne peut pas être zéro.",
    "A trade needs a quantity and a price per unit.":
        "Une opération a besoin d'une quantité et d'un prix unitaire.",
    "The amount is missing.": "Le montant manque.",
    "Bought {qty} × {name}": "Achat {qty} × {name}",
    "Sold {qty} × {name}": "Vente {qty} × {name}",
    "Includes {amounts}, converted at ECB rates — each month at its own rate, and months older than the rates on file at the oldest.":
        "Comprend {amounts}, convertis aux taux de la BCE — chaque mois à son propre taux, et les mois antérieurs aux taux enregistrés au plus ancien.",
    "Not counted, because no rate here covers them:":
        "Non comptés, parce qu'aucun taux ici ne les couvre :",
    "Fetch rates under {settings}.":
        "Récupère les taux dans {settings}.",
    "Budgeted": "Budgété",
    "Spent so far": "Dépensé à ce jour",
    "Remaining": "Restant",
    "for {month}": "pour {month}",
    "day {day} of {days} · {pct}% through the month":
        "jour {day} sur {days} · {pct} % du mois",
    "budget less spending": "budget moins dépenses",
    "Budget against spent": "Budget contre dépensé",
    "this month, per category — the chart follows the fields below as you type":
        "ce mois-ci, par catégorie — le graphique suit les champs ci-dessous pendant la saisie",
    "in {currency}": "en {currency}",
    "Everything you hold, aggregated by ISIN across accounts — the same fund at two brokers is one position from where you are standing. Values use the last market price, and each one names its day; a holding no price could be found for uses the price of your last trade, and says so.":
        "Tout ce que tu détiens, regroupé par ISIN entre les comptes — le même fonds chez deux courtiers est une seule position de là où tu te tiens. Valorisé au dernier cours de marché, et chacun indique son jour ; une position sans cours trouvé prend le prix de ta dernière opération, et le dit.",
    "Every holding is valued at its last market price — free, without a key — and every total built from prices names their day. A broker export gives an ISIN and a price source wants a ticker, so the ticker is looked up once and kept. Where the lookup fails or picks the wrong exchange, type the ticker Yahoo uses, like IWDA.AS; what you type is never replaced by a lookup.":
        "Chaque position est valorisée à son dernier cours de marché — gratuit, sans clé — et chaque total construit sur des cours indique leur jour. Un export de courtier donne un ISIN et une source de cours veut un ticker, donc le ticker est cherché une fois et conservé. Là où la recherche échoue ou choisit la mauvaise bourse, saisis le ticker qu'utilise Yahoo, comme IWDA.AS ; ce que tu saisis n'est jamais remplacé par une recherche.",
    "Also updated on start-up and every few hours in the background. A holding no price could be found for is valued at your last trade, and the pages say so.":
        "Mis à jour aussi au démarrage et toutes les quelques heures en arrière-plan. Une position sans cours trouvé est valorisée à ta dernière opération, et les pages le disent.",
    "Nothing to price yet — holdings appear here once a broker export or a trade typed in by hand has given you one.":
        "Rien à valoriser pour l'instant — les positions apparaissent ici dès qu'un export de courtier ou une opération saisie à la main t'en a donné une.",
    "Market prices": "Cours de marché",
    "Yahoo Finance": "Yahoo Finance",
    "Price": "Cours",
    "Ticker": "Ticker",
    "Ticker for {name}": "Ticker de {name}",
    "Update prices now": "Mettre à jour les cours",
    "Priced.": "Valorisé.",
    "at market prices of {date}": "aux cours de marché du {date}",
    "last trade, no market price":
        "dernière opération, pas de cours de marché",
    "{n} holding at its last traded price":
        "{n} position à son dernier prix d'opération",
    "{n} holdings at their last traded price":
        "{n} positions à leur dernier prix d'opération",
    "{n} holding priced.": "{n} position valorisée.",
    "{n} holdings priced.": "{n} positions valorisées.",
    "{ok} of {held} holdings priced. Could not price: {failed}.":
        "{ok} positions sur {held} valorisées. Pas de cours pour : {failed}.",

    # ─── Personnes ───────────────────────────────────────────────────
    "A person needs a name.":
        "Une personne a besoin d'un nom.",
    "Add person":
        "Ajouter une personne",
    "Add the people in your household, then tick on each account who it belongs to — one person, or several for a joint account. A switch appears in the header: Everyone shows the whole household, a name shows only that person's accounts on every page. An account ticked for nobody shows under Everyone only. This is a lens, not a lock: anyone who can sign in can flip it.":
        "Ajoute les personnes de ton foyer, puis coche sur chaque compte à qui il appartient — une personne, ou plusieurs pour un compte joint. Un sélecteur apparaît dans l'en-tête : « Tout le monde » montre le foyer entier, un prénom ne montre que les comptes de cette personne sur chaque page. Un compte coché pour personne n'apparaît que sous « Tout le monde ». C'est une loupe, pas un verrou : quiconque peut se connecter peut basculer.",
    "Alex":
        "Alex",
    "Everyone":
        "Tout le monde",
    "New person":
        "Nouvelle personne",
    "No people yet. Add the household under Settings → People, and each account can be somebody's.":
        "Pas encore de personnes. Crée le foyer sous Réglages → Personnes, et chaque compte pourra appartenir à quelqu'un.",
    "Only {name}'s accounts are counted on this page.":
        "Seuls les comptes de {name} sont comptés sur cette page.",
    "People":
        "Personnes",
    "Remove {name}? Their accounts stay.":
        "Retirer {name} ? Ses comptes restent.",
    "Removed. Their accounts stay; they just belong to one person fewer.":
        "Retiré. Les comptes restent ; ils appartiennent juste à une personne de moins.",
    "The budget itself is the household's; the spending measured against it here is {name}'s alone.":
        "Le budget est celui du foyer ; les dépenses mesurées ici sont celles de {name} seulement.",
    "There is already somebody called {name}.":
        "Il y a déjà quelqu'un qui s'appelle {name}.",
    "Tick one person, or several for a joint account. Nobody ticked means it shows only under Everyone.":
        "Coche une personne, ou plusieurs pour un compte joint. Sans coche, il n'apparaît que sous « Tout le monde ».",
    "Whose":
        "À qui",
    "Whose accounts":
        "Les comptes de qui",
    "Whose is it":
        "À qui est-il",
    "nobody yet":
        "personne pour l'instant",
    "whose accounts are whose":
        "à qui est quel compte",
    "{n} account":
        "{n} compte",
    "{n} accounts":
        "{n} comptes",
    "{n} more account belongs to somebody else, or to nobody yet — switch to Everyone to see it.":
        "{n} autre compte appartient à quelqu'un d'autre, ou à personne encore — passe sur « Tout le monde » pour le voir.",
    "{n} more accounts belong to somebody else, or to nobody yet — switch to Everyone to see them.":
        "{n} autres comptes appartiennent à quelqu'un d'autre, ou à personne encore — passe sur « Tout le monde » pour les voir.",
    "Belongs to {names}.":
        "Appartient à {names}.",
    "Belongs to nobody yet, so it shows under Everyone only.":
        "N'appartient encore à personne, et n'apparaît donc que sous « Tout le monde ».",
    "Change":
        "Modifier",

    # ─── Projection et synchronisation ───────────────────────────────
    "A goal to mark, in {currency}":
        "Un objectif à marquer, en {currency}",
    "Amounts in a currency with no rate on file are not in that figure.":
        "Les montants dans une devise sans taux enregistré ne sont pas dans ce chiffre.",
    "At":
        "À",
    "Automatic sync is off.":
        "La synchronisation automatique est désactivée.",
    "Average return per year, in %":
        "Rendement moyen par an, en %",
    "Bank sync":
        "Synchronisation bancaire",
    "Before inflation. Broad stock-market funds have averaged around 6–8 % a year over long periods, savings accounts far less; a cautious plan uses a lower number than history did.":
        "Avant inflation. Les fonds actions larges ont fait en moyenne 6–8 % par an sur de longues périodes, les livrets bien moins ; un plan prudent prend un chiffre plus bas que l'histoire.",
    "Calculate":
        "Calculer",
    "Forecast":
        "Projection",
    "Goal":
        "Objectif",
    "Goal, in {currency}":
        "Objectif, en {currency}",
    "I have a goal":
        "J'ai un objectif",
    "I save a fixed amount":
        "J'épargne un montant fixe",
    "In {year}":
        "En {year}",
    "Last automatic sync: {when}.":
        "Dernière synchronisation automatique : {when}.",
    "Local time of the machine this runs on. A day that was slept through — the machine was off at that hour — is caught up as soon as it is next awake.":
        "Heure locale de la machine qui fait tourner l'app. Un jour manqué — la machine était éteinte à cette heure — est rattrapé dès qu'elle est de nouveau allumée.",
    "No account is connected to a bank yet.":
        "Aucun compte n'est encore connecté à une banque.",
    "No automatic sync has run yet.":
        "Aucune synchronisation automatique n'a encore eu lieu.",
    "Returns":
        "Rendement",
    "Returns earn":
        "Le rendement rapporte",
    "Save per month":
        "À épargner par mois",
    "Saved per month, in {currency}":
        "Épargné par mois, en {currency}",
    "Show as a table":
        "Afficher en tableau",
    "Starting from {amount}: what {who} adds up to today across {n} accounts.":
        "À partir de {amount} : ce que {who} totalise aujourd'hui sur {n} comptes.",
    "Sync all accounts now":
        "Synchroniser tous les comptes maintenant",
    "Sync connected accounts automatically every day":
        "Synchroniser les comptes connectés automatiquement chaque jour",
    "The goal is already met — nothing more is needed.":
        "L'objectif est déjà atteint — rien de plus n'est nécessaire.",
    "The next one is at {time}.":
        "La prochaine est à {time}.",
    "What to work out":
        "Que calculer",
    "Where the money is heading, starting from what the accounts add up to today. The return is your assumption, not a prediction — the page only does the arithmetic, and shows how much of the result is your own deposits.":
        "Où va l'argent, à partir de ce que les comptes totalisent aujourd'hui. Le rendement est ton hypothèse, pas une prédiction — la page ne fait que le calcul, et montre quelle part du résultat vient de tes propres versements.",
    "With returns":
        "Avec rendement",
    "Year":
        "Année",
    "Year by year":
        "Année par année",
    "Years from now":
        "Années à partir d'aujourd'hui",
    "You put in":
        "Tu verses",
    "and want to know what it takes a month":
        "et veux savoir ce que ça demande par mois",
    "and want to see where it leads":
        "et veux voir où ça mène",
    "at {rate} % a year, compounding monthly":
        "à {rate} % par an, capitalisé mensuellement",
    "the goal is not reached in this time":
        "l'objectif n'est pas atteint dans ce délai",
    "the goal is reached in {year}":
        "l'objectif est atteint en {year}",
    "the household":
        "le foyer",
    "to reach {target} by {year}":
        "pour atteindre {target} d'ici {year}",
    "today's {start} plus {monthly} a month":
        "les {start} d'aujourd'hui plus {monthly} par mois",
    "{n} account connected":
        "{n} compte connecté",
    "{n} accounts connected":
        "{n} comptes connectés",
    "{n} new transaction across {accounts} accounts.":
        "{n} nouvelle transaction sur {accounts} comptes.",
    "{n} new transactions across {accounts} accounts.":
        "{n} nouvelles transactions sur {accounts} comptes.",
    "{n} year from now":
        "dans {n} an",
    "{n} years from now":
        "dans {n} ans",
    "{ok} of {total} accounts synced. Failed: {names}.":
        "{ok} comptes sur {total} synchronisés. Échec : {names}.",

    # ─── Historique, connexions, retraite ────────────────────────────
    "A birthday is optional; with one, the Forecast page adds a retirement outlook for that person.":
        "La date de naissance est facultative ; avec elle, la page Projection ajoute une perspective de retraite pour cette personne.",
    "Add the people in your household under Settings → People, each with a birthday, and this page will say where each of them stands for retirement.":
        "Ajoute les personnes de ton foyer sous Réglages → Personnes, chacune avec sa date de naissance, et cette page dira où chacune en est pour la retraite.",
    "Age":
        "Âge",
    "All":
        "Tout",
    "At {age}, in {year}":
        "À {age} ans, en {year}",
    "Bank connections":
        "Connexions bancaires",
    "Birthday of {name}":
        "Date de naissance de {name}",
    "Birthday — what the retirement outlook counts from":
        "Date de naissance — le point de départ de la perspective de retraite",
    "Consent expired — reconnect.":
        "Consentement expiré — reconnecte.",
    "Last sync failed: {error}":
        "Dernière synchronisation échouée : {error}",
    "Last sync {n} days ago.":
        "Dernière synchronisation il y a {n} jours.",
    "Last sync {n} hours ago.":
        "Dernière synchronisation il y a {n} heures.",
    "Never synced.":
        "Jamais synchronisé.",
    "No birthday on file for {names}. Add one under Settings → People and the outlook appears here.":
        "Pas de date de naissance pour {names}. Ajoute-la sous Réglages → Personnes et la perspective apparaît ici.",
    "No dated readings yet — the line starts with the first balance or trade.":
        "Pas encore de relevé daté — la ligne commence au premier solde ou à la première opération.",
    "Overrides the Forecast plan's {amount}; clear the field to follow it again.":
        "Remplace les {amount} du plan de Projection ; vide le champ pour le suivre à nouveau.",
    "Records go back to {date}; the line fills in with every daily sync.":
        "Les relevés remontent au {date} ; la ligne se remplit à chaque synchronisation quotidienne.",
    "Retire at":
        "Retraite à",
    "Retirement outlook":
        "Perspective de retraite",
    "Return per year, %":
        "Rendement par an, %",
    "Saved per month, {currency}":
        "Épargné par mois, {currency}",
    "Saved.":
        "Enregistré.",
    "Supports, per month":
        "Permet, par mois",
    "Synced {n} hours ago":
        "Synchronisé il y a {n} heures",
    "The birthday needs to be a date.":
        "La date de naissance doit être une date.",
    "The monthly amount is taken from this person's Forecast plan; type one to override it.":
        "Le montant mensuel vient du plan de Projection de cette personne ; saisis-en un pour le remplacer.",
    "Time range":
        "Période",
    "at a 4 % yearly withdrawal — the usual rule of thumb, before tax and pension":
        "à un retrait de 4 % par an — la règle empirique habituelle, avant impôts et pension",
    "consent for {n} more days":
        "consentement encore {n} jours",
    "since the start of the range":
        "depuis le début de la période",
    "{age} today · {n} accounts · {amount}":
        "{age} ans aujourd'hui · {n} comptes · {amount}",
    "{name} is already {age} — past the retirement age set here.":
        "{name} a déjà {age} ans — au-delà de l'âge de retraite fixé ici.",
    "{n} connected account":
        "{n} compte connecté",
    "{n} connected accounts":
        "{n} comptes connectés",
    "{part} of it returns":
        "dont {part} de rendement",

    # ─── Idées d'actions ─────────────────────────────────────────────
    "Share Ideas": "Idées d'actions",
    "Four boards over the same nightly Yahoo cache: shares that have fallen and are cheap, shares paying a high dividend that is still growing, ETFs with strong past growth at a low TER, and dividend ETFs paying a high yield at a low TER. A shortlist to research, never a recommendation to buy.":
        "Quatre tableaux sur le même cache Yahoo, rafraîchi chaque nuit : des actions qui ont chuté et sont bon marché, des actions au dividende élevé qui continue de croître, des ETF à forte croissance passée pour des frais bas, et des ETF de dividendes au rendement élevé pour des frais bas. Une liste à creuser, jamais une recommandation d'achat.",
    "Value [board]": "Décote",
    "fallen · cheap · quality · pays": "chuté · pas cher · qualité · paie",
    "Dividends": "Dividendes",
    "high yield that is still growing": "rendement élevé qui croît encore",
    "ETFs": "ETF",
    "high growth · low TER": "forte croissance · TER bas",
    "Dividend ETFs": "ETF de dividendes",
    "high yield · low TER": "rendement élevé · TER bas",
    "The board": "Le tableau",
    "Loading…": "Chargement…",
    "Names that pass every hard gate and therefore carry a score.":
        "Les titres qui passent chaque filtre dur et portent donc un score.",
    "Ranked candidates": "Candidats classés",
    "Scored 70 or above out of 100 on this board.":
        "Notés 70 ou plus sur 100 sur ce tableau.",
    "Strong (70+)": "Solides (70+)",
    "Can sit inside a French PEA. For shares this is inferred from the country of incorporation; for ETFs it is a curated fact, because no data source publishes it.":
        "Peut se loger dans un PEA. Pour les actions, déduit du pays du siège ; pour les ETF, un fait tenu à la main, car aucune source ne le publie.",
    "PEA-eligible": "Éligible PEA",
    "Excluded before scoring, with the reason kept. Listed at the bottom of the page.":
        "Écartés avant la notation, motif conservé. Listés en bas de page.",
    "Gated out": "Écartés",
    "The screen is transparent on purpose — every column below is an input to the score, not an output of it.":
        "Le filtre est transparent à dessein — chaque colonne ci-dessous est un ingrédient du score, pas un résultat.",
    "PEA-eligible only": "Éligibles PEA seulement",
    "Hide what I already own": "Masquer ce que je détiens déjà",
    "Hide dismissed": "Masquer les écartés",
    "Watchlist only": "Liste de suivi seulement",
    "Sector": "Secteur",
    "Min score": "Score minimum",
    "Show": "Afficher",
    "all": "tout",
    "Candidates": "Candidats",
    "Click a row for the full breakdown.": "Cliquez sur une ligne pour le détail complet.",
    "Excluded before scoring, and why. Shown because an absence you cannot explain is worse than no screen at all.":
        "Écartés avant la notation, et pourquoi. Affichés parce qu'une absence inexplicable est pire qu'aucun filtre.",
    "Symbol": "Symbole",
    "Group": "Groupe",
    "Reason": "Motif",
    "Close": "Fermer",
    "How to read this": "Comment lire ce tableau",
    "Value 25% · cheapness 25% · quality 30% · dividend 20%. It finds shares that have fallen a long way from their own 52-week high and are cheap on earnings while still earning well and paying a covered dividend.":
        "Décote 25 % · cherté 25 % · qualité 30 % · dividende 20 %. Il trouve les actions tombées loin de leur plus haut sur 52 semaines et bon marché rapportées aux bénéfices, tout en gagnant encore bien et en versant un dividende couvert.",
    "The flag that matters most is “near its 52-week low”. “40% off the high” and “still falling” are the same fact seen from two ends, and only the second tells you the market has not finished selling.":
        "L'alerte qui compte le plus est « près de son plus bas sur 52 semaines ». « 40 % sous le plus haut » et « chute encore » sont le même fait vu des deux bouts, et seul le second dit que le marché n'a pas fini de vendre.",
    "Yield 35% · growth 30% · safety 20% · quality 15%. Yield and growth carry most of it, as they should on an income board — but not all of it, because a ranking on yield alone puts the next dividend cut at the top of the list every single time. The growth pillar blends dividend growth (the forward annual rate against the last twelve months' actual), revenue growth and earnings growth.":
        "Rendement 35 % · croissance 30 % · sécurité 20 % · qualité 15 %. Rendement et croissance portent l'essentiel, comme il se doit sur un tableau de revenu — mais pas tout, car un classement sur le seul rendement met chaque fois la prochaine coupe de dividende en tête. Le pilier croissance mêle la croissance du dividende (le taux annuel annoncé contre celui réellement versé sur douze mois), celle du chiffre d'affaires et celle des bénéfices.",
    "A yield above 12% is gated out rather than rewarded: on a large cap that is the market pricing a cut, not an opportunity. So is a payout ratio above 90%, and a business whose revenue is shrinking. The free-cash-flow payout is the column to look at when two names have the same yield — earnings can be flattered, cash cannot, and a dividend costing more than 100% of free cash flow is being paid out of the balance sheet.":
        "Un rendement au-dessus de 12 % est écarté plutôt que récompensé : sur une grande capitalisation, c'est le marché qui anticipe une coupe, pas une occasion. Idem pour un taux de distribution au-dessus de 90 % et un chiffre d'affaires qui recule. La distribution rapportée au flux de trésorerie libre est la colonne à regarder quand deux titres ont le même rendement — les bénéfices se maquillent, la trésorerie non, et un dividende qui coûte plus de 100 % du flux libre est payé avec le bilan.",
    "Growth 40% · cost 30% · risk 20% · size 10%. Growth is the compound annual total return in euros, computed from the adjusted price history rather than read from a field — Yahoo leaves its own return fields empty for almost every European UCITS listing, and the raw price of a distributing fund understates its return by roughly its yield every year.":
        "Croissance 40 % · coût 30 % · risque 20 % · taille 10 %. La croissance est le rendement total annualisé en euros, calculé à partir de l'historique de cours ajusté plutôt que lu dans un champ — Yahoo laisse ses propres champs de rendement vides pour presque toutes les cotations UCITS européennes, et le cours brut d'un fonds distribuant sous-estime son rendement d'à peu près son taux de distribution chaque année.",
    "The growth column is the past and the TER is the future. Five years that contained one of the strongest US equity runs on record will rank concentration highly for reasons that have already happened. The TER is charged every year whatever the market does — which is why cost carries 30% of a board whose headline is growth.":
        "La colonne croissance, c'est le passé ; le TER, c'est l'avenir. Cinq années contenant l'une des plus fortes hausses des actions américaines classeront haut la concentration pour des raisons déjà passées. Le TER est prélevé chaque année quoi que fasse le marché — d'où 30 % pour le coût sur un tableau dont le titre est la croissance.",
    "The universe is UCITS-only on purpose: without a PRIIPs KID a US-listed ETF cannot be bought at a European broker at all, so ranking one would be ranking something unbuyable. PEA eligibility is a curated fact, not an inferred one — it depends on the fund's holdings and wrapper, and a synthetic MSCI World qualifies where a physical one does not.":
        "L'univers est volontairement limité aux UCITS : sans DIC PRIIPs, un ETF coté aux États-Unis ne s'achète pas chez un courtier européen, le classer reviendrait à classer l'inachetable. L'éligibilité PEA est un fait tenu à la main, pas déduit — elle dépend des positions et de l'enveloppe du fonds, et un MSCI World synthétique se qualifie là où un physique ne le fait pas.",
    "Yield 35% · cost 25% · growth 20% · stability 20%. The yield is computed from the distributions the fund actually paid over the last twelve months, not read from a field — Yahoo populates its own yield for barely one European listing in six, so a board that trusted it would be blank for five funds out of every six it ranks.":
        "Rendement 35 % · coût 25 % · croissance 20 % · stabilité 20 %. Le rendement est calculé à partir des distributions réellement versées sur douze mois, pas lu dans un champ — Yahoo ne renseigne son propre rendement que pour à peine une cotation européenne sur six, un tableau qui s'y fierait serait vide pour cinq fonds sur six.",
    "It will read lower than the yield on the factsheet. The numerator is the past year's payments and the denominator is today's price, so a fund that has risen shows a smaller ratio than the “indicated” yield a provider quotes. Both are honest; this one is backward-looking on purpose, because a forward yield is an estimate and there are enough estimates on this page already.":
        "Il paraîtra plus bas que le rendement de la fiche. Le numérateur est ce qui a été versé l'an passé et le dénominateur le cours d'aujourd'hui, un fonds qui a monté affiche donc un ratio plus petit que le rendement « indicatif » d'un émetteur. Les deux sont honnêtes ; celui-ci regarde en arrière à dessein, car un rendement prévisionnel est une estimation, et il y en a déjà assez sur cette page.",
    "Yield is only 35% for the same reason it is on the share board, and the reason bites harder here: an index that selects on yield mechanically buys whatever has just fallen. Worse, a fund has no payout ratio and no balance sheet you can interrogate — so the only evidence that its income is durable is whether it has ever collapsed. That is the Worst cut column, and it carries most of the stability pillar.":
        "Le rendement ne pèse que 35 %, pour la même raison que sur le tableau des actions, et elle mord plus fort ici : un indice qui sélectionne sur le rendement achète mécaniquement ce qui vient de chuter. Pire, un fonds n'a ni taux de distribution ni bilan à interroger — la seule preuve que son revenu est durable est de savoir s'il s'est déjà effondré. C'est la colonne « Pire coupe », et elle porte l'essentiel du pilier stabilité.",
    "Cost is 25% because the TER comes out of the same cash the distribution does. At a 3.5% yield a 0.45% TER is not “half a percent” — it is 13% of your income, every year, guaranteed. The Net column does that subtraction. Accumulating share classes are gated out: they pay nothing, which does not make them bad funds, only not income ones.":
        "Le coût pèse 25 % parce que le TER sort de la même trésorerie que la distribution. À 3,5 % de rendement, un TER de 0,45 % n'est pas « un demi pour cent » — c'est 13 % de votre revenu, chaque année, garanti. La colonne « Net » fait cette soustraction. Les parts capitalisantes sont écartées : elles ne versent rien, ce qui n'en fait pas de mauvais fonds, seulement pas des fonds de revenu.",
    "Every score is a sorting device for a research queue, not a valuation and not advice. Fundamentals come from Yahoo and are refreshed once a day in the background; they can be wrong, stale, or reported in a currency other than the price. Verify the two or three names you actually care about at the source before doing anything.":
        "Chaque score est un outil de tri pour une file de recherche, ni une valorisation ni un conseil. Les fondamentaux viennent de Yahoo et sont rafraîchis une fois par jour en arrière-plan ; ils peuvent être faux, périmés ou exprimés dans une autre devise que le cours. Vérifiez à la source les deux ou trois titres qui vous intéressent vraiment avant de faire quoi que ce soit.",

    # Colonnes et raccourcis
    "Score": "Score",
    "Pillars": "Piliers",
    "Off high": "Sous le haut",
    "P/E": "PER",
    "Yield": "Rendement",
    "Payout": "Distribution",
    "ROE": "ROE",
    "Debt/Eq": "Dette/FP",
    "Div growth": "Croiss. div.",
    "Rev growth": "Croiss. CA",
    "EPS growth": "Croiss. BPA",
    "FCF payout": "Distrib. / FCF",
    "5y p.a.": "5 ans p. a.",
    "3y p.a.": "3 ans p. a.",
    "1y": "1 an",
    "Vol": "Vol.",
    "Max DD": "Baisse max.",
    "Policy": "Politique",
    "Size": "Taille",
    "Net": "Net",
    "Worst cut": "Pire coupe",
    "Pays": "Verse",
    "Region": "Région",
    "no data": "pas de données",
    "held": "détenu",
    "Already in the portfolio": "Déjà en portefeuille",
    "Can sit in a French PEA.": "Peut se loger dans un PEA.",
    "watching": "suivi",
    "dismissed": "écarté",
    "Add to watchlist": "Ajouter à la liste de suivi",
    "Dismiss": "Écarter",
    "☆ Watch": "☆ Suivre",
    "✕ Dismiss": "✕ Écarter",
    "Clear mark": "Effacer la marque",
    "Open on Yahoo ↗": "Ouvrir sur Yahoo ↗",
    "Nothing matches these filters.": "Rien ne correspond à ces filtres.",
    "Nothing gated out.": "Rien d'écarté.",
    "Gated out:": "Écarté :",
    "Last fetch error:": "Dernière erreur de collecte :",
    "data coverage": "couverture des données",
    "mkt cap": "capi.",
    "yes": "oui",
    "no": "non",
    "yes (EU/EEA seat)": "oui (siège UE/EEE)",
    "no — outside a PEA only": "non — hors PEA seulement",
    "never fell": "jamais baissé",
    "× a year": "× par an",
    "Failed to load": "Échec du chargement",
    "Loaded, but failed to render — see the console":
        "Chargé, mais impossible à afficher — voir la console",
    "{n} screened · last refresh {date}": "{n} passés au crible · dernier rafraîchissement {date}",
    "This cache is empty. The first refresh starts a minute after start-up and takes a few minutes; there is also a button under Settings.":
        "Ce cache est vide. Le premier rafraîchissement démarre une minute après le lancement et prend quelques minutes ; il y a aussi un bouton dans les Réglages.",
    "Data was last refreshed {days} days ago. Every price-derived figure below is that old.":
        "Les données datent d'il y a {days} jours. Chaque chiffre dérivé d'un cours ci-dessous a cet âge.",
    "{n} symbol(s) failed their last fetch and are showing older figures.":
        "{n} symbole(s) ont échoué à leur dernière collecte et affichent des chiffres plus anciens.",
    "Hide": "Masquer",
    "A hollow bar means there was no data for that pillar — the score is then a mean over the pillars that do have data, which is why thin rows carry a “thin data” flag.":
        "Une barre creuse signifie qu'il n'y avait pas de données pour ce pilier — le score est alors une moyenne des piliers renseignés, d'où l'alerte « données minces » sur les lignes maigres.",
    "Trailing where there is a trailing profit, otherwise the forward estimate (marked ƒ).":
        "Sur douze mois glissants s'il y a un bénéfice, sinon l'estimation prévisionnelle (marquée ƒ).",
    "Yahoo’s figure, not the KID’s": "Chiffre de Yahoo, pas du DIC",
    "value": "décote",
    "cheap": "pas cher",
    "quality": "qualité",
    "dividend": "dividende",
    "yield": "rendement",
    "growth": "croissance",
    "safety": "sécurité",
    "cost": "coût",
    "risk": "risque",
    "size": "taille",
    "stability": "stabilité",
    "Ongoing charge per year. Curated from the fund KID where we have it; Yahoo otherwise, which is then flagged.":
        "Frais courants par an. Tirés du DIC du fonds quand nous l'avons ; sinon de Yahoo, ce qui est alors signalé.",

    # Les quatre tableaux
    "Cheap and beaten down": "Pas cher et massacré",
    "Shares that have fallen from their own 52-week high, trade on a low P/E, still earn well, and pay a dividend their earnings cover.":
        "Des actions tombées de leur plus haut sur 52 semaines, à PER bas, qui gagnent encore bien et versent un dividende couvert par leurs bénéfices.",
    "Pillar bars are, left to right: value (how far it has fallen), cheap (P/E and price-to-book), quality (ROE, operating margin, leverage, liquidity), dividend (yield, and whether earnings cover it).":
        "Les barres des piliers sont, de gauche à droite : décote (l'ampleur de la chute), pas cher (PER et cours sur actif net), qualité (ROE, marge opérationnelle, endettement, liquidité), dividende (rendement, et s'il est couvert par les bénéfices).",
    "How far below its own 52-week high the price sits.":
        "À quelle distance sous son plus haut sur 52 semaines se situe le cours.",
    "Share of earnings paid out as dividend. Sweet spot 25–60%.":
        "Part des bénéfices versée en dividende. Idéal entre 25 et 60 %.",
    "Ratio, not percent. Above 2.0 is flagged.": "Un ratio, pas un pourcentage. Signalé au-dessus de 2,0.",
    "High dividend, still growing": "Dividende élevé, qui croît encore",
    "The highest yields that are not warning you about themselves: the dividend must be growing, covered by earnings AND by free cash flow, on a business that is not shrinking.":
        "Les rendements les plus élevés qui ne vous mettent pas en garde contre eux-mêmes : le dividende doit croître, être couvert par les bénéfices ET par le flux de trésorerie libre, dans une entreprise qui ne rétrécit pas.",
    "Pillar bars are, left to right: yield (what it pays today), growth (dividend, revenue and earnings growth), safety (payout ratio, free-cash-flow cover, leverage, liquidity), quality (ROE and margins). Dividend growth is the forward annual rate against the last twelve months actually paid, so a declared cut shows up here the day it is announced rather than a year later.":
        "Les barres des piliers sont, de gauche à droite : rendement (ce qui est versé aujourd'hui), croissance (dividende, chiffre d'affaires, bénéfices), sécurité (taux de distribution, couverture par le flux libre, endettement, liquidité), qualité (ROE et marges). La croissance du dividende est le taux annuel annoncé contre ce qui a été réellement versé sur douze mois, une coupe déclarée apparaît donc ici le jour de l'annonce plutôt qu'un an plus tard.",
    "Forward annual dividend against the last twelve months actually paid. Negative = a cut has been declared.":
        "Dividende annuel annoncé contre celui réellement versé sur douze mois. Négatif = une coupe est déclarée.",
    "Share of EARNINGS paid out.": "Part des BÉNÉFICES distribuée.",
    "Share of FREE CASH FLOW paid out. Above 100% the dividend is coming out of the balance sheet.":
        "Part du FLUX DE TRÉSORERIE LIBRE distribuée. Au-dessus de 100 %, le dividende sort du bilan.",
    "High growth, low TER": "Forte croissance, TER bas",
    "UCITS ETFs ranked on compound annual total return in EUR against what they charge for it. Growth is the past; the TER is the only column here that is a fact about the future.":
        "Des ETF UCITS classés sur le rendement total annualisé en EUR rapporté à ce qu'ils facturent. La croissance, c'est le passé ; le TER est la seule colonne ici qui soit un fait sur l'avenir.",
    "Pillar bars are, left to right: growth (5-year and 3-year CAGR in EUR, total return), cost (TER), risk (return per unit of volatility, and the worst peak-to-trough fall in the window), size (fund assets — a small fund can close, and trades on a wider spread). Returns are converted to euros before they are measured: a USD-quoted UCITS ETF and its EUR-quoted twin are the same fund, and comparing their raw returns would rank the dollar.":
        "Les barres des piliers sont, de gauche à droite : croissance (rendement annualisé sur 5 et 3 ans en EUR, total), coût (TER), risque (rendement par unité de volatilité, et pire baisse du haut au bas dans la fenêtre), taille (encours — un petit fonds peut fermer et se traite avec un écart plus large). Les rendements sont convertis en euros avant d'être mesurés : un ETF UCITS coté en USD et son jumeau coté en EUR sont le même fonds, et comparer leurs rendements bruts classerait le dollar.",
    "Compound annual total return over five years, in EUR.":
        "Rendement total annualisé sur cinq ans, en EUR.",
    "Annualised standard deviation of weekly returns over the last year.":
        "Écart-type annualisé des rendements hebdomadaires sur l'année écoulée.",
    "Worst peak-to-trough fall within the cached history.":
        "Pire baisse du haut au bas dans l'historique en cache.",
    "acc = accumulating (nothing is paid out, nothing is taxed until you sell). dist = distributing.":
        "acc = capitalisant (rien n'est versé, rien n'est imposé avant la vente). dist = distribuant.",
    "High yield, low TER": "Rendement élevé, TER bas",
    "Distributing UCITS ETFs ranked on the income they actually paid over the last twelve months against what they charge for it — and on whether that income is growing rather than being cut. Accumulating share classes are excluded: they pay nothing.":
        "Des ETF UCITS distribuants classés sur le revenu réellement versé sur douze mois rapporté à ce qu'ils facturent — et sur le fait que ce revenu croît plutôt que d'être coupé. Les parts capitalisantes sont exclues : elles ne versent rien.",
    "Pillar bars are, left to right: yield (distributions paid over the last twelve months, divided by today’s price), cost (TER), growth (this year’s distributions against last year’s, plus the price return as a check that the income is not just capital coming back), stability (the worst year-on-year fall in the distribution on record, and the worst peak-to-trough price fall). The yield is computed from the distributions themselves, not read from a field — Yahoo populates its own yield for barely one European listing in six. Because the numerator is the past year and the denominator is today’s price, it reads lower than a provider’s “indicated yield” whenever the fund has risen.":
        "Les barres des piliers sont, de gauche à droite : rendement (distributions versées sur douze mois, divisées par le cours du jour), coût (TER), croissance (les distributions de cette année contre celles de l'an passé, plus le rendement du cours pour vérifier que le revenu n'est pas du capital qui revient), stabilité (la pire baisse annuelle de la distribution connue, et la pire baisse du cours du haut au bas). Le rendement est calculé à partir des distributions elles-mêmes, pas lu dans un champ — Yahoo ne renseigne le sien que pour à peine une cotation européenne sur six. Le numérateur étant l'année écoulée et le dénominateur le cours du jour, il paraît plus bas que le « rendement indicatif » d'un émetteur dès que le fonds a monté.",
    "Distributions actually paid over the last 12 months, divided by the current price.":
        "Distributions réellement versées sur les 12 derniers mois, divisées par le cours actuel.",
    "Yield minus TER — the income that reaches you before tax. Shown, never ranked on: a high net yield can come from paying a lot or from costing little, and those are different funds.":
        "Rendement moins TER — le revenu qui vous parvient avant impôt. Affiché, jamais utilisé pour classer : un rendement net élevé peut venir d'un fonds qui verse beaucoup ou d'un fonds qui coûte peu, et ce sont des fonds différents.",
    "Distributions of the last 12 months against the 12 before. Negative = the payout is shrinking.":
        "Distributions des 12 derniers mois contre les 12 précédents. Négatif = la distribution rétrécit.",
    "The deepest year-on-year fall in the distribution across the years on record. “none” means every year on record was at least as big as the one before. Blank means there is not enough history to say.":
        "La plus forte baisse annuelle de la distribution sur les années connues. « aucune » signifie que chaque année connue a été au moins aussi grosse que la précédente. Vide signifie qu'il n'y a pas assez d'historique pour le dire.",
    "Compound annual TOTAL return in EUR — price plus distributions reinvested. A high yield beside a poor total return means capital is being handed back.":
        "Rendement TOTAL annualisé en EUR — cours plus distributions réinvesties. Un rendement élevé à côté d'un rendement total médiocre signifie que du capital est rendu.",
    "Distributions in the last 12 months: 1 = annual, 2 = semi-annual, 4 = quarterly, 12 = monthly.":
        "Distributions sur les 12 derniers mois : 1 = annuelle, 2 = semestrielle, 4 = trimestrielle, 12 = mensuelle.",

    # Le panneau de détail
    "Trailing yield": "Rendement sur 12 mois",
    "Distributions paid over the last 12 months divided by the current price. Computed from the payments themselves — Yahoo’s own yield field is populated for barely one European listing in six.":
        "Distributions versées sur les 12 derniers mois divisées par le cours actuel. Calculé à partir des versements eux-mêmes — le champ rendement de Yahoo n'est renseigné que pour à peine une cotation européenne sur six.",
    "Charged out of the same cash the distribution comes from.":
        "Prélevé sur la même trésorerie que celle d'où vient la distribution.",
    "Net yield": "Rendement net",
    "Yield minus TER, before any tax. Shown but never ranked on — a high net yield can come from paying a lot or from costing little.":
        "Rendement moins TER, avant tout impôt. Affiché mais jamais utilisé pour classer — un rendement net élevé peut venir d'un fonds qui verse beaucoup ou qui coûte peu.",
    "TER as a share of income": "TER en part du revenu",
    "What proportion of the income the fund keeps. Half a percent sounds small until it is 13% of a 3.5% yield.":
        "Quelle part du revenu le fonds garde. Un demi pour cent paraît peu jusqu'à ce que ce soit 13 % d'un rendement de 3,5 %.",
    "Distributions, last 12m": "Distributions, 12 derniers mois",
    "In the listing currency. A yield is a ratio, so it needs no currency conversion.":
        "Dans la devise de cotation. Un rendement est un ratio, il n'a pas besoin de conversion.",
    "Distributions, 12m before": "Distributions, 12 mois avant",
    "Distribution growth": "Croissance de la distribution",
    "This year’s total against last year’s.": "Le total de cette année contre celui de l'an passé.",
    "Worst year on record": "Pire année connue",
    "The deepest year-on-year fall in the distribution across the years available. An index fund has no payout ratio to interrogate, so this is the only evidence that its income is durable.":
        "La plus forte baisse annuelle de la distribution sur les années disponibles. Un fonds indiciel n'a pas de taux de distribution à interroger, c'est donc la seule preuve que son revenu est durable.",
    "A change in frequency makes one year’s total incomparable with the next.":
        "Un changement de fréquence rend le total d'une année incomparable avec le suivant.",
    "Last distribution": "Dernière distribution",
    "Distribution history": "Historique des distributions",
    "5-year total return": "Rendement total sur 5 ans",
    "Price plus distributions reinvested, in EUR. A high yield beside a weak total return means capital is being returned rather than earned.":
        "Cours plus distributions réinvesties, en EUR. Un rendement élevé à côté d'un rendement total faible signifie que du capital est rendu plutôt que gagné.",
    "Max drawdown": "Baisse maximale",
    "Fund size": "Encours",
    "Policy (curated)": "Politique (tenue à la main)",
    "Cross-checked against the distributions actually observed; a disagreement is flagged rather than resolved silently.":
        "Recoupé avec les distributions réellement observées ; un désaccord est signalé plutôt que tranché en silence.",
    "Provider": "Émetteur",
    "Matters more on an income holding than on an accumulating one: outside a PEA every distribution is taxed the year it is paid, so the headline yield is not the net one.":
        "Compte plus pour une position de revenu que pour une capitalisante : hors PEA, chaque distribution est imposée l'année de son versement, le rendement affiché n'est donc pas le net.",
    "In the portfolio": "En portefeuille",
    "Data fetched": "Données collectées",
    "Curated from the fund KID where we have it — Yahoo has no expense ratio for most European listings, and reports it in two different units when it does.":
        "Tiré du DIC du fonds quand nous l'avons — Yahoo n'a pas de frais pour la plupart des cotations européennes, et les donne dans deux unités différentes quand il en a.",
    "Yahoo’s TER": "TER selon Yahoo",
    "Kept as a cross-check. A disagreement usually means a different share class.":
        "Gardé comme contrôle. Un désaccord signifie en général une autre classe de parts.",
    "5-year CAGR": "Rendement annualisé 5 ans",
    "Compound annual total return in EUR, from the dividend-adjusted price history.":
        "Rendement total annualisé en EUR, d'après l'historique de cours ajusté des dividendes.",
    "3-year CAGR": "Rendement annualisé 3 ans",
    "1-year return": "Rendement 1 an",
    "Volatility (1y)": "Volatilité (1 an)",
    "Annualised standard deviation of weekly returns.":
        "Écart-type annualisé des rendements hebdomadaires.",
    "Worst peak-to-trough fall inside the cached history — measured on weekly closes, so it is a floor on the real figure.":
        "Pire baisse du haut au bas dans l'historique en cache — mesurée sur les clôtures hebdomadaires, donc un plancher du chiffre réel.",
    "Return per unit of vol": "Rendement par unité de vol.",
    "3-year CAGR divided by volatility. Not a Sharpe ratio — no risk-free rate is subtracted.":
        "Rendement annualisé 3 ans divisé par la volatilité. Pas un ratio de Sharpe — aucun taux sans risque n'est soustrait.",
    "A small fund can be closed and merged, and trades on a wider spread.":
        "Un petit fonds peut être fermé et fusionné, et se traite avec un écart plus large.",
    "Distribution policy": "Politique de distribution",
    "acc = accumulating. Outside a tax wrapper, a distributing fund is taxed on each distribution in the year it is paid.":
        "acc = capitalisant. Hors enveloppe fiscale, un fonds distribuant est imposé sur chaque distribution l'année de son versement.",
    "History used": "Historique utilisé",
    "A curated fact, not an inferred one: it depends on the fund’s holdings and wrapper, and no data source publishes it.":
        "Un fait tenu à la main, pas déduit : il dépend des positions et de l'enveloppe du fonds, et aucune source ne le publie.",
    "Dividend yield": "Rendement du dividende",
    "5-year average yield": "Rendement moyen sur 5 ans",
    "A yield far above its own average is often a falling price, not a rising dividend.":
        "Un rendement bien au-dessus de sa propre moyenne est souvent un cours qui baisse, pas un dividende qui monte.",
    "Payout ratio": "Taux de distribution",
    "Share of earnings paid out.": "Part des bénéfices distribuée.",
    "Trailing where there is a trailing profit, else forward.":
        "Sur douze mois glissants s'il y a un bénéfice, sinon prévisionnel.",
    "Trailing / forward P/E": "PER glissant / prévisionnel",
    "Price / book": "Cours / actif net",
    "Return on equity": "Rentabilité des capitaux propres",
    "Operating margin": "Marge opérationnelle",
    "Profit margin": "Marge nette",
    "Debt / equity": "Dette / fonds propres",
    "Ratio, not percent.": "Un ratio, pas un pourcentage.",
    "Current ratio": "Ratio de liquidité générale",
    "Revenue growth": "Croissance du chiffre d'affaires",
    "Earnings growth": "Croissance des bénéfices",
    "Off 52-week high": "Sous le plus haut 52 sem.",
    "Above 52-week low": "Au-dessus du plus bas 52 sem.",
    "Small = the market may not have finished selling.":
        "Petit = le marché n'a peut-être pas fini de vendre.",
    "Beta": "Bêta",
    "Indicative, from the reported country of incorporation. Confirm with the broker.":
        "Indicatif, d'après le pays du siège déclaré. À confirmer auprès du courtier.",
    "Fundamentals fetched": "Fondamentaux collectés",
    "Dividend growth": "Croissance du dividende",
    "Forward annual dividend against the last twelve months actually paid.":
        "Dividende annuel annoncé contre celui réellement versé sur douze mois.",
    "Forward / trailing dividend": "Dividende annoncé / versé",
    "Per share, in the reporting currency. Their ratio is the growth figure above.":
        "Par action, dans la devise de publication. Leur ratio est le chiffre de croissance ci-dessus.",
    "Free-cash-flow payout": "Distribution / flux de trésorerie libre",
    "Dividends as a share of free cash flow. Earnings can be flattered; cash cannot.":
        "Dividendes en part du flux de trésorerie libre. Les bénéfices se maquillent, la trésorerie non.",
    "Free cash flow": "Flux de trésorerie libre",

    # Réglages
    "refreshing now": "rafraîchissement en cours",
    "last refreshed {when}": "dernier rafraîchissement {when}",
    "never refreshed": "jamais rafraîchi",
    "The four boards under Share Ideas rank a fixed list of shares and ETFs on figures fetched from Yahoo — free, without a key. The cache is refreshed once a day in the background; the first refresh runs a minute after start-up. A refresh is a few hundred requests with a pause between them and takes a few minutes, so it runs on its own and the boards fill in as it goes.":
        "Les quatre tableaux d'Idées d'actions classent une liste fixe d'actions et d'ETF sur des chiffres collectés chez Yahoo — gratuits, sans clé. Le cache est rafraîchi une fois par jour en arrière-plan ; le premier rafraîchissement démarre une minute après le lancement. Un rafraîchissement, ce sont quelques centaines de requêtes espacées d'une pause et quelques minutes, il tourne donc tout seul et les tableaux se remplissent au fur et à mesure.",
    "Shares: {n} cached, {errors} with a fetch error.":
        "Actions : {n} en cache, {errors} avec une erreur de collecte.",
    "ETFs: {n} cached, {errors} with a fetch error.":
        "ETF : {n} en cache, {errors} avec une erreur de collecte.",
    "To screen more names, or to correct an ETF's TER, edit screener_universe.json and screener_etf_universe.json in the data folder; thresholds live in screener.json beside them. All three are read on every page load.":
        "Pour passer plus de titres au crible, ou corriger le TER d'un ETF, modifiez screener_universe.json et screener_etf_universe.json dans le dossier de données ; les seuils sont dans screener.json à côté. Les trois sont relus à chaque chargement de page.",
    "Refresh share ideas now": "Rafraîchir les idées d'actions maintenant",
    "everything, not only what is older than a day":
        "tout, pas seulement ce qui date de plus d'un jour",
    "Refreshing the share ideas in the background. It takes a few minutes; the boards fill in as it goes.":
        "Rafraîchissement des idées d'actions en arrière-plan. Cela prend quelques minutes ; les tableaux se remplissent au fur et à mesure.",
    "A refresh is already running.": "Un rafraîchissement est déjà en cours.",

    # Filtres et alertes, formulés par le serveur
    "not a share ({type})": "pas une action ({type})",
    "no market cap": "pas de capitalisation",
    "too small ({bn}bn)": "trop petit ({bn} Md)",
    "no positive earnings": "pas de bénéfice positif",
    "P/E too high ({pe})": "PER trop élevé ({pe})",
    "pays no dividend": "ne verse pas de dividende",
    "token dividend ({pct}%)": "dividende symbolique ({pct} %)",
    "dividend not covered ({pct}% payout)": "dividende non couvert ({pct} % de distribution)",
    "near its 52-week low — still falling?": "près de son plus bas sur 52 semaines — chute encore ?",
    "payout ratio above 90% — dividend barely covered":
        "taux de distribution au-dessus de 90 % — dividende à peine couvert",
    "yield far above its own 5-year average — possible yield trap":
        "rendement bien au-dessus de sa moyenne sur 5 ans — piège à rendement possible",
    "no trailing profit — P/E is the forward estimate":
        "pas de bénéfice sur douze mois — le PER est l'estimation prévisionnelle",
    "earnings down {pct}% year on year": "bénéfices en baisse de {pct} % sur un an",
    "leveraged ({ratio}x debt/equity)": "endetté ({ratio}× dette/fonds propres)",
    "thin data — score built on few figures": "données minces — score bâti sur peu de chiffres",
    "yield too low for income ({pct}%)": "rendement trop bas pour du revenu ({pct} %)",
    "yield says distress ({pct}%)": "le rendement dit la détresse ({pct} %)",
    "payout leaves no headroom ({pct}%)": "la distribution ne laisse aucune marge ({pct} %)",
    "revenue shrinking ({pct}%)": "chiffre d'affaires en recul ({pct} %)",
    "forward dividend {pct}% BELOW the trailing one — a cut is already declared":
        "dividende annoncé {pct} % SOUS le précédent — une coupe est déjà déclarée",
    "dividend rate moved more than 50% — likely a special, or a change of payment frequency, not real growth":
        "dividende modifié de plus de 50 % — probablement un exceptionnel ou un changement de fréquence, pas une vraie croissance",
    "yield well above its own 5-year average — the price fell, the dividend did not rise":
        "rendement nettement au-dessus de sa moyenne sur 5 ans — le cours a baissé, le dividende n'a pas monté",
    "dividend costs {pct}% of free cash flow — paid out of the balance sheet, not out of the business":
        "le dividende coûte {pct} % du flux de trésorerie libre — payé avec le bilan, pas avec l'activité",
    "payout ratio {pct}% — little room for a bad year":
        "taux de distribution de {pct} % — peu de marge pour une mauvaise année",
    "near its 52-week low — the market is still selling":
        "près de son plus bas sur 52 semaines — le marché vend encore",
    "not a fund ({type})": "pas un fonds ({type})",
    "leveraged or inverse — a multi-year CAGR is meaningless":
        "à levier ou inversé — un rendement pluriannuel n'a aucun sens",
    "no TER known — add it to screener_etf_universe.json":
        "TER inconnu — à ajouter dans screener_etf_universe.json",
    "too expensive ({pct}% a year)": "trop cher ({pct} % par an)",
    "no price history": "pas d'historique de cours",
    "only {years} years of history": "seulement {years} ans d'historique",
    "fund too small ({m}m)": "fonds trop petit ({m} M)",
    "our TER {ours}% vs Yahoo's {theirs}% — likely a different share class; check the ISIN":
        "notre TER {ours} % contre {theirs} % chez Yahoo — probablement une autre classe de parts ; vérifiez l'ISIN",
    "TER is Yahoo's, not the KID's — verify before ranking on it":
        "le TER vient de Yahoo, pas du DIC — à vérifier avant de classer dessus",
    "returns are in {ccy}, not EUR — the FX series could not be fetched, so this row is not comparable with the rest":
        "rendements en {ccy}, pas en EUR — la série de change n'a pas pu être collectée, cette ligne n'est pas comparable aux autres",
    "under 5 years of history — growth is the 3-year figure alone":
        "moins de 5 ans d'historique — la croissance est le seul chiffre à 3 ans",
    "distributing — outside a tax wrapper each distribution is taxed in the year it is paid, so it compounds slower":
        "distribuant — hors enveloppe fiscale, chaque distribution est imposée l'année de son versement, la capitalisation est donc plus lente",
    "fell {pct}% peak to trough within this window":
        "a chuté de {pct} % du haut au bas dans cette fenêtre",
    "volatile ({pct}% a year)": "volatil ({pct} % par an)",
    "single theme or sector — a concentrated bet, not a core holding":
        "un seul thème ou secteur — un pari concentré, pas une position de fond",
    "fund size unknown — Yahoo reports none for this listing":
        "encours inconnu — Yahoo n'en donne aucun pour cette cotation",
    "US mutual fund — its annual distribution is mostly realised capital gains, not income":
        "fonds commun américain — sa distribution annuelle est surtout des plus-values réalisées, pas du revenu",
    "leveraged or inverse — not an income holding": "à levier ou inversé — pas une position de revenu",
    "no distribution data — the fetch has not run yet":
        "pas de données de distribution — la collecte n'a pas encore tourné",
    "accumulating — reinvests internally and pays no income":
        "capitalisant — réinvestit en interne et ne verse aucun revenu",
    "yield too low for an income holding ({pct}%)":
        "rendement trop bas pour une position de revenu ({pct} %)",
    "implausible yield ({pct}%) — a special distribution, a return of capital, or a stale price":
        "rendement invraisemblable ({pct} %) — une distribution exceptionnelle, un remboursement de capital ou un cours périmé",
    "only {years} years of price history": "seulement {years} ans d'historique de cours",
    "only {years} years of distributions — too short to tell a rising payout from a lucky one":
        "seulement {years} ans de distributions — trop court pour distinguer une distribution qui monte d'une distribution chanceuse",
    "listed as accumulating but has paid distributions — the universe entry is probably the wrong share class":
        "répertorié capitalisant mais a versé des distributions — l'entrée de l'univers est probablement la mauvaise classe de parts",
    "listed as distributing but has paid nothing in 12 months — probably the accumulating share class of the same fund":
        "répertorié distribuant mais n'a rien versé en 12 mois — probablement la classe capitalisante du même fonds",
    "our trailing yield {ours}% vs Yahoo's {theirs}% — check for a special distribution":
        "notre rendement {ours} % contre {theirs} % chez Yahoo — cherchez une distribution exceptionnelle",
    "paid {now} times this year vs {before} last — a schedule change, so the growth figure is not like-for-like":
        "versé {now} fois cette année contre {before} l'an passé — un changement de calendrier, le chiffre de croissance ne compare donc pas à périmètre égal",
    "has cut before — worst year was {pct}%": "a déjà coupé — la pire année a fait {pct} %",
    "distribution is shrinking ({pct}% year on year)": "la distribution rétrécit ({pct} % sur un an)",
    "the TER eats {pct}% of the income": "le TER mange {pct} % du revenu",
    "PEA-eligible — distributions inside a PEA are not taxed in the year they are paid, which matters more on an income holding than on an accumulating one":
        "éligible PEA — dans un PEA, les distributions ne sont pas imposées l'année de leur versement, ce qui compte plus pour une position de revenu que pour une capitalisante",
    "not PEA-eligible — in a plain broker account each distribution is taxed the year it is paid, so the headline yield is not the net one":
        "non éligible PEA — sur un compte-titres ordinaire, chaque distribution est imposée l'année de son versement, le rendement affiché n'est donc pas le net",
    "single sector — a concentrated bet, not a core income holding":
        "un seul secteur — un pari concentré, pas une position de revenu de fond",
    "the same fund is also listed as {others} — pick the listing your broker offers, they are not separate holdings":
        "le même fonds est aussi coté sous {others} — prenez la cotation que propose votre courtier, ce ne sont pas des positions distinctes",

    # ─── MCP ─────────────────────────────────────────────────────────
    'An assistant that speaks MCP can read this dashboard and do the chores that are slow by hand — categorise the queue and teach the rules, set budgets, type in a transaction, star a share idea, start a sync. It cannot delete an account, change settings, or see your bank credentials. Access is by a token, which stands in for your password: keep it as private, and revoke it here the moment you are unsure.':
        "Un assistant qui parle MCP peut lire ce tableau de bord et faire les corvées lentes à la main — catégoriser la file et apprendre les règles, fixer des budgets, saisir une opération, marquer une idée d'action, lancer une synchronisation. Il ne peut ni supprimer un compte, ni changer les réglages, ni voir vos identifiants bancaires. L'accès se fait par un jeton, qui tient lieu de mot de passe : gardez-le aussi secret, et révoquez-le ici au moindre doute.",
    'Claude and other assistants (MCP)': 'Claude et autres assistants (MCP)',
    'Create a token': 'Créer un jeton',
    'For Claude Code on your network, this is the whole setup:': 'Pour Claude Code sur votre réseau, voici toute la configuration :',
    'Replace the token': 'Remplacer le jeton',
    'Revoke': 'Révoquer',
    'Token created. Any earlier token stopped working.': 'Jeton créé. Tout jeton précédent ne fonctionne plus.',
    'Token revoked. Anything connected with it is cut off.': 'Jeton révoqué. Tout ce qui y était connecté est coupé.',
    'a token exists': 'un jeton existe',
    'off — no token': 'désactivé — pas de jeton',

    # ─── Saxo und Kraken ───────────────────────────────────────────────
    'API key': 'Clé API',
    'Add your Kraken API key under Settings first.': "Ajoutez d'abord votre clé API Kraken dans les Réglages.",
    "At developer.saxo → Apps, create an application: Live (or Simulation, to try it against Saxo's demo account), grant type Authorization Code, and this exact redirect URL:":
        "Sur developer.saxo → Apps, créez une application : Live (ou Simulation, pour l'essayer sur le compte de démonstration de Saxo), type d'octroi Authorization Code, et exactement cette URL de redirection :",
    'Broker connection': 'Connexion au courtier',
    'Connect Kraken': 'Connecter Kraken',
    'Connect Saxo': 'Connecter Saxo',
    'Connect Saxo again': 'Reconnecter Saxo',
    'Connected. Imported {n} transaction.': 'Connecté. {n} opération importée.',
    'Connected. Imported {n} transactions.': 'Connecté. {n} opérations importées.',
    'Environment': 'Environnement',
    'Finish by hand': 'Terminer à la main',
    'Forget Saxo': 'Oublier Saxo',
    'Forget the Kraken key': 'Oublier la clé Kraken',
    "It is your dashboard's address plus /saxo/callback, taken from the redirect URL above. If Saxo will not accept it, register it anyway and use “Finish by hand” on the account page.":
        "C'est l'adresse de votre tableau de bord suivie de /saxo/callback, dérivée de l'URL de redirection ci-dessus. Si Saxo la refuse, enregistrez-la quand même et utilisez « Terminer à la main » sur la page du compte.",
    'Kraken key forgotten. The account and its history stay.': 'Clé Kraken oubliée. Le compte et son historique restent.',
    'Kraken key works. Balances: {assets}. Now connect an account from its page.':
        'La clé Kraken fonctionne. Soldes : {assets}. Connectez maintenant un compte depuis sa page.',
    'Kraken needs an API key of your own: kraken.com → Settings → API → Add key. Give it only Query Funds, Query Closed Orders & Trades and Query Ledger Entries — nothing that can trade, withdraw or stake. A key that can only read cannot lose you a coin. Paste the key and the private key here; the private key is shown once when the key is created and is kept 0600 beside the bank key.':
        "Kraken demande une clé API à vous : kraken.com → Settings → API → Add key. Ne lui donnez que Query Funds, Query Closed Orders & Trades et Query Ledger Entries — rien qui puisse trader, retirer ou staker. Une clé qui ne peut que lire ne peut pas vous faire perdre une pièce. Collez ici la clé et la clé privée ; la clé privée n'est montrée qu'une fois à la création et est gardée en 0600 à côté de la clé bancaire.",
    'Kraken: link this account to the API key under Settings and pull every trade, deposit and reward.':
        'Kraken : liez ce compte à la clé API des Réglages et récupérez chaque trade, dépôt et récompense.',
    'Landed on a dead page after the Saxo login? Paste its address here.':
        'Arrivé sur une page morte après la connexion Saxo ? Collez son adresse ici.',
    'No code and state in that. Paste the whole address, including the ?code=… part.':
        "Ni code ni state là-dedans. Collez l'adresse entière, y compris la partie ?code=…",
    'Open a broker account here and press Connect Saxo.': 'Ouvrez ici un compte de courtier et appuyez sur « Connecter Saxo ».',
    'Paste the AppKey and the AppSecret below.': "Collez l'AppKey et l'AppSecret ci-dessous.",
    'Private key': 'Clé privée',
    'Read-only key; syncs with the daily sync.': 'Clé en lecture seule ; synchronisée avec la synchronisation quotidienne.',
    'Save Saxo credentials': 'Enregistrer les identifiants Saxo',
    'Save and check the key': 'Enregistrer et vérifier la clé',
    'Saxo Bank: log in at Saxo and this account becomes your first Saxo account; any others are created beside it.':
        'Saxo Bank : connectez-vous chez Saxo et ce compte devient votre premier compte Saxo ; les autres sont créés à côté.',
    'Saxo credentials saved. Now connect an account from its page.':
        'Identifiants Saxo enregistrés. Connectez maintenant un compte depuis sa page.',
    'Saxo forgotten. The accounts and their history stay.': 'Saxo oublié. Les comptes et leur historique restent.',
    'Saxo refused the login: {reason}': 'Saxo a refusé la connexion : {reason}',
    'Saxo sent us back without a code. Paste the address bar on the account page.':
        "Saxo nous a renvoyés sans code. Collez la barre d'adresse sur la page du compte.",
    "Saxo's OpenAPI is OAuth: you register an application of your own in Saxo's developer portal, paste its AppKey and AppSecret here, and connect an account from its page — Saxo's login, then straight back. The tokens Saxo hands out die within the hour, so the app renews them every five minutes while it runs; if it was down for longer, the account page says so and connecting again is one click.":
        "L'OpenAPI de Saxo est en OAuth : vous enregistrez une application à vous sur le portail développeur de Saxo, collez ici son AppKey et son AppSecret, et connectez un compte depuis sa page — la connexion Saxo, puis retour direct. Les jetons que Saxo délivre meurent en moins d'une heure, l'application les renouvelle donc toutes les cinq minutes tant qu'elle tourne ; si elle est restée arrêtée plus longtemps, la page du compte le dit et se reconnecter tient en un clic.",
    'Simulation': 'Simulation',
    'The Saxo login has lapsed — connect again to resume syncing.': 'La connexion Saxo a expiré — reconnectez-vous pour reprendre la synchronisation.',
    'The login is being kept alive.': 'La connexion est maintenue en vie.',
    'account {id}': 'compte {id}',
    'connected · client {id}': 'connecté · client {id}',
    'credentials saved, nothing connected yet': 'identifiants enregistrés, rien de connecté encore',
    'key saved': 'clé enregistrée',
    'login lapsed': 'connexion expirée',
    'not set up': 'non configuré',
    'simulation': 'simulation',

    # ─── Die Zeilen eines Wertpapiers ─────────────────────────────────
    'Amount in {currency}': 'Montant en {currency}',
    'Click a security to see, and correct, every row behind it.': 'Cliquez sur un titre pour voir, et corriger, chaque ligne derrière lui.',
    'Correct': 'Corriger',
    'Corrected.': 'Corrigé.',
    'Every row behind this holding': 'Chaque ligne derrière cette position',
    'Held': 'Détenu',
    'If a figure is wrong — a quantity a statement read badly, a price in the wrong currency — correct it here. A correction stays: the next import recognises the row and leaves it alone. Sizes are typed unsigned; the kind supplies the sign. The amount is the whole cash effect as the broker booked it, fees and taxes included.':
        "Si un chiffre est faux — une quantité mal lue sur un relevé, un cours dans la mauvaise devise — corrigez-le ici. Une correction reste : le prochain import reconnaît la ligne et la laisse tranquille. Les tailles se saisissent sans signe ; le type fournit le signe. Le montant est l'effet total en espèces tel que le courtier l'a comptabilisé, frais et impôts compris.",
    'No transaction carries that security.': 'Aucune opération ne porte ce titre.',
    'Remove this row': 'Supprimer cette ligne',
    'Save correction': 'Enregistrer la correction',
    'Security name': 'Nom du titre',
    'That transaction does not exist.': "Cette opération n'existe pas.",
    'Units': 'Unités',
    'at {price} on {date}': 'à {price} le {date}',
    'buys minus sales, fees included': 'achats moins ventes, frais compris',
    'corrected {date}': 'corrigé le {date}',
    'dividends and interest': 'dividendes et intérêts',
    'in': 'entrée',
    'no market price yet': 'pas encore de cours',
    'out': 'sortie',
    'the running sum of every row below': 'la somme cumulée de chaque ligne ci-dessous',
    'Collapse all': 'Tout replier',
    'Expand all': 'Tout déplier',
    'by year and month, newest first': 'par année et par mois, du plus récent au plus ancien',
    'everything': 'tout',
    'fee': 'frais',
    'tax': 'impôt',
    'the quantity as it ran': 'la quantité après cette ligne',
    '{amount} bought': '{amount} achetés',
    '{amount} paid out': '{amount} versés',
    '{amount} sold': '{amount} vendus',
    '{n} row': '{n} ligne',
    '{n} rows': '{n} lignes',

    # ─── Krypto, Kredite, Wertpapierseite ─────────────────────────────
    'Add a loan': 'Ajouter un prêt',
    'Add the loan': 'Ajouter le prêt',
    'Balance after': 'Capital restant',
    'Capital': 'Capital',
    'Change the terms, or delete': 'Modifier les conditions, ou supprimer',
    'Connect Kraken under Settings, or add a buy by hand on a broker account with CRYPTO:BTC as the ISIN.':
        'Connectez Kraken dans les Réglages, ou saisissez un achat à la main sur un compte de courtier avec CRYPTO:BTC comme ISIN.',
    'Cost basis': 'Prix de revient',
    'Crypto': 'Crypto',
    'Debt': 'Dettes',
    'Every': 'Tous les',
    "Every coin you hold, at today's price, with the wallet's value over time. Coins arrive from Kraken or from a row typed in by hand with the code as its ISIN — CRYPTO:BTC — and are priced from Yahoo like everything else.":
        "Chaque coin que vous détenez, au cours du jour, avec la valeur du portefeuille dans le temps. Les coins arrivent de Kraken ou d'une ligne saisie à la main avec le code comme ISIN — CRYPTO:BTC — et sont valorisés via Yahoo comme tout le reste.",
    'Extra': 'Remboursement anticipé',
    'Extra repayments': 'Remboursements anticipés',
    'First instalment': 'Première échéance',
    'Instalment': 'Échéance',
    'Interest': 'Intérêts',
    'Interest over the whole loan': 'Intérêts sur toute la durée',
    'Latest rows': 'Dernières lignes',
    'Loan added. Its balance is on the overview, and its history runs from the first instalment.': "Prêt ajouté. Son solde est sur la vue d'ensemble, et son historique court depuis la première échéance.",
    'Loan deleted, with its account.': 'Prêt supprimé, avec son compte.',
    'Loan or mortgage': 'Prêt ou hypothèque',
    'Loan updated.': 'Prêt mis à jour.',
    'Loans': 'Prêts',
    'Loans and mortgages': 'Prêts et hypothèques',
    'Mortgage, house': 'Prêt immobilier, maison',
    'No coins yet.': 'Pas encore de coins.',
    'No such coin is held.': "Ce coin n'est pas détenu.",
    'Notes': 'Notes',
    'Of': 'Sur',
    'Owed today': "Dû aujourd'hui",
    'Paid off': 'Remboursé le',
    'Price chart': 'Graphique du cours',
    "Price: Yahoo's daily close of the pair, in the base currency. Wallet: that price times the units held on each day, from the rows below — so a purchase shows as a step up and a sale as a step down.":
        "Cours : la clôture quotidienne de la paire chez Yahoo, dans la devise de base. Portefeuille : ce cours multiplié par les unités détenues chaque jour, d'après les lignes ci-dessous — un achat apparaît comme une marche vers le haut, une vente comme une marche vers le bas.",
    'Principal': 'Capital emprunté',
    'Rate, % per year': 'Taux, % par an',
    'Save the terms': 'Enregistrer les conditions',
    'Since the first purchase': 'Depuis le premier achat',
    'Still owed': 'Reste dû',
    'Term, months': 'Durée, mois',
    "The instalment is the figure on the contract. Leave it blank and give the term instead, and it is worked out as a constant annuity — the usual shape of a mortgage. Interest is rounded to the cent each period, the way a bank does it, so the schedule reproduces the bank's own figures.":
        "L'échéance est le chiffre du contrat. Laissez-la vide et donnez la durée à la place : elle est calculée en annuité constante — la forme habituelle d'un prêt immobilier. Les intérêts sont arrondis au centime à chaque période, comme le fait une banque, pour que le tableau reproduise ses propres chiffres.",
    'The schedule, instalment by instalment': "Le tableau d'amortissement, échéance par échéance",
    "Type the loan's name exactly to confirm the deletion.": 'Tapez le nom exact du prêt pour confirmer la suppression.',
    'Type “{name}” to delete this loan and its account': 'Tapez « {name} » pour supprimer ce prêt et son compte',
    'Unrealised gain': 'Plus-value latente',
    'Value is the units held times the price of the day — the market price where the app has one, the last price paid before that. Invested is buys minus sales, fees included. Dividends and interest are drawn as their own line, because they are return that never shows in the value.':
        "La valeur est le nombre d'unités détenues multiplié par le cours du jour — le cours de marché quand l'application en a un, le dernier prix payé avant cela. L'investi est achats moins ventes, frais compris. Dividendes et intérêts ont leur propre ligne, parce que c'est un rendement qui n'apparaît jamais dans la valeur.",
    'Wallet': 'Portefeuille',
    "What you owe, computed from the terms rather than typed in: the schedule gives the balance as of today, the overview subtracts it from the net worth, and nothing needs updating month by month. A balance typed in on the loan's account page — from the bank's letter — still wins on the day it is typed.":
        "Ce que vous devez, calculé d'après les conditions plutôt que saisi : le tableau d'amortissement donne le capital restant à ce jour, l'aperçu le retranche du patrimoine net, et rien n'est à mettre à jour mois après mois. Un solde saisi sur la page du compte du prêt — d'après la lettre de la banque — l'emporte quand même le jour où il est saisi.",
    'a mortgage, a car loan, a consumer credit — anything paid off in instalments':
        'un prêt immobilier, un crédit auto, un crédit à la consommation — tout ce qui se rembourse par échéances',
    'all instalments, as a monthly figure': 'toutes les échéances, ramenées au mois',
    'avg {price} per {code}': 'moy. {price} par {code}',
    'every row, and corrections': 'toutes les lignes, et les corrections',
    'loans and mortgages': 'prêts et hypothèques',
    'never at this payment': 'jamais avec cette échéance',
    'next {date}': 'prochaine le {date}',
    'no price history yet — it arrives with the next price refresh':
        "pas encore d'historique de cours — il arrive au prochain rafraîchissement des cours",
    'no price yet — it arrives with the next price refresh': 'pas encore de cours — il arrive au prochain rafraîchissement des cours',
    'no prices for this range': 'pas de cours sur cette période',
    'one per line: date and amount': 'un par ligne : date et montant',
    'or leave blank': 'ou laisser vide',
    'over the range': 'sur la période',
    'repaid': 'remboursé',
    'the account': 'le compte',
    'value plus income, against what went in, since {date}': 'valeur plus revenus, contre ce qui a été investi, depuis le {date}',
    'wallet value over the range — units bought or sold count too': 'valeur du portefeuille sur la période — les unités achetées ou vendues comptent aussi',
    'what it was worth against what went in, day by day': 'ce que ça valait contre ce qui a été investi, jour après jour',
    '{code} price': 'Cours {code}',
    '{interest} of it interest': "dont {interest} d'intérêts",
    '{n} instalment left': '{n} échéance restante',
    '{n} instalments left': '{n} échéances restantes',
    '{n} loan': '{n} prêt',
    '{n} loans': '{n} prêts',
    'Extra repayment {line}: write the date and the amount, like 2027-04-10 20000.':
        'Remboursement anticipé {line} : écrivez la date et le montant, comme 2027-04-10 20000.',
    'Give the payment per period, or the term in months to work it out.':
        "Donnez l'échéance par période, ou la durée en mois pour la calculer.",
    'Payments are monthly, quarterly, half-yearly or yearly.': 'Les échéances sont mensuelles, trimestrielles, semestrielles ou annuelles.',
    'That loan does not exist.': "Ce prêt n'existe pas.",
    'That payment does not even cover the interest — the loan would never end.':
        'Cette échéance ne couvre même pas les intérêts — le prêt ne finirait jamais.',
    'The first payment needs a date, written year-month-day.': "La première échéance a besoin d'une date, écrite année-mois-jour.",
    'The loan needs a name.': "Le prêt a besoin d'un nom.",
    'The principal must be a positive amount.': 'Le capital emprunté doit être un montant positif.',
    'The rate is a percentage per year, like 3.2.': 'Le taux est un pourcentage par an, comme 3.2.',
    'Last twelve months': 'Douze derniers mois',
    "Measured from {date}, day by day, on the prices the app has — backfilled to each security's first trade. A dash means there is nothing to measure yet.":
        "Mesuré depuis le {date}, jour par jour, sur les cours que l'application possède — récupérés jusqu'au premier achat de chaque titre. Un tiret signifie qu'il n'y a encore rien à mesurer.",
    'Money-weighted (MWR), a year': 'Pondéré par les capitaux (MWR), par an',
    'Money-weighted, a year.': 'Pondéré par les capitaux, par an.',
    'Money-weighted, the internal rate of return: the annual rate your own money earned, timing included — what a savings account would have had to pay.':
        "Pondéré par les capitaux, le taux de rendement interne : le taux annuel qu'a rapporté votre propre argent, moments des versements compris — ce qu'un livret aurait dû payer.",
    'Return': 'Rendement',
    'Return (TWR)': 'Rendement (TWR)',
    'Since the first trade': 'Depuis la première opération',
    'This year': 'Cette année',
    'Time-weighted (TWR)': 'Pondéré par le temps (TWR)',
    'Time-weighted, since the first purchase; a year when it is longer than one.':
        "Pondéré par le temps, depuis le premier achat ; par an au-delà d'un an.",
    'Time-weighted: the return of the investment itself, with the timing of your own money taken out — what compares one holding to another.':
        "Pondéré par le temps : le rendement du placement lui-même, sans l'effet du moment où votre argent est arrivé — ce qui permet de comparer une position à une autre.",
    'Your money (MWR)': 'Votre argent (MWR)',
    'a year': 'par an',
    'a year, on what went in and came out': 'par an, sur ce qui est entré et sorti',
    'since {date}': 'depuis le {date}',
    'the securities as one investment, in the base currency; cash left out on purpose':
        'les titres comme un seul placement, dans la devise de base ; les liquidités volontairement exclues',
    '{pct} % a year': '{pct} % par an',
    '{pct} % a year, since {date}': '{pct} % par an, depuis le {date}',
    # Realised gains, by lots (0.25.0)
    'All time': 'Depuis le début',
    'Average cost — every unit costs the average paid': 'Prix moyen pondéré — chaque titre coûte la moyenne payée',
    'Cost of those units': 'Coût de ces titres',
    'Each sale against the cost of the units it sold — the oldest units first under FIFO, every unit at the average paid under average cost. Proceeds and costs as the broker booked them, fees included; a position closed years ago still counts. Kept per currency: a gain in dollars is not a gain in euros without a rate, and this is the figure a tax form asks for.': 'Chaque vente contre le coût des titres vendus — les plus anciens d’abord en FIFO, chaque titre à la moyenne payée en prix moyen pondéré. Produit et coût tels que le courtier les a comptabilisés, frais compris ; une position fermée il y a des années compte toujours. Tenu par devise : un gain en dollars n’est pas un gain en euros sans taux, et c’est le chiffre que demande une déclaration fiscale.',
    'Each sale against the cost of the units it sold, lots kept per account — a unit bought at one broker is never sold at another. Under FIFO the oldest units go first, which is how Germany taxes; under average cost every unit costs the average paid, the French prix moyen pondéré. Units that arrived without a purchase — a transfer in — cost what their row says, or nothing; units that left without a sale realise nothing.': 'Chaque vente contre le coût des titres vendus, lots tenus par compte — un titre acheté chez un courtier n’est jamais vendu chez un autre. En FIFO les plus anciens partent d’abord, comme l’Allemagne impose ; en prix moyen pondéré chaque titre coûte la moyenne payée, la règle française. Les titres arrivés sans achat — un transfert entrant — coûtent ce que dit leur ligne, ou rien ; ceux partis sans vente ne réalisent rien.',
    'FIFO': 'FIFO',
    'FIFO — the oldest units are sold first': 'FIFO — les titres les plus anciens sont vendus d’abord',
    'Gain': 'Plus-value',
    'Proceeds': 'Produit',
    'Realised': 'Réalisé',
    'Realised gains': 'Plus-values réalisées',
    'Realised gains, by': 'Plus-values réalisées, selon',
    'Units sold': 'Titres vendus',
    'Unrealised': 'Latent',
    'Value minus what the units still held cost, by lots; minus net invested when there is no price by lots.': 'Valeur moins le coût des titres encore détenus, par lots ; moins le net investi quand il n’y a pas de prix par lots.',
    'What the sales of this security made, by lots.': 'Ce que les ventes de ce titre ont rapporté, par lots.',
    'Which units a sale sells decides what it made. FIFO is what Germany taxes on and what Portfolio Performance shows; average cost is the French prix moyen pondéré. Switzerland taxes no private capital gain, so a Swiss reader may pick either. Nothing is stored: switching recomputes every figure.': 'Les titres qu’une vente vend décident de ce qu’elle a rapporté. Le FIFO est ce sur quoi l’Allemagne impose et ce que montre Portfolio Performance ; le prix moyen pondéré est la règle française. La Suisse n’impose pas les gains en capital privés, un lecteur suisse peut donc choisir l’un ou l’autre. Rien n’est stocké : changer recalcule chaque chiffre.',
    'average cost': 'prix moyen pondéré',
    'change': 'changer',
    'cost {amount}': 'coût {amount}',
    'units held cost {amount}, {avg} each': 'les titres détenus ont coûté {amount}, {avg} chacun',
    'what the sales made, by lots': 'ce que les ventes ont rapporté, par lots',
    '{amount} realised': '{amount} réalisé',
    '{amount} unrealised': '{amount} latent',
    '{n} sale': '{n} vente',
    '{n} sales': '{n} ventes',
    # A CSV mapped by hand (0.26.0)
    'A date column and an amount column — or a debit and a credit column — are the least a mapping needs.': 'Une colonne de date et une colonne de montant — ou une colonne débit et une colonne crédit — sont le minimum qu’une correspondance demande.',
    'A file with one of these headers is imported through its mapping without asking. Forget one and the next such file asks again — the rows already imported stay.': 'Un fichier portant l’un de ces en-têtes est importé par sa correspondance sans rien demander. Oubliez-en une et le prochain fichier de ce type redemande — les lignes déjà importées restent.',
    'Amount, signed': 'Montant, signé',
    'Any other bank': 'Toute autre banque',
    'Blank means the ISIN is looked for in the description.': 'Vide : l’ISIN est cherché dans le libellé.',
    "Blank means the account's currency, or the one typed in below.": 'Vide : la devise du compte, ou celle saisie ci-dessous.',
    'Buy, sell, dividend, interest, fee, tax, deposit, withdrawal or transfer — in English, German, French or Spanish. Left blank, the kind is worked out from the row: an ISIN and units is a trade, an ISIN and money in a dividend, plain money a deposit or a withdrawal.': 'Achat, vente, dividende, intérêts, frais, impôt, dépôt, retrait ou transfert — en anglais, allemand, français ou espagnol. Laissé vide, le type est déduit de la ligne : un ISIN et des titres est une opération, un ISIN et de l’argent entrant un dividende, de l’argent seul un dépôt ou un retrait.',
    'CSV mappings': 'Correspondances CSV',
    'Call this mapping': 'Nom de cette correspondance',
    'Cancel': 'Annuler',
    'Columns': 'Colonnes',
    'Credit (money in)': 'Crédit (argent entrant)',
    'Currency when the file has no column for it': 'Devise quand le fichier n’a pas de colonne pour elle',
    'Debit (money out)': 'Débit (argent sortant)',
    "Export the transactions as CSV and drop the file in. If no importer knows it you are asked, once, which column is the date, the amount and so on; the mapping is remembered under the file's header, so the next export from that bank goes straight in.": 'Exportez les opérations en CSV et déposez le fichier ici. Si aucun importateur ne le connaît, on vous demande, une fois, quelle colonne est la date, le montant et ainsi de suite ; la correspondance est retenue sous l’en-tête du fichier, et le prochain export de cette banque entre directement.',
    'Forget': 'Oublier',
    'If a kind, a sign or a date looks wrong here it will be wrong in the account: change the mapping and look again before importing. Every row is imported; a row without a readable date is listed and left out.': 'Si un type, un signe ou une date semble faux ici, il sera faux dans le compte : changez la correspondance et regardez à nouveau avant d’importer. Chaque ligne est importée ; une ligne sans date lisible est listée et laissée de côté.',
    'Map the columns': 'Faire correspondre les colonnes',
    'Mapping forgotten. The next file with that header asks again.': 'Correspondance oubliée. Le prochain fichier avec cet en-tête redemandera.',
    'Money in positive, money out negative. If the file has one column for each, leave this blank and map the two below.': 'Argent entrant positif, sortant négatif. Si le fichier a une colonne pour chacun, laissez ceci vide et remplissez les deux ci-dessous.',
    "No importer here knows this file, and it does not need to: say which column is which, once. The mapping is kept under the file's header, so the next export from the same bank is recognised by itself — like a Degiro file is.": 'Aucun importateur ici ne connaît ce fichier, et ce n’est pas nécessaire : dites une fois quelle colonne est quoi. La correspondance est gardée sous l’en-tête du fichier, et le prochain export de la même banque est reconnu tout seul — comme l’est un fichier Degiro.',
    'Not one row could be read through that mapping.': 'Pas une ligne n’a pu être lue avec cette correspondance.',
    'Nothing readable yet — the date or the amount column is not the right one.': 'Rien de lisible encore — la colonne de date ou de montant n’est pas la bonne.',
    'Only when there is no signed amount column.': 'Seulement s’il n’y a pas de colonne de montant signé.',
    'Read through this mapping': 'Lu avec cette correspondance',
    'Save the mapping and import': 'Enregistrer la correspondance et importer',
    'Show me the first rows': 'Montrer les premières lignes',
    'Since': 'Depuis',
    'That upload has expired — choose the file again.': 'Cet envoi a expiré — choisissez le fichier à nouveau.',
    'The file': 'Le fichier',
    'The file writes money out as positive — flip every sign': 'Le fichier écrit l’argent sortant en positif — inverser chaque signe',
    "The kind gives the sign: a buy's units come in, a sale's go out.": 'Le type donne le signe : les titres d’un achat entrent, ceux d’une vente sortent.',
    'The mapping is saved as {name}; the next file with this header is recognised by itself.': 'La correspondance est enregistrée sous {name} ; le prochain fichier avec cet en-tête est reconnu tout seul.',
    'What the row says; the counterparty stands in when this is blank.': 'Ce que dit la ligne ; la contrepartie prend le relais quand c’est vide.',
    'Which column is which': 'Quelle colonne est quoi',
    'Who paid or was paid.': 'Qui a payé ou a été payé.',
    'Written year-month-day, day.month.year or day/month/year. A US month-first date is not guessed.': 'Écrite année-mois-jour, jour.mois.année ou jour/mois/année. Une date américaine mois d’abord n’est pas devinée.',
    'columns': 'colonnes',
    'saved as {name} — this changes it': 'enregistrée sous {name} — ceci la modifie',
    'separated by {delimiter}': 'séparées par {delimiter}',
    'the bank, say': 'la banque, par exemple',
    'the first rows, as they would be imported': 'les premières lignes, telles qu’elles seraient importées',
    '{n} file layout you mapped yourself': '{n} format de fichier que vous avez défini vous-même',
    '{n} file layouts you mapped yourself': '{n} formats de fichier que vous avez définis vous-même',
    # CSV export (0.26.0)
    'Every row these filters match, not just the ones shown, in a file a spreadsheet opens right.': 'Chaque ligne que ces filtres retiennent, pas seulement celles affichées, dans un fichier qu’un tableur ouvre correctement.',
    'Export as CSV': 'Exporter en CSV',
    'This table with every figure on it — price, value, gains, TWR and MWR — in a file a spreadsheet opens right.': 'Ce tableau avec chaque chiffre — cours, valeur, plus-values, TWR et MWR — dans un fichier qu’un tableur ouvre correctement.',
    # Stock splits (0.27.0)
    "A split adds a row per account — the units that appeared, at no cost — so the quantity above is right from that day on. Earlier rows keep the units and prices of their day; the chart values them in today's units, as Yahoo's history is, and a lot keeps its cost, so a later sale realises the same gain it would have in the old units. Write 1:10 for a reverse split.": 'Une division ajoute une ligne par compte — les titres apparus, sans coût — pour que la quantité ci-dessus soit juste à partir de ce jour. Les lignes antérieures gardent les titres et les cours de leur jour ; le graphique les valorise en titres d’aujourd’hui, comme l’historique de Yahoo, et un lot garde son coût, si bien qu’une vente ultérieure réalise la même plus-value qu’en anciens titres. Écrivez 1:10 pour un regroupement.',
    'New for old': 'Nouveaux pour anciens',
    'Nothing was held on that day — or that split is already recorded.': 'Rien n’était détenu ce jour-là — ou cette division est déjà enregistrée.',
    'Record a split': 'Enregistrer une division',
    'Record the split': 'Enregistrer la division',
    'Split recorded on {n} account.': 'Division enregistrée sur {n} compte.',
    'Split recorded on {n} accounts.': 'Division enregistrée sur {n} comptes.',
    'split [kind]': 'Division',
    'when the units changed and the money did not': 'quand les titres ont changé et pas l’argent',
    'Write the split as new for old, like 44:1 — or 1:10 for a reverse split.': 'Écrivez la division en nouveaux pour anciens, comme 44:1 — ou 1:10 pour un regroupement.',
    # Sidebar navigation and the three stages (0.28.0)
    'A month, in {currency}': 'Par mois, en {currency}',
    'A year of returns and a year of savings are of the same order — anywhere from half to twice each other. The crossover, where they are equal, is here. Both levers matter now, and a bad year can undo a year of saving.': 'Une année de rendement et une année d’épargne sont du même ordre — entre la moitié et le double l’une de l’autre. Le croisement, où elles sont égales, est ici. Les deux leviers comptent désormais, et une mauvaise année peut défaire une année d’épargne.',
    'A year of returns is less than half of what you put in. The monthly amount is the lever; the return barely moves the needle yet. Keep it boring and keep it up.': 'Une année de rendement fait moins de la moitié de ce que vous versez. Le montant mensuel est le levier ; le rendement bouge à peine l’aiguille. Restez ennuyeux et tenez bon.',
    'A year of returns is more than twice what you put in. The pile carries itself; what you add is a rounding error against what the market does. From here on, the risk you carry matters more than the amount you save.': 'Une année de rendement fait plus du double de ce que vous versez. Le tas se porte lui-même ; ce que vous ajoutez est une erreur d’arrondi face à ce que fait le marché. Dès lors, le risque que vous portez compte plus que le montant que vous épargnez.',
    'As it went': 'Comme c’est allé',
    'Back to the plan': 'Retour au plan',
    'Close the menu': 'Fermer le menu',
    'Collapse the menu': 'Replier le menu',
    'Compounding carries it': 'Les intérêts composés le portent',
    'Crossover': 'Croisement',
    'Early on, what you put in is what grows the pile. Later the two pull together. Later still the return on what is there outweighs anything you could add, and the pile carries itself. One ratio tells them apart: what the market does in a year against what you put in in a year.': 'Au début, ce que vous versez est ce qui fait grossir le tas. Plus tard, les deux tirent ensemble. Plus tard encore, le rendement de ce qui est là dépasse tout ce que vous pourriez ajouter, et le tas se porte lui-même. Un seul ratio les distingue : ce que fait le marché en un an face à ce que vous versez en un an.',
    'End of year': 'Fin d’année',
    'Expected return, % a year': 'Rendement attendu, % par an',
    'Investing': 'Investir',
    'Market did': 'Le marché a fait',
    'Market did is the value at the end of the year minus the value at the start minus what went in, plus the dividends and interest paid out — everything the money did that you did not do. A single year says little: a bad year in stage 3 looks like stage 1, and that is the point of stage 3.': '« Le marché a fait » est la valeur en fin d’année moins la valeur en début d’année moins ce qui a été versé, plus les dividendes et intérêts perçus — tout ce que l’argent a fait que vous n’avez pas fait. Une seule année dit peu : une mauvaise année en étape 3 ressemble à l’étape 1, et c’est tout l’intérêt de l’étape 3.',
    'Money': 'Argent',
    "Monthly compounding at the rate given, contributions at the end of each month — the same arithmetic as the Forecast. A rate is an assumption, not a promise: the world's stock market has averaged about 7 % a year over a century, with decades on either side of it.": 'Capitalisation mensuelle au taux donné, versements en fin de mois — la même arithmétique que la Projection. Un taux est une hypothèse, pas une promesse : le marché mondial des actions a fait environ 7 % par an sur un siècle, avec des décennies de part et d’autre.',
    'Navigation': 'Navigation',
    'No securities records yet.': 'Pas encore de données de titres.',
    'No securities yet. The stages begin with the first purchase.': 'Pas encore de titres. Les étapes commencent avec le premier achat.',
    "Nothing goes in a month, so everything the pile does from here is the market's — stage 3 by definition, but of a pile that only grows if the market does.": 'Rien n’entre par mois, donc tout ce que le tas fait à partir d’ici est l’affaire du marché — étape 3 par définition, mais d’un tas qui ne grossit que si le marché le fait.',
    'On the plan, year by year': 'Sur le plan, année par année',
    'Open the menu': 'Ouvrir le menu',
    'Paid out': 'Perçu',
    'Planning': 'Planifier',
    'Put in': 'Versé',
    'Ratio': 'Ratio',
    'Returns equal your savings — the crossover': 'Le rendement égale votre épargne — le croisement',
    'Returns reach half your savings': 'Le rendement atteint la moitié de votre épargne',
    'Returns reach twice your savings — compounding takes over': 'Le rendement atteint le double de votre épargne — les intérêts composés prennent le relais',
    'Saving and returns pull together': 'Épargne et rendement tirent ensemble',
    'Saving builds it': 'L’épargne le construit',
    'Stage': 'Étape',
    'Stage {n}': 'Étape {n}',
    'Stages': 'Étapes',
    'Start of year': 'Début d’année',
    'The last twelve months, {amount} a month actually went into securities.': 'Ces douze derniers mois, {amount} par mois sont réellement allés en titres.',
    "The plan's figures come from the Forecast page, so they are set once.": 'Les chiffres du plan viennent de la page Projection, pour n’être réglés qu’une fois.',
    'The three stages': 'Les trois étapes',
    'Tried, not kept.': 'Essayé, pas gardé.',
    'Try it': 'Essayer',
    'Where you stand': 'Où vous en êtes',
    'every year the app has records of — what you put in against what the market did': 'chaque année dont l’app a des données — ce que vous avez versé face à ce que le marché a fait',
    'in {year}, at about {value}': 'en {year}, à environ {value}',
    'not within fifty years on these figures': 'pas d’ici cinquante ans avec ces chiffres',
    'over {x}×': 'au-delà de {x}×',
    'returns under {x}× savings': 'rendement sous {x}× l’épargne',
    'so far': 'à ce jour',
    "the wealth at which a year of returns pays a year of savings — twelve months' saving divided by the rate": 'le patrimoine auquel une année de rendement paie une année d’épargne — douze mois d’épargne divisés par le taux',
    'what goes in against what the market does, until compounding has been in charge for five years': 'ce qui entre face à ce que fait le marché, jusqu’à ce que les intérêts composés aient mené pendant cinq ans',
    '{a}× to {b}×': '{a}× à {b}×',
    '{value} in securities at {rate} % expected is {returns} a year; {monthly} a month is {saved} a year — a ratio of {ratio}.': '{value} en titres à {rate} % attendus font {returns} par an ; {monthly} par mois font {saved} par an — un ratio de {ratio}.',
    # Corrections over the MCP (0.28.1)
    'Nothing to change.': 'Rien à changer.',
    'Transaction {id} does not exist.': 'La transaction {id} n’existe pas.',
    '{what} cannot be changed here.': '{what} ne peut pas être modifié ici.',
    '{what} is not a number.': '{what} n’est pas un nombre.',
    # MCP setup notes (0.28.2)
    'For Claude Desktop, which only speaks to local processes, the mcp-remote bridge carries the same URL and header. This goes into claude_desktop_config.json under mcpServers:': 'Pour Claude Desktop, qui ne parle qu’à des processus locaux, la passerelle mcp-remote porte la même URL et le même en-tête. Ceci va dans claude_desktop_config.json sous mcpServers :',
    "Two things that cost people an afternoon. The URL is the one the browser reaches the dashboard at: behind a reverse proxy that is the https:// address, not the container's http:// one — the address above is what this page was opened at, so it is right if this page was. And --transport http-only matters: without it mcp-remote first tries the older SSE transport, which this endpoint does not speak, and reports a connection failure that is not one.": 'Deux choses qui coûtent un après-midi. L’URL est celle à laquelle le navigateur atteint le tableau de bord : derrière un proxy inverse, c’est l’adresse https://, pas l’adresse http:// du conteneur — l’adresse ci-dessus est celle à laquelle cette page a été ouverte, elle est donc bonne si cette page l’est. Et --transport http-only compte : sans lui, mcp-remote essaie d’abord l’ancien transport SSE, que ce point d’accès ne parle pas, et signale un échec de connexion qui n’en est pas un.',
    # A share quoted in another currency (0.28.3)
    'quoted {price} {currency}': 'coté {price} {currency}',
    "A price quoted in another currency than the shares were paid in is turned into theirs at the day's ECB rate, so the lines are one currency.": 'Un cours coté dans une autre devise que celle où les titres ont été payés est converti dans celle-ci au taux BCE du jour, pour que les courbes soient d’une seule devise.',
    'fees {fees}, tax {taxes} paid': '{fees} de frais, {taxes} d’impôt payés',
    # Currency switch on the security page (0.29.0)
    'Show in': 'Afficher en',
    'base': 'base',
    "every amount at its own day's ECB rate; today's price at today's. The rows below stay as booked, in {currency}.": 'chaque montant au taux BCE de son jour ; le cours d’aujourd’hui à celui d’aujourd’hui. Les lignes ci-dessous restent telles que comptabilisées, en {currency}.',
    'paid in': 'payé en',
    'quoted in': 'coté en',
    # Settings in chapters, rules with terms (0.30.0)
    'Add the rule': 'Ajouter la règle',
    'Assistants': 'Assistants',
    'Banks & brokers': 'Banques & courtiers',
    'Prices & rates': 'Cours & taux',
    'Rule changed and every rule re-applied, oldest first.': 'Règle modifiée et chaque règle réappliquée, la plus ancienne d’abord.',
    'Settings chapters': 'Chapitres des réglages',
    'That rule does not exist.': 'Cette règle n’existe pas.',
    'The text is matched anywhere in the description or the counterparty, or in one of them; the amounts are sizes — 20 to 50 catches a payment of 30 whichever way it went, and the direction says which way. Blank means no limit. A rule applies to what is already imported as well as to what arrives next.': 'Le texte est cherché n’importe où dans le libellé ou la contrepartie, ou dans l’un des deux ; les montants sont des tailles — 20 à 50 attrape un paiement de 30 dans un sens comme dans l’autre, et le sens dit lequel. Vide signifie sans limite. Une règle s’applique à ce qui est déjà importé comme à ce qui arrive ensuite.',
    'When': 'Quand',
    'and the money is': 'et l’argent est',
    'contains': 'contient',
    'from': 'de',
    'in or out': 'entrant ou sortant',
    'money in': 'argent entrant',
    'money out': 'argent sortant',
    'the counterparty': 'la contrepartie',
    'the description': 'le libellé',
    'the text anywhere': 'le texte n’importe où',
    'to': 'à',
    # Allocation (0.31.0)
    'About to invest, in {currency}': 'Sur le point d’investir, en {currency}',
    'Allocation': 'Allocation',
    'Asset class': 'Classe d’actifs',
    'Bucket': 'Poche',
    'Buy': 'Acheter',
    'Buying only: the keys below their target get the amount in proportion to how far below they are.': 'Achats seulement : les clés sous leur cible reçoivent le montant en proportion de leur retard.',
    'By asset class': 'Par classe d’actifs',
    'By bucket': 'Par poche',
    'By region': 'Par région',
    "Cash is every account balance; the rest is each holding's class.": 'Le cash est le solde de chaque compte ; le reste est la classe de chaque position.',
    'Classification saved.': 'Classification enregistrée.',
    'Drift': 'Écart',
    'Key': 'Clé',
    'Nothing to allocate yet — no holdings and no cash balance.': 'Rien à allouer encore — pas de positions ni de solde.',
    'Save targets': 'Enregistrer les cibles',
    'Share': 'Part',
    'Spread it': 'Répartir',
    'Target': 'Cible',
    'Targets saved.': 'Cibles enregistrées.',
    'What each holding is': 'Ce qu’est chaque position',
    'Where a fund invests, or where a share is listed — guessed from the name and the ISIN, yours to correct.': 'Où un fonds investit, ou où une action est cotée — deviné d’après le nom et l’ISIN, à vous de corriger.',
    'Where the money is by what it is — asset class, region, and buckets of your own — against where you meant it to be. Set a target per key and the page shows the drift; give it the amount you are about to invest and it says how to spread it so the drift shrinks, without selling anything.': 'Où est l’argent selon ce qu’il est — classe d’actifs, région, et des poches à vous — face à où il devait être. Fixez une cible par clé et la page montre l’écart ; donnez-lui le montant que vous allez investir et elle dit comment le répartir pour réduire l’écart, sans rien vendre.',
    'Your own taxonomy — Core and Satellite, Safe and Play, whatever you think in. Nothing is guessed here.': 'Votre propre taxonomie — Cœur et Satellite, Sûr et Jeu, ce en quoi vous pensez. Rien n’est deviné ici.',
    'a bucket, like Core': 'une poche, comme Cœur',
    'add a target for…': 'ajouter une cible pour…',
    'Asia Pacific [region]': 'Asie-Pacifique',
    'Bonds [class]': 'Obligations',
    'Cash [class]': 'Cash',
    'Commodities [class]': 'Matières premières',
    'Crypto [class]': 'Crypto',
    'Emerging markets [region]': 'Émergents',
    'Equity [class]': 'Actions',
    'Europe [region]': 'Europe',
    'Germany [region]': 'Allemagne',
    'guessed': 'deviné',
    "guessed from the name and Yahoo's type; a guess is marked until you confirm it": 'deviné d’après le nom et le type Yahoo ; une supposition est marquée jusqu’à ce que vous la confirmiez',
    'no targets yet': 'pas encore de cibles',
    'North America [region]': 'Amérique du Nord',
    'Other [class]': 'Autre',
    'Other [region]': 'Autre',
    'Real estate [class]': 'Immobilier',
    'Switzerland [region]': 'Suisse',
    'targets set for {pct} %': 'cibles fixées pour {pct} %',
    'unassigned': 'non attribué',
    'World [region]': 'Monde',
    '{amount} to target': '{amount} jusqu’à la cible',
    '{total} in total — {cash} of it cash.': '{total} au total — dont {cash} de cash.',
    'A target is a percentage between 0 and 100.': 'Une cible est un pourcentage entre 0 et 100.',
    'The targets add up to more than a hundred percent.': 'Les cibles totalisent plus de cent pour cent.',
    # Rules that do more, and tags (0.32.0)
    'A rule can also rename the counterparty — AMZN Mktp DE*2K3 becomes Amazon — set the kind, to mark a transfer between your own accounts, say, and add a tag; those three are applied on every sync, so they win over a correction by hand.': 'Une règle peut aussi renommer la contrepartie — AMZN Mktp DE*2K3 devient Amazon —, fixer le type, pour marquer un virement entre vos propres comptes par exemple, et ajouter une étiquette ; ces trois actions s’appliquent à chaque synchronisation et l’emportent donc sur une correction à la main.',
    'A rule has to do something: file under a category, rename the counterparty, set the kind, or add a tag.': 'Une règle doit faire quelque chose : classer sous une catégorie, renommer la contrepartie, fixer le type ou ajouter une étiquette.',
    'Tag': 'Étiquette',
    'Tags': 'Étiquettes',
    'That pattern is not a valid regular expression: {error}': 'Ce motif n’est pas une expression régulière valide : {error}',
    'add the tag': 'ajouter l’étiquette',
    'is exactly': 'est exactement',
    'leave the category': 'laisser la catégorie',
    'matches the pattern': 'correspond au motif',
    'of kind': 'de type',
    'on account': 'sur le compte',
    'rename the counterparty to': 'renommer la contrepartie en',
    'set the kind to': 'fixer le type à',
    'starts with': 'commence par',
    'tags, comma-separated': 'étiquettes, séparées par des virgules',
    'then file under': 'puis classer sous',
    # Benchmark (0.33.0)
    'Against a benchmark': 'Face à un indice de référence',
    'Nothing to compare yet.': 'Rien à comparer encore.',
    "The portfolio line is the time-weighted return: every deposit counts from the day it arrived and every withdrawal stops counting the day it left, so investing bit by bit does not put you behind the index here — what is compared is how the investments did, not when your money came. The return that does feel the timing is the money-weighted one on the Portfolio page. The index is turned into the portfolio's currency at each day's rate; where Yahoo has no clean index in euros an accumulating ETF stands in. Nothing is stored but the index's daily closes.": 'La courbe du portefeuille est le rendement pondéré dans le temps : chaque versement compte à partir du jour où il est arrivé et chaque retrait cesse de compter le jour où il est parti — investir petit à petit ne vous met donc pas derrière l’indice ici. Ce qui est comparé, c’est la performance des placements, pas le moment où l’argent est venu. Le rendement qui ressent le timing est le rendement pondéré par l’argent, sur la page Portefeuille. L’indice est converti dans la devise du portefeuille au taux de chaque jour ; là où Yahoo n’a pas d’indice propre en euros, un ETF capitalisant le remplace. Rien n’est stocké hormis les clôtures quotidiennes de l’indice.',
    'Yahoo has no history for {symbol} over this span.': 'Yahoo n’a pas d’historique pour {symbol} sur cette période.',
    'You': 'Vous',
    'ahead by {pct} points': '{pct} points d’avance',
    'another symbol…': 'un autre symbole…',
    'behind by {pct} points': '{pct} points de retard',
    'time-weighted, both at 100 on the first day': 'pondéré dans le temps, tous deux à 100 le premier jour',
    'you': 'vous',
    # Bills and goals (0.34.0)
    'A bill needs a name and at least three characters of text to recognise it by.': 'Une facture a besoin d’un nom et d’au moins trois caractères de texte pour la reconnaître.',
    'A goal needs a name and a positive amount.': 'Un objectif a besoin d’un nom et d’un montant positif.',
    'Active': 'Active',
    'Add a bill': 'Ajouter une facture',
    'Add a goal': 'Ajouter un objectif',
    'Add the bill': 'Ajouter la facture',
    'Add the goal': 'Ajouter l’objectif',
    'An amount by a date, and how it is going. A goal is fed by an account — the holiday account, whose balance is the progress — or by hand, an amount at a time, for a goal that lives inside a bigger account.': 'Un montant pour une date, et où ça en est. Un objectif est alimenté par un compte — le compte vacances, dont le solde est la progression — ou à la main, montant par montant, pour un objectif qui vit dans un compte plus grand.',
    'Bill added.': 'Facture ajoutée.',
    'Bill removed.': 'Facture supprimée.',
    'Bill saved.': 'Facture enregistrée.',
    'Bills': 'Factures',
    'By': 'Pour le',
    'Change the goal': 'Modifier l’objectif',
    'Due day': 'Jour d’échéance',
    'Due within a week': 'À payer sous une semaine',
    'Every bill': 'Toutes les factures',
    'Fed by an account': 'Alimenté par un compte',
    'Fixed costs a month': 'Charges fixes par mois',
    'Goal added.': 'Objectif ajouté.',
    'Goal removed.': 'Objectif supprimé.',
    'Goal saved.': 'Objectif enregistré.',
    'Goals': 'Objectifs',
    'Missed': 'Manquées',
    'No goals yet.': 'Pas encore d’objectif.',
    'Note it': 'Noter',
    'Noted.': 'Noté.',
    'Put towards it': 'Y mettre',
    'Savings goals': 'Objectifs d’épargne',
    'Text that identifies it': 'Texte qui l’identifie',
    'That bill does not exist.': 'Cette facture n’existe pas.',
    'That goal does not exist.': 'Cet objectif n’existe pas.',
    'The text is looked for in the counterparty and the description of money going out; an amount, if given, allows a fifth either way — utilities vary. The due day snaps the next date to the day of the month the bill is usually taken.': 'Le texte est cherché dans la contrepartie et le libellé des sorties d’argent ; un montant, s’il est donné, tolère un cinquième dans chaque sens — les charges varient. Le jour d’échéance cale la prochaine date sur le jour du mois où la facture est habituellement prélevée.',
    'What is expected to leave the account, and whether it did. A subscription is found; a bill is declared — the rent, the insurance, the electricity — and matched against the rows as they arrive, so this page can say paid, due, or missed.': 'Ce qui doit quitter le compte, et si c’est arrivé. Un abonnement se détecte ; une facture se déclare — le loyer, l’assurance, l’électricité — et se rapproche des lignes au fur et à mesure, pour que cette page dise payée, à payer ou manquée.',
    'by hand': 'à la main',
    'by {date}': 'pour le {date}',
    'due': 'à payer',
    'fed by hand': 'alimenté à la main',
    'fed by {account}': 'alimenté par {account}',
    'last {date}, {amount}': 'dernière le {date}, {amount}',
    'make it a bill': 'en faire une facture',
    'missed': 'manquée',
    'more than the {plan} a month of your plan': 'plus que les {plan} par mois de votre plan',
    'never seen': 'jamais vue',
    'next {date}, in {n} days': 'prochaine le {date}, dans {n} jours',
    'next: {name}, {date}': 'prochaine : {name}, le {date}',
    'no payment matched yet': 'aucun paiement rapproché encore',
    'or adopt one the app detected': 'ou en adopter une détectée',
    'paid': 'payée',
    'past due by more than a week, nothing seen since': 'en retard de plus d’une semaine, rien vu depuis',
    'reached': 'atteint',
    'the date has passed': 'la date est passée',
    'was due {date}, {n} days ago': 'attendue le {date}, il y a {n} jours',
    '{amount} a month for {n} months reaches it': '{amount} par mois pendant {n} mois y arrive',
    '{amount} to go': '{amount} restants',
    '{n} active bill': '{n} facture active',
    '{n} active bills': '{n} factures actives',
    '{n} payment seen': '{n} paiement vu',
    '{n} payments seen': '{n} paiements vus',
    # Dividend calendar (0.35.0)
    'By security': 'Par titre',
    'By year': 'Par année',
    'Coming up': 'À venir',
    'Dividend calendar': 'Calendrier des dividendes',
    'Ex-date': 'Date ex-dividende',
    'Expected': 'Attendu',
    'Expected, 12 months': 'Attendu, 12 mois',
    'Expected, next twelve months': 'Attendu, douze prochains mois',
    'Month by month': 'Mois par mois',
    'Next ex-date': 'Prochaine date ex-dividende',
    'No dividends received yet, and nothing expected — either no holding pays out, or Yahoo has not been asked yet.': 'Aucun dividende reçu encore, et rien d’attendu — soit aucune position ne distribue, soit Yahoo n’a pas encore été interrogé.',
    'Per month, expected': 'Par mois, attendu',
    'Per share': 'Par action',
    'Per share, a year': 'Par action, par an',
    'Received': 'Reçu',
    'Received, 12 months': 'Reçu, 12 mois',
    'Received, all': 'Reçu, en tout',
    'Received, last twelve months': 'Reçu, douze derniers mois',
    "What the holdings paid out, month by month, and what is due in the next twelve: each holding's payments of the last year, times the units held today, a year on. A calendar, not a forecast — it assumes every payer keeps paying what it paid.": 'Ce que les positions ont versé, mois par mois, et ce qui est dû dans les douze prochains : les versements de chaque position sur la dernière année, fois les titres détenus aujourd’hui, un an plus tard. Un calendrier, pas une prévision — il suppose que chaque payeur continue de payer ce qu’il a payé.',
    "Yield on today's value": 'Rendement sur la valeur d’aujourd’hui',
    'averaged over the year': 'en moyenne sur l’année',
    "by ex-date, from last year's dates": 'par date ex-dividende, d’après les dates de l’an dernier',
    'from {n} payer': 'de {n} payeur',
    'from {n} payers': 'de {n} payeurs',
    'no longer held': 'plus détenu',
    'on {value}': 'sur {value}',
    'refresh from Yahoo': 'actualiser depuis Yahoo',
    'twelve months back, twelve ahead': 'douze mois en arrière, douze en avant',
    '{n} holding has no distribution data at Yahoo.': '{n} position n’a pas de données de distribution chez Yahoo.',
    '{n} holdings have no distribution data at Yahoo.': '{n} positions n’ont pas de données de distribution chez Yahoo.',
    '{n} payment': '{n} versement',
    '{n} payments': '{n} versements',
    '{total} since the records begin': '{total} depuis le début des relevés',
    # REST API and webhooks (0.36.0)
    "A POST to a URL of yours when something happened: a sync ran or failed, a bill is past due. Home Assistant, n8n, a bot, a script. The body is JSON — event, time, data — and the X-Wealth-Signature header is an HMAC-SHA256 of it with the receiver's secret, so it can tell this app from anyone who found the URL. One attempt, five seconds; a receiver that is down misses that event and the list says so.": 'Un POST vers une URL à vous quand quelque chose s’est passé : une synchronisation a tourné ou échoué, une facture est en retard. Home Assistant, n8n, un bot, un script. Le corps est du JSON — événement, heure, données — et l’en-tête X-Wealth-Signature en est un HMAC-SHA256 avec le secret du récepteur, pour qu’il distingue cette app de quiconque a trouvé l’URL. Une tentative, cinq secondes ; un récepteur hors ligne manque cet événement et la liste le dit.',
    'Add the webhook': 'Ajouter le webhook',
    'Create a token above and the examples appear here.': 'Créez un jeton ci-dessus et les exemples apparaîtront ici.',
    'Events': 'Événements',
    'Every tool the assistant has is also a URL, for a script or an automation that speaks no MCP — the same token, the same answers, one registry. GET lists the tools with their schemas; GET or POST calls one, arguments as query parameters or a JSON body.': 'Chaque outil de l’assistant est aussi une URL, pour un script ou une automatisation qui ne parle pas MCP — le même jeton, les mêmes réponses, un seul registre. GET liste les outils avec leurs schémas ; GET ou POST en appelle un, arguments en paramètres de requête ou en corps JSON.',
    'Last': 'Dernier',
    'REST API': 'API REST',
    'Secret': 'Secret',
    'Send a test event': 'Envoyer un événement de test',
    'Test event sent to {n} webhook.': 'Événement de test envoyé à {n} webhook.',
    'Test event sent to {n} webhooks.': 'Événement de test envoyé à {n} webhooks.',
    'Webhook added. Its secret is shown in the list; give it to the receiver to check the signature.': 'Webhook ajouté. Son secret figure dans la liste ; donnez-le au récepteur pour vérifier la signature.',
    'Webhook removed.': 'Webhook supprimé.',
    'Webhooks': 'Webhooks',
    'the same tools over plain HTTP': 'les mêmes outils en simple HTTP',
    '{n} receiver': '{n} récepteur',
    '{n} receivers': '{n} récepteurs',
    # Undoing an import (0.36.1)
    "A named kind decides the sign: a Kauf is money out whichever way the bank wrote the figure, a Dividende money in. Without a kind column the sign is the file's — so if your bank writes a purchase as a positive amount and has no kind column, tick the box below, or the buys come in as money received.": 'Un type nommé décide du signe : un Kauf est une sortie d’argent quelle que soit la façon dont la banque a écrit le chiffre, une Dividende une entrée. Sans colonne de type, le signe est celui du fichier — si votre banque écrit un achat en positif et n’a pas de colonne de type, cochez la case ci-dessous, sinon les achats entrent comme de l’argent reçu.',
    'An import can be taken back as one thing — every row it brought, and only those; a row a re-import found already there belongs to the import that first brought it. Wrong signs from a mapping: undo, forget the mapping, import again.': 'Un import se reprend d’un bloc — chaque ligne qu’il a apportée, et seulement celles-là ; une ligne qu’un réimport a trouvée déjà là appartient à l’import qui l’a apportée en premier. Signes faux d’une correspondance : annuler, oublier la correspondance, réimporter.',
    'File': 'Fichier',
    'Import undone — {n} row removed.': 'Import annulé — {n} ligne supprimée.',
    'Import undone — {n} rows removed.': 'Import annulé — {n} lignes supprimées.',
    'Recent imports': 'Imports récents',
    'Remove every row this import brought?': 'Supprimer chaque ligne apportée par cet import ?',
    'Rows brought': 'Lignes apportées',
    'Signs.': 'Signes.',
    'That import is not on record.': 'Cet import n’est pas enregistré.',
    'That is usually the signs the wrong way round.': 'Ce sont généralement les signes à l’envers.',
    'Through': 'Par',
    'Undo': 'Annuler',
    'and forget its mapping': 'et oublier sa correspondance',
    'nothing left of it': 'il n’en reste rien',
    'of {n}': 'sur {n}',
    '{n} of the first rows look like purchases with money coming in.': '{n} des premières lignes ressemblent à des achats avec de l’argent entrant.',
    '{n} of the first rows looks like a purchase with money coming in.': '{n} des premières lignes ressemble à un achat avec de l’argent entrant.',
    # Retirement plan and goal kinds (0.37.0)
    'A car': 'Une voiture',
    'A deposit for a place of your own.': 'Un apport pour un chez-soi.',
    'A home': 'Un logement',
    'A month until then': 'Par mois jusque-là',
    'A trip': 'Un voyage',
    'A wedding': 'Un mariage',
    'An amount by a date, for whatever it is.': 'Un montant pour une date, quel qu’en soit l’objet.',
    'An emergency fund': 'Un fonds d’urgence',
    "An item with no ages runs from retirement to the horizon; clear its name to remove it. Amounts are in today's money and inflate with the rate above; what the pile has to cover is spending minus income, grossed up for the tax on withdrawals.": 'Un poste sans âges court de la retraite à l’horizon ; effacez son nom pour le retirer. Les montants sont en argent d’aujourd’hui et suivent le taux d’inflation ci-dessus ; ce que le capital doit couvrir est la dépense moins le revenu, majoré de l’impôt sur les retraits.',
    'Fees, % a year': 'Frais, % par an',
    'Fees, books and courses.': 'Frais, livres et cours.',
    'For': 'Pour',
    'Funded': 'Financé',
    "Income in retirement, a month, in today's money": 'Revenus à la retraite, par mois, en argent d’aujourd’hui',
    'Inflation, %': 'Inflation, %',
    'Lasts to {age}': 'Dure jusqu’à {age}',
    'Life after work — and whether it lasts. A plan of its own.': 'La vie après le travail — et si ça suffit. Un plan à part.',
    'Living, health, travel…': 'Vie courante, santé, voyages…',
    'Nominal': 'Nominal',
    'On these assumptions the pile is {value} when {name} retires at {retire} in {year}, against {required} needed — the money runs out at {age}, {years} years before the horizon.': 'Sur ces hypothèses, le capital est de {value} quand {name} part en retraite à {retire} en {year}, contre {required} nécessaires — l’argent s’épuise à {age}, {years} ans avant l’horizon.',
    'On these assumptions the pile is {value} when {name} retires at {retire} in {year}, against {required} needed, and {left} is still there at {horizon}.': 'Sur ces hypothèses, le capital est de {value} quand {name} part en retraite à {retire} en {year}, contre {required} nécessaires, et il reste {left} à {horizon}.',
    'Plan saved.': 'Plan enregistré.',
    'Plan to age': 'Planifier jusqu’à',
    'Projected': 'Projeté',
    'Required': 'Requis',
    'Required is, from retirement on, the capital that funds the rest of the plan from that year at the return after retirement; before it, the path that would reach the required capital exactly with the same contributions — the projection above it means ahead of plan. Projections rest on your assumptions; outcomes will differ. Not financial advice.': 'Requis est, à partir de la retraite, le capital qui finance le reste du plan depuis cette année au rendement d’après la retraite ; avant, la trajectoire qui atteindrait exactement le capital requis avec les mêmes versements — la projection au-dessus signifie en avance sur le plan. Les projections reposent sur vos hypothèses ; la réalité différera. Pas un conseil financier.',
    'Retired already': 'Déjà à la retraite',
    'Retirement': 'Retraite',
    'Retirement plan': 'Plan de retraite',
    'Return after, %': 'Rendement après, %',
    'Return before, %': 'Rendement avant, %',
    'Runs out at {age}': 'S’épuise à {age}',
    'Save the plan': 'Enregistrer le plan',
    'Something I am saving for': 'Quelque chose pour lequel j’épargne',
    "Spending in retirement, a month, in today's money": 'Dépenses à la retraite, par mois, en argent d’aujourd’hui',
    'State pension, rent, a part-time job…': 'Pension d’État, loyer, un emploi à temps partiel…',
    'Tax on withdrawals, %': 'Impôt sur les retraits, %',
    'The day itself.': 'Le jour même.',
    'The next car, paid for rather than financed.': 'La prochaine voiture, payée plutôt que financée.',
    'The one you keep putting off.': 'Celui que vous repoussez toujours.',
    'The plan': 'Le plan',
    'Three to six months of spending, untouched.': 'Trois à six mois de dépenses, intouchés.',
    "Today's money": 'Argent d’aujourd’hui',
    "Will the money last — and if not, until when. What goes in until you stop, what you will spend each month from then on, what will still come in, a return before and after, fees, inflation, tax on what is withdrawn: walked a year at a time to a horizon. The Forecast page's outlook is the first answer; this is the one with the retirement in it.": 'L’argent durera-t-il — et sinon, jusqu’à quand ? Ce qui entre jusqu’à l’arrêt, ce que vous dépenserez chaque mois ensuite, ce qui rentrera encore, un rendement avant et après, les frais, l’inflation, l’impôt sur les retraits : parcouru une année à la fois jusqu’à un horizon. La perspective de la page Projection est la première réponse ; celle-ci est celle qui contient la retraite.',
    'Withdrawn': 'Retiré',
    'age {age}': '{age} ans',
    'every rate is yours; the page predicts nothing': 'chaque taux est le vôtre ; la page ne prédit rien',
    'from age': 'dès l’âge',
    'from the Forecast plan': 'du plan Projection',
    'from {value} today across {n} accounts, {monthly} a month{plan}': 'à partir de {value} aujourd’hui sur {n} comptes, {monthly} par mois{plan}',
    "in today's money": 'en argent d’aujourd’hui',
    'nominal': 'nominal',
    'retired': 'retraité',
    'saving': 'épargne',
    'to age': 'jusqu’à l’âge',
    '{monthly} a month needed at retirement, in the money of that day': '{monthly} par mois nécessaires à la retraite, en argent de ce jour-là',
    '…growing % a year': '…croissant de % par an',
    # Moving in from Financial Planner (0.42.0)
    'Move in': 'Emménager',
    'Move in from Financial Planner': 'Emménager depuis Financial Planner',
    'Moved in': 'Emménagé',
    'Bring the books of the Financial Planner app over in one go: its accounts, every row of its ledger, its holdings, the daily balances it snapshotted and the price history it kept. Upload its wealth.db, look at what will be written, then confirm — nothing is touched until you do.': "Rapatrie les livres de l'app Financial Planner d'un coup : ses comptes, chaque ligne de son journal, ses positions, les soldes quotidiens de ses instantanés et son historique de cours. Téléverse sa wealth.db, regarde ce qui sera écrit, puis confirme — rien n'est touché avant.",
    'Accounts created': 'Comptes créés',
    'Rows': 'Lignes',
    'Rows already here': 'Lignes déjà présentes',
    'Opening positions': "Positions d'ouverture",
    'Balance readings': 'Relevés de solde',
    'Price days': 'Jours de cours',
    'Categories created': 'Catégories créées',
    "Each account's rows are one import, so an account page can undo its share. Refresh the prices and the rates next — Settings › Market — and compare the overview with the old app's.": "Les lignes de chaque compte forment un import, qu'une page de compte peut annuler pour sa part. Rafraîchis ensuite les cours et les taux — Réglages › Marché — et compare la vue d'ensemble avec l'ancienne app.",
    'To the overview': "Vers la vue d'ensemble",
    'What will be written': 'Ce qui sera écrit',
    '{rows} rows across {accounts} accounts, {balances} balance readings, {openings} opening positions, {prices} price days, {cats} new categories.': "{rows} lignes sur {accounts} comptes, {balances} relevés de solde, {openings} positions d'ouverture, {prices} jours de cours, {cats} nouvelles catégories.",
    '{n} rows are already here and are left alone.': '{n} lignes sont déjà là et restent telles quelles.',
    'Old account': 'Ancien compte',
    'From — to': 'De — à',
    'Readings': 'Relevés',
    'Goes into': 'Va dans',
    'closed': 'fermé',
    'left out — holds nothing': 'laissé de côté — ne contient rien',
    'a new account': 'un nouveau compte',
    'Where the rows do not add up to what the old app held — a position set from a statement, a sale whose purchase predates the ledger — a row dated before the first one makes up the difference, at the cost the old app carried.': "Là où les lignes ne donnent pas ce que l'ancienne app détenait — une position posée d'après un relevé, une vente dont l'achat précède le journal — une ligne datée avant la première comble l'écart, au coût que l'ancienne app portait.",
    'held {held}, rows give {rows}': 'détenu {held}, les lignes donnent {rows}',
    'New categories:': 'Nouvelles catégories :',
    'Worth knowing': 'Bon à savoir',
    "Rows keep the ids the old app gave them. Where this app's own importer would give the same row a different id, the account remembers how far its ledger is on record, and an export or a sync covering those days leaves them alone — so an export from before today need not be imported again, and a later one is safe.": "Les lignes gardent les identifiants de l'ancienne app. Là où l'importateur de cette app donnerait un autre identifiant à la même ligne, le compte retient jusqu'où son journal est enregistré, et un export ou une synchro couvrant ces jours les laisse tranquilles — un export d'avant aujourd'hui n'a donc pas à être réimporté, et un plus récent ne risque rien.",
    'The wealth.db file': 'Le fichier wealth.db',
    'Read it': 'Le lire',
    "Take a copy of the old app's wealth.db while it is not running, and upload the copy. Nothing is written until you have seen the plan and confirmed it.": "Copie la wealth.db de l'ancienne app pendant qu'elle ne tourne pas, et téléverse la copie. Rien n'est écrit avant que tu aies vu le plan et confirmé.",
    'That upload has expired — start again.': 'Ce téléversement a expiré — recommence.',
    'Moved in: {rows} rows, {balances} balance readings, {accounts} accounts created.': 'Emménagé : {rows} lignes, {balances} relevés de solde, {accounts} comptes créés.',
    'That is not a Financial Planner database — it should be the wealth.db file.': "Ce n'est pas une base Financial Planner — ce devrait être le fichier wealth.db.",
    'Could not read the file: {reason}': 'Impossible de lire le fichier : {reason}',
    'Ledger on record until': "Journal enregistré jusqu'au",
    'Rows up to this day were moved in from another app under its own ids. An import or a sync covering those days leaves them alone, so nothing is booked twice. Clear it to let everything in.': "Les lignes jusqu'à ce jour viennent d'une autre app, avec ses identifiants. Un import ou une synchro couvrant ces jours les laisse tranquilles, pour que rien ne soit comptabilisé deux fois. Vide le champ pour tout laisser entrer.",
    'Worked out for the accounts proposed above, and again for the ones you pick when you confirm: rows already in a chosen account count towards its holding.': 'Calculé pour les comptes proposés ci-dessus, et de nouveau pour ceux que tu choisis en confirmant : les lignes déjà dans un compte choisi comptent dans sa position.',
    # Trades on the chart, sold-out list, removing a row (0.43.0)
    'A correction survives the next import: the row is recognised by its id and left as you set it. So does a removal — the id is remembered, and an import or a sync leaves that row out.': "Une correction survit à l'import suivant : la ligne est reconnue par son identifiant et laissée telle que tu l'as mise. Une suppression aussi — l'identifiant est retenu, et un import ou une synchro laisse cette ligne dehors.",
    "A position sold down to nothing leaves the table above; it is kept here so what it made does not vanish with it. Its rows are on its page, like any other's.": "Une position vendue jusqu'à zéro quitte le tableau ci-dessus ; elle reste ici pour que ce qu'elle a rapporté ne disparaisse pas avec elle. Ses lignes sont sur sa page, comme pour toute autre.",
    'Bought': 'Acheté',
    'Dividend': 'Dividende',
    'Mark the trades': 'Marquer les opérations',
    'Remove this row? An import or a sync will not bring it back.': 'Supprimer cette ligne ? Un import ou une synchro ne la ramènera pas.',
    'Removed. An import or a sync will not bring it back.': 'Supprimée. Un import ou une synchro ne la ramènera pas.',
    'Sold': 'Vendu',
    'Sold out': 'Entièrement vendus',
    'Split': 'Division',
    'That row is not there.': "Cette ligne n'existe pas.",
    'newest first': 'les plus récents en premier',
    '{n} securities no longer held': '{n} titres plus détenus',
    '{n} security no longer held': '{n} titre plus détenu',
    'Without {what}: the whole is {total}.': 'Sans {what} : le tout fait {total}.',
    'incl.': 'incl.',
    'Cash & banks': 'Cash & banques',
    'Investments': 'Investissements',
    'Pension': 'Retraite',
    'Liabilities': 'Passifs',
    'In its currency': 'Dans sa devise',
    'what each is worth, cash and holdings together': 'ce que chacun vaut, cash et positions ensemble',
    '{n} row here': '{n} ligne ici',
    '{n} rows here': '{n} lignes ici',
    'Pick the account you already have for the same bank or broker, never a second one:': 'Choisis le compte que tu as déjà pour la même banque ou le même courtier, jamais un second :',
    "a duplicate account carries the same balance twice. And where the account you pick already has rows from a file of its own, the old app's rows of the same days are booked beside them unless the ids match — they match for Trade Republic, Saxo, Kraken and Crédit Agricole next bank, not for the rest; for those, undo the move's import on that account afterwards, or leave that account out by giving it no rows of its own first.": "un compte en double porte le même solde deux fois. Et là où le compte choisi a déjà des lignes venues d'un fichier à lui, les lignes de l'ancienne app des mêmes jours sont comptabilisées à côté, sauf si les identifiants coïncident — c'est le cas pour Trade Republic, Saxo, Kraken et Crédit Agricole next bank, pas pour les autres ; pour ceux-là, annule ensuite l'import de l'emménagement sur ce compte.",
    'Coins withdrawn go to': 'Les coins retirés vont vers',
    'nowhere — they simply leave': 'nulle part — ils partent, simplement',
    'A coin sent to a wallet of your own is still yours. Name the wallet — an account of type Broker, created under Accounts — and a withdrawal becomes a move between the two, at the cost the units carried; a coin sent back in is the same the other way round.': "Un coin envoyé vers un portefeuille à toi reste à toi. Nomme le portefeuille — un compte de type Courtier, créé sous Comptes — et un retrait devient un mouvement entre les deux, au coût que portaient les unités ; un coin renvoyé, pareil dans l'autre sens.",
    'Saved. A coin withdrawn from now on arrives there, at the cost it carried.': "Enregistré. Un coin retiré désormais y arrive, au coût qu'il portait.",
    'Saved. A coin withdrawn simply leaves.': 'Enregistré. Un coin retiré part, simplement.',
    'Balance over time': 'Solde dans le temps',
    '{n} reading since {date}': '{n} relevé depuis le {date}',
    '{n} readings since {date}': '{n} relevés depuis le {date}',
    "Each point is a reading of the balance on that day — from a sync, a statement, the loan's schedule, or typed in above. The newest reading of a day stands for the day; between readings the last one holds.": "Chaque point est un relevé du solde ce jour-là — d'une synchro, d'un extrait, de l'échéancier du prêt, ou saisi ci-dessus. Le relevé le plus récent d'un jour vaut pour le jour ; entre deux relevés, le dernier tient.",
}
