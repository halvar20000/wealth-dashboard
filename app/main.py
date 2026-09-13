"""Wealth Dashboard — the web app.

Run it:  python -m app          (or `flask --app app.main run`)

The route list is the whole product so far, in order of first use:

    /setup              create the first user — only until one exists
    /login /logout
    /                   accounts and their balances
    /accounts/new       create an account by hand
    /accounts/<id>      one account: balance, transactions, connection
    /settings           categories, Enable Banking credentials, redirect URL
    /connect/<id>       choose a bank
    /connect/<id>/start begin authorisation — leaves for the bank
    /connect/callback   the bank sends the user back here
    /connect/paste      finish by hand when the callback cannot fire
    /accounts/<id>/sync   pull balance and transactions
    /accounts/<id>/import upload a broker CSV
    /screener           share ideas: four ranked boards over a Yahoo cache
    /saxo/connect/<id>  Saxo: OAuth login, then /saxo/callback links the accounts
    /accounts/<id>/connect/kraken   Kraken: link this account to the API key
    /mcp                the MCP endpoint, for an assistant with a token

Every page except /setup and /login requires a signed-in user.
"""

from __future__ import annotations

import io
import os
import re
import secrets
import threading
import time
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import (Flask, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)

from . import __version__, auth, changelog, fx, i18n, prices, settings
from .banks import enablebanking as eb
from .banks import sync as banksync
from . import (allocation, benchmark, cashflow, categories, crypto, export, forecast, gains, history, importers, loans,
               manual, mcp, overview, people, performance, screener, screener_etf,
               screener_jobs, splits, stages, subscriptions)
from . import brokers
from .brokers import kraken, saxo
from . import db as db_state
from .db import get_conn, has_users, init_db

APP_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(APP_DIR / "templates"),
            static_folder=str(APP_DIR / "static"))
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# A transaction export is tens of kilobytes. The ceiling is not about
# disk: it is so that a mis-chosen file — a database dump, a video — is
# refused with a sentence instead of being read into memory first.
MAX_IMPORT_BYTES = 16 * 1024 * 1024

# Stamped onto the stylesheet URL. A cached stylesheet against a new
# template is indistinguishable from a broken page: the markup changes,
# the styling does not, and the reader blames the markup.
try:
    _ASSET_VERSION = int((APP_DIR / "static" / "css" / "app.css").stat().st_mtime)
except OSError:
    _ASSET_VERSION = 0
app.config["MAX_CONTENT_LENGTH"] = MAX_IMPORT_BYTES + 1024


def _secret_key() -> bytes:
    """Persisted, because a key regenerated on every restart signs
    everyone out on every restart — which teaches people to expect the
    login page and hides a real session problem when one appears."""
    env = os.environ.get("WD_SECRET_KEY")
    if env:
        return env.encode()
    settings.ensure_dirs()
    path = settings.SECRETS_DIR / "flask_secret"
    if path.exists():
        return path.read_bytes()
    key = secrets.token_bytes(32)
    path.write_bytes(key)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key


app.secret_key = _secret_key()


@app.before_request
def _first_run_gate():
    """Before anybody exists, every path leads to /setup. A login form in
    front of an app with no users is a door with no key."""
    if request.endpoint in ("static", "setup", "healthz", "mcp_endpoint"):
        return None
    if not has_users():
        return redirect(url_for("setup"))
    return None


@app.after_request
def _no_store(response):
    """A financial page must not be sitting in the browser cache after a
    logout, or behind the back button on a shared machine."""
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


# The language lives in i18n, which every layer can reach. These are
# the names it goes by on a page: `_` rather than `t`, because templates
# already loop over transactions as `t` and a global shadowed halfway
# down a table is a bug that only shows up in the rows.
current_language = i18n.active
_t, _f, _n = i18n.t, i18n.f, i18n.n


def _money(amount, currency=None) -> str:
    """One place that formats money, so two pages cannot disagree about
    what a thousand euros looks like."""
    currency = (currency or settings.get("base_currency", "EUR"))
    return i18n.money(amount, currency, current_language())


def _qty(value) -> str:
    return i18n.qty(value, current_language())


def _date(value) -> str:
    return i18n.fmt_date(value, current_language())


def _month(value) -> str:
    return i18n.fmt_month(value, current_language())


# The five account types, and the English of each. Stored as the slug,
# shown through the catalogue — so a German install lists "Girokonto"
# while the database still says "bank" and an export still matches.
ACCOUNT_TYPES = {"bank": "Bank account", "savings": "Savings",
                 "card": "Credit card", "broker": "Broker",
                 "loan": "Loan or mortgage", "other": "Other"}


def _type_label(slug: str) -> str:
    return _t(ACCOUNT_TYPES.get(slug, slug))


# What a bank or broker called the event. Stored as the slug the
# importers assign; shown through the catalogue. A kind this app has
# never heard of is shown as it arrived rather than swallowed.
KINDS = {"deposit": "deposit", "withdrawal": "withdrawal", "buy": "buy",
         "sell": "sell", "dividend": "dividend", "interest": "interest",
         "fee": "fee", "tax": "tax", "transfer": "transfer",
         "other": "other", "split": "split"}


# What a security is, as allocation.py names it — shown through the
# catalogue with a context suffix, like the kinds.
ASSET_CLASS_LABELS = allocation.CLASS_NAMES
REGION_LABELS = allocation.REGION_NAMES


# How often a subscription repeats, as subscriptions.py names it.
RHYTHMS = ("weekly", "monthly", "quarterly", "half-yearly", "yearly")


def _rhythm_label(name: str) -> str:
    return _t(f"{name} [rhythm]") if name in RHYTHMS else (name or "")


def _kind_label(slug: str) -> str:
    return _t(f"{KINDS[slug]} [kind]") if slug in KINDS else (slug or "")


@app.context_processor
def _globals():
    return {"user": auth.current_user(),
            "base_currency": settings.get("base_currency", "EUR"),
            "money": _money, "qty": _qty, "d": _date, "mon": _month,
            "_": _t, "_n": _n, "_f": _f, "lang": current_language(),
            "languages": i18n.LANGUAGES,
            "categories": categories,
            "account_types": ACCOUNT_TYPES, "type_label": _type_label,
            "kind_label": _kind_label, "rhythm_label": _rhythm_label,
            "class_label": allocation.class_label, "region_label": allocation.region_label,
            "asset_version": _ASSET_VERSION,
            "version": __version__,
            # The household, and whose picture the header is set to.
            "people": people.all_people() if auth.current_user() else [],
            "view_person": people.current() if auth.current_user() else None}


@app.route("/healthz")
def healthz():
    # The version is here so a monitor can see a container that never
    # restarted after an update — which looks identical to a healthy one
    # from the outside.
    return {"ok": True, "configured": has_users(), "version": __version__}


@app.route("/changelog")
@auth.login_required
def changelog_page():
    """What changed, read out of CHANGELOG.md.

    Behind the login like every other page: it is not a secret, but an
    unauthenticated page is a page that tells a stranger which version
    you are running and therefore which bugs you still have.
    """
    return render_template("changelog.html", active_page="changelog",
                           releases=changelog.load(), version=__version__)


# ─── First run and sign-in ───────────────────────────────────────────

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if has_users():
        return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        try:
            uid = auth.create_user(request.form.get("username", ""),
                                   request.form.get("password", ""))
            if request.form.get("password") != request.form.get("password2"):
                raise ValueError("The two passwords do not match.")
            session["uid"] = uid
            return redirect(url_for("index"))
        except ValueError as exc:
            error = str(exc)
    return render_template("setup.html", error=error,
                           username=request.form.get("username", ""))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        ip = request.remote_addr or "?"
        if auth.throttled(ip):
            error = _t("Too many attempts. Wait a few minutes.")
        else:
            user = auth.verify(request.form.get("username", ""),
                               request.form.get("password", ""))
            if user:
                session.clear()
                session["uid"] = user["id"]
                session.permanent = True
                return redirect(auth.safe_next(request.args.get("next")))
            auth.record_failure(ip)
            # One message for both cases. "No such user" tells an
            # attacker which half to keep guessing.
            error = _t("Wrong username or password.")
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─── Accounts ────────────────────────────────────────────────────────

@app.route("/")
@auth.login_required
def index():
    base = settings.get("base_currency", "EUR")
    return render_template(
        "overview.html", active_page="overview",
        s=overview.summary(base, account_ids=people.scope()),
        history=history.series(base, people.scope(), "ytd"),
        health=banksync.health())


@app.route("/api/networth")
@auth.login_required
def api_networth():
    """The hero chart's data for one period, under the current view."""
    period = request.args.get("period") or "ytd"
    if period not in history.PERIODS:
        period = "ytd"
    return history.series(settings.get("base_currency", "EUR"),
                          people.scope(), period)


@app.route("/view", methods=["POST"])
@auth.login_required
def view_switch():
    """The header's switch: everyone, or one person. Back to the page
    it was pressed on, which now adds up differently."""
    chosen = (request.form.get("person") or "").strip()
    people.choose(int(chosen) if chosen.isdigit() else None)
    nxt = request.form.get("next") or ""
    if not nxt.startswith("/") or nxt.startswith("//"):
        nxt = url_for("index")
    return redirect(nxt)


@app.route("/accounts")
@auth.login_required
def accounts():
    return render_template(
        "accounts.html", active_page="accounts",
        s=overview.summary(settings.get("base_currency", "EUR"),
                           account_ids=people.scope()))


@app.route("/accounts/new", methods=["GET", "POST"])
@auth.login_required
def account_new():
    error = None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            error = _t("The account needs a name.")
        else:
            with get_conn() as conn:
                cur = conn.execute(
                    "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                    (name, request.form.get("type") or "bank",
                     (request.form.get("currency") or "EUR").upper()[:3]))
                new_id = int(cur.lastrowid)
            people.set_for_account(new_id, request.form.getlist("people"))
            return redirect(url_for("account_detail", account_id=new_id))
    # An account made while looking at one person's picture is probably
    # theirs, so their box starts ticked. A tick is easy to remove.
    viewing = people.current()
    return render_template("account_new.html", error=error,
                           base_currency=settings.get("base_currency", "EUR"),
                           owner_ids={viewing["id"]} if viewing else set())


@app.route("/accounts/<int:account_id>")
@auth.login_required
def account_detail(account_id: int):
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what=_t("That account does not exist.")), 404
        link = conn.execute("SELECT * FROM bank_links WHERE account_id = ? LIMIT 1",
                            (account_id,)).fetchone()
        balance = conn.execute(
            "SELECT * FROM balances WHERE account_id = ? "
            "ORDER BY as_of DESC, id DESC LIMIT 1", (account_id,)).fetchone()
        txns = conn.execute(
            "SELECT * FROM transactions WHERE account_id = ? "
            "ORDER BY txn_date DESC, id DESC LIMIT 200", (account_id,)).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM transactions WHERE account_id = ?",
            (account_id,)).fetchone()["n"]

    link = dict(link) if link else None
    if link:
        link["days_left"] = banksync.days_until_expiry(link.get("valid_until"))
    return render_template("account.html", account=dict(account), link=link,
                           broker=brokers.link_for(account_id),
                           saxo_state=saxo.describe(),
                           kraken_ready=kraken.credentials_present(),
                           positions=importers.positions(account_id),
                           balance=dict(balance) if balance else None,
                           transactions=[dict(t) for t in txns],
                           total_transactions=total,
                           configured=banksync.credentials_present(),
                           owners=people.for_account(account_id),
                           today=date.today().isoformat())


