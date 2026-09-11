"""Transactions and balances typed in by hand.

Not every account has an API, and not every broker exports a CSV. A
pension, a share plan at work, a savings account at a bank that is not
in Enable Banking's list, a crypto exchange — the money is real and the
dashboard is wrong without it. So a row can be typed in, and it lands in
the same table in the same shape as an imported one: a hand-entered
purchase counts toward the holding, a hand-entered dividend is income,
and nothing downstream knows or cares where the row came from. `source`
says `manual`, which is what lets the account page offer to delete it —
an imported row would only come back on the next import, so those stay.

The sign of the amount is decided by the kind, not typed. Money into
the account is positive everywhere in this app, and a person entering a
fee does not think of it as "minus twelve"; they think of it as a fee.
Only a transfer or an "other" row needs a direction said out loud.

A balance is a reading, not a sum: this app never derives a balance from
transactions, because a statement is the truth and the transactions are
only ever a subset of it. Typing one in is the same as a bank reporting
one, dated the day it was true.
"""

from __future__ import annotations

from datetime import date

from . import categories, i18n
from .db import get_conn
from .importers.base import find_isin, parse_decimal

SOURCE = "manual"

# What each kind does to the cash in the account. A kind with a fixed
# sign takes the size the user typed and applies it; the two without one
# ask for a direction.
_SIGN = {
    "deposit": +1, "dividend": +1, "interest": +1, "sell": +1,
    "withdrawal": -1, "fee": -1, "tax": -1, "buy": -1,
}
DIRECTIONAL = ("transfer", "other")
TRADES = ("buy", "sell")

# The kinds offered per account type. A trade on a current account is
# not impossible, but offering it there is offering the wrong thing to
# nine people to serve the tenth, who can set the account's type.
KINDS_FOR = {
    "broker": ("buy", "sell", "dividend", "interest", "fee", "tax",
               "deposit", "withdrawal", "transfer", "other"),
    "default": ("deposit", "withdrawal", "interest", "fee", "tax",
                "transfer", "other"),
}


def kinds_for(account_type: str) -> tuple[str, ...]:
    return KINDS_FOR.get(account_type, KINDS_FOR["default"])


def _number(raw: str | None, what: str, *, allow_zero: bool = False) -> float | None:
    """A positive number from whatever the user typed, or None if blank.
    Sizes are typed unsigned; the kind supplies the sign."""
    value = parse_decimal(raw)
    if value is None:
        return None
    value = abs(value)
    if value == 0 and not allow_zero:
        raise ValueError(i18n.f("{what} cannot be zero.", what=what))
    return value


def _date(raw: str | None) -> str:
    raw = (raw or "").strip()
    try:
        when = date.fromisoformat(raw)
    except ValueError:
        raise ValueError(i18n.t("The date needs to be a real day, "
                                "written year-month-day.")) from None
    if when > date.today():
        raise ValueError(i18n.t("That date is in the future. A transaction "
                                "is something that happened."))
    return when.isoformat()


