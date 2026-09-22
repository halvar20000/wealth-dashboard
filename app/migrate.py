"""Moving in: the books of another app, brought over in one go.

The first supported source is Financial Planner — the private Flask
dashboard this app grew out of — whose `wealth.db` holds accounts,
a ledger, holdings, daily per-position snapshots and price history.
Reading it is two steps, so the user sees what will happen before it
does: `read()` turns the file into a plan — every account of theirs
with what it maps to here, every row, every balance, every opening
position that has to be written so the holdings agree — and
`apply()` writes the plan, into accounts the user chose or new ones.

What crosses, and how:

* **Accounts** by type: bank, savings and broker as they are; crypto
  as a broker whose coins are `CRYPTO:<code>` holdings; a mortgage as a
  loan; pension, P2P and property as themselves. An account of the
  same name here is offered as the target, so a broker already
  connected is not created twice.
* **Rows** as they are, with their ids: a Trade Republic or Saxo id is
  the same string in both apps, so a later import here recognises the
  row; a Kraken trade id gets this app's prefix; the rest keep the id
  they had, and the only cost is that an export from *before* the move
  must not be re-imported here — a later one is fine.
* **Holdings** are recomputed from the rows, and where the two differ —
  a position set from a statement rather than built from trades — an
  opening row makes up the difference, dated before the first row of
  that holding, at the cost the old app carried, so the cost basis
  survives. Each one is listed in the plan.
* **Balances**: every daily snapshot line of cash, a pension, a loan, a
  house becomes a balance reading of that day, so the history chart
  reaches back as far as the snapshots do. The last holdings give a
  reading of today.
* **Prices** by ISIN, so a chart has history before the first refresh
  here; and each security's symbol, kept as the user's own.
* **Categories**: a slug both apps know is used; one only the old app
  had is created, as spending, under a readable name; `interest` is
  this app's "Interest & dividends".

What does not cross, and why: aggregate net-worth snapshots from before
the old app wrote per-position lines (no account to hang them on);
per-row expense owners and retirement flags (nothing here to read
them yet); the old app's FX table (the ECB history is fetched whole).
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import date, timedelta

import re

from . import categories, importers
from .db import get_conn
from .importers.base import find_isin

SOURCE = "financial_planner"
SQLITE_MAGIC = b"SQLite format 3\x00"

# Financial Planner's account types → this app's.
TYPE_MAP = {"bank": "bank", "savings": "savings", "broker": "broker", "crypto": "broker",
            "mortgage": "loan", "pension": "pension", "p2p": "p2p", "real_estate": "property",
            "private_equity": "other", "other": "other", "card": "card"}

# Category slugs that mean the same thing under another name here.
CATEGORY_MAP = {"interest": "capital_income", "assurance": "insurance"}

_QUANTITY_KINDS = ("buy", "sell", "transfer", "split")

# Id prefixes this app's own importers produce in exactly the old app's
# shape. An account whose rows all carry one of these needs no
# ledger_until: a re-import recognises every row by its id.
SHARED_ID_PREFIXES = tuple(p for p in importers.SHARED_ID_PREFIXES if p != "fp:")
_KRAKEN_TXID = re.compile(r"^[A-Z0-9]{6}-[A-Z0-9]{5}-[A-Z0-9]{6}$")


def is_planner_db(content: bytes) -> bool:
    return content.startswith(SQLITE_MAGIC) and b"snapshot_lines" in content and b"holdings" in content


def _open(content: bytes) -> tuple[sqlite3.Connection, str]:
    fd, path = tempfile.mkstemp(suffix=".db")
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn, path


def _asset_key(asset: dict | None) -> str | None:
    """How this app keys the holding: the ISIN; a coin as CRYPTO:<code>;
    a fund with no ISIN by its ticker. Cash is not a holding, and nor
    is a house — that is an account with a value, not units at a price."""
    if not asset or (asset.get("asset_class") or "") in ("cash", "real_estate"):
        return None
    ticker = (asset.get("ticker") or "").upper()
    if ticker.startswith("CASH_"):
        return None
    if (asset.get("asset_class") or "") == "crypto":
        code = ticker
        ccy = (asset.get("currency") or "").upper()
        if ccy and code.endswith(ccy) and len(code) > len(ccy):
            code = code[:-len(ccy)]
        return f"CRYPTO:{code}"
    isin = (asset.get("isin") or "").strip().upper()
    if isin:
        return isin
    return f"SYM:{ticker}" if ticker else None


def _external_id(raw: str | None, source: str | None, fp_id: int) -> str:
    """The old app's id, in this app's shape where the two importers
    would otherwise disagree about the same row."""
    raw = (raw or "").strip()
    if not raw:
        return f"fp:{fp_id}"
    if _KRAKEN_TXID.match(raw) or ((source or "").startswith("kraken_api") and ":" not in raw):
        return f"kraken:trade:{raw}"     # from the API or from a Kraken CSV alike
    if raw.startswith("ca_ch:"):
        return "ca-ch:" + raw[6:]
    return raw


_TICKER_IN_TEXT = re.compile(r"\b(?:BUY|SELL)\s+-?[\d.,]+\s+([A-Z0-9_.-]{1,12}):", re.I)


def _infer_key(description: str | None, by_ticker: dict[str, str]) -> str | None:
    """The security a trade row concerns when the old app did not link
    one: an ISIN in the text, or a `BUY 594.0 DCAM:xpar` ticker."""
    text = description or ""
    isin = find_isin(text)
    if isin:
        return isin
    m = _TICKER_IN_TEXT.search(text)
    if m:
        return by_ticker.get(m.group(1).upper())
    return None


def _category(slug: str | None, known: dict[str, dict], to_create: dict[str, str]) -> str | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    slug = CATEGORY_MAP.get(slug, slug)
    if slug in known:
        return slug
    to_create.setdefault(slug, slug.replace("_", " ").strip().capitalize())
    return slug


def _owner_key(raw: str | None) -> str | None:
    """The old app's owner as this app names it: "shared" for common,
    else the name as a title-cased word — "marie_ange" → "Marie-Ange"."""
    raw = (raw or "").strip().lower()
    if not raw:
        return None
    if raw in ("common", "shared", "both", "household"):
        return "shared"
    return "-".join(part.capitalize() for part in re.split(r"[_\s]+", raw) if part)


def _match_person(name: str, persons: list[dict]) -> int | None:
    """A person here whose name is the old app's owner — letters only,
    case aside, so Marie-Ange, marie_ange and Marie Ange are one."""
    key = re.sub(r"[^a-z]", "", name.lower())
    for p in persons:
        if re.sub(r"[^a-z]", "", p["name"].lower()) == key:
            return p["id"]
    return None


def read_rules(content: bytes) -> list[dict]:
    """The old app's category_rules.json: [{pattern, category}]."""
    import json
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return []
    rules = data.get("rules") if isinstance(data, dict) else data
    out = []
    for r in rules or []:
        if isinstance(r, dict) and r.get("match") and r.get("category"):
            out.append({"pattern": " ".join(str(r["match"]).split())[:200], "category": str(r["category"])})
    return out


