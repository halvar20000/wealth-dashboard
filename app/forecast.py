"""Where the money is heading, on the assumptions the user states.

Two questions, one calculation. *If I put in this much a month, at this
return, where am I in N years?* And its inverse: *I want this much by
then — how much a month does that take?* Both start from what the
accounts add up to today, so the forecast moves with the real balance
rather than with a number typed in once and forgotten.

The arithmetic is the ordinary future value of an annuity with monthly
compounding, contributions at the end of each month:

    value_n = start · (1+i)^n + monthly · ((1+i)^n − 1) / i

with `i` the monthly rate that compounds to the yearly one — (1+r)^(1/12)
− 1, so that "6 % a year" is exactly 6 % after twelve months — and the
required contribution is the same identity solved for `monthly`.

The retirement outlook is the same path measured in age instead of
years: from the person's age today to the age they mean to stop, and
then the one figure the question is really about — what that sum
supports a month at a 4 % withdrawal, the rule of thumb every
retirement calculator quotes and this one labels as such. Nothing here predicts a return; the rate is the user's, and
the page says so. What the page does add is the split between what
was put in and what the return earned, because "€400k in twenty years"
means something different when €300k of it is your own deposits.
"""

from __future__ import annotations

from datetime import date

from .importers.base import parse_decimal

# The bounds the form accepts. Wide, because a forecast is a what-if,
# but bounded, because a 600-year horizon at 90 % is a page of infinities.
MAX_YEARS = 60
MAX_RATE = 30.0

DEFAULTS = {"mode": "project", "monthly": 500.0, "rate": 5.0, "years": 20,
            "target": 0.0}


def clean(form: dict) -> dict:
    """The user's inputs, typed and bounded. Anything unreadable falls
    back to the default rather than to an error page."""
    out = dict(DEFAULTS)
    out["mode"] = "target" if form.get("mode") == "target" else "project"
    out["monthly"] = max(0.0, _num(form.get("monthly"), DEFAULTS["monthly"]))
    out["rate"] = min(MAX_RATE, max(-MAX_RATE, _num(form.get("rate"), DEFAULTS["rate"])))
    out["years"] = int(min(MAX_YEARS, max(1, _num(form.get("years"), DEFAULTS["years"]))))
    out["target"] = max(0.0, _num(form.get("target"), DEFAULTS["target"]))
    return out


def monthly_rate(rate: float) -> float:
    """The monthly rate that compounds to `rate` % a year."""
    return (1 + rate / 100.0) ** (1 / 12.0) - 1


def _num(raw, default: float) -> float:
    """`1500`, `1500,50`, `1.500,50` and `1,500.50` all read as intended —
    the importers' European-or-English parser, reused."""
    if raw is None or str(raw).strip() == "":
        return float(default)
    value = parse_decimal(str(raw))
    return float(default) if value is None else value


def project(start: float, monthly: float, rate: float, years: int,
            first_year: int | None = None) -> list[dict]:
    """One point per year, year 0 being today.

    Computed month by month rather than from the closed form, so the
    yearly points are exactly what the monthly path passes through and
    a negative rate (a what-if worth allowing) needs no special case.
    """
    i = monthly_rate(rate)
    first_year = first_year or date.today().year
    value = float(start)
    contributed = float(start)
    points = [{"year": first_year, "years": 0, "value": value,
               "contributed": contributed, "returns": 0.0}]
    for month in range(1, years * 12 + 1):
        value = value * (1 + i) + monthly
        contributed += monthly
        if month % 12 == 0:
            points.append({"year": first_year + month // 12, "years": month // 12,
                           "value": value, "contributed": contributed,
                           "returns": value - contributed})
    return points


def required_monthly(start: float, target: float, rate: float, years: int) -> float:
    """What a month has to be for `start` to become `target` in `years`.
    Zero when the target is already met — never negative, because
    "withdraw €120 a month" is not advice this page gives."""
    n = years * 12
    if n <= 0:
        return 0.0
    i = monthly_rate(rate)
    if abs(i) < 1e-12:
        needed = (target - start) / n
    else:
        growth = (1 + i) ** n
        needed = (target - start * growth) * i / (growth - 1)
    return max(0.0, needed)


