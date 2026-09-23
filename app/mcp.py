"""An MCP endpoint, so an assistant can read the dashboard and do the
chores a person would otherwise do by hand — categorise the queue,
write a rule, set a budget, star a share idea.

MCP is JSON-RPC 2.0. Its "Streamable HTTP" transport is a POST per
message to one URL, which is a shape Flask already has; the subset a
client needs to be useful — `initialize`, `tools/list`, `tools/call`,
`ping` — is small enough to write here rather than to import the
official SDK, which brings pydantic, starlette, anyio and httpx into a
four-line requirements file. What is not here: server-initiated
streams (a GET on the endpoint answers 405), resources, prompts,
sessions. A client that needs any of those will say so, and this
answers with a clean JSON-RPC error rather than a stack trace.

Why inside the app and not a separate program reading `wealth.db`
------------------------------------------------------------------
The database is in the container's volume, and a second process
writing to it from another machine over a share is the thing the README
says will corrupt it. Every tool below goes through the same module the
web page goes through — `categories.set_category()`, `manual.add_
transaction()`, `screener.set_watch()` — so a write from an assistant
is a write the UI could have made, under the same single-writer rule.

What it can and cannot do
-------------------------
Reads: everything the pages show. Writes: categories and rules,
budgets, hand-typed transactions and balances, the share-ideas
watchlist, and "sync / refresh now". Not: deleting an account, editing
settings, reading or writing credentials. The bearer token is generated
under Settings, kept 0600 beside the bank key, and revocable there.

The language of everything returned is English whatever the UI is set
to — the consumer is a program, and the source strings are the
contract.
"""

from __future__ import annotations

import hmac
import inspect
import json
import secrets
from datetime import date

from flask import g

from . import __version__, categories, cashflow, history, manual, overview
from . import people, prices, screener, screener_etf, screener_jobs, settings
from . import subscriptions as subs
from .banks import sync as banksync
from .db import get_conn

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
TOKEN_FILE = settings.SECRETS_DIR / "mcp_token"
SERVER_INFO = {"name": "wealth-dashboard", "version": __version__}
INSTRUCTIONS = (
    "A self-hosted net-worth dashboard. Amounts are in the account's own "
    "currency unless a field says base currency. Categories are slugs — "
    "call `categories` for the list. To categorise transactions, read "
    "`uncategorised` and call `categorise_many`; each item may carry a "
    "`pattern` so the app learns a rule and applies it to every past and "
    "future transaction that matches. Prefer the counterparty as the "
    "pattern; never a pattern under three characters. Nothing here can "
    "delete an account or touch credentials."
)

# JSON-RPC error codes.
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL = (
    -32700, -32600, -32601, -32602, -32603)


# ─── The token ───────────────────────────────────────────────────────

def token() -> str | None:
    try:
        value = TOKEN_FILE.read_text().strip()
    except OSError:
        return None
    return value or None


def new_token() -> str:
    """Make one, replacing any old one — which stops working at once."""
    settings.ensure_dirs()
    value = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(value)
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass
    return value


def revoke() -> None:
    try:
        TOKEN_FILE.unlink()
    except FileNotFoundError:
        pass


# ─── Pairing a device ────────────────────────────────────────────────
#
# A phone should not have a 43-character token typed into it, and a
# token shown as a QR is a token anyone who photographs the screen
# owns. So: a six-digit code, good for five minutes and for one
# exchange, which a device trades for the token over the same HTTPS the
# dashboard is reached by. The code lives in app_state, not in a table
# of its own — it is one value at a time, and it expires.

PAIR_TTL = 300                                    # seconds
_PAIR_KEY = "pair_code"


def start_pairing() -> dict:
    """A fresh pairing code; any earlier one stops working. Returns
    {code, expires_at, expires_in}."""
    from .db import set_state
    from datetime import datetime, timedelta, timezone
    if not token():
        new_token()
    code = f"{secrets.randbelow(1000000):06d}"
    until = datetime.now(timezone.utc) + timedelta(seconds=PAIR_TTL)
    set_state(_PAIR_KEY, json.dumps({"code": code, "until": until.isoformat(timespec="seconds")}))
    return {"code": code, "expires_at": until.isoformat(timespec="seconds"), "expires_in": PAIR_TTL}


def pending_code() -> dict | None:
    """The code still waiting, or None — what the Settings page shows
    when the browser is reloaded within the five minutes."""
    from .db import get_state
    from datetime import datetime, timezone
    raw = get_state(_PAIR_KEY)
    if not raw:
        return None
    try:
        held = json.loads(raw)
        until = datetime.fromisoformat(held["until"])
    except (ValueError, KeyError, TypeError):
        return None
    left = int((until - datetime.now(timezone.utc)).total_seconds())
    if left <= 0:
        return None
    return {"code": held["code"], "expires_at": held["until"], "expires_in": left}


def redeem(code: str | None) -> str | None:
    """The token, for the right code, once. Wrong, late or already
    used: None, and the code is burnt either way — six digits guessed
    at leisure are six digits guessed."""
    from .db import set_state
    held = pending_code()
    set_state(_PAIR_KEY, "")
    if not held or not code:
        return None
    if not hmac.compare_digest(str(code).strip(), held["code"]):
        return None
    return token()


def authorised(header: str | None) -> bool:
    """`Authorization: Bearer <token>`, compared in constant time."""
    want = token()
    if not want or not header:
        return False
    scheme, _, given = header.strip().partition(" ")
    return scheme.lower() == "bearer" and hmac.compare_digest(given.strip(), want)


