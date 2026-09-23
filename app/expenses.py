"""Who spent what — the household's spending split between its people.

A row of spending belongs to one person, or to the household (shared,
halved between the two), or to nobody yet. The page sums a month, or
the last so many months, per person: what each spent directly, their
half of what was shared, and the total; what is still unassigned sits
in a bucket of its own, because a split that quietly absorbs it is
not a split. Per month for the chart, per category for the table.

Spending is what cashflow.py calls spending: money out, in a category
of the spending group; transfers and investments are not spending,
and income is not. Foreign amounts convert at the month's rate the
way the Cash Flow page converts them.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import cashflow, categories, people
from .db import get_conn


def month_bounds(month: str) -> tuple[date, date, date]:
    """(first day, last day counted — today when the month is the
    current one — and the month's real last day)."""
    y, m = int(month[:4]), int(month[5:7])
    first = date(y, m, 1)
    last = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) - timedelta(days=1)
    return first, min(last, date.today()), last


def available_months(account_ids: list[int] | None = None) -> list[str]:
    only, params = people.sql_in(account_ids)
    with get_conn() as conn:
        return [r["m"] for r in conn.execute(
            f"SELECT DISTINCT substr(txn_date, 1, 7) AS m FROM transactions "
            f"WHERE amount < 0{only} ORDER BY m DESC", params)]


def _rows(since: date | None, until: date | None, account_ids: list[int] | None, base: str) -> list[dict]:
    """Every spending row in the window, converted to the base currency:
    {month, category, owner, amount}. An owner is a person's id, "shared"
    or None."""
    spending = set(categories.spending())
    only, params = people.sql_in(account_ids)
    where, args = ["amount < 0", "kind NOT IN ('buy', 'sell', 'transfer')"], []
    if since:
        where.append("txn_date >= ?"); args.append(since.isoformat())
    if until:
        where.append("txn_date <= ?"); args.append(until.isoformat())
    rate_cache: dict[str, tuple] = {}
    out = []
    with get_conn() as conn:
        for r in conn.execute(
                f"SELECT txn_date, amount, currency, category, owner_id, owner_shared FROM transactions "
                f"WHERE {' AND '.join(where)}{only}", [*args, *params]):
            cat = r["category"] or "other"
            if cat not in spending:
                continue
            month = r["txn_date"][:7]
            amount = -r["amount"]
            ccy = (r["currency"] or base).upper()
            if ccy != base:
                if month not in rate_cache:
                    rate_cache[month] = cashflow._month_rates(month)
                _, rates = rate_cache[month]
                if ccy not in rates or base not in rates:
                    continue
                amount = amount / rates[ccy] * rates[base]
            owner = "shared" if r["owner_shared"] else (str(r["owner_id"]) if r["owner_id"] else None)
            out.append({"month": month, "category": cat, "owner": owner, "amount": amount})
    return out


def _totals(buckets: dict, persons: list[dict]) -> dict:
    """Per person: direct, their share of what was shared, the total —
    the shared half is split evenly among the people there are."""
    shared = buckets.get("shared", 0.0)
    n = len(persons) or 1
    out = {"people": [], "shared": round(shared, 2), "unassigned": round(buckets.get(None, 0.0), 2)}
    for p in persons:
        direct = buckets.get(str(p["id"]), 0.0)
        out["people"].append({"id": p["id"], "name": p["name"], "direct": round(direct, 2),
                              "share": round(shared / n, 2), "total": round(direct + shared / n, 2)})
    assigned = sum(v for k, v in buckets.items() if k is not None)
    out["assigned"] = round(assigned, 2)
    out["total"] = round(assigned + buckets.get(None, 0.0), 2)
    return out


def unowned(limit: int = 60, base: str = "EUR", account_ids: list[int] | None = None) -> tuple[list[dict], int]:
    """The spending nobody has claimed, biggest first — the other queue,
    beside the uncategorised one. Only spending: income and transfers
    belong to nobody in particular."""
    spending = set(categories.spending())
    only, params = people.sql_in(account_ids, "t.account_id")
    if not spending:
        return [], 0
    marks = ",".join("?" * len(spending))
    where = (f"t.amount < 0 AND t.kind NOT IN ('buy', 'sell', 'transfer') "
             f"AND t.owner_id IS NULL AND t.owner_shared = 0 "
             f"AND COALESCE(NULLIF(t.category, ''), 'other') IN ({marks}){only}")
    args = [*spending, *params]
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.id, t.account_id, a.name AS account_name, t.txn_date, t.description, "
            f"       t.counterparty, t.amount, t.currency, t.kind, t.category "
            f"  FROM transactions t JOIN accounts a ON a.id = t.account_id "
            f" WHERE {where} ORDER BY ABS(t.amount) DESC LIMIT ?", (*args, max(1, min(limit, 500))))]
        total = conn.execute(f"SELECT COUNT(*) FROM transactions t WHERE {where}", args).fetchone()[0]
    for r in rows:
        r["label"] = categories.label(r["category"])
    return rows, total


def split(base: str = "EUR", account_ids: list[int] | None = None,
          month: str | None = None, months: int | None = None) -> dict:
    """The split over one calendar month (`month`, YYYY-MM) or the last
    `months` full months; everything when neither is given. The chart
    always gets the twelve months ending with the window."""
    persons = people.all_people()
    since = until = None
    partial = False
    if month:
        since, until, real_last = month_bounds(month)
        partial = until < real_last
    elif months:
        first = date.today().replace(day=1)
        until = first - timedelta(days=1)
        since = first
        for _ in range(int(months)):
            since = (since - timedelta(days=1)).replace(day=1)
    rows = _rows(since, until, account_ids, base)
    buckets: dict = {}
    by_cat: dict[str, dict] = {}
    for r in rows:
        buckets[r["owner"]] = buckets.get(r["owner"], 0.0) + r["amount"]
        c = by_cat.setdefault(r["category"], {})
        c[r["owner"]] = c.get(r["owner"], 0.0) + r["amount"]
    # The chart: twelve months ending with the window's last month.
    end = until or date.today()
    chart_since = end.replace(day=1)
    for _ in range(11):
        chart_since = (chart_since - timedelta(days=1)).replace(day=1)
    by_month: dict[str, dict] = {}
    for r in _rows(chart_since, end, account_ids, base):
        m = by_month.setdefault(r["month"], {})
        m[r["owner"]] = m.get(r["owner"], 0.0) + r["amount"]
    previous = None
    if month:
        prev = (since - timedelta(days=1)).strftime("%Y-%m")
        previous = {"month": prev, "totals": _totals(by_month.get(prev, {}), persons)}
    return {
        "period": {"since": since.isoformat() if since else None, "until": until.isoformat() if until else None,
                   "month": month, "months": months, "partial": partial},
        "people": persons,
        "totals": _totals(buckets, persons),
        "counts": {"unassigned": sum(1 for r in rows if r["owner"] is None), "rows": len(rows)},
        "by_month": [{"month": m, **_totals(by_month[m], persons)} for m in sorted(by_month)],
        "by_category": sorted(
            ({"category": c, "label": categories.label(c), "colour": categories.colour(c), **_totals(v, persons)}
             for c, v in by_cat.items()), key=lambda x: -x["total"]),
        "previous": previous,
        "available_months": available_months(account_ids),
        "base_currency": base,
    }
