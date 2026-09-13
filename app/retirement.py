"""A retirement plan: will the money last, and if not, until when.

The Forecast page's outlook answers one question — what the pile at
retirement supports at 4 % — and that is the right first answer. This
is the second: a plan with the retirement in it. What you put in
until then, growing a little each year; what you will spend each
month from then on, item by item, each with the ages it runs from and
to; what will come in — a state pension, a rent; a return before and
a return after, the fees off both, inflation on everything, tax on
what is withdrawn. Walked a year at a time from today's age to a
horizon — ninety, say — the plan says what the pile is at retirement,
what it would have to be, how far along that is, and the age the
money runs out or what is left at the horizon.

Two lines beside the projection. *Required*: from retirement on, the
capital that funds the rest of the plan from that age — the present
value of every net need to the horizon at the retirement return — so
the projection sitting above it means the money lasts. *On track*:
before retirement, the path that would reach the required capital
exactly, with the same contributions — the projection above it means
ahead of plan.

Everything nominal inside; the page can show it in today's money by
taking the inflation back out, which is what "will it be enough" is
really asked in. Nothing predicts a return: every rate is the user's,
and the page says so.
"""

from __future__ import annotations

import json
from datetime import date

from .importers.base import parse_decimal

DEFAULTS = {
    "retire_age": 65, "horizon_age": 90, "monthly": None, "contribution_growth": 2.0,
    "return_before": 5.0, "return_after": 3.0, "fee": 0.3, "inflation": 2.0, "tax": 0.0,
    "expenses": [], "incomes": [],
}
MAX_ITEMS = 12


def _num(raw, default):
    if raw is None or str(raw).strip() == "":
        return float(default) if default is not None else None
    v = parse_decimal(str(raw))
    return float(default) if v is None else v


def clean(form) -> dict:
    """The plan's inputs from a form (or a stored dict), bounded."""
    out = dict(DEFAULTS)
    get = form.get
    out["retire_age"] = int(min(80, max(40, _num(get("retire_age"), DEFAULTS["retire_age"]))))
    out["horizon_age"] = int(min(110, max(out["retire_age"] + 1, _num(get("horizon_age"), DEFAULTS["horizon_age"]))))
    raw = get("monthly")
    out["monthly"] = None if raw in (None, "") else max(0.0, _num(raw, 0.0))
    for key, lo, hi in (("contribution_growth", 0, 20), ("return_before", -30, 30), ("return_after", -30, 30),
                        ("fee", 0, 10), ("inflation", 0, 20), ("tax", 0, 80)):
        out[key] = min(hi, max(lo, _num(get(key), DEFAULTS[key])))
    for kind in ("expenses", "incomes"):
        items = form.get(kind)
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except ValueError:
                items = []
        if not isinstance(items, list):
            # Rows from the page: name_0, monthly_0, from_0, to_0 …
            items = []
            prefix = "exp" if kind == "expenses" else "inc"
            for i in range(MAX_ITEMS + 1):
                name = " ".join((get(f"{prefix}_name_{i}") or "").split())[:60]
                if not name:
                    continue
                items.append({"name": name, "monthly": get(f"{prefix}_monthly_{i}"),
                              "from_age": get(f"{prefix}_from_{i}"), "to_age": get(f"{prefix}_to_{i}")})
        clean_items = []
        for it in items[:MAX_ITEMS]:
            if not isinstance(it, dict) or not it.get("name"):
                continue
            monthly = max(0.0, _num(it.get("monthly"), 0.0))
            if monthly <= 0:
                continue
            from_age = _num(it.get("from_age"), None)
            to_age = _num(it.get("to_age"), None)
            clean_items.append({"name": str(it["name"])[:60], "monthly": monthly,
                                "from_age": int(from_age) if from_age else None,
                                "to_age": int(to_age) if to_age else None})
        out[kind] = clean_items
    return out


def _active(items: list[dict], age: int, default_from: int, default_to: int) -> float:
    total = 0.0
    for it in items:
        lo = it.get("from_age") or default_from
        hi = it.get("to_age") or default_to
        if lo <= age < hi:
            total += it["monthly"]
    return total