def years_to_reach(start: float, monthly: float, rate: float, target: float,
                   limit: int = MAX_YEARS) -> int | None:
    """The first whole year the projection is at or above `target`, or
    None within the limit. Year 0 when it already is."""
    for p in project(start, monthly, rate, limit):
        if p["value"] >= target:
            return p["years"]
    return None


def plan(start: float, inputs: dict) -> dict:
    """Everything the page shows, from the balance and the inputs."""
    mode, rate, years = inputs["mode"], inputs["rate"], inputs["years"]
    if mode == "target":
        monthly = required_monthly(start, inputs["target"], rate, years)
    else:
        monthly = inputs["monthly"]
    points = project(start, monthly, rate, years)
    end = points[-1]
    out = {
        "mode": mode, "start": start, "monthly": monthly, "rate": rate,
        "years": years, "target": inputs["target"],
        "points": points,
        "end_value": end["value"],
        "end_contributed": end["contributed"],
        "end_returns": end["returns"],
        "end_year": end["year"],
        "already_there": mode == "target" and start >= inputs["target"] > 0,
    }
    if mode == "project" and inputs["target"] > 0:
        out["reach_years"] = years_to_reach(start, monthly, rate, inputs["target"])
    return out


# ─── Retirement ──────────────────────────────────────────────────────

RETIREMENT_DEFAULTS = {"retire_age": 65, "rate": 5.0, "monthly": None}
MIN_RETIRE_AGE, MAX_RETIRE_AGE = 40, 80
SAFE_WITHDRAWAL = 0.04            # the 4 % rule, per year


def clean_retirement(form: dict) -> dict:
    """Retire age, return, and a monthly amount — or None for "take it
    from my Forecast plan", which is what an empty field means."""
    out = dict(RETIREMENT_DEFAULTS)
    out["retire_age"] = int(min(MAX_RETIRE_AGE, max(
        MIN_RETIRE_AGE, _num(form.get("retire_age"), RETIREMENT_DEFAULTS["retire_age"]))))
    out["rate"] = min(MAX_RATE, max(-MAX_RATE, _num(form.get("rate"), RETIREMENT_DEFAULTS["rate"])))
    raw = form.get("monthly")
    out["monthly"] = None if raw is None or str(raw).strip() == "" else max(0.0, _num(raw, 0.0))
    return out


def retirement(start: float, monthly: float, rate: float, age_now: float,
               retire_age: int, today: date | None = None) -> dict:
    """The path from today's age to the retirement age, one point a
    year, and what the sum at the end supports.

    Ages are fractional, so a 47.3-year-old retiring at 65 gets 212
    months, not 216 — the same month-by-month walk as `project`, only
    the axis is age.
    """
    today = today or date.today()
    months = max(0, int(round((retire_age - age_now) * 12)))
    i = monthly_rate(rate)
    value = float(start)
    contributed = float(start)
    points = [{"age": round(age_now, 1), "year": today.year, "value": value,
               "contributed": contributed}]
    for m in range(1, months + 1):
        value = value * (1 + i) + monthly
        contributed += monthly
        age = age_now + m / 12.0
        if m % 12 == 0 or m == months:
            points.append({"age": round(age, 1), "year": today.year + (today.month - 1 + m) // 12,
                           "value": value, "contributed": contributed})
    at_retirement = points[-1]["value"]
    return {
        "age_now": round(age_now, 1), "retire_age": retire_age,
        "years_to_go": round(months / 12.0, 1), "months_to_go": months,
        "retire_year": points[-1]["year"],
        "points": points,
        "at_retirement": at_retirement,
        "contributed": points[-1]["contributed"],
        "returns": at_retirement - points[-1]["contributed"],
        "monthly_income": at_retirement * SAFE_WITHDRAWAL / 12.0,
        "retired_already": months == 0,
    }
