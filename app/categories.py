"""Categories, and the rules that assign them.

A transaction arrives with a description, a counterparty and nothing
else. Turning that into "food" or "insurance" is the work that makes Cash
Flow, Budget and everything downstream mean anything, and it is work no
importer can do — the same string means different things to different
households.

So: the user categorises, and **a correction becomes a rule**. The rule
applies to what is already in the database as well as to what arrives
next, because a rule that only works going forwards makes you fix the
same shop every month for a year before it stops.

Rules match on a substring of the description or counterparty, and the
newest matching rule wins. Not a regex: a rule the user cannot read is a
rule they cannot correct, and this list is meant to be looked at.
"""

from __future__ import annotations

from .db import get_conn

# The spending categories. Deliberately ordinary — no hobby of one
# household's is in here, because a category nobody uses still takes a
# colour and a row in every breakdown. Users add their own.
SPENDING = {
    "housing":        ("Housing", "#a78bfa"),
    "food":           ("Groceries", "#f5d76e"),
    "restaurants":    ("Restaurants & bars", "#f43f5e"),
    "transport":      ("Transport", "#22d3ee"),
    "car":            ("Car", "#7c3aed"),
    "travel":         ("Travel", "#8b5cf6"),
    "shopping":       ("Shopping", "#fb7185"),
    "subscription":   ("Subscriptions", "#c084fc"),
    "health":         ("Health", "#84cc16"),
    "insurance":      ("Insurance", "#0891b2"),
    "education":      ("Education", "#38bdf8"),
    "entertainment":  ("Entertainment", "#e879f9"),
    "fee":            ("Fees", "#94a3b8"),
    "tax":            ("Tax", "#facc15"),
    "cash_withdrawal": ("Cash withdrawal", "#fde047"),
    "other":          ("Uncategorised", "#5e6a86"),
}

# Not spending. The distinction is what stops a transfer between your own
# accounts from being counted as money you spent — and counted twice,
# once on each side.
NON_SPENDING = {
    "income":     ("Income", "#34d399"),
    "investment": ("Investment", "#5b9dff"),
    "transfer":   ("Internal transfer", "#64748b"),
}

ALL = {**SPENDING, **NON_SPENDING}


def label(slug: str | None) -> str:
    if not slug:
        return SPENDING["other"][0]
    if slug in ALL:
        return ALL[slug][0]
    return slug.replace("_", " ").capitalize()


def colour(slug: str | None) -> str:
    return ALL.get(slug or "other", SPENDING["other"])[1]


# ─── Built-in hints ──────────────────────────────────────────────────
# A starting guess so a new install is not a wall of "uncategorised".
# Deliberately short and international: a long list of one country's
# supermarket chains is a long list of names that are wrong everywhere
# else. The user's own rules are what make this accurate; these only
# save the first hour.

_HINTS: list[tuple[str, str]] = [
    ("supermarket", "food"), ("supermarch", "food"), ("grocer", "food"),
    ("aldi", "food"), ("lidl", "food"), ("carrefour", "food"),
    ("rewe", "food"), ("edeka", "food"), ("migros", "food"), ("coop", "food"),
    ("restaurant", "restaurants"), ("cafe", "restaurants"),
    ("bar ", "restaurants"), ("pizza", "restaurants"), ("mcdonald", "restaurants"),
    ("uber eats", "restaurants"), ("deliveroo", "restaurants"),
    ("pharmac", "health"), ("apothe", "health"), ("doctor", "health"),
    ("medic", "health"), ("dentist", "health"), ("hospital", "health"),
    ("insur", "insurance"), ("assuran", "insurance"), ("versicher", "insurance"),
    ("netflix", "subscription"), ("spotify", "subscription"),
    ("disney", "subscription"), ("amazon prime", "subscription"),
    ("icloud", "subscription"), ("google one", "subscription"),
    ("microsoft 365", "subscription"), ("adobe", "subscription"),
    ("fuel", "car"), ("petrol", "car"), ("essence", "car"), ("tankstelle", "car"),
    ("shell", "car"), ("total energ", "car"), ("parking", "car"), ("garage", "car"),
    ("railway", "transport"), ("sncf", "transport"), ("db bahn", "transport"),
    ("bahn", "transport"), ("bus ", "transport"), ("metro", "transport"),
    ("taxi", "transport"), ("uber", "transport"),
    ("hotel", "travel"), ("airbnb", "travel"), ("booking.com", "travel"),
    ("airline", "travel"), ("ryanair", "travel"), ("lufthansa", "travel"),
    ("easyjet", "travel"),
    ("rent", "housing"), ("loyer", "housing"), ("miete", "housing"),
    ("mortgage", "housing"), ("electric", "housing"), ("energie", "housing"),
    ("water", "housing"), ("internet", "housing"), ("telecom", "housing"),
    ("salary", "income"), ("salaire", "income"), ("gehalt", "income"),
    ("payroll", "income"), ("pension", "income"),
    ("atm", "cash_withdrawal"), ("cash withdrawal", "cash_withdrawal"),
    ("retrait", "cash_withdrawal"), ("bargeld", "cash_withdrawal"),
    ("tax", "tax"), ("impot", "tax"), ("steuer", "tax"), ("urssaf", "tax"),
    ("fee", "fee"), ("frais", "fee"), ("commission", "fee"),
]


def suggest(description: str | None, counterparty: str | None = None) -> str | None:
    """A first guess, or None. Never overrides a stored category."""
    text = f"{description or ''} {counterparty or ''}".lower()
    for needle, category in _HINTS:
        if needle in text:
            return category
    return None


