"""What the bank said the balance was, and whether the bookings agree.

An account's worth is the **last balance the bank reported**, not the
sum of its rows: a sync fetches ninety days of bookings but the balance
of today, and a statement from 2019 does not know what has happened
since. That is right, and it has one consequence worth being able to
see — when a balance jumps and no booking explains the jump, the net
worth moves for a reason nobody can point at.

Usually the reason is innocent: a bank credits the balance when the
money arrives and itemises the booking a day later. Sometimes it is
not: a reading typed with a digit too many, a sync that answered for
the wrong account. Either way the question is the same — *which
account moved, when, and do its rows add up to the move* — and until
now nothing in the app could answer it.

So: every reading of an account, newest first, each with the step from
the reading before it, what the bookings in between add up to, and the
difference between the two.
"""

from __future__ import annotations

from . import people
from .db import get_conn


def readings(account_id: int, limit: int = 30) -> list[dict]:
    """One account's balance readings, newest first."""
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT id, amount, currency, as_of, balance_type FROM balances "
            "WHERE account_id = ? ORDER BY as_of DESC, id DESC LIMIT ?",
            (account_id, max(1, min(int(limit or 30), 500))))]
        booked = {}
        for a, b in zip(rows, rows[1:]):
            # The rows between the two readings. A reading is of the end
            # of its day, so the day itself counts.
            n = conn.execute(
                "SELECT TOTAL(amount) AS t, COUNT(*) AS n FROM transactions "
                "WHERE account_id = ? AND txn_date > ? AND txn_date <= ?",
                (account_id, b["as_of"][:10], a["as_of"][:10])).fetchone()
            booked[a["id"]] = (n["t"] or 0.0, n["n"] or 0)
    out = []
    for i, r in enumerate(rows):
        before = rows[i + 1] if i + 1 < len(rows) else None
        step = round(r["amount"] - before["amount"], 2) if before else None
        total, count = booked.get(r["id"], (None, 0))
        out.append({
            "as_of": r["as_of"], "amount": round(r["amount"], 2), "currency": r["currency"],
            "previous": before["as_of"] if before else None,
            "step": step, "booked": None if before is None else round(total, 2),
            "rows": count,
            "unexplained": None if (before is None or total is None) else round(step - total, 2),
        })
    return out


def steps(account_ids: list[int] | None = None) -> list[dict]:
    """The newest reading of every account that has two, with what the
    bookings in between say — biggest unexplained step first. One call
    to answer "which account moved, and why can nobody see it"."""
    only, params = people.sql_in(account_ids, "id")
    with get_conn() as conn:
        accounts = [dict(r) for r in conn.execute(
            f"SELECT id, name, currency, type FROM accounts WHERE 1=1{only}", params)]
    out = []
    for a in accounts:
        last = readings(a["id"], 2)
        if len(last) < 2:
            continue
        newest = last[0]
        if newest["step"] is None:
            continue
        out.append({"account_id": a["id"], "account": a["name"], "type": a["type"],
                    "currency": newest["currency"] or a["currency"], **newest})
    out.sort(key=lambda r: -abs(r["unexplained"] or 0))
    return out