def _account_counts(conn, account_id: int) -> dict:
    """What an account is holding. The page and the delete both ask
    this, so they cannot disagree about whether there is anything to
    lose."""
    counts = {
        "transactions": conn.execute(
            "SELECT COUNT(*) n FROM transactions WHERE account_id = ?",
            (account_id,)).fetchone()["n"],
        "balances": conn.execute(
            "SELECT COUNT(*) n FROM balances WHERE account_id = ?",
            (account_id,)).fetchone()["n"],
        "links": conn.execute(
            "SELECT COUNT(*) n FROM bank_links WHERE account_id = ?",
            (account_id,)).fetchone()["n"],
    }
    counts["empty"] = not (counts["transactions"] or counts["balances"]
                           or counts["links"])
    return counts


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@auth.login_required
def account_edit(account_id: int):
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what=_t("That account does not exist.")), 404
        counts = _account_counts(conn, account_id)

    error = None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            error = _t("The account needs a name.")
        else:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE accounts SET name = ?, type = ?, currency = ? "
                    "WHERE id = ?",
                    (name, request.form.get("type") or "bank",
                     (request.form.get("currency") or "EUR").upper()[:3],
                     account_id))
            people.set_for_account(account_id, request.form.getlist("people"))
            flash(_t("Account updated."), "ok")
            return redirect(url_for("account_detail", account_id=account_id))

    return render_template("account_edit.html", account=dict(account),
                           counts=counts, error=error, active_page="accounts",
                           owner_ids={p["id"] for p in people.for_account(account_id)})


@app.route("/accounts/<int:account_id>/delete", methods=["POST"])
@auth.login_required
def account_delete(account_id: int):
    """Delete an account and everything hanging off it.

    The friction is proportionate to what is at stake, because friction
    that is always there is friction nobody reads.

    An account holding nothing — no transactions, no balance readings,
    no bank connection — goes on one click. It is the account you
    created with a typo in the name thirty seconds ago, and making
    somebody type the name of a thing that is empty teaches them that
    the confirmation is a formality, which is exactly the lesson you do
    not want them carrying into the next one.

    An account holding anything is confirmed by typing its name, not by
    an "are you sure" dialog. The dialog is clicked through without
    reading; a name cannot be typed by accident, and that is the
    difference between removing the duplicate you made by mistake and
    removing the one with six years in it.

    Which of the two it is, is decided here from the database and never
    from the form: a hidden field saying "this one was empty" is a
    hidden field somebody can send.
    """
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what=_t("That account does not exist.")), 404
        counts = _account_counts(conn, account_id)
        if not counts["empty"] and \
                (request.form.get("confirm") or "").strip() != account["name"]:
            flash(_t("Type the account name exactly to confirm the deletion."),
                  "error")
            return redirect(url_for("account_edit", account_id=account_id))
        # ON DELETE CASCADE takes the transactions, balances and links.
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    flash(_f("Deleted {name}.", name=account["name"]), "ok")
    return redirect(url_for("accounts"))


@app.route("/accounts/<int:account_id>/import", methods=["GET", "POST"])
@auth.login_required
def account_import(account_id: int):
    """Upload a broker CSV, or a set of statement PDFs.

    The file is recognised rather than declared. Asking someone to pick
    the right parser from a list, for a file that says which broker it
    came from on every line, is asking them to get it wrong — and the
    wrong parser does not fail, it produces a confident mess.

    Several files at once, and a ZIP of them, because a Depot's history
    is one PDF per order and nobody should upload ninety files one at a
    time. Each file is recognised on its own, so a CSV and a pile of
    PDFs can arrive in the same upload.
    """
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
    if account is None:
        return render_template("missing.html",
                               what=_t("That account does not exist.")), 404

    report = None
    if request.method == "POST":
        uploads = [u for u in request.files.getlist("file") if u and u.filename]
        if not uploads:
            flash(_t("Choose a CSV or PDF file first."), "error")
            return redirect(url_for("account_import", account_id=account_id))

        files = []                              # (name, bytes)
        for upload in uploads:
            content = upload.read(MAX_IMPORT_BYTES + 1)
            if len(content) > MAX_IMPORT_BYTES:
                flash(_f("{name} is larger than {mb} MB. A transaction export "
                         "should be far smaller — is it the right file?",
                         name=upload.filename, mb=MAX_IMPORT_BYTES // (1024 * 1024)),
                      "error")
                return redirect(url_for("account_import", account_id=account_id))
            files.extend(_unpack(upload.filename, content))

        try:
            report = _import_files(account_id, account["currency"], files)
        except RuntimeError as exc:                  # a PDF, and no pypdf
            flash(str(exc), "error")
            return redirect(url_for("account_import", account_id=account_id))
        if report is None:
            # A CSV nobody here knows is not a dead end: the user says
            # which column is which, once, and the header is remembered.
            csvs = [(n, c) for n, c in files if importers.generic.is_csv(c)]
            if csvs:
                token = _stash_upload(account_id, *csvs[0])
                return redirect(url_for("import_map", account_id=account_id, token=token))
            flash(_f("None of those files match an importer here. "
                     "Supported: {list}",
                     list=", ".join(m.LABEL for m in importers.IMPORTERS
                                    + importers.PDF_IMPORTERS)),
                  "error")
            return redirect(url_for("account_import", account_id=account_id))
        if not report["parsed"] and report["problems"]:
            # Nothing readable in any of it. Say why, not "0 new".
            flash(report["problems"][0], "error")
            return redirect(url_for("account_import", account_id=account_id))
        flash(_f("{importer}: {new} new, {had} already had.",
                 importer=report["label"], new=report["inserted"],
                 had=report["duplicates"]), "ok")

    return render_template("import.html", account=dict(account), report=report,
                           importers=importers.IMPORTERS + importers.PDF_IMPORTERS)


# A ZIP is opened, but not blindly: a few hundred statements is a big
# Depot; a hundred thousand entries is not a Depot.
MAX_ZIP_MEMBERS = 2000

# An upload that is waiting for its column mapping, in memory under a
# token for half an hour. Not on disk: it is a bank statement, and a
# user who walks away from the mapping page should leave nothing behind.
_PENDING: dict[str, dict] = {}
PENDING_TTL = 30 * 60


def _stash_upload(account_id: int, name: str, content: bytes) -> str:
    now = time.time()
    for tok in [t for t, p in _PENDING.items() if now - p["at"] > PENDING_TTL]:
        _PENDING.pop(tok, None)
    token = secrets.token_urlsafe(16)
    _PENDING[token] = {"account_id": account_id, "name": name, "content": content, "at": now}
    return token


# What a column heading usually means, for the first guess on the
# mapping page — in the languages the banks this app targets write in.
# A guess the user corrects in one click; a blank form is twelve.
_HEADER_GUESSES = {
    "txn_date": ("date", "datum", "fecha", "buchungstag", "buchungsdatum", "valuta", "booking"),
    "amount": ("amount", "betrag", "montant", "importe", "value", "umsatz", "wert"),
    "debit": ("debit", "soll", "débit", "debe", "ausgang", "lastschrift"),
    "credit": ("credit", "haben", "crédit", "haber", "eingang", "gutschrift"),
    "description": ("description", "beschreibung", "verwendungszweck", "libellé", "libelle",
                    "concepto", "text", "buchungstext", "memo", "details", "purpose"),
    "counterparty": ("counterparty", "payee", "empfänger", "beneficiary", "auftraggeber",
                     "gegenkonto", "bénéficiaire", "contrapartida", "zahlungsempfänger", "name"),
    "currency": ("currency", "währung", "devise", "divisa", "ccy"),
    "isin": ("isin",),
    "security_name": ("security", "wertpapier", "titre", "producto", "product", "produkt",
                      "bezeichnung", "instrument", "valor"),
    "quantity": ("quantity", "anzahl", "stück", "quantité", "cantidad", "units", "nominal", "shares"),
    "price": ("price", "kurs", "prix", "precio", "rate"),
    "fee": ("fee", "gebühr", "frais", "comisión", "commission", "kosten"),
    "tax": ("tax", "steuer", "impôt", "impuesto", "withholding"),
    "kind": ("type", "typ", "art", "kind", "transaktion", "transaction type", "tipo", "opération",
             "umsatzart", "buchungsart", "transaktionsart", "geschäftsart", "vorgang", "nature"),
}


def _guess_mapping(header: list[str]) -> dict:
    guess: dict[str, str] = {}
    lowered = [(h, h.lower()) for h in header]
    # A heading matches a word whole — "Umsatzart" is a kind, not an
    # "Umsatz"; "Betrag (EUR)" is an amount. Kind before amount, so the
    # kind column is not taken for money first.
    order = ["kind"] + [f for f in _HEADER_GUESSES if f != "kind"]
    for field in order:
        words = _HEADER_GUESSES[field]
        for h, low in lowered:
            if h in guess.values():
                continue
            if any(re.search(rf"(^|[^a-zäöüéèàñ]){re.escape(w)}([^a-zäöüéèàñ]|$)", low) for w in words):
                guess[field] = h
                break
    # Debit and credit only make sense as a pair; a lone "debit" guess
    # beside a signed amount column is the amount column's job.
    if guess.get("amount") and (guess.get("debit") or guess.get("credit")):
        guess.pop("debit", None); guess.pop("credit", None)
    return guess


@app.route("/accounts/<int:account_id>/import/map/<token>", methods=["GET", "POST"])
@auth.login_required
def import_map(account_id: int, token: str):
    """Draw the column mapping for a CSV no importer knows, see the
    first rows read through it, and import — the mapping is kept under
    the file's header, so the next export from that bank is recognised
    like any other."""
    from .importers import generic
    account = _load_account(account_id)
    if account is None:
        return render_template("missing.html", what=_t("That account does not exist.")), 404
    pending = _PENDING.get(token)
    if pending is None or pending["account_id"] != account_id \
            or time.time() - pending["at"] > PENDING_TTL:
        flash(_t("That upload has expired — choose the file again."), "error")
        return redirect(url_for("account_import", account_id=account_id))
    header, rows, delimiter = generic.read(pending["content"])
    saved = generic.find(header)
    mapping = (saved["mapping"] if saved else None) or _guess_mapping(header)
    name = saved["name"] if saved else os.path.splitext(os.path.basename(pending["name"]))[0][:40]
    preview, problems, wrong = None, [], []
    if request.method == "POST":
        mapping = {f: request.form.get(f"col_{f}") for f in generic.FIELDS
                   if request.form.get(f"col_{f}") in header}
        if request.form.get("negate"):
            mapping["negate"] = True
        fixed = (request.form.get("currency_fixed") or "").strip().upper()[:3]
        if fixed and not mapping.get("currency"):
            mapping["currency_fixed"] = fixed
        name = " ".join((request.form.get("name") or "").split())[:80] or name
        wrong = generic.check(mapping)
        if wrong:
            flash(_t("A date column and an amount column — or a debit and a credit column — are the least a mapping needs."), "error")
        elif request.form.get("action") == "import":
            generic.save(name, header, delimiter, mapping)
            report = _import_files(account_id, account["currency"], [(pending["name"], pending["content"])])
            _PENDING.pop(token, None)
            if report and report["parsed"]:
                flash(_f("{importer}: {new} new, {had} already had.", importer=report["label"],
                         new=report["inserted"], had=report["duplicates"]), "ok")
                flash(_f("The mapping is saved as {name}; the next file with this header is recognised by itself.", name=name), "ok")
                return render_template("import.html", account=account, report=report,
                                       importers=importers.IMPORTERS + importers.PDF_IMPORTERS)
            flash((report["problems"][0] if report and report["problems"] else _t("Not one row could be read through that mapping.")), "error")
            return redirect(url_for("account_import", account_id=account_id))
    parsed = generic.parse_with(mapping, pending["content"], account["currency"], delimiter, limit=8)
    preview, problems = parsed.rows, parsed.problems[:5]
    return render_template("import_map.html", account=account, token=token, name=name,
                           header=header, sample=rows[:5], delimiter=delimiter,
                           mapping=mapping, fields=generic.FIELDS, preview=preview,
                           problems=problems, wrong=wrong, saved=saved,
                           kind_words=sorted(w for ws in generic.KIND_WORDS.values() for w in ws))


def _unpack(name: str, content: bytes) -> list[tuple[str, bytes]]:
    """A ZIP becomes its files; anything else is itself."""
    import zipfile
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return [(name, content)]
    out = []
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        for info in z.infolist()[:MAX_ZIP_MEMBERS]:
            if info.is_dir() or info.file_size > MAX_IMPORT_BYTES:
                continue
            base = os.path.basename(info.filename)
            if not base or base.startswith(".") or "__MACOSX" in info.filename:
                continue
            out.append((f"{name}/{info.filename}", z.read(info)))
    return out


def _import_files(account_id: int, currency: str, files: list[tuple[str, bytes]]):
    """Every file through its own importer; one report for all of them.

    None if not a single file was recognised. A file that was not — a
    Kontoauszug among the Abrechnungen, say — is listed by name under
    problems, with the others imported around it, rather than failing
    the whole upload for one stray document.
    """
    total = {"inserted": 0, "duplicates": 0, "skipped": 0, "parsed": 0,
             "problems": [], "closing_balance": None, "files": len(files),
             "unrecognised": []}
    labels: list[str] = []
    many = len(files) > 1
    for name, content in files:
        module = importers.sniff(content)
        if module is None:
            total["unrecognised"].append(name)
            continue
        parsed = module.parse(content, account_currency=currency)
        r = importers.store(account_id, parsed, module.SLUG)
        for key in ("inserted", "duplicates", "skipped", "parsed"):
            total[key] += r[key]
        total["problems"].extend(
            f"{os.path.basename(name)}: {p}" if many else p for p in r["problems"])
        if r["closing_balance"]:
            total["closing_balance"] = r["closing_balance"]
        if module.LABEL not in labels:
            labels.append(module.LABEL)
    if not labels:
        return None
    for name in total["unrecognised"]:
        total["problems"].append(
            f"{os.path.basename(name)}: " + _t("not recognised, left out"))
    total["label"] = ", ".join(labels)
    return total


def _load_account(account_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?",
                           (account_id,)).fetchone()
    return dict(row) if row else None


@app.route("/accounts/<int:account_id>/add", methods=["GET", "POST"])
@auth.login_required
def account_add(account_id: int):
    """Type a transaction in by hand — see manual.py for why.

    On an error the form comes back filled in, not blank: a person who
    has typed an ISIN, a quantity and a price and mistyped the date
    should fix the date, not start over.
    """
    account = _load_account(account_id)
    if account is None:
        return render_template("missing.html",
                               what=_t("That account does not exist.")), 404
    error = None
    if request.method == "POST":
        try:
            manual.add_transaction(account, request.form)
            flash(_t("Added."), "ok")
            if request.form.get("another"):
                return redirect(url_for("account_add", account_id=account_id))
            return redirect(url_for("account_detail", account_id=account_id))
        except ValueError as exc:
            error = str(exc)
    return render_template(
        "account_add.html", account=account, error=error,
        form=request.form if request.method == "POST" else {},
        kinds=manual.kinds_for(account["type"]), trades=manual.TRADES,
        directional=manual.DIRECTIONAL, today=date.today().isoformat())


@app.route("/accounts/<int:account_id>/balance", methods=["POST"])
@auth.login_required
def account_balance(account_id: int):
    """Record the balance as of a day, for an account nothing reports on."""
    account = _load_account(account_id)
    if account is None:
        return render_template("missing.html",
                               what=_t("That account does not exist.")), 404
    try:
        reading = manual.set_balance(account, request.form)
        flash(_f("Balance recorded: {amount} as of {date}.",
                 amount=_money(reading["amount"], reading["currency"]),
                 date=i18n.fmt_date(reading["as_of"], current_language())), "ok")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("account_detail", account_id=account_id))


