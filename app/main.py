"""Wealth Dashboard — the web app.

Run it:  python -m app          (or `flask --app app.main run`)

The route list is the whole product so far, in order of first use:

    /setup              create the first user — only until one exists
    /login /logout
    /                   accounts and their balances
    /accounts/new       create an account by hand
    /accounts/<id>      one account: balance, transactions, connection
    /settings           Enable Banking credentials and the redirect URL
    /connect/<id>       choose a bank
    /connect/<id>/start begin authorisation — leaves for the bank
    /connect/callback   the bank sends the user back here
    /connect/paste      finish by hand when the callback cannot fire
    /accounts/<id>/sync   pull balance and transactions
    /accounts/<id>/import upload a broker CSV

Every page except /setup and /login requires a signed-in user.
"""

from __future__ import annotations

import os
import secrets
import urllib.parse
from pathlib import Path

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)

from . import auth, settings
from .banks import enablebanking as eb
from .banks import sync as banksync
from . import importers, overview
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
    if request.endpoint in ("static", "setup", "healthz"):
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


def _money(amount, currency=None) -> str:
    """One place that formats money, so two pages cannot disagree about
    what a thousand euros looks like."""
    if amount is None:
        return "—"
    currency = (currency or settings.get("base_currency", "EUR")).upper()
    sign = "-" if amount < 0 else ""
    whole = f"{abs(amount):,.2f}".replace(",", "\u00a0")
    return f"{sign}{whole}\u00a0{currency}"


def _qty(value) -> str:
    """Share counts. Fractional shares are normal now, and trailing
    zeroes on a whole number are noise."""
    if value is None:
        return "—"
    text = f"{value:,.4f}".rstrip("0").rstrip(".")
    return (text or "0").replace(",", "\u00a0")


@app.context_processor
def _globals():
    return {"user": auth.current_user(),
            "base_currency": settings.get("base_currency", "EUR"),
            "money": _money, "qty": _qty,
            "asset_version": _ASSET_VERSION}


@app.route("/healthz")
def healthz():
    return {"ok": True, "configured": has_users()}


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
            error = "Too many attempts. Wait a few minutes."
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
            error = "Wrong username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─── Accounts ────────────────────────────────────────────────────────

@app.route("/")
@auth.login_required
def index():
    return render_template(
        "overview.html", active_page="overview",
        s=overview.summary(settings.get("base_currency", "EUR")))


@app.route("/accounts")
@auth.login_required
def accounts():
    return render_template(
        "accounts.html", active_page="accounts",
        s=overview.summary(settings.get("base_currency", "EUR")))


@app.route("/accounts/new", methods=["GET", "POST"])
@auth.login_required
def account_new():
    error = None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            error = "The account needs a name."
        else:
            with get_conn() as conn:
                cur = conn.execute(
                    "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                    (name, request.form.get("type") or "bank",
                     (request.form.get("currency") or "EUR").upper()[:3]))
                new_id = int(cur.lastrowid)
            return redirect(url_for("account_detail", account_id=new_id))
    return render_template("account_new.html", error=error,
                           base_currency=settings.get("base_currency", "EUR"))


@app.route("/accounts/<int:account_id>")
@auth.login_required
def account_detail(account_id: int):
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what="That account does not exist."), 404
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
                           positions=importers.positions(account_id),
                           balance=dict(balance) if balance else None,
                           transactions=[dict(t) for t in txns],
                           total_transactions=total,
                           configured=banksync.credentials_present())


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@auth.login_required
def account_edit(account_id: int):
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what="That account does not exist."), 404
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

    error = None
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            error = "The account needs a name."
        else:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE accounts SET name = ?, type = ?, currency = ? "
                    "WHERE id = ?",
                    (name, request.form.get("type") or "bank",
                     (request.form.get("currency") or "EUR").upper()[:3],
                     account_id))
            flash("Account updated.", "ok")
            return redirect(url_for("account_detail", account_id=account_id))

    return render_template("account_edit.html", account=dict(account),
                           counts=counts, error=error, active_page="accounts")


@app.route("/accounts/<int:account_id>/delete", methods=["POST"])
@auth.login_required
def account_delete(account_id: int):
    """Delete an account and everything hanging off it.

    Confirmed by typing the name, not by an "are you sure" dialog. The
    dialog is clicked through without reading; typing the name cannot be
    done by accident, and it is the difference between removing the
    duplicate account you created by mistake and removing the one with
    six years of history in it.
    """
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
        if account is None:
            return render_template("missing.html",
                                   what="That account does not exist."), 404
        if (request.form.get("confirm") or "").strip() != account["name"]:
            flash("Type the account name exactly to confirm the deletion.",
                  "error")
            return redirect(url_for("account_edit", account_id=account_id))
        # ON DELETE CASCADE takes the transactions, balances and links.
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    flash(f"Deleted {account['name']}.", "ok")
    return redirect(url_for("accounts"))


