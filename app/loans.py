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

The arithmetic runs from the terms until something better comes
along: a reading of the balance that is not the schedule's own — a
bank sync, a statement, a figure typed in from the lender's letter.
From the first instalment after that reading the schedule restarts
from what the lender said, not from what the sum said, because a
rate change, a fee, a rounding rule nobody wrote down all show up in
that one number and in nothing else. The rows before it stay as
computed, so the history still has a line; the rows after it are the
lender's figure carried forward by the same arithmetic.
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
    """One row per payment: {n, date, payment, interest, capital, extra, balance}.

    `loan["anchor"]`, when the loader found one, is {date, amount}: the
    newest reading of the balance that did not come from this schedule.
    The first row dated after it starts from that amount instead of the
    computed balance and carries `anchored: True`."""
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
    anchor = loan.get("anchor") or None
    anchor_date = anchor["date"] if anchor else None
    anchored = False
    rows, balance, n = [], round(principal, 2), 0
    while n < MAX_PERIODS:
        when = _add_months(first, n * months)
        rebased = False
        if anchor_date and not anchored and when.isoformat() > anchor_date:
            balance, anchored, rebased = round(abs(float(anchor["amount"])), 2), True, True
        if balance <= 0.005:
            if anchor_date and not anchored:
                n += 1                             # the sum says paid off; the lender has not said so yet
                continue
            break
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
                     "capital": capital, "extra": round(extra, 2), "balance": balance, "anchored": rebased})
        n += 1
    return rows


def status(loan: dict, today: date | None = None) -> dict:
    """The loan as of `today`: what is owed, what was paid, what is left."""
    today = (today or date.today()).isoformat()
    rows = schedule(loan)
    done = [r for r in rows if r["date"] <= today]
    left = [r for r in rows if r["date"] > today]
    balance = done[-1]["balance"] if done else round(float(loan["principal"]), 2)
    anchor = loan.get("anchor") or None
    if anchor and anchor["date"] <= today and (not done or anchor["date"] >= done[-1]["date"]):
        # A reading since the last instalment: that is the balance,
        # today, and the page must agree with the account that holds it.
        balance = round(abs(float(anchor["amount"])), 2)
    return {
        "balance": balance,
        "anchor": anchor,
        # What the lender has been paid off, not what the sum expected
        # to have been — the two differ from the first reading on.
        "paid_capital": round(float(loan["principal"]) - balance, 2),
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

def anchor_for(conn, loan: dict, today: date | None = None) -> dict | None:
    """The newest reading of the loan's balance that is not the
    schedule's own — typed in, synced, or moved in — on or after the
    first instalment and not in the future. None when the arithmetic
    is all there is."""
    today = (today or date.today()).isoformat()
    row = conn.execute(
        "SELECT as_of, amount FROM balances WHERE account_id = ? AND balance_type != 'schedule' "
        "AND as_of >= ? AND as_of <= ? ORDER BY as_of DESC, id DESC LIMIT 1",
        (loan["account_id"], loan["first_payment"], today)).fetchone()
    return {"date": row["as_of"], "amount": abs(float(row["amount"]))} if row else None


def _with_anchor(conn, row) -> dict:
    loan = dict(row)
    loan["anchor"] = anchor_for(conn, loan)
    return loan


def all_loans(account_ids: list[int] | None = None) -> list[dict]:
    from . import people
    only, params = people.sql_in(account_ids, "l.account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT l.*, a.name, a.currency FROM loans l JOIN accounts a ON a.id = l.account_id "
            f"WHERE 1=1{only} ORDER BY a.name", params).fetchall()
        return [_with_anchor(conn, r) for r in rows]


def get(loan_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT l.*, a.name, a.currency FROM loans l JOIN accounts a "
                           "ON a.id = l.account_id WHERE l.id = ?", (loan_id,)).fetchone()
        return _with_anchor(conn, row) if row else None


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
    drawn = parse_decimal(form.get("drawn_amount"))
    drawn_ccy = (form.get("drawn_currency") or "").strip().upper()[:3]
    return {"name": name, "principal": principal, "rate_pct": rate, "first_payment": first.isoformat(),
            "period_months": months, "payment": payment if payment and payment > 0 else None,
            "term_months": int(term) if term and term > 0 else None,
            "extras": json.dumps(extras), "notes": " ".join((form.get("notes") or "").split())[:500] or None,
            "currency": (form.get("currency") or "EUR").upper()[:3],
            "drawn_amount": drawn if drawn and drawn > 0 and drawn_ccy else None,
            "drawn_currency": drawn_ccy if drawn and drawn > 0 and drawn_ccy else None}


def add(form, person_ids=None) -> int:
    """A loan and the account that carries it, in one go."""
    from . import people
    terms = clean(form)
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO accounts (name, type, currency) VALUES (?, 'loan', ?)",
                           (terms["name"], terms["currency"]))
        account_id = int(cur.lastrowid)
        loan_id = _insert(conn, account_id, terms)
    if person_ids:
        people.set_for_account(account_id, person_ids)
    write_balance(loan_id)
    write_history(loan_id)
    return loan_id