@app.route("/securities/<path:isin>")
@auth.login_required
def security_page(isin: str):
    """One security, and every row behind its holding — the buys, the
    sales, the dividends, the transfers — across every account, each
    row editable. The place to go when a quantity on the portfolio
    page looks wrong: the answer is always one of these rows.
    """
    isin = isin.strip()
    only, params = people.sql_in(people.scope(), "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name, a.type AS account_type, "
            f"a.currency AS account_currency FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id WHERE t.isin = ?{only} "
            f"ORDER BY t.txn_date, t.id", [isin, *params]).fetchall()]
        sec = conn.execute("SELECT * FROM securities WHERE isin = ?", (isin,)).fetchone()
    if not rows:
        return render_template("missing.html", what=_t("No transaction carries that security.")), 404
    running = 0.0
    for r in rows:
        running += r["quantity"] or 0.0
        r["running"] = running
        r["kinds"] = manual.kinds_for(r["account_type"])
    # Year → month, newest first, each with what was bought, sold and
    # paid out. Twelve identical savings-plan buys are noise as a flat
    # list and a story grouped: "six buys this year, 1 200 in".
    groups = _cluster(rows)
    name = next((r["security_name"] for r in reversed(rows) if r["security_name"]), None) \
        or (sec["name"] if sec else None) or isin
    currency = next((r["currency"] for r in rows if r["kind"] in ("buy", "sell")), rows[0]["currency"])
    price = prices.latest().get(isin)
    # Which currency the page is in: the one the shares were paid in
    # unless asked otherwise — the one they are quoted in, or the
    # dashboard's base. Amounts are turned at their own day's rate;
    # today's price at today's. The rows below stay as booked.
    base = settings.get("base_currency", "EUR")
    options = []
    for c_ in (currency, price["currency"] if price else None, base):
        if c_ and c_.upper() not in options:
            options.append(c_.upper())
    roles = {currency.upper(): "paid"}
    if price and price.get("currency"):
        roles.setdefault(price["currency"].upper(), "quoted")
    roles.setdefault(base.upper(), "base")
    asked = (request.args.get("ccy") or "").upper()
    shown = asked if asked in options else currency.upper()
    convert = prices.in_currency(shown)
    if price and price.get("currency") and price["currency"].upper() != shown:
        quoted = dict(price)
        converted = convert(price["price"], price["currency"], price["as_of"])
        price = {**price, "price": converted, "currency": shown, "quoted": quoted} if converted is not None else price
    def in_shown(r):
        return convert(r["amount"], r["currency"], r["txn_date"]) or 0.0
    net_invested = sum(-in_shown(r) for r in rows if r["kind"] == "buy") \
        - sum(in_shown(r) for r in rows if r["kind"] == "sell")
    income = sum(in_shown(r) for r in rows if r["kind"] in ("dividend", "interest"))
    costs = {"fees": sum(convert(r["fee"], r["currency"], r["txn_date"]) or 0.0 for r in rows if r["fee"]),
             "taxes": sum(convert(r["tax"], r["currency"], r["txn_date"]) or 0.0 for r in rows if r["tax"])}
    # What each sale made, by lots — and what the units still held
    # cost, which is the cost basis the unrealised gain is measured
    # against. Both under the method chosen in Settings.
    realised = gains.realised(isin, people.scope())
    by_sale = {s_["id"]: s_ for s_ in realised["sales"]}
    for r in rows:
        r["sale"] = by_sale.get(r["id"])
    unrealised = None
    if price and price.get("price") is not None and realised["open_quantity"] > 1e-12:
        # The lots' cost is in the trade currency; in another it is
        # turned at today's rate — what the same money would be now.
        open_cost = realised["open_cost"] if shown == currency.upper() \
            else convert(realised["open_cost"], currency, price["as_of"])
        if open_cost is not None:
            unrealised = price["price"] * realised["open_quantity"] - open_cost
    return render_template("security.html", active_page="portfolio", isin=isin, name=name,
                           perf=performance.for_security(isin, people.scope(), currency=shown),
                           shown=shown, options=options, roles=roles, benchmarks=benchmark.BENCHMARKS,
                           realised=realised, unrealised=unrealised,
                           rows=rows, groups=groups, quantity=running, net_invested=net_invested,
                           income=income, costs=costs, price=price, currency=currency,
                           symbol=sec["symbol"] if sec else None,
                           trades=manual.TRADES, directional=manual.DIRECTIONAL,
                           accounts=sorted({r["account_name"] for r in rows}))


@app.route("/securities/<isin>/split", methods=["POST"])
@auth.login_required
def security_split(isin: str):
    """Record a stock split: one `split` row per account holding the
    security that day, so every earlier row is read in today's units.
    See splits.py."""
    isin = isin.strip()
    try:
        written = splits.record(isin, request.form.get("txn_date"), request.form.get("ratio"),
                                people.scope())
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("security_page", isin=isin) + "#split")
    if not written:
        flash(_t("Nothing was held on that day — or that split is already recorded."), "error")
    else:
        flash(_n(len(written), "Split recorded on {n} account.", "Split recorded on {n} accounts."), "ok")
    return redirect(url_for("security_page", isin=isin))


def _cluster(rows: list[dict]) -> list[dict]:
    """[{year, months: [{month, rows, ...totals}], ...totals}], newest
    first, rows within a month newest first too. The totals are the
    money that went into buys, came out of sales, and was paid as
    dividends or interest — the three things a person asks of a month."""
    def totals(items):
        return {"count": len(items),
                "bought": sum(-r["amount"] for r in items if r["kind"] == "buy"),
                "sold": sum(r["amount"] for r in items if r["kind"] == "sell"),
                "income": sum(r["amount"] for r in items if r["kind"] in ("dividend", "interest")),
                "units": sum(r["quantity"] or 0.0 for r in items)}
    years: dict[str, dict] = {}
    for r in rows:
        y, m = r["txn_date"][:4], r["txn_date"][:7]
        year = years.setdefault(y, {"year": y, "months": {}})
        year["months"].setdefault(m, []).append(r)
    out = []
    for y in sorted(years, reverse=True):
        months = [{"month": m, "rows": sorted(items, key=lambda r: (r["txn_date"], r["id"]), reverse=True),
                   **totals(items)} for m, items in sorted(years[y]["months"].items(), reverse=True)]
        out.append({"year": y, "months": months, **totals([r for mo in months for r in mo["rows"]])})
    return out