# ─── Tools ───────────────────────────────────────────────────────────

TOOLS: list[dict] = []
_HANDLERS: dict = {}


def tool(name: str, description: str, properties: dict | None = None,
         required: list[str] | None = None):
    """Register a handler. The schema is written out here, once, in the
    form the client shows the model — a tool the model cannot read the
    arguments of is a tool it calls wrongly."""
    def wrap(fn):
        TOOLS.append({
            "name": name, "description": description,
            "inputSchema": {"type": "object",
                            "properties": properties or {},
                            "required": required or []},
        })
        _HANDLERS[name] = fn
        return fn
    return wrap


def _base() -> str:
    return settings.get("base_currency", "EUR")


def _scope(person) -> list[int] | None:
    """Everyone's accounts, or one person's — by name or id."""
    if person in (None, "", 0):
        return None
    for p in people.all_people():
        if p["id"] == person or str(p["id"]) == str(person) \
                or p["name"].lower() == str(person).strip().lower():
            return people.account_ids(p["id"])
    raise ValueError(f"No person called {person!r}. "
                     f"Known: {', '.join(p['name'] for p in people.all_people()) or 'nobody'}.")


def _account(account_id) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?",
                           (int(account_id),)).fetchone()
    if row is None:
        raise ValueError(f"No account with id {account_id}.")
    return dict(row)


def _num_str(value) -> str | None:
    """A number for the manual-entry parser, which reads what a person
    types. Six decimals is beyond any price or quantity here, and it
    keeps a value like 1234 from being read as a European thousand."""
    if value is None or value == "":
        return None
    return f"{float(value):.6f}"


PERSON = {"type": ["string", "integer", "null"],
          "description": "Restrict to one person's accounts, by name or id. "
                         "Omit for the whole household."}


@tool("net_worth",
      "Net worth right now in the base currency: cash, securities, per-account "
      "balances, and which day the prices and exchange rates are from.",
      {"person": PERSON})
def _net_worth(person=None):
    s = overview.summary(_base(), account_ids=_scope(person))
    return {k: s[k] for k in ("base_currency", "net_worth", "cash", "securities",
                              "unconverted", "fx_as_of", "prices_as_of",
                              "holdings_at_market", "holdings_at_trade",
                              "account_count", "connected_count")} | {
        "accounts": [{k: a.get(k) for k in ("id", "name", "type", "currency", "bank",
                                            "balance", "balance_base", "as_of", "people")}
                     for a in s["accounts"]],
        "by_class": s["by_class"],
    }


@tool("snapshot",
      "Everything a home screen needs, in one call: net worth and its parts, the "
      "return over every period, the accounts, what is coming in the next days, how "
      "many rows wait to be categorised or assigned, and whether the syncs are "
      "healthy. Meant for a phone or a widget, where each round trip costs.",
      {"person": PERSON, "days": {"type": "integer", "description": "How far ahead to "
                                  "look for bills and subscriptions. Default 30."}})
def _snapshot(person=None, days=30):
    from datetime import datetime, timezone
    from . import expenses, performance, upcoming
    scope = _scope(person)
    base = _base()
    s = overview.summary(base, account_ids=scope)
    try:
        ahead = upcoming.project(base, max(1, min(int(days or 30), 365)), scope)
    except Exception:                                   # noqa: BLE001 — a widget still wants the rest
        ahead = None
    _, waiting = categories.uncategorised(1, account_ids=scope)
    split = expenses.split(base, scope, months=1)
    health = banksync.health()
    return {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_currency": base,
        "net_worth": {k: s[k] for k in ("net_worth", "cash", "securities", "assets", "debt",
                                        "fx_as_of", "prices_as_of") if k in s} | {"by_class": s["by_class"]},
        "performance": performance.periods(base, scope),
        "accounts": [{k: a.get(k) for k in ("id", "name", "type", "currency", "bank",
                                            "balance", "balance_base", "as_of")} for a in s["accounts"]],
        "upcoming": {k: ahead.get(k) for k in ("today", "until", "days", "starting", "ending",
                                               "total_in", "total_out", "lowest", "below_zero",
                                               "counts")} if ahead else None,
        "events": (ahead or {}).get("entries", [])[:12],
        "waiting": {"uncategorised": waiting,
                    "unassigned_spending": split["counts"]["unassigned"]},
        "sync": {"links": len(health),
                 "red": sum(1 for h in health if h.get("status") == "red"),
                 "yellow": sum(1 for h in health if h.get("status") == "yellow"),
                 "last_sync_at": max([h.get("last_sync_at") or "" for h in health] or [""]) or None},
    }


@tool("accounts", "Every account: id, name, type, currency, whose it is, and "
      "whether a bank is connected.")
def _accounts():
    s = overview.summary(_base())
    return [{k: a.get(k) for k in ("id", "name", "type", "currency", "bank", "people",
                                   "balance", "as_of", "transactions")}
            for a in s["accounts"]]


@tool("holdings", "Securities held, computed from the trades: ISIN, name, "
      "quantity, net invested, the last price and its day, and the value.",
      {"person": PERSON})
def _holdings(person=None):
    s = overview.summary(_base(), account_ids=_scope(person))
    return {"base_currency": s["base_currency"], "prices_as_of": s["prices_as_of"],
            "holdings": s["holdings"]}


@tool("performance",
      "Time-weighted (TWR) and money-weighted (MWR) return of the securities held, "
      "as fractions: since the first trade, this year, and the last twelve months; "
      "and per holding. Cash is left out; MWR is annual; TWR total plus annualised.",
      {"person": PERSON})
