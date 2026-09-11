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

from . import i18n, people
from .db import get_conn

# The spending categories a fresh install starts with. Deliberately
# ordinary — no hobby of one household's is in here, because a category
# nobody uses still takes a colour and a row in every breakdown. Users
# add their own under Settings, and may rename, recolour or remove any
# of these; the built-ins are defaults, not a fixed list.
_BUILTIN_SPENDING = {
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
_BUILTIN_NON_SPENDING = {
    "income":     ("Income", "#34d399"),
    "investment": ("Investment", "#5b9dff"),
    "transfer":   ("Internal transfer", "#64748b"),
}

SPENDING_GROUP = "spending"
NON_SPENDING_GROUP = "non_spending"
GROUPS = (SPENDING_GROUP, NON_SPENDING_GROUP)

BUILTIN: dict[str, tuple[str, str, str]] = {
    **{slug: (name, col, SPENDING_GROUP)
       for slug, (name, col) in _BUILTIN_SPENDING.items()},
    **{slug: (name, col, NON_SPENDING_GROUP)
       for slug, (name, col) in _BUILTIN_NON_SPENDING.items()},
}

# Four slugs the code itself reasons about by name: `other` is where a
# row lands when it has no category and where a deleted category's rows
# are moved to, and cashflow.py treats `income`, `investment` and
# `transfer` specially so that moving your own money is not counted as
# spending it. They can be renamed and recoloured like any other — what
# they cannot be is deleted, because nothing would replace them.
PROTECTED = frozenset({"other", "income", "investment", "transfer"})

# Three of those four have their meaning wired into cashflow.py by name:
# income is income, investment is investment, and a transfer is neither,
# whatever group the catalogue puts them in. Offering a “counts as”
# control for them would be offering a control that does nothing, so the
# UI shows theirs as fixed and a form that says otherwise is ignored.
GROUP_LOCKED = frozenset({"income", "investment", "transfer"})


# ─── The catalogue ───────────────────────────────────────────────────
# What the user sees is the built-ins overlaid with their own edits. A
# row in `categories` either overrides a built-in (a new name, a new
# colour, hidden) or is a category of their own; either way the slug is
# the identity, and the slug is what every transaction stores. So a
# rename is a rename — it never re-files a single row — and that is why
# renaming is offered and changing a slug is not.

# The catalogue, per language code. See all_categories().
_cache: dict[str, dict[str, dict]] = {}


def invalidate() -> None:
    """Forget the cached catalogue. Called after every write."""
    _cache.clear()


def _build() -> dict[str, dict]:
    with get_conn() as conn:
        rows = {r["slug"]: dict(r) for r in
                conn.execute("SELECT * FROM categories").fetchall()}

    entries: dict[str, dict] = {}
    for slug, (name, col, group) in BUILTIN.items():
        row = rows.pop(slug, None)
        if row and row["hidden"]:
            continue
        entries[slug] = {
            "slug": slug,
            # A built-in nobody has touched is translated; one the user
            # renamed is theirs, and is shown exactly as they typed it in
            # whatever language they typed it in.
            "label": (row or {}).get("label") or i18n.t(name),
            "colour": (row or {}).get("colour") or col,
            "group": (row or {}).get("cat_group") or group,
            "builtin": True,
        }
    for slug, row in sorted(rows.items(),
                            key=lambda kv: (kv[1]["label"] or "").lower()):
        if row["hidden"]:
            continue
        entries[slug] = {
            "slug": slug, "label": row["label"], "colour": row["colour"],
            "group": row["cat_group"], "builtin": False,
        }

    # Spending first, then the rest: every page that lists categories
    # wants them in that order, and doing it once here means no page has
    # to think about it.
    return {slug: e for group in GROUPS
            for slug, e in entries.items() if e["group"] == group}


def all_categories() -> dict[str, dict]:
    """Every category in use, spending first.

    Cached — the transactions page asks once per row, and that is 400
    queries otherwise. Cached *per language*, because the labels of the
    built-ins are translated in here: one cache shared across languages
    hands a German page to the next English reader.
    """
    lang = i18n.active()
    if lang not in _cache:
        _cache[lang] = _build()
    return _cache[lang]


def spending() -> dict[str, dict]:
    return {s: e for s, e in all_categories().items()
            if e["group"] == SPENDING_GROUP}


def non_spending() -> dict[str, dict]:
    return {s: e for s, e in all_categories().items()
            if e["group"] == NON_SPENDING_GROUP}


def label(slug: str | None) -> str:
    if not slug:
        slug = "other"
    entry = all_categories().get(slug)
    if entry:
        return entry["label"]
    # A slug that no longer exists still sits on old rows; show it
    # rather than pretending the row has no category at all.
    return slug.replace("_", " ").capitalize()


def colour(slug: str | None) -> str:
    cats = all_categories()
    entry = cats.get(slug or "other") or cats.get("other")
    return entry["colour"] if entry else _BUILTIN_SPENDING["other"][1]


def usage() -> dict[str, int]:
    """How many transactions carry each slug — so the delete button can
    say what it is about to move."""
    with get_conn() as conn:
        return {r["category"]: r["n"] for r in conn.execute(
            "SELECT COALESCE(NULLIF(category, ''), 'other') AS category, "
            "       COUNT(*) AS n FROM transactions GROUP BY 1").fetchall()}


def catalogue() -> list[dict]:
    """The list the settings page edits: every category, with how many
    transactions and rules would be affected by removing it."""
    counts = usage()
    with get_conn() as conn:
        rule_counts: dict[str, int] = {r["category"]: r["n"] for r in conn.execute(
            "SELECT category, COUNT(*) AS n FROM category_rules GROUP BY 1")}
    out = []
    for entry in all_categories().values():
        out.append({**entry,
                    "transactions": counts.get(entry["slug"], 0),
                    "rules": rule_counts.get(entry["slug"], 0),
                    "deletable": entry["slug"] not in PROTECTED,
                    "group_locked": entry["slug"] in GROUP_LOCKED})
    return out


def _slugify(name: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in (name or "").lower())
    return "_".join(part for part in slug.split("_") if part)[:40]


def _clean(name: str, hex_colour: str, group: str) -> tuple[str, str, str]:
    name = (name or "").strip()
    if not name:
        raise ValueError(i18n.t("A category needs a name."))
    if len(name) > 40:
        raise ValueError(i18n.t("Keep the name under 40 characters — it has "
                                "to fit in a table cell and a chart legend."))
    hex_colour = (hex_colour or "").strip().lower()
    if not (len(hex_colour) == 7 and hex_colour[0] == "#"
            and all(c in "0123456789abcdef" for c in hex_colour[1:])):
        raise ValueError(i18n.f("{given} is not a colour like #a78bfa.",
                                given=hex_colour or i18n.t("That")))
    if group not in GROUPS:
        raise ValueError(f"Unknown group {group!r}")
    return name, hex_colour, group


def add_category(name: str, hex_colour: str,
                 group: str = SPENDING_GROUP) -> str:
    """Create a category and return its slug."""
    name, hex_colour, group = _clean(name, hex_colour, group)
    slug = _slugify(name)
    if not slug:
        raise ValueError(i18n.t("That name has no letters or digits in it, "
                                "and the name is what the internal id is "
                                "made from."))
    existing = all_categories()
    if slug in existing:
        raise ValueError(i18n.f("“{name}” already uses that name.",
                                name=existing[slug]["label"]))
    for entry in existing.values():
        if entry["label"].casefold() == name.casefold():
            raise ValueError(i18n.f("There is already a category called "
                                    "“{name}”.", name=entry["label"]))
    with get_conn() as conn:
        # A built-in the user deleted earlier is un-deleted rather than
        # duplicated: the slug is already on their old transactions, and
        # a second category with the same slug cannot exist anyway.
        conn.execute(
            "INSERT INTO categories (slug, label, colour, cat_group, hidden) "
            "VALUES (?, ?, ?, ?, 0) "
            "ON CONFLICT(slug) DO UPDATE SET label = excluded.label, "
            "  colour = excluded.colour, cat_group = excluded.cat_group, hidden = 0",
            (slug, name, hex_colour, group))
    invalidate()
    return slug


def update_category(slug: str, name: str, hex_colour: str, group: str) -> None:
    """Rename, recolour, or move a category between spending and not.

    The slug never changes, so no transaction is re-filed by an edit.
    The three slugs cashflow.py knows by name keep their group whatever
    the form asked for — see GROUP_LOCKED.
    """
    existing = all_categories()
    if slug not in existing:
        raise ValueError(f"Unknown category {slug!r}")
    if slug in GROUP_LOCKED:
        group = BUILTIN[slug][2]
    name, hex_colour, group = _clean(name, hex_colour, group)
    for other, entry in existing.items():
        if other != slug and entry["label"].casefold() == name.casefold():
            raise ValueError(i18n.f("There is already a category called "
                                    "“{name}”.", name=entry["label"]))
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO categories (slug, label, colour, cat_group, hidden) "
            "VALUES (?, ?, ?, ?, 0) "
            "ON CONFLICT(slug) DO UPDATE SET label = excluded.label, "
            "  colour = excluded.colour, cat_group = excluded.cat_group, hidden = 0",
            (slug, name, hex_colour, group))
    invalidate()