def attach_rules(plan: dict, content: bytes) -> int:
    """The old app's category rules onto a plan: their categories
    mapped the way the rows' were, made here when missing. Returns
    how many rules the file held."""
    known = categories.all_categories()
    rules = []
    for r in read_rules(content):
        cat = _category(r["category"], known, plan["categories"])
        if cat:
            rules.append({"pattern": r["pattern"], "category": cat})
    plan["category_rules"] = rules
    if rules:
        plan["notes"].append(f"{len(rules)} category rules from category_rules.json come along and apply to what is here.")
    return len(rules)


def read(content: bytes) -> dict:
    """The plan: what the file holds and what would be written. Nothing
    is written. `accounts` carries, per old account, a `target` — the
    id of an account here with the same name, or None for a new one —
    which the page lets the user change before apply()."""
    conn, path = _open(content)
    try:
        return _read(conn)
    finally:
        conn.close()
        try:
            os.unlink(path)
        except OSError:
            pass


def _read(src: sqlite3.Connection) -> dict:
    plan: dict = {"accounts": [], "transactions": [], "balances": [], "securities": [],
                  "prices": [], "openings": [], "categories": {}, "notes": []}
    with get_conn() as conn:
        existing = {r["name"].strip().casefold(): dict(r) for r in
                    conn.execute("SELECT id, name, type, currency FROM accounts")}
        existing_ids = {r["external_id"] for r in
                        conn.execute("SELECT external_id FROM transactions WHERE external_id IS NOT NULL")}
        held = {}
        for r in conn.execute("SELECT account_id, isin, SUM(COALESCE(quantity, 0)) AS q FROM transactions "
                              "WHERE isin IS NOT NULL AND quantity IS NOT NULL GROUP BY account_id, isin"):
            held[(r["account_id"], r["isin"])] = r["q"]
    known_cats = categories.all_categories()

    assets = {r["id"]: dict(r) for r in src.execute("SELECT * FROM assets")}
    keys = {aid: _asset_key(a) for aid, a in assets.items()}
    by_ticker = {(a.get("ticker") or "").upper(): keys[aid] for aid, a in assets.items() if keys.get(aid)}
    names = {keys[aid]: a.get("name") for aid, a in assets.items() if keys.get(aid)}
    # An old account of any type that holds securities is a broker here.
    holdings = src.execute("SELECT * FROM holdings").fetchall()
    holds_securities = {h["account_id"] for h in holdings if keys.get(h["asset_id"]) and abs(h["quantity"] or 0) > 1e-9}

    accounts = [dict(r) for r in src.execute("SELECT * FROM accounts ORDER BY name")]
    for a in accounts:
        typ = TYPE_MAP.get((a.get("type") or "other").lower(), "other")
        if a["id"] in holds_securities and typ not in ("broker",):
            plan["notes"].append(f"{a['name']} holds securities and becomes a broker account here (it was {a.get('type')}).")
            typ = "broker"
        match = existing.get((a["name"] or "").strip().casefold())
        plan["accounts"].append({
            "fp_id": a["id"], "name": a["name"], "fp_type": a.get("type"), "type": typ,
            "currency": (a.get("currency") or "EUR").upper(),
            "closed": bool(a.get("closed_on")),
            "target": match["id"] if match else None, "target_name": match["name"] if match else None,
            "rows": 0, "duplicates": 0, "first": None, "last": None, "balances": 0,
            "ids_shared": True,
        })
    by_fp = {a["fp_id"]: a for a in plan["accounts"]}

    # The ledger.
    rows = src.execute("SELECT * FROM transactions ORDER BY txn_date, id").fetchall()
    for r in rows:
        a = by_fp.get(r["account_id"])
        if a is None:
            continue
        asset = assets.get(r["asset_id"]) if r["asset_id"] else None
        key = keys.get(r["asset_id"]) if r["asset_id"] else None
        kind = (r["type"] or "other").lower()
        if key is None and kind in ("buy", "sell") and r["quantity"]:
            key = _infer_key(r["description"], by_ticker)
        if kind not in ("buy", "sell", "dividend", "interest", "fee", "tax", "deposit",
                        "withdrawal", "transfer", "split", "other"):
            kind = "other"
        # A quantity on a dividend is the position it was paid on, not
        # units that moved — the same trap the Trade Republic export set.
        quantity = r["quantity"] if kind in _QUANTITY_KINDS else None
        price = r["price"] if kind in _QUANTITY_KINDS else None
        ext = _external_id(r["external_id"], r["source"], r["id"])
        dup = ext in existing_ids
        a["rows"] += 1
        a["duplicates"] += dup
        a["ids_shared"] = a["ids_shared"] and ext.startswith(SHARED_ID_PREFIXES)
        a["first"] = min(a["first"] or r["txn_date"], r["txn_date"])
        a["last"] = max(a["last"] or r["txn_date"], r["txn_date"])
        plan["transactions"].append({
            "fp_account": r["account_id"], "txn_date": r["txn_date"],
            "description": " ".join((r["description"] or "").split())[:500],
            "counterparty": (r["counterparty"] or None),
            "amount": float(r["amount"] or 0.0), "currency": (r["currency"] or a["currency"]).upper()[:3],
            "kind": kind, "isin": key, "security_name": (asset.get("name") if asset else names.get(key)),
            "quantity": quantity, "price": price,
            "fee": (abs(r["fee"]) if r["fee"] else None),
            "category": _category(r["category"], known_cats, plan["categories"]),
            "external_id": ext, "duplicate": dup,
            "source": f"{SOURCE}:{(r['source'] or '').split(':')[0]}",
            "owner": _owner_key(r["expense_owner"] if "expense_owner" in r.keys() else None),
        })

    # What the old app held, per account and holding — kept in the plan,
    # because the opening rows depend on which account here the rows go
    # into, and that is the user's choice on the page.
    plan["holdings"] = [
        {"fp_account": h["account_id"], "isin": keys[h["asset_id"]], "name": assets[h["asset_id"]].get("name"),
         "quantity": h["quantity"] or 0.0, "price": h["avg_cost"],
         "currency": (h["cost_currency"] or by_fp[h["account_id"]]["currency"]).upper()[:3],
         "updated_at": (h["updated_at"] or date.today().isoformat())[:10]}
        for h in holdings if keys.get(h["asset_id"]) and h["account_id"] in by_fp]
    plan["openings"] = openings(plan, {a["fp_id"]: a["target"] for a in plan["accounts"]}, held)

    # Balances: the cash lines of every snapshot day, and the value of
    # every balance-only account — a pension, a house, a loan.
    balance_only = {"pension", "p2p", "property", "loan", "other"}
    # One snapshot per day: a day with two — a manual one beside the
    # nightly one — would otherwise count every balance twice. The
    # newest of the day is the one.
    lines = src.execute(
        "SELECT s.snapshot_date, l.account_id, l.asset_id, l.quantity, l.price, l.currency "
        "FROM snapshot_lines l JOIN snapshots s ON s.id = l.snapshot_id "
        "WHERE s.id = (SELECT MAX(s2.id) FROM snapshots s2 WHERE s2.snapshot_date = s.snapshot_date "
        "              AND EXISTS (SELECT 1 FROM snapshot_lines l2 WHERE l2.snapshot_id = s2.id)) "
        "ORDER BY s.snapshot_date").fetchall()
    per_day: dict[tuple[int, str], dict[str, float]] = {}
    for l_ in lines:
        a = by_fp.get(l_["account_id"])
        if a is None:
            continue
        asset = assets.get(l_["asset_id"])
        if keys.get(l_["asset_id"]) is not None and a["type"] not in balance_only:
            continue                     # a security: valued from prices here
        is_cash = (asset or {}).get("asset_class") == "cash" or ((asset or {}).get("ticker") or "").upper().startswith("CASH_")
        amount = (l_["quantity"] or 0.0) * (1.0 if is_cash else (l_["price"] or 0.0))
        ccy = (l_["currency"] or (asset or {}).get("currency") or a["currency"]).upper()[:3]
        pile = per_day.setdefault((l_["account_id"], l_["snapshot_date"]), {})
        pile[ccy] = pile.get(ccy, 0.0) + amount
    # And today's cash, from the holdings table — where no snapshot of
    # the day has it already. Only cash: a house's holding row carries
    # its purchase price, the snapshot line its value.
    for h in holdings:
        a = by_fp.get(h["account_id"])
        asset = assets.get(h["asset_id"])
        if a is None or asset is None or asset.get("asset_class") != "cash":
            continue
        day = (h["updated_at"] or date.today().isoformat())[:10]
        if (h["account_id"], day) in per_day:
            continue
        ccy = (asset.get("currency") or a["currency"]).upper()[:3]
        pile = per_day.setdefault((h["account_id"], day), {})
        pile[ccy] = pile.get(ccy, 0.0) + (h["quantity"] or 0.0)
    for (fp_account, day), pile in sorted(per_day.items(), key=lambda kv: kv[0][1]):
        a = by_fp[fp_account]
        # One reading per day: the account's own currency where it has
        # money, else the biggest pile. A second currency with money in
        # it is noted, not silently dropped.
        nonzero = {c: v for c, v in pile.items() if abs(v) > 0.005}
        if not nonzero:
            nonzero = {a["currency"]: pile.get(a["currency"], 0.0)}
        ccy = a["currency"] if a["currency"] in nonzero else max(nonzero, key=lambda c: abs(nonzero[c]))
        others = {c: v for c, v in nonzero.items() if c != ccy}
        if others:
            plan["notes"].append(f"{a['name']} {day}: also " + ", ".join(f"{v:.2f} {c}" for c, v in others.items())
                                 + " — a reading holds one currency; only " + ccy + " was kept.")
        a["balances"] += 1
        plan["balances"].append({"fp_account": fp_account, "as_of": day, "amount": nonzero[ccy], "currency": ccy})

    # An old account with nothing in it — no row, no balance, no
    # holding — is not created here.
    opened = {o["fp_account"] for o in plan["openings"]}
    empty = [a for a in plan["accounts"] if not a["rows"] and not a["balances"] and a["fp_id"] not in opened]
    for a in empty:
        plan["notes"].append(f"{a['name']} holds nothing and is left out.")
        a["skip"] = True

    # Securities and their prices.
    for aid, asset in assets.items():
        key = keys.get(aid)
        if key:
            plan["securities"].append({"isin": key, "symbol": asset.get("yahoo_symbol"), "name": asset.get("name")})
    for p in src.execute("SELECT asset_id, price_date, close, currency FROM prices WHERE close IS NOT NULL"):
        key = keys.get(p["asset_id"])
        if key:
            plan["prices"].append((key, p["price_date"], p["close"], (p["currency"] or "EUR").upper()[:3]))

    # The net worth the old app recorded on the days before it kept
    # per-position lines: no account to hang it on, but a day and a
    # figure, and the history line uses them up to the day the
    # readings above take over.
    plan["net_worth"] = []
    try:
        first_lines = src.execute("SELECT MIN(s.snapshot_date) FROM snapshots s "
                                  "JOIN snapshot_lines l ON l.snapshot_id = s.id").fetchone()[0]
        for r in src.execute("SELECT snapshot_date, MAX(id) AS id FROM snapshots WHERE net_worth_eur IS NOT NULL "
                             "GROUP BY snapshot_date ORDER BY snapshot_date"):
            if first_lines and r["snapshot_date"] >= first_lines:
                continue
            nw = src.execute("SELECT net_worth_eur FROM snapshots WHERE id = ?", (r["id"],)).fetchone()[0]
            plan["net_worth"].append({"as_of": r["snapshot_date"], "amount": float(nw), "currency": "EUR"})
    except sqlite3.Error:
        pass
    plan["lines_from"] = first_lines
    if plan["net_worth"]:
        plan["notes"].append(f"{len(plan['net_worth'])} days of net worth from before the old app kept per-position lines "
                             f"go on the history line as recorded, up to {first_lines}.")
    # Whose spending: the old app's owners — a first name, or "common"
    # for the household — become people here (matched by name, made
    # when missing) and "shared"; its keyword rules become rules here.
    plan["owners"] = sorted({t["owner"] for t in plan["transactions"] if t["owner"] and t["owner"] != "shared"})
    plan["owner_rules"] = []
    try:
        for r in src.execute("SELECT keyword, owner FROM expense_owner_rules ORDER BY id"):
            owner = _owner_key(r["owner"])
            if r["keyword"] and owner:
                plan["owner_rules"].append({"pattern": r["keyword"], "owner": owner})
    except sqlite3.Error:
        pass
    if plan["owners"] or plan["owner_rules"]:
        plan["notes"].append(f"Whose spending: {', '.join(plan['owners']) or 'nobody'} and the household's shared rows, "
                             f"with {len(plan['owner_rules'])} keyword rules, go onto the Who spent page.")
    for tbl, what in (("retirement_rules", "retirement rules"),
                      ("recurring_contributions", "recurring contributions")):
        try:
            n = src.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except sqlite3.Error:
            n = 0
        if n:
            plan["notes"].append(f"{n} {what} are not carried over: nothing here reads them yet.")
    plan["totals"] = {"accounts": len(plan["accounts"]), "rows": len(plan["transactions"]),
                      "duplicates": sum(1 for t in plan["transactions"] if t["duplicate"]),
                      "balances": len(plan["balances"]), "openings": len(plan["openings"]),
                      "securities": len(plan["securities"]), "prices": len(plan["prices"]),
                      "new_categories": len(plan["categories"])}
    return plan