def _performance(person=None):
    from . import performance
    from datetime import date as _date, timedelta as _td
    scope = _scope(person)
    today = _date.today()
    out = {"all": performance.for_accounts(_base(), scope),
           "ytd": performance.for_accounts(_base(), scope, start=_date(today.year, 1, 1)),
           "1y": performance.for_accounts(_base(), scope, start=today - _td(days=365)),
           "holdings": {}}
    for h in overview.summary(_base(), account_ids=scope)["holdings"]:
        out["holdings"][h["isin"]] = {"name": h["name"], **performance.for_security(h["isin"], scope)}
    return out


@tool("realised_gains",
      "What the sales made, by lots: per year and all time, per currency, and per "
      "security ever sold. Pass an ISIN for every sale of that one security with the "
      "cost of the units sold and the gain, plus what is still held and what it cost. "
      "Method is the Settings choice (fifo or average) unless given.",
      {"person": PERSON,
       "isin": {"type": "string", "description": "One security; omit for the summary."},
       "method": {"type": "string", "enum": ["fifo", "average"]}})
def _realised_gains(person=None, isin=None, method=None):
    from . import gains
    scope = _scope(person)
    if isin:
        return gains.realised(isin.strip(), scope, method)
    return gains.summary(scope, method)


@tool("record_split",
      "Record a stock split on a security: one 'split' row per account holding it on "
      "that day, with the units that appeared at no cost. ratio is new for old — "
      "'44:1', or '1:10' for a reverse split. Returns the rows written.",
      {"isin": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"},
       "ratio": {"type": "string"}, "person": PERSON})
def _record_split(isin, date, ratio, person=None):
    from . import splits
    return {"written": splits.record(isin.strip(), date, ratio, _scope(person))}


@tool("allocation",
      "Where the money is by asset class, region and the user's own buckets: per key "
      "the value, share, target, drift and — given a contribution — how much of it to "
      "put there. Also each holding's classification.",
      {"contribution": {"type": "number"}, "person": PERSON})
def _allocation(contribution=0, person=None):
    from . import allocation
    return allocation.breakdown(overview.summary(_base(), account_ids=_scope(person)),
                                float(contribution or 0))


@tool("set_security_class",
      "Classify a holding: asset class (equity, bond, real_estate, commodity, cash, "
      "crypto, other), region (world, europe, north_america, emerging, asia_pacific, "
      "switzerland, germany, other or free text) and bucket (free text).",
      {"isin": {"type": "string"}, "asset_class": {"type": "string"},
       "region": {"type": "string"}, "bucket": {"type": "string"}}, ["isin"])
def _set_security_class(isin, asset_class=None, region=None, bucket=None):
    from . import allocation
    allocation.set_class(isin.strip(), asset_class, region, bucket)
    return {"isin": isin, "asset_class": asset_class, "region": region, "bucket": bucket}


@tool("set_allocation_targets",
      "Replace the targets of one dimension (asset_class, region or bucket): a map of "
      "key to percent. Keys left out lose their target; the sum may not exceed 100.",
      {"dimension": {"type": "string", "enum": ["asset_class", "region", "bucket"]},
       "targets": {"type": "object", "additionalProperties": {"type": "number"}}},
      ["dimension", "targets"])
def _set_allocation_targets(dimension, targets):
    from . import allocation
    allocation.set_targets(dimension, dict(targets))
    return {"dimension": dimension, "targets": allocation.targets(dimension)}


@tool("net_worth_history",
      "Net worth on a set of days across a period, rebuilt from the records.",
      {"period": {"type": "string", "enum": sorted(history.PERIODS),
                  "description": "1m, 3m, 6m, ytd, 1y or all."},
       "person": PERSON})
def _history(period="ytd", person=None):
    if period not in history.PERIODS:
        raise ValueError(f"period must be one of {sorted(history.PERIODS)}")
    return history.series(_base(), _scope(person), period)


@tool("transactions",
      "Search transactions, newest first. Every filter is optional.",
      {"q": {"type": "string", "description": "Text in the description or counterparty."},
       "account_id": {"type": "integer"},
       "category": {"type": "string", "description": "A category slug, or "
                    "'uncategorised' for rows with none."},
       "kind": {"type": "string", "description": "deposit, withdrawal, buy, sell, "
                "dividend, interest, fee, tax, transfer, other."},
       "date_from": {"type": "string", "description": "ISO date, inclusive."},
       "date_to": {"type": "string", "description": "ISO date, inclusive."},
       "tag": {"type": "string", "description": "Only rows carrying this tag."},
       "limit": {"type": "integer", "description": "Default 100, at most 500."},
       "person": PERSON})