@app.route("/crypto")
@app.route("/crypto/<coin>")
@auth.login_required
def crypto_page(coin: str | None = None):
    base = settings.get("base_currency", "EUR")
    held = crypto.coins(base, people.scope())
    chosen = next((c for c in held if c["code"] == (coin or "").upper()), held[0] if held else None)
    if coin and chosen and chosen["code"] != coin.upper():
        return render_template("missing.html", what=_t("No such coin is held.")), 404
    return render_template("crypto.html", active_page="crypto", coins=held, coin=chosen,
                           rows=crypto.recent(chosen["isin"], people.scope()) if chosen else [])


@app.route("/api/crypto/<coin>/chart")
@auth.login_required
def api_crypto_chart(coin: str):
    range_key = request.args.get("range", "3m")
    if range_key not in crypto.RANGES:
        range_key = "3m"
    mode = "wallet" if request.args.get("mode") == "wallet" else "price"
    try:
        return crypto.chart(f"{prices.CRYPTO_PREFIX}{coin.upper()}", range_key, mode,
                            settings.get("base_currency", "EUR"), people.scope())
    except prices.PriceError as exc:
        return {"points": [], "error": str(exc)}


# ─── Loans and mortgages ─────────────────────────────────────────────

@app.route("/loans", methods=["GET", "POST"])
@auth.login_required
def loans_page():
    if request.method == "POST":
        action = request.form.get("form")
        try:
            if action == "loan_add":
                loans.add(request.form, request.form.getlist("people"))
                flash(_t("Loan added. Its balance is on the overview from today."), "ok")
            elif action == "loan_edit":
                loans.update(int(request.form.get("id", "0")), request.form)
                flash(_t("Loan updated."), "ok")
            elif action == "loan_delete":
                loan = loans.get(int(request.form.get("id", "0")))
                if loan and (request.form.get("confirm") or "").strip() != loan["name"]:
                    flash(_t("Type the loan's name exactly to confirm the deletion."), "error")
                else:
                    loans.delete(int(request.form.get("id", "0")))
                    flash(_t("Loan deleted, with its account."), "ok")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("loans_page"))
    loans.write_all_balances()
    items = []
    for loan in loans.all_loans(people.scope()):
        st = loans.status(loan)
        items.append({**loan, "status": st, "schedule": loans.schedule(loan),
                      "extras_text": "\n".join(f"{e['date']} {e['amount']:g}" for e in loans._extras(loan)),
                      "owners": people.for_account(loan["account_id"])})
    base = settings.get("base_currency", "EUR")
    total = sum(v for v in (fx.convert(i["status"]["balance"], i["currency"], base)[0]
                            for i in items) if v is not None)
    per_month = sum(v for v in (fx.convert(i["status"]["per_month"], i["currency"], base)[0]
                                for i in items) if v is not None)
    return render_template("loans.html", active_page="loans", loans=items,
                           total_debt=total, per_month=per_month, base_currency=base,
                           periods=loans.PERIODS, today=date.today().isoformat(),
                           viewing=people.current())


@app.route("/api/securities/<path:isin>/history")
@auth.login_required
def api_security_history(isin: str):
    """Day by day since the first row: units, invested, value, income —
    in the currency asked for with `ccy`, else the one the shares were
    paid in."""
    ccy = (request.args.get("ccy") or "").upper() or None
    return prices.series_for(isin.strip(), people.scope(), currency=ccy)


@app.route("/transactions/<int:txn_id>/edit", methods=["POST"])
@auth.login_required
def transaction_edit(txn_id: int):
    """Correct one row. Back to wherever the form was, which is the
    security page when it came from there."""
    try:
        manual.update_transaction(txn_id, request.form)
        flash(_t("Corrected."), "ok")
    except ValueError as exc:
        flash(str(exc), "error")
    back = request.form.get("back") or ""
    if not back.startswith("/") or back.startswith("//"):
        back = url_for("transactions")
    return redirect(back)


@app.route("/accounts/<int:account_id>/transactions/<int:txn_id>/delete",
           methods=["POST"])
@auth.login_required
def transaction_delete(account_id: int, txn_id: int):
    if manual.delete_transaction(account_id, txn_id):
        flash(_t("Removed."), "ok")
    else:
        flash(_t("Only a transaction typed in by hand can be removed. An "
                 "imported one would only come back with the next import."),
              "error")
    back = request.form.get("back") or ""
    if back.startswith("/") and not back.startswith("//"):
        return redirect(back)
    return redirect(url_for("account_detail", account_id=account_id))


@app.route("/accounts/<int:account_id>/sync", methods=["POST"])
@auth.login_required
def account_sync(account_id: int):
    broker = brokers.link_for(account_id)
    if broker:
        result = brokers.sync_link(broker)
        if result["error"]:
            flash(_f("Sync failed: {reason}", reason=result["error"]), "error")
        else:
            flash(_n(result["inserted"], "Imported {n} new transaction.",
                     "Imported {n} new transactions."), "ok")
        return redirect(url_for("account_detail", account_id=account_id))
    with get_conn() as conn:
        link = conn.execute("SELECT id FROM bank_links WHERE account_id = ? LIMIT 1",
                            (account_id,)).fetchone()
    if link is None:
        flash(_t("That account is not connected to a bank."), "error")
    else:
        result = banksync.sync_link(int(link["id"]))
        if result["error"]:
            flash(_f("Sync failed: {reason}", reason=result["error"]), "error")
        else:
            flash(_n(result["inserted"], "Imported {n} new transaction.",
                     "Imported {n} new transactions."), "ok")
    return redirect(url_for("account_detail", account_id=account_id))


# ─── Brokers by API: Saxo and Kraken ─────────────────────────────────

@app.route("/saxo/connect/<int:account_id>")
@auth.login_required
def saxo_connect(account_id: int):
    """Off to Saxo's login. What comes back lands on /saxo/callback."""
    try:
        return redirect(saxo.begin_connect(account_id))
    except saxo.SaxoError as exc:
        flash(str(exc), "error")
        return redirect(url_for("account_detail", account_id=account_id))


def _finish_saxo(code: str, state_token: str):
    try:
        result = saxo.complete_connect(code, state_token)
    except saxo.SaxoError as exc:
        flash(str(exc), "error")
        return None
    flash(_f("Connected: {accounts}", accounts=", ".join(result["linked"])), "ok")
    for r in brokers.sync_all():
        if r["provider"] != "saxo":
            continue
        if r["error"]:
            flash(_f("Connected, but the first sync failed: {reason}", reason=r["error"]), "error")
        else:
            flash(_n(r["inserted"], "Imported {n} transaction.", "Imported {n} transactions."), "ok")
    return result


@app.route("/saxo/callback")
@auth.login_required
def saxo_callback():
    code, state_token = request.args.get("code"), request.args.get("state")
    if request.args.get("error"):
        flash(_f("Saxo refused the login: {reason}", reason=request.args["error"]), "error")
        return redirect(url_for("accounts"))
    if not code or not state_token:
        flash(_t("Saxo sent us back without a code. Paste the address bar on the account page."), "error")
        return redirect(url_for("accounts"))
    result = _finish_saxo(code, state_token)
    if result and result.get("account_id"):
        return redirect(url_for("account_detail", account_id=result["account_id"]))
    return redirect(url_for("accounts"))


@app.route("/saxo/paste/<int:account_id>", methods=["POST"])
@auth.login_required
def saxo_paste(account_id: int):
    """The same finish, from the address bar of the dead page Saxo left
    the browser on — for a redirect URL that points at a host the
    browser could not reach."""
    code, state_token = _parse_pasted_redirect(request.form.get("pasted") or "")
    if not code or not state_token:
        flash(_t("No code and state in that. Paste the whole address, including "
                 "the ?code=… part."), "error")
    else:
        _finish_saxo(code, state_token)
    return redirect(url_for("account_detail", account_id=account_id))


@app.route("/accounts/<int:account_id>/connect/kraken", methods=["POST"])
@auth.login_required
def kraken_connect(account_id: int):
    """One key, one balance sheet: link it to this account and pull."""
    if not kraken.credentials_present():
        flash(_t("Add your Kraken API key under Settings first."), "error")
        return redirect(url_for("account_detail", account_id=account_id))
    link_id = brokers.add_link(account_id, "kraken", remote_id="kraken",
                               remote_label="Kraken")
    result = brokers.sync_link(next(l for l in brokers.links() if l["id"] == link_id))
    if result["error"]:
        flash(_f("Connected, but the first sync failed: {reason}", reason=result["error"]), "error")
    else:
        flash(_n(result["inserted"], "Connected. Imported {n} transaction.",
                 "Connected. Imported {n} transactions."), "ok")
    return redirect(url_for("account_detail", account_id=account_id))


# ─── MCP ─────────────────────────────────────────────────────────────

@app.route("/mcp", methods=["GET", "POST", "DELETE"])
def mcp_endpoint():
    """JSON-RPC over POST, behind a bearer token — see mcp.py.

    Not behind the login: a program has no session. The token stands in
    for the password and is checked on every message. A missing or wrong
    one is a 401 with nothing else said — which is also what an assistant
    sees before anybody has generated a token at all.
    """
    if not has_users():
        return jsonify({"ok": False, "error": "This dashboard has no user yet."}), 503
    if not mcp.authorised(request.headers.get("Authorization")):
        return (jsonify({"ok": False, "error": "A bearer token from Settings is required."}),
                401, {"WWW-Authenticate": 'Bearer realm="wealth-dashboard"'})
    if request.method != "POST":
        return jsonify({"ok": False, "error": "POST JSON-RPC messages here."}), 405
    body = request.get_json(silent=True)
    if body is None:
        return jsonify(mcp._err(None, mcp.PARSE_ERROR, "The body is not JSON.")), 400
    status, answer = mcp.handle(body)
    if answer is None:
        return "", status
    return jsonify(answer), status


# ─── Settings ────────────────────────────────────────────────────────

# ─── Spending ────────────────────────────────────────────────────────

@app.route("/transactions")
@auth.login_required
def transactions():
    """Everything, filterable. The page people go to when a number
    elsewhere looks wrong, so the filters are the feature."""
    q, category, account_id, kind, clause, params, tag = _transactions_filter()

    only_a, a_params = people.sql_in(people.scope(), "id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id WHERE {clause} "
            f"ORDER BY t.txn_date DESC, t.id DESC LIMIT 400", params).fetchall()]
        total = conn.execute(
            f"SELECT COUNT(*) n, SUM(t.amount) s FROM transactions t "
            f"WHERE {clause}", params).fetchone()
        accounts_list = [dict(r) for r in conn.execute(
            f"SELECT id, name FROM accounts WHERE 1=1{only_a} ORDER BY name",
            a_params).fetchall()]
        kinds = [r["kind"] for r in conn.execute(
            "SELECT DISTINCT kind FROM transactions ORDER BY kind").fetchall()]

    return render_template("transactions.html", active_page="transactions",
                           rows=rows, matched=total["n"], total=total["s"] or 0,
                           accounts=accounts_list, kinds=kinds, tags=categories.all_tags(),
                           q=q, category=category, account_id=account_id, kind=kind, tag=tag)