@app.route("/accounts/<int:account_id>/import", methods=["GET", "POST"])
@auth.login_required
def account_import(account_id: int):
    """Upload a broker CSV.

    The file is recognised rather than declared. Asking someone to pick
    the right parser from a list, for a file that says which broker it
    came from on every line, is asking them to get it wrong — and the
    wrong parser does not fail, it produces a confident mess.
    """
    with get_conn() as conn:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?",
                               (account_id,)).fetchone()
    if account is None:
        return render_template("missing.html",
                               what="That account does not exist."), 404

    report = None
    if request.method == "POST":
        upload = request.files.get("file")
        if not upload or not upload.filename:
            flash("Choose a CSV file first.", "error")
            return redirect(url_for("account_import", account_id=account_id))

        content = upload.read(MAX_IMPORT_BYTES + 1)
        if len(content) > MAX_IMPORT_BYTES:
            flash(f"That file is larger than "
                  f"{MAX_IMPORT_BYTES // (1024 * 1024)} MB. A transaction "
                  f"export should be far smaller — is it the right file?",
                  "error")
            return redirect(url_for("account_import", account_id=account_id))

        module = importers.sniff(content)
        if module is None:
            flash("That file's columns do not match any importer here. "
                  "Supported: " + ", ".join(m.LABEL for m in importers.IMPORTERS),
                  "error")
            return redirect(url_for("account_import", account_id=account_id))

        parsed = module.parse(content, account_currency=account["currency"])
        if not parsed.rows and parsed.problems:
            flash(parsed.problems[0], "error")
            return redirect(url_for("account_import", account_id=account_id))

        report = importers.store(account_id, parsed, module.SLUG)
        report["label"] = module.LABEL
        flash(f"{module.LABEL}: {report['inserted']} new, "
              f"{report['duplicates']} already had.", "ok")

    return render_template("import.html", account=dict(account), report=report,
                           importers=importers.IMPORTERS)


@app.route("/accounts/<int:account_id>/sync", methods=["POST"])
@auth.login_required
def account_sync(account_id: int):
    with get_conn() as conn:
        link = conn.execute("SELECT id FROM bank_links WHERE account_id = ? LIMIT 1",
                            (account_id,)).fetchone()
    if link is None:
        flash("That account is not connected to a bank.", "error")
    else:
        result = banksync.sync_link(int(link["id"]))
        if result["error"]:
            flash(f"Sync failed: {result['error']}", "error")
        else:
            flash(f"Imported {result['inserted']} new transaction(s).", "ok")
    return redirect(url_for("account_detail", account_id=account_id))


# ─── Settings ────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@auth.login_required
def settings_page():
    cfg = settings.load()
    error = None
    if request.method == "POST":
        if request.form.get("form") == "credentials":
            try:
                banksync.save_credentials(request.form.get("app_id", ""),
                                          request.form.get("private_key", ""))
                flash("Credentials saved. Checking them with Enable Banking…", "ok")
                # Straight into the check. "Saved" answers a question
                # nobody asked; "your key works and these redirect URLs
                # are registered" answers the real one, at the only
                # moment the user is looking.
                return redirect(url_for("settings_page", check=1))
            except ValueError as exc:
                error = str(exc)
        else:
            cfg["base_currency"] = (request.form.get("base_currency")
                                    or "EUR").upper()[:3]
            cfg["redirect_url"] = (request.form.get("redirect_url")
                                   or cfg["redirect_url"]).strip()
            settings.save(cfg)
            flash("Settings saved.", "ok")
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

    return render_template("settings.html", cfg=cfg, error=error,
                           configured=banksync.credentials_present(),
                           secrets_dir=str(settings.SECRETS_DIR),
                           secrets_inside_data=settings.SECRETS_INSIDE_DATA,
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

    flash("Connected: " + ", ".join(result["linked"]), "ok")
    # Pull straight away. A connection that lands on an empty page gives
    # the user no evidence it worked, and "did it work?" is the only
    # question they have at this moment.
    outcome = banksync.sync_account(result["account_id"])
    if outcome and outcome.get("error"):
        flash(f"Connected, but the first sync failed: {outcome['error']}", "error")
    elif outcome:
        flash(f"Imported {outcome['inserted']} transaction(s).", "ok")
    return result


@app.route("/connect/callback")
@auth.login_required
def connect_callback():
    error = request.args.get("error")
    code = request.args.get("code")
    state = request.args.get("state")
    if error:
        flash(f"The bank refused the authorisation: {error}", "error")
        return redirect(url_for("index"))
    if not code or not state:
        flash("The bank sent us back without an authorisation code.", "error")
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
            flash("No authorisation code in that. Paste the whole URL from "
                  "the address bar, including the ?code=… part.", "error")
        elif not state:
            flash("That code could belong to any of several connections in "
                  "progress. Paste the full URL, which carries the state.",
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
    return render_template("missing.html", what="No such page."), 404


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
    # threaded: one slow bank call must not freeze every other page.
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
