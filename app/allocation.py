"""Where the money is, by what it is — and where it was meant to be.

Three ways of cutting the same portfolio, each a dimension with a
share per key and, if the user says so, a target:

  * **asset class** — equity, bonds, real estate, commodities, cash,
    crypto. Cash is the accounts' balances; everything else is the
    holdings, each classified once.
  * **region** — world, Europe, North America, emerging markets, Asia
    Pacific, Switzerland, Germany, or whatever the user types.
  * **bucket** — the user's own taxonomy: Core and Satellite, Safe and
    Play, Mine and Ours. Nothing is guessed here; it is theirs.

A holding's class and region are guessed once from its name and from
what Yahoo says it is — an ETF called "MSCI World" is world equity —
and the guess is marked as one until a person confirms or changes it.
The targets are percentages per key; the page shows the drift from
them and, given an amount about to be invested, how to spread it so
the drift shrinks without selling anything: the underweight keys get
it in proportion to their shortfall. Rebalancing by selling is left to
the person, because selling has tax consequences this app does not
know.

Nothing here is a valuation of its own: the values come from
overview.summary(), in the base currency, the same figures every
other page shows.
"""

from __future__ import annotations

import re

from . import i18n
from .db import get_conn

ASSET_CLASSES = ("equity", "bond", "real_estate", "commodity", "cash", "crypto", "other")
REGIONS = ("world", "europe", "north_america", "emerging", "asia_pacific",
           "switzerland", "germany", "other")
DIMENSIONS = ("asset_class", "region", "bucket")


CLASS_NAMES = {"equity": "Equity", "bond": "Bonds", "real_estate": "Real estate", "commodity": "Commodities",
               "cash": "Cash", "crypto": "Crypto", "other": "Other"}
REGION_NAMES = {"world": "World", "europe": "Europe", "north_america": "North America", "emerging": "Emerging markets",
                "asia_pacific": "Asia Pacific", "switzerland": "Switzerland", "germany": "Germany", "other": "Other"}


def class_label(key: str | None) -> str:
    return i18n.t(f"{CLASS_NAMES.get(key or 'other', 'Other')} [class]")


def region_label(key: str | None) -> str:
    return i18n.t(f"{REGION_NAMES.get(key or 'other', 'Other')} [region]")


# ─── Guessing ────────────────────────────────────────────────────────

_CLASS_WORDS = (
    ("bond", r"\b(bond|bonds|anleihe|anleihen|treasury|treasuries|gilt|gilts|obligation|obligations|"
             r"govt|government|corporate|corp\.?|aggregate|high yield|renten|staatsanleihen|euro gov|"
             r"fixed income|money market|geldmarkt|overnight|eonia|ester|€str)\b"),
    ("real_estate", r"\b(reit|reits|real estate|immobilien|property|immobilier|epra)\b"),
    ("commodity", r"\b(gold|silver|silber|commodit|rohstoff|oil|crude|metal|xetra-gold|euwax gold|wti|brent)\b"),
    ("crypto", r"\b(bitcoin|ethereum|crypto|krypto|btc|eth|solana)\b"),
)
_REGION_WORDS = (
    ("world", r"\b(world|all-world|all world|acwi|global|welt|monde|mundo|all country|developed)\b"),
    ("emerging", r"\b(emerging|em\b|schwellenl|émergents|emergentes|frontier)\b"),
    ("switzerland", r"\b(switzerland|swiss|schweiz|suisse|suiza|smi|spi|sli)\b"),
    ("germany", r"\b(germany|deutschland|dax|mdax|sdax|tecdax|german)\b"),
    ("north_america", r"\b(usa|u\.s\.|us\b|s&p|s&p 500|sp500|nasdaq|dow|russell|north america|nordamerika|"
                      r"america|amerika|canada|kanada|msci usa)\b"),
    ("asia_pacific", r"\b(japan|nikkei|topix|asia|pacific|pazifik|china|india|korea|australia|apac)\b"),
    ("europe", r"\b(europe|europa|euro stoxx|stoxx|eurozone|emu|euro\b|uk|ftse 100|cac|ibex|mib|nordic|"
               r"europ\.?|eur\.)\b"),
)


def guess(name: str | None, quote_type: str | None = None, isin: str | None = None) -> dict:
    """{asset_class, region} from what the name and Yahoo say."""
    text = f" {(name or '').lower()} "
    out = {"asset_class": "equity", "region": None}
    if (isin or "").upper().startswith("CRYPTO:") or (quote_type or "").upper() == "CRYPTOCURRENCY":
        out["asset_class"] = "crypto"
        return out
    for key, pattern in _CLASS_WORDS:
        if re.search(pattern, text):
            out["asset_class"] = key
            break
    for key, pattern in _REGION_WORDS:
        if re.search(pattern, text):
            out["region"] = key
            break
    # A single share with a country in its ISIN: the ISIN says where.
    if out["region"] is None and (quote_type or "").upper() == "EQUITY" and isin:
        cc = isin[:2].upper()
        out["region"] = {"CH": "switzerland", "DE": "germany", "US": "north_america", "CA": "north_america",
                         "JP": "asia_pacific", "AU": "asia_pacific", "HK": "asia_pacific", "CN": "asia_pacific",
                         "KR": "asia_pacific", "IN": "asia_pacific"}.get(cc, "europe" if cc in
                         ("FR", "NL", "GB", "IE", "IT", "ES", "SE", "DK", "FI", "NO", "BE", "AT", "PT", "LU") else None)
    return out


# ─── Storage ─────────────────────────────────────────────────────────