def _transactions_filter():
    """The page's filters as a WHERE clause — shared with the export,
    so a CSV holds exactly the rows the page shows."""
    q = (request.args.get("q") or "").strip()
    category = request.args.get("category") or ""
    account_id = request.args.get("account") or ""
    kind = request.args.get("kind") or ""
    tag = categories.clean_tag(request.args.get("tag")) or ""
    where, params = ["1=1"], []
    if q:
        where.append("(LOWER(t.description) LIKE ? OR LOWER(COALESCE(t.counterparty,'')) LIKE ?)")
        params += [f"%{q.lower()}%"] * 2
    if tag:
        where.append("(',' || COALESCE(t.tags,'') || ',') LIKE ?")
        params.append(f"%,{tag},%")
    if category:
        where.append("COALESCE(NULLIF(t.category,''),'other') = ?")
        params.append(category)
    if account_id.isdigit():
        where.append("t.account_id = ?")
        params.append(int(account_id))
    if kind:
        where.append("t.kind = ?")
        params.append(kind)
    only, only_params = people.sql_in(people.scope(), "t.account_id")
    return q, category, account_id, kind, " AND ".join(where) + only, params + only_params, tag


@app.route("/transactions.csv")
@auth.login_required
def transactions_csv():
    """Every row the Transactions page would show under its filters —
    not just the first four hundred — as a CSV. See export.py."""
    _, _, _, _, clause, params, _ = _transactions_filter()
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id WHERE {clause} "
            f"ORDER BY t.txn_date DESC, t.id DESC", params).fetchall()]
    return export.response(export.transactions(rows, request.args.get("sep")),
                           f"transactions-{date.today().isoformat()}.csv")


@app.route("/accounts/<int:account_id>/transactions.csv")
@auth.login_required
def account_csv(account_id: int):
    account = _load_account(account_id)
    if account is None:
        return render_template("missing.html", what=_t("That account does not exist.")), 404
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT t.*, a.name AS account_name FROM transactions t JOIN accounts a ON a.id = t.account_id "
            "WHERE t.account_id = ? ORDER BY t.txn_date DESC, t.id DESC", (account_id,)).fetchall()]
    slug = "".join(ch if ch.isalnum() else "-" for ch in account["name"]).strip("-").lower() or "account"
    return export.response(export.transactions(rows, request.args.get("sep")),
                           f"{slug}-{date.today().isoformat()}.csv")


@app.route("/securities/<isin>.csv")
@auth.login_required
def security_csv(isin: str):
    only, params = people.sql_in(people.scope(), "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t JOIN accounts a ON a.id = t.account_id "
            f"WHERE t.isin = ?{only} ORDER BY t.txn_date DESC, t.id DESC", [isin.strip(), *params]).fetchall()]
    return export.response(export.transactions(rows, request.args.get("sep")),
                           f"{isin.strip()}-{date.today().isoformat()}.csv")


@app.route("/api/benchmark")
@auth.login_required
def api_benchmark():
    """The portfolio (or one security) against an index, both at 100
    on the first day: {points: [{date, portfolio, benchmark}], …}.
    `bench` is a known key or a Yahoo symbol; `period` all|ytd|1y|3y|5y;
    `isin` for one holding, in `ccy` if given. See benchmark.py."""
    base = settings.get("base_currency", "EUR")
    label, symbol = benchmark.resolve(request.args.get("bench") or "world")
    period = request.args.get("period") or "all"
    today = date.today()
    start = {"ytd": date(today.year, 1, 1), "1y": today - timedelta(days=365),
             "3y": today - timedelta(days=3 * 365), "5y": today - timedelta(days=5 * 365)}.get(period)
    isin = (request.args.get("isin") or "").strip()
    if isin:
        ccy = (request.args.get("ccy") or "").upper() or None
        values, flows, _, series = performance.security_series(isin, people.scope(), today, ccy)
        currency = series.get("currency") or base
        if start:
            values = [(d, v) for d, v in values if d >= start.isoformat()]
    else:
        values, flows, _, _ = performance.accounts_series(base, people.scope(), start, today)
        currency = base
    line = benchmark.indexed(values, flows)
    if not line:
        return jsonify({"points": [], "label": label, "symbol": symbol, "error": _t("Nothing to compare yet.")})
    try:
        bench = benchmark.closes(symbol, line[0][0], today=today)
    except Exception as exc:                        # noqa: BLE001
        return jsonify({"points": [], "label": label, "symbol": symbol, "error": str(exc)})
    out = benchmark.compare(line, bench, currency)
    if not out["points"]:
        out["error"] = _f("Yahoo has no history for {symbol} over this span.", symbol=symbol)
    return jsonify({**out, "label": label, "symbol": symbol, "currency": currency})


@app.route("/portfolio.csv")
@auth.login_required
def portfolio_csv():
    """The holdings table, one row per security, with the figures the
    page computes — price, value, unrealised and realised gain, TWR
    and MWR (in percent)."""
    return export.response(export.holdings(_holdings_with_figures()[0], request.args.get("sep")),
                           f"holdings-{date.today().isoformat()}.csv")


@app.route("/transactions/<int:txn_id>/tags", methods=["POST"])
@auth.login_required
def transaction_tags(txn_id: int):
    """Set one row's tags — words, comma-separated. No rule follows:
    a tag is a label on this row, where a category is a habit."""
    categories.set_tags(txn_id, request.form.get("tags"))
    back = request.form.get("back") or ""
    if back.startswith("/") and not back.startswith("//"):
        return redirect(back)
    return redirect(url_for("transactions"))


@app.route("/transactions/<int:txn_id>/category", methods=["POST"])
@auth.login_required
def transaction_category(txn_id: int):
    """Set one transaction's category, and remember it as a rule.

    The "remember" half is the whole design: a correction that does not
    become a rule means fixing the same merchant every month. The
    Categorize page shows the pattern in a field, so the user can change
    it or clear it to make a one-off correction; the Transactions page
    has only the dropdown, sends no `pattern` at all, and the pattern is
    worked out from the transaction — see categories.suggest_pattern().
    Filing something under Uncategorised is never a rule: a rule that
    un-categorises is only ever a mistake waiting for the next import.
    """
    category = request.form.get("category") or "other"
    if "pattern" in request.form:
        pattern = (request.form.get("pattern") or "").strip()
    else:
        with get_conn() as conn:
            row = conn.execute("SELECT description, counterparty FROM "
                               "transactions WHERE id = ?", (txn_id,)).fetchone()
        pattern = categories.suggest_pattern(
            row["description"], row["counterparty"]) if row else ""
    if category == "other":
        pattern = ""
    try:
        categories.set_category(txn_id, category)
        if pattern:
            applied = categories.add_rule(pattern, category)
            flash(_n(applied, "Rule saved — {n} transaction matched “{pattern}”.",
                     "Rule saved — {n} transactions matched “{pattern}”.",
                     pattern=pattern), "ok")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(request.form.get("back") or url_for("categorize"))


@app.route("/categorize", methods=["GET", "POST"])
@auth.login_required
def categorize():
    if request.method == "POST":
        if request.form.get("action") == "seed":
            changed = categories.seed_from_kind()
            flash(_n(changed,
                     "{n} transaction categorised from what the importer "
                     "already knew.",
                     "{n} transactions categorised from what the importer "
                     "already knew."), "ok")
        elif request.form.get("action") == "delete_rule":
            categories.delete_rule(int(request.form["rule_id"]))
            categories.apply_all()
            flash(_t("Rule deleted and the remaining rules re-applied."), "ok")
        elif request.form.get("action") in ("add_rule", "edit_rule"):
            f = request.form
            terms = {"field": f.get("field", "any"), "direction": f.get("direction", "any"),
                     "amount_min": f.get("amount_min"), "amount_max": f.get("amount_max"),
                     "match_mode": f.get("match_mode", "contains"), "account_id": f.get("account_id"),
                     "kind": f.get("kind"), "set_counterparty": f.get("set_counterparty"),
                     "set_kind": f.get("set_kind"), "add_tag": f.get("add_tag")}
            try:
                if f.get("action") == "add_rule":
                    n = categories.add_rule(f.get("pattern", ""), f.get("category", ""), **terms)
                    flash(_n(n, "Rule saved — {n} transaction matched “{pattern}”.",
                             "Rule saved — {n} transactions matched “{pattern}”.",
                             pattern=f.get("pattern", "").strip()), "ok")
                else:
                    categories.update_rule(int(f.get("rule_id") or 0), f.get("pattern", ""),
                                           f.get("category", ""), **terms)
                    flash(_t("Rule changed and every rule re-applied, oldest first."), "ok")
            except ValueError as exc:
                flash(str(exc), "error")
            return redirect(url_for("categorize") + "#rules")
        return redirect(url_for("categorize"))

    queue, remaining = categories.uncategorised(account_ids=people.scope())
    with get_conn() as conn:
        accounts_list = [dict(r) for r in conn.execute("SELECT id, name FROM accounts ORDER BY name")]
    from .importers.base import KINDS as _kinds
    return render_template("categorize.html", active_page="categorize",
                           queue=queue, remaining=remaining,
                           rules=categories.rules(), rule_fields=categories.FIELDS,
                           rule_directions=categories.DIRECTIONS, rule_modes=categories.MATCH_MODES,
                           rule_kinds=sorted(_kinds), accounts_list=accounts_list)


@app.route("/cashflow")
@auth.login_required
def cashflow_page():
    months = int(request.args.get("months") or 13)
    return render_template(
        "cashflow.html", active_page="cashflow",
        data=cashflow.monthly(months, settings.get("base_currency", "EUR"),
                              account_ids=people.scope()),
        months=months)


@app.route("/budget", methods=["GET", "POST"])
@auth.login_required
def budget_page():
    if request.method == "POST":
        for key, value in request.form.items():
            if not key.startswith("budget_"):
                continue
            category = key[len("budget_"):]
            try:
                amount = float(value.replace(",", ".")) if value.strip() else None
            except ValueError:
                amount = None
            cashflow.set_budget(category, amount)
        flash(_t("Budget saved."), "ok")
        return redirect(url_for("budget_page"))
    return render_template(
        "budget.html", active_page="budget",
        report=cashflow.budget_report(settings.get("base_currency", "EUR"),
                                      account_ids=people.scope()))


@app.route("/forecast", methods=["GET", "POST"])
@auth.login_required
def forecast_page():
    """Where the money is heading, from today's balance and the user's
    own assumptions. The inputs are kept, so the page answers the same
    question next month with next month's balance."""
    cfg = settings.load()
    # One plan per view: the household's, and each person's own. Anna's
    # "600 a month towards 500 000" must not become Ben's the moment he
    # flips the switch — his balance with her plan answers nobody.
    plans = _forecast_plans(cfg)
    key = _forecast_key()
    if request.method == "POST":
        if request.form.get("form") == "retirement":
            pid = request.form.get("person", "")
            if pid.isdigit():
                outlooks = dict(cfg.get("retirement") or {})
                outlooks[f"person:{pid}"] = forecast.clean_retirement(request.form)
                cfg["retirement"] = outlooks
                settings.save(cfg)
            return redirect(url_for("forecast_page") + "#retirement")
        plans[key] = forecast.clean(request.form)
        cfg["forecast"] = plans
        settings.save(cfg)
        return redirect(url_for("forecast_page"))
    inputs = forecast.clean(plans.get(key) or {})
    base = cfg.get("base_currency", "EUR")
    s = overview.summary(base, account_ids=people.scope())
    return render_template("forecast.html", active_page="forecast",
                           inputs=inputs, s=s,
                           plan=forecast.plan(s["net_worth"], inputs),
                           retirement=_retirement_blocks(cfg, base, plans),
                           max_years=forecast.MAX_YEARS, max_rate=forecast.MAX_RATE,
                           min_retire_age=forecast.MIN_RETIRE_AGE,
                           max_retire_age=forecast.MAX_RETIRE_AGE)


