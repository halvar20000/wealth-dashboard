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
       "limit": {"type": "integer", "description": "Default 100, at most 500."},
       "person": PERSON})
def _transactions(q=None, account_id=None, category=None, kind=None,
                  date_from=None, date_to=None, limit=100, person=None):
    where, params = ["1=1"], []
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
            f"t.counterparty, t.amount, t.currency, t.kind, t.category, t.isin, "
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


_RULE_TERMS = {"pattern": {"type": "string", "description": "Text to match, three characters at least."},
               "category": {"type": "string"},
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
      _RULE_TERMS, ["pattern", "category"])
def _add_rule(pattern, category, field="any", direction="any", amount_min=None, amount_max=None):
    return {"pattern": pattern, "category": category,
            "applied": categories.add_rule(pattern, category, field=field, direction=direction,
                                           amount_min=amount_min, amount_max=amount_max)}


@tool("update_rule", "Change a rule's terms — the fields given replace the rule's; then "
      "every rule is re-applied, oldest first.",
      {"rule_id": {"type": "integer"}, **_RULE_TERMS}, ["rule_id", "pattern", "category"])
def _update_rule(rule_id, pattern, category, field="any", direction="any", amount_min=None, amount_max=None):
    return {"rule_id": rule_id, "reapplied": categories.update_rule(
        int(rule_id), pattern, category, field=field, direction=direction,
        amount_min=amount_min, amount_max=amount_max)}


@tool("delete_rule", "Remove a rule by id and re-apply the remaining ones. "
      "Transactions it had categorised keep their category unless another "
      "rule claims them.", {"rule_id": {"type": "integer"}}, ["rule_id"])
def _delete_rule(rule_id):
    categories.delete_rule(int(rule_id))
    return {"deleted": int(rule_id), "reapplied": categories.apply_all()}


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
    return banksync.health()


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
