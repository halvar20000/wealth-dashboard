"""The people in the household, and whose accounts are whose.

A household's money is not one pile. One account is hers, one is his,
the joint one is both of theirs, and the child's savings are nobody's
in particular yet. Everybody wants to see their own picture, and the
household wants to see the whole.

So an account can belong to any number of people, and the header
carries a switch: *Everyone*, or one person. The choice lives in the
session, and every page that adds accounts up asks `scope()` which
accounts to count. `None` means all of them; a list means only those —
and an empty list means none, which is what a person with no accounts
yet should see, rather than everything.

An account assigned to nobody shows up under *Everyone* only. That is
deliberate: the alternative — showing it to everyone — quietly puts the
child's savings into both parents' net worth.

A person is a lens, not a permission. Everyone who can log in can flip
the switch. Keeping a spouse out of an account is a different feature,
and pretending this one does it would be worse than not having it.
"""

from __future__ import annotations

from datetime import date

from flask import g, session

from .db import get_conn

SESSION_KEY = "person"


def all_people() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM people ORDER BY name COLLATE NOCASE").fetchall()]


def add(name: str) -> int:
    name = " ".join((name or "").split())[:60]
    if not name:
        raise ValueError("A person needs a name.")
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM people WHERE name = ?", (name,)).fetchone():
            raise ValueError(f"There is already somebody called {name}.")
        return int(conn.execute("INSERT INTO people (name) VALUES (?)",
                                (name,)).lastrowid)


def rename(person_id: int, name: str) -> None:
    name = " ".join((name or "").split())[:60]
    if not name:
        raise ValueError("A person needs a name.")
    with get_conn() as conn:
        clash = conn.execute("SELECT id FROM people WHERE name = ? AND id != ?",
                             (name, person_id)).fetchone()
        if clash:
            raise ValueError(f"There is already somebody called {name}.")
        conn.execute("UPDATE people SET name = ? WHERE id = ?", (name, person_id))


def set_birthday(person_id: int, birthday: str | None) -> None:
    """ISO date or nothing. A birthday in the future is a typo, not a
    person, and is refused."""
    value = (birthday or "").strip() or None
    if value:
        try:
            when = date.fromisoformat(value)
        except ValueError:
            raise ValueError("The birthday needs to be a date.")
        if when > date.today():
            raise ValueError("The birthday needs to be a date.")
        value = when.isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE people SET birthday = ? WHERE id = ?", (value, person_id))


def age_on(birthday: str | None, today: date | None = None) -> float | None:
    """Age in years, with the fraction — 47.3, not 47 — because a plan
    that retires "at 65" is off by up to a year otherwise."""
    if not birthday:
        return None
    try:
        born = date.fromisoformat(birthday)
    except ValueError:
        return None
    today = today or date.today()
    return round((today - born).days / 365.2425, 2)


def delete(person_id: int) -> None:
    """The person goes; their accounts stay, now assigned to one fewer."""
    with get_conn() as conn:
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
    if session.get(SESSION_KEY) == person_id:
        session.pop(SESSION_KEY, None)


def for_account(account_id: int, conn=None) -> list[dict]:
    def run(c):
        return [dict(r) for r in c.execute(
            "SELECT p.* FROM people p JOIN account_people ap ON ap.person_id = p.id "
            " WHERE ap.account_id = ? ORDER BY p.name COLLATE NOCASE",
            (account_id,)).fetchall()]
    if conn is not None:
        return run(conn)
    with get_conn() as c:
        return run(c)


def by_account(conn=None) -> dict[int, list[str]]:
    """account id -> the names it belongs to, for a list page."""
    def run(c):
        out: dict[int, list[str]] = {}
        for r in c.execute(
                "SELECT ap.account_id, p.name FROM account_people ap "
                "JOIN people p ON p.id = ap.person_id "
                "ORDER BY p.name COLLATE NOCASE"):
            out.setdefault(r["account_id"], []).append(r["name"])
        return out
    if conn is not None:
        return run(conn)
    with get_conn() as c:
        return run(c)


def set_for_account(account_id: int, person_ids) -> None:
    ids = {int(p) for p in person_ids if str(p).isdigit()}
    with get_conn() as conn:
        conn.execute("DELETE FROM account_people WHERE account_id = ?", (account_id,))
        conn.executemany(
            "INSERT OR IGNORE INTO account_people (account_id, person_id) "
            "SELECT ?, id FROM people WHERE id = ?",
            [(account_id, pid) for pid in ids])


def account_ids(person_id: int) -> list[int]:
    with get_conn() as conn:
        return [r["account_id"] for r in conn.execute(
            "SELECT account_id FROM account_people WHERE person_id = ? "
            "ORDER BY account_id", (person_id,)).fetchall()]


# ─── The view in the header ──────────────────────────────────────────

def choose(person_id: int | None) -> None:
    """What the switch does. None is Everyone."""
    if person_id is None:
        session.pop(SESSION_KEY, None)
    else:
        session[SESSION_KEY] = int(person_id)


def current() -> dict | None:
    """The person the header is set to, or None for Everyone.

    Resolved once per request. A person who was deleted while somebody
    else's browser still remembered them resolves to Everyone rather
    than to an empty page with no way back.
    """
    if hasattr(g, "_person"):
        return g._person
    person = None
    pid = session.get(SESSION_KEY)
    if pid is not None:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM people WHERE id = ?", (pid,)).fetchone()
        person = dict(row) if row else None
        if person is None:
            session.pop(SESSION_KEY, None)
    g._person = person
    return person


def scope() -> list[int] | None:
    """Which accounts the pages should add up: None for all of them,
    else exactly this person's — possibly none at all."""
    person = current()
    return None if person is None else account_ids(person["id"])


def sql_in(ids: list[int] | None, column: str = "account_id") -> tuple[str, list]:
    """An `AND …` clause that narrows a query to `ids`, or nothing.

    `[]` gives `AND 0`: a person with no accounts sees no rows. Building
    `IN ()` instead is a syntax error in SQLite, and skipping the clause
    would show them everybody's money.
    """
    if ids is None:
        return "", []
    if not ids:
        return " AND 0", []
    return f" AND {column} IN ({','.join('?' * len(ids))})", list(ids)