def _retirement_blocks(cfg: dict, base: str, plans: dict) -> dict:
    """One outlook per person in view — everybody under Everyone, one
    under a name — each from their own accounts and their own Forecast
    plan, with their own retirement settings on top.

    The monthly amount comes from the person's Forecast plan unless
    they typed one here: the two pages answer the same question from
    the same number until somebody says otherwise.
    """
    viewing = people.current()
    everyone = people.all_people()
    subjects = [viewing] if viewing else everyone
    stored = cfg.get("retirement") or {}
    blocks, without_birthday = [], []
    for person in subjects:
        if not person.get("birthday"):
            without_birthday.append(person["name"])
            continue
        own = overview.summary(base, account_ids=people.account_ids(person["id"]))
        plan_inputs = forecast.clean(plans.get(f"person:{person['id']}") or {})
        plan = forecast.plan(own["net_worth"], plan_inputs)
        settings_ = forecast.clean_retirement(stored.get(f"person:{person['id']}") or {})
        monthly = settings_["monthly"] if settings_["monthly"] is not None else plan["monthly"]
        age_now = people.age_on(person["birthday"])
        blocks.append({
            "person": person, "age_now": age_now, "settings": settings_,
            "from_plan": settings_["monthly"] is None, "plan_monthly": plan["monthly"],
            "net_worth": own["net_worth"], "accounts": own["account_count"],
            "outlook": forecast.retirement(own["net_worth"], monthly, settings_["rate"],
                                           age_now, settings_["retire_age"]),
        })
    return {"blocks": blocks, "without_birthday": without_birthday,
            "no_people": not everyone}


@app.route("/allocation", methods=["GET", "POST"])
@auth.login_required
def allocation_page():
    """Where the money is by what it is — asset class, region, the
    user's own buckets — against the targets, with a contribution
    spread so the drift shrinks. See allocation.py."""
    if request.method == "POST":
        f = request.form
        try:
            if f.get("form") == "classify":
                allocation.set_class(f.get("isin", "").strip(), f.get("asset_class"), f.get("region"), f.get("bucket"))
                flash(_t("Classification saved."), "ok")
            elif f.get("form") == "targets":
                dim = f.get("dimension", "")
                values = {k[len("target_"):]: v for k, v in f.items() if k.startswith("target_")}
                new_key = " ".join((f.get("new_key") or "").split())[:40]
                if new_key:
                    values[new_key] = f.get("new_pct")
                allocation.set_targets(dim, values)
                flash(_t("Targets saved."), "ok")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("allocation_page") + "#" + (f.get("dimension") or f.get("form") or ""))
    base = settings.get("base_currency", "EUR")
    s = overview.summary(base, account_ids=people.scope())
    contribution = max(0.0, forecast._num(request.args.get("contribution"), 0.0))
    data = allocation.breakdown(s, contribution)
    for dim, d in data["dimensions"].items():
        for r in d["rows"]:
            if r["key"] == "unassigned":
                r["label"] = _t("unassigned")
            elif dim == "asset_class":
                r["label"] = allocation.class_label(r["key"])
            elif dim == "region":
                r["label"] = allocation.region_label(r["key"]) if r["key"] in allocation.REGIONS else r["key"]
            else:
                r["label"] = r["key"]
    return render_template("allocation.html", active_page="allocation", s=s, data=data,
                           contribution=contribution, base_currency=base,
                           asset_classes=allocation.ASSET_CLASSES, regions=allocation.REGIONS,
                           dimensions=allocation.DIMENSIONS)


@app.route("/stages")
@auth.login_required
def stages_page():
    """Which of the three stages the securities are in: saving builds
    it, saving and returns pull together, compounding carries it. On
    the plan from the Forecast page, and as it actually went, year by
    year. See stages.py."""
    cfg = settings.load()
    base = cfg.get("base_currency", "EUR")
    plan = forecast.clean(_forecast_plans(cfg).get(_forecast_key()) or {})
    scope = people.scope()
    s = overview.summary(base, account_ids=scope)
    went = stages.as_it_went(base, scope)
    actual = stages.actual_monthly(went)
    # The plan's figures, unless the page is being played with: a
    # monthly amount or a rate in the address is tried, not kept.
    monthly = max(0.0, forecast._num(request.args.get("monthly"), plan["monthly"]))
    rate = min(forecast.MAX_RATE, max(-forecast.MAX_RATE, forecast._num(request.args.get("rate"), plan["rate"])))
    start = s["securities"] or 0.0
    return render_template("stages.html", active_page="stages", s=s, base_currency=base,
                           monthly=monthly, rate=rate, start=start,
                           projected=stages.path(start, monthly, rate), went=went, actual=actual,
                           lower=stages.LOWER, upper=stages.UPPER,
                           playing=("monthly" in request.args or "rate" in request.args))


def _forecast_key() -> str:
    person = people.current()
    return f"person:{person['id']}" if person else "all"


def _forecast_plans(cfg: dict) -> dict:
    """The stored plans, keyed by view. A settings file from 0.16.0 holds
    one flat plan; it becomes the household's rather than being lost."""
    stored = cfg.get("forecast") or {}
    if "mode" in stored:
        return {"all": stored}
    return dict(stored)


@app.route("/subscriptions")
@auth.login_required
def subscriptions_page():
    return render_template(
        "subscriptions.html", active_page="subscriptions",
        data=subscriptions.detect(settings.get("base_currency", "EUR"),
                                  account_ids=people.scope()))


@app.route("/portfolio")
@auth.login_required
def portfolio_page():
    holdings, s, perf, realised = _holdings_with_figures()
    return render_template("portfolio.html", active_page="portfolio", s=s, perf=perf,
                           realised=realised, benchmarks=benchmark.BENCHMARKS)


def _holdings_with_figures():
    """The holdings with every figure the Portfolio page shows on them
    — the page and its CSV export share this so they cannot disagree."""
    base = settings.get("base_currency", "EUR")
    scope = people.scope()
    s = overview.summary(base, account_ids=scope)
    # The returns: the securities as one investment, since the first
    # trade, this year and the last twelve months — and each holding's
    # own, in its table row.
    today = date.today()
    perf = {
        "all": performance.for_accounts(base, scope),
        "ytd": performance.for_accounts(base, scope, start=date(today.year, 1, 1)),
        "1y": performance.for_accounts(base, scope, start=today - timedelta(days=365)),
    }
    for h in s["holdings"]:
        h["perf"] = performance.for_security(h["isin"], scope)
        # The gain by lots: what the sales of this holding made, and
        # what the units still held cost — the basis the market price
        # is measured against — under the method chosen in Settings.
        r = gains.realised(h["isin"], scope)
        h["realised"] = r["total"] if r["sales"] else None
        h["open_cost"] = r["open_cost"]
        h["unrealised"] = (h["quantity"] * h["price"] - r["open_cost"]) \
            if h["price"] is not None and r["open_quantity"] > 1e-12 else None
    # Every security ever sold, held or not: a position closed last
    # year still made what it made.
    realised = gains.summary(scope)
    return s["holdings"], s, perf, realised


# ─── Share Ideas ─────────────────────────────────────────────────────
# Four boards over one nightly Yahoo cache, rendered by the page's own
# script from two JSON routes. The routes are read-only against Yahoo:
# fetching is minutes of requests and belongs to the background job in
# screener_jobs.py, and nothing here can place an order — the page ends
# at "here is a shortlist".

@app.route("/screener")
@auth.login_required
def screener_page():
    return render_template("screener.html", active_page="screener")


def _flag(name: str) -> bool:
    return request.args.get(name, "").lower() in ("1", "true", "yes")


@app.route("/api/screener")
@auth.login_required
def api_screener():
    """The share boards: ?profile=value (default) or income."""
    top = max(1, min(request.args.get("top", default=60, type=int), 500))
    sectors = [x for x in request.args.get("sector", "").split(",") if x]
    try:
        with get_conn() as conn:
            payload = screener.results(
                conn, top=top, pea_only=_flag("pea"), include_failed=_flag("failed"),
                sectors=sectors or None,
                min_score=request.args.get("min_score", type=float),
                profile=request.args.get("profile", "value").lower())
    except ValueError as exc:
        # An unknown profile is a typo in a query string, not a server
        # fault — 500 would make the page say "failed to load".
        return jsonify({"ok": False, "error": str(exc)}), 400
    payload["ok"] = True
    return jsonify(payload)


@app.route("/api/screener/etf")
@auth.login_required
def api_screener_etf():
    """The ETF boards: ?profile=growth (default) or dividend. Their own
    table, so their own route; the same rows under both profiles, so the
    two tabs cannot report a different TER for one fund."""
    top = max(1, min(request.args.get("top", default=60, type=int), 500))
    regions = [x for x in request.args.get("region", "").split(",") if x]
    try:
        with get_conn() as conn:
            payload = screener_etf.results(
                conn, top=top, pea_only=_flag("pea"), include_failed=_flag("failed"),
                regions=regions or None,
                min_score=request.args.get("min_score", type=float),
                profile=request.args.get("profile", "growth").lower())
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    payload["ok"] = True
    return jsonify(payload)


@app.route("/api/screener/watch/<path:symbol>", methods=["POST"])
@auth.login_required
def api_screener_watch(symbol: str):
    body = request.get_json(silent=True) or {}
    try:
        with get_conn() as conn:
            res = screener.set_watch(conn, symbol, body.get("status"), body.get("note"))
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    res["ok"] = True
    return jsonify(res)


def _category_form(form) -> None:
    """Add, edit or remove one category, and say what it did.

    Deleting is the one that needs a sentence rather than a tick: the
    transactions that carried the category do not disappear with it, they
    move to Uncategorised, and a user who is not told that will go
    looking for money that seems to have gone missing.
    """
    action = form.get("form")
    try:
        if action == "category_new":
            categories.add_category(form.get("label", ""),
                                    form.get("colour", ""),
                                    form.get("group", categories.SPENDING_GROUP))
            flash(_f("Category “{name}” added.", name=form.get("label").strip()), "ok")
        elif action == "category_edit":
            categories.update_category(form.get("slug", ""),
                                       form.get("label", ""),
                                       form.get("colour", ""),
                                       form.get("group",
                                                categories.SPENDING_GROUP))
            flash(_t("Category updated."), "ok")
        elif action == "category_delete":
            slug = form.get("slug", "")
            name = categories.label(slug)
            moved = categories.delete_category(slug)
            if moved:
                flash(_n(moved,
                         "“{name}” deleted — {n} transaction moved to "
                         "Uncategorised, and its rules were removed with it.",
                         "“{name}” deleted — {n} transactions moved to "
                         "Uncategorised, and its rules were removed with it.",
                         name=name), "ok")
            else:
                flash(_f("“{name}” deleted.", name=name), "ok")
    except ValueError as exc:
        flash(str(exc), "error")