def delete_category(slug: str) -> int:
    """Remove a category and return how many transactions it held.

    Those transactions are moved to “Uncategorised” rather than left
    pointing at something that no longer exists, and the rules that
    assigned the category go with it — a rule that files into a deleted
    category would put every future import back into limbo.
    """
    cats = all_categories()
    if slug not in cats:
        raise ValueError(f"Unknown category {slug!r}")
    if slug in PROTECTED:
        raise ValueError(
            f"“{cats[slug]['label']}” is one of the four the app itself uses "
            f"to tell spending from moving your own money. Rename it or give "
            f"it another colour, but it cannot be removed.")
    with get_conn() as conn:
        moved = conn.execute(
            "UPDATE transactions SET category = 'other' WHERE category = ?",
            (slug,)).rowcount
        conn.execute("DELETE FROM category_rules WHERE category = ?", (slug,))
        conn.execute("DELETE FROM budgets WHERE category = ?", (slug,))
        if slug in BUILTIN:
            conn.execute(
                "INSERT INTO categories (slug, label, colour, cat_group, hidden) "
                "VALUES (?, ?, ?, ?, 1) "
                "ON CONFLICT(slug) DO UPDATE SET hidden = 1",
                (slug, cats[slug]["label"], cats[slug]["colour"],
                 cats[slug]["group"]))
        else:
            conn.execute("DELETE FROM categories WHERE slug = ?", (slug,))
    invalidate()
    return moved


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

