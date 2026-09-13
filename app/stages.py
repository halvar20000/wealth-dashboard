"""The three stages of building wealth — and which one you are in.

Early on, what you put in is what grows the pile: a 6 % return on
10 000 is 600, and 500 a month is 6 000. Later the two pull together.
Later still the return on what is there outweighs anything you could
add, and the pile carries itself — the compounding stage, the one the
whole exercise was for. The border between them is one ratio:

    what the market does in a year      value × rate
    ────────────────────────────── =  ─────────────────
    what you put in in a year         12 × monthly

Below a half, saving is what matters (stage 1). Between a half and
two, the two are of the same order (stage 2). Above two, compounding
is in charge (stage 3). The crossover — returns equal to savings —
sits in the middle of stage 2, at the one figure worth knowing by
heart: `12 × monthly / rate`, the wealth at which a year of returns
pays a year of savings.

Two views of the same ratio. *On your plan*: today's securities and
the Forecast page's monthly amount and expected return, projected
year by year until compounding takes over. *As it went*: for every
calendar year the app has records of, what actually went in against
what the market actually did — value at the end minus value at the
start minus the money put in, plus the dividends paid out. Nothing is
stored; the answer moves with the balance.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import forecast, history
from .db import get_conn

# The borders of stage 2, as returns ÷ savings.
LOWER, UPPER = 0.5, 2.0
MAX_YEARS = 50


def stage_of(ratio: float | None) -> int | None:
    if ratio is None:
        return None
    if ratio < LOWER:
        return 1
    if ratio <= UPPER:
        return 2
    return 3


def crossover_wealth(monthly: float, rate: float) -> float | None:
    """The wealth at which a year of returns equals a year of savings."""
    if rate <= 0 or monthly <= 0:
        return None
    return 12.0 * monthly / (rate / 100.0)


def path(start: float, monthly: float, rate: float, first_year: int | None = None) -> dict:
    """Year by year until stage 3 has been reached for five years, or
    fifty years, whichever is sooner: what goes in, what the market
    does, the ratio and the stage — with the year each border falls."""
    first_year = first_year or date.today().year
    i = forecast.monthly_rate(rate)
    value = float(start)
    years = []
    milestones: dict[str, dict] = {}
    yearly_in = 12.0 * monthly
    stage3_since = None
    for n in range(1, MAX_YEARS + 1):
        opening = value
        returns = 0.0
        for _ in range(12):
            r = value * i
            value = value + r + monthly
            returns += r
        ratio = (returns / yearly_in) if yearly_in > 0 else None
        stage = stage_of(ratio) if ratio is not None else (3 if returns > 0 else None)
        years.append({"n": n, "year": first_year + n, "opening": opening, "put_in": yearly_in,
                      "returns": returns, "closing": value, "ratio": ratio, "stage": stage})
        if ratio is not None:
            for key, border in (("half", LOWER), ("equal", 1.0), ("double", UPPER)):
                if key not in milestones and ratio >= border:
                    milestones[key] = {"n": n, "year": first_year + n, "value": opening}
        if stage == 3 and stage3_since is None:
            stage3_since = n
        if stage3_since is not None and n - stage3_since >= 5 and n >= 10:
            break
    now_ratio = (start * rate / 100.0 / yearly_in) if yearly_in > 0 else None
    return {"years": years, "milestones": milestones, "ratio": now_ratio,
            "stage": stage_of(now_ratio) if now_ratio is not None else (3 if start > 0 else None),
            "crossover": crossover_wealth(monthly, rate)}


def as_it_went(base_currency: str, account_ids: list[int] | None = None,
               today: date | None = None) -> list[dict]:
    """Every calendar year the app has securities records of: what went
    in, what the market did, the ratio, the stage. The current year is
    measured to today and the money it put in is left as is — a
    half-year is a half-year, and the ratio is of the same halves."""
    today = today or date.today()
    v = history.Valuer(base_currency, account_ids)
    if not v.trades:
        return []
    first = min(d[0] for d, _, _ in v.trades.values() if d)
    from . import people
    only, params = people.sql_in(account_ids, "account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT txn_date, kind, amount, currency FROM transactions WHERE isin IS NOT NULL "
            f"AND kind IN ('buy', 'sell', 'dividend', 'interest'){only} ORDER BY txn_date",
            params).fetchall()
    out = []
    for year in range(int(first[:4]), today.year + 1):
        start_day = f"{year}-01-01"
        end = date(year, 12, 31) if year < today.year else today
        opening = v.value_on((date(year, 1, 1) - timedelta(days=1)).isoformat())[1] if start_day > first else 0.0
        closing = v.value_on(end.isoformat())[1]
        put_in = income = 0.0
        for r in rows:
            if not (start_day <= r["txn_date"] <= end.isoformat()):
                continue
            amt = v.to_base(r["amount"], r["currency"], r["txn_date"])
            if amt is None:
                continue
            if r["kind"] == "buy":
                put_in += -amt
            elif r["kind"] == "sell":
                put_in -= amt
            else:
                income += amt
        if closing is None:
            continue
        opening = opening or 0.0
        returns = closing - opening - put_in + income
        ratio = (returns / put_in) if put_in > 1e-9 else None
        out.append({"year": year, "opening": opening, "put_in": put_in, "income": income,
                    "returns": returns, "closing": closing, "ratio": ratio,
                    "stage": stage_of(ratio) if ratio is not None else None,
                    "partial": year == today.year,
                    "days": (end - max(date(year, 1, 1), date.fromisoformat(first))).days + 1})
    return out


def actual_monthly(rows_years: list[dict]) -> float | None:
    """What actually went in a month, over the last twelve months of
    records — the figure to put beside the plan's."""
    if not rows_years:
        return None
    last = rows_years[-1]
    days = last["days"]
    put_in = last["put_in"]
    if len(rows_years) > 1 and days < 365:
        prev = rows_years[-2]
        put_in += prev["put_in"] * (365 - days) / max(prev["days"], 1)
        days = 365
    if days < 30:
        return None
    return put_in / days * 365 / 12
