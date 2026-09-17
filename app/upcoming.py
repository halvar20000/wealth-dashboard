"""Upcoming: the cash balance, carried forward through what is known
to be coming.

Every other page looks back. This one starts from today's balance on
the cash accounts and lays out, day by day, what is expected to leave
and to arrive — the bills as declared on the Bills page, the
subscriptions the app has detected and nobody declared, the salary as
the newest payslip had it — and says where that leaves the balance:
the lowest it gets, and the day it would go below zero, if it would.

The rules, borrowed from people who have thought about bills longer:
income lands before bills on the same day, because that is what a
paycheck is for; a balance that starts below zero — an overdraft, a
card — is not "going negative", so the alert only fires when the line
is crossed; a bill without a fixed amount is carried at what it last
cost and marked as an estimate. A missed bill is expected today: the
money is still owed.

What is NOT here: loan instalments, unless declared as a bill on the
Bills page. A loan is owed from some cash account, and this app does
not know which — a bill says.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from . import bills, fx, people, subscriptions
from .db import get_conn
from .overview import GROUPS, _latest_balances

CASH_TYPES = next(types for key, _, types in GROUPS if key == "cash")
HORIZONS = (30, 60, 90)
# A payslip older than this is not a salary that is still arriving.
STALE_MONTHS = 3


def _month_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def _monthly_from(anchor: date, after: date, until: date) -> list[date]:
    """Every same-day-of-month date after `after` up to `until`, the
    day of the month kept from the anchor (31 → 28 in February, back
    to 31 in March — computed from the anchor each time, not stepped)."""
    out, n = [], 0
    while True:
        y, m = anchor.year + (anchor.month - 1 + n) // 12, (anchor.month - 1 + n) % 12 + 1
        d = _month_day(y, m, anchor.day)
        if d > until:
            return out
        if d > after:
            out.append(d)
        n += 1


def _bill_dates(bill: dict, today: date, until: date) -> list[date]:
    """The bill's due dates from today through the horizon: the next
    one the Bills page worked out, then a period on each time. A next
    date already past — the bill was missed — is expected today."""
    if not bill.get("next"):
        return []
    nxt = date.fromisoformat(bill["next"])
    out = []
    if nxt < today:
        out.append(today)
        nxt = bills.next_after(nxt, bill["rhythm"], bill.get("due_day"))
        while nxt <= today:
            nxt = bills.next_after(nxt, bill["rhythm"], bill.get("due_day"))
    while nxt <= until:
        out.append(nxt)
        nxt = bills.next_after(nxt, bill["rhythm"], bill.get("due_day"))
    return out


def _covered_by_bill(name: str, key: str, declared: list[dict]) -> bool:
    """A detected subscription the user has already declared as a bill
    — the bill's text is in the subscription's name or fingerprint."""
    hay = f"{name} {key}".lower()
    return any(b["pattern"].lower() in hay for b in declared)


def project(base_currency: str = "EUR", days: int = 30, account_ids: list[int] | None = None,
            today: date | None = None) -> dict:
    today = today or date.today()
    days = days if days in HORIZONS else HORIZONS[0]
    until = today + timedelta(days=days)
    only, params = people.sql_in(account_ids, "id")
    only_slip, params_slip = people.sql_in(account_ids, "account_id")

    with get_conn() as conn:
        accounts = [dict(r) for r in conn.execute(
            f"SELECT id, name, type, currency FROM accounts WHERE type IN ({','.join('?' * len(CASH_TYPES))}){only} "
            f"ORDER BY name", (*CASH_TYPES, *params)).fetchall()]
        latest = _latest_balances(conn)
        slips = [dict(r) for r in conn.execute(
            f"SELECT employer, employee, period, paid_on, currency, net_paid, account_id FROM payslips "
            f"WHERE 1=1{only_slip} ORDER BY period", params_slip).fetchall()]

    def to_base(amount: float, ccy: str) -> tuple[float, bool]:
        if ccy.upper() == base_currency.upper():
            return amount, True
        v, _ = fx.convert(amount, ccy, base_currency)
        return (v, True) if v is not None else (0.0, False)

    # Where it starts: every cash account's newest reading, in base.
    starting, unpriced = 0.0, []
    for a in accounts:
        b = latest.get(a["id"])
        a["balance"] = b["amount"] if b else 0.0
        a["as_of"] = b["as_of"] if b else None
        v, ok = to_base(a["balance"], b["currency"] if b else a["currency"])
        a["balance_base"] = v
        if not ok:
            unpriced.append(a["currency"])
        starting += v
    account_names = {a["id"]: a["name"] for a in accounts}

    items: list[dict] = []

    # Bills, as declared.
    data = bills.all_bills(account_ids, today)
    declared = data["active"]
    for b in declared:
        # A bill on an account outside this person's share is theirs, not this view's.
        if account_ids is not None and b.get("account_id") and b["account_id"] not in account_ids:
            continue
        amount = b["amount"] or b.get("last_amount")
        if not amount:
            continue
        v, ok = to_base(float(amount), b["currency"])
        if not ok:
            unpriced.append(b["currency"])
            continue
        for d in _bill_dates(b, today, until):
            items.append({"date": d.isoformat(), "kind": "bill", "name": b["name"], "amount": -round(v, 2),
                          "account": account_names.get(b.get("account_id")), "estimate": not b["amount"],
                          "overdue": b["state"] == "missed" and d == today, "href": "bills"})

    # Subscriptions the app found and nobody declared.
    found = subscriptions.detect(base_currency, account_ids=account_ids)
    for s in found["active"]:
        if not s["rhythm"] or _covered_by_bill(s["name"], s["key"], declared):
            continue
        period = next((p for n, p, _ in subscriptions._RHYTHMS if n == s["rhythm"]), None)
        if not period:
            continue
        nxt = date.fromisoformat(s["last_seen"]) + timedelta(days=round(period))
        while nxt < today:
            nxt += timedelta(days=round(period))
        while nxt <= until:
            items.append({"date": nxt.isoformat(), "kind": "subscription", "name": s["name"],
                          "amount": -round(s["amount"], 2), "account": s["account"], "estimate": True,
                          "overdue": False, "href": "subscriptions"})
            nxt += timedelta(days=round(period))

    # Salary: the newest payslip per employer and earner, monthly on the
    # day it was paid, as long as it is recent enough to still be a job.
    newest: dict[tuple[str, str], dict] = {}
    for s in slips:
        newest[(s["employer"], s["employee"])] = s
    stale_before = _month_day(today.year + (today.month - 1 - STALE_MONTHS) // 12,
                              (today.month - 1 - STALE_MONTHS) % 12 + 1, 1)
    for (employer, employee), s in newest.items():
        if s["period"] < stale_before.strftime("%Y-%m") or not s["net_paid"]:
            continue
        v, ok = to_base(float(s["net_paid"]), s["currency"])
        if not ok:
            unpriced.append(s["currency"])
            continue
        y, m = int(s["period"][:4]), int(s["period"][5:7])
        anchor = date.fromisoformat(s["paid_on"]) if s.get("paid_on") else _month_day(y, m, 25)
        for d in _monthly_from(anchor, today, until):
            items.append({"date": d.isoformat(), "kind": "income", "name": f"{employee} · {employer}",
                          "amount": round(v, 2), "account": account_names.get(s.get("account_id")),
                          "estimate": False, "overdue": False, "href": "income"})

    # The day's order: money in before money out, then by name.
    items.sort(key=lambda i: (i["date"], i["amount"] < 0, i["name"].lower()))
    running = starting
    for i in items:
        running = round(running + i["amount"], 2)
        i["running"] = running

    lowest = min(items, key=lambda i: i["running"]) if items else None
    below_zero = next((i for i in items if i["running"] < 0), None) if starting >= 0 else None
    return {
        "today": today.isoformat(), "until": until.isoformat(), "days": days, "horizons": HORIZONS,
        "accounts": accounts, "starting": round(starting, 2), "ending": round(running, 2),
        "total_in": round(sum(i["amount"] for i in items if i["amount"] > 0), 2),
        "total_out": round(-sum(i["amount"] for i in items if i["amount"] < 0), 2),
        "entries": items, "lowest": lowest, "below_zero": below_zero,
        "counts": {k: sum(1 for i in items if i["kind"] == k) for k in ("bill", "subscription", "income")},
        "unpriced": sorted(set(unpriced)), "base_currency": base_currency,
        # One point per entry for the chart, the start in front.
        "series": [{"date": today.isoformat(), "balance": round(starting, 2)}]
                  + [{"date": i["date"], "balance": i["running"]} for i in items],
    }