# The shortest pattern a rule may have. Two characters catch half the
# database; three is where "IKE" stops matching "LIKE" often enough.
MIN_PATTERN = 3


def suggest_pattern(description: str | None,
                    counterparty: str | None = None) -> str | None:
    """The text a rule should remember this transaction by, or None.

    The counterparty is the merchant's name as the bank has it, and is
    the right answer whenever there is one. Card payments often come
    without one, and then the description is all there is — but a
    description is a merchant name buried in a booking date, a card
    number and a reference, none of which the next payment to the same
    shop will share. So: the longest run of words in it with no digit,
    and only the first few of them, which is the name and not the noise.
    """
    party = " ".join((counterparty or "").split())
    if len(party) >= MIN_PATTERN:
        return party[:40]
    words = (description or "").split()
    runs: list[list[str]] = [[]]
    for w in words:
        if any(c.isdigit() for c in w) or sum(c.isalpha() for c in w) < 2:
            runs.append([])
        else:
            runs[-1].append(w)
    best = max(runs, key=len)
    pattern = " ".join(best[:4])[:40].strip()
    return pattern if len(pattern) >= MIN_PATTERN else None


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
    if len(pattern) < MIN_PATTERN:
        raise ValueError(i18n.t("A rule needs at least three characters to "
                                "match on — anything shorter will catch "
                                "transactions you did not mean."))
    if category not in all_categories():
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


def _apply_one(conn, pattern: str, category: str, *,
               only_uncategorised: bool = False,
               account_id: int | None = None) -> int:
    sql = ("UPDATE transactions SET category = ? "
           " WHERE (LOWER(description) LIKE ? OR LOWER(COALESCE(counterparty,'')) LIKE ?)"
           "   AND kind NOT IN ('buy', 'sell')")
    params: list = [category, f"%{pattern.lower()}%", f"%{pattern.lower()}%"]
    if only_uncategorised:
        sql += " AND (category IS NULL OR category = '')"
    if account_id is not None:
        sql += " AND account_id = ?"
        params.append(account_id)
    return conn.execute(sql, params).rowcount


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
    if category not in all_categories():
        raise ValueError(f"Unknown category {category!r}")
    with get_conn() as conn:
        conn.execute("UPDATE transactions SET category = ? WHERE id = ?",
                     (category, txn_id))


