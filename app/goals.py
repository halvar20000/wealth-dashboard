"""Savings goals: an amount, by a date, and how it is going.

A goal is fed one of two ways. By an account — the holiday account,
the one the deposit for the flat goes into — whose balance *is* the
progress, nothing to type. Or by hand, an amount at a time, for a
goal that lives inside a bigger account. Either way the page says
how far along it is, how much a month reaches it by the date, and
whether that is more than the Forecast's monthly amount.
"""

from __future__ import annotations

from datetime import date

from . import i18n
from .db import get_conn


# What a goal is for. Mostly a word on the card — a house, a car — and
# a hint for the form; retirement is its own plan, see retirement.py.
KINDS = ("saving", "house", "car", "education", "wedding", "emergency", "travel")


def clean(form) -> dict:
    from .importers.base import parse_decimal
    name = " ".join((form.get("name") or "").split())[:80]
    target = parse_decimal(form.get("target"))
    if not name or not target or target <= 0:
        raise ValueError(i18n.t("A goal needs a name and a positive amount."))
    when = (form.get("target_date") or "").strip() or None
    if when:
        try:
            when = date.fromisoformat(when).isoformat()
        except ValueError:
            raise ValueError(i18n.t("The date needs to be a real day, written year-month-day.")) from None
    acc = form.get("account_id")
    return {"name": name, "target": target, "currency": (form.get("currency") or "EUR").upper()[:3],
            "target_date": when, "account_id": int(acc) if acc and str(acc).isdigit() else None,
            "notes": " ".join((form.get("notes") or "").split())[:300] or None,
            "kind": form.get("kind") if form.get("kind") in KINDS else "saving"}


def add(form) -> int:
    g = clean(form)
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO goals (name, target, currency, target_date, account_id, notes, kind) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (g["name"], g["target"], g["currency"], g["target_date"], g["account_id"], g["notes"], g["kind"]))
        return int(cur.lastrowid)


def update(goal_id: int, form) -> None:
    g = clean(form)
    with get_conn() as conn:
        cur = conn.execute("UPDATE goals SET name = ?, target = ?, currency = ?, target_date = ?, account_id = ?, notes = ?, kind = ? WHERE id = ?",
                           (g["name"], g["target"], g["currency"], g["target_date"], g["account_id"], g["notes"], g["kind"], goal_id))
        if not cur.rowcount:
            raise ValueError(i18n.t("That goal does not exist."))


def delete(goal_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))


def add_saved(goal_id: int, amount) -> float:
    """Money put towards a goal by hand; negative takes it out."""
    from .importers.base import parse_decimal
    value = parse_decimal(str(amount)) if amount not in (None, "") else None
    if value is None:
        raise ValueError(i18n.t("The amount is missing."))
    with get_conn() as conn:
        conn.execute("UPDATE goals SET saved = MAX(0, saved + ?) WHERE id = ?", (value, goal_id))
        row = conn.execute("SELECT saved FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return row["saved"] if row else 0.0


def all_goals(today: date | None = None) -> list[dict]:
    today = today or date.today()
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT g.*, a.name AS account_name FROM goals g LEFT JOIN accounts a ON a.id = g.account_id ORDER BY g.target_date, g.name").fetchall()]
        for g in rows:
            if g["account_id"]:
                bal = conn.execute("SELECT amount FROM balances WHERE account_id = ? ORDER BY as_of DESC, id DESC LIMIT 1",
                                   (g["account_id"],)).fetchone()
                g["progress"] = max(0.0, bal["amount"]) if bal else 0.0
                g["fed_by"] = "account"
            else:
                g["progress"] = g["saved"] or 0.0
                g["fed_by"] = "hand"
            g["pct"] = min(100.0, g["progress"] / g["target"] * 100) if g["target"] else 0.0
            g["remaining"] = max(0.0, g["target"] - g["progress"])
            g["done"] = g["progress"] >= g["target"]
            g["months_left"] = None
            g["monthly_needed"] = None
            if g["target_date"]:
                td = date.fromisoformat(g["target_date"])
                months = (td.year - today.year) * 12 + (td.month - today.month) - (1 if td.day < today.day else 0)
                g["overdue"] = td < today and not g["done"]
                # A date still ahead but under a month away is one month's
                # saving, not a division by nothing.
                g["months_left"] = max(1, months) if td >= today else 0
                if g["months_left"] > 0 and not g["done"]:
                    g["monthly_needed"] = g["remaining"] / g["months_left"]
    return rows