def project(start: float, age_now: float, plan: dict, monthly: float, today: date | None = None) -> dict:
    """The plan walked a year at a time. See the module docstring."""
    today = today or date.today()
    retire, horizon = plan["retire_age"], plan["horizon_age"]
    r_before = (plan["return_before"] - plan["fee"]) / 100.0
    r_after = (plan["return_after"] - plan["fee"]) / 100.0
    infl = plan["inflation"] / 100.0
    tax = plan["tax"] / 100.0
    growth = plan["contribution_growth"] / 100.0
    age0 = int(age_now)
    years_to_retire = max(0, retire - age0)

    def walk(start_value: float) -> tuple[list[dict], float | None]:
        value = float(start_value)
        contrib = monthly * 12.0
        rows, runs_out = [], None
        for k in range(0, horizon - age0):
            age = age0 + k
            year = today.year + k
            deflate = (1 + infl) ** k
            if age < retire:
                value = value * (1 + r_before) + contrib
                rows.append({"age": age, "year": year, "phase": "saving", "end": value, "end_real": value / deflate,
                             "contribution": contrib, "expenses": 0.0, "income": 0.0, "withdrawal": 0.0})
                contrib *= (1 + growth)
            else:
                expenses = _active(plan["expenses"], age, retire, horizon) * 12 * deflate
                income = _active(plan["incomes"], age, retire, horizon) * 12 * deflate
                need = max(0.0, expenses - income)
                gross = need / (1 - tax) if tax < 1 else need
                value = value * (1 + r_after) - gross
                if value < 0:
                    if runs_out is None:
                        runs_out = age
                    value = 0.0
                rows.append({"age": age, "year": year, "phase": "retired", "end": value, "end_real": value / deflate,
                             "contribution": 0.0, "expenses": expenses, "income": income, "withdrawal": gross})
        return rows, runs_out

    rows, runs_out = walk(start)
    # Required from each retirement age: the present value of what is
    # still to be withdrawn, at the retirement return.
    retired = [r for r in rows if r["phase"] == "retired"]
    required_at: dict[int, float] = {}
    acc = 0.0
    for r in reversed(retired):
        acc = (acc + r["withdrawal"]) / (1 + r_after) if (1 + r_after) > 0 else acc + r["withdrawal"]
        required_at[r["age"]] = acc
    # required_at[age] is the pile needed at the START of that year;
    # the pile at retirement is the end of the year before, the same
    # moment — so it compares against the retirement year's figure,
    # and a year's end against the year after's.
    required = required_at.get(retire, 0.0)
    # Where the pile stands at retirement, and the on-track path — the
    # walk is linear in the start value, so two walks give the start
    # that would land exactly on the required capital.
    at_retirement = next((r["end"] for r in rows if r["age"] == retire - 1), start) if years_to_retire else start
    zero_rows, _ = walk(0.0)
    one_rows, _ = walk(1.0)
    zero_end = next((r["end"] for r in zero_rows if r["age"] == retire - 1), 0.0) if years_to_retire else 0.0
    one_end = next((r["end"] for r in one_rows if r["age"] == retire - 1), 1.0) if years_to_retire else 1.0
    gain = one_end - zero_end
    start_needed = (required - zero_end) / gain if gain > 1e-9 else None
    on_track = {}
    if start_needed is not None and start_needed > 0:
        track_rows, _ = walk(start_needed)
        on_track = {r["age"]: r["end"] for r in track_rows if r["phase"] == "saving"}
    for r in rows:
        r["required"] = (required_at.get(r["age"] + 1, 0.0) if r["phase"] == "retired" else on_track.get(r["age"]))
        r["required_real"] = (r["required"] / (1 + infl) ** (r["age"] - age0)) if r["required"] is not None else None
    left = rows[-1]["end"] if rows else start
    funded = (at_retirement / required) if required > 0 else None
    monthly_needs = _active(plan["expenses"], retire, retire, horizon) - _active(plan["incomes"], retire, retire, horizon)
    return {"rows": rows, "at_retirement": at_retirement, "required": required, "funded": funded,
            "runs_out_age": runs_out, "left_at_horizon": left, "start_needed": start_needed,
            "years_to_retire": years_to_retire, "retire_year": today.year + years_to_retire,
            "retired_already": years_to_retire == 0,
            "monthly_needs_at_retirement": monthly_needs * (1 + infl) ** years_to_retire,
            "monthly_needs_today": monthly_needs,
            "at_retirement_real": at_retirement / (1 + infl) ** years_to_retire,
            "required_real": required / (1 + infl) ** years_to_retire,
            "enough": runs_out is None}