# ─── Rules ───────────────────────────────────────────────────────────

def rules(conn=None) -> list[dict]:
    def _read(c):
        return [dict(r) for r in c.execute(
            "SELECT * FROM category_rules ORDER BY id DESC").fetchall()]
    if conn is not None:
        return _read(conn)
    with get_conn() as c:
        return _read(c)


def add_rule(pattern: str, category: str) -> int:
    """Store a rule and apply it to everything already imported.

    Applying retroactively is the point. A rule that only affects future
    imports means correcting the same merchant every month until the
    year is out, and people stop correcting long before that.
    """
    pattern = (pattern or "").strip()
    if len(pattern) < 3:
        raise ValueError("A rule needs at least three characters to match on — "
                         "anything shorter will catch transactions you did not "
                         "mean.")
    if category not in ALL:
        raise ValueError(f"Unknown category {category!r}")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO category_rules (pattern, category) VALUES (?, ?)",
            (pattern, category))
        applied = _apply_one(conn, pattern, category)
    return applied


def delete_rule(rule_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM category_rules WHERE id = ?", (rule_id,))


def _apply_one(conn, pattern: str, category: str) -> int:
    cur = conn.execute(
        "UPDATE transactions SET category = ? "
        " WHERE (LOWER(description) LIKE ? OR LOWER(COALESCE(counterparty,'')) LIKE ?)"
        "   AND kind NOT IN ('buy', 'sell')",
        (category, f"%{pattern.lower()}%", f"%{pattern.lower()}%"))
    return cur.rowcount


def apply_all() -> int:
    """Re-run every rule, oldest first, so the newest rule wins on a
    transaction that two rules both match."""
    with get_conn() as conn:
        total = 0
        for rule in conn.execute(
                "SELECT pattern, category FROM category_rules ORDER BY id ASC"):
            total += _apply_one(conn, rule["pattern"], rule["category"])
    return total


def set_category(txn_id: int, category: str) -> None:
    if category not in ALL:
        raise ValueError(f"Unknown category {category!r}")
    with get_conn() as conn:
        conn.execute("UPDATE transactions SET category = ? WHERE id = ?",
                     (category, txn_id))


def uncategorised(limit: int = 60) -> list[dict]:
    """The queue. Biggest amounts first, because categorising a €900 row
    changes the picture and categorising a €1.20 one does not — and the
    queue is long enough that the order decides whether it gets used."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT t.*, a.name AS account_name
              FROM transactions t JOIN accounts a ON a.id = t.account_id
             WHERE (t.category IS NULL OR t.category = '')
               AND t.kind NOT IN ('buy', 'sell', 'transfer')
             ORDER BY ABS(t.amount) DESC
             LIMIT ?
            """, (limit,)).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) n FROM transactions "
            " WHERE (category IS NULL OR category = '') "
            "   AND kind NOT IN ('buy','sell','transfer')").fetchone()["n"]
    out = []
    for r in rows:
        item = dict(r)
        item["suggestion"] = suggest(item["description"], item["counterparty"])
        out.append(item)
    return out, total


def seed_from_kind() -> int:
    """Give every row a starting category from what the importer already
    knew about it.

    A broker fee is a fee and an interest payment is income whatever the
    description says, so those need no rule and no human. Only the rows
    where the kind says nothing — a card payment, a transfer out — reach
    the queue.
    """
    # What a kind means depends on the ACCOUNT it happened in.
    #
    # A deposit into a BANK account may well be salary. A deposit into a
    # BROKER is your own money arriving from your own bank: internal,
    # every time. Treating it as income inflates income by everything you
    # have ever invested — on a real broker export that came out as
    # €46,335 "kept" in a period where nothing was earned at all. The
    # bank side of the same movement is already booked by the bank, so
    # counting it here is also counting it twice.
    common = {
        "dividend": "income", "interest": "income",
        "fee": "fee", "tax": "tax", "transfer": "transfer",
    }
    by_account_type = {
        "broker": {"deposit": "transfer", "withdrawal": "transfer"},
        "bank":   {"deposit": "income"},
        "savings": {"deposit": "transfer", "withdrawal": "transfer"},
        "card":   {},
        "other":  {},
    }
    with get_conn() as conn:
        changed = 0
        for kind, category in common.items():
            changed += conn.execute(
                "UPDATE transactions SET category = ? "
                " WHERE kind = ? AND (category IS NULL OR category = '')",
                (category, kind)).rowcount
        for acct_type, mapping in by_account_type.items():
            for kind, category in mapping.items():
                changed += conn.execute(
                    "UPDATE transactions SET category = ? "
                    "  WHERE kind = ? AND (category IS NULL OR category = '') "
                    "    AND account_id IN (SELECT id FROM accounts WHERE type = ?)",
                    (category, kind, acct_type)).rowcount
        # A guess for the rest, marked as a guess by leaving it in the
        # queue is not possible — so hints are applied but the row is
        # still counted as categorised. The user can correct it, which is
        # what the rules are for.
        for row in conn.execute(
                "SELECT id, description, counterparty FROM transactions "
                " WHERE (category IS NULL OR category = '') "
                "   AND kind NOT IN ('buy','sell')").fetchall():
            guess = suggest(row["description"], row["counterparty"])
            if guess:
                conn.execute("UPDATE transactions SET category = ? WHERE id = ?",
                             (guess, row["id"]))
                changed += 1
    return changed