def clean_transaction(account: dict, form) -> dict:
    """Turn the form into a row, or raise ValueError with a sentence.

    Everything the row will carry is decided here, so the insert below
    is a plain insert and a test can check the row without a browser.
    """
    kind = (form.get("kind") or "").strip()
    if kind not in kinds_for(account["type"]):
        raise ValueError(i18n.t("Pick what kind of entry this is."))
    txn_date = _date(form.get("txn_date"))
    description = " ".join((form.get("description") or "").split())[:500]
    counterparty = " ".join((form.get("counterparty") or "").split())[:200] or None
    category = (form.get("category") or "").strip() or None
    if category and category not in categories.all_categories():
        raise ValueError(f"Unknown category {category!r}")

    row = {
        "account_id": account["id"], "txn_date": txn_date,
        "description": description, "counterparty": counterparty,
        "currency": account["currency"], "kind": kind, "category": category,
        "isin": None, "security_name": None, "quantity": None,
        "price": None, "fee": None, "tax": None, "source": SOURCE,
    }

    if kind in TRADES:
        isin = find_isin(form.get("isin"))
        if not isin:
            raise ValueError(i18n.t("A trade needs the security's ISIN — two "
                                    "letters and ten characters, like "
                                    "IE00B4L5Y983. It is on the order "
                                    "confirmation, and it is how the same fund "
                                    "at two brokers is recognised as one "
                                    "holding."))
        quantity = _number(form.get("quantity"), i18n.t("The quantity"))
        price = _number(form.get("price"), i18n.t("The price"))
        if quantity is None or price is None:
            raise ValueError(i18n.t("A trade needs a quantity and a price "
                                    "per unit."))
        fee = _number(form.get("fee"), i18n.t("The fee"), allow_zero=True) or 0.0
        tax = _number(form.get("tax"), i18n.t("The tax"), allow_zero=True) or 0.0
        # The total the broker actually took or paid, if the user has
        # it — a broker's total rarely equals quantity × price to the
        # cent, and the statement is the truth. Otherwise, computed.
        total = _number(form.get("total"), i18n.t("The total"))
        if total is None:
            total = quantity * price + (fee + tax) * (1 if kind == "buy" else -1)
        name = " ".join((form.get("security_name") or "").split())[:200] or None
        row.update({
            "isin": isin, "security_name": name,
            "quantity": quantity if kind == "buy" else -quantity,
            "price": price, "fee": fee or None, "tax": tax or None,
            "amount": -total if kind == "buy" else total,
        })
        if not description:
            shown = i18n.qty(quantity, i18n.active())
            row["description"] = (
                i18n.f("Bought {qty} × {name}", qty=shown, name=name or isin)
                if kind == "buy" else
                i18n.f("Sold {qty} × {name}", qty=shown, name=name or isin))
        return row

    amount = _number(form.get("amount"), i18n.t("The amount"))
    if amount is None:
        raise ValueError(i18n.t("The amount is missing."))
    if kind in DIRECTIONAL:
        direction = form.get("direction") or "out"
        sign = +1 if direction == "in" else -1
    else:
        sign = _SIGN[kind]
    row["amount"] = sign * amount
    if not description:
        row["description"] = i18n.t(f"{kind} [kind]")
    return row


def add_transaction(account: dict, form) -> int:
    """Store one hand-entered row and return its id.

    A row with no category picked gets one the way an imported row does:
    from its kind where the kind settles it, from the user's rules where
    one matches. A hand-entered dividend should not need a human to say
    it is income.
    """
    row = clean_transaction(account, form)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO transactions (account_id, txn_date, description, "
            " counterparty, amount, currency, kind, category, isin, "
            " security_name, quantity, price, fee, tax, source) "
            "VALUES (:account_id, :txn_date, :description, :counterparty, "
            " :amount, :currency, :kind, :category, :isin, :security_name, "
            " :quantity, :price, :fee, :tax, :source)", row)
        txn_id = int(cur.lastrowid)
    if not row["category"]:
        categories.categorise_new(account["id"])
    return txn_id


def delete_transaction(account_id: int, txn_id: int) -> bool:
    """Remove a hand-entered row. Only those: an imported row is the
    bank's word, and deleting it would only hide it until the next
    sync put it back."""
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM transactions WHERE id = ? AND account_id = ? "
            "AND source = ?", (txn_id, account_id, SOURCE))
        return cur.rowcount > 0


def set_balance(account: dict, form) -> dict:
    """Record the balance as of a day. Returns the reading stored."""
    amount = parse_decimal(form.get("amount"))
    if amount is None:
        raise ValueError(i18n.t("The balance is missing."))
    as_of = _date(form.get("as_of"))
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO balances (account_id, amount, currency, balance_type, "
            "as_of) VALUES (?, ?, ?, ?, ?)",
            (account["id"], amount, account["currency"], SOURCE, as_of))
    return {"amount": amount, "currency": account["currency"], "as_of": as_of}
