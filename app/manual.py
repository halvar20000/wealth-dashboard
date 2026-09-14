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

import re
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
DIRECTIONAL = ("transfer", "other", "split")
TRADES = ("buy", "sell")
# The kinds that can concern one security besides a trade — what the
# holding page offers, and what carries an ISIN when one is given.
ON_SECURITY = ("dividend", "interest", "fee", "tax")

# The kinds offered per account type. A trade on a current account is
# not impossible, but offering it there is offering the wrong thing to
# nine people to serve the tenth, who can set the account's type.
KINDS_FOR = {
    "broker": ("buy", "sell", "dividend", "interest", "fee", "tax",
               "deposit", "withdrawal", "transfer", "other", "split"),
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
        raw_isin = (form.get("isin") or "").strip().upper()
        isin = find_isin(raw_isin)
        if not isin and re.match(r"^CRYPTO:[A-Z0-9]{2,10}$", raw_isin):
            isin = raw_isin                      # a coin, keyed by its code
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
    # A dividend, a fee, a tax on ONE holding: the holding page adds
    # them with its ISIN, so they show among that security's rows and
    # in its income — an imported dividend does, and a typed one
    # should not be the poorer for having been typed.
    if kind in ON_SECURITY:
        raw_isin = (form.get("isin") or "").strip().upper()
        isin = find_isin(raw_isin) or (
            raw_isin if re.match(r"^CRYPTO:[A-Z0-9]{2,10}$", raw_isin) else None)
        if isin:
            row["isin"] = isin
            row["security_name"] = " ".join((form.get("security_name") or "").split())[:200] or None
    if not description:
        row["description"] = i18n.t(f"{kind} [kind]")
        if row["isin"]:
            row["description"] += f" · {row['security_name'] or row['isin']}"
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
    """Remove a row, typed in or imported.

    An imported row is the bank's word and would come back with the
    next import or sync — so its id is remembered in `removed_rows`,
    and the importers leave a remembered id out. A duplicate the bank
    booked, a corporate action the export got wrong, a row that
    belongs to somebody else: gone, and staying gone.
    """
    with get_conn() as conn:
        row = conn.execute("SELECT external_id FROM transactions WHERE id = ? AND account_id = ?",
                           (txn_id, account_id)).fetchone()
        if row is None:
            return False
        _remember_removed(conn, row["external_id"], account_id)
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    return True


def _remember_removed(conn, external_id: str | None, account_id: int | None) -> None:
    if external_id:
        conn.execute("INSERT OR IGNORE INTO removed_rows (external_id, account_id) VALUES (?, ?)",
                     (external_id, account_id))


def removed_ids(conn, account_id: int | None = None) -> set[str]:
    """The ids the user removed — what an import or a sync leaves out."""
    if account_id is None:
        return {r["external_id"] for r in conn.execute("SELECT external_id FROM removed_rows")}
    return {r["external_id"] for r in conn.execute(
        "SELECT external_id FROM removed_rows WHERE account_id = ? OR account_id IS NULL", (account_id,))}


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


# The fields a correction may touch, and nothing else: the id that
# recognises the row on the next import stays, and so do the account
# and the source.
EDITABLE = ("txn_date", "kind", "description", "counterparty", "quantity",
            "price", "amount", "fee", "tax", "security_name")


def update_transaction(txn_id: int, form) -> dict:
    """Correct a row the user says is wrong — imported or typed in.

    Editing is safe where deleting is not: a re-import recognises the
    row by its id and leaves it alone, so the corrected figures stay.
    Sizes are typed unsigned, as when adding; the kind supplies the
    sign, so a sale's quantity is stored negative and a buy's money
    negative whatever was typed. The amount is the whole cash effect —
    fees and taxes included, as the broker booked it — and is taken as
    given rather than recomputed, because the statement is the truth.
    """
    with get_conn() as conn:
        row = conn.execute("SELECT t.*, a.type AS account_type FROM transactions t "
                           "JOIN accounts a ON a.id = t.account_id WHERE t.id = ?",
                           (txn_id,)).fetchone()
    if row is None:
        raise ValueError(i18n.t("That transaction does not exist."))
    kind = (form.get("kind") or row["kind"]).strip()
    if kind not in kinds_for(row["account_type"]):
        raise ValueError(i18n.t("Pick what kind of entry this is."))
    txn_date = _date(form.get("txn_date") or row["txn_date"])
    description = " ".join((form.get("description") or "").split())[:500] or row["description"]
    counterparty = " ".join((form.get("counterparty") or "").split())[:200] or None
    name = " ".join((form.get("security_name") or "").split())[:200] or row["security_name"]

    amount = _number(form.get("amount"), i18n.t("The amount"), allow_zero=True)
    if amount is None:
        raise ValueError(i18n.t("The amount is missing."))
    if kind in _SIGN:
        amount = _SIGN[kind] * amount
    elif kind in DIRECTIONAL:
        amount = amount if (form.get("direction") or ("in" if row["amount"] >= 0 else "out")) == "in" \
            else -amount

    quantity = price = fee = tax = None
    if row["isin"]:
        quantity = _number(form.get("quantity"), i18n.t("The quantity"), allow_zero=True)
        if quantity is not None:
            if kind == "sell":
                quantity = -abs(quantity)
            elif kind == "buy":
                quantity = abs(quantity)
            elif form.get("quantity_direction") == "out":
                quantity = -abs(quantity)
            if quantity == 0:
                quantity = None
        price = _number(form.get("price"), i18n.t("The price"), allow_zero=True) or None
    fee = _number(form.get("fee"), i18n.t("The fee"), allow_zero=True) or None
    tax = _number(form.get("tax"), i18n.t("The tax"), allow_zero=True) or None

    with get_conn() as conn:
        conn.execute(
            "UPDATE transactions SET txn_date = ?, kind = ?, description = ?, "
            "counterparty = ?, security_name = ?, amount = ?, quantity = ?, price = ?, "
            "fee = ?, tax = ?, edited_at = datetime('now') WHERE id = ?",
            (txn_date, kind, description, counterparty, name, amount, quantity, price,
             fee, tax, txn_id))
    return {"id": txn_id, "txn_date": txn_date, "kind": kind, "amount": amount,
            "quantity": quantity, "price": price}


# What a patch may touch — the same fields as a correction, plus the
# security itself, because a row filed under the wrong ISIN is a row
# on the wrong holding.
PATCHABLE = ("txn_date", "kind", "description", "counterparty", "amount", "quantity",
             "price", "fee", "tax", "isin", "security_name", "category")


def patch_transactions(txn_ids: list[int], fields: dict, negate_amount: bool = False) -> list[dict]:
    """Change the given fields on the given rows, and nothing else — for
    the MCP, where the caller says exactly what is wrong. Signed
    figures are taken as given: the amount is the cash effect from
    the account's side, the quantity positive for units in. Any row,
    imported or typed: the id that recognises it on the next import
    stays, so the correction survives. Returns the rows as they are now.
    """
    from .importers.base import KINDS
    patch: dict = {}
    for key, value in (fields or {}).items():
        if key not in PATCHABLE:
            raise ValueError(i18n.f("{what} cannot be changed here.", what=key))
        if key == "txn_date":
            patch[key] = _date(value)
        elif key == "kind":
            if value not in KINDS:
                raise ValueError(i18n.t("Pick what kind of entry this is."))
            patch[key] = value
        elif key in ("amount", "quantity", "price", "fee", "tax"):
            if value is None or value == "":
                patch[key] = None
            else:
                num = parse_decimal(str(value))
                if num is None:
                    raise ValueError(i18n.f("{what} is not a number.", what=key))
                patch[key] = num
            if key == "amount" and patch[key] is None:
                raise ValueError(i18n.t("The amount is missing."))
        elif key == "isin":
            isin = find_isin((value or "").upper()) or (value if value and str(value).upper().startswith("CRYPTO:") else None)
            patch[key] = isin
        elif key == "category":
            if value and value not in categories.all_categories():
                raise ValueError(f"Unknown category {value!r}")
            patch[key] = value or None
        else:
            patch[key] = " ".join(str(value or "").split())[:500] or None
    if not patch and not negate_amount:
        raise ValueError(i18n.t("Nothing to change."))
    ids = [int(i) for i in txn_ids]
    out = []
    with get_conn() as conn:
        for txn_id in ids:
            row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
            if row is None:
                raise ValueError(i18n.f("Transaction {id} does not exist.", id=txn_id))
            sets = dict(patch)
            if negate_amount:
                sets["amount"] = -(sets.get("amount", row["amount"]))
            if "description" in sets and sets["description"] is None:
                sets["description"] = row["description"]
            cols = ", ".join(f"{k} = ?" for k in sets)
            conn.execute(f"UPDATE transactions SET {cols}, edited_at = datetime('now') WHERE id = ?",
                         [*sets.values(), txn_id])
            out.append(dict(conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()))
    return out


def delete_transactions(txn_ids: list[int]) -> int:
    """Remove rows, whatever their source — for the MCP, where the
    caller has looked at them. Remembered by id, as delete_transaction
    does, so a re-import does not bring them back."""
    ids = [int(i) for i in txn_ids]
    if not ids:
        return 0
    marks = ",".join("?" * len(ids))
    with get_conn() as conn:
        for r in conn.execute(f"SELECT external_id, account_id FROM transactions WHERE id IN ({marks})", ids):
            _remember_removed(conn, r["external_id"], r["account_id"])
        cur = conn.execute(f"DELETE FROM transactions WHERE id IN ({marks})", ids)
        return cur.rowcount