def uncategorised(limit: int = 60,
                  account_ids: list[int] | None = None) -> tuple[list[dict], int]:
    """The queue. Biggest amounts first, because categorising a €900 row
    changes the picture and categorising a €1.20 one does not — and the
    queue is long enough that the order decides whether it gets used."""
    only, params = people.sql_in(account_ids, "t.account_id")
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT t.*, a.name AS account_name
              FROM transactions t JOIN accounts a ON a.id = t.account_id
             WHERE (t.category IS NULL OR t.category = '')
               AND t.kind NOT IN ('buy', 'sell', 'transfer'){only}
             ORDER BY ABS(t.amount) DESC
             LIMIT ?
            """, (*params, limit)).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) n FROM transactions t "
            f" WHERE (t.category IS NULL OR t.category = '') "
            f"   AND t.kind NOT IN ('buy','sell','transfer'){only}", params).fetchone()["n"]
    out = []
    for r in rows:
        item = dict(r)
        item["suggestion"] = suggest(item["description"], item["counterparty"])
        item["pattern"] = suggest_pattern(item["description"], item["counterparty"])
        out.append(item)
    return out, total


# What a kind means, where the kind alone settles it: a broker fee is a
# fee and an interest payment is income whatever the description says,
# so those need no rule and no human.
_KIND_CATEGORY = {
    "dividend": "income", "interest": "income",
    "fee": "fee", "tax": "tax", "transfer": "transfer",
}

# And what a kind means depending on the ACCOUNT it happened in.
#
# A deposit into a BANK account may well be salary. A deposit into a
# BROKER is your own money arriving from your own bank: internal, every
# time. Treating it as income inflates income by everything you have
# ever invested — on a real broker export that came out as €46,335
# "kept" in a period where nothing was earned at all. The bank side of
# the same movement is already booked by the bank, so counting it here
# is also counting it twice.
_KIND_CATEGORY_BY_ACCOUNT_TYPE = {
    "broker": {"deposit": "transfer", "withdrawal": "transfer"},
    "bank":   {"deposit": "income"},
    "savings": {"deposit": "transfer", "withdrawal": "transfer"},
    "card":   {},
    "other":  {},
}


def _categorise_by_kind(conn, account_id: int | None = None) -> int:
    """Rows with no category yet get one from their kind, where the
    kind settles it. Only those rows: a category somebody chose is
    never touched here."""
    scope = " AND account_id = ?" if account_id is not None else ""
    extra = (account_id,) if account_id is not None else ()
    changed = 0
    for kind, category in _KIND_CATEGORY.items():
        changed += conn.execute(
            "UPDATE transactions SET category = ? "
            " WHERE kind = ? AND (category IS NULL OR category = '')" + scope,
            (category, kind, *extra)).rowcount
    for acct_type, mapping in _KIND_CATEGORY_BY_ACCOUNT_TYPE.items():
        for kind, category in mapping.items():
            changed += conn.execute(
                "UPDATE transactions SET category = ? "
                "  WHERE kind = ? AND (category IS NULL OR category = '') "
                "    AND account_id IN (SELECT id FROM accounts WHERE type = ?)"
                + scope, (category, kind, acct_type, *extra)).rowcount
    return changed


def categorise_new(account_id: int | None = None) -> int:
    """What a row that has just arrived gets without anyone asking.

    Its kind, where the kind settles it; then the user's rules, oldest
    first so the newest wins. Only rows with no category are touched —
    a row the user filed by hand, without a rule, stays where they put
    it — and the built-in hints are left to the Categorize page's
    button, because a guess is something to be asked for.
    """
    with get_conn() as conn:
        changed = _categorise_by_kind(conn, account_id)
        for rule in conn.execute(
                "SELECT pattern, category FROM category_rules ORDER BY id ASC"):
            changed += _apply_one(conn, rule["pattern"], rule["category"],
                                  only_uncategorised=True, account_id=account_id)
    return changed


def seed_from_kind() -> int:
    """Give every row a starting category from what the importer already
    knew about it, and a guess for the rest.

    Only the rows where neither the kind nor a hint says anything — a
    card payment at a shop the hints have never heard of — reach the
    queue.
    """
    with get_conn() as conn:
        changed = _categorise_by_kind(conn)
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
