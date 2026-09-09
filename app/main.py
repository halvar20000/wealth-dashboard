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
    /accounts/<id>/sync pull balance and transactions

Every page except /setup and /login requires a signed-in user.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)

from . import auth, settings
from .banks import enablebanking as eb
from .banks import sync as banksync
from .db import get_conn, has_users, init_db

APP_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder=str(APP_DIR / "templates"),
            static_folder=str(APP_DIR / "static"))
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


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


@app.context_processor
def _globals():
    return {"user": auth.current_user(),
            "base_currency": settings.get("base_currency", "EUR")}


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
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT a.*,
                   (SELECT amount FROM balances b WHERE b.account_id = a.id
                     ORDER BY b.as_of DESC, b.id DESC LIMIT 1) AS balance,
                   (SELECT as_of  FROM balances b WHERE b.account_id = a.id
                     ORDER BY b.as_of DESC, b.id DESC LIMIT 1) AS balance_as_of,
                   (SELECT COUNT(*) FROM transactions t WHERE t.account_id = a.id) AS txn_count,
                   (SELECT aspsp_name FROM bank_links bl WHERE bl.account_id = a.id LIMIT 1) AS bank
              FROM accounts a ORDER BY a.name
        """).fetchall()
    return render_template("index.html", accounts=[dict(r) for r in rows])


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
                           balance=dict(balance) if balance else None,
                           transactions=[dict(t) for t in txns],
                           total_transactions=total,
                           configured=banksync.credentials_present())


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
                flash("Enable Banking credentials saved.", "ok")
                return redirect(url_for("settings_page"))
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
    banks.sort(key=lambda b: (b.get("name") or "").lower())
    return render_template("connect_pick.html", account_id=account_id,
                           banks=banks, country=country, q=request.args.get("q", ""),
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
        return redirect(url_for("index"))
    try:
        result = banksync.complete_connect(code, state)
    except Exception as exc:                        # noqa: BLE001
        flash(str(exc), "error")
        return redirect(url_for("index"))

    flash("Connected: " + ", ".join(result["linked"]), "ok")
    # Pull straight away. A connection that lands on an empty page gives
    # the user no evidence it worked, and "did it work?" is the only
    # question they have at this moment.
    outcome = banksync.sync_account(result["account_id"])
    if outcome and outcome.get("error"):
        flash(f"Connected, but the first sync failed: {outcome['error']}", "error")
    elif outcome:
        flash(f"Imported {outcome['inserted']} transaction(s).", "ok")
    return redirect(url_for("account_detail", account_id=result["account_id"]))


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
