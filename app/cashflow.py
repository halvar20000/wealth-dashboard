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

from . import categories, fx, people
from .db import get_conn


def _month_floor(months_back: int) -> str:
    today = date.today()
    year, month = today.year, today.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}-01"


def _month_rates(month: str) -> tuple[str | None, dict[str, float]]:
    """The ECB rates for a month: the newest publication in it, or the
    oldest on file for a month older than what is kept.

    Ninety days of rates are stored. A transaction from last spring is
    converted at the oldest rate the app has rather than dropped —
    a spending figure a few percent off on the exchange rate is a
    figure; a category that silently omits a whole account is not."""
    as_of, rates = fx.rates_on(f"{month}-31")
    if as_of is None:
        with get_conn() as conn:
            row = conn.execute("SELECT MIN(as_of) AS d FROM fx_rates").fetchone()
        if row and row["d"]:
            as_of, rates = fx.rates_on(row["d"])
    return as_of, rates


def monthly(months: int = 13, base_currency: str = "EUR",
            account_ids: list[int] | None = None) -> dict:
    """Income, spending and investment per calendar month.

    Every currency is counted, converted into the base at the ECB rate
    of its month — see _month_rates(). An amount in a currency no rate
    covers is not converted and not silently dropped either: it is
    reported in `unconverted`, so the page can say what it left out.
    Until 0.10.1 only the base currency was summed, which meant the
    spending on a foreign-currency account was simply missing from the
    Budget and Cash Flow pages, with nothing on either page to say so.
    """
    since = _month_floor(months - 1)
    base = base_currency.upper()
    only, params = people.sql_in(account_ids)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT substr(txn_date, 1, 7) AS month,
                   COALESCE(NULLIF(category, ''), 'other') AS category,
                   UPPER(currency) AS currency,
                   SUM(amount) AS total,
                   COUNT(*)    AS n
              FROM transactions
             WHERE txn_date >= ?
               AND kind NOT IN ('buy', 'sell'){only}
             GROUP BY month, category, currency
             ORDER BY month
            """, (since, *params)).fetchall()

    # Read once, not per row: the user can change which categories count
    # as spending or as income, so this cannot be a constant fixed at
    # import time.
    spending = set(categories.spending())
    income = set(categories.income())

    rate_cache: dict[str, tuple[str | None, dict[str, float]]] = {}
    converted: dict[str, float] = {}      # currency -> amount converted, as typed
    unconverted: dict[str, float] = {}    # currency -> amount left out
    fx_as_of: str | None = None

    months_map: dict[str, dict] = {}
    by_category: dict[str, float] = {}
    income_by_category: dict[str, float] = {}
    for r in rows:
        m = months_map.setdefault(r["month"], {
            "month": r["month"], "income": 0.0, "spending": 0.0,
            "investment": 0.0, "categories": {}, "income_categories": {}})
        cat, total, ccy = r["category"], r["total"] or 0.0, r["currency"] or base
        if ccy != base:
            if r["month"] not in rate_cache:
                rate_cache[r["month"]] = _month_rates(r["month"])
            as_of, rates = rate_cache[r["month"]]
            if ccy not in rates or base not in rates:
                unconverted[ccy] = unconverted.get(ccy, 0.0) + abs(total)
                continue
            converted[ccy] = converted.get(ccy, 0.0) + abs(total)
            total = total / rates[ccy] * rates[base]
            if as_of and (fx_as_of is None or as_of > fx_as_of):
                fx_as_of = as_of
        if cat == "transfer":
            continue                      # internal: not a flow at all
        if cat in income:
            # Every category in the income group, each its own line:
            # a salary, a rent coming in, interest — see categories.py.
            m["income"] += total
            m["income_categories"][cat] = m["income_categories"].get(cat, 0.0) + total
            income_by_category[cat] = income_by_category.get(cat, 0.0) + total
        elif cat == "investment":
            m["investment"] += abs(total)
        elif cat in spending:
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
        "income_by_category": sorted(
            ({"category": c, "label": categories.label(c),
              "colour": categories.colour(c), "total": v, "per_month": v / n}
             for c, v in income_by_category.items()),
            key=lambda x: -x["total"]),
        "total_income": sum(m["income"] for m in series),
        "total_spending": sum(m["spending"] for m in series),
        "total_investment": sum(m["investment"] for m in series),
        "average_spending": sum(m["spending"] for m in series) / n,
        "average_income": sum(m["income"] for m in series) / n,
        "months_covered": len(series),
        "base_currency": base_currency,
        # What crossed a currency on the way in, and what could not.
        "converted": sorted(({"currency": c, "amount": a} for c, a in converted.items()),
                            key=lambda x: -x["amount"]),
        "unconverted": sorted(({"currency": c, "amount": a} for c, a in unconverted.items()),
                              key=lambda x: -x["amount"]),
        "fx_as_of": fx_as_of,
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


def budget_report(base_currency: str = "EUR",
                  account_ids: list[int] | None = None) -> dict:
    """This month against the budget, with a typical month for context.

    The comparison people actually want is not "am I over" — halfway
    through a month everyone is under. It is "am I over *for how far
    through the month I am*", so the expected-to-date figure is what the
    bar is measured against.
    """
    today = date.today()
    this_month = today.strftime("%Y-%m")
    limits = budgets()
    data = monthly(months=13, base_currency=base_currency, account_ids=account_ids)

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

    # Every spending category gets a row, whether or not anything has
    # been booked to it yet — a row is the only place a budget can be
    # typed in, so a category with no row is a category that can never
    # have one. Categories that were deleted but still carry spending
    # this year stay too, since the money is real. Biggest budgets first,
    # then biggest typical spend, then the catalogue's own order.
    order = {c: i for i, c in enumerate(categories.spending())}
    rows = []
    for cat in sorted(set(order) | set(limits) | set(spent_now) | set(typical),
                      key=lambda c: (-(limits.get(c) or typical.get(c, 0)),
                                     order.get(c, len(order)))):
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
        "day": today.day, "days_in_month": days_in_month,
        "rows": rows,
        "total_budget": sum(v for v in limits.values()),
        "total_spent": sum(spent_now.values()),
        "base_currency": base_currency,
        "has_budgets": bool(limits),
        "converted": data["converted"],
        "unconverted": data["unconverted"],
        "fx_as_of": data["fx_as_of"],
    }
