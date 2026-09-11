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
    "Last price": "Último precio",
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
    "Everything you hold, aggregated by ISIN across accounts — the same fund "
    "at two brokers is one position from where you are standing. Values use "
    "the price of your last trade, which is not a market price; a price feed "
    "is the next thing to build.":
        "Todo lo que tienes, agrupado por ISIN a través de las cuentas — el "
        "mismo fondo en dos brókeres es una sola posición desde donde tú "
        "estás. La valoración usa el precio de tu última orden, que no es un "
        "precio de mercado; una fuente de cotizaciones es lo siguiente que "
        "hay que construir.",
    "{n} position": "{n} posición",
    "{n} positions": "{n} posiciones",
    "across all accounts": "en todas las cuentas",
    "what you put in, {currency} positions":
        "lo que pusiste, posiciones en {currency}",
    "at last traded prices, not market":
        "a los últimos precios operados, no al mercado",
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
    "valued at your last traded price, not a market price":
        "valorado a tu último precio operado, no a uno de mercado",
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
    "CSV file": "Archivo CSV",
    "Drop in a CSV your broker exported. The file is recognised by its "
    "columns, so there is nothing to choose — and re-importing a period you "
    "already loaded is harmless, because every row carries an id.":
        "Suelta aquí un CSV que haya exportado tu bróker. El archivo se "
        "reconoce por sus columnas, así que no hay nada que elegir — y volver "
        "a importar un periodo ya cargado no hace daño, porque cada fila lleva "
        "un identificador.",
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
    "Export a period that overlaps what you already imported. Overlap costs "
    "nothing and a gap costs you transactions.":
        "Exporta un periodo que se solape con lo ya importado. El solape no "
        "cuesta nada; un hueco te cuesta transacciones.",
    "Choose a CSV file first.": "Elige primero un archivo CSV.",
    "That file is larger than {mb} MB. A transaction export should be far "
    "smaller — is it the right file?":
        "Ese archivo pasa de {mb} MB. Un export de transacciones es mucho más "
        "pequeño — ¿es el archivo correcto?",
    "That file's columns do not match any importer here. Supported: {list}":
        "Las columnas de ese archivo no encajan con ningún importador de aquí. "
        "Compatibles: {list}",
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
    "{currency} only": "solo {currency}",
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
    "Spent in {month}": "Gastado en {month}",
    "of": "de",
    "budgeted": "presupuestados",
    "{pct}% through the month": "{pct}% del mes transcurrido",
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
    "When the text contains": "Cuando el texto contiene",
    "Added": "Añadida",
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
}
