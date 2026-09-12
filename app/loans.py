"""Loans and mortgages: the schedule, computed, so the debt is right today.

A loan is an account of type `loan` — it belongs to people, it has a
balance reading, the overview subtracts it — plus a row here with the
terms: principal, rate, first payment, how often, how much. From those
the amortisation schedule follows, and with it the one number that
matters and that nobody wants to keep typing in: what is still owed
today. The reading on the account is written from the schedule each
day; a balance typed in by hand on the account page still wins on the
day it is typed, because the bank's letter beats the arithmetic.

The arithmetic is the bank's: a constant annuity, interest rounded to
the cent each period, the last payment whatever is left. That is what
reproduces a bank's own worked example to the cent, and it was checked
against one — a CHF mortgage whose first instalment split 128.61 of
interest from 4 142.60 of capital.

The payment can be given (the figure on the contract) or left blank
and worked out from a term in months; extra repayments are dated
lump sums applied after the regular capital of that period.
"""

from __future__ import annotations

import calendar
import json
from datetime import date

from . import i18n
from .db import get_conn

PERIODS = {1: "monthly", 3: "quarterly", 6: "half-yearly", 12: "yearly"}
MAX_PERIODS = 1200


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def annuity(principal: float, period_rate: float, periods: int) -> float:
    """The constant payment that clears `principal` in `periods`."""
    if periods <= 0:
        return principal
    if period_rate <= 0:
        return principal / periods
    return principal * period_rate / (1 - (1 + period_rate) ** -periods)


def schedule(loan: dict) -> list[dict]:
    """One row per payment: {n, date, payment, interest, capital, extra, balance}."""
    principal = float(loan["principal"])
    months = int(loan.get("period_months") or 1)
    rate = float(loan.get("rate_pct") or 0) / 100 / (12 / months)
    first = date.fromisoformat(loan["first_payment"])
    payment = loan.get("payment")
    if not payment:
        payment = annuity(principal, rate, int(loan.get("term_months") or months) // months)
    payment = round(float(payment), 2)
    extras: dict[str, float] = {}
    for e in _extras(loan):
        extras[e["date"]] = extras.get(e["date"], 0.0) + float(e["amount"])
    rows, balance, n = [], round(principal, 2), 0
    while balance > 0.005 and n < MAX_PERIODS:
        when = _add_months(first, n * months)
        interest = round(balance * rate, 2)
        capital = round(payment - interest, 2)
        if capital <= 0 and n > 0 and rate > 0:
            break                                  # a payment that does not cover the interest never ends
        if capital >= balance:
            capital, pay = balance, round(interest + balance, 2)
        else:
            pay = payment
        balance = round(balance - capital, 2)
        extra = min(extras.get(when.isoformat(), 0.0), balance)
        if extra:
            balance = round(balance - extra, 2)
        rows.append({"n": n + 1, "date": when.isoformat(), "payment": pay, "interest": interest,
                     "capital": capital, "extra": round(extra, 2), "balance": balance})
        n += 1
    return rows


def status(loan: dict, today: date | None = None) -> dict:
    """The loan as of `today`: what is owed, what was paid, what is left."""
    today = (today or date.today()).isoformat()
    rows = schedule(loan)
    done = [r for r in rows if r["date"] <= today]
    left = [r for r in rows if r["date"] > today]
    balance = done[-1]["balance"] if done else round(float(loan["principal"]), 2)
    return {
        "balance": balance,
        "paid_capital": round(sum(r["capital"] + r["extra"] for r in done), 2),
        "paid_interest": round(sum(r["interest"] for r in done), 2),
        "paid_total": round(sum(r["payment"] + r["extra"] for r in done), 2),
        "payments_done": len(done), "payments_left": len(left),
        "next": left[0] if left else None,
        "payoff": rows[-1]["date"] if rows else None,
        "total_interest": round(sum(r["interest"] for r in rows), 2),
        "payment": rows[0]["payment"] if rows else None,
        "per_month": round((rows[0]["payment"] if rows else 0) / int(loan.get("period_months") or 1), 2),
        "progress": (1 - balance / float(loan["principal"])) if float(loan["principal"]) else 1.0,
        "endless": bool(rows) and rows[-1]["balance"] > 0.005,
    }


def _extras(loan: dict) -> list[dict]:
    try:
        raw = json.loads(loan.get("extras") or "[]")
    except ValueError:
        return []
    return [e for e in raw if isinstance(e, dict) and e.get("date") and e.get("amount")]


# ─── Storage ─────────────────────────────────────────────────────────

def all_loans(account_ids: list[int] | None = None) -> list[dict]:
    from . import people
    only, params = people.sql_in(account_ids, "l.account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT l.*, a.name, a.currency FROM loans l JOIN accounts a ON a.id = l.account_id "
            f"WHERE 1=1{only} ORDER BY a.name", params).fetchall()
    return [dict(r) for r in rows]


def get(loan_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT l.*, a.name, a.currency FROM loans l JOIN accounts a "
                           "ON a.id = l.account_id WHERE l.id = ?", (loan_id,)).fetchone()
    return dict(row) if row else None


def clean(form) -> dict:
    """The form → the terms, or a ValueError in a sentence."""
    from .importers.base import parse_decimal
    name = " ".join((form.get("name") or "").split())[:80]
    if not name:
        raise ValueError(i18n.t("The loan needs a name."))
    principal = parse_decimal(form.get("principal"))
    if not principal or principal <= 0:
        raise ValueError(i18n.t("The principal must be a positive amount."))
    rate = parse_decimal(form.get("rate_pct"))
    if rate is None or rate < 0 or rate > 100:
        raise ValueError(i18n.t("The rate is a percentage per year, like 3.2."))
    try:
        first = date.fromisoformat((form.get("first_payment") or "").strip())
    except ValueError:
        raise ValueError(i18n.t("The first payment needs a date, written year-month-day.")) from None
    try:
        months = int(form.get("period_months") or 1)
    except ValueError:
        months = 1
    if months not in PERIODS:
        raise ValueError(i18n.t("Payments are monthly, quarterly, half-yearly or yearly."))
    payment = parse_decimal(form.get("payment"))
    term = parse_decimal(form.get("term_months"))
    if (payment is None or payment <= 0) and (term is None or term <= 0):
        raise ValueError(i18n.t("Give the payment per period, or the term in months to work it out."))
    if payment and payment > 0:
        period_rate = rate / 100 / (12 / months)
        if principal * period_rate >= payment:
            raise ValueError(i18n.t("That payment does not even cover the interest — the loan would never end."))
    extras = []
    for line in (form.get("extras") or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            raise ValueError(i18n.f("Extra repayment {line}: write the date and the amount, like 2027-04-10 20000.", line=line))
        try:
            when = date.fromisoformat(parts[0]).isoformat()
            amount = float(parts[1].replace("'", ""))
        except ValueError:
            raise ValueError(i18n.f("Extra repayment {line}: write the date and the amount, like 2027-04-10 20000.", line=line)) from None
        extras.append({"date": when, "amount": amount})
    return {"name": name, "principal": principal, "rate_pct": rate, "first_payment": first.isoformat(),
            "period_months": months, "payment": payment if payment and payment > 0 else None,
            "term_months": int(term) if term and term > 0 else None,
            "extras": json.dumps(extras), "notes": " ".join((form.get("notes") or "").split())[:500] or None,
            "currency": (form.get("currency") or "EUR").upper()[:3]}


def add(form, person_ids=None) -> int:
    """A loan and the account that carries it, in one go."""
    from . import people
    terms = clean(form)
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO accounts (name, type, currency) VALUES (?, 'loan', ?)",
                           (terms["name"], terms["currency"]))
        account_id = int(cur.lastrowid)
        cur = conn.execute(
            "INSERT INTO loans (account_id, principal, rate_pct, first_payment, period_months, "
            "payment, term_months, extras, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (account_id, terms["principal"], terms["rate_pct"], terms["first_payment"],
             terms["period_months"], terms["payment"], terms["term_months"], terms["extras"], terms["notes"]))
        loan_id = int(cur.lastrowid)
    if person_ids:
        people.set_for_account(account_id, person_ids)
    write_balance(loan_id)
    return loan_id