def _person_form(form) -> None:
    """Add, rename or remove a person. Errors are flashed, not raised:
    a name clash is the user's to fix, not a crash."""
    action = form.get("form")
    try:
        if action == "person_add":
            people.add(form.get("name", ""))
            flash(_t("Added."), "ok")
        elif action == "person_rename":
            pid = int(form.get("id", "0"))
            people.rename(pid, form.get("name", ""))
            people.set_birthday(pid, form.get("birthday"))
            flash(_t("Saved."), "ok")
        elif action == "person_delete":
            pid = int(form.get("id", "0"))
            people.delete(pid)
            cfg = settings.load()
            plans = _forecast_plans(cfg)
            outlooks = dict(cfg.get("retirement") or {})
            gone = plans.pop(f"person:{pid}", None), outlooks.pop(f"person:{pid}", None)
            if any(g is not None for g in gone):
                cfg["forecast"], cfg["retirement"] = plans, outlooks
                settings.save(cfg)
            flash(_t("Removed. Their accounts stay; they just belong to "
                     "one person fewer."), "ok")
    except ValueError as exc:
        flash(_person_error(str(exc)), "error")


def _person_error(message: str) -> str:
    if message.startswith("There is already somebody called "):
        return _f("There is already somebody called {name}.",
                  name=message[len("There is already somebody called "):-1])
    if "birthday" in message:
        return _t("The birthday needs to be a date.")
    return _t("A person needs a name.")


def _valid_hhmm(value: str) -> bool:
    parts = value.split(":")
    return (len(parts) == 2 and all(p.isdigit() for p in parts)
            and 0 <= int(parts[0]) < 24 and 0 <= int(parts[1]) < 60)


def _connected_count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM bank_links "
                            "WHERE account_uid IS NOT NULL").fetchone()["n"]


def _people_with_counts() -> list[dict]:
    """Each person with how many accounts are theirs, for Settings."""
    with get_conn() as conn:
        counts = {r["person_id"]: r["n"] for r in conn.execute(
            "SELECT person_id, COUNT(*) AS n FROM account_people "
            "GROUP BY person_id").fetchall()}
    return [{**p, "accounts": counts.get(p["id"], 0)} for p in people.all_people()]


# The settings, in chapters: one page each, so that a setting is found
# by the chapter it belongs to and not by scrolling. Every card lives
# in exactly one; a POST that ends with an anchor is sent back to the
# chapter holding it — see _settings_url().
SETTINGS_SECTIONS = ("general", "banks", "market", "categories", "people", "assistants")
_SETTINGS_ANCHORS = {
    "general": "general",
    "sync": "banks", "saxo": "banks", "kraken": "banks", "mappings": "banks", "enablebanking": "banks",
    "rates": "market", "prices": "market", "ideas": "market",
    "categories": "categories", "people": "people", "mcp": "assistants",
}


def _settings_url(anchor: str | None = None, **args) -> str:
    section = _SETTINGS_ANCHORS.get(anchor or "", "general")
    url = url_for("settings_page", section=None if section == "general" else section, **args)
    return f"{url}#{anchor}" if anchor and anchor != section else url


@app.route("/settings", methods=["GET", "POST"])
@app.route("/settings/<section>", methods=["GET", "POST"])
@auth.login_required
def settings_page(section: str = "general"):
    if section not in SETTINGS_SECTIONS:
        return redirect(url_for("settings_page"))
    cfg = settings.load()
    error = None
    if request.method == "POST":
        if request.form.get("form") == "credentials":
            try:
                banksync.save_credentials(request.form.get("app_id", ""),
                                          request.form.get("private_key", ""))
                flash(_t("Credentials saved. Checking them with Enable Banking…"), "ok")
                # Straight into the check. "Saved" answers a question
                # nobody asked; "your key works and these redirect URLs
                # are registered" answers the real one, at the only
                # moment the user is looking.
                return redirect(_settings_url("enablebanking", check=1))
            except ValueError as exc:
                error = str(exc)
        elif request.form.get("form", "").startswith("category"):
            _category_form(request.form)
            return redirect(_settings_url("categories"))
        elif request.form.get("form", "").startswith("person"):
            _person_form(request.form)
            return redirect(_settings_url("people"))
        elif request.form.get("form") == "prices_refresh":
            info = prices.refresh(cfg.get("base_currency", "EUR"))
            if info["failed"]:
                flash(_f("{ok} of {held} holdings priced. Could not price: "
                         "{failed}.", ok=info["priced"], held=info["held"],
                         failed=", ".join(f["isin"] for f in info["failed"])),
                      "error")
            else:
                flash(_n(info["priced"], "{n} holding priced.",
                         "{n} holdings priced."), "ok")
            return redirect(_settings_url("prices"))
        elif request.form.get("form") == "price_symbol":
            try:
                prices.set_symbol(request.form.get("isin", ""),
                                  request.form.get("symbol"))
                info = prices.refresh(cfg.get("base_currency", "EUR"),
                                      isins=[request.form.get("isin", "")])
                if info["failed"]:
                    flash(info["failed"][0]["error"], "error")
                else:
                    flash(_t("Priced."), "ok")
            except ValueError as exc:
                flash(str(exc), "error")
            return redirect(_settings_url("prices"))
        elif request.form.get("form") == "ideas_refresh":
            # On a thread: it is minutes of Yahoo requests, and a form
            # post that hangs for minutes teaches people to press it
            # twice. The page says when it last ran.
            if screener_jobs.start_background(force=bool(request.form.get("force"))):
                flash(_t("Refreshing the share ideas in the background. It takes "
                         "a few minutes; the boards fill in as it goes."), "ok")
            else:
                flash(_t("A refresh is already running."), "error")
            return redirect(_settings_url("ideas"))
        elif request.form.get("form") == "saxo_credentials":
            try:
                saxo.save_credentials(request.form.get("app_key", ""),
                                      request.form.get("app_secret", ""),
                                      request.form.get("environment", "live"))
                flash(_t("Saxo credentials saved. Now connect an account from its page."), "ok")
            except ValueError as exc:
                flash(str(exc), "error")
            return redirect(_settings_url("saxo"))
        elif request.form.get("form") == "saxo_forget":
            saxo.forget()
            brokers.remove_links("saxo")
            flash(_t("Saxo forgotten. The accounts and their history stay."), "ok")
            return redirect(_settings_url("saxo"))
        elif request.form.get("form") == "kraken_credentials":
            try:
                kraken.save_credentials(request.form.get("api_key", ""),
                                        request.form.get("api_secret", ""))
                info = kraken.check()
                flash(_f("Kraken key works. Balances: {assets}. Now connect an account "
                         "from its page.", assets=", ".join(
                             f"{v:g} {k}" for k, v in sorted(info["assets"].items())) or "none"),
                      "ok")
            except (ValueError, kraken.KrakenError) as exc:
                flash(str(exc), "error")
            return redirect(_settings_url("kraken"))
        elif request.form.get("form") == "kraken_forget":
            kraken.forget_credentials()
            brokers.remove_links("kraken")
            flash(_t("Kraken key forgotten. The account and its history stay."), "ok")
            return redirect(_settings_url("kraken"))
        elif request.form.get("form") == "mcp_token":
            if request.form.get("action") == "revoke":
                mcp.revoke()
                flash(_t("Token revoked. Anything connected with it is cut off."), "ok")
            else:
                mcp.new_token()
                flash(_t("Token created. Any earlier token stopped working."), "ok")
            return redirect(_settings_url("mcp"))
        elif request.form.get("form") == "sync_all":
            results = banksync.sync_all() + brokers.sync_all()
            failed = [r for r in results if r["error"]]
            new_rows = sum(r["inserted"] for r in results)
            if failed:
                flash(_f("{ok} of {total} accounts synced. Failed: {names}.",
                         ok=len(results) - len(failed), total=len(results),
                         names=", ".join(r["account"] for r in failed)), "error")
            elif not results:
                flash(_t("No account is connected to a bank yet."), "error")
            else:
                flash(_n(new_rows, "{n} new transaction across {accounts} accounts.",
                         "{n} new transactions across {accounts} accounts.",
                         accounts=len(results)), "ok")
            return redirect(_settings_url("sync"))
        elif request.form.get("form") == "csv_mapping_delete":
            from .importers import generic
            try:
                generic.delete(int(request.form.get("mapping_id") or 0))
            except ValueError:
                pass
            flash(_t("Mapping forgotten. The next file with that header asks again."), "ok")
            return redirect(_settings_url("mappings"))
        elif request.form.get("form") == "fx_refresh":
            # In the request, because the user asked for it and is
            # waiting for the answer. The automatic one is on a thread.
            try:
                info = fx.refresh()
                flash(_n(info["currencies"],
                         "{n} exchange rate fetched, published {date}.",
                         "{n} exchange rates fetched, published {date}.",
                         date=_date(info["latest"])), "ok")
            except fx.FxError as exc:
                flash(str(exc), "error")
            return redirect(_settings_url("rates"))
        else:
            cfg["base_currency"] = (request.form.get("base_currency")
                                    or "EUR").upper()[:3]
            cfg["redirect_url"] = (request.form.get("redirect_url")
                                   or cfg["redirect_url"]).strip()
            # Anything that is not a language this app has is "follow the
            # browser", which is also what the blank option posts.
            chosen = (request.form.get("language") or "").strip()
            cfg["language"] = chosen if i18n.known(chosen) else ""
            cfg["auto_sync"] = bool(request.form.get("auto_sync"))
            how = (request.form.get("gains_method") or "fifo").strip()
            cfg["gains_method"] = how if how in gains.METHODS else "fifo"
            when = (request.form.get("sync_time") or "12:00").strip()
            cfg["sync_time"] = when if _valid_hhmm(when) else "12:00"
            settings.save(cfg)
            # The language decided at the top of this request is the old
            # one. Forget it, so the confirmation of the change is
            # already in the language it changed to.
            g.pop("_language", None)
            flash(_t("Settings saved."), "ok")
            return redirect(url_for("settings_page"))

    check = None
    if banksync.credentials_present() and request.args.get("check"):
        # Deliberately only on request. It is a live API call, and a
        # settings page that reaches the network on every render is a
        # settings page that hangs when the network does.
        try:
            check = {"ok": True, "application": banksync.client().application()}
        except Exception as exc:                    # noqa: BLE001
            check = {"ok": False, "error": str(exc)}

    section_labels = {"general": _t("General"), "banks": _t("Banks & brokers"), "market": _t("Prices & rates"),
                      "categories": _t("Categories"), "people": _t("People"), "assistants": _t("Assistants")}
    return render_template("settings.html", cfg=cfg, error=error, section=section,
                           sections=[(k, section_labels[k]) for k in SETTINGS_SECTIONS],
                           people_list=_people_with_counts(),
                           today=date.today().isoformat(),
                           configured=banksync.credentials_present(),
                           secrets_dir=str(settings.SECRETS_DIR),
                           secrets_inside_data=settings.SECRETS_INSIDE_DATA,
                           catalogue=categories.catalogue(),
                           groups=categories.GROUPS,
                           rates=fx.status(),
                           last_auto_sync=db_state.get_state("last_auto_sync"),
                           connected_links=_connected_count(),
                           securities=prices.status(),
                           prices_hours_ago=prices.fetched_hours_ago(),
                           ideas=screener_jobs.status(),
                           mcp_token=mcp.token(),
                           saxo_state=saxo.describe(),
                           kraken_state=kraken.describe(),
                           broker_links=brokers.links(),
                           mcp_url=request.host_url.rstrip("/") + "/mcp",
                           csv_mappings=importers.generic.all_mappings(),
                           check=check)


# ─── Connecting a bank ───────────────────────────────────────────────