def _transactions(q=None, account_id=None, category=None, kind=None,
                  date_from=None, date_to=None, limit=100, person=None, tag=None):
    where, params = ["1=1"], []
    if tag:
        where.append("(',' || COALESCE(t.tags,'') || ',') LIKE ?")
        params.append(f"%,{categories.clean_tag(tag)},%")
    if q:
        where.append("(LOWER(t.description) LIKE ? OR LOWER(COALESCE(t.counterparty,'')) LIKE ?)")
        params += [f"%{str(q).lower()}%"] * 2
    if account_id is not None:
        where.append("t.account_id = ?")
        params.append(int(account_id))
    if category == "uncategorised":
        where.append("(t.category IS NULL OR t.category = '')")
    elif category:
        where.append("t.category = ?")
        params.append(category)
    if kind:
        where.append("t.kind = ?")
        params.append(kind)
    if date_from:
        where.append("t.txn_date >= ?")
        params.append(str(date_from)[:10])
    if date_to:
        where.append("t.txn_date <= ?")
        params.append(str(date_to)[:10])
    only, only_params = people.sql_in(_scope(person), "t.account_id")
    limit = max(1, min(int(limit or 100), 500))
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT t.id, t.account_id, a.name AS account, t.txn_date, t.description, "
            f"t.counterparty, t.amount, t.currency, t.kind, t.category, t.tags, t.isin, "
            f"t.security_name, t.quantity, t.price, t.source FROM transactions t "
            f"JOIN accounts a ON a.id = t.account_id WHERE {' AND '.join(where)}{only} "
            f"ORDER BY t.txn_date DESC, t.id DESC LIMIT ?",
            [*params, *only_params, limit]).fetchall()]
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM transactions t WHERE {' AND '.join(where)}{only}",
            [*params, *only_params]).fetchone()["n"]
    return {"matched": total, "returned": len(rows), "transactions": rows}


@tool("uncategorised",
      "The queue of transactions with no category, biggest first, each with the "
      "app's own first guess and the pattern a rule would remember it by.",
      {"limit": {"type": "integer", "description": "Default 60, at most 500."},
       "person": PERSON})
def _uncategorised(limit=60, person=None):
    rows, total = categories.uncategorised(max(1, min(int(limit or 60), 500)),
                                           account_ids=_scope(person))
    keep = ("id", "account_id", "account_name", "txn_date", "description",
            "counterparty", "amount", "currency", "kind", "suggestion", "pattern")
    return {"remaining": total, "transactions": [{k: r.get(k) for k in keep} for r in rows]}


@tool("categories", "The category slugs, their labels, whether each counts as "
      "spending, and how many transactions carry each.")
def _categories():
    return categories.catalogue()


@tool("rules", "The categorisation rules: a substring, and the category it files "
      "a matching transaction under. Newest first; on a clash the newest wins.")
def _rules():
    return categories.rules()


@tool("set_category",
      "File one transaction under a category. With `remember` (the default) the "
      "app also stores a rule on `pattern` — the counterparty, or the merchant "
      "name from the description — and applies it to every past and future "
      "transaction that matches. Filing under 'other' never makes a rule.",
      {"txn_id": {"type": "integer"},
       "category": {"type": "string", "description": "A slug from `categories`."},
       "pattern": {"type": "string", "description": "Substring for the rule; at "
                   "least three characters. Defaults to the app's suggestion."},
       "remember": {"type": "boolean", "description": "Default true."}},
      ["txn_id", "category"])
def _set_category(txn_id, category, pattern=None, remember=True):
    return _categorise_one(int(txn_id), category, pattern, remember)


def _categorise_one(txn_id: int, category: str, pattern, remember) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT description, counterparty FROM transactions "
                           "WHERE id = ?", (txn_id,)).fetchone()
    if row is None:
        raise ValueError(f"No transaction with id {txn_id}.")
    categories.set_category(txn_id, category)
    out = {"txn_id": txn_id, "category": category, "rule": None, "applied": 0}
    if remember and category != "other":
        pattern = (pattern or "").strip() or categories.suggest_pattern(
            row["description"], row["counterparty"])
        if pattern:
            out["applied"] = categories.add_rule(pattern, category)
            out["rule"] = pattern
    return out


@tool("categorise_many",
      "File many transactions at once — the tool to use after reading "
      "`uncategorised`. Each item is {txn_id, category, pattern?}; `remember` "
      "applies to all. Items that fail are reported, the rest go through.",
      {"items": {"type": "array", "items": {"type": "object", "properties": {
          "txn_id": {"type": "integer"}, "category": {"type": "string"},
          "pattern": {"type": "string"}}, "required": ["txn_id", "category"]}},
       "remember": {"type": "boolean", "description": "Default true."}},
      ["items"])
def _categorise_many(items, remember=True):
    done, failed = [], []
    for item in items or []:
        try:
            done.append(_categorise_one(int(item["txn_id"]), item["category"],
                                        item.get("pattern"), remember))
        except (ValueError, KeyError, TypeError) as exc:
            failed.append({"item": item, "error": str(exc)})
    return {"categorised": len(done), "failed": failed, "results": done}


_RULE_TERMS = {"pattern": {"type": "string", "description": "Text to match, three characters at least — or a regular expression with match_mode regex."},
               "category": {"type": "string", "description": "The category to file under; empty to leave the category alone."},
               "match_mode": {"type": "string", "enum": ["contains", "starts", "exact", "regex"]},
               "account_id": {"type": "integer", "description": "Only rows of this account."},
               "kind": {"type": "string", "description": "Only rows of this kind."},
               "set_counterparty": {"type": "string", "description": "Rename the counterparty to this."},
               "set_kind": {"type": "string", "description": "Set the kind, e.g. transfer."},
               "add_tag": {"type": "string", "description": "Add this tag."},
               "set_owner": {"type": "string", "description": "Whose spending a match is: a person's id (see `people`), or \"shared\"."},
               "field": {"type": "string", "enum": ["any", "description", "counterparty"],
                         "description": "Where the text is looked for. Default any."},
               "direction": {"type": "string", "enum": ["any", "in", "out"],
                             "description": "Which way the money went. Default any."},
               "amount_min": {"type": "number", "description": "Smallest size of the amount, unsigned."},
               "amount_max": {"type": "number", "description": "Largest size of the amount, unsigned."}}