def openings(plan: dict, targets: dict[int, int | None], held: dict | None = None) -> list[dict]:
    """The rows that make the holdings agree, given where each old
    account's rows go: what the old app held, less what the rows to be
    written add up to, less what the chosen account here already holds
    — the duplicates left alone are counted through the latter. And the
    other way round: rows that add up to a position the old app did not
    hold — a sale whose purchase predates the ledger — are closed."""
    if held is None:
        with get_conn() as conn:
            held = {(r["account_id"], r["isin"]): r["q"] for r in conn.execute(
                "SELECT account_id, isin, SUM(COALESCE(quantity, 0)) AS q FROM transactions "
                "WHERE isin IS NOT NULL AND quantity IS NOT NULL GROUP BY account_id, isin")}
    by_fp = {a["fp_id"]: a for a in plan["accounts"]}
    first_row: dict[tuple[int, str], str] = {}
    summed: dict[tuple[int, str], float] = {}
    for t in plan["transactions"]:
        if t["isin"] and t["quantity"] is not None and not t["duplicate"]:
            k = (t["fp_account"], t["isin"])
            summed[k] = summed.get(k, 0.0) + t["quantity"]
            first_row[k] = min(first_row.get(k, t["txn_date"]), t["txn_date"])

    def already(fp_account: int, key: str) -> float:
        target = targets.get(fp_account, by_fp[fp_account]["target"])
        return held.get((target, key), 0.0) if target else 0.0

    out = []
    listed = set()
    for h in plan["holdings"]:
        k = (h["fp_account"], h["isin"])
        listed.add(k)
        a = by_fp[k[0]]
        from_rows = summed.get(k, 0.0) + already(*k)
        diff = h["quantity"] - from_rows
        if abs(diff) < 1e-6:
            continue
        day = first_row.get(k)
        out.append({
            "fp_account": k[0], "account": a["name"], "isin": k[1], "name": h["name"],
            "quantity": diff, "held": h["quantity"], "from_rows": from_rows,
            "price": h["price"], "currency": h["currency"],
            "txn_date": (date.fromisoformat(day) - timedelta(days=1)).isoformat() if day else h["updated_at"],
        })
    names = {h["isin"]: h["name"] for h in plan["holdings"]}
    for k, q in summed.items():
        if k in listed or abs(q) < 1e-9:
            continue
        a = by_fp[k[0]]
        total = q + already(*k)
        if abs(total) < 1e-9:
            continue
        out.append({
            "fp_account": k[0], "account": a["name"], "isin": k[1], "name": names.get(k[1]),
            "quantity": -total, "held": 0.0, "from_rows": total, "price": None,
            "currency": a["currency"],
            "txn_date": (date.fromisoformat(first_row[k]) - timedelta(days=1)).isoformat(),
        })
    return out


