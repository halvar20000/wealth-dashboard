"""Stock splits: 44 new units for 1 old, and nothing else changed.

A split is the one event that makes every earlier row of a holding
look wrong without any of them being wrong: 0.4753 units at 420.79
before, 21.57 units at 9.27 after, and a running quantity that adds
the two as if they were the same thing. The brokers' exports do not
carry it — DKB's Abrechnungen say what was bought, not what was
renamed — so it is recorded by hand, once, on the security's page.

It is stored as a row like any other: kind `split`, quantity the
units that appeared (or vanished, for a reverse split), amount zero,
one row per account holding the security that day — a lot never
crosses a depot. A holding's quantity is still the sum of its rows;
the security page still shows every row; a correction still edits
it. What the row changes is how the *earlier* rows are read:

  * A market price is quoted in today's units — Yahoo's history is
    split-adjusted — so a day before the split is valued at the units
    held then times the ratio of every split since. `factors()` says
    by how much, per row.
  * A lot keeps its cost and gets more units, so the average cost
    per unit falls by the ratio and the realised gain of a later
    sale is unchanged by the split — see gains.py.
  * Net invested, income and the money flows do not change: nothing
    was paid and nothing was received.
"""

from __future__ import annotations

import re
from datetime import date

from . import i18n
from .db import get_conn

KIND = "split"
_RATIO_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(?:[:/]\s*(\d+(?:[.,]\d+)?))?\s*$")


def parse_ratio(text: str | None) -> tuple[float, float]:
    """"44:1" → (44, 1); "44" → (44, 1); "1:10" → (1, 10) — new for old."""
    m = _RATIO_RE.match(text or "")
    if not m:
        raise ValueError(i18n.t("Write the split as new for old, like 44:1 — or 1:10 for a reverse split."))
    new = float(m.group(1).replace(",", "."))
    old = float(m.group(2).replace(",", ".")) if m.group(2) else 1.0
    if new <= 0 or old <= 0 or new == old:
        raise ValueError(i18n.t("Write the split as new for old, like 44:1 — or 1:10 for a reverse split."))
    return new, old


def factors(rows: list) -> list[float]:
    """For rows of one holding in date order (each with `kind` and
    `quantity`), the factor that turns the units held after row i into
    today's units: the product of the ratios of every split after it.
    1.0 everywhere when there is no split."""
    running = 0.0
    ratios = []
    for r in rows:
        q = r["quantity"] or 0.0
        if r["kind"] == KIND and abs(running) > 1e-12:
            ratios.append((running + q) / running)
        else:
            ratios.append(1.0)
        running += q
    out = [1.0] * len(rows)
    acc = 1.0
    for i in range(len(rows) - 1, -1, -1):
        out[i] = acc
        acc *= ratios[i]
    return out


def record(isin: str, when: str, ratio_text: str, account_ids: list[int] | None = None) -> list[dict]:
    """One `split` row per account holding the security on `when`.
    Returns what was written; an empty list means nothing was held."""
    from . import people
    new, old = parse_ratio(ratio_text)
    try:
        day = date.fromisoformat((when or "").strip())
    except ValueError:
        raise ValueError(i18n.t("The date needs to be a real day, written year-month-day.")) from None
    if day > date.today():
        raise ValueError(i18n.t("That date is in the future. A transaction is something that happened."))
    ratio = new / old
    only, params = people.sql_in(account_ids, "account_id")
    label = f"{new:g}:{old:g}"
    written = []
    with get_conn() as conn:
        held = conn.execute(
            f"SELECT account_id, currency, MAX(security_name) AS name, SUM(quantity) AS q "
            f"FROM transactions WHERE isin = ? AND quantity IS NOT NULL AND txn_date <= ?{only} "
            f"GROUP BY account_id", [isin, day.isoformat(), *params]).fetchall()
        for h in held:
            if not h["q"] or abs(h["q"]) < 1e-12:
                continue
            extra = h["q"] * (ratio - 1.0)
            cur = conn.execute(
                "INSERT OR IGNORE INTO transactions (account_id, txn_date, description, amount, currency, "
                "kind, isin, security_name, quantity, external_id, source) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 'manual')",
                (h["account_id"], day.isoformat(), f"Split {label}", h["currency"], KIND, isin,
                 h["name"], extra, f"split:{isin}:{h['account_id']}:{day.isoformat()}"))
            if cur.rowcount:
                written.append({"account_id": h["account_id"], "quantity": extra, "ratio": ratio})
    return written