@tool("add_rule", "Store a categorisation rule and apply it to everything already "
      "imported. Returns how many transactions it matched. The text can be "
      "confined to the description or the counterparty, to money in or out, and "
      "to a range of amount sizes.",
      _RULE_TERMS, ["pattern"])
def _add_rule(pattern, category="", field="any", direction="any", amount_min=None, amount_max=None,
              match_mode="contains", account_id=None, kind=None, set_counterparty=None, set_kind=None, add_tag=None,
              set_owner=None):
    return {"pattern": pattern, "category": category,
            "applied": categories.add_rule(pattern, category, field=field, direction=direction,
                                           amount_min=amount_min, amount_max=amount_max, match_mode=match_mode,
                                           account_id=account_id, kind=kind, set_counterparty=set_counterparty,
                                           set_kind=set_kind, add_tag=add_tag, set_owner=set_owner)}


@tool("update_rule", "Change a rule's terms — the fields given replace the rule's; then "
      "every rule is re-applied, oldest first.",
      {"rule_id": {"type": "integer"}, **_RULE_TERMS}, ["rule_id", "pattern"])
def _update_rule(rule_id, pattern, category="", field="any", direction="any", amount_min=None, amount_max=None,
                 match_mode="contains", account_id=None, kind=None, set_counterparty=None, set_kind=None, add_tag=None,
                 set_owner=None):
    return {"rule_id": rule_id, "reapplied": categories.update_rule(
        int(rule_id), pattern, category, field=field, direction=direction,
        amount_min=amount_min, amount_max=amount_max, match_mode=match_mode, account_id=account_id,
        kind=kind, set_counterparty=set_counterparty, set_kind=set_kind, add_tag=add_tag, set_owner=set_owner)}


@tool("set_owner", "Say whose spending a transaction is: a person's id (see `people`), "
      "\"shared\" for the household, or empty for nobody. Optionally remember it as a rule "
      "for the same merchant.",
      {"txn_id": {"type": "integer"}, "owner": {"type": "string"},
       "remember": {"type": "boolean", "description": "Also store a rule from the row's text. Default false."}},
      ["txn_id"])
def _set_owner(txn_id, owner="", remember=False):
    owner = categories.set_owner(int(txn_id), owner)
    rule = None
    if remember and owner:
        with get_conn() as conn:
            row = conn.execute("SELECT description, counterparty FROM transactions WHERE id = ?", (int(txn_id),)).fetchone()
        pattern = categories.suggest_pattern(row["description"], row["counterparty"]) if row else ""
        if pattern:
            categories.add_rule(pattern, categories.KEEP, set_owner=owner)
            rule = pattern
    return {"txn_id": int(txn_id), "owner": owner, "rule": rule}


@tool("people", "The household: who the app knows, with the accounts each is on. "
      "An id from here is what `set_owner` and a rule's `set_owner` take.")
def _people():
    from . import people as _p
    by_account = _p.by_account()
    out = []
    for person in _p.all_people():
        out.append({"id": person["id"], "name": person["name"],
                    "birthday": person.get("birthday"),
                    "accounts": [acc for acc, names in by_account.items() if person["name"] in names]})
    return {"people": out}


@tool("unowned_spending", "The queue of spending nobody has claimed yet — the other side "
      "of `uncategorised`, for the Who spent page. Biggest first.",
      {"limit": {"type": "integer", "description": "Default 60, at most 500."},
       "person": PERSON})
def _unowned(limit=60, person=None):
    from . import expenses
    rows, total = expenses.unowned(int(limit or 60), _base(), _scope(person))
    return {"remaining": total, "transactions": rows}


@tool("who_spent", "The household's spending split between its people for a month "
      "(YYYY-MM) or the last N months: each person's own spending, their share of what "
      "was shared, the total; what nobody has claimed yet; per month and per category.",
      {"month": {"type": "string", "description": "A calendar month, YYYY-MM."},
       "months": {"type": "integer", "description": "The last N full months instead. Default 12."}})
def _who_spent(month=None, months=None):
    from . import expenses
    return expenses.split(_base(), people.scope(), month=month or None,
                          months=None if month else int(months or 12))


@tool("set_tags", "Set a transaction's tags — a comma-separated list of words; replaces what was there.",
      {"txn_id": {"type": "integer"}, "tags": {"type": "string"}}, ["txn_id", "tags"])
def _set_tags(txn_id, tags):
    return {"txn_id": txn_id, "tags": categories.set_tags(int(txn_id), tags)}


@tool("tags", "Every tag in use, with how many transactions carry it.")
def _tags():
    return {"tags": categories.all_tags()}


@tool("delete_rule", "Remove a rule by id and re-apply the remaining ones. "
      "Transactions it had categorised keep their category unless another "
      "rule claims them.", {"rule_id": {"type": "integer"}}, ["rule_id"])
def _delete_rule(rule_id):
    categories.delete_rule(int(rule_id))
    return {"deleted": int(rule_id), "reapplied": categories.apply_all()}


@tool("set_cashflow_spread", "How one payment counts on the Cash Flow page: \"normal\" as it was "
      "booked, 0 to leave it out of the monthly figures, or a number of months to spread it "
      "over from its own month — a car over 48. The transaction's amount is not changed.",
      {"txn_id": {"type": "integer"},
       "spread": {"type": "string", "description": "normal | 0 | a number of months"}},
      ["txn_id", "spread"])
