"""Users, passwords and the request gate.

A username as well as a password, even though the app is single-user to
begin with. It costs one column now; retrofitting identity onto an app
whose sessions only ever meant "someone typed the password" means
rewriting every place that assumed one user.

Storage is PBKDF2-HMAC-SHA256 with a per-user salt. Not because an
attacker is expected to read the database file — if they can, they have
your finances anyway — but because people reuse passwords, and a
recoverable one here becomes someone else's problem elsewhere.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for

from .db import get_conn

ROUNDS = 240_000
MIN_PASSWORD_LEN = 8

# Failed attempts per IP. Rate limiting, not lockout: a lockout lets
# anyone on the network deny the owner access to their own dashboard by
# guessing wrongly on purpose.
_FAILURES: dict[str, list[float]] = {}
_WINDOW_S = 300
_MAX_FAILURES = 5


def hash_password(password: str, salt: str, rounds: int = ROUNDS) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), rounds).hex()


def create_user(username: str, password: str) -> int:
    username = (username or "").strip()
    if not username:
        raise ValueError("A username is required.")
    if len(password or "") < MIN_PASSWORD_LEN:
        raise ValueError(
            f"The password must be at least {MIN_PASSWORD_LEN} characters.")
    salt = secrets.token_bytes(16).hex()
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, salt, rounds) "
                "VALUES (?, ?, ?, ?)",
                (username, hash_password(password, salt), salt, ROUNDS))
        except sqlite3.IntegrityError:
            raise ValueError(f"The username {username!r} is already taken.")
        return int(cur.lastrowid)


def verify(username: str, password: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", ((username or "").strip(),)
        ).fetchone()
    if row is None:
        # Hash anyway. Returning early on an unknown username makes the
        # response measurably faster than for a known one, which turns
        # the login form into a way to enumerate usernames.
        hash_password(password or "", secrets.token_bytes(16).hex())
        return None
    expected = hash_password(password or "", row["salt"], row["rounds"])
    if not hmac.compare_digest(expected, row["password_hash"]):
        return None
    return {"id": row["id"], "username": row["username"]}


def throttled(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _FAILURES.get(ip, []) if now - t < _WINDOW_S]
    _FAILURES[ip] = hits
    return len(hits) >= _MAX_FAILURES


def record_failure(ip: str) -> None:
    _FAILURES.setdefault(ip, []).append(time.time())


def current_user() -> dict | None:
    uid = session.get("uid")
    if not uid:
        return None
    if getattr(g, "_user", None) and g._user["id"] == uid:
        return g._user
    with get_conn() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE id = ?",
                           (uid,)).fetchone()
    g._user = dict(row) if row else None
    if g._user is None:
        session.clear()          # the user was deleted under a live session
    return g._user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            if request.path.startswith("/api/"):
                # A fetch() handed a redirect to an HTML login form parses
                # the page as JSON and reports a nonsense error, sending
                # the reader after a data bug that does not exist.
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def safe_next(raw: str | None) -> str:
    """Where to send someone after they sign in.

    Checking for a leading "/" is not enough: `//evil.example` starts
    with one and a browser resolves a protocol-relative URL to an
    off-site host. A login form that forwards you off-site is how a
    phishing link borrows a domain you trust.
    """
    if not raw or not raw.startswith("/") or raw.startswith("//"):
        return "/"
    if "\\" in raw or "://" in raw:
        return "/"
    return raw