def apply(plan: dict, targets: dict[int, int | None] | None = None) -> dict:
    """Write the plan. `targets` maps an old account id to an account
    here, or None for a new one; unset means what the plan proposed."""
    targets = targets or {}
    report = {"accounts_created": 0, "rows": 0, "duplicates": 0, "balances": 0,
              "openings": 0, "securities": 0, "prices": 0, "categories": 0, "imports": []}
    for slug, label in plan["categories"].items():
        try:
            categories.add_category(label, "#94a3b8", categories.SPENDING_GROUP)
            report["categories"] += 1
        except ValueError:
            pass
    # add_category derives the slug from the label; the rows carry the
    # old slug, so make sure the two agree, else file under the new one.
    live = categories.all_categories()
    slug_map = {}
    for slug, label in plan["categories"].items():
        if slug in live:
            slug_map[slug] = slug
        else:
            slug_map[slug] = next((s for s, e in live.items() if e["label"].casefold() == label.casefold()), None)

    chosen_targets = {a["fp_id"]: targets.get(a["fp_id"], a["target"]) for a in plan["accounts"]}
    plan["openings"] = openings(plan, chosen_targets)
    id_map: dict[int, int] = {}
    with get_conn() as conn:
        for a in plan["accounts"]:
            if a.get("skip"):
                continue
            chosen = chosen_targets[a["fp_id"]]
            if chosen:
                id_map[a["fp_id"]] = int(chosen)
                continue
            cur = conn.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                               (a["name"], a["type"], a["currency"]))
            id_map[a["fp_id"]] = int(cur.lastrowid)
            report["accounts_created"] += 1
        for s_ in plan["securities"]:
            cur = conn.execute(
                "INSERT INTO securities (isin, symbol, name, symbol_source) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(isin) DO UPDATE SET symbol = COALESCE(securities.symbol, excluded.symbol), "
                "name = COALESCE(securities.name, excluded.name)",
                (s_["isin"], s_["symbol"], s_["name"], "manual" if s_["symbol"] else None))
            report["securities"] += 1
        for key, day, close, ccy in plan["prices"]:
            cur = conn.execute("INSERT OR IGNORE INTO prices (isin, as_of, price, currency) VALUES (?, ?, ?, ?)",
                               (key, day, close, ccy))
            report["prices"] += cur.rowcount

    # The people the old app's owners name — made when missing.
    from . import people
    persons = people.all_people()
    owner_ids: dict[str, int] = {}
    for name in plan.get("owners") or []:
        pid = _match_person(name, persons)
        if pid is None:
            pid = people.add(name)
            persons = people.all_people()
            report["people_created"] = report.get("people_created", 0) + 1
        owner_ids[name] = pid

    def owner_cols(owner):
        if owner == "shared":
            return None, 1
        if owner in owner_ids:
            return owner_ids[owner], 0
        return None, 0

    imports_by_account: dict[int, int] = {}
    for t in plan["transactions"]:
        acc = id_map[t["fp_account"]]
        if acc not in imports_by_account:
            imports_by_account[acc] = importers.begin_import(acc, "wealth.db", SOURCE)
    with get_conn() as conn:
        for t in plan["transactions"]:
            acc = id_map[t["fp_account"]]
            cat = t["category"]
            cat = slug_map.get(cat, cat) if cat else None
            oid, shared = owner_cols(t.get("owner"))
            cur = conn.execute(
                "INSERT OR IGNORE INTO transactions (account_id, txn_date, description, counterparty, "
                "amount, currency, external_id, kind, category, isin, security_name, quantity, price, "
                "fee, source, import_id, owner_id, owner_shared) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (acc, t["txn_date"], t["description"], t["counterparty"], t["amount"], t["currency"],
                 t["external_id"], t["kind"], cat, t["isin"], t["security_name"], t["quantity"],
                 t["price"], t["fee"], t["source"], imports_by_account[acc], oid, shared))
            if cur.rowcount:
                report["rows"] += 1
            else:
                report["duplicates"] += 1
                # A row moved in earlier, before owners came across:
                # it learns whose it is now, unless somebody said since.
                if oid or shared:
                    conn.execute("UPDATE transactions SET owner_id = ?, owner_shared = ? WHERE external_id = ? "
                                 "AND owner_id IS NULL AND owner_shared = 0", (oid, shared, t["external_id"]))
        for o in plan["openings"]:
            acc = id_map[o["fp_account"]]
            cur = conn.execute(
                "INSERT OR IGNORE INTO transactions (account_id, txn_date, description, amount, currency, "
                "external_id, kind, category, isin, security_name, quantity, price, source, import_id) "
                "VALUES (?,?,?,0,?,?,'transfer','transfer',?,?,?,?,?,?)",
                (acc, o["txn_date"], "Opening position — moved in from Financial Planner",
                 o["currency"], f"fp:open:{o['fp_account']}:{o['isin']}", o["isin"], o["name"],
                 o["quantity"], o["price"], SOURCE, imports_by_account.get(acc)))
            report["openings"] += cur.rowcount
        for b in plan["balances"]:
            acc = id_map[b["fp_account"]]
            cur = conn.execute(
                "INSERT INTO balances (account_id, amount, currency, balance_type, as_of) "
                "SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM balances WHERE account_id = ? "
                "AND as_of = ? AND currency = ? AND balance_type = ? AND abs(amount - ?) < 0.005)",
                (acc, b["amount"], b["currency"], SOURCE, b["as_of"], acc, b["as_of"], b["currency"], SOURCE, b["amount"]))
            report["balances"] += cur.rowcount
        for r in plan.get("net_worth") or []:
            conn.execute("INSERT OR REPLACE INTO net_worth_readings (as_of, currency, amount, source) VALUES (?, ?, ?, ?)",
                         (r["as_of"], r["currency"], r["amount"], SOURCE))
        report["net_worth_days"] = len(plan.get("net_worth") or [])
        # From this day the readings above cover every account, and the
        # history line is this app's own arithmetic; before it, the
        # recorded totals. See history.series().
        if plan.get("lines_from"):
            conn.execute("INSERT INTO app_state (key, value, updated_at) VALUES ('records_from', ?, datetime('now')) "
                         "ON CONFLICT(key) DO UPDATE SET value = MIN(value, excluded.value), updated_at = excluded.updated_at",
                         (plan["lines_from"],))
        for acc, imp in imports_by_account.items():
            conn.execute("UPDATE imports SET inserted = (SELECT COUNT(*) FROM transactions WHERE import_id = ?) "
                         "WHERE id = ?", (imp, imp))
        # The rows came in under the old app's ids. An export or a sync
        # covering the same days would book them again under this
        # app's ids, so the account remembers how far its ledger is
        # already on record — see accounts.ledger_until.
        for a in plan["accounts"]:
            if a.get("skip") or not a["last"] or a["ids_shared"]:
                continue
            conn.execute("UPDATE accounts SET ledger_until = MAX(COALESCE(ledger_until, ''), ?) WHERE id = ?",
                         (a["last"], id_map[a["fp_id"]]))
    # The rules: whose spending, by keyword; and the old app's category
    # rules when their file was given. Each is applied as it is stored,
    # to what is already here — that is what a rule is for.
    report["rules"] = 0
    existing = {(r["pattern"].lower(), r["category"] or "", r.get("set_owner") or "") for r in categories.rules()}
    for r in plan.get("owner_rules") or []:
        owner = "shared" if r["owner"] == "shared" else (str(owner_ids[r["owner"]]) if r["owner"] in owner_ids else None)
        if not owner or (r["pattern"].lower(), "", owner) in existing:
            continue
        try:
            categories.add_rule(r["pattern"], categories.KEEP, set_owner=owner)
            report["rules"] += 1
        except ValueError:
            pass
    for r in plan.get("category_rules") or []:
        cat = slug_map.get(r["category"], r["category"]) if r["category"] in plan["categories"] else r["category"]
        if cat not in live or (r["pattern"].lower(), cat, "") in existing:
            continue
        try:
            categories.add_rule(r["pattern"], cat)
            report["rules"] += 1
        except ValueError:
            pass
    # The sync may have booked the same days before the move-in — under
    # its own ids, so nothing above caught them. The bare copies go.
    from . import ledger
    report["twins_removed"] = sum(ledger.heal_twins(acc) for acc in imports_by_account)
    for acc in imports_by_account:
        categories.categorise_new(acc)
    report["imports"] = list(imports_by_account.values())
    report["account_ids"] = sorted(set(id_map.values()))
    return report