def _set_spread(txn_id, spread):
    cashflow.set_spread(int(txn_id), spread)
    return {"txn_id": int(txn_id), "spread": spread}


@tool("cashflow_large", "The largest single payments in the window, with how each counts on the "
      "Cash Flow page.", {"months": {"type": "integer", "description": "Default 13."}})
def _cashflow_large(months=13):
    return {"large": cashflow.large(int(months or 13), _base(), people.scope())}


@tool("budget_report", "This month's spending per category against its budget, "
      "with the expected-to-date figure and a typical month for context.",
      {"person": PERSON})
def _budget(person=None):
    return cashflow.budget_report(_base(), account_ids=_scope(person))


@tool("set_budget", "Set a category's monthly budget in the base currency, or "
      "clear it with null / 0.",
      {"category": {"type": "string"}, "monthly": {"type": ["number", "null"]}},
      ["category"])
def _set_budget(category, monthly=None):
    if category not in categories.all_categories():
        raise ValueError(f"Unknown category {category!r}")
    cashflow.set_budget(category, float(monthly) if monthly is not None else None)
    return {"category": category, "monthly": monthly}


@tool("subscriptions", "Recurring payments the app has detected, with rhythm and "
      "yearly cost.", {"person": PERSON})
def _subscriptions(person=None):
    return subs.detect(_base(), account_ids=_scope(person))


@tool("add_transaction",
      "Type a transaction in, for an account nothing reports on. Kinds on a "
      "broker account: buy, sell, dividend, interest, fee, tax, deposit, "
      "withdrawal, transfer, other; elsewhere the same without buy/sell. Sizes "
      "are unsigned — the kind supplies the sign; transfer/other take "
      "`direction` in|out. A buy or sell needs isin, quantity and price.",
      {"account_id": {"type": "integer"}, "kind": {"type": "string"},
       "txn_date": {"type": "string", "description": "ISO date, not in the future."},
       "amount": {"type": "number", "description": "For everything but a trade."},
       "description": {"type": "string"}, "counterparty": {"type": "string"},
       "category": {"type": "string"}, "direction": {"type": "string", "enum": ["in", "out"]},
       "isin": {"type": "string"}, "security_name": {"type": "string"},
       "quantity": {"type": "number"}, "price": {"type": "number"},
       "fee": {"type": "number"}, "tax": {"type": "number"},
       "total": {"type": "number", "description": "The broker's total, if known."}},
      ["account_id", "kind", "txn_date"])
def _add_transaction(account_id, kind, txn_date, amount=None, description=None,
                     counterparty=None, category=None, direction=None, isin=None,
                     security_name=None, quantity=None, price=None, fee=None,
                     tax=None, total=None):
    account = _account(account_id)
    form = {"kind": kind, "txn_date": txn_date, "amount": _num_str(amount),
            "description": description, "counterparty": counterparty,
            "category": category, "direction": direction, "isin": isin,
            "security_name": security_name, "quantity": _num_str(quantity),
            "price": _num_str(price), "fee": _num_str(fee), "tax": _num_str(tax),
            "total": _num_str(total)}
    txn_id = manual.add_transaction(account, form)
    with get_conn() as conn:
        row = dict(conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone())
    return {k: row.get(k) for k in ("id", "account_id", "txn_date", "description",
                                    "amount", "currency", "kind", "category", "isin",
                                    "quantity", "price")}


_UNSET = object()          # an argument not given, as opposed to given as null


def _given(fields: dict) -> dict:
    return {k: v for k, v in fields.items() if v is not _UNSET}


_TXN_KEYS = ("id", "account_id", "txn_date", "description", "counterparty", "amount",
             "currency", "kind", "category", "isin", "security_name", "quantity", "price",
             "fee", "tax", "source", "edited_at")


@tool("update_transaction",
      "Correct one transaction: change only the fields given. Signed figures as "
      "the app stores them — amount is the cash effect from the account's side "
      "(a buy negative, a sale or dividend positive), quantity positive for units "
      "in, negative for units out. Works on imported rows too, and the correction "
      "survives the next import. `negate_amount` flips the sign of the amount.",
      {"txn_id": {"type": "integer"}, "txn_date": {"type": "string"}, "kind": {"type": "string"},
       "description": {"type": "string"}, "counterparty": {"type": "string"},
       "amount": {"type": "number"}, "quantity": {"type": "number"}, "price": {"type": "number"},
       "fee": {"type": "number"}, "tax": {"type": "number"}, "isin": {"type": "string"},
       "security_name": {"type": "string"}, "category": {"type": "string"},
       "negate_amount": {"type": "boolean"}},
      ["txn_id"])
def _update_transaction(txn_id, negate_amount=False, txn_date=_UNSET, kind=_UNSET, description=_UNSET, counterparty=_UNSET, amount=_UNSET, quantity=_UNSET, price=_UNSET, fee=_UNSET, tax=_UNSET, isin=_UNSET, security_name=_UNSET, category=_UNSET):
    rows = manual.patch_transactions([txn_id], _given({"txn_date": txn_date, "kind": kind, "description": description, "counterparty": counterparty, "amount": amount, "quantity": quantity, "price": price, "fee": fee, "tax": tax, "isin": isin, "security_name": security_name, "category": category}), negate_amount=bool(negate_amount))
    return {k: rows[0].get(k) for k in _TXN_KEYS}