def _insert(conn, account_id: int, terms: dict) -> int:
    cur = conn.execute(
        "INSERT INTO loans (account_id, principal, rate_pct, first_payment, period_months, "
        "payment, term_months, extras, notes, drawn_amount, drawn_currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (account_id, terms["principal"], terms["rate_pct"], terms["first_payment"],
         terms["period_months"], terms["payment"], terms["term_months"], terms["extras"], terms["notes"],
         terms["drawn_amount"], terms["drawn_currency"]))
    return int(cur.lastrowid)


def attach(account_id: int, form) -> int:
    """The terms for a loan account that exists already — one moved in
    from another app with its balance readings, say — so its schedule
    can be drawn. The account keeps its name; the form's name is
    ignored, the currency follows the account."""
    with get_conn() as conn:
        account = conn.execute("SELECT id, name, type, currency FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if account is None or account["type"] != "loan":
            raise ValueError(i18n.t("That account is not a loan."))
        if conn.execute("SELECT 1 FROM loans WHERE account_id = ?", (account_id,)).fetchone():
            raise ValueError(i18n.t("That account already has its terms."))
    form = {**{k: form.get(k) for k in form.keys()}, "name": account["name"], "currency": account["currency"]}
    terms = clean(form)
    with get_conn() as conn:
        loan_id = _insert(conn, account_id, terms)
    write_balance(loan_id)
    write_history(loan_id)
    return loan_id


def for_account(account_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT l.*, a.name, a.currency FROM loans l JOIN accounts a "
                           "ON a.id = l.account_id WHERE l.account_id = ?", (account_id,)).fetchone()
        return _with_anchor(conn, row) if row else None


def detail(loan: dict, base_currency: str, today: date | None = None) -> dict:
    """Everything the loan's own page shows: the schedule, where it
    stands today, the split of every instalment, and — where the loan
    is not in the base currency — today's rate to show it at, and what
    it was drawn as."""
    from . import fx
    today = today or date.today()
    rows = schedule(loan)
    st = status(loan, today)
    rate = None
    if loan["currency"].upper() != base_currency.upper():
        one, _ = fx.convert(1.0, loan["currency"], base_currency)
        rate = one
    return {
        "schedule": rows, "status": st, "today": today.isoformat(),
        "rate": rate,                                   # base per unit of the loan's currency
        "paid_interest_total": st["total_interest"],
        "capital_total": round(sum(r["capital"] + r["extra"] for r in rows), 2),
        "first_year": loan["first_payment"][:4],
        "drawn": ({"amount": loan["drawn_amount"], "currency": loan["drawn_currency"],
                   "rate": round(float(loan["principal"]) / float(loan["drawn_amount"]), 5)}
                  if loan.get("drawn_amount") else None),
    }


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
            "payment = ?, term_months = ?, extras = ?, notes = ?, drawn_amount = ?, drawn_currency = ? WHERE id = ?",
            (terms["principal"], terms["rate_pct"], terms["first_payment"], terms["period_months"],
             terms["payment"], terms["term_months"], terms["extras"], terms["notes"],
             terms["drawn_amount"], terms["drawn_currency"], loan_id))
    write_balance(loan_id)
    write_history(loan_id)


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


def write_history(loan_id: int, today: date | None = None) -> int:
    """A reading at every instalment date already past, from the
    schedule — so the loan has a line on the history chart from its
    first payment, not from the day it was typed in here. A day that
    already has a reading is left alone."""
    loan = get(loan_id)
    if loan is None:
        return 0
    today = today or date.today()
    written = 0
    with get_conn() as conn:
        for row in schedule(loan):
            if row["date"] > today.isoformat():
                break
            if conn.execute("SELECT 1 FROM balances WHERE account_id = ? AND as_of = ?",
                            (loan["account_id"], row["date"])).fetchone():
                continue
            conn.execute("INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                         "VALUES (?, ?, ?, 'schedule', ?)",
                         (loan["account_id"], -row["balance"], loan["currency"], row["date"]))
            written += 1
    return written


def write_all_balances(today: date | None = None) -> int:
    n = 0
    for loan in all_loans():
        if write_balance(loan["id"], today) is not None:
            n += 1
    return n
