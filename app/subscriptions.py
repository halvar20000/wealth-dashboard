"""Finding the charges that repeat.

Nobody knows what they are subscribed to. The bank does, in the sense
that the evidence is all there — the same merchant, the same amount,
every month — and nobody reads a statement that way.

The detection is deliberately conservative, because the failure that
matters is not missing a subscription. It is announcing that something
is a €400 monthly commitment when it was three unrelated payments to the
same shop, which makes the whole page untrustworthy and it never gets
looked at again.

So a group has to clear all of these:

* **at least three payments** — two is a coincidence
* **a recognisable rhythm** — the gaps cluster around monthly, quarterly
  or yearly rather than being scattered
* **a stable amount** — subscriptions move with price rises, not with
  what you felt like buying, so the spread has to be tight

What it will not find: anything billed at a genuinely irregular
interval, and anything that changes merchant name every time. Those are
listed as "possibly recurring" rather than promoted, so the page can be
wrong out loud instead of quietly.
"""

from __future__ import annotations

import re
import statistics
from datetime import date, datetime

from . import fx, people
from .db import get_conn

# The rhythms worth naming, in days, with how far a gap may drift and
# still count. A month is not 30 days — billing on the 3rd gives gaps of
# 28 to 31 — so the tolerance is what makes monthly detectable at all.
_RHYTHMS = [
    ("weekly", 7, 2),
    ("monthly", 30.4, 6),
    ("quarterly", 91.3, 12),
    ("half-yearly", 182.6, 20),
    ("yearly", 365.25, 30),
]

_NOISE = re.compile(
    r"\b(\d{2,}[/-]\d{2,}|\d{6,}|card|carte|kartenzahlung|paiement|payment|"
    r"achat|purchase|ref|reference|mandate|sepa|dd|direct debit)\b", re.I)


def _fingerprint(description: str, counterparty: str | None) -> str:
    """What makes two charges "the same thing".

    The counterparty is used when the bank supplies one, because it is
    already the clean version. Otherwise the description is stripped of
    the parts that change every time — dates, card numbers, reference
    numbers — and what is left is the merchant.
    """
    if counterparty and counterparty.strip():
        base = counterparty
    else:
        base = _NOISE.sub(" ", description or "")
        base = re.sub(r"\d", " ", base)
    return " ".join(base.lower().split())[:60]


def _rhythm(gaps: list[float]) -> tuple[str | None, float]:
    """Name the rhythm, and say how well the gaps fit it (0–1)."""
    if not gaps:
        return None, 0.0
    median = statistics.median(gaps)
    for name, days, tolerance in _RHYTHMS:
        if abs(median - days) <= tolerance:
            fits = sum(1 for g in gaps if abs(g - days) <= tolerance * 1.5)
            return name, fits / len(gaps)
    return None, 0.0


def marks() -> dict[str, str]:
    """What the user has already judged: fingerprint → state."""
    with get_conn() as conn:
        return {r["key"]: r["state"] for r in
                conn.execute("SELECT key, state FROM subscription_marks")}


def mark(key: str, state: str | None, name: str | None = None) -> str | None:
    """Say that a detection is a subscription, or is not one. `None`
    forgets the judgement and puts it back among the found."""
    key = (key or "").strip()[:60]
    if not key:
        raise ValueError("A subscription needs its key.")
    if state not in ("confirmed", "ignored", None, ""):
        raise ValueError("state must be 'confirmed', 'ignored' or empty.")
    with get_conn() as conn:
        if not state:
            conn.execute("DELETE FROM subscription_marks WHERE key = ?", (key,))
            return None
        conn.execute("INSERT INTO subscription_marks (key, state, name) VALUES (?, ?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET state = excluded.state, "
                     "name = COALESCE(excluded.name, subscription_marks.name)",
                     (key, state, (name or "").strip()[:70] or None))
    return state


