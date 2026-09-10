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
    "nothing imported yet": "rien d'importé pour l'instant",
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
    "Last price": "Dernier prix",
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
    "Quantities are the running sum of every buy and sell imported. The last "
    "two columns use the price of your most recent trade, not a market price — "
    "this app has no price feed yet, and a stale number presented as a "
    "valuation is worse than none.":
        "Les quantités sont la somme courante de tous les achats et ventes "
        "importés. Les deux dernières colonnes utilisent le prix de ton ordre "
        "le plus récent, pas un prix de marché — cette application n'a pas "
        "encore de source de cours, et un chiffre périmé présenté comme une "
        "valorisation est pire que rien.",
    "Everything you hold, aggregated by ISIN across accounts — the same fund "
    "at two brokers is one position from where you are standing. Values use "
    "the price of your last trade, which is not a market price; a price feed "
    "is the next thing to build.":
        "Tout ce que tu détiens, regroupé par ISIN sur l'ensemble des comptes "
        "— le même fonds chez deux courtiers ne fait qu'une position de là où "
        "tu es. La valorisation utilise le prix de ton dernier ordre, qui "
        "n'est pas un prix de marché ; une source de cours est la prochaine "
        "chose à construire.",
    "{n} position": "{n} position",
    "{n} positions": "{n} positions",
    "across all accounts": "sur tous les comptes",
    "what you put in, {currency} positions":
        "ce que tu as mis, positions en {currency}",
    "at last traded prices, not market":
        "aux derniers prix traités, pas au marché",
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
    "valued at your last traded price, not a market price":
        "valorisé à ton dernier prix traité, pas à un prix de marché",
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
    "CSV file": "Fichier CSV",
    "Drop in a CSV your broker exported. The file is recognised by its "
    "columns, so there is nothing to choose — and re-importing a period you "
    "already loaded is harmless, because every row carries an id.":
        "Dépose un CSV exporté par ton courtier. Le fichier est reconnu à ses "
        "colonnes, il n'y a donc rien à choisir — et réimporter une période "
        "déjà chargée ne fait aucun mal, puisque chaque ligne porte un "
        "identifiant.",
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
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exporte une période qui recouvre ce que tu as déjà importé. Le "
        "recouvrement ne coûte rien ; un trou te coûte des transactions.",
    "Choose a CSV file first.": "Choisis d'abord un fichier CSV.",
    "That file is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "Ce fichier dépasse {mb} Mo. Un export de transactions est bien plus "
        "petit — est-ce le bon fichier ?",
    "That file's columns do not match any importer here. Supported: {list}":
        "Les colonnes de ce fichier ne correspondent à aucun importateur ici. "
        "Pris en charge : {list}",
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
    "{currency} only": "{currency} uniquement",
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
    "Spent in {month}": "Dépensé en {month}",
    "of": "sur",
    "budgeted": "budgétés",
    "{pct}% through the month": "{pct}% du mois écoulé",
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
    "tick “remember” to turn a choice into a rule":
        "coche « retenir » pour transformer un choix en règle",
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
    "When the text contains": "Quand le texte contient",
    "Added": "Ajoutée",
    "Rule saved — {n} transaction matched “{pattern}”.":
        "Règle enregistrée — {n} transaction correspondait à « {pattern} ».",
    "Rule saved — {n} transactions matched “{pattern}”.":
        "Règle enregistrée — {n} transactions correspondaient à « {pattern} ».",
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
    "broker and it is not.":
        "Une catégorie est identifiée en interne par le nom sous lequel elle a "
        "été créée : la renommer ou la recolorier ne reclasse donc jamais une "
        "transaction — les Courses que tu as déjà triées restent triées, quel "
        "que soit le nom que tu leur donnes. Ce que « compte comme » décide, "
        "c'est si Flux de trésorerie et Budget traitent l'argent comme dépensé "
        "ou simplement déplacé : payer le déjeuner est une dépense, virer "
        "500 € vers ton courtier n'en est pas une.",
    "Colour for {name}": "Couleur de {name}",
    "Name of {name}": "Nom de {name}",
    "Cash Flow knows this one by name — it is never counted as spending.":
        "Flux de trésorerie connaît celle-ci par son nom — elle n'est jamais "
        "comptée comme une dépense.",
    "not spending": "pas une dépense",
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
}