@app.route("/connect/<int:account_id>")
@auth.login_required
def connect_pick(account_id: int):
    """Choose the bank. Defaults to Germany and shows DKB first, because
    that is the worked example in the README and a list of 2,000 banks
    with no starting point is not a choice."""
    country = (request.args.get("country") or "DE").upper()[:2]
    query = (request.args.get("q") or "").strip().lower()
    banks, error = [], None
    if not banksync.credentials_present():
        error = ("Enable Banking is not configured yet. Add your Application "
                 "ID and private key in Settings first.")
    else:
        try:
            banks = banksync.client().aspsps(country)
        except Exception as exc:                    # noqa: BLE001
            error = str(exc)
    if query:
        banks = [b for b in banks if query in (b.get("name") or "").lower()]
    # Sandbox banks first. They are the only way to walk this flow without
    # spending a real consent at a real bank, and a real consent is not a
    # thing to spend while finding out whether a redirect URL was
    # registered correctly. Enable Banking flags them; surfacing the flag
    # is the difference between a safe test and a broken connection
    # somewhere else.
    banks.sort(key=lambda b: (not b.get("sandbox"), (b.get("name") or "").lower()))
    return render_template("connect_pick.html", account_id=account_id,
                           banks=banks, country=country, q=request.args.get("q", ""),
                           sandboxes=sum(1 for b in banks if b.get("sandbox")),
                           error=error)


@app.route("/connect/<int:account_id>/start", methods=["POST"])
@auth.login_required
def connect_start(account_id: int):
    name = request.form.get("aspsp_name") or ""
    country = request.form.get("aspsp_country") or "DE"
    try:
        url = banksync.begin_connect(account_id, name, country)
    except Exception as exc:                        # noqa: BLE001
        flash(str(exc), "error")
        return redirect(url_for("connect_pick", account_id=account_id,
                                country=country))
    # Off to the bank. Everything needed to finish is in the database.
    return redirect(url)


def _finish_connection(code: str, state: str):
    """Shared by the automatic callback and the manual paste. One function,
    so the two paths cannot drift into behaving differently."""
    try:
        result = banksync.complete_connect(code, state)
    except Exception as exc:                        # noqa: BLE001
        flash(str(exc), "error")
        return None

    flash(_f("Connected: {accounts}",
              accounts=", ".join(result["linked"])), "ok")
    # Pull straight away. A connection that lands on an empty page gives
    # the user no evidence it worked, and "did it work?" is the only
    # question they have at this moment.
    outcome = banksync.sync_account(result["account_id"])
    if outcome and outcome.get("error"):
        flash(_f("Connected, but the first sync failed: {reason}",
                 reason=outcome["error"]), "error")
    elif outcome:
        flash(_n(outcome["inserted"], "Imported {n} transaction.",
                 "Imported {n} transactions."), "ok")
    return result


@app.route("/connect/callback")
@auth.login_required
def connect_callback():
    error = request.args.get("error")
    code = request.args.get("code")
    state = request.args.get("state")
    if error:
        flash(_f("The bank refused the authorisation: {reason}", reason=error),
              "error")
        return redirect(url_for("index"))
    if not code or not state:
        flash(_t("The bank sent us back without an authorisation code."), "error")
        return redirect(url_for("connect_paste"))
    result = _finish_connection(code, state)
    if result is None:
        return redirect(url_for("connect_paste"))
    return redirect(url_for("account_detail", account_id=result["account_id"]))


@app.route("/connect/paste", methods=["GET", "POST"])
@auth.login_required
def connect_paste():
    """Finish a connection by hand, when the callback cannot fire.

    This is not only a workaround for a rejected redirect URL. A provider
    that requires an https redirect cannot send anyone back to a NAS on
    a LAN address, and a self-hosted app has no business demanding a
    public hostname and a certificate before it will read a bank
    balance. So the supported answer is: let the bank bounce the user to
    a URL that goes nowhere, and paste the address bar in here.

    What gets pasted is the whole URL, because that is what a person can
    actually copy — asking someone to find `code=` inside a 300-character
    query string and stop at the `&` is asking for a support thread.
    """
    with get_conn() as conn:
        pending = [dict(r) for r in conn.execute(
            "SELECT s.*, a.name AS account_name FROM auth_states s "
            "LEFT JOIN accounts a ON a.id = s.account_id "
            "ORDER BY s.created_at DESC").fetchall()]

    if request.method == "POST":
        raw = (request.form.get("pasted") or "").strip()
        code, state = _parse_pasted_redirect(raw)
        if not state and len(pending) == 1:
            # Only one connection is in flight, so a bare code is
            # unambiguous. Refusing it would be pedantry.
            state = pending[0]["state"]
        if not code:
            flash(_t("No authorisation code in that. Paste the whole URL from "
                     "the address bar, including the ?code=… part."), "error")
        elif not state:
            flash(_t("That code could belong to any of several connections in "
                     "progress. Paste the full URL, which carries the state."),
                  "error")
        else:
            result = _finish_connection(code, state)
            if result is not None:
                return redirect(url_for("account_detail",
                                        account_id=result["account_id"]))
        return redirect(url_for("connect_paste"))

    return render_template("connect_paste.html", pending=pending)


def _parse_pasted_redirect(raw: str) -> tuple[str | None, str | None]:
    """Pull (code, state) out of whatever was pasted.

    Accepts a full redirect URL, a bare query string, or just the code.
    A URL the bank produced may well be http on a host that does not
    resolve — it is never fetched, only parsed, so that is fine.
    """
    if not raw:
        return None, None
    query = raw
    if "?" in raw:
        query = raw.split("?", 1)[1]
    if "#" in query:
        query = query.split("#", 1)[0]
    if "=" in query:
        params = dict(urllib.parse.parse_qsl(query))
        code = params.get("code")
        if code:
            return code.strip(), (params.get("state") or "").strip() or None
    # No key=value pairs at all: treat the whole thing as a bare code,
    # but only if it looks like one rather than like a sentence.
    token = raw.strip()
    if token and " " not in token and "/" not in token:
        return token, None
    return None, None


@app.errorhandler(404)
def _not_found(_e):
    return render_template("missing.html", what=_t("No such page.")), 404


def _start_rate_refresher() -> None:
    """Keep the ECB rates current, off the request path.

    Started from main() and nowhere else, which is the point: importing
    this module — as the test suite does, and as any script poking at
    the database does — must not reach the network. A dashboard that
    cannot be imported offline is a dashboard that cannot be tested
    offline.

    A daemon thread, so stopping the server stops it too rather than
    leaving something to time out. Failures are logged and forgotten:
    the rates are an improvement to the page, never a condition of it.
    """
    def loop() -> None:
        while True:
            try:
                if fx.is_stale():
                    info = fx.refresh()
                    print(f"  rates: {info['currencies']} currencies, "
                          f"published {info['latest']}", flush=True)
                if fx.needs_backfill():
                    info = fx.backfill()
                    print(f"  rates: history back to {info['oldest']}, "
                          f"{info['days']} days", flush=True)
            except fx.FxError as exc:
                print(f"  rates: {exc}", flush=True)
            except Exception as exc:                      # noqa: BLE001
                print(f"  rates: unexpected: {exc}", flush=True)
            # Half a day. The ECB publishes once, at about 16:00 CET,
            # and this way a server started in the morning still picks
            # up the afternoon's without a second thought.
            time.sleep(12 * 3600)

    threading.Thread(target=loop, name="fx-refresh", daemon=True).start()

    def price_loop() -> None:
        # Same shape, its own cadence: a market price is worth asking
        # for a few times a day, a reference rate once.
        while True:
            try:
                if prices.is_stale():
                    info = prices.refresh(settings.get("base_currency", "EUR"))
                    print(f"  prices: {info['priced']} of {info['held']} "
                          f"holdings priced", flush=True)
                    for f in info["failed"]:
                        print(f"  prices: {f['isin']}: {f['error']}", flush=True)
            except Exception as exc:                      # noqa: BLE001
                print(f"  prices: unexpected: {exc}", flush=True)
            time.sleep(prices.FRESH_HOURS * 3600)

    threading.Thread(target=price_loop, name="prices-refresh", daemon=True).start()

    def sync_loop() -> None:
        # Once a day, at the time under Settings. Checked every minute
        # rather than slept until, so a changed time takes effect
        # without a restart and a laptop lid closed over noon still
        # gets its sync when it opens.
        while True:
            try:
                cfg = settings.load()
                if ((banksync.credentials_present() or brokers.links() or loans.all_loans())
                        and banksync.sync_due(datetime.now(), cfg,
                                              db_state.get_state("last_auto_sync"))):
                    db_state.set_state("last_auto_sync",
                                       datetime.now().isoformat(timespec="seconds"))
                    loans.write_all_balances()
                    results = banksync.sync_all() + brokers.sync_all()
                    for r in results:
                        if r["error"]:
                            print(f"  sync: {r['account']}: {r['error']}", flush=True)
                        else:
                            print(f"  sync: {r['account']}: {r['inserted']} new",
                                  flush=True)
                    if not results:
                        print("  sync: nothing connected", flush=True)
            except Exception as exc:                      # noqa: BLE001
                print(f"  sync: unexpected: {exc}", flush=True)
            time.sleep(60)

    threading.Thread(target=sync_loop, name="bank-sync", daemon=True).start()

    # The share-ideas cache: an hourly tick that refetches whatever is
    # older than a day, so the boards are current without a cron.
    threading.Thread(target=screener_jobs.loop, name="ideas-refresh",
                     daemon=True).start()

    def saxo_loop() -> None:
        # Saxo's refresh token is single-use and dies in an hour, so the
        # chain is renewed every five minutes while the app runs. When
        # nothing is connected, a tick costs a file read.
        while True:
            try:
                info = saxo.keepalive()
                if info["status"] == "error":
                    print(f"  saxo: {info['message']}", flush=True)
            except Exception as exc:                      # noqa: BLE001
                print(f"  saxo: unexpected: {exc}", flush=True)
            time.sleep(saxo.KEEPALIVE_S)

    threading.Thread(target=saxo_loop, name="saxo-keepalive", daemon=True).start()


def main() -> None:
    try:
        init_db()
    except RuntimeError as exc:
        print(f"Cannot start: {exc}", flush=True)
        raise SystemExit(1)
    host = os.environ.get("WD_HOST", "127.0.0.1")
    port = int(os.environ.get("WD_PORT", "8000"))
    # flush, because this is the output of a server people run under
    # nohup, systemd or docker. Python buffers stdout when it is not a
    # terminal, so without this the log stays empty until the buffer
    # fills and a perfectly healthy start looks like a hang.
    print(f"Wealth Dashboard — http://{host}:{port}", flush=True)
    print(f"  data:    {settings.DATA_DIR}", flush=True)
    print(f"  secrets: {settings.SECRETS_DIR}", flush=True)
    if not has_users():
        print("  first run: open the URL above to create your account",
              flush=True)
    _start_rate_refresher()
    # waitress where it is installed — which is everywhere the app is
    # run from the image. Flask's own server says on every start that it
    # is not for production use and is right: this one is reachable from
    # a LAN, and on a NAS it may well be the thing a reverse proxy
    # points at.
    #
    # Threads either way: one slow bank call must not freeze every other
    # page.
    try:
        from waitress import serve
    except ImportError:
        app.run(host=host, port=port, threaded=True)
    else:
        serve(app, host=host, port=port, threads=8,
              ident="wealth-dashboard")


if __name__ == "__main__":
    main()