def detect(base_currency: str = "EUR", min_occurrences: int = 3,
           account_ids: list[int] | None = None) -> dict:
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"""
            SELECT t.id, t.txn_date, t.description, t.counterparty, t.amount,
                   t.currency, t.category, a.name AS account_name
              FROM transactions t JOIN accounts a ON a.id = t.account_id
             WHERE t.amount < 0
               AND t.kind NOT IN ('buy', 'sell')
               AND COALESCE(t.category, '') NOT IN ('transfer', 'investment'){only}
             ORDER BY t.txn_date
            """, params).fetchall()]
    # A charge in another currency is still a charge. It is converted at
    # the rate of its own day, so a £12.99 subscription on a euro
    # dashboard is found and costed like any other; where there is no
    # rate, the row is left out rather than guessed at.
    for r in rows:
        if (r["currency"] or base_currency).upper() == base_currency.upper():
            r["base_amount"] = r["amount"]
        else:
            converted, _as_of = fx.convert(r["amount"], r["currency"], base_currency, r["txn_date"])
            r["base_amount"] = converted
    rows = [r for r in rows if r["base_amount"] is not None]

    groups: dict[str, list[dict]] = {}
    for r in rows:
        key = _fingerprint(r["description"], r["counterparty"])
        if len(key) >= 3:
            groups.setdefault(key, []).append(r)

    judged = marks()
    confirmed, possible, ignored = [], [], []
    for key, items in groups.items():
        if len(items) < min_occurrences:
            continue
        dates = [datetime.strptime(i["txn_date"], "%Y-%m-%d").date() for i in items]
        gaps = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
        if not gaps:
            continue
        rhythm, fit = _rhythm(gaps)
        amounts = [abs(i["base_amount"]) for i in items]
        median_amount = statistics.median(amounts)
        spread = (statistics.pstdev(amounts) / median_amount) if median_amount else 1.0

        last = max(dates)
        entry = {
            "key": key,
            "name": (items[-1]["counterparty"] or items[-1]["description"])[:70],
            "account": items[-1]["account_name"],
            "category": items[-1]["category"],
            "count": len(items),
            "amount": median_amount,
            "total_paid": sum(amounts),
            "currency": base_currency,
            "rhythm": rhythm,
            "fit": round(fit, 2),
            "spread": round(spread, 3),
            "first_seen": min(dates).isoformat(),
            "last_seen": last.isoformat(),
            "days_since": (date.today() - last).days,
            "yearly": _yearly_cost(median_amount, rhythm),
            "currencies": sorted({(i["currency"] or base_currency).upper() for i in items}),
            "marked": judged.get(key),
        }
        # What the user has said outranks what the arithmetic thinks:
        # a ragged rhythm they call a subscription is one, and a tidy
        # one they have dismissed stops being offered. Everything else
        # is judged as before — a tight amount and a clear rhythm, or
        # it goes in the maybe pile.
        if judged.get(key) == "ignored":
            ignored.append(entry)
        elif judged.get(key) == "confirmed":
            entry["rhythm"] = rhythm or "monthly"
            entry["yearly"] = entry["yearly"] or _yearly_cost(median_amount, entry["rhythm"])
            confirmed.append(entry)
        elif rhythm and fit >= 0.6 and spread <= 0.15:
            confirmed.append(entry)
        elif len(items) >= 4:
            possible.append(entry)

    confirmed.sort(key=lambda e: -(e["yearly"] or 0))
    possible.sort(key=lambda e: -e["total_paid"])

    # A subscription whose last charge is long overdue for its rhythm has
    # probably been cancelled. Worth saying, rather than leaving a dead
    # €14/month on a page headed "what you pay every month".
    for e in confirmed:
        period = next((d for n, d, _ in _RHYTHMS if n == e["rhythm"]), None)
        e["likely_ended"] = bool(period and e["days_since"] > period * 2)
        # One a person has confirmed is not quietly dropped from the
        # total because a charge is late; saying it looks ended is
        # enough.
        if e.get("marked") == "confirmed":
            e["likely_ended"] = False

    active = [e for e in confirmed if not e["likely_ended"]]
    return {
        "confirmed": confirmed,
        "active": active,
        "possible": possible[:15],
        "ignored": sorted(ignored, key=lambda e: -e["total_paid"]),
        "yearly_total": sum(e["yearly"] or 0 for e in active),
        "monthly_total": sum((e["yearly"] or 0) / 12 for e in active),
        "base_currency": base_currency,
    }


def _yearly_cost(amount: float, rhythm: str | None) -> float | None:
    if not rhythm:
        return None
    per_year = {"weekly": 52, "monthly": 12, "quarterly": 4,
                "half-yearly": 2, "yearly": 1}[rhythm]
    return amount * per_year