@tool("update_transactions",
      "The same correction on many transactions at once — the fields given are "
      "set on every id; `negate_amount` flips each one's sign. For the case of a "
      "whole import whose buys came in positive: the ids and negate_amount.",
      {"txn_ids": {"type": "array", "items": {"type": "integer"}},
       "txn_date": {"type": "string"}, "kind": {"type": "string"},
       "description": {"type": "string"}, "counterparty": {"type": "string"},
       "amount": {"type": "number"}, "quantity": {"type": "number"}, "price": {"type": "number"},
       "fee": {"type": "number"}, "tax": {"type": "number"}, "isin": {"type": "string"},
       "security_name": {"type": "string"}, "category": {"type": "string"},
       "negate_amount": {"type": "boolean"}},
      ["txn_ids"])
def _update_transactions(txn_ids, negate_amount=False, txn_date=_UNSET, kind=_UNSET, description=_UNSET, counterparty=_UNSET, amount=_UNSET, quantity=_UNSET, price=_UNSET, fee=_UNSET, tax=_UNSET, isin=_UNSET, security_name=_UNSET, category=_UNSET):
    rows = manual.patch_transactions(list(txn_ids), _given({"txn_date": txn_date, "kind": kind, "description": description, "counterparty": counterparty, "amount": amount, "quantity": quantity, "price": price, "fee": fee, "tax": tax, "isin": isin, "security_name": security_name, "category": category}), negate_amount=bool(negate_amount))
    return {"changed": len(rows), "transactions": [{k: r.get(k) for k in _TXN_KEYS} for r in rows]}


@tool("delete_transactions",
      "Remove transactions by id, whatever their source. An imported row comes "
      "back if the same file is imported again — prefer a correction where one "
      "will do, it survives re-imports.",
      {"txn_ids": {"type": "array", "items": {"type": "integer"}}}, ["txn_ids"])
def _delete_transactions(txn_ids):
    return {"deleted": manual.delete_transactions(list(txn_ids))}


@tool("set_balance", "Record an account's balance as of a day, for an account "
      "nothing reports on.",
      {"account_id": {"type": "integer"}, "amount": {"type": "number"},
       "as_of": {"type": "string", "description": "ISO date; default today."}},
      ["account_id", "amount"])
def _set_balance(account_id, amount, as_of=None):
    account = _account(account_id)
    return manual.set_balance(account, {"amount": _num_str(amount),
                                        "as_of": as_of or date.today().isoformat()})


BOARDS = {"value": (screener, "value"), "income": (screener, "income"),
          "etf": (screener_etf, "growth"), "etf_dividend": (screener_etf, "dividend")}

_ROW_KEYS = {
    "value": ("drawdown", "off_52w_low", "effective_pe", "pe_basis", "dividend_yield",
              "payout_ratio", "return_on_equity", "debt_to_equity", "sector", "country",
              "market_cap", "price", "currency"),
    "income": ("dividend_yield", "dividend_growth", "revenue_growth", "earnings_growth",
               "payout_ratio", "fcf_payout", "effective_pe", "return_on_equity",
               "sector", "country", "market_cap", "price", "currency"),
    "etf": ("ter", "ter_source", "cagr_5y", "cagr_3y", "cagr_1y", "volatility_1y",
            "max_drawdown", "dist", "region", "total_assets", "history_years"),
    "etf_dividend": ("div_yield_ttm", "ter", "ter_source", "net_yield", "div_growth",
                     "div_worst_cut", "cagr_5y", "max_drawdown", "div_events_12m",
                     "dist", "region", "total_assets"),
}


@tool("share_ideas",
      "One of the four Share Ideas boards, ranked. value: fallen, cheap, quality, "
      "pays. income: high dividend still growing. etf: high growth, low TER. "
      "etf_dividend: high yield, low TER. Rates are fractions (0.034 = 3.4%). "
      "A score is a sorting device, not advice; the flags are the caveats.",
      {"board": {"type": "string", "enum": list(BOARDS)},
       "top": {"type": "integer", "description": "Default 25, at most 500."},
       "min_score": {"type": "number"},
       "pea_only": {"type": "boolean", "description": "Only names a French PEA can hold."},
       "include_gated": {"type": "boolean", "description": "Also list what was "
                         "excluded before scoring, with the reason."}},
      ["board"])
def _share_ideas(board, top=25, min_score=None, pea_only=False, include_gated=False):
    if board not in BOARDS:
        raise ValueError(f"board must be one of {list(BOARDS)}")
    module, profile = BOARDS[board]
    with get_conn() as conn:
        data = module.results(conn, top=max(1, min(int(top or 25), 500)),
                              pea_only=bool(pea_only), include_failed=bool(include_gated),
                              min_score=min_score, profile=profile)
    keys = ("symbol", "name", "score", "coverage", "pillars", "flags", "pea_eligible",
            "held", "watch_status", "note", "fetched_at") + _ROW_KEYS[board]
    trim = lambda r: {k: r.get(k) for k in keys}   # noqa: E731
    return {"board": board, "pillar_order": data["pillar_order"],
            "universe_size": data["universe_size"], "last_refresh": data["last_refresh"],
            "ranked": [trim(r) for r in data["ranked"]],
            "gated_count": data["rejected_count"],
            "gated": [trim(r) | {"gate_failed": r["gate_failed"]} for r in data["rejected"]]}


@tool("watch_idea", "Star, dismiss, or clear the mark on a share-ideas symbol. "
      "One list serves all four boards.",
      {"symbol": {"type": "string"},
       "status": {"type": "string", "enum": ["watch", "dismissed", "clear"]},
       "note": {"type": "string"}},
      ["symbol", "status"])