def classes(isins: list[str], names: dict[str, str] | None = None,
            quote_types: dict[str, str] | None = None) -> dict[str, dict]:
    """The classification of every ISIN given, guessing and storing
    the ones not seen before, so the page never shows a blank."""
    names, quote_types = names or {}, quote_types or {}
    with get_conn() as conn:
        rows = {r["isin"]: dict(r) for r in conn.execute("SELECT * FROM security_classes")}
        for isin in isins:
            if isin in rows:
                continue
            g = guess(names.get(isin), quote_types.get(isin), isin)
            conn.execute("INSERT OR IGNORE INTO security_classes (isin, asset_class, region, bucket, guessed) "
                         "VALUES (?, ?, ?, NULL, 1)", (isin, g["asset_class"], g["region"]))
            rows[isin] = {"isin": isin, "asset_class": g["asset_class"], "region": g["region"],
                          "bucket": None, "guessed": 1}
    return {i: rows[i] for i in isins if i in rows}


def set_class(isin: str, asset_class: str | None, region: str | None, bucket: str | None) -> None:
    asset_class = asset_class if asset_class in ASSET_CLASSES else "other"
    region = (region or "").strip()[:40] or None
    bucket = " ".join((bucket or "").split())[:40] or None
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO security_classes (isin, asset_class, region, bucket, guessed, updated_at) "
            "VALUES (?, ?, ?, ?, 0, datetime('now')) ON CONFLICT(isin) DO UPDATE SET asset_class = excluded.asset_class, "
            "region = excluded.region, bucket = excluded.bucket, guessed = 0, updated_at = datetime('now')",
            (isin, asset_class, region, bucket))


def targets(dimension: str) -> dict[str, float]:
    with get_conn() as conn:
        return {r["key"]: r["target_pct"] for r in conn.execute(
            "SELECT key, target_pct FROM allocation_targets WHERE dimension = ?", (dimension,))}


def set_targets(dimension: str, values: dict[str, float | None]) -> None:
    """Replace the targets of one dimension. A blank clears a key; the
    targets need not sum to a hundred — a person may only care about
    one of them — but they may not exceed it."""
    if dimension not in DIMENSIONS:
        raise ValueError(f"Unknown dimension {dimension!r}")
    from .importers.base import parse_decimal
    clean: dict[str, float] = {}
    for key, raw in values.items():
        if raw in (None, ""):
            continue
        pct = parse_decimal(str(raw))
        if pct is None or pct < 0 or pct > 100:
            raise ValueError(i18n.t("A target is a percentage between 0 and 100."))
        if pct > 0:
            clean[key.strip()[:40]] = pct
    if sum(clean.values()) > 100.0001:
        raise ValueError(i18n.t("The targets add up to more than a hundred percent."))
    with get_conn() as conn:
        conn.execute("DELETE FROM allocation_targets WHERE dimension = ?", (dimension,))
        for key, pct in clean.items():
            conn.execute("INSERT INTO allocation_targets (dimension, key, target_pct) VALUES (?, ?, ?)",
                         (dimension, key, pct))


# ─── The breakdown ───────────────────────────────────────────────────

def breakdown(summary: dict, contribution: float = 0.0) -> dict:
    """The three dimensions from an overview summary: per key the
    value, the share, the target, the drift, and — given a
    contribution — how much of it goes there. Also the holdings with
    their classification, for the editing table."""
    holdings = [h for h in summary["holdings"] if h.get("value_base")]
    isins = [h["isin"] for h in summary["holdings"]]
    with get_conn() as conn:
        qt = {r["isin"]: r["quote_type"] for r in conn.execute("SELECT isin, quote_type FROM securities")}
    cls = classes(isins, {h["isin"]: h.get("name") for h in summary["holdings"]}, qt)
    cash = summary.get("cash") or 0.0
    total = sum(h["value_base"] for h in holdings) + cash
    out = {"total": total, "cash": cash, "dimensions": {}, "holdings": []}
    for h in summary["holdings"]:
        c = cls.get(h["isin"], {})
        out["holdings"].append({**{k: h.get(k) for k in ("isin", "name", "value_base", "currency", "quantity")},
                                "asset_class": c.get("asset_class") or "other", "region": c.get("region"),
                                "bucket": c.get("bucket"), "guessed": bool(c.get("guessed", 1))})
    for dim in DIMENSIONS:
        values: dict[str, float] = {}
        for h in holdings:
            c = cls.get(h["isin"], {})
            key = c.get(dim)
            if dim == "asset_class":
                key = key or "other"
            elif not key:
                key = "unassigned"
            values[key] = values.get(key, 0.0) + h["value_base"]
        if dim == "asset_class" and cash:
            values["cash"] = values.get("cash", 0.0) + cash
        tg = targets(dim)
        keys = sorted(set(values) | set(tg), key=lambda k: -(values.get(k, 0.0)))
        rows = []
        for k in keys:
            v = values.get(k, 0.0)
            share = (v / total * 100) if total > 0 else 0.0
            t = tg.get(k)
            rows.append({"key": k, "value": v, "share": share, "target": t,
                         "drift": (share - t) if t is not None else None,
                         "gap": ((t / 100 * total) - v) if t is not None else None})
        # Spreading a contribution: to the keys below target, in
        # proportion to how far below. Buying only, no selling.
        if contribution > 0 and tg:
            after = total + contribution
            short = {r["key"]: max(0.0, (r["target"] / 100 * after) - r["value"]) for r in rows if r["target"] is not None}
            need = sum(short.values())
            for r in rows:
                s_ = short.get(r["key"], 0.0)
                r["buy"] = (contribution * s_ / need) if need > 0 else (contribution * (r["target"] or 0) / 100 if r["target"] else 0.0)
        out["dimensions"][dim] = {"rows": rows, "has_targets": bool(tg),
                                  "target_sum": sum(tg.values()) if tg else 0.0}
    return out