def update(loan_id: int, form) -> None:
    terms = clean(form)
    loan = get(loan_id)
    if loan is None:
        raise ValueError(i18n.t("That loan does not exist."))
    with get_conn() as conn:
        conn.execute("UPDATE accounts SET name = ?, currency = ? WHERE id = ?",
                     (terms["name"], terms["currency"], loan["account_id"]))
        conn.execute(
            "UPDATE loans SET principal = ?, rate_pct = ?, first_payment = ?, period_months = ?, "
            "payment = ?, term_months = ?, extras = ?, notes = ? WHERE id = ?",
            (terms["principal"], terms["rate_pct"], terms["first_payment"], terms["period_months"],
             terms["payment"], terms["term_months"], terms["extras"], terms["notes"], loan_id))
    write_balance(loan_id)


def delete(loan_id: int) -> None:
    """The loan and its account, history included — the account exists
    for the loan, so there is nothing to keep without it."""
    loan = get(loan_id)
    if loan is None:
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM accounts WHERE id = ?", (loan["account_id"],))


def write_balance(loan_id: int, today: date | None = None) -> float | None:
    """Today's balance from the schedule onto the account, as a negative
    reading — it is money owed — unless a reading typed in by hand is
    already there for today."""
    loan = get(loan_id)
    if loan is None:
        return None
    today = today or date.today()
    owed = status(loan, today)["balance"]
    with get_conn() as conn:
        manual = conn.execute(
            "SELECT 1 FROM balances WHERE account_id = ? AND as_of = ? AND balance_type = 'manual'",
            (loan["account_id"], today.isoformat())).fetchone()
        if manual:
            return owed
        conn.execute("DELETE FROM balances WHERE account_id = ? AND as_of = ? AND balance_type = 'schedule'",
                     (loan["account_id"], today.isoformat()))
        conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                     "VALUES (?, ?, ?, 'schedule', ?)",
                     (loan["account_id"], -owed, loan["currency"], today.isoformat()))
    return owed


def write_all_balances(today: date | None = None) -> int:
    n = 0
    for loan in all_loans():
        if write_balance(loan["id"], today) is not None:
            n += 1
    return n
