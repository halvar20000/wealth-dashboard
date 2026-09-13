"""Bills: what is expected to leave the account, and whether it did.

A subscription is found; a bill is declared. The rent, the insurance,
the electricity, the phone — a name, a text that identifies the
payment in the rows, an amount if it is fixed, a rhythm, and the day
of the month it is usually taken. From those and the rows as they
arrive the page says, for each bill: paid this period on such a day,
due in so many days, or missed — the one thing a list of recurring
payments is for, and the one thing detection alone cannot say,
because it can only see what happened.

A bill matches a row when the text is in the counterparty or the
description, the money went out, and — if an amount is given — the
row is within a fifth of it; utilities vary. The period is the
rhythm's; the due date is the last payment plus the period, snapped
to the due day when there is one, and "missed" is a due date more
than seven days gone with no payment since.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from . import i18n
from .db import get_conn

RHYTHMS = {"weekly": 7, "monthly": 30, "quarterly": 91, "half-yearly": 182, "yearly": 365}
GRACE_DAYS = 7
TOLERANCE = 0.2


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


def next_after(last: date, rhythm: str, due_day: int | None) -> date:
    """The due date after `last`: a period on, snapped to the due day."""
    months = {"monthly": 1, "quarterly": 3, "half-yearly": 6, "yearly": 12}.get(rhythm)
    if months:
        nxt = _add_months(last, months)
        if due_day:
            nxt = date(nxt.year, nxt.month, min(due_day, monthrange(nxt.year, nxt.month)[1]))
            if nxt <= last:
                nxt = _add_months(nxt, months)
        return nxt
    return last + timedelta(days=RHYTHMS.get(rhythm, 30))


def clean(form) -> dict:
    from .importers.base import parse_decimal
    name = " ".join((form.get("name") or "").split())[:80]
    pattern = " ".join((form.get("pattern") or "").split())[:80]
    if not name or len(pattern) < 3:
        raise ValueError(i18n.t("A bill needs a name and at least three characters of text to recognise it by."))
    amount = parse_decimal(form.get("amount")) if (form.get("amount") or "").strip() else None
    rhythm = form.get("rhythm") if form.get("rhythm") in RHYTHMS else "monthly"
    due_raw = (form.get("due_day") or "").strip()
    due_day = int(due_raw) if due_raw.isdigit() and 1 <= int(due_raw) <= 31 else None
    acc = form.get("account_id")
    account_id = int(acc) if acc and str(acc).isdigit() else None
    return {"name": name, "pattern": pattern, "amount": abs(amount) if amount else None,
            "currency": (form.get("currency") or "EUR").upper()[:3], "rhythm": rhythm,
            "due_day": due_day, "account_id": account_id,
            "notes": " ".join((form.get("notes") or "").split())[:300] or None,
            "active": 0 if form.get("active") in ("0", "off", "no") else 1}


def add(form) -> int:
    b = clean(form)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO bills (name, pattern, amount, currency, rhythm, due_day, account_id, active, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (b["name"], b["pattern"], b["amount"], b["currency"], b["rhythm"], b["due_day"],
             b["account_id"], b["active"], b["notes"]))
        return int(cur.lastrowid)


def update(bill_id: int, form) -> None:
    b = clean(form)
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE bills SET name = ?, pattern = ?, amount = ?, currency = ?, rhythm = ?, due_day = ?, "
            "account_id = ?, active = ?, notes = ? WHERE id = ?",
            (b["name"], b["pattern"], b["amount"], b["currency"], b["rhythm"], b["due_day"],
             b["account_id"], b["active"], b["notes"], bill_id))
        if not cur.rowcount:
            raise ValueError(i18n.t("That bill does not exist."))


def delete(bill_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM bills WHERE id = ?", (bill_id,))


def payments(bill: dict, conn, account_ids: list[int] | None = None, limit: int = 24) -> list[dict]:
    """The rows this bill matched, newest first."""
    from . import people
    only, params = people.sql_in(account_ids, "t.account_id")
    like = f"%{bill['pattern'].lower()}%"
    sql = (f"SELECT t.id, t.txn_date, t.amount, t.currency, t.description, t.counterparty FROM transactions t "
           f"WHERE (LOWER(t.description) LIKE ? OR LOWER(COALESCE(t.counterparty,'')) LIKE ?) AND t.amount < 0 "
           f"AND t.kind NOT IN ('buy', 'sell'){only}")
    args: list = [like, like, *params]
    if bill.get("account_id"):
        sql += " AND t.account_id = ?"
        args.append(bill["account_id"])
    if bill.get("amount"):
        sql += " AND ABS(t.amount) BETWEEN ? AND ?"
        args += [bill["amount"] * (1 - TOLERANCE), bill["amount"] * (1 + TOLERANCE)]
    sql += " ORDER BY t.txn_date DESC, t.id DESC LIMIT ?"
    args.append(limit)
    return [dict(r) for r in conn.execute(sql, args)]


def status(bill: dict, paid: list[dict], today: date | None = None) -> dict:
    """paid | due | missed | never, with the dates that say why."""
    today = today or date.today()
    if not paid:
        return {"state": "never", "last": None, "next": None, "days": None}
    last = date.fromisoformat(paid[0]["txn_date"])
    nxt = next_after(last, bill["rhythm"], bill.get("due_day"))
    days = (nxt - today).days
    if days < -GRACE_DAYS:
        state = "missed"
    elif days <= GRACE_DAYS:
        state = "due"
    else:
        state = "paid"
    return {"state": state, "last": last.isoformat(), "last_amount": abs(paid[0]["amount"]),
            "next": nxt.isoformat(), "days": days}


def all_bills(account_ids: list[int] | None = None, today: date | None = None) -> dict:
    today = today or date.today()
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT b.*, a.name AS account_name FROM bills b LEFT JOIN accounts a ON a.id = b.account_id "
            "ORDER BY b.active DESC, b.name").fetchall()]
        for b in rows:
            paid = payments(b, conn, account_ids)
            b["payments"] = paid[:6]
            b["paid_count"] = len(paid)
            b.update(status(b, paid, today))
            typical = b["amount"] or (abs(paid[0]["amount"]) if paid else 0.0)
            per_month = {"weekly": 52 / 12, "monthly": 1.0, "quarterly": 1 / 3, "half-yearly": 1 / 6, "yearly": 1 / 12}
            b["monthly"] = typical * per_month.get(b["rhythm"], 1.0) if typical else 0.0
    active = [b for b in rows if b["active"]]
    per_ccy: dict[str, float] = {}
    for b in active:
        per_ccy[b["currency"]] = per_ccy.get(b["currency"], 0.0) + b["monthly"]
    upcoming = sorted([b for b in active if b["next"] and b["state"] in ("due", "paid") and b["days"] is not None and b["days"] <= 30],
                      key=lambda b: b["days"])
    return {"bills": rows, "active": active, "monthly": per_ccy,
            "missed": [b for b in active if b["state"] == "missed"],
            "due": [b for b in active if b["state"] == "due"],
            "upcoming": upcoming}
