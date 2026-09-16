"""Realised gains: what each sale actually made, by lots.

"Net invested" says what went in minus what came out; it does not say
what a sale made, because that depends on which units were sold and
what *they* cost. That is a lot calculation, and there are two
conventions for it — and the choice is a tax question, not a taste:

  * **FIFO** — the units sold are the oldest held. Germany taxes on
    this; Portfolio Performance shows it.
  * **Average cost** — every unit held costs the same: the weighted
    average of what was paid. France's *prix moyen pondéré* for the
    PFU. Switzerland taxes no private capital gain at all, so a Swiss
    reader can pick either and it is a curiosity.

Both are computed; Settings says which the pages show, FIFO unless
told otherwise. Neither is stored.

Lots live per account: a unit bought at one broker and one at another
are two lots even for the same ISIN, and a sale at the first cannot
consume the second's. Units that arrive without a purchase — a
transfer in, a staking reward — open a lot at the price the row
carries, or at zero when it carries none; units that leave without a
sale — a transfer out — close lots without realising anything, the
gain travels with them. The proceeds of a sale are what the broker
booked, fees included, so the gain is net of costs.
"""

from __future__ import annotations

from collections import defaultdict

from . import people, settings
from .db import get_conn

METHODS = ("fifo", "average")


def method() -> str:
    m = settings.get("gains_method", "fifo")
    return m if m in METHODS else "fifo"


def _run(rows: list[dict], how: str) -> dict:
    """Walk one account's rows for one security, in date order.

    Returns {sales, moves, open_cost, open_quantity}. `sales` is one
    entry per sale with quantity, proceeds, cost, gain; `moves` one per
    transfer out, with the cost that left with the units — what the
    receiving account books them at.
    """
    lots: list[list[float]] = []            # [quantity, cost] per lot, oldest first
    sales = []
    moves = []
    for r in rows:
        qty = r["quantity"] or 0.0
        if abs(qty) < 1e-12:
            continue
        if r["kind"] == "split":
            # More (or fewer) units, the same money: every lot scales,
            # its cost stays, and a later sale realises what it would
            # have realised in the old units.
            held = sum(l[0] for l in lots)
            if held > 1e-12:
                ratio = (held + qty) / held
                lots = [[l[0] * ratio, l[1]] for l in lots]
            continue
        if qty > 0:
            if r["kind"] == "buy":
                cost = -r["amount"]              # what left the pocket, fees included
            else:
                cost = (r["price"] or 0.0) * qty  # a transfer in, a reward
            if how == "average" and lots:
                lots[0][0] += qty
                lots[0][1] += cost
            else:
                lots.append([qty, cost])
            continue
        # Units leaving. A sale realises; a transfer out just carries the
        # lots away.
        leaving = -qty
        cost_out = 0.0
        if how == "average" and lots:
            total_q = sum(l[0] for l in lots)
            total_c = sum(l[1] for l in lots)
            take = min(leaving, total_q)
            cost_out = total_c * (take / total_q) if total_q > 1e-12 else 0.0
            remaining_q = total_q - take
            lots = [[remaining_q, total_c - cost_out]] if remaining_q > 1e-12 else []
        else:
            need = leaving
            while need > 1e-12 and lots:
                lq, lc = lots[0]
                take = min(need, lq)
                cost_out += lc * (take / lq) if lq > 1e-12 else 0.0
                if take >= lq - 1e-12:
                    lots.pop(0)
                else:
                    lots[0] = [lq - take, lc * (1 - take / lq)]
                need -= take
        if r["kind"] == "sell":
            proceeds = r["amount"]
            sales.append({"id": r["id"], "date": r["txn_date"], "account": r["account_name"],
                          "account_id": r["account_id"], "quantity": leaving,
                          "proceeds": proceeds, "cost": round(cost_out, 2),
                          "gain": round(proceeds - cost_out, 2), "currency": r["currency"],
                          "price": r["price"]})
        else:
            moves.append({"id": r["id"], "external_id": r.get("external_id"), "date": r["txn_date"],
                          "quantity": leaving, "cost": round(cost_out, 2)})
    return {"sales": sales, "moves": moves,
            "open_quantity": sum(l[0] for l in lots),
            "open_cost": round(sum(l[1] for l in lots), 2),
            "lots": [{"quantity": l[0], "cost": round(l[1], 2)} for l in lots]}


def realised(isin: str, account_ids: list[int] | None = None, how: str | None = None,
             until: str | None = None) -> dict:
    """Every sale of one security and what it made, plus what is still
    held and what it cost — under one method. `until` stops at a day,
    for what the lots were on it."""
    how = how or method()
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.*, a.name AS account_name FROM transactions t JOIN accounts a ON a.id = t.account_id "
            f"WHERE t.isin = ? AND t.quantity IS NOT NULL{only}"
            + (" AND t.txn_date <= ?" if until else "") + " ORDER BY t.txn_date, t.id",
            [isin, *params] + ([until] if until else [])).fetchall()]
    by_account: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_account[r["account_id"]].append(r)
    sales, moves, open_cost, open_qty, lots = [], [], 0.0, 0.0, []
    for acct_rows in by_account.values():
        res = _run(acct_rows, how)
        sales.extend(res["sales"])
        moves.extend(res["moves"])
        open_cost += res["open_cost"]
        open_qty += res["open_quantity"]
        lots.extend(res["lots"])
    sales.sort(key=lambda s: (s["date"], s["id"]))
    by_year: dict[str, float] = defaultdict(float)
    for s_ in sales:
        by_year[s_["date"][:4]] += s_["gain"]
    return {"method": how, "sales": sales, "moves": moves, "total": round(sum(s_["gain"] for s_ in sales), 2),
            "by_year": {y: round(v, 2) for y, v in sorted(by_year.items())},
            "open_quantity": open_qty, "open_cost": round(open_cost, 2), "lots": lots,
            "avg_cost": (open_cost / open_qty) if open_qty > 1e-12 else None}


def summary(account_ids: list[int] | None = None, how: str | None = None) -> dict:
    """Realised gains across every security ever sold, held or not —
    by year and all time, kept per currency because a sale in dollars
    and one in euros do not add up without a rate, and a realised
    gain is a tax figure that wants the currency it was booked in."""
    how = how or method()
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        isins = [r["isin"] for r in conn.execute(
            f"SELECT DISTINCT t.isin FROM transactions t WHERE t.isin IS NOT NULL "
            f"AND t.kind = 'sell'{only}", params).fetchall()]
    by_year: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total: dict[str, float] = defaultdict(float)
    per_isin = {}
    sales = 0
    for isin in isins:
        r = realised(isin, account_ids, how)
        per_isin[isin] = r["total"]
        for s_ in r["sales"]:
            ccy = s_["currency"] or "EUR"
            by_year[s_["date"][:4]][ccy] += s_["gain"]
            total[ccy] += s_["gain"]
            sales += 1
    return {"method": how, "sales": sales,
            "by_year": [{"year": y, "amounts": {c: round(v, 2) for c, v in sorted(a.items())}}
                        for y, a in sorted(by_year.items(), reverse=True)],
            "total": {c: round(v, 2) for c, v in sorted(total.items())}, "per_isin": per_isin}