def _watch(symbol, status, note=None):
    with get_conn() as conn:
        return screener.set_watch(conn, symbol, None if status == "clear" else status, note)


@tool("sync_health", "Every bank connection, graded green/yellow/red, with the "
      "last sync and when the consent expires.")
def _health():
    links = banksync.health()
    # A ledger that holds a booking twice — the sync's bare copy beside
    # a move-in's — is a health matter too: every sum over it is doubled.
    # It goes on the link of the account it concerns; `health()` returns
    # a list and always has.
    from . import ledger
    twins = ledger.doubled()
    for link in links:
        n = twins.get(link.get("account_id"))
        if n:
            link["doubled_rows"] = n
            link["doubled_hint"] = ("bank rows with an enriched twin — `heal_twins` "
                                    "removes the bare copies")
    return links


@tool("forget_removed", "Forget the rows removed by hand from an account, so the next import or "
      "sync books them again. A removed row's id is remembered forever otherwise — even "
      "across deleting and re-making the account.",
      {"account_id": {"type": "integer"}}, ["account_id"])
def _forget_removed(account_id):
    return {"forgotten": manual.forget_removed(int(account_id))}


@tool("heal_twins", "Remove the bank sync's bare copy of every booking a move-in or a file "
      "import also holds — the same booking under two ids, which doubles every sum. "
      "The enriched copy is kept. Returns how many rows went.",
      {"account_id": {"type": "integer", "description": "One account; all when left out."}})
def _heal_twins(account_id=None):
    from . import ledger
    acc = int(account_id) if account_id else None
    return {"removed": ledger.heal_twins(acc), "trades": ledger.heal_trade_twins(acc)}


@tool("sync_banks", "Pull balance and transactions from every connected bank, now. "
      "Takes a few seconds per account.")
def _sync():
    if not banksync.credentials_present():
        raise ValueError("Enable Banking is not configured.")
    return banksync.sync_all()


@tool("refresh_prices", "Fetch the market price of every holding, now.")
def _refresh_prices():
    return prices.refresh(_base())


@tool("refresh_share_ideas", "Refetch the share-ideas caches in the background. "
      "Takes a few minutes; call `share_ideas` afterwards.",
      {"force": {"type": "boolean", "description": "Everything, not only what "
                 "is older than a day."}})
def _refresh_ideas(force=False):
    started = screener_jobs.start_background(force=bool(force))
    return {"started": started, "running": screener_jobs.is_running(),
            "status": screener_jobs.status()}


# ─── JSON-RPC ────────────────────────────────────────────────────────

def _ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


def _call(name: str, arguments: dict) -> dict:
    """Run one tool. A ValueError is the tool's own sentence to the
    model and is returned as an error *result*, which is what the
    protocol wants for "the call ran and did not work"; a missing tool
    or bad argument shape is a JSON-RPC error instead."""
    fn = _HANDLERS.get(name)
    if fn is None:
        raise KeyError(name)
    sig = inspect.signature(fn)
    unknown = set(arguments) - set(sig.parameters)
    if unknown:
        raise TypeError(f"unknown argument(s): {', '.join(sorted(unknown))}")
    missing = [p for p, v in sig.parameters.items()
               if v.default is inspect.Parameter.empty and p not in arguments]
    if missing:
        raise TypeError(f"missing argument(s): {', '.join(missing)}")
    try:
        result = fn(**arguments)
    except ValueError as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    text = json.dumps(result, ensure_ascii=False, default=str)
    out = {"content": [{"type": "text", "text": text}]}
    if isinstance(result, dict):
        out["structuredContent"] = result
    return out


def dispatch(message) -> dict | None:
    """One JSON-RPC message → one response, or None for a notification."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" \
            or not isinstance(message.get("method"), str):
        return _err(message.get("id") if isinstance(message, dict) else None,
                    INVALID_REQUEST, "Not a JSON-RPC 2.0 request.")
    method, id_ = message["method"], message.get("id")
    params = message.get("params") or {}
    if method.startswith("notifications/"):
        return None                          # acknowledged, nothing to say
    if method == "initialize":
        asked = str(params.get("protocolVersion") or "")
        return _ok(id_, {
            "protocolVersion": asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        })
    if method == "ping":
        return _ok(id_, {})
    if method == "tools/list":
        return _ok(id_, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _err(id_, INVALID_PARAMS, "arguments must be an object")
        try:
            return _ok(id_, _call(str(name), arguments))
        except KeyError:
            return _err(id_, INVALID_PARAMS, f"Unknown tool {name!r}")
        except TypeError as exc:
            return _err(id_, INVALID_PARAMS, str(exc))
        except Exception as exc:                          # noqa: BLE001
            return _err(id_, INTERNAL, f"{type(exc).__name__}: {exc}")
    return _err(id_, METHOD_NOT_FOUND, f"Method not found: {method}")


def handle(body) -> tuple[int, object]:
    """A POST body → (HTTP status, JSON body or None).

    A single notification gets 202 and no body; a batch gets a list of
    the responses its requests produced. Everything is answered in
    English: the reader is a program, not the person whose UI language
    is set.
    """
    g._language = "en"
    if isinstance(body, list):
        if not body:
            return 400, _err(None, INVALID_REQUEST, "Empty batch.")
        answers = [r for r in (dispatch(m) for m in body) if r is not None]
        return (200, answers) if answers else (202, None)
    answer = dispatch(body)
    return (200, answer) if answer is not None else (202, None)
