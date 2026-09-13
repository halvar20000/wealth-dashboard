"""CSV out — the transactions and the holdings, filtered as the page is.

The data is the user's, and a dashboard that only lets it in is a
dashboard that keeps it. So every list has an "Export as CSV" that
writes exactly what the page shows — the same filters, every row
rather than the first four hundred — in a file a spreadsheet opens
right and this app reads back through a mapping.

"Opens right" is a locale question, so the file follows the language
of the request: a German, French or Spanish reader gets semicolons and
a decimal comma, which is what their Excel expects; an English one
gets commas and a point. Either can be forced with `?sep=,` or
`?sep=;`. Dates are ISO in every case; a UTF-8 byte-order mark is
written so Excel does not guess the encoding wrong.
"""

from __future__ import annotations

import csv
import io

from . import i18n

TXN_COLUMNS = ("date", "account", "kind", "description", "counterparty", "amount",
               "currency", "category", "tags", "isin", "security_name", "quantity", "price",
               "fee", "tax", "source", "id")
HOLDING_COLUMNS = ("isin", "name", "accounts", "quantity", "price", "price_as_of",
                   "currency", "net_invested", "value", "unrealised", "realised",
                   "twr", "twr_annual", "mwr")


def dialect(sep: str | None = None) -> tuple[str, str]:
    """(delimiter, decimal) for this request."""
    if sep in (",", ";"):
        return sep, ("," if sep == ";" else ".")
    return (";", ",") if i18n.active() in ("de", "fr", "es") else (",", ".")


def _num(v, decimal: str) -> str:
    if v is None:
        return ""
    s = f"{v:.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    return s.replace(".", decimal) if decimal != "." else s


def _money(v, decimal: str) -> str:
    if v is None:
        return ""
    s = f"{v:.2f}"
    return s.replace(".", decimal) if decimal != "." else s


def write(columns: tuple[str, ...], rows: list[list], sep: str | None = None) -> bytes:
    delimiter, _ = dialect(sep)
    out = io.StringIO()
    w = csv.writer(out, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow(columns)
    w.writerows(rows)
    return ("﻿" + out.getvalue()).encode("utf-8")


def transactions(rows: list[dict], sep: str | None = None) -> bytes:
    _, dec = dialect(sep)
    return write(TXN_COLUMNS, [[
        r["txn_date"], r.get("account_name", ""), r["kind"], r["description"] or "",
        r.get("counterparty") or "", _money(r["amount"], dec), r["currency"],
        r.get("category") or "", r.get("tags") or "", r.get("isin") or "", r.get("security_name") or "",
        _num(r.get("quantity"), dec), _num(r.get("price"), dec), _num(r.get("fee"), dec),
        _num(r.get("tax"), dec), r.get("source") or "", r["id"]] for r in rows], sep)


def holdings(items: list[dict], sep: str | None = None) -> bytes:
    _, dec = dialect(sep)
    def pct(v):
        return _num(round(v * 100, 2), dec) if v is not None else ""
    return write(HOLDING_COLUMNS, [[
        h["isin"], h.get("name") or "", ", ".join(sorted(set(h.get("accounts") or []))),
        _num(h.get("quantity"), dec), _num(h.get("price"), dec), h.get("price_as_of") or "",
        h.get("currency") or "", _money(h.get("net_invested"), dec), _money(h.get("value"), dec),
        _money(h.get("unrealised"), dec), _money(h.get("realised"), dec),
        pct((h.get("perf") or {}).get("twr")), pct((h.get("perf") or {}).get("twr_annual")),
        pct((h.get("perf") or {}).get("mwr"))] for h in items], sep)


def response(payload: bytes, filename: str):
    from flask import Response
    return Response(payload, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
