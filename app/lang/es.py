"""Español.

Se tutea: esto corre en tu propio servidor, para ti. Los números y las
fechas salen de i18n.FORMATS, no de aquí.

Una entrada que falte no es un error — entonces aparece el inglés
original. Ver app/i18n.py.
"""

STRINGS: dict[str, str] = {

    # ─── Navegación y marco ──────────────────────────────────────────
    "Overview": "Resumen",
    "Portfolio": "Cartera",
    "Cash Flow": "Flujo de caja",
    "Budget": "Presupuesto",
    "Subscriptions": "Suscripciones",
    "Transactions": "Transacciones",
    "Categorize": "Categorizar",
    "Accounts": "Cuentas",
    "Settings": "Ajustes",
    "Sign in": "Iniciar sesión",
    "Sign out": "Cerrar sesión",
    "Runs on your machine. Your data never leaves it, except to your own bank.":
        "Funciona en tu máquina. Tus datos nunca salen de ella, salvo hacia tu "
        "propio banco.",
    "Not found": "No encontrado",
    "No such page.": "Esta página no existe.",
    "Back to accounts": "Volver a las cuentas",

    # ─── Acceso e instalación ────────────────────────────────────────
    "Username": "Usuario",
    "Password": "Contraseña",
    "Password again": "Contraseña otra vez",
    "at least 8 characters": "al menos 8 caracteres",
    "Create account": "Crear la cuenta",
    "Create your account": "Crea tu acceso",
    "This is the only account on this installation, and it lives in your own "
    "database. Nothing is sent anywhere, so there is no email to confirm and "
    "no way for anyone to reset it for you — choose a password you will keep.":
        "Este es el único acceso a esta instalación, y vive en tu propia base "
        "de datos. No se envía nada a ninguna parte: no hay correo que "
        "confirmar ni nadie que pueda restablecer tu contraseña por ti — elige "
        "una que vayas a recordar.",
    "Too many attempts. Wait a few minutes.":
        "Demasiados intentos. Espera unos minutos.",
    "Wrong username or password.": "Usuario o contraseña incorrectos.",
    "A username is required.": "Hace falta un usuario.",
    "The password must be at least {n} characters.":
        "La contraseña debe tener al menos {n} caracteres.",
    "The username “{name}” is already taken.":
        "El usuario «{name}» ya está ocupado.",

    # ─── Cuentas ─────────────────────────────────────────────────────
    "Account": "Cuenta",
    "Add an account": "Añadir una cuenta",
    "New account": "Cuenta nueva",
    "Name": "Nombre",
    "Type": "Tipo",
    "Currency": "Moneda",
    "Source": "Origen",
    "Balance": "Saldo",
    "As of": "A fecha",
    "Edit": "Editar",
    "Delete": "Eliminar",
    "Save": "Guardar",
    "connected": "conectada",
    "imported file": "archivo importado",
    "nothing yet": "nada todavía",
    "An account exists whether or not a bank is ever connected to it. Name it "
    "something you will recognise — you can connect it to your bank on the "
    "next screen, or type the balance in yourself and never connect it at all.":
        "Una cuenta existe se conecte o no a un banco. Ponle un nombre que "
        "reconozcas — puedes conectarla a tu banco en la pantalla siguiente, o "
        "escribir el saldo tú mismo y no conectarla nunca.",
    "The account needs a name.": "La cuenta necesita un nombre.",
    "Account updated.": "Cuenta actualizada.",
    "That account does not exist.": "Esa cuenta no existe.",
    "Bank account": "Cuenta corriente",
    "Savings": "Ahorro",
    "Credit card": "Tarjeta de crédito",
    "Broker": "Bróker",
    "Other": "Otro",

    # ─── Eliminar una cuenta ─────────────────────────────────────────
    "Delete this account": "Eliminar esta cuenta",
    "This account holds nothing — no transactions, no balance readings, no "
    "bank connection. There is nothing to lose by removing it.":
        "Esta cuenta no contiene nada — ni transacciones, ni lecturas de "
        "saldo, ni conexión bancaria. Al eliminarla no se pierde nada.",
    "This cannot be undone.": "Esto no se puede deshacer.",
    "Deleting {name} also removes {what}.":
        "Al eliminar {name} desaparecen también {what}.",
    "Deleting {name} removes everything on it.":
        "Al eliminar {name} desaparece todo lo que contiene.",
    "{n} transaction": "{n} transacción",
    "{n} transactions": "{n} transacciones",
    "{n} balance reading": "{n} lectura de saldo",
    "{n} balance readings": "{n} lecturas de saldo",
    "{a} and {b}": "{a} y {b}",
    "The bank connection goes with it. The consent itself stays alive at your "
    "bank until it expires or you revoke it there, and re-connecting means "
    "going through your bank's login again.":
        "La conexión bancaria se va con ella. El consentimiento sigue vivo en "
        "tu banco hasta que caduque o lo revoques allí, y volver a conectar "
        "significa pasar otra vez por el acceso de tu banco.",
    "There is no undo and no copy of this anywhere else.":
        "No hay deshacer ni copia de esto en ningún otro sitio.",
    "Type {name} to confirm": "Escribe {name} para confirmar",
    "Delete permanently": "Eliminar definitivamente",
    "Type the account name exactly to confirm the deletion.":
        "Escribe el nombre de la cuenta exactamente para confirmar que se "
        "elimina.",
    "Deleted {name}.": "{name} eliminada.",

    # ─── Página de la cuenta ─────────────────────────────────────────
    "Bank connection": "Conexión bancaria",
    "reported": "declarado",
    "as of {date}": "a fecha {date}",
    "nothing reported yet": "todavía no se ha declarado nada",
    "Last sync: {when}.": "Última sincronización: {when}.",
    "never": "nunca",
    "Consent valid for {n} more day.":
        "El consentimiento vale {n} día más.",
    "Consent valid for {n} more days.":
        "El consentimiento vale {n} días más.",
    "Consent expires in {n} day — reconnect soon.":
        "El consentimiento caduca en {n} día — vuelve a conectar pronto.",
    "Consent expires in {n} days — reconnect soon.":
        "El consentimiento caduca en {n} días — vuelve a conectar pronto.",
    "Consent expired. Reconnect to resume syncing.":
        "Consentimiento caducado. Vuelve a conectar para seguir "
        "sincronizando.",
    "Sync now": "Sincronizar ahora",
    "Reconnect or change bank": "Reconectar o cambiar de banco",
    "This account is not connected to a bank. Connecting it pulls the balance "
    "and the transaction history straight from the bank, with your own Enable "
    "Banking credentials.":
        "Esta cuenta no está conectada a ningún banco. Conectada, trae el "
        "saldo y el historial directamente del banco, con tus propias "
        "credenciales de Enable Banking.",
    "Connect a bank": "Conectar un banco",
    "Started one already and landed on a dead page? {paste}.":
        "¿Ya empezaste y acabaste en una página muerta? {paste}.",
    "Paste the code here": "Pega el código aquí",
    "Add your Enable Banking Application ID and private key in {settings} first.":
        "Añade primero tu Application ID y tu clave privada de Enable Banking "
        "en {settings}.",
    "Import a broker CSV": "Importar un CSV del bróker",
    "Edit or delete": "Editar o eliminar",
    "Recent transactions": "Transacciones recientes",
    "No transactions yet.": "Todavía no hay transacciones.",
    "Showing the {shown} most recent of {total}.":
        "Las {shown} más recientes de {total}.",
    "That account is not connected to a bank.":
        "Esa cuenta no está conectada a ningún banco.",
    "Sync failed: {reason}": "Falló la sincronización: {reason}",
    "Imported {n} new transaction.": "{n} transacción nueva importada.",
    "Imported {n} new transactions.": "{n} transacciones nuevas importadas.",

    # ─── Posiciones ──────────────────────────────────────────────────
    "Holdings": "Posiciones",
    "Security": "Título",
    "ISIN": "ISIN",
    "Quantity": "Cantidad",
    "Net invested": "Invertido neto",
    "Last traded at": "Último precio operado",
    "At that price": "A ese precio",
    "Value": "Valor",
    "Difference": "Diferencia",
    "Where": "Dónde",
    "largest first": "las mayores primero",
    "{n} trade": "{n} orden",
    "{n} trades": "{n} órdenes",
    "last {date}": "la última el {date}",
    "last trade {date}": "última orden el {date}",
    "export starts too late": "el export empieza demasiado tarde",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export a period that starts when you "
    "opened the account and re-import — overlap is free.":
        "Una cantidad negativa no es una posición corta: es una venta cuya "
        "compra es más antigua que el archivo que importaste. Exporta un "
        "periodo que empiece cuando abriste la cuenta y vuelve a importar — el "
        "solape sale gratis.",
    "A negative quantity is not a short position: it is a sale whose purchase "
    "is older than the file you imported. Export from the account opening and "
    "re-import — overlap is free.":
        "Una cantidad negativa no es una posición corta: es una venta cuya "
        "compra es más antigua que el archivo que importaste. Exporta desde la "
        "apertura de la cuenta y vuelve a importar — el solape sale gratis.",
    "Quantities are the running sum of every buy and sell, imported or typed in. The last "
    "two columns use the price of your most recent trade, not a market price — "
    "this app has no price feed yet, and a stale number presented as a "
    "valuation is worse than none.":
        "Las cantidades son la suma corriente de todas las compras y ventas, "
        "importadas o introducidas a mano. Las dos últimas columnas usan el precio de tu orden más "
        "reciente, no un precio de mercado — esta aplicación todavía no tiene "
        "fuente de cotizaciones, y un número caducado presentado como "
        "valoración es peor que ninguno.",
    "{n} position": "{n} posición",
    "{n} positions": "{n} posiciones",
    "across all accounts": "en todas las cuentas",
    "what you put in, {currency} positions":
        "lo que pusiste, posiciones en {currency}",
    "No holdings yet.": "Todavía no hay posiciones.",
    "Import a broker export from an account and the positions are computed "
    "from its trades.":
        "Importa un export del bróker en una cuenta y las posiciones se "
        "calculan a partir de sus órdenes.",

    # ─── Resumen ─────────────────────────────────────────────────────
    "Net worth": "Patrimonio neto",
    "Cash": "Efectivo",
    "Securities": "Valores",
    "{n} connected to a bank": "{n} conectada a un banco",
    "across {n} account with a balance": "en {n} cuenta con saldo",
    "across {n} accounts with a balance": "en {n} cuentas con saldo",
    "{n} holding": "{n} posición",
    "{n} holdings": "{n} posiciones",
    "{n} with no price": "{n} sin precio",
    "imported and synced": "importadas y sincronizadas",
    "Largest holding": "Mayor posición",
    "import a broker export to see holdings":
        "importa un export del bróker para ver posiciones",
    "Cash vs securities": "Efectivo frente a valores",
    "Where it is": "Dónde está",
    "by account": "por cuenta",
    "no price": "sin precio",
    "Latest activity": "Última actividad",
    "Date": "Fecha",
    "Description": "Concepto",
    "Kind": "Tipo",
    "Amount": "Importe",
    "Counterparty": "Contraparte",
    "Nothing here yet.": "Aquí todavía no hay nada.",
    "Add an account, then connect it to your bank or import a broker export. "
    "Both routes end in the same place.":
        "Añade una cuenta y conéctala a tu banco o importa un export del "
        "bróker. Los dos caminos acaban en el mismo sitio.",

    # ─── Importar ────────────────────────────────────────────────────
    "Import": "Importar",
    "Import into {name}": "Importar en {name}",
    "Rows read": "Filas leídas",
    "Imported": "Importadas",
    "Already had": "Ya estaban",
    "No cash movement, skipped": "Sin movimiento de efectivo, omitidas",
    "{n} line could not be read.": "{n} línea no se pudo leer.",
    "{n} lines could not be read.": "{n} líneas no se pudieron leer.",
    "Everything else was imported. These are listed rather than counted so you "
    "can see whether they matter:":
        "Todo lo demás se importó. Se enumeran en lugar de contarse para que "
        "veas si importan:",
    "…and {n} more.": "…y {n} más.",
    "See the account": "Ver la cuenta",
    "Where to get the file": "De dónde sale el archivo",
    "Inbox → Account statement → choose the period → export CSV. That is the "
    "cash ledger: deposits, trades, dividends and fees. Set the start date "
    "back to when you opened the account and you get the whole history in one "
    "go.":
        "Bandeja de entrada → Extracto de cuenta → elegir el periodo → "
        "exportar CSV. Ese es el libro de efectivo: ingresos, órdenes, "
        "dividendos y comisiones. Pon la fecha de inicio en la apertura de la "
        "cuenta y tendrás todo el historial de una vez.",
    "Profile → Transactions → export.": "Perfil → Transacciones → exportar.",
    "Drop in a CSV your broker exported, or the statement PDFs from your bank's "
    "mailbox — as many as you like, or a ZIP of them. Each file is recognised by "
    "what is in it, so there is nothing to choose — and re-importing what you "
    "already loaded is harmless, because every row carries an id.":
        "Suelta aquí un CSV exportado por tu bróker, o los PDF de liquidación del "
        "buzón de tu banco — tantos como quieras, o un ZIP con ellos. Cada archivo "
        "se reconoce por su contenido, así que no hay nada que elegir — y volver a "
        "importar lo que ya cargaste no hace daño, porque cada fila lleva un "
        "identificador.",
    "CSV or PDF files":
        "Archivos CSV o PDF",
    "Files":
        "Archivos",
    "Postfach → filter by the Depot → download the Wertpapierabrechnungen as PDF "
    "and drop them all in here at once. The Depot's CSV says only what money "
    "moved; the PDFs say how many units, at what price, with what fee. Orders, "
    "fund purchases, dividends, interest, the Vorabpauschale and the half-year "
    "Sparplan overview are all read. A Storno is skipped and named.":
        "Postfach → filtrar por el Depot → descargar las Wertpapierabrechnungen en "
        "PDF y soltarlas todas aquí de una vez. El CSV del Depot solo dice qué "
        "dinero se movió; los PDF dicen cuántas participaciones, a qué precio, con "
        "qué comisión. Órdenes, compras de fondos, dividendos, intereses, la "
        "Vorabpauschale y el resumen semestral del Sparplan se leen todos. Un "
        "Storno se omite y se nombra.",
    "Open the account or the Visa card → Umsätze → choose the period → "
    "CSV-Export. Girokonto, Tagesgeld and Visa all work, and so do files from "
    "the old portal. Pending (vorgemerkt) rows are left out until they are "
    "booked.":
        "Abre la cuenta o la tarjeta Visa → Umsätze → elige el periodo → "
        "CSV-Export. Girokonto, Tagesgeld y Visa funcionan todos, igual que los "
        "archivos del portal antiguo. Los movimientos pendientes (vorgemerkt) se "
        "dejan fuera hasta que estén contabilizados.",
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exporta un periodo que se solape con lo ya importado. El solape no "
        "cuesta nada; un hueco te cuesta transacciones.",
    "Choose a CSV or PDF file first.": "Elige primero un archivo CSV o PDF.",
    "{name} is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "{name} pasa de {mb} MB. Un export de transacciones es mucho más "
        "pequeño — ¿es el archivo correcto?",
    "None of those files match an importer here. Supported: {list}":
        "Ninguno de esos archivos encaja con un importador de aquí. "
        "Compatibles: {list}",
    "not recognised, left out": "no reconocido, omitido",
    "{importer}: {new} new, {had} already had.":
        "{importer}: {new} nuevas, {had} ya estaban.",

    # ─── Conectar un banco ───────────────────────────────────────────
    "You will be sent to your bank's own login page. This app never sees your "
    "banking password — the bank gives it read-only access to the account you "
    "tick, for {days} days at a time, and you can revoke it at your bank.":
        "Se te enviará a la página de acceso de tu propio banco. Esta "
        "aplicación nunca ve tu contraseña bancaria — el banco le da acceso de "
        "solo lectura a la cuenta que marques, durante {days} días cada vez, y "
        "puedes revocarlo en tu banco.",
    "If your bank leaves you on a page that will not load, that is expected "
    "with an https-only redirect URL — {by_hand}.":
        "Si tu banco te deja en una página que no carga, es lo esperable con "
        "una URL de redirección solo https — {by_hand}.",
    "finish the connection by hand": "termina la conexión a mano",
    "Country": "País",
    "Search": "Buscar",
    "Show banks": "Mostrar bancos",
    "{n} bank in {country}": "{n} banco en {country}",
    "{n} banks in {country}": "{n} bancos en {country}",
    "including {n} sandbox": "de ellos {n} sandbox",
    "including {n} sandboxes": "de ellos {n} sandbox",
    "Connect a sandbox bank first.": "Conecta primero un banco sandbox.",
    "It walks the identical flow — redirect, consent, session, balances, "
    "transactions — with the provider's own test credentials, and creates no "
    "consent at a real bank. If your redirect URL is registered wrongly, you "
    "find out here instead of by spending an authorisation you rely on.":
        "Recorre exactamente el mismo camino — redirección, consentimiento, "
        "sesión, saldos, transacciones — con las credenciales de prueba del "
        "proveedor, y no crea ningún consentimiento en un banco real. Si tu "
        "URL de redirección está mal registrada, te enteras aquí en lugar de "
        "gastar una autorización de la que dependes.",
    "Bank": "Banco",
    "Connect": "Conectar",
    "sandbox": "sandbox",
    "No banks matched. Try a shorter search, or check the country code.":
        "Ningún banco coincide. Prueba una búsqueda más corta, o revisa el "
        "código de país.",
    "Connected: {accounts}": "Conectado: {accounts}",
    "Connected, but the first sync failed: {reason}":
        "Conectado, pero la primera sincronización falló: {reason}",
    "Imported {n} transaction.": "{n} transacción importada.",
    "Imported {n} transactions.": "{n} transacciones importadas.",
    "The bank refused the authorisation: {reason}":
        "El banco rechazó la autorización: {reason}",
    "The bank sent us back without an authorisation code.":
        "El banco nos devolvió sin código de autorización.",

    # ─── Terminar la conexión a mano ─────────────────────────────────
    "Finish connecting": "Terminar la conexión",
    "Finish connecting by hand": "Terminar la conexión a mano",
    "Some providers only accept an https redirect URL, which an app on your "
    "own network cannot have. Then the bank sends you to a page that does not "
    "exist — and that is fine. The authorisation code is in the address bar of "
    "that dead page. Copy the whole address and paste it here.":
        "Algunos proveedores solo aceptan una URL de redirección https, que "
        "una aplicación en tu propia red no puede tener. Entonces el banco te "
        "manda a una página que no existe — y está bien. El código de "
        "autorización está en la barra de direcciones de esa página muerta. "
        "Copia la dirección entera y pégala aquí.",
    "Waiting to be finished": "Esperando a terminarse",
    "Started": "Empezada",
    "One connection is in progress, so pasting just the code works too — but "
    "the whole URL is easier and always right.":
        "Solo hay una conexión en curso, así que pegar únicamente el código "
        "también vale — pero la URL entera es más fácil y siempre acierta.",
    "The address the bank sent you to":
        "La dirección a la que te mandó el banco",
    "Nothing is fetched from this address — it is only read for the code and "
    "state it carries.":
        "De esta dirección no se descarga nada — solo se lee para sacar el "
        "código y el state que lleva.",
    "No connection is waiting to be finished.":
        "No hay ninguna conexión esperando a terminarse.",
    "Start one from an account, then come back here if the bank leaves you on "
    "a page that will not load.":
        "Empieza una desde una cuenta y vuelve aquí si el banco te deja en una "
        "página que no carga.",
    "No authorisation code in that. Paste the whole URL from the address bar, "
    "including the ?code=… part.":
        "Ahí no hay código de autorización. Pega la URL entera de la barra de "
        "direcciones, incluida la parte ?code=….",
    "That code could belong to any of several connections in progress. Paste "
    "the full URL, which carries the state.":
        "Ese código podría ser de varias conexiones en curso. Pega la URL "
        "completa, que lleva el state.",

    # ─── Flujo de caja ───────────────────────────────────────────────
    "Money in against money out, per month. Internal transfers are excluded — "
    "moving money between your own accounts is not income and not spending, "
    "and counting it would inflate both by the same amount. Investment is "
    "separated for the same reason: a month you invested €3,000 is not a month "
    "you overspent.":
        "El dinero que entra frente al que sale, por mes. Los traspasos "
        "internos quedan fuera — mover dinero entre tus propias cuentas no es "
        "ingreso ni gasto, y contarlo inflaría ambos por el mismo importe. La "
        "inversión va aparte por lo mismo: un mes en el que invertiste 3.000 € "
        "no es un mes en el que gastaste de más.",
    "Income": "Ingresos",
    "Spending": "Gastos",
    "Invested": "Invertido",
    "Kept": "Ahorrado",
    "a month": "al mes",
    "a month, over {n} month": "al mes, sobre {n} mes",
    "a month, over {n} months": "al mes, sobre {n} meses",
    "over the period": "en el periodo",
    "income less spending": "ingresos menos gastos",
    "By month": "Por mes",
    "Where it goes": "Adónde va",
    "By category": "Por categoría",
    "per month on average": "de media al mes",
    "Category": "Categoría",
    "Per month": "Al mes",
    "Total": "Total",
    "No transactions in the base currency yet.":
        "Todavía no hay transacciones en la moneda base.",
    "Connect a bank or import a statement, then categorise on the {page} page "
    "— until things have categories, this page has nothing to add up.":
        "Conecta un banco o importa un extracto y luego categoriza en la "
        "página {page} — mientras nada tenga categoría, esta página no tiene "
        "qué sumar.",

    # ─── Presupuesto ─────────────────────────────────────────────────
    "Measured against how far through the month you are, not against the whole "
    "month. Halfway through, everyone is under budget — the useful question is "
    "whether you are ahead of the pace.":
        "Medido contra lo que llevas de mes, no contra el mes entero. A mitad "
        "de mes todo el mundo va por debajo del presupuesto — la pregunta útil "
        "es si vas por delante del ritmo.",
    "No budgets set yet — fill some in below.":
        "Todavía no hay presupuestos — rellena alguno abajo.",
    "Monthly budget per category": "Presupuesto mensual por categoría",
    "leave blank for no budget": "déjalo vacío para no poner presupuesto",
    "Spent": "Gastado",
    "Typical": "Habitual",
    "Pace": "Ritmo",
    "over budget": "pasado de presupuesto",
    "ahead of pace": "por delante del ritmo",
    "on track": "en camino",
    "{pct}% used": "{pct}% usado",
    "Save budget": "Guardar presupuesto",
    "Budget saved.": "Presupuesto guardado.",

    # ─── Suscripciones ───────────────────────────────────────────────
    "Charges that repeat on a recognisable rhythm, at a stable amount, at "
    "least three times. Deliberately cautious: the failure that matters is not "
    "missing one, it is calling three unrelated payments a €400 commitment — "
    "which makes the whole page untrustworthy.":
        "Cargos que se repiten con un ritmo reconocible, por un importe "
        "estable, al menos tres veces. Deliberadamente prudente: el fallo que "
        "importa no es dejarse uno, es llamar a tres pagos sin relación un "
        "compromiso de 400 € — con lo que la página entera deja de ser "
        "creíble.",
    "Per year": "Al año",
    "{n} active": "{n} activas",
    "at the current rhythm": "al ritmo actual",
    "Possibly recurring": "Quizá recurrente",
    "repeated, but not on a clear rhythm":
        "se repite, pero sin un ritmo claro",
    "Recurring": "Recurrente",
    "What": "Qué",
    "Rhythm": "Ritmo",
    "Each": "Cada uno",
    "Paid so far": "Pagado hasta ahora",
    "Last seen": "Visto por última vez",
    "{n} payment since {date}": "{n} pago desde el {date}",
    "{n} payments since {date}": "{n} pagos desde el {date}",
    "probably ended": "probablemente terminada",
    "{n} day ago": "hace {n} día",
    "{n} days ago": "hace {n} días",
    "Nothing detected yet.": "Todavía no se ha detectado nada.",
    "A charge has to appear at least three times, on a recognisable rhythm, at "
    "a stable amount. Import a longer history and it will find more.":
        "Un cargo tiene que aparecer al menos tres veces, con un ritmo "
        "reconocible y un importe estable. Importa un historial más largo y "
        "encontrará más.",
    "repeats, but the rhythm or the amount wanders":
        "se repite, pero el ritmo o el importe bailan",
    "Times": "Veces",

    # ─── Transacciones y categorización ──────────────────────────────
    "merchant or text": "comercio o texto",
    "any": "todas",
    "Filter": "Filtrar",
    "Clear": "Limpiar",
    "net {amount}": "neto {amount}",
    "showing the {n} most recent": "las {n} más recientes",
    "Nothing matches those filters.": "Nada coincide con esos filtros.",
    "Correcting a transaction here can leave a rule behind. A rule applies to "
    "what is already imported as well as to what arrives next — otherwise the "
    "same shop has to be fixed every month for a year before it stops asking.":
        "Corregir una transacción aquí puede dejar una regla detrás. Una regla "
        "se aplica a lo ya importado igual que a lo que llegue después — si no, "
        "hay que corregir la misma tienda todos los meses durante un año antes "
        "de que deje de preguntar.",
    "Waiting": "Pendientes",
    "largest amounts first": "los importes mayores primero",
    "Rules": "Reglas",
    "applied to past and future": "se aplican al pasado y al futuro",
    "Quick start": "Empezar rápido",
    "Categorise what is obvious": "Categorizar lo evidente",
    "fees, interest, dividends, known merchants":
        "comisiones, intereses, dividendos, comercios conocidos",
    "The queue": "La cola",
    "clear “remember as” to correct this one row without making a rule":
        "vacía «recordar como» para corregir solo esta fila, sin crear una regla",
    "Remember as": "Recordar como",
    "text to match, optional": "texto para reconocerlo, opcional",
    "Apply": "Aplicar",
    "Nothing waiting.": "Nada pendiente.",
    "Every transaction has a category. Import more, or adjust one from the "
    "{page} page.":
        "Cada transacción tiene categoría. Importa más, o cambia alguna desde "
        "la página {page}.",
    "newest wins where two match":
        "si coinciden dos, gana la más reciente",
    "Rule saved — {n} transaction matched “{pattern}”.":
        "Regla guardada — {n} transacción coincidió con «{pattern}».",
    "Rule saved — {n} transactions matched “{pattern}”.":
        "Regla guardada — {n} transacciones coincidieron con «{pattern}».",
    "Changing a category here also makes a rule from the merchant, and applies it to every transaction that matches. To correct a single row without a rule, use the Categorize page and clear “remember as”.":
        "Cambiar una categoría aquí también crea una regla a partir del comercio, y la aplica a todas las transacciones que coincidan. Para corregir una sola fila sin regla, usa la página Categorizar y vacía «recordar como».",
    "A rule needs at least three characters to match on — anything shorter will catch transactions you did not mean.":
        "Una regla necesita al menos tres caracteres para reconocer algo — con menos atrapará transacciones que no querías.",
    "{n} transaction categorised from what the importer already knew.":
        "{n} transacción categorizada con lo que el importador ya sabía.",
    "{n} transactions categorised from what the importer already knew.":
        "{n} transacciones categorizadas con lo que el importador ya sabía.",
    "Rule deleted and the remaining rules re-applied.":
        "Regla eliminada y las demás reglas aplicadas de nuevo.",

    # ─── Ajustes ─────────────────────────────────────────────────────
    "General": "General",
    "Language": "Idioma",
    "Follow my browser": "Seguir a mi navegador",
    "Changes the language of the app, and with it how numbers and dates are "
    "written. It does not touch what your bank sent: a transaction described "
    "in German stays in German.":
        "Cambia el idioma de la aplicación y, con él, cómo se escriben números "
        "y fechas. No toca lo que envió tu banco: una transacción descrita en "
        "alemán sigue en alemán.",
    "Base currency": "Moneda base",
    "Redirect URL": "URL de redirección",
    "Where your bank sends you back after you authorise. This exact string "
    "must also be registered in the Enable Banking Control Panel — if the two "
    "differ by so much as a trailing slash, the bank refuses the handover and "
    "the error it shows names nothing useful.":
        "Adónde te devuelve tu banco después de autorizar. Esta cadena exacta "
        "tiene que estar registrada también en el Control Panel de Enable "
        "Banking — si se diferencian aunque sea en una barra final, el banco "
        "rechaza el traspaso, y el error que enseña no nombra nada útil.",
    "Settings saved.": "Ajustes guardados.",

    # ─── Categorías ──────────────────────────────────────────────────
    "Categories": "Categorías",
    "renaming one keeps every transaction it holds":
        "renombrar una conserva todas sus transacciones",
    "A category is identified internally by the name it was created with, so "
    "renaming or recolouring one never re-files a transaction — the Groceries "
    "you already sorted stay sorted whatever you call them. What “counts as” "
    "decides is whether Cash Flow and Budget treat the money as spent, or "
    "merely as moved: pay for lunch and it is spending, move €500 to your "
    "broker and it is not.":
        "Una categoría se identifica internamente por el nombre con el que se "
        "creó, así que renombrarla o cambiarle el color nunca reclasifica una "
        "transacción — el Supermercado que ya ordenaste sigue ordenado, lo "
        "llames como lo llames. Lo que decide «cuenta como» es si Flujo de "
        "caja y Presupuesto tratan el dinero como gastado o solo como movido: "
        "pagar la comida es gasto, pasar 500 € a tu bróker no lo es.",
    "Colour for {name}": "Color de {name}",
    "Name of {name}": "Nombre de {name}",
    "Cash Flow knows this one by name — it is never counted as spending.":
        "Flujo de caja conoce esta por su nombre — nunca cuenta como gasto.",
    "not spending": "no es gasto",
    "What {name} counts as": "Qué cuenta {name} como",
    "Not spending": "No es gasto",
    "{n} rule": "{n} regla",
    "{n} rules": "{n} reglas",
    "Delete this category? {n} transaction moves to Uncategorised.":
        "¿Eliminar esta categoría? {n} transacción pasa a Sin categoría.",
    "Delete this category? {n} transactions move to Uncategorised.":
        "¿Eliminar esta categoría? {n} transacciones pasan a Sin categoría.",
    "{n} rule is deleted with it.": "{n} regla se elimina con ella.",
    "{n} rules are deleted with it.": "{n} reglas se eliminan con ella.",
    "The app tells spending from moving your own money by this category, so it "
    "cannot be removed.":
        "Por esta categoría distingue la aplicación gastar de mover tu propio "
        "dinero, así que no se puede quitar.",
    "needed": "necesaria",
    "Colour": "Color",
    "New category": "Categoría nueva",
    "Childcare": "Cuidado de niños",
    "Counts as": "Cuenta como",
    "Add category": "Añadir categoría",
    "Category “{name}” added.": "Categoría «{name}» añadida.",
    "Category updated.": "Categoría actualizada.",
    "“{name}” deleted.": "«{name}» eliminada.",
    "“{name}” deleted — {n} transaction moved to Uncategorised, and its rules "
    "were removed with it.":
        "«{name}» eliminada — {n} transacción pasó a Sin categoría, y sus "
        "reglas se fueron con ella.",
    "“{name}” deleted — {n} transactions moved to Uncategorised, and its rules "
    "were removed with it.":
        "«{name}» eliminada — {n} transacciones pasaron a Sin categoría, y sus "
        "reglas se fueron con ella.",
    "A category needs a name.": "Una categoría necesita un nombre.",
    "Keep the name under 40 characters — it has to fit in a table cell and a "
    "chart legend.":
        "Deja el nombre por debajo de 40 caracteres — tiene que caber en una "
        "celda de tabla y en la leyenda de un gráfico.",
    "{given} is not a colour like #a78bfa.":
        "{given} no es un color como #a78bfa.",
    "That": "Eso",
    "That name has no letters or digits in it, and the name is what the "
    "internal id is made from.":
        "Ese nombre no tiene ni letras ni cifras, y del nombre se fabrica el "
        "identificador interno.",
    "“{name}” already uses that name.": "«{name}» ya se llama así.",
    "There is already a category called “{name}”.":
        "Ya hay una categoría llamada «{name}».",

    # ─── Enable Banking ──────────────────────────────────────────────
    "Your own application, your own key. Nothing here is shared with anyone — "
    "the key never leaves this machine and is only used to sign your own "
    "requests.":
        "Tu propia aplicación, tu propia clave. Aquí no se comparte nada con "
        "nadie — la clave nunca sale de esta máquina y solo sirve para firmar "
        "tus propias peticiones.",
    "Create an application": "Crea una aplicación",
    "at {control_panel}.": "en {control_panel}.",
    "Environment Production — restricted mode is a state of a production app, "
    "not a separate environment.":
        "Entorno Production — el «restricted mode» es un estado de una "
        "aplicación de producción, no un entorno aparte.",
    "Find your Application ID.": "Encuentra tu Application ID.",
    "It is on the application's page in the Control Panel — a UUID like "
    "{example}.":
        "Está en la página de la aplicación en el Control Panel — un UUID como "
        "{example}.",
    "If you chose Generate for the key, it is also the filename of the file "
    "your browser downloaded: {file}.":
        "Si elegiste «Generate» para la clave, es también el nombre del "
        "archivo que descargó tu navegador: {file}.",
    "Find your private key.": "Encuentra tu clave privada.",
    "Which file depends on the choice you made when creating the application:":
        "Qué archivo sea depende de lo que elegiste al crear la aplicación:",
    "You chose “Generate”": "Elegiste «Generate»",
    "the usual case": "el caso habitual",
    "your browser downloaded {file}.": "tu navegador descargó {file}.",
    "That file is the private key.": "Ese archivo es la clave privada.",
    "Open it in a text editor and copy everything, including the BEGIN and END "
    "lines. There is nothing to generate yourself.":
        "Ábrelo en un editor de texto y copia todo, incluidas las líneas BEGIN "
        "y END. No tienes que generar nada tú.",
    "You provided your own key": "Aportaste tu propia clave",
    "then you already ran the commands below and want {file}.":
        "entonces ya ejecutaste los comandos de abajo y lo que quieres es "
        "{file}.",
    "Do not paste enablebanking_public.pem, or anything you uploaded to Enable "
    "Banking. That is the public half; they have it, you need the other one.":
        "No pegues enablebanking_public.pem, ni nada que hayas subido a Enable "
        "Banking. Esa es la mitad pública; ellos la tienen, tú necesitas la "
        "otra.",
    "Paste both below": "Pega las dos abajo",
    "and save. The app checks them immediately against Enable Banking and "
    "tells you what it finds.":
        "y guarda. La aplicación las comprueba enseguida contra Enable Banking "
        "y te dice qué encuentra.",
    "Only if you want to supply your own key instead of letting the Control "
    "Panel generate one":
        "Solo si quieres aportar tu propia clave en vez de dejar que la genere "
        "el Control Panel",
    "Upload enablebanking_public.pem in the Control Panel; paste "
    "enablebanking_private.key below.":
        "Sube enablebanking_public.pem en el Control Panel; pega "
        "enablebanking_private.key abajo.",
    "The key is stored at {path} with permissions 0600.":
        "La clave se guarda en {path} con permisos 0600.",
    "Your credentials live inside the data folder, so every backup of that "
    "folder carries your bank key with it. Set WD_SECRETS_DIR to a folder "
    "outside it if that matters to you.":
        "Tus credenciales viven dentro de la carpeta de datos, así que cada "
        "copia de seguridad de esa carpeta se lleva tu clave bancaria con "
        "ella. Apunta WD_SECRETS_DIR a una carpeta de fuera si eso te importa.",
    "Application ID": "Application ID",
    "stored — paste again to replace":
        "guardado — vuelve a pegarlo para sustituirlo",
    "Private key (PEM)": "Clave privada (PEM)",
    "Save credentials": "Guardar credenciales",
    "Credentials saved. Checking them with Enable Banking…":
        "Credenciales guardadas. Comprobándolas con Enable Banking…",
    "Credentials are stored. {test} — this makes one live call to Enable "
    "Banking.":
        "Las credenciales están guardadas. {test} — esto hace una llamada real "
        "a Enable Banking.",
    "Test them": "Pruébalas",
    "Working. Registered redirect URLs:":
        "Funciona. URL de redirección registradas:",
    "none": "ninguna",

    # ─── Tipos de cambio ─────────────────────────────────────────────
    "Exchange rates": "Tipos de cambio",
    "European Central Bank": "Banco Central Europeo",
    "The ECB publishes euro reference rates every business day — free, "
    "without a key and without an account. They are what converts an amount in "
    "another currency into your base currency, and every total built from them "
    "names the day they were published.":
        "El BCE publica tipos de referencia del euro cada día hábil — gratis, "
        "sin clave y sin cuenta. Son los que convierten un importe en otra "
        "moneda a tu moneda base, y cada total que sale de ellos nombra el día "
        "en que se publicaron.",
    "{n} currency, published {date}.": "{n} moneda, publicada el {date}.",
    "{n} currencies, published {date}.": "{n} monedas, publicadas el {date}.",
    "The ECB does not publish at the weekend, so this is Friday's — which is "
    "also the newest rate there is.":
        "El BCE no publica el fin de semana, así que este es el del viernes — "
        "que además es el más nuevo que existe.",
    "No rates yet, so amounts in another currency are reported beside your "
    "totals rather than inside them. Fetching them needs this machine to reach "
    "the internet once.":
        "Todavía no hay tipos, así que los importes en otra moneda aparecen "
        "junto a tus totales en vez de dentro. Traerlos exige que esta máquina "
        "llegue a internet una vez.",
    "Update rates now": "Actualizar los tipos ahora",
    "Also updated on start-up, at most once a day, in the background. Nothing "
    "waits on it: a page renders whether or not the rates arrived.":
        "También se actualizan al arrancar, como mucho una vez al día, en "
        "segundo plano. Nada espera por ellos: una página se muestra hayan "
        "llegado o no.",
    "{n} exchange rate fetched, published {date}.":
        "{n} tipo de cambio traído, publicado el {date}.",
    "{n} exchange rates fetched, published {date}.":
        "{n} tipos de cambio traídos, publicados el {date}.",
    "Includes {amounts}, converted at the ECB rate of {date}.":
        "Incluye {amounts}, convertido al tipo del BCE del {date}.",
    "Not included, because no rate here covers them:":
        "No incluidos, porque ningún tipo de aquí los cubre:",
    "Amounts in another currency are in the totals above, converted at the ECB "
    "reference rate — a published mid-market rate, not one your broker would "
    "give you.":
        "Los importes en otra moneda están en los totales de arriba, "
        "convertidos al tipo de referencia del BCE — un tipo medio publicado, "
        "no el que te daría tu bróker.",
    "Rates of {date}.": "Tipos del {date}.",
    "These are not in the totals above, because no rate here covers them:":
        "Estos no están en los totales de arriba, porque ningún tipo de aquí "
        "los cubre:",

    # ─── Novedades ───────────────────────────────────────────────────
    "What changed": "Qué ha cambiado",
    "You are running version {version}.": "Estás en la versión {version}.",
    "Release notes are written once, in English, and are not translated — a "
    "translation of a note about a fix is one more thing that can be wrong "
    "about the fix.":
        "Las notas de versión se escriben una vez, en inglés, y no se "
        "traducen — la traducción de una nota sobre un arreglo es una cosa más "
        "que puede estar mal sobre ese arreglo.",
    "you are here": "estás aquí",
    "Added [changelog]": "Añadido",
    "Changed [changelog]": "Cambiado",
    "Fixed [changelog]": "Arreglado",
    "Removed [changelog]": "Eliminado",
    "No changelog shipped with this build.":
        "Con esta versión no vino ninguna lista de cambios.",
    "CHANGELOG.md is not inside the image — it is in the repository, which is "
    "where this page reads it from when you run from source.":
        "CHANGELOG.md no está dentro de la imagen — el archivo está en el "
        "repositorio, que es de donde lo lee esta página cuando arrancas desde "
        "el código.",

    # ─── Nombres de las categorías de serie ──────────────────────────
    "Housing": "Vivienda",
    "Groceries": "Supermercado",
    "Restaurants & bars": "Restaurantes y bares",
    "Transport": "Transporte",
    "Car": "Coche",
    "Travel": "Viajes",
    "Shopping": "Compras",
    "Health": "Salud",
    "Insurance": "Seguros",
    "Education": "Educación",
    "Entertainment": "Ocio",
    "Fees": "Comisiones",
    "Tax": "Impuestos",
    "Cash withdrawal": "Retirada de efectivo",
    "Uncategorised": "Sin categoría",
    "Investment": "Inversión",
    "Internal transfer": "Traspaso interno",

    # ─── Tipos de transacción ────────────────────────────────────────
    "deposit [kind]": "ingreso",
    "withdrawal [kind]": "retirada",
    "buy [kind]": "compra",
    "sell [kind]": "venta",
    "dividend [kind]": "dividendo",
    "interest [kind]": "intereses",
    "fee [kind]": "comisión",
    "tax [kind]": "impuesto",
    "transfer [kind]": "traspaso",
    "other [kind]": "otro",

    # ─── Ritmos ──────────────────────────────────────────────────────
    "weekly [rhythm]": "semanal",
    "monthly [rhythm]": "mensual",
    "quarterly [rhythm]": "trimestral",
    "half-yearly [rhythm]": "semestral",
    "yearly [rhythm]": "anual",

    # ─── Introducido a mano ─────────────────────────────────────────
    "typed in": "introducido a mano",
    "Balance in {currency}": "Saldo en {currency}",
    "Record balance": "Registrar saldo",
    "Balance recorded: {amount} as of {date}.":
        "Saldo registrado: {amount} a fecha {date}.",
    "The balance is missing.": "Falta el saldo.",
    "Add by hand": "Añadir a mano",
    "Add to {name} by hand": "Añadir a {name} a mano",
    "For an account no bank connection and no export will describe. What you type in lands beside the imported rows and counts the same way: a purchase becomes part of the holding, a dividend is income, a fee is a fee.":
        "Para una cuenta que ninguna conexión bancaria ni exportación describe. Lo que escribes aquí queda junto a las filas importadas y cuenta igual: una compra pasa a formar parte de la posición, un dividendo es ingreso, una comisión es una comisión.",
    "What happened": "Qué ha pasado",
    "Fee": "Comisión",
    "optional": "opcional",
    "optional, but it is what the holding will be called":
        "opcional, pero así se llamará la posición",
    "Price per unit, in {currency}":
        "Precio por unidad, en {currency}",
    "Total on the statement": "Total según el extracto",
    "optional — otherwise quantity × price, plus the fee and tax on a purchase and minus them on a sale":
        "opcional — si no, cantidad × precio, más comisión e impuesto en una compra y menos en una venta",
    "Amount, in {currency}": "Importe, en {currency}",
    "as a size — whether it is money in or out follows from what happened":
        "como magnitud — si el dinero entra o sale se deduce de lo que ha pasado",
    "Direction": "Sentido",
    "Money out of this account": "Dinero que sale de esta cuenta",
    "Money into this account": "Dinero que entra en esta cuenta",
    "optional — the shop, the employer, the other account":
        "opcional — la tienda, la empresa, la otra cuenta",
    "decide from the kind and my rules":
        "deducirla del tipo y de mis reglas",
    "Stay on this page to add another":
        "Quedarme en esta página para añadir otra",
    "Add": "Añadir",
    "Back to the account": "Volver a la cuenta",
    "Added.": "Añadido.",
    "Remove": "Quitar",
    "Removed.": "Quitado.",
    "Only a transaction typed in by hand can be removed. An imported one would only come back with the next import.":
        "Solo se puede quitar una transacción introducida a mano. Una importada volvería con la siguiente importación.",
    "Connect a bank, import a CSV, or {add}.":
        "Conecta un banco, importa un CSV o {add}.",
    "Pick what kind of entry this is.":
        "Elige qué tipo de entrada es.",
    "The date needs to be a real day, written year-month-day.":
        "La fecha tiene que ser un día real, escrito como año-mes-día.",
    "That date is in the future. A transaction is something that happened.":
        "Esa fecha está en el futuro. Una transacción es algo que ya ha ocurrido.",
    "A trade needs the security's ISIN — two letters and ten characters, like IE00B4L5Y983. It is on the order confirmation, and it is how the same fund at two brokers is recognised as one holding.":
        "Una operación necesita el ISIN del valor — dos letras y diez caracteres, como IE00B4L5Y983. Está en la confirmación de la orden, y es lo que permite reconocer el mismo fondo en dos brókeres como una sola posición.",
    "The quantity": "La cantidad",
    "The price": "El precio",
    "The fee": "La comisión",
    "The tax": "El impuesto",
    "The total": "El total",
    "The amount": "El importe",
    "{what} cannot be zero.": "{what} no puede ser cero.",
    "A trade needs a quantity and a price per unit.":
        "Una operación necesita una cantidad y un precio por unidad.",
    "The amount is missing.": "Falta el importe.",
    "Bought {qty} × {name}": "Compra {qty} × {name}",
    "Sold {qty} × {name}": "Venta {qty} × {name}",
    "Includes {amounts}, converted at ECB rates — each month at its own rate, and months older than the rates on file at the oldest.":
        "Incluye {amounts}, convertidos a tipos del BCE — cada mes a su propio tipo, y los meses anteriores a los tipos guardados al más antiguo.",
    "Not counted, because no rate here covers them:":
        "No contados, porque ningún tipo de cambio aquí los cubre:",
    "Fetch rates under {settings}.":
        "Descarga los tipos en {settings}.",
    "Budgeted": "Presupuestado",
    "Spent so far": "Gastado hasta ahora",
    "Remaining": "Restante",
    "for {month}": "para {month}",
    "day {day} of {days} · {pct}% through the month":
        "día {day} de {days} · {pct} % del mes",
    "budget less spending": "presupuesto menos gasto",
    "Budget against spent": "Presupuesto frente a gasto",
    "this month, per category — the chart follows the fields below as you type":
        "este mes, por categoría — el gráfico sigue los campos de abajo mientras escribes",
    "in {currency}": "en {currency}",
    "Everything you hold, aggregated by ISIN across accounts — the same fund at two brokers is one position from where you are standing. Values use the last market price, and each one names its day; a holding no price could be found for uses the price of your last trade, and says so.":
        "Todo lo que tienes, agrupado por ISIN entre cuentas — el mismo fondo en dos brókeres es una sola posición desde donde estás. Valorado al último precio de mercado, y cada uno indica su día; una posición para la que no se encontró precio usa el de tu última operación, y lo dice.",
    "Every holding is valued at its last market price — free, without a key — and every total built from prices names their day. A broker export gives an ISIN and a price source wants a ticker, so the ticker is looked up once and kept. Where the lookup fails or picks the wrong exchange, type the ticker Yahoo uses, like IWDA.AS; what you type is never replaced by a lookup.":
        "Cada posición se valora a su último precio de mercado — gratis, sin clave — y cada total construido con precios indica su día. Una exportación del bróker da un ISIN y una fuente de precios quiere un ticker, así que el ticker se busca una vez y se guarda. Donde la búsqueda falla o elige la bolsa equivocada, escribe el ticker que usa Yahoo, como IWDA.AS; lo que escribes nunca lo sustituye una búsqueda.",
    "Also updated on start-up and every few hours in the background. A holding no price could be found for is valued at your last trade, and the pages say so.":
        "También se actualiza al arrancar y cada pocas horas en segundo plano. Una posición sin precio encontrado se valora a tu última operación, y las páginas lo dicen.",
    "Nothing to price yet — holdings appear here once a broker export or a trade typed in by hand has given you one.":
        "Nada que valorar todavía — las posiciones aparecen aquí cuando una exportación del bróker o una operación introducida a mano te da una.",
    "Market prices": "Precios de mercado",
    "Yahoo Finance": "Yahoo Finance",
    "Price": "Precio",
    "Ticker": "Ticker",
    "Ticker for {name}": "Ticker de {name}",
    "Update prices now": "Actualizar precios ahora",
    "Priced.": "Valorado.",
    "at market prices of {date}": "a precios de mercado del {date}",
    "last trade, no market price":
        "última operación, sin precio de mercado",
    "{n} holding at its last traded price":
        "{n} posición a su último precio operado",
    "{n} holdings at their last traded price":
        "{n} posiciones a su último precio operado",
    "{n} holding priced.": "{n} posición valorada.",
    "{n} holdings priced.": "{n} posiciones valoradas.",
    "{ok} of {held} holdings priced. Could not price: {failed}.":
        "{ok} de {held} posiciones valoradas. Sin precio para: {failed}.",

    # ─── Personas ────────────────────────────────────────────────────
    "A person needs a name.":
        "Una persona necesita un nombre.",
    "Add person":
        "Añadir persona",
    "Add the people in your household, then tick on each account who it belongs to — one person, or several for a joint account. A switch appears in the header: Everyone shows the whole household, a name shows only that person's accounts on every page. An account ticked for nobody shows under Everyone only. This is a lens, not a lock: anyone who can sign in can flip it.":
        "Añade a las personas de tu hogar y marca en cada cuenta a quién pertenece — a una persona, o a varias si es una cuenta conjunta. En la cabecera aparece un selector: «Todos» muestra el hogar entero, un nombre muestra solo las cuentas de esa persona en cada página. Una cuenta sin marcar solo aparece bajo «Todos». Es una lente, no un candado: cualquiera que pueda iniciar sesión puede cambiarla.",
    "Alex":
        "Alex",
    "Everyone":
        "Todos",
    "New person":
        "Nueva persona",
    "No people yet. Add the household under Settings → People, and each account can be somebody's.":
        "Aún no hay personas. Crea el hogar en Ajustes → Personas y cada cuenta podrá ser de alguien.",
    "Only {name}'s accounts are counted on this page.":
        "En esta página solo cuentan las cuentas de {name}.",
    "People":
        "Personas",
    "Remove {name}? Their accounts stay.":
        "¿Quitar a {name}? Sus cuentas se quedan.",
    "Removed. Their accounts stay; they just belong to one person fewer.":
        "Quitada. Las cuentas se quedan; solo pertenecen a una persona menos.",
    "The budget itself is the household's; the spending measured against it here is {name}'s alone.":
        "El presupuesto es del hogar; el gasto que aquí se mide contra él es solo el de {name}.",
    "There is already somebody called {name}.":
        "Ya hay alguien que se llama {name}.",
    "Tick one person, or several for a joint account. Nobody ticked means it shows only under Everyone.":
        "Marca a una persona, o a varias si es una cuenta conjunta. Sin marcar, solo aparece bajo «Todos».",
    "Whose":
        "De quién",
    "Whose accounts":
        "Cuentas de quién",
    "Whose is it":
        "De quién es",
    "nobody yet":
        "de nadie aún",
    "whose accounts are whose":
        "de quién es cada cuenta",
    "{n} account":
        "{n} cuenta",
    "{n} accounts":
        "{n} cuentas",
    "{n} more account belongs to somebody else, or to nobody yet — switch to Everyone to see it.":
        "{n} cuenta más pertenece a otra persona, o a nadie aún — cambia a «Todos» para verla.",
    "{n} more accounts belong to somebody else, or to nobody yet — switch to Everyone to see them.":
        "{n} cuentas más pertenecen a otra persona, o a nadie aún — cambia a «Todos» para verlas.",
    "Belongs to {names}.":
        "Pertenece a {names}.",
    "Belongs to nobody yet, so it shows under Everyone only.":
        "Aún no pertenece a nadie, así que solo aparece bajo «Todos».",
    "Change":
        "Cambiar",

    # ─── Proyección y sincronización ─────────────────────────────────
    "A goal to mark, in {currency}":
        "Una meta que marcar, en {currency}",
    "Amounts in a currency with no rate on file are not in that figure.":
        "Los importes en una moneda sin tipo de cambio registrado no están en esa cifra.",
    "At":
        "A las",
    "Automatic sync is off.":
        "La sincronización automática está apagada.",
    "Average return per year, in %":
        "Rentabilidad media anual, en %",
    "Bank sync":
        "Sincronización bancaria",
    "Before inflation. Broad stock-market funds have averaged around 6–8 % a year over long periods, savings accounts far less; a cautious plan uses a lower number than history did.":
        "Antes de inflación. Los fondos de bolsa amplios han rendido de media un 6–8 % al año en periodos largos, las cuentas de ahorro mucho menos; un plan prudente usa una cifra menor que la histórica.",
    "Calculate":
        "Calcular",
    "Forecast":
        "Proyección",
    "Goal":
        "Meta",
    "Goal, in {currency}":
        "Meta, en {currency}",
    "I have a goal":
        "Tengo una meta",
    "I save a fixed amount":
        "Ahorro una cantidad fija",
    "In {year}":
        "En {year}",
    "Last automatic sync: {when}.":
        "Última sincronización automática: {when}.",
    "Local time of the machine this runs on. A day that was slept through — the machine was off at that hour — is caught up as soon as it is next awake.":
        "Hora local de la máquina donde corre esto. Un día perdido — la máquina estaba apagada a esa hora — se recupera en cuanto vuelve a estar despierta.",
    "No account is connected to a bank yet.":
        "Ninguna cuenta está conectada a un banco todavía.",
    "No automatic sync has run yet.":
        "Aún no se ha ejecutado ninguna sincronización automática.",
    "Returns":
        "Rentabilidad",
    "Returns earn":
        "La rentabilidad aporta",
    "Save per month":
        "Ahorrar al mes",
    "Saved per month, in {currency}":
        "Ahorrado al mes, en {currency}",
    "Show as a table":
        "Mostrar como tabla",
    "Starting from {amount}: what {who} adds up to today across {n} accounts.":
        "Partiendo de {amount}: lo que {who} suma hoy en {n} cuentas.",
    "Sync all accounts now":
        "Sincronizar todas las cuentas ahora",
    "Sync connected accounts automatically every day":
        "Sincronizar las cuentas conectadas automáticamente cada día",
    "The goal is already met — nothing more is needed.":
        "La meta ya está cumplida — no hace falta nada más.",
    "The next one is at {time}.":
        "La siguiente es a las {time}.",
    "What to work out":
        "Qué calcular",
    "Where the money is heading, starting from what the accounts add up to today. The return is your assumption, not a prediction — the page only does the arithmetic, and shows how much of the result is your own deposits.":
        "Hacia dónde va el dinero, partiendo de lo que las cuentas suman hoy. La rentabilidad es tu supuesto, no una predicción — la página solo hace la aritmética, y muestra cuánto del resultado son tus propias aportaciones.",
    "With returns":
        "Con rentabilidad",
    "Year":
        "Año",
    "Year by year":
        "Año a año",
    "Years from now":
        "Años a partir de hoy",
    "You put in":
        "Tú aportas",
    "and want to know what it takes a month":
        "y quiero saber qué hace falta al mes",
    "and want to see where it leads":
        "y quiero ver adónde lleva",
    "at {rate} % a year, compounding monthly":
        "al {rate} % anual, capitalizando cada mes",
    "the goal is not reached in this time":
        "la meta no se alcanza en ese tiempo",
    "the goal is reached in {year}":
        "la meta se alcanza en {year}",
    "the household":
        "el hogar",
    "to reach {target} by {year}":
        "para llegar a {target} en {year}",
    "today's {start} plus {monthly} a month":
        "los {start} de hoy más {monthly} al mes",
    "{n} account connected":
        "{n} cuenta conectada",
    "{n} accounts connected":
        "{n} cuentas conectadas",
    "{n} new transaction across {accounts} accounts.":
        "{n} transacción nueva en {accounts} cuentas.",
    "{n} new transactions across {accounts} accounts.":
        "{n} transacciones nuevas en {accounts} cuentas.",
    "{n} year from now":
        "dentro de {n} año",
    "{n} years from now":
        "dentro de {n} años",
    "{ok} of {total} accounts synced. Failed: {names}.":
        "{ok} de {total} cuentas sincronizadas. Fallaron: {names}.",

    # ─── Historial, conexiones, jubilación ───────────────────────────
    "A birthday is optional; with one, the Forecast page adds a retirement outlook for that person.":
        "La fecha de nacimiento es opcional; con ella, la página Proyección añade una perspectiva de jubilación para esa persona.",
    "Add the people in your household under Settings → People, each with a birthday, and this page will say where each of them stands for retirement.":
        "Añade a las personas de tu hogar en Ajustes → Personas, cada una con su fecha de nacimiento, y esta página dirá cómo va cada una de cara a la jubilación.",
    "Age":
        "Edad",
    "All":
        "Todo",
    "At {age}, in {year}":
        "A los {age}, en {year}",
    "Bank connections":
        "Conexiones bancarias",
    "Birthday of {name}":
        "Fecha de nacimiento de {name}",
    "Birthday — what the retirement outlook counts from":
        "Fecha de nacimiento — desde la que cuenta la perspectiva de jubilación",
    "Consent expired — reconnect.":
        "Consentimiento caducado — vuelve a conectar.",
    "Last sync failed: {error}":
        "La última sincronización falló: {error}",
    "Last sync {n} days ago.":
        "Última sincronización hace {n} días.",
    "Last sync {n} hours ago.":
        "Última sincronización hace {n} horas.",
    "Never synced.":
        "Nunca sincronizado.",
    "No birthday on file for {names}. Add one under Settings → People and the outlook appears here.":
        "No hay fecha de nacimiento para {names}. Añádela en Ajustes → Personas y la perspectiva aparecerá aquí.",
    "No dated readings yet — the line starts with the first balance or trade.":
        "Aún no hay lecturas con fecha — la línea empieza con el primer saldo u operación.",
    "Overrides the Forecast plan's {amount}; clear the field to follow it again.":
        "Sustituye los {amount} del plan de Proyección; vacía el campo para volver a seguirlo.",
    "Records go back to {date}; the line fills in with every daily sync.":
        "Los registros llegan hasta el {date}; la línea se completa con cada sincronización diaria.",
    "Retire at":
        "Jubilarse a los",
    "Retirement outlook":
        "Perspectiva de jubilación",
    "Return per year, %":
        "Rentabilidad anual, %",
    "Saved per month, {currency}":
        "Ahorrado al mes, {currency}",
    "Saved.":
        "Guardado.",
    "Supports, per month":
        "Da para, al mes",
    "Synced {n} hours ago":
        "Sincronizado hace {n} horas",
    "The birthday needs to be a date.":
        "La fecha de nacimiento tiene que ser una fecha.",
    "The monthly amount is taken from this person's Forecast plan; type one to override it.":
        "El importe mensual sale del plan de Proyección de esta persona; escribe uno para sustituirlo.",
    "Time range":
        "Periodo",
    "at a 4 % yearly withdrawal — the usual rule of thumb, before tax and pension":
        "con una retirada del 4 % anual — la regla habitual, antes de impuestos y pensión",
    "consent for {n} more days":
        "consentimiento {n} días más",
    "since the start of the range":
        "desde el inicio del periodo",
    "{age} today · {n} accounts · {amount}":
        "{age} hoy · {n} cuentas · {amount}",
    "{name} is already {age} — past the retirement age set here.":
        "{name} ya tiene {age} — más que la edad de jubilación fijada aquí.",
    "{n} connected account":
        "{n} cuenta conectada",
    "{n} connected accounts":
        "{n} cuentas conectadas",
    "{part} of it returns":
        "{part} de ello es rentabilidad",

    # ─── Ideas de acciones ───────────────────────────────────────────
    "Share Ideas": "Ideas de acciones",
    "Four boards over the same nightly Yahoo cache: shares that have fallen and are cheap, shares paying a high dividend that is still growing, ETFs with strong past growth at a low TER, and dividend ETFs paying a high yield at a low TER. A shortlist to research, never a recommendation to buy.":
        "Cuatro tablas sobre la misma caché de Yahoo, renovada cada noche: acciones que han caído y están baratas, acciones con un dividendo alto que sigue creciendo, ETF con fuerte crecimiento pasado y TER bajo, y ETF de dividendos con alta rentabilidad y TER bajo. Una lista para investigar, nunca una recomendación de compra.",
    "Value [board]": "Valor",
    "fallen · cheap · quality · pays": "caído · barato · calidad · paga",
    "Dividends": "Dividendos",
    "high yield that is still growing": "alta rentabilidad que sigue creciendo",
    "ETFs": "ETF",
    "high growth · low TER": "alto crecimiento · TER bajo",
    "Dividend ETFs": "ETF de dividendos",
    "high yield · low TER": "alta rentabilidad · TER bajo",
    "The board": "La tabla",
    "Loading…": "Cargando…",
    "Names that pass every hard gate and therefore carry a score.":
        "Valores que superan todos los filtros duros y por tanto llevan puntuación.",
    "Ranked candidates": "Candidatos clasificados",
    "Scored 70 or above out of 100 on this board.":
        "Con 70 o más sobre 100 en esta tabla.",
    "Strong (70+)": "Fuertes (70+)",
    "Can sit inside a French PEA. For shares this is inferred from the country of incorporation; for ETFs it is a curated fact, because no data source publishes it.":
        "Puede estar dentro de un PEA francés. En acciones se deduce del país de constitución; en ETF es un dato mantenido a mano, porque ninguna fuente lo publica.",
    "PEA-eligible": "Apto para PEA",
    "Excluded before scoring, with the reason kept. Listed at the bottom of the page.":
        "Excluidos antes de puntuar, con el motivo guardado. Listados al pie de la página.",
    "Gated out": "Excluidos",
    "The screen is transparent on purpose — every column below is an input to the score, not an output of it.":
        "El filtro es transparente a propósito: cada columna de abajo es un ingrediente de la puntuación, no un resultado.",
    "PEA-eligible only": "Solo aptos para PEA",
    "Hide what I already own": "Ocultar lo que ya tengo",
    "Hide dismissed": "Ocultar descartados",
    "Watchlist only": "Solo la lista de seguimiento",
    "Sector": "Sector",
    "Min score": "Puntuación mínima",
    "Show": "Mostrar",
    "all": "todos",
    "Candidates": "Candidatos",
    "Click a row for the full breakdown.": "Pulsa una fila para ver el desglose completo.",
    "Excluded before scoring, and why. Shown because an absence you cannot explain is worse than no screen at all.":
        "Excluidos antes de puntuar, y por qué. Se muestran porque una ausencia que no puedes explicar es peor que no filtrar.",
    "Symbol": "Símbolo",
    "Group": "Grupo",
    "Reason": "Motivo",
    "Close": "Cerrar",
    "How to read this": "Cómo leer esto",
    "Value 25% · cheapness 25% · quality 30% · dividend 20%. It finds shares that have fallen a long way from their own 52-week high and are cheap on earnings while still earning well and paying a covered dividend.":
        "Valor 25 % · baratura 25 % · calidad 30 % · dividendo 20 %. Encuentra acciones que han caído mucho desde su máximo de 52 semanas y están baratas respecto a sus beneficios, mientras siguen ganando bien y pagando un dividendo cubierto.",
    "The flag that matters most is “near its 52-week low”. “40% off the high” and “still falling” are the same fact seen from two ends, and only the second tells you the market has not finished selling.":
        "El aviso que más importa es «cerca de su mínimo de 52 semanas». «Un 40 % bajo el máximo» y «sigue cayendo» son el mismo hecho visto desde dos extremos, y solo el segundo te dice que el mercado no ha terminado de vender.",
    "Yield 35% · growth 30% · safety 20% · quality 15%. Yield and growth carry most of it, as they should on an income board — but not all of it, because a ranking on yield alone puts the next dividend cut at the top of the list every single time. The growth pillar blends dividend growth (the forward annual rate against the last twelve months' actual), revenue growth and earnings growth.":
        "Rentabilidad 35 % · crecimiento 30 % · seguridad 20 % · calidad 15 %. Rentabilidad y crecimiento llevan la mayor parte, como corresponde a una tabla de rentas, pero no todo, porque una clasificación solo por rentabilidad pone el próximo recorte de dividendo en cabeza cada vez. El pilar de crecimiento mezcla el crecimiento del dividendo (la tasa anual anunciada frente a la pagada en los últimos doce meses), el de ingresos y el de beneficios.",
    "A yield above 12% is gated out rather than rewarded: on a large cap that is the market pricing a cut, not an opportunity. So is a payout ratio above 90%, and a business whose revenue is shrinking. The free-cash-flow payout is the column to look at when two names have the same yield — earnings can be flattered, cash cannot, and a dividend costing more than 100% of free cash flow is being paid out of the balance sheet.":
        "Una rentabilidad superior al 12 % se excluye en lugar de premiarse: en una gran empresa es el mercado descontando un recorte, no una oportunidad. Igual con un ratio de reparto superior al 90 % y con un negocio cuyos ingresos se reducen. El reparto sobre flujo de caja libre es la columna a mirar cuando dos valores tienen la misma rentabilidad: los beneficios se maquillan, la caja no, y un dividendo que cuesta más del 100 % del flujo libre se paga con el balance.",
    "Growth 40% · cost 30% · risk 20% · size 10%. Growth is the compound annual total return in euros, computed from the adjusted price history rather than read from a field — Yahoo leaves its own return fields empty for almost every European UCITS listing, and the raw price of a distributing fund understates its return by roughly its yield every year.":
        "Crecimiento 40 % · coste 30 % · riesgo 20 % · tamaño 10 %. El crecimiento es la rentabilidad total anualizada en euros, calculada a partir del historial de precios ajustado en lugar de leída de un campo: Yahoo deja vacíos sus propios campos de rentabilidad en casi todas las cotizaciones UCITS europeas, y el precio bruto de un fondo de distribución infravalora su rentabilidad cada año en más o menos lo que reparte.",
    "The growth column is the past and the TER is the future. Five years that contained one of the strongest US equity runs on record will rank concentration highly for reasons that have already happened. The TER is charged every year whatever the market does — which is why cost carries 30% of a board whose headline is growth.":
        "La columna de crecimiento es el pasado y el TER es el futuro. Cinco años que contienen una de las mayores subidas de la bolsa estadounidense clasificarán alto la concentración por motivos que ya ocurrieron. El TER se cobra cada año haga lo que haga el mercado; por eso el coste pesa un 30 % en una tabla cuyo título es crecimiento.",
    "The universe is UCITS-only on purpose: without a PRIIPs KID a US-listed ETF cannot be bought at a European broker at all, so ranking one would be ranking something unbuyable. PEA eligibility is a curated fact, not an inferred one — it depends on the fund's holdings and wrapper, and a synthetic MSCI World qualifies where a physical one does not.":
        "El universo es solo UCITS a propósito: sin KID PRIIPs, un ETF cotizado en EE. UU. no se puede comprar en un bróker europeo, así que clasificarlo sería clasificar algo incomprable. La aptitud para PEA es un dato mantenido a mano, no deducido: depende de las posiciones y la envoltura del fondo, y un MSCI World sintético se califica donde uno físico no.",
    "Yield 35% · cost 25% · growth 20% · stability 20%. The yield is computed from the distributions the fund actually paid over the last twelve months, not read from a field — Yahoo populates its own yield for barely one European listing in six, so a board that trusted it would be blank for five funds out of every six it ranks.":
        "Rentabilidad 35 % · coste 25 % · crecimiento 20 % · estabilidad 20 %. La rentabilidad se calcula con los repartos que el fondo pagó realmente en los últimos doce meses, no se lee de un campo: Yahoo rellena su propia rentabilidad en apenas una de cada seis cotizaciones europeas, así que una tabla que confiara en ella quedaría vacía en cinco de cada seis fondos.",
    "It will read lower than the yield on the factsheet. The numerator is the past year's payments and the denominator is today's price, so a fund that has risen shows a smaller ratio than the “indicated” yield a provider quotes. Both are honest; this one is backward-looking on purpose, because a forward yield is an estimate and there are enough estimates on this page already.":
        "Saldrá más baja que la rentabilidad de la ficha. El numerador son los pagos del último año y el denominador el precio de hoy, así que un fondo que ha subido muestra un ratio menor que la rentabilidad «indicativa» de la gestora. Ambas son honestas; esta mira atrás a propósito, porque una rentabilidad futura es una estimación y ya hay bastantes en esta página.",
    "Yield is only 35% for the same reason it is on the share board, and the reason bites harder here: an index that selects on yield mechanically buys whatever has just fallen. Worse, a fund has no payout ratio and no balance sheet you can interrogate — so the only evidence that its income is durable is whether it has ever collapsed. That is the Worst cut column, and it carries most of the stability pillar.":
        "La rentabilidad pesa solo un 35 % por la misma razón que en la tabla de acciones, y aquí muerde más: un índice que selecciona por rentabilidad compra mecánicamente lo que acaba de caer. Peor aún, un fondo no tiene ratio de reparto ni balance que interrogar, así que la única prueba de que su renta es duradera es si alguna vez se ha desplomado. Esa es la columna «Peor recorte», y lleva la mayor parte del pilar de estabilidad.",
    "Cost is 25% because the TER comes out of the same cash the distribution does. At a 3.5% yield a 0.45% TER is not “half a percent” — it is 13% of your income, every year, guaranteed. The Net column does that subtraction. Accumulating share classes are gated out: they pay nothing, which does not make them bad funds, only not income ones.":
        "El coste pesa un 25 % porque el TER sale de la misma caja que el reparto. Con una rentabilidad del 3,5 %, un TER del 0,45 % no es «medio punto»: es el 13 % de tu renta, cada año, garantizado. La columna «Neto» hace esa resta. Las clases de acumulación quedan excluidas: no pagan nada, lo que no las convierte en malos fondos, solo en fondos que no son de rentas.",
    "Every score is a sorting device for a research queue, not a valuation and not advice. Fundamentals come from Yahoo and are refreshed once a day in the background; they can be wrong, stale, or reported in a currency other than the price. Verify the two or three names you actually care about at the source before doing anything.":
        "Cada puntuación es una herramienta para ordenar una cola de investigación, no una valoración ni un consejo. Los fundamentales vienen de Yahoo y se renuevan una vez al día en segundo plano; pueden estar mal, desfasados o en una moneda distinta a la del precio. Comprueba en la fuente los dos o tres valores que de verdad te interesan antes de hacer nada.",

    # Columnas y abreviaturas
    "Score": "Puntos",
    "Pillars": "Pilares",
    "Off high": "Bajo máximo",
    "P/E": "PER",
    "Yield": "Rentabilidad",
    "Payout": "Reparto",
    "ROE": "ROE",
    "Debt/Eq": "Deuda/FP",
    "Div growth": "Crec. div.",
    "Rev growth": "Crec. ingresos",
    "EPS growth": "Crec. BPA",
    "FCF payout": "Reparto / FCF",
    "5y p.a.": "5 a. anual",
    "3y p.a.": "3 a. anual",
    "1y": "1 a.",
    "Vol": "Vol.",
    "Max DD": "Caída máx.",
    "Policy": "Política",
    "Size": "Tamaño",
    "Net": "Neto",
    "Worst cut": "Peor recorte",
    "Pays": "Paga",
    "Region": "Región",
    "no data": "sin datos",
    "held": "en cartera",
    "Already in the portfolio": "Ya en la cartera",
    "Can sit in a French PEA.": "Puede estar dentro de un PEA francés.",
    "watching": "en seguimiento",
    "dismissed": "descartado",
    "Add to watchlist": "Añadir a la lista de seguimiento",
    "Dismiss": "Descartar",
    "☆ Watch": "☆ Seguir",
    "✕ Dismiss": "✕ Descartar",
    "Clear mark": "Quitar la marca",
    "Open on Yahoo ↗": "Abrir en Yahoo ↗",
    "Nothing matches these filters.": "Nada coincide con estos filtros.",
    "Nothing gated out.": "Nada excluido.",
    "Gated out:": "Excluido:",
    "Last fetch error:": "Último error de descarga:",
    "data coverage": "cobertura de datos",
    "mkt cap": "cap.",
    "yes": "sí",
    "no": "no",
    "yes (EU/EEA seat)": "sí (sede en UE/EEE)",
    "no — outside a PEA only": "no: solo fuera de un PEA",
    "never fell": "nunca bajó",
    "× a year": "× al año",
    "Failed to load": "No se pudo cargar",
    "Loaded, but failed to render — see the console":
        "Cargado, pero no se pudo mostrar: mira la consola",
    "{n} screened · last refresh {date}": "{n} analizados · última actualización {date}",
    "This cache is empty. The first refresh starts a minute after start-up and takes a few minutes; there is also a button under Settings.":
        "Esta caché está vacía. La primera actualización empieza un minuto después del arranque y tarda unos minutos; también hay un botón en Ajustes.",
    "Data was last refreshed {days} days ago. Every price-derived figure below is that old.":
        "Los datos se actualizaron hace {days} días. Cada cifra derivada de un precio tiene esa antigüedad.",
    "{n} symbol(s) failed their last fetch and are showing older figures.":
        "{n} símbolo(s) fallaron en su última descarga y muestran cifras más antiguas.",
    "Hide": "Ocultar",
    "A hollow bar means there was no data for that pillar — the score is then a mean over the pillars that do have data, which is why thin rows carry a “thin data” flag.":
        "Una barra hueca significa que no había datos para ese pilar; la puntuación es entonces la media de los pilares con datos, por eso las filas escasas llevan el aviso «datos escasos».",
    "Trailing where there is a trailing profit, otherwise the forward estimate (marked ƒ).":
        "De los últimos doce meses cuando hay beneficio; si no, la estimación futura (marcada con ƒ).",
    "Yahoo’s figure, not the KID’s": "Cifra de Yahoo, no del KID",
    "value": "valor",
    "cheap": "barato",
    "quality": "calidad",
    "dividend": "dividendo",
    "yield": "rentabilidad",
    "growth": "crecimiento",
    "safety": "seguridad",
    "cost": "coste",
    "risk": "riesgo",
    "size": "tamaño",
    "stability": "estabilidad",
    "Ongoing charge per year. Curated from the fund KID where we have it; Yahoo otherwise, which is then flagged.":
        "Gastos corrientes al año. Del KID del fondo cuando lo tenemos; si no, de Yahoo, y entonces se señala.",

    # Las cuatro tablas
    "Cheap and beaten down": "Barato y castigado",
    "Shares that have fallen from their own 52-week high, trade on a low P/E, still earn well, and pay a dividend their earnings cover.":
        "Acciones que han caído desde su máximo de 52 semanas, cotizan con un PER bajo, siguen ganando bien y pagan un dividendo cubierto por sus beneficios.",
    "Pillar bars are, left to right: value (how far it has fallen), cheap (P/E and price-to-book), quality (ROE, operating margin, leverage, liquidity), dividend (yield, and whether earnings cover it).":
        "Las barras de los pilares son, de izquierda a derecha: valor (cuánto ha caído), barato (PER y precio sobre valor contable), calidad (ROE, margen operativo, apalancamiento, liquidez), dividendo (rentabilidad, y si los beneficios lo cubren).",
    "How far below its own 52-week high the price sits.":
        "Cuánto está el precio por debajo de su máximo de 52 semanas.",
    "Share of earnings paid out as dividend. Sweet spot 25–60%.":
        "Parte del beneficio repartida como dividendo. Lo ideal, entre el 25 y el 60 %.",
    "Ratio, not percent. Above 2.0 is flagged.": "Un ratio, no un porcentaje. Se señala por encima de 2,0.",
    "High dividend, still growing": "Dividendo alto, que sigue creciendo",
    "The highest yields that are not warning you about themselves: the dividend must be growing, covered by earnings AND by free cash flow, on a business that is not shrinking.":
        "Las rentabilidades más altas que no te avisan de sí mismas: el dividendo debe crecer, estar cubierto por beneficios Y por flujo de caja libre, en un negocio que no se reduce.",
    "Pillar bars are, left to right: yield (what it pays today), growth (dividend, revenue and earnings growth), safety (payout ratio, free-cash-flow cover, leverage, liquidity), quality (ROE and margins). Dividend growth is the forward annual rate against the last twelve months actually paid, so a declared cut shows up here the day it is announced rather than a year later.":
        "Las barras de los pilares son, de izquierda a derecha: rentabilidad (lo que paga hoy), crecimiento (de dividendo, ingresos y beneficios), seguridad (ratio de reparto, cobertura por flujo libre, apalancamiento, liquidez), calidad (ROE y márgenes). El crecimiento del dividendo es la tasa anual anunciada frente a lo pagado realmente en los últimos doce meses, así que un recorte declarado aparece aquí el día del anuncio y no un año después.",
    "Forward annual dividend against the last twelve months actually paid. Negative = a cut has been declared.":
        "Dividendo anual anunciado frente al pagado realmente en los últimos doce meses. Negativo = se ha declarado un recorte.",
    "Share of EARNINGS paid out.": "Parte de los BENEFICIOS repartida.",
    "Share of FREE CASH FLOW paid out. Above 100% the dividend is coming out of the balance sheet.":
        "Parte del FLUJO DE CAJA LIBRE repartida. Por encima del 100 %, el dividendo sale del balance.",
    "High growth, low TER": "Alto crecimiento, TER bajo",
    "UCITS ETFs ranked on compound annual total return in EUR against what they charge for it. Growth is the past; the TER is the only column here that is a fact about the future.":
        "ETF UCITS clasificados por rentabilidad total anualizada en EUR frente a lo que cobran por ella. El crecimiento es el pasado; el TER es la única columna aquí que es un hecho sobre el futuro.",
    "Pillar bars are, left to right: growth (5-year and 3-year CAGR in EUR, total return), cost (TER), risk (return per unit of volatility, and the worst peak-to-trough fall in the window), size (fund assets — a small fund can close, and trades on a wider spread). Returns are converted to euros before they are measured: a USD-quoted UCITS ETF and its EUR-quoted twin are the same fund, and comparing their raw returns would rank the dollar.":
        "Las barras de los pilares son, de izquierda a derecha: crecimiento (rentabilidad anualizada a 5 y 3 años en EUR, total), coste (TER), riesgo (rentabilidad por unidad de volatilidad, y peor caída de máximo a mínimo en la ventana), tamaño (patrimonio: un fondo pequeño puede cerrar y cotiza con más horquilla). Las rentabilidades se convierten a euros antes de medirlas: un ETF UCITS cotizado en USD y su gemelo en EUR son el mismo fondo, y comparar sus rentabilidades brutas clasificaría al dólar.",
    "Compound annual total return over five years, in EUR.":
        "Rentabilidad total anualizada a cinco años, en EUR.",
    "Annualised standard deviation of weekly returns over the last year.":
        "Desviación típica anualizada de las rentabilidades semanales del último año.",
    "Worst peak-to-trough fall within the cached history.":
        "Peor caída de máximo a mínimo dentro del historial en caché.",
    "acc = accumulating (nothing is paid out, nothing is taxed until you sell). dist = distributing.":
        "acc = de acumulación (no se paga nada, no tributa nada hasta que vendes). dist = de distribución.",
    "High yield, low TER": "Alta rentabilidad, TER bajo",
    "Distributing UCITS ETFs ranked on the income they actually paid over the last twelve months against what they charge for it — and on whether that income is growing rather than being cut. Accumulating share classes are excluded: they pay nothing.":
        "ETF UCITS de distribución clasificados por la renta que pagaron realmente en los últimos doce meses frente a lo que cobran por ella, y por si esa renta crece en vez de recortarse. Las clases de acumulación quedan fuera: no pagan nada.",
    "Pillar bars are, left to right: yield (distributions paid over the last twelve months, divided by today’s price), cost (TER), growth (this year’s distributions against last year’s, plus the price return as a check that the income is not just capital coming back), stability (the worst year-on-year fall in the distribution on record, and the worst peak-to-trough price fall). The yield is computed from the distributions themselves, not read from a field — Yahoo populates its own yield for barely one European listing in six. Because the numerator is the past year and the denominator is today’s price, it reads lower than a provider’s “indicated yield” whenever the fund has risen.":
        "Las barras de los pilares son, de izquierda a derecha: rentabilidad (repartos de los últimos doce meses divididos por el precio de hoy), coste (TER), crecimiento (los repartos de este año frente a los del anterior, más la rentabilidad del precio como comprobación de que la renta no es solo capital que vuelve), estabilidad (la peor caída anual del reparto registrada y la peor caída del precio de máximo a mínimo). La rentabilidad se calcula con los propios repartos, no se lee de un campo: Yahoo rellena la suya en apenas una de cada seis cotizaciones europeas. Como el numerador es el último año y el denominador el precio de hoy, sale más baja que la «rentabilidad indicativa» de la gestora siempre que el fondo haya subido.",
    "Distributions actually paid over the last 12 months, divided by the current price.":
        "Repartos pagados realmente en los últimos 12 meses, divididos por el precio actual.",
    "Yield minus TER — the income that reaches you before tax. Shown, never ranked on: a high net yield can come from paying a lot or from costing little, and those are different funds.":
        "Rentabilidad menos TER: la renta que te llega antes de impuestos. Se muestra, nunca se usa para clasificar: una rentabilidad neta alta puede venir de pagar mucho o de costar poco, y son fondos distintos.",
    "Distributions of the last 12 months against the 12 before. Negative = the payout is shrinking.":
        "Repartos de los últimos 12 meses frente a los 12 anteriores. Negativo = el reparto se reduce.",
    "The deepest year-on-year fall in the distribution across the years on record. “none” means every year on record was at least as big as the one before. Blank means there is not enough history to say.":
        "La mayor caída anual del reparto en los años registrados. «ninguna» significa que cada año registrado fue al menos tan grande como el anterior. En blanco significa que no hay historial suficiente para decirlo.",
    "Compound annual TOTAL return in EUR — price plus distributions reinvested. A high yield beside a poor total return means capital is being handed back.":
        "Rentabilidad TOTAL anualizada en EUR: precio más repartos reinvertidos. Una rentabilidad alta junto a una rentabilidad total pobre significa que se está devolviendo capital.",
    "Distributions in the last 12 months: 1 = annual, 2 = semi-annual, 4 = quarterly, 12 = monthly.":
        "Repartos en los últimos 12 meses: 1 = anual, 2 = semestral, 4 = trimestral, 12 = mensual.",

    # El panel de detalle
    "Trailing yield": "Rentabilidad a 12 meses",
    "Distributions paid over the last 12 months divided by the current price. Computed from the payments themselves — Yahoo’s own yield field is populated for barely one European listing in six.":
        "Repartos pagados en los últimos 12 meses divididos por el precio actual. Calculado con los propios pagos: el campo de rentabilidad de Yahoo está relleno en apenas una de cada seis cotizaciones europeas.",
    "Charged out of the same cash the distribution comes from.":
        "Se cobra de la misma caja de la que sale el reparto.",
    "Net yield": "Rentabilidad neta",
    "Yield minus TER, before any tax. Shown but never ranked on — a high net yield can come from paying a lot or from costing little.":
        "Rentabilidad menos TER, antes de impuestos. Se muestra pero nunca se usa para clasificar: una rentabilidad neta alta puede venir de pagar mucho o de costar poco.",
    "TER as a share of income": "TER como parte de la renta",
    "What proportion of the income the fund keeps. Half a percent sounds small until it is 13% of a 3.5% yield.":
        "Qué parte de la renta se queda el fondo. Medio punto parece poco hasta que es el 13 % de una rentabilidad del 3,5 %.",
    "Distributions, last 12m": "Repartos, últimos 12 m",
    "In the listing currency. A yield is a ratio, so it needs no currency conversion.":
        "En la moneda de cotización. Una rentabilidad es un ratio, así que no necesita conversión.",
    "Distributions, 12m before": "Repartos, 12 m anteriores",
    "Distribution growth": "Crecimiento del reparto",
    "This year’s total against last year’s.": "El total de este año frente al del anterior.",
    "Worst year on record": "Peor año registrado",
    "The deepest year-on-year fall in the distribution across the years available. An index fund has no payout ratio to interrogate, so this is the only evidence that its income is durable.":
        "La mayor caída anual del reparto en los años disponibles. Un fondo indexado no tiene ratio de reparto que interrogar, así que esta es la única prueba de que su renta es duradera.",
    "A change in frequency makes one year’s total incomparable with the next.":
        "Un cambio de frecuencia hace que el total de un año no sea comparable con el siguiente.",
    "Last distribution": "Último reparto",
    "Distribution history": "Historial de repartos",
    "5-year total return": "Rentabilidad total a 5 años",
    "Price plus distributions reinvested, in EUR. A high yield beside a weak total return means capital is being returned rather than earned.":
        "Precio más repartos reinvertidos, en EUR. Una rentabilidad alta junto a una rentabilidad total floja significa que se devuelve capital en vez de ganarlo.",
    "Max drawdown": "Caída máxima",
    "Fund size": "Patrimonio",
    "Policy (curated)": "Política (mantenida a mano)",
    "Cross-checked against the distributions actually observed; a disagreement is flagged rather than resolved silently.":
        "Contrastada con los repartos realmente observados; una discrepancia se señala en lugar de resolverse en silencio.",
    "Provider": "Gestora",
    "Matters more on an income holding than on an accumulating one: outside a PEA every distribution is taxed the year it is paid, so the headline yield is not the net one.":
        "Importa más en una posición de rentas que en una de acumulación: fuera de un PEA cada reparto tributa el año en que se paga, así que la rentabilidad bruta no es la neta.",
    "In the portfolio": "En la cartera",
    "Data fetched": "Datos descargados",
    "Curated from the fund KID where we have it — Yahoo has no expense ratio for most European listings, and reports it in two different units when it does.":
        "Del KID del fondo cuando lo tenemos: Yahoo no tiene gastos para la mayoría de cotizaciones europeas, y cuando los tiene los da en dos unidades distintas.",
    "Yahoo’s TER": "TER según Yahoo",
    "Kept as a cross-check. A disagreement usually means a different share class.":
        "Guardado como comprobación. Una discrepancia suele significar otra clase de participaciones.",
    "5-year CAGR": "Rentabilidad anualizada 5 años",
    "Compound annual total return in EUR, from the dividend-adjusted price history.":
        "Rentabilidad total anualizada en EUR, del historial de precios ajustado por dividendos.",
    "3-year CAGR": "Rentabilidad anualizada 3 años",
    "1-year return": "Rentabilidad 1 año",
    "Volatility (1y)": "Volatilidad (1 año)",
    "Annualised standard deviation of weekly returns.":
        "Desviación típica anualizada de las rentabilidades semanales.",
    "Worst peak-to-trough fall inside the cached history — measured on weekly closes, so it is a floor on the real figure.":
        "Peor caída de máximo a mínimo en el historial en caché, medida con cierres semanales, así que es un suelo de la cifra real.",
    "Return per unit of vol": "Rentabilidad por unidad de vol.",
    "3-year CAGR divided by volatility. Not a Sharpe ratio — no risk-free rate is subtracted.":
        "Rentabilidad anualizada a 3 años dividida por la volatilidad. No es un ratio de Sharpe: no se resta ningún tipo sin riesgo.",
    "A small fund can be closed and merged, and trades on a wider spread.":
        "Un fondo pequeño puede cerrarse y fusionarse, y cotiza con más horquilla.",
    "Distribution policy": "Política de distribución",
    "acc = accumulating. Outside a tax wrapper, a distributing fund is taxed on each distribution in the year it is paid.":
        "acc = de acumulación. Fuera de una envoltura fiscal, un fondo de distribución tributa por cada reparto el año en que se paga.",
    "History used": "Historial usado",
    "A curated fact, not an inferred one: it depends on the fund’s holdings and wrapper, and no data source publishes it.":
        "Un dato mantenido a mano, no deducido: depende de las posiciones y la envoltura del fondo, y ninguna fuente lo publica.",
    "Dividend yield": "Rentabilidad por dividendo",
    "5-year average yield": "Rentabilidad media a 5 años",
    "A yield far above its own average is often a falling price, not a rising dividend.":
        "Una rentabilidad muy por encima de su propia media suele ser un precio que cae, no un dividendo que sube.",
    "Payout ratio": "Ratio de reparto",
    "Share of earnings paid out.": "Parte del beneficio repartida.",
    "Trailing where there is a trailing profit, else forward.":
        "De los últimos doce meses cuando hay beneficio; si no, futuro.",
    "Trailing / forward P/E": "PER pasado / futuro",
    "Price / book": "Precio / valor contable",
    "Return on equity": "Rentabilidad sobre fondos propios",
    "Operating margin": "Margen operativo",
    "Profit margin": "Margen neto",
    "Debt / equity": "Deuda / fondos propios",
    "Ratio, not percent.": "Un ratio, no un porcentaje.",
    "Current ratio": "Ratio de liquidez",
    "Revenue growth": "Crecimiento de ingresos",
    "Earnings growth": "Crecimiento de beneficios",
    "Off 52-week high": "Bajo el máximo de 52 sem.",
    "Above 52-week low": "Sobre el mínimo de 52 sem.",
    "Small = the market may not have finished selling.":
        "Pequeño = puede que el mercado no haya terminado de vender.",
    "Beta": "Beta",
    "Indicative, from the reported country of incorporation. Confirm with the broker.":
        "Indicativo, del país de constitución declarado. Confírmalo con el bróker.",
    "Fundamentals fetched": "Fundamentales descargados",
    "Dividend growth": "Crecimiento del dividendo",
    "Forward annual dividend against the last twelve months actually paid.":
        "Dividendo anual anunciado frente al pagado realmente en los últimos doce meses.",
    "Forward / trailing dividend": "Dividendo anunciado / pagado",
    "Per share, in the reporting currency. Their ratio is the growth figure above.":
        "Por acción, en la moneda de reporte. Su cociente es la cifra de crecimiento de arriba.",
    "Free-cash-flow payout": "Reparto sobre flujo de caja libre",
    "Dividends as a share of free cash flow. Earnings can be flattered; cash cannot.":
        "Dividendos como parte del flujo de caja libre. Los beneficios se maquillan; la caja no.",
    "Free cash flow": "Flujo de caja libre",

    # Ajustes
    "refreshing now": "actualizando ahora",
    "last refreshed {when}": "última actualización {when}",
    "never refreshed": "nunca actualizado",
    "The four boards under Share Ideas rank a fixed list of shares and ETFs on figures fetched from Yahoo — free, without a key. The cache is refreshed once a day in the background; the first refresh runs a minute after start-up. A refresh is a few hundred requests with a pause between them and takes a few minutes, so it runs on its own and the boards fill in as it goes.":
        "Las cuatro tablas de Ideas de acciones clasifican una lista fija de acciones y ETF con cifras descargadas de Yahoo, gratis y sin clave. La caché se renueva una vez al día en segundo plano; la primera actualización arranca un minuto después del inicio. Una actualización son unos cientos de peticiones con pausa entre ellas y tarda unos minutos, así que va por su cuenta y las tablas se van rellenando.",
    "Shares: {n} cached, {errors} with a fetch error.":
        "Acciones: {n} en caché, {errors} con error de descarga.",
    "ETFs: {n} cached, {errors} with a fetch error.":
        "ETF: {n} en caché, {errors} con error de descarga.",
    "To screen more names, or to correct an ETF's TER, edit screener_universe.json and screener_etf_universe.json in the data folder; thresholds live in screener.json beside them. All three are read on every page load.":
        "Para analizar más valores o corregir el TER de un ETF, edita screener_universe.json y screener_etf_universe.json en la carpeta de datos; los umbrales están al lado, en screener.json. Los tres se leen en cada carga de página.",
    "Refresh share ideas now": "Actualizar las ideas de acciones ahora",
    "everything, not only what is older than a day":
        "todo, no solo lo que tiene más de un día",
    "Refreshing the share ideas in the background. It takes a few minutes; the boards fill in as it goes.":
        "Actualizando las ideas de acciones en segundo plano. Tarda unos minutos; las tablas se van rellenando.",
    "A refresh is already running.": "Ya hay una actualización en marcha.",

    # Filtros y avisos, redactados por el servidor
    "not a share ({type})": "no es una acción ({type})",
    "no market cap": "sin capitalización",
    "too small ({bn}bn)": "demasiado pequeña ({bn} mil M)",
    "no positive earnings": "sin beneficio positivo",
    "P/E too high ({pe})": "PER demasiado alto ({pe})",
    "pays no dividend": "no paga dividendo",
    "token dividend ({pct}%)": "dividendo simbólico ({pct} %)",
    "dividend not covered ({pct}% payout)": "dividendo no cubierto ({pct} % de reparto)",
    "near its 52-week low — still falling?": "cerca de su mínimo de 52 semanas: ¿sigue cayendo?",
    "payout ratio above 90% — dividend barely covered":
        "ratio de reparto superior al 90 %: dividendo apenas cubierto",
    "yield far above its own 5-year average — possible yield trap":
        "rentabilidad muy por encima de su media a 5 años: posible trampa de rentabilidad",
    "no trailing profit — P/E is the forward estimate":
        "sin beneficio en los últimos doce meses: el PER es la estimación futura",
    "earnings down {pct}% year on year": "beneficios un {pct} % por debajo del año anterior",
    "leveraged ({ratio}x debt/equity)": "apalancada ({ratio}× deuda/fondos propios)",
    "thin data — score built on few figures": "datos escasos: puntuación construida con pocas cifras",
    "yield too low for income ({pct}%)": "rentabilidad demasiado baja para rentas ({pct} %)",
    "yield says distress ({pct}%)": "la rentabilidad indica apuros ({pct} %)",
    "payout leaves no headroom ({pct}%)": "el reparto no deja margen ({pct} %)",
    "revenue shrinking ({pct}%)": "ingresos en retroceso ({pct} %)",
    "forward dividend {pct}% BELOW the trailing one — a cut is already declared":
        "dividendo anunciado un {pct} % POR DEBAJO del anterior: ya hay un recorte declarado",
    "dividend rate moved more than 50% — likely a special, or a change of payment frequency, not real growth":
        "el dividendo cambió más de un 50 %: probablemente un extraordinario o un cambio de frecuencia, no crecimiento real",
    "yield well above its own 5-year average — the price fell, the dividend did not rise":
        "rentabilidad bastante por encima de su media a 5 años: el precio cayó, el dividendo no subió",
    "dividend costs {pct}% of free cash flow — paid out of the balance sheet, not out of the business":
        "el dividendo cuesta el {pct} % del flujo de caja libre: se paga con el balance, no con el negocio",
    "payout ratio {pct}% — little room for a bad year":
        "ratio de reparto del {pct} %: poco margen para un mal año",
    "near its 52-week low — the market is still selling":
        "cerca de su mínimo de 52 semanas: el mercado sigue vendiendo",
    "not a fund ({type})": "no es un fondo ({type})",
    "leveraged or inverse — a multi-year CAGR is meaningless":
        "apalancado o inverso: una rentabilidad plurianual no significa nada",
    "no TER known — add it to screener_etf_universe.json":
        "TER desconocido: añádelo en screener_etf_universe.json",
    "too expensive ({pct}% a year)": "demasiado caro ({pct} % al año)",
    "no price history": "sin historial de precios",
    "only {years} years of history": "solo {years} años de historial",
    "fund too small ({m}m)": "fondo demasiado pequeño ({m} M)",
    "our TER {ours}% vs Yahoo's {theirs}% — likely a different share class; check the ISIN":
        "nuestro TER {ours} % frente al {theirs} % de Yahoo: probablemente otra clase de participaciones; comprueba el ISIN",
    "TER is Yahoo's, not the KID's — verify before ranking on it":
        "el TER es el de Yahoo, no el del KID: verifícalo antes de clasificar por él",
    "returns are in {ccy}, not EUR — the FX series could not be fetched, so this row is not comparable with the rest":
        "rentabilidades en {ccy}, no en EUR: no se pudo descargar la serie de cambio, así que esta fila no es comparable con el resto",
    "under 5 years of history — growth is the 3-year figure alone":
        "menos de 5 años de historial: el crecimiento es solo la cifra a 3 años",
    "distributing — outside a tax wrapper each distribution is taxed in the year it is paid, so it compounds slower":
        "de distribución: fuera de una envoltura fiscal cada reparto tributa el año en que se paga, así que capitaliza más despacio",
    "fell {pct}% peak to trough within this window":
        "cayó un {pct} % de máximo a mínimo dentro de esta ventana",
    "volatile ({pct}% a year)": "volátil ({pct} % al año)",
    "single theme or sector — a concentrated bet, not a core holding":
        "un solo tema o sector: una apuesta concentrada, no una posición central",
    "fund size unknown — Yahoo reports none for this listing":
        "patrimonio desconocido: Yahoo no lo da para esta cotización",
    "US mutual fund — its annual distribution is mostly realised capital gains, not income":
        "fondo de inversión estadounidense: su reparto anual es sobre todo plusvalías realizadas, no renta",
    "leveraged or inverse — not an income holding": "apalancado o inverso: no es una posición de rentas",
    "no distribution data — the fetch has not run yet":
        "sin datos de repartos: la descarga aún no se ha ejecutado",
    "accumulating — reinvests internally and pays no income":
        "de acumulación: reinvierte internamente y no paga renta",
    "yield too low for an income holding ({pct}%)":
        "rentabilidad demasiado baja para una posición de rentas ({pct} %)",
    "implausible yield ({pct}%) — a special distribution, a return of capital, or a stale price":
        "rentabilidad inverosímil ({pct} %): un reparto extraordinario, una devolución de capital o un precio desfasado",
    "only {years} years of price history": "solo {years} años de historial de precios",
    "only {years} years of distributions — too short to tell a rising payout from a lucky one":
        "solo {years} años de repartos: demasiado poco para distinguir un reparto creciente de uno afortunado",
    "listed as accumulating but has paid distributions — the universe entry is probably the wrong share class":
        "figura como de acumulación pero ha pagado repartos: la entrada del universo es probablemente la clase equivocada",
    "listed as distributing but has paid nothing in 12 months — probably the accumulating share class of the same fund":
        "figura como de distribución pero no ha pagado nada en 12 meses: probablemente la clase de acumulación del mismo fondo",
    "our trailing yield {ours}% vs Yahoo's {theirs}% — check for a special distribution":
        "nuestra rentabilidad {ours} % frente al {theirs} % de Yahoo: busca un reparto extraordinario",
    "paid {now} times this year vs {before} last — a schedule change, so the growth figure is not like-for-like":
        "pagó {now} veces este año frente a {before} el anterior: un cambio de calendario, así que la cifra de crecimiento no compara lo mismo con lo mismo",
    "has cut before — worst year was {pct}%": "ya ha recortado antes: el peor año fue del {pct} %",
    "distribution is shrinking ({pct}% year on year)": "el reparto se reduce ({pct} % interanual)",
    "the TER eats {pct}% of the income": "el TER se come el {pct} % de la renta",
    "PEA-eligible — distributions inside a PEA are not taxed in the year they are paid, which matters more on an income holding than on an accumulating one":
        "apto para PEA: dentro de un PEA los repartos no tributan el año en que se pagan, lo que importa más en una posición de rentas que en una de acumulación",
    "not PEA-eligible — in a plain broker account each distribution is taxed the year it is paid, so the headline yield is not the net one":
        "no apto para PEA: en una cuenta de valores normal cada reparto tributa el año en que se paga, así que la rentabilidad bruta no es la neta",
    "single sector — a concentrated bet, not a core income holding":
        "un solo sector: una apuesta concentrada, no una posición de rentas central",
    "the same fund is also listed as {others} — pick the listing your broker offers, they are not separate holdings":
        "el mismo fondo también cotiza como {others}: elige la cotización que ofrezca tu bróker, no son posiciones distintas",

    # ─── MCP ─────────────────────────────────────────────────────────
    'An assistant that speaks MCP can read this dashboard and do the chores that are slow by hand — categorise the queue and teach the rules, set budgets, type in a transaction, star a share idea, start a sync. It cannot delete an account, change settings, or see your bank credentials. Access is by a token, which stands in for your password: keep it as private, and revoke it here the moment you are unsure.':
        'Un asistente que hable MCP puede leer este panel y hacer las tareas lentas a mano: categorizar la cola y enseñar las reglas, fijar presupuestos, teclear una transacción, marcar una idea de acciones, lanzar una sincronización. No puede borrar una cuenta, cambiar ajustes ni ver tus credenciales bancarias. El acceso es por un token, que hace las veces de tu contraseña: guárdalo igual de en secreto y revócalo aquí en cuanto dudes.',
    'Claude and other assistants (MCP)': 'Claude y otros asistentes (MCP)',
    'Create a token': 'Crear un token',
    'For Claude Code on your network, this is the whole setup:': 'Para Claude Code en tu red, esta es toda la configuración:',
    'Replace the token': 'Sustituir el token',
    'Revoke': 'Revocar',
    'Token created. Any earlier token stopped working.': 'Token creado. Cualquier token anterior ha dejado de funcionar.',
    'Token revoked. Anything connected with it is cut off.': 'Token revocado. Todo lo que estaba conectado con él queda cortado.',
    'a token exists': 'hay un token',
    'off — no token': 'desactivado: sin token',

    # ─── Saxo und Kraken ───────────────────────────────────────────────
    'API key': 'Clave API',
    'Add your Kraken API key under Settings first.': 'Añade primero tu clave API de Kraken en Ajustes.',
    "At developer.saxo → Apps, create an application: Live (or Simulation, to try it against Saxo's demo account), grant type Authorization Code, and this exact redirect URL:":
        'En developer.saxo → Apps, crea una aplicación: Live (o Simulation, para probarla con la cuenta de demostración de Saxo), tipo de concesión Authorization Code, y exactamente esta URL de redirección:',
    'Broker connection': 'Conexión con el bróker',
    'Connect Kraken': 'Conectar Kraken',
    'Connect Saxo': 'Conectar Saxo',
    'Connect Saxo again': 'Volver a conectar Saxo',
    'Connected. Imported {n} transaction.': 'Conectado. {n} transacción importada.',
    'Connected. Imported {n} transactions.': 'Conectado. {n} transacciones importadas.',
    'Environment': 'Entorno',
    'Finish by hand': 'Terminar a mano',
    'Forget Saxo': 'Olvidar Saxo',
    'Forget the Kraken key': 'Olvidar la clave de Kraken',
    "It is your dashboard's address plus /saxo/callback, taken from the redirect URL above. If Saxo will not accept it, register it anyway and use “Finish by hand” on the account page.":
        'Es la dirección de tu panel más /saxo/callback, tomada de la URL de redirección de arriba. Si Saxo no la acepta, regístrala igualmente y usa «Terminar a mano» en la página de la cuenta.',
    'Kraken key forgotten. The account and its history stay.': 'Clave de Kraken olvidada. La cuenta y su historial se quedan.',
    'Kraken key works. Balances: {assets}. Now connect an account from its page.':
        'La clave de Kraken funciona. Saldos: {assets}. Conecta ahora una cuenta desde su página.',
    'Kraken needs an API key of your own: kraken.com → Settings → API → Add key. Give it only Query Funds, Query Closed Orders & Trades and Query Ledger Entries — nothing that can trade, withdraw or stake. A key that can only read cannot lose you a coin. Paste the key and the private key here; the private key is shown once when the key is created and is kept 0600 beside the bank key.':
        'Kraken necesita una clave API tuya: kraken.com → Settings → API → Add key. Dale solo Query Funds, Query Closed Orders & Trades y Query Ledger Entries; nada que pueda operar, retirar o hacer staking. Una clave que solo puede leer no puede hacerte perder una moneda. Pega aquí la clave y la clave privada; la privada se muestra una sola vez al crearla y se guarda con permisos 0600 junto a la clave bancaria.',
    'Kraken: link this account to the API key under Settings and pull every trade, deposit and reward.':
        'Kraken: vincula esta cuenta con la clave API de Ajustes y descarga cada operación, depósito y recompensa.',
    'Landed on a dead page after the Saxo login? Paste its address here.':
        '¿Has acabado en una página muerta tras iniciar sesión en Saxo? Pega aquí su dirección.',
    'No code and state in that. Paste the whole address, including the ?code=… part.':
        'Ahí no hay código ni state. Pega la dirección completa, incluida la parte ?code=…',
    'Open a broker account here and press Connect Saxo.': 'Abre aquí una cuenta de bróker y pulsa «Conectar Saxo».',
    'Paste the AppKey and the AppSecret below.': 'Pega el AppKey y el AppSecret abajo.',
    'Private key': 'Clave privada',
    'Read-only key; syncs with the daily sync.': 'Clave de solo lectura; se sincroniza con la sincronización diaria.',
    'Save Saxo credentials': 'Guardar las credenciales de Saxo',
    'Save and check the key': 'Guardar y comprobar la clave',
    'Saxo Bank: log in at Saxo and this account becomes your first Saxo account; any others are created beside it.':
        'Saxo Bank: inicia sesión en Saxo y esta cuenta pasa a ser tu primera cuenta Saxo; las demás se crean a su lado.',
    'Saxo credentials saved. Now connect an account from its page.':
        'Credenciales de Saxo guardadas. Conecta ahora una cuenta desde su página.',
    'Saxo forgotten. The accounts and their history stay.': 'Saxo olvidado. Las cuentas y su historial se quedan.',
    'Saxo refused the login: {reason}': 'Saxo rechazó el inicio de sesión: {reason}',
    'Saxo sent us back without a code. Paste the address bar on the account page.':
        'Saxo nos devolvió sin código. Pega la barra de direcciones en la página de la cuenta.',
    "Saxo's OpenAPI is OAuth: you register an application of your own in Saxo's developer portal, paste its AppKey and AppSecret here, and connect an account from its page — Saxo's login, then straight back. The tokens Saxo hands out die within the hour, so the app renews them every five minutes while it runs; if it was down for longer, the account page says so and connecting again is one click.":
        'La OpenAPI de Saxo es OAuth: registras una aplicación tuya en el portal de desarrolladores de Saxo, pegas aquí su AppKey y AppSecret y conectas una cuenta desde su página: el inicio de sesión de Saxo y de vuelta. Los tokens que entrega Saxo caducan en menos de una hora, así que la app los renueva cada cinco minutos mientras está en marcha; si estuvo parada más tiempo, la página de la cuenta lo dice y volver a conectar es un clic.',
    'Simulation': 'Simulación',
    'The Saxo login has lapsed — connect again to resume syncing.': 'La sesión de Saxo ha caducado: vuelve a conectar para seguir sincronizando.',
    'The login is being kept alive.': 'La sesión se mantiene viva.',
    'account {id}': 'cuenta {id}',
    'connected · client {id}': 'conectado · cliente {id}',
    'credentials saved, nothing connected yet': 'credenciales guardadas, nada conectado aún',
    'key saved': 'clave guardada',
    'login lapsed': 'sesión caducada',
    'not set up': 'sin configurar',
    'simulation': 'simulación',

    # ─── Die Zeilen eines Wertpapiers ─────────────────────────────────
    'Amount in {currency}': 'Importe en {currency}',
    'An imported row cannot be removed — it would only come back with the next import — but it can be corrected to a quantity of zero. A row typed in by hand can be removed.':
        'Una fila importada no se puede eliminar (volvería con la siguiente importación), pero sí corregir a una cantidad de cero. Una fila tecleada a mano sí se puede eliminar.',
    'Click a security to see, and correct, every row behind it.': 'Pulsa un valor para ver, y corregir, cada fila que hay detrás.',
    'Correct': 'Corregir',
    'Corrected.': 'Corregido.',
    'Every row behind this holding': 'Cada fila detrás de esta posición',
    'Held': 'En cartera',
    'If a figure is wrong — a quantity a statement read badly, a price in the wrong currency — correct it here. A correction stays: the next import recognises the row and leaves it alone. Sizes are typed unsigned; the kind supplies the sign. The amount is the whole cash effect as the broker booked it, fees and taxes included.':
        'Si una cifra está mal (una cantidad mal leída de un extracto, un precio en la moneda equivocada), corrígela aquí. La corrección se mantiene: la siguiente importación reconoce la fila y la deja en paz. Las cantidades se escriben sin signo; el tipo pone el signo. El importe es el efecto total en efectivo tal como lo contabilizó el bróker, con comisiones e impuestos.',
    'No transaction carries that security.': 'Ninguna transacción lleva ese valor.',
    'Remove this row': 'Eliminar esta fila',
    'Save correction': 'Guardar la corrección',
    'Security name': 'Nombre del valor',
    'That transaction does not exist.': 'Esa transacción no existe.',
    'Units': 'Unidades',
    'at {price} on {date}': 'a {price} el {date}',
    'buys minus sales, fees included': 'compras menos ventas, comisiones incluidas',
    'corrected {date}': 'corregido el {date}',
    'dividends and interest': 'dividendos e intereses',
    'in': 'entrada',
    'no market price yet': 'aún sin precio de mercado',
    'out': 'salida',
    'the running sum of every row below': 'la suma acumulada de cada fila de abajo',
    'Collapse all': 'Contraer todo',
    'Expand all': 'Expandir todo',
    'by year and month, newest first': 'por año y mes, lo más reciente primero',
    'everything': 'todo',
    'fee': 'comisión',
    'tax': 'impuesto',
    'the quantity as it ran': 'la cantidad tras esta fila',
    '{amount} bought': '{amount} comprados',
    '{amount} paid out': '{amount} pagados',
    '{amount} sold': '{amount} vendidos',
    '{n} row': '{n} fila',
    '{n} rows': '{n} filas',

    # ─── Krypto, Kredite, Wertpapierseite ─────────────────────────────
    'Add a loan': 'Añadir un préstamo',
    'Add the loan': 'Añadir el préstamo',
    'Balance after': 'Saldo pendiente',
    'Capital': 'Capital',
    'Change the terms, or delete': 'Cambiar las condiciones o eliminar',
    'Connect Kraken under Settings, or add a buy by hand on a broker account with CRYPTO:BTC as the ISIN.':
        'Conecta Kraken en Ajustes, o añade una compra a mano en una cuenta de bróker con CRYPTO:BTC como ISIN.',
    'Cost basis': 'Coste de adquisición',
    'Crypto': 'Cripto',
    'Debt': 'Deuda',
    'Every': 'Cada',
    "Every coin you hold, at today's price, with the wallet's value over time. Coins arrive from Kraken or from a row typed in by hand with the code as its ISIN — CRYPTO:BTC — and are priced from Yahoo like everything else.":
        'Cada moneda que tienes, al precio de hoy, con el valor del monedero a lo largo del tiempo. Las monedas llegan de Kraken o de una fila tecleada a mano con el código como ISIN (CRYPTO:BTC) y se valoran con Yahoo como todo lo demás.',
    'Extra': 'Amortización extra',
    'Extra repayments': 'Amortizaciones extra',
    'First instalment': 'Primera cuota',
    'Instalment': 'Cuota',
    'Interest': 'Intereses',
    'Interest over the whole loan': 'Intereses de todo el préstamo',
    'Latest rows': 'Últimas filas',
    'Loan added. Its balance is on the overview from today.': 'Préstamo añadido. Su saldo está en el resumen desde hoy.',
    'Loan deleted, with its account.': 'Préstamo eliminado, con su cuenta.',
    'Loan or mortgage': 'Préstamo o hipoteca',
    'Loan updated.': 'Préstamo actualizado.',
    'Loans': 'Préstamos',
    'Loans and mortgages': 'Préstamos e hipotecas',
    'Mortgage, house': 'Hipoteca, casa',
    'No coins yet.': 'Aún no hay monedas.',
    'No such coin is held.': 'No se tiene esa moneda.',
    'Notes': 'Notas',
    'Of': 'De',
    'Owed today': 'Debido hoy',
    'Paid off': 'Liquidado el',
    'Price chart': 'Gráfico de precio',
    "Price: Yahoo's daily close of the pair, in the base currency. Wallet: that price times the units held on each day, from the rows below — so a purchase shows as a step up and a sale as a step down.":
        'Precio: el cierre diario del par en Yahoo, en la moneda base. Monedero: ese precio por las unidades que tenías cada día, según las filas de abajo; una compra aparece como un escalón hacia arriba y una venta como uno hacia abajo.',
    'Principal': 'Capital prestado',
    'Rate, % per year': 'Tipo, % anual',
    'Save the terms': 'Guardar las condiciones',
    'Since the first purchase': 'Desde la primera compra',
    'Still owed': 'Aún debido',
    'Term, months': 'Plazo, meses',
    "The instalment is the figure on the contract. Leave it blank and give the term instead, and it is worked out as a constant annuity — the usual shape of a mortgage. Interest is rounded to the cent each period, the way a bank does it, so the schedule reproduces the bank's own figures.":
        'La cuota es la cifra del contrato. Déjala en blanco e indica el plazo en su lugar, y se calcula como anualidad constante, la forma habitual de una hipoteca. Los intereses se redondean al céntimo en cada periodo, como hace un banco, para que el cuadro reproduzca las cifras del propio banco.',
    'The schedule, instalment by instalment': 'El cuadro de amortización, cuota a cuota',
    "Type the loan's name exactly to confirm the deletion.": 'Escribe el nombre exacto del préstamo para confirmar la eliminación.',
    'Type “{name}” to delete this loan and its account': 'Escribe «{name}» para eliminar este préstamo y su cuenta',
    'Unrealised gain': 'Ganancia latente',
    'Value is the units held times the price of the day — the market price where the app has one, the last price paid before that. Invested is buys minus sales, fees included. Dividends and interest are drawn as their own line, because they are return that never shows in the value.':
        'El valor son las unidades en cartera por el precio del día: el precio de mercado donde la app lo tiene, el último precio pagado antes de eso. Invertido son compras menos ventas, comisiones incluidas. Dividendos e intereses van en su propia línea, porque son rentabilidad que nunca aparece en el valor.',
    'Wallet': 'Monedero',
    "What you owe, computed from the terms rather than typed in: the schedule gives the balance as of today, the overview subtracts it from the net worth, and nothing needs updating month by month. A balance typed in on the loan's account page — from the bank's letter — still wins on the day it is typed.":
        'Lo que debes, calculado a partir de las condiciones en vez de tecleado: el cuadro de amortización da el saldo a día de hoy, el resumen lo resta del patrimonio neto y no hay nada que actualizar mes a mes. Un saldo tecleado en la página de la cuenta del préstamo (de la carta del banco) sigue ganando el día en que se teclea.',
    'a mortgage, a car loan, a consumer credit — anything paid off in instalments':
        'una hipoteca, un préstamo del coche, un crédito al consumo: cualquier cosa que se pague en cuotas',
    'all instalments, as a monthly figure': 'todas las cuotas, en cifra mensual',
    'avg {price} per {code}': 'media {price} por {code}',
    'every row, and corrections': 'cada fila, y las correcciones',
    'loans and mortgages': 'préstamos e hipotecas',
    'never at this payment': 'nunca con esta cuota',
    'next {date}': 'siguiente el {date}',
    'no price history yet — it arrives with the next price refresh':
        'aún sin historial de precios; llega con la siguiente actualización de precios',
    'no price yet — it arrives with the next price refresh': 'aún sin precio; llega con la siguiente actualización de precios',
    'no prices for this range': 'sin precios para este periodo',
    'one per line: date and amount': 'una por línea: fecha e importe',
    'or leave blank': 'o dejar en blanco',
    'over the range': 'en el periodo',
    'repaid': 'amortizado',
    'the account': 'la cuenta',
    'value plus income, against what went in, since {date}': 'valor más ingresos, frente a lo invertido, desde el {date}',
    'wallet value over the range — units bought or sold count too': 'valor del monedero en el periodo; las unidades compradas o vendidas también cuentan',
    'what it was worth against what went in, day by day': 'lo que valía frente a lo invertido, día a día',
    '{code} price': 'Precio de {code}',
    '{interest} of it interest': '{interest} de ellos intereses',
    '{n} instalment left': 'queda {n} cuota',
    '{n} instalments left': 'quedan {n} cuotas',
    '{n} loan': '{n} préstamo',
    '{n} loans': '{n} préstamos',
    'Extra repayment {line}: write the date and the amount, like 2027-04-10 20000.':
        'Amortización extra {line}: escribe la fecha y el importe, como 2027-04-10 20000.',
    'Give the payment per period, or the term in months to work it out.':
        'Indica la cuota por periodo, o el plazo en meses para calcularla.',
    'Payments are monthly, quarterly, half-yearly or yearly.': 'Las cuotas son mensuales, trimestrales, semestrales o anuales.',
    'That loan does not exist.': 'Ese préstamo no existe.',
    'That payment does not even cover the interest — the loan would never end.':
        'Esa cuota ni siquiera cubre los intereses: el préstamo no terminaría nunca.',
    'The first payment needs a date, written year-month-day.': 'La primera cuota necesita una fecha, escrita año-mes-día.',
    'The loan needs a name.': 'El préstamo necesita un nombre.',
    'The principal must be a positive amount.': 'El capital prestado debe ser un importe positivo.',
    'The rate is a percentage per year, like 3.2.': 'El tipo es un porcentaje anual, como 3.2.',
    'Last twelve months': 'Últimos doce meses',
    "Measured from {date}, day by day, on the prices the app has — backfilled to each security's first trade. A dash means there is nothing to measure yet.":
        'Medido desde el {date}, día a día, con los precios que tiene la app, recuperados hasta la primera operación de cada valor. Un guion significa que aún no hay nada que medir.',
    'Money-weighted (MWR), a year': 'Ponderado por dinero (MWR), anual',
    'Money-weighted, a year.': 'Ponderado por dinero, anual.',
    'Money-weighted, the internal rate of return: the annual rate your own money earned, timing included — what a savings account would have had to pay.':
        'Ponderado por dinero, la tasa interna de retorno: el tipo anual que ganó tu propio dinero, momentos incluidos; lo que una cuenta de ahorro habría tenido que pagar.',
    'Return': 'Rentabilidad',
    'Return (TWR)': 'Rentabilidad (TWR)',
    'Since the first trade': 'Desde la primera operación',
    'This year': 'Este año',
    'Time-weighted (TWR)': 'Ponderado por tiempo (TWR)',
    'Time-weighted, since the first purchase; a year when it is longer than one.':
        'Ponderado por tiempo, desde la primera compra; anual cuando supera un año.',
    'Time-weighted: the return of the investment itself, with the timing of your own money taken out — what compares one holding to another.':
        'Ponderado por tiempo: la rentabilidad de la inversión en sí, sin el efecto de cuándo llegó tu dinero; lo que permite comparar una posición con otra.',
    'Your money (MWR)': 'Tu dinero (MWR)',
    'a year': 'anual',
    'a year, on what went in and came out': 'anual, sobre lo que entró y salió',
    'since {date}': 'desde el {date}',
    'the securities as one investment, in the base currency; cash left out on purpose':
        'los valores como una sola inversión, en la moneda base; el efectivo queda fuera a propósito',
    '{pct} % a year': '{pct} % anual',
    '{pct} % a year, since {date}': '{pct} % anual, desde el {date}',
    # Realised gains, by lots (0.25.0)
    'All time': 'Desde el principio',
    'Average cost — every unit costs the average paid': 'Coste medio — cada título cuesta la media pagada',
    'Cost of those units': 'Coste de esos títulos',
    'Each sale against the cost of the units it sold — the oldest units first under FIFO, every unit at the average paid under average cost. Proceeds and costs as the broker booked them, fees included; a position closed years ago still counts. Kept per currency: a gain in dollars is not a gain in euros without a rate, and this is the figure a tax form asks for.': 'Cada venta contra el coste de los títulos vendidos — los más antiguos primero con FIFO, cada título a la media pagada con coste medio. Ingresos y costes tal como los contabilizó el bróker, comisiones incluidas; una posición cerrada hace años sigue contando. Por divisa: una ganancia en dólares no es una ganancia en euros sin un tipo de cambio, y esta es la cifra que pide una declaración fiscal.',
    'Each sale against the cost of the units it sold, lots kept per account — a unit bought at one broker is never sold at another. Under FIFO the oldest units go first, which is how Germany taxes; under average cost every unit costs the average paid, the French prix moyen pondéré. Units that arrived without a purchase — a transfer in — cost what their row says, or nothing; units that left without a sale realise nothing.': 'Cada venta contra el coste de los títulos vendidos, lotes por cuenta — un título comprado en un bróker nunca se vende en otro. Con FIFO salen primero los más antiguos, como grava Alemania; con coste medio cada título cuesta la media pagada, el prix moyen pondéré francés. Los títulos llegados sin compra — un traspaso entrante — cuestan lo que dice su fila, o nada; los que salieron sin venta no realizan nada.',
    'FIFO': 'FIFO',
    'FIFO — the oldest units are sold first': 'FIFO — los títulos más antiguos se venden primero',
    'Gain': 'Ganancia',
    'Proceeds': 'Ingresos',
    'Realised': 'Realizado',
    'Realised gains': 'Ganancias realizadas',
    'Realised gains, by': 'Ganancias realizadas, por',
    'Units sold': 'Títulos vendidos',
    'Unrealised': 'Latente',
    'Value minus what the units still held cost, by lots; minus net invested when there is no price by lots.': 'Valor menos el coste de los títulos aún en cartera, por lotes; menos lo invertido neto cuando no hay precio por lotes.',
    'What the sales of this security made, by lots.': 'Lo que rindieron las ventas de este título, por lotes.',
    'Which units a sale sells decides what it made. FIFO is what Germany taxes on and what Portfolio Performance shows; average cost is the French prix moyen pondéré. Switzerland taxes no private capital gain, so a Swiss reader may pick either. Nothing is stored: switching recomputes every figure.': 'Qué títulos vende una venta decide lo que rindió. FIFO es lo que grava Alemania y lo que muestra Portfolio Performance; el coste medio es el prix moyen pondéré francés. Suiza no grava las ganancias de capital privadas, así que un lector suizo puede elegir cualquiera. Nada se guarda: cambiar recalcula cada cifra.',
    'average cost': 'coste medio',
    'change': 'cambiar',
    'cost {amount}': 'coste {amount}',
    'units held cost {amount}, {avg} each': 'los títulos en cartera costaron {amount}, {avg} cada uno',
    'what the sales made, by lots': 'lo que rindieron las ventas, por lotes',
    '{amount} realised': '{amount} realizado',
    '{amount} unrealised': '{amount} latente',
    '{n} sale': '{n} venta',
    '{n} sales': '{n} ventas',
    # A CSV mapped by hand (0.26.0)
    'A date column and an amount column — or a debit and a credit column — are the least a mapping needs.': 'Una columna de fecha y una de importe — o una de debe y una de haber — son lo mínimo que necesita una correspondencia.',
    'A file with one of these headers is imported through its mapping without asking. Forget one and the next such file asks again — the rows already imported stay.': 'Un archivo con una de estas cabeceras se importa por su correspondencia sin preguntar. Olvida una y el siguiente archivo así vuelve a preguntar — las filas ya importadas se quedan.',
    'Amount, signed': 'Importe, con signo',
    'Any other bank': 'Cualquier otro banco',
    'Blank means the ISIN is looked for in the description.': 'Vacío: el ISIN se busca en la descripción.',
    "Blank means the account's currency, or the one typed in below.": 'Vacío: la divisa de la cuenta, o la escrita abajo.',
    'Buy, sell, dividend, interest, fee, tax, deposit, withdrawal or transfer — in English, German, French or Spanish. Left blank, the kind is worked out from the row: an ISIN and units is a trade, an ISIN and money in a dividend, plain money a deposit or a withdrawal.': 'Compra, venta, dividendo, intereses, comisión, impuesto, depósito, retiro o traspaso — en inglés, alemán, francés o español. Si se deja vacío, el tipo se deduce de la fila: un ISIN y títulos es una operación, un ISIN y dinero entrante un dividendo, dinero a secas un depósito o un retiro.',
    'CSV mappings': 'Correspondencias CSV',
    'Call this mapping': 'Nombre de esta correspondencia',
    'Cancel': 'Cancelar',
    'Columns': 'Columnas',
    'Credit (money in)': 'Haber (dinero entrante)',
    'Currency when the file has no column for it': 'Divisa cuando el archivo no tiene columna para ella',
    'Debit (money out)': 'Debe (dinero saliente)',
    "Export the transactions as CSV and drop the file in. If no importer knows it you are asked, once, which column is the date, the amount and so on; the mapping is remembered under the file's header, so the next export from that bank goes straight in.": 'Exporta los movimientos como CSV y suelta el archivo aquí. Si ningún importador lo conoce, se te pregunta, una vez, qué columna es la fecha, el importe y demás; la correspondencia se recuerda bajo la cabecera del archivo, y el siguiente export de ese banco entra directamente.',
    'Forget': 'Olvidar',
    'If a kind, a sign or a date looks wrong here it will be wrong in the account: change the mapping and look again before importing. Every row is imported; a row without a readable date is listed and left out.': 'Si un tipo, un signo o una fecha parece mal aquí, estará mal en la cuenta: cambia la correspondencia y vuelve a mirar antes de importar. Cada fila se importa; una fila sin fecha legible se lista y se deja fuera.',
    'Map the columns': 'Asignar las columnas',
    'Mapping forgotten. The next file with that header asks again.': 'Correspondencia olvidada. El siguiente archivo con esa cabecera volverá a preguntar.',
    'Money in positive, money out negative. If the file has one column for each, leave this blank and map the two below.': 'Dinero entrante positivo, saliente negativo. Si el archivo tiene una columna para cada uno, deja esto vacío y asigna las dos de abajo.',
    "No importer here knows this file, and it does not need to: say which column is which, once. The mapping is kept under the file's header, so the next export from the same bank is recognised by itself — like a Degiro file is.": 'Ningún importador conoce este archivo, y no hace falta: di una vez qué columna es qué. La correspondencia se guarda bajo la cabecera del archivo, y el siguiente export del mismo banco se reconoce solo — como un archivo de Degiro.',
    'Not one row could be read through that mapping.': 'Ni una fila pudo leerse con esa correspondencia.',
    'Nothing readable yet — the date or the amount column is not the right one.': 'Nada legible todavía — la columna de fecha o de importe no es la correcta.',
    'Only when there is no signed amount column.': 'Solo cuando no hay una columna de importe con signo.',
    'Read through this mapping': 'Leído con esta correspondencia',
    'Save the mapping and import': 'Guardar la correspondencia e importar',
    'Show me the first rows': 'Muéstrame las primeras filas',
    'Since': 'Desde',
    'That upload has expired — choose the file again.': 'Esa subida ha caducado — elige el archivo de nuevo.',
    'The file': 'El archivo',
    'The file writes money out as positive — flip every sign': 'El archivo escribe el dinero saliente en positivo — invertir cada signo',
    "The kind gives the sign: a buy's units come in, a sale's go out.": 'El tipo da el signo: los títulos de una compra entran, los de una venta salen.',
    'The mapping is saved as {name}; the next file with this header is recognised by itself.': 'La correspondencia se ha guardado como {name}; el siguiente archivo con esta cabecera se reconoce solo.',
    'What the row says; the counterparty stands in when this is blank.': 'Lo que dice la fila; la contraparte la sustituye cuando está vacía.',
    'Which column is which': 'Qué columna es qué',
    'Who paid or was paid.': 'Quién pagó o fue pagado.',
    'Written year-month-day, day.month.year or day/month/year. A US month-first date is not guessed.': 'Escrita año-mes-día, día.mes.año o día/mes/año. Una fecha estadounidense con el mes primero no se adivina.',
    'columns': 'columnas',
    'saved as {name} — this changes it': 'guardada como {name} — esto la cambia',
    'separated by {delimiter}': 'separadas por {delimiter}',
    'the bank, say': 'el banco, por ejemplo',
    'the first rows, as they would be imported': 'las primeras filas, tal como se importarían',
    '{n} file layout you mapped yourself': '{n} formato de archivo asignado por ti',
    '{n} file layouts you mapped yourself': '{n} formatos de archivo asignados por ti',
    # CSV export (0.26.0)
    'Every row these filters match, not just the ones shown, in a file a spreadsheet opens right.': 'Cada fila que cumplen estos filtros, no solo las mostradas, en un archivo que una hoja de cálculo abre bien.',
    'Export as CSV': 'Exportar como CSV',
    'This table with every figure on it — price, value, gains, TWR and MWR — in a file a spreadsheet opens right.': 'Esta tabla con cada cifra — precio, valor, ganancias, TWR y MWR — en un archivo que una hoja de cálculo abre bien.',
    # Stock splits (0.27.0)
    "A split adds a row per account — the units that appeared, at no cost — so the quantity above is right from that day on. Earlier rows keep the units and prices of their day; the chart values them in today's units, as Yahoo's history is, and a lot keeps its cost, so a later sale realises the same gain it would have in the old units. Write 1:10 for a reverse split.": 'Un split añade una fila por cuenta — los títulos que aparecieron, sin coste — para que la cantidad de arriba sea correcta desde ese día. Las filas anteriores conservan los títulos y precios de su día; el gráfico los valora en títulos de hoy, como hace el histórico de Yahoo, y un lote conserva su coste, así que una venta posterior realiza la misma ganancia que en títulos antiguos. Escribe 1:10 para un contrasplit.',
    'New for old': 'Nuevos por antiguos',
    'Nothing was held on that day — or that split is already recorded.': 'Ese día no se tenía nada — o ese split ya está registrado.',
    'Record a split': 'Registrar un split',
    'Record the split': 'Registrar el split',
    'Split recorded on {n} account.': 'Split registrado en {n} cuenta.',
    'Split recorded on {n} accounts.': 'Split registrado en {n} cuentas.',
    'split [kind]': 'Split',
    'when the units changed and the money did not': 'cuando cambiaron los títulos y no el dinero',
    'Write the split as new for old, like 44:1 — or 1:10 for a reverse split.': 'Escribe el split como nuevos por antiguos, como 44:1 — o 1:10 para un contrasplit.',
    # Sidebar navigation and the three stages (0.28.0)
    'A month, in {currency}': 'Al mes, en {currency}',
    'A year of returns and a year of savings are of the same order — anywhere from half to twice each other. The crossover, where they are equal, is here. Both levers matter now, and a bad year can undo a year of saving.': 'Un año de rendimiento y un año de ahorro son del mismo orden — entre la mitad y el doble uno del otro. El cruce, donde son iguales, está aquí. Ahora cuentan las dos palancas, y un mal año puede deshacer un año de ahorro.',
    'A year of returns is less than half of what you put in. The monthly amount is the lever; the return barely moves the needle yet. Keep it boring and keep it up.': 'Un año de rendimiento es menos de la mitad de lo que aportas. La cuota mensual es la palanca; el rendimiento apenas mueve la aguja todavía. Mantenlo aburrido y sigue.',
    'A year of returns is more than twice what you put in. The pile carries itself; what you add is a rounding error against what the market does. From here on, the risk you carry matters more than the amount you save.': 'Un año de rendimiento es más del doble de lo que aportas. El montón se sostiene solo; lo que añades es un error de redondeo frente a lo que hace el mercado. A partir de aquí, el riesgo que asumes importa más que la cantidad que ahorras.',
    'As it went': 'Cómo fue',
    'Back to the plan': 'Volver al plan',
    'Close the menu': 'Cerrar el menú',
    'Collapse the menu': 'Plegar el menú',
    'Compounding carries it': 'El interés compuesto lo lleva',
    'Crossover': 'Cruce',
    'Early on, what you put in is what grows the pile. Later the two pull together. Later still the return on what is there outweighs anything you could add, and the pile carries itself. One ratio tells them apart: what the market does in a year against what you put in in a year.': 'Al principio, lo que aportas es lo que hace crecer el montón. Después los dos tiran juntos. Más tarde el rendimiento de lo que hay supera cualquier cosa que pudieras añadir, y el montón se sostiene solo. Una sola proporción los distingue: lo que hace el mercado en un año frente a lo que aportas en un año.',
    'End of year': 'Fin de año',
    'Expected return, % a year': 'Rendimiento esperado, % al año',
    'Investing': 'Invertir',
    'Market did': 'El mercado hizo',
    'Market did is the value at the end of the year minus the value at the start minus what went in, plus the dividends and interest paid out — everything the money did that you did not do. A single year says little: a bad year in stage 3 looks like stage 1, and that is the point of stage 3.': '«El mercado hizo» es el valor a final de año menos el valor a principio de año menos lo aportado, más los dividendos e intereses cobrados — todo lo que hizo el dinero que no hiciste tú. Un solo año dice poco: un mal año en la etapa 3 parece la etapa 1, y ese es el sentido de la etapa 3.',
    'Money': 'Dinero',
    "Monthly compounding at the rate given, contributions at the end of each month — the same arithmetic as the Forecast. A rate is an assumption, not a promise: the world's stock market has averaged about 7 % a year over a century, with decades on either side of it.": 'Capitalización mensual al tipo dado, aportaciones a fin de mes — la misma aritmética que la Previsión. Un tipo es una suposición, no una promesa: la bolsa mundial ha dado cerca del 7 % anual en un siglo, con décadas a ambos lados.',
    'Navigation': 'Navegación',
    'No securities records yet.': 'Aún no hay datos de títulos.',
    'No securities yet. The stages begin with the first purchase.': 'Aún no hay títulos. Las etapas empiezan con la primera compra.',
    "Nothing goes in a month, so everything the pile does from here is the market's — stage 3 by definition, but of a pile that only grows if the market does.": 'No entra nada al mes, así que todo lo que haga el montón desde aquí es cosa del mercado — etapa 3 por definición, pero de un montón que solo crece si el mercado lo hace.',
    'On the plan, year by year': 'Según el plan, año a año',
    'Open the menu': 'Abrir el menú',
    'Paid out': 'Cobrado',
    'Planning': 'Planificar',
    'Put in': 'Aportado',
    'Ratio': 'Proporción',
    'Returns equal your savings — the crossover': 'El rendimiento iguala tu ahorro — el cruce',
    'Returns reach half your savings': 'El rendimiento alcanza la mitad de tu ahorro',
    'Returns reach twice your savings — compounding takes over': 'El rendimiento alcanza el doble de tu ahorro — el interés compuesto toma el mando',
    'Saving and returns pull together': 'Ahorro y rendimiento tiran juntos',
    'Saving builds it': 'El ahorro lo construye',
    'Stage': 'Etapa',
    'Stage {n}': 'Etapa {n}',
    'Stages': 'Etapas',
    'Start of year': 'Principio de año',
    'The last twelve months, {amount} a month actually went into securities.': 'En los últimos doce meses, {amount} al mes fueron realmente a títulos.',
    "The plan's figures come from the Forecast page, so they are set once.": 'Las cifras del plan vienen de la página Previsión, para fijarlas una sola vez.',
    'The three stages': 'Las tres etapas',
    'Tried, not kept.': 'Probado, no guardado.',
    'Try it': 'Probar',
    'Where you stand': 'Dónde estás',
    'every year the app has records of — what you put in against what the market did': 'cada año del que la app tiene datos — lo que aportaste frente a lo que hizo el mercado',
    'in {year}, at about {value}': 'en {year}, con unos {value}',
    'not within fifty years on these figures': 'no en cincuenta años con estas cifras',
    'over {x}×': 'más de {x}×',
    'returns under {x}× savings': 'rendimiento por debajo de {x}× el ahorro',
    'so far': 'hasta ahora',
    "the wealth at which a year of returns pays a year of savings — twelve months' saving divided by the rate": 'el patrimonio en el que un año de rendimiento paga un año de ahorro — doce meses de ahorro divididos por el tipo',
    'what goes in against what the market does, until compounding has been in charge for five years': 'lo que entra frente a lo que hace el mercado, hasta que el interés compuesto haya mandado cinco años',
    '{a}× to {b}×': 'de {a}× a {b}×',
    '{value} in securities at {rate} % expected is {returns} a year; {monthly} a month is {saved} a year — a ratio of {ratio}.': '{value} en títulos al {rate} % esperado son {returns} al año; {monthly} al mes son {saved} al año — una proporción de {ratio}.',
    # Corrections over the MCP (0.28.1)
    'Nothing to change.': 'Nada que cambiar.',
    'Transaction {id} does not exist.': 'La transacción {id} no existe.',
    '{what} cannot be changed here.': '{what} no se puede cambiar aquí.',
    '{what} is not a number.': '{what} no es un número.',
    # MCP setup notes (0.28.2)
    'For Claude Desktop, which only speaks to local processes, the mcp-remote bridge carries the same URL and header. This goes into claude_desktop_config.json under mcpServers:': 'Para Claude Desktop, que solo habla con procesos locales, el puente mcp-remote lleva la misma URL y la misma cabecera. Esto va en claude_desktop_config.json bajo mcpServers:',
    "Two things that cost people an afternoon. The URL is the one the browser reaches the dashboard at: behind a reverse proxy that is the https:// address, not the container's http:// one — the address above is what this page was opened at, so it is right if this page was. And --transport http-only matters: without it mcp-remote first tries the older SSE transport, which this endpoint does not speak, and reports a connection failure that is not one.": 'Dos cosas que cuestan una tarde. La URL es aquella en la que el navegador llega al panel: detrás de un proxy inverso es la dirección https://, no la http:// del contenedor — la dirección de arriba es en la que se abrió esta página, así que es correcta si esta página lo es. Y --transport http-only importa: sin él, mcp-remote prueba primero el antiguo transporte SSE, que este punto de acceso no habla, e informa de un fallo de conexión que no lo es.',
    # A share quoted in another currency (0.28.3)
    'quoted {price} {currency}': 'cotizado {price} {currency}',
    "A price quoted in another currency than the shares were paid in is turned into theirs at the day's ECB rate, so the lines are one currency.": 'Un precio cotizado en otra divisa que aquella en la que se pagaron los títulos se convierte a esta al tipo del BCE del día, para que las líneas sean de una sola divisa.',
    'fees {fees}, tax {taxes} paid': '{fees} de comisiones, {taxes} de impuestos pagados',
    # Currency switch on the security page (0.29.0)
    'Show in': 'Mostrar en',
    'base': 'base',
    "every amount at its own day's ECB rate; today's price at today's. The rows below stay as booked, in {currency}.": 'cada importe al tipo del BCE de su día; el precio de hoy al de hoy. Las filas de abajo se quedan como se contabilizaron, en {currency}.',
    'paid in': 'pagado en',
    'quoted in': 'cotizado en',
    # Settings in chapters, rules with terms (0.30.0)
    'Add the rule': 'Añadir la regla',
    'Assistants': 'Asistentes',
    'Banks & brokers': 'Bancos y brókeres',
    'Prices & rates': 'Precios y tipos',
    'Rule changed and every rule re-applied, oldest first.': 'Regla cambiada y cada regla reaplicada, la más antigua primero.',
    'Settings chapters': 'Capítulos de los ajustes',
    'That rule does not exist.': 'Esa regla no existe.',
    'The text is matched anywhere in the description or the counterparty, or in one of them; the amounts are sizes — 20 to 50 catches a payment of 30 whichever way it went, and the direction says which way. Blank means no limit. A rule applies to what is already imported as well as to what arrives next.': 'El texto se busca en cualquier parte de la descripción o de la contraparte, o en una de las dos; los importes son tamaños — de 20 a 50 atrapa un pago de 30 en cualquier sentido, y el sentido dice cuál. Vacío significa sin límite. Una regla se aplica a lo ya importado igual que a lo que llegue después.',
    'When': 'Cuando',
    'and the money is': 'y el dinero es',
    'contains': 'contiene',
    'from': 'de',
    'in or out': 'entrante o saliente',
    'money in': 'dinero entrante',
    'money out': 'dinero saliente',
    'the counterparty': 'la contraparte',
    'the description': 'la descripción',
    'the text anywhere': 'el texto en cualquier parte',
    'to': 'a',
    # Allocation (0.31.0)
    'About to invest, in {currency}': 'A punto de invertir, en {currency}',
    'Allocation': 'Asignación',
    'Asset class': 'Clase de activo',
    'Bucket': 'Cesta',
    'Buy': 'Comprar',
    'Buying only: the keys below their target get the amount in proportion to how far below they are.': 'Solo compras: las claves por debajo de su objetivo reciben el importe en proporción a lo lejos que están.',
    'By asset class': 'Por clase de activo',
    'By bucket': 'Por cesta',
    'By region': 'Por región',
    "Cash is every account balance; the rest is each holding's class.": 'El efectivo es el saldo de cada cuenta; el resto es la clase de cada posición.',
    'Classification saved.': 'Clasificación guardada.',
    'Drift': 'Desvío',
    'Key': 'Clave',
    'Nothing to allocate yet — no holdings and no cash balance.': 'Nada que asignar todavía — sin posiciones ni saldo.',
    'Save targets': 'Guardar objetivos',
    'Share': 'Peso',
    'Spread it': 'Repartir',
    'Target': 'Objetivo',
    'Targets saved.': 'Objetivos guardados.',
    'What each holding is': 'Qué es cada posición',
    'Where a fund invests, or where a share is listed — guessed from the name and the ISIN, yours to correct.': 'Dónde invierte un fondo, o dónde cotiza una acción — deducido del nombre y del ISIN, para que lo corrijas.',
    'Where the money is by what it is — asset class, region, and buckets of your own — against where you meant it to be. Set a target per key and the page shows the drift; give it the amount you are about to invest and it says how to spread it so the drift shrinks, without selling anything.': 'Dónde está el dinero según lo que es — clase de activo, región y cestas propias — frente a dónde debía estar. Fija un objetivo por clave y la página muestra el desvío; dale el importe que vas a invertir y dice cómo repartirlo para que el desvío se reduzca, sin vender nada.',
    'Your own taxonomy — Core and Satellite, Safe and Play, whatever you think in. Nothing is guessed here.': 'Tu propia taxonomía — Núcleo y Satélite, Seguro y Juego, lo que tú pienses. Aquí no se adivina nada.',
    'a bucket, like Core': 'una cesta, como Núcleo',
    'add a target for…': 'añadir un objetivo para…',
    'Asia Pacific [region]': 'Asia-Pacífico',
    'Bonds [class]': 'Bonos',
    'Cash [class]': 'Efectivo',
    'Commodities [class]': 'Materias primas',
    'Crypto [class]': 'Cripto',
    'Emerging markets [region]': 'Emergentes',
    'Equity [class]': 'Acciones',
    'Europe [region]': 'Europa',
    'Germany [region]': 'Alemania',
    'guessed': 'deducido',
    "guessed from the name and Yahoo's type; a guess is marked until you confirm it": 'deducido del nombre y del tipo de Yahoo; una suposición queda marcada hasta que la confirmes',
    'no targets yet': 'aún sin objetivos',
    'North America [region]': 'Norteamérica',
    'Other [class]': 'Otros',
    'Other [region]': 'Otras',
    'Real estate [class]': 'Inmobiliario',
    'Switzerland [region]': 'Suiza',
    'targets set for {pct} %': 'objetivos fijados para el {pct} %',
    'unassigned': 'sin asignar',
    'World [region]': 'Mundo',
    '{amount} to target': '{amount} hasta el objetivo',
    '{total} in total — {cash} of it cash.': '{total} en total — {cash} de ello en efectivo.',
    'A target is a percentage between 0 and 100.': 'Un objetivo es un porcentaje entre 0 y 100.',
    'The targets add up to more than a hundred percent.': 'Los objetivos suman más del cien por cien.',
    # Rules that do more, and tags (0.32.0)
    'A rule can also rename the counterparty — AMZN Mktp DE*2K3 becomes Amazon — set the kind, to mark a transfer between your own accounts, say, and add a tag; those three are applied on every sync, so they win over a correction by hand.': 'Una regla también puede renombrar la contraparte — AMZN Mktp DE*2K3 pasa a ser Amazon —, fijar el tipo, por ejemplo para marcar un traspaso entre tus propias cuentas, y añadir una etiqueta; esas tres se aplican en cada sincronización, así que prevalecen sobre una corrección a mano.',
    'A rule has to do something: file under a category, rename the counterparty, set the kind, or add a tag.': 'Una regla tiene que hacer algo: archivar en una categoría, renombrar la contraparte, fijar el tipo o añadir una etiqueta.',
    'Tag': 'Etiqueta',
    'Tags': 'Etiquetas',
    'That pattern is not a valid regular expression: {error}': 'Ese patrón no es una expresión regular válida: {error}',
    'add the tag': 'añadir la etiqueta',
    'is exactly': 'es exactamente',
    'leave the category': 'dejar la categoría',
    'matches the pattern': 'coincide con el patrón',
    'of kind': 'de tipo',
    'on account': 'en la cuenta',
    'rename the counterparty to': 'renombrar la contraparte a',
    'set the kind to': 'fijar el tipo a',
    'starts with': 'empieza por',
    'tags, comma-separated': 'etiquetas, separadas por comas',
    'then file under': 'luego archivar en',
    # Benchmark (0.33.0)
    'Against a benchmark': 'Frente a un índice de referencia',
    'Nothing to compare yet.': 'Nada que comparar todavía.',
    "The portfolio line is the time-weighted return — your own deposits and withdrawals taken out — so it can be set against an index at all. The index is turned into the portfolio's currency at each day's rate; where Yahoo has no clean index in euros an accumulating ETF stands in. Nothing is stored but the index's daily closes.": 'La línea de la cartera es el rendimiento ponderado por tiempo — sin tus propias aportaciones y retiradas — para que pueda compararse con un índice. El índice se convierte a la divisa de la cartera al tipo de cada día; donde Yahoo no tiene un índice limpio en euros, lo sustituye un ETF de acumulación. No se guarda nada salvo los cierres diarios del índice.',
    'Yahoo has no history for {symbol} over this span.': 'Yahoo no tiene histórico de {symbol} en este periodo.',
    'You': 'Tú',
    'ahead by {pct} points': '{pct} puntos por delante',
    'another symbol…': 'otro símbolo…',
    'behind by {pct} points': '{pct} puntos por detrás',
    'time-weighted, both at 100 on the first day': 'ponderado por tiempo, ambos en 100 el primer día',
    'you': 'tú',
    # Bills and goals (0.34.0)
    'A bill needs a name and at least three characters of text to recognise it by.': 'Una factura necesita un nombre y al menos tres caracteres de texto para reconocerla.',
    'A goal needs a name and a positive amount.': 'Un objetivo necesita un nombre y un importe positivo.',
    'Active': 'Activa',
    'Add a bill': 'Añadir una factura',
    'Add a goal': 'Añadir un objetivo',
    'Add the bill': 'Añadir la factura',
    'Add the goal': 'Añadir el objetivo',
    'An amount by a date, and how it is going. A goal is fed by an account — the holiday account, whose balance is the progress — or by hand, an amount at a time, for a goal that lives inside a bigger account.': 'Un importe para una fecha, y cómo va. Un objetivo se alimenta de una cuenta — la cuenta de vacaciones, cuyo saldo es el progreso — o a mano, importe a importe, para un objetivo que vive dentro de una cuenta mayor.',
    'Bill added.': 'Factura añadida.',
    'Bill removed.': 'Factura eliminada.',
    'Bill saved.': 'Factura guardada.',
    'Bills': 'Facturas',
    'By': 'Para el',
    'Change the goal': 'Cambiar el objetivo',
    'Due day': 'Día de vencimiento',
    'Due within a week': 'Vence en una semana',
    'Every bill': 'Todas las facturas',
    'Fed by an account': 'Alimentado por una cuenta',
    'Fixed costs a month': 'Gastos fijos al mes',
    'Goal added.': 'Objetivo añadido.',
    'Goal removed.': 'Objetivo eliminado.',
    'Goal saved.': 'Objetivo guardado.',
    'Goals': 'Objetivos',
    'Missed': 'Sin pagar',
    'No goals yet.': 'Aún no hay objetivos.',
    'Note it': 'Anotar',
    'Noted.': 'Anotado.',
    'Put towards it': 'Aportar',
    'Savings goals': 'Objetivos de ahorro',
    'Text that identifies it': 'Texto que la identifica',
    'That bill does not exist.': 'Esa factura no existe.',
    'That goal does not exist.': 'Ese objetivo no existe.',
    'The text is looked for in the counterparty and the description of money going out; an amount, if given, allows a fifth either way — utilities vary. The due day snaps the next date to the day of the month the bill is usually taken.': 'El texto se busca en la contraparte y la descripción del dinero saliente; un importe, si se da, admite una quinta parte de margen — los suministros varían. El día de vencimiento ajusta la siguiente fecha al día del mes en que suele cobrarse.',
    'What is expected to leave the account, and whether it did. A subscription is found; a bill is declared — the rent, the insurance, the electricity — and matched against the rows as they arrive, so this page can say paid, due, or missed.': 'Lo que debe salir de la cuenta, y si salió. Una suscripción se detecta; una factura se declara — el alquiler, el seguro, la luz — y se coteja con las filas según llegan, para que esta página diga pagada, vence o sin pagar.',
    'by hand': 'a mano',
    'by {date}': 'para el {date}',
    'due': 'vence',
    'fed by hand': 'alimentado a mano',
    'fed by {account}': 'alimentado por {account}',
    'last {date}, {amount}': 'última el {date}, {amount}',
    'make it a bill': 'convertir en factura',
    'missed': 'sin pagar',
    'more than the {plan} a month of your plan': 'más que los {plan} al mes de tu plan',
    'never seen': 'nunca vista',
    'next {date}, in {n} days': 'siguiente el {date}, en {n} días',
    'next: {name}, {date}': 'siguiente: {name}, el {date}',
    'no payment matched yet': 'aún sin pago cotejado',
    'or adopt one the app detected': 'o adoptar una detectada',
    'paid': 'pagada',
    'past due by more than a week, nothing seen since': 'vencida hace más de una semana, nada visto desde entonces',
    'reached': 'alcanzado',
    'the date has passed': 'la fecha ha pasado',
    'was due {date}, {n} days ago': 'vencía el {date}, hace {n} días',
    '{amount} a month for {n} months reaches it': '{amount} al mes durante {n} meses lo alcanza',
    '{amount} to go': 'faltan {amount}',
    '{n} active bill': '{n} factura activa',
    '{n} active bills': '{n} facturas activas',
    '{n} payment seen': '{n} pago visto',
    '{n} payments seen': '{n} pagos vistos',
    # Dividend calendar (0.35.0)
    'By security': 'Por título',
    'By year': 'Por año',
    'Coming up': 'Próximamente',
    'Dividend calendar': 'Calendario de dividendos',
    'Ex-date': 'Fecha ex-dividendo',
    'Expected': 'Esperado',
    'Expected, 12 months': 'Esperado, 12 meses',
    'Expected, next twelve months': 'Esperado, próximos doce meses',
    'Month by month': 'Mes a mes',
    'Next ex-date': 'Próxima fecha ex-dividendo',
    'No dividends received yet, and nothing expected — either no holding pays out, or Yahoo has not been asked yet.': 'Aún no se han recibido dividendos ni se espera nada — o ninguna posición reparte, o todavía no se ha consultado a Yahoo.',
    'Per month, expected': 'Al mes, esperado',
    'Per share': 'Por acción',
    'Per share, a year': 'Por acción, al año',
    'Received': 'Recibido',
    'Received, 12 months': 'Recibido, 12 meses',
    'Received, all': 'Recibido, total',
    'Received, last twelve months': 'Recibido, últimos doce meses',
    "What the holdings paid out, month by month, and what is due in the next twelve: each holding's payments of the last year, times the units held today, a year on. A calendar, not a forecast — it assumes every payer keeps paying what it paid.": 'Lo que repartieron las posiciones, mes a mes, y lo que toca en los próximos doce: los pagos de cada posición en el último año, por los títulos en cartera hoy, un año después. Un calendario, no una previsión — supone que cada pagador sigue pagando lo que pagó.',
    "Yield on today's value": 'Rentabilidad sobre el valor de hoy',
    'averaged over the year': 'promediado en el año',
    "by ex-date, from last year's dates": 'por fecha ex-dividendo, según las fechas del año pasado',
    'from {n} payer': 'de {n} pagador',
    'from {n} payers': 'de {n} pagadores',
    'no longer held': 'ya no en cartera',
    'on {value}': 'sobre {value}',
    'refresh from Yahoo': 'actualizar desde Yahoo',
    'twelve months back, twelve ahead': 'doce meses atrás, doce adelante',
    '{n} holding has no distribution data at Yahoo.': '{n} posición no tiene datos de reparto en Yahoo.',
    '{n} holdings have no distribution data at Yahoo.': '{n} posiciones no tienen datos de reparto en Yahoo.',
    '{n} payment': '{n} pago',
    '{n} payments': '{n} pagos',
    '{total} since the records begin': '{total} desde el inicio de los registros',
}
