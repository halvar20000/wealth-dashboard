"""Money in, money out, by month and by category.

The rule that makes the numbers mean something: **only `category` is
counted, never `kind` and never the account.** A row categorised
`transfer` is money moving inside the household's own accounts, and
counting it would inflate both income and spending by the same amount
— twice for a transfer between two accounts the app can both see, since
each side has its own row.

Investment is separated from spending for the same reason. Money moved
into a broker has not been spent; it has been moved. A month where you
invested three thousand euros is not a month you overspent.
"""

from __future__ import annotations

from datetime import date

from . import categories
from .db import get_conn

SPENDING = set(categories.SPENDING)


def _month_floor(months_back: int) -> str:
    today = date.today()
    year, month = today.year, today.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}-01"


def monthly(months: int = 13, base_currency: str = "EUR") -> dict:
    """Income, spending and investment per calendar month.

    Only the base currency is summed — see overview.py for why a total
    that mixes currencies is worse than two totals.
    """
    since = _month_floor(months - 1)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT substr(txn_date, 1, 7) AS month,
                   COALESCE(NULLIF(category, ''), 'other') AS category,
                   SUM(amount) AS total,
                   COUNT(*)    AS n
              FROM transactions
             WHERE txn_date >= ? AND currency = ?
               AND kind NOT IN ('buy', 'sell')
             GROUP BY month, category
             ORDER BY month
            """, (since, base_currency)).fetchall()

    months_map: dict[str, dict] = {}
    by_category: dict[str, float] = {}
    for r in rows:
        m = months_map.setdefault(r["month"], {
            "month": r["month"], "income": 0.0, "spending": 0.0,
            "investment": 0.0, "categories": {}})
        cat, total = r["category"], r["total"] or 0.0
        if cat == "transfer":
            continue                      # internal: not a flow at all
        if cat == "income":
            m["income"] += total
        elif cat == "investment":
            m["investment"] += abs(total)
        elif cat in SPENDING:
            # Spending is stored as a negative amount; report it as a
            # positive size, because "you spent -1,200" reads as income
            # to everyone who is not a bookkeeper.
            spent = -total if total < 0 else 0.0
            m["spending"] += spent
            m["categories"][cat] = m["categories"].get(cat, 0.0) + spent
            by_category[cat] = by_category.get(cat, 0.0) + spent

    series = [months_map[k] for k in sorted(months_map)]
    for m in series:
        m["net"] = m["income"] - m["spending"]

    n = len(series) or 1
    return {
        "months": series,
        "by_category": sorted(
            ({"category": c, "label": categories.label(c),
              "colour": categories.colour(c), "total": v, "per_month": v / n}
             for c, v in by_category.items()),
            key=lambda x: -x["total"]),
        "total_income": sum(m["income"] for m in series),
        "total_spending": sum(m["spending"] for m in series),
        "total_investment": sum(m["investment"] for m in series),
        "average_spending": sum(m["spending"] for m in series) / n,
        "average_income": sum(m["income"] for m in series) / n,
        "months_covered": len(series),
        "base_currency": base_currency,
    }


def budgets() -> dict[str, float]:
    with get_conn() as conn:
        return {r["category"]: r["monthly"] for r in
                conn.execute("SELECT * FROM budgets").fetchall()}


def set_budget(category: str, monthly_amount: float | None) -> None:
    with get_conn() as conn:
        if monthly_amount is None or monthly_amount <= 0:
            conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
        else:
            conn.execute(
                "INSERT INTO budgets (category, monthly) VALUES (?, ?) "
                "ON CONFLICT(category) DO UPDATE SET monthly = excluded.monthly",
                (category, monthly_amount))


def budget_report(base_currency: str = "EUR") -> dict:
    """This month against the budget, with a typical month for context.

    The comparison people actually want is not "am I over" — halfway
    through a month everyone is under. It is "am I over *for how far
    through the month I am*", so the expected-to-date figure is what the
    bar is measured against.
    """
    today = date.today()
    this_month = today.strftime("%Y-%m")
    limits = budgets()
    data = monthly(months=13, base_currency=base_currency)

    current = next((m for m in data["months"] if m["month"] == this_month), None)
    spent_now = (current or {}).get("categories", {})

    # Average per category over the completed months only. Including the
    # month in progress drags every average down by however much of it
    # has not happened yet.
    completed = [m for m in data["months"] if m["month"] != this_month]
    typical: dict[str, float] = {}
    for m in completed:
        for cat, amount in m["categories"].items():
            typical[cat] = typical.get(cat, 0.0) + amount
    if completed:
        typical = {c: v / len(completed) for c, v in typical.items()}

    import calendar
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    through = today.day / days_in_month

    rows = []
    for cat in sorted(set(limits) | set(spent_now) | set(typical),
                      key=lambda c: -(limits.get(c) or typical.get(c, 0))):
        limit = limits.get(cat)
        spent = spent_now.get(cat, 0.0)
        expected = (limit * through) if limit else None
        rows.append({
            "category": cat, "label": categories.label(cat),
            "colour": categories.colour(cat),
            "budget": limit, "spent": spent,
            "typical": typical.get(cat),
            "expected_by_now": expected,
            "over": bool(limit and spent > limit),
            "ahead_of_pace": bool(expected and spent > expected),
            "pct": (spent / limit * 100) if limit else None,
        })

    return {
        "month": this_month,
        "through_month": through,
        "rows": rows,
        "total_budget": sum(v for v in limits.values()),
        "total_spent": sum(spent_now.values()),
        "base_currency": base_currency,
        "has_budgets": bool(limits),
    }
