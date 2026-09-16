"""The Income page: every payslip on record, per earner.

A payslip is imported into the account the net lands in (see
importers/payslip.py); this reads them back grouped by the earner the
sheet names, with the totals a year's tax return asks for and the
pension inflow a retirement forecast wants. Nothing here is computed
from the bank: the bank saw the net, the sheet saw the rest.
"""

from __future__ import annotations

import json
from collections import defaultdict

from . import people
from .db import get_conn


def earners(account_ids: list[int] | None = None) -> list[dict]:
    """[{name, employer, currency, months: [...], totals: {...}, years: {...}}]
    in the order the earners' names sort, the account scope respected."""
    only, params = people.sql_in(account_ids, "account_id")
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            f"SELECT * FROM payslips WHERE 1=1{only} ORDER BY employee, period", params)]
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        r["lines"] = json.loads(r["lines"] or "[]")
        by[r["employee"]].append(r)
    out = []
    for name, months in by.items():
        employers = []
        for m in months:
            if m["employer"] not in employers:
                employers.append(m["employer"])
        years: dict[str, dict] = {}
        for m in months:
            years.setdefault(m["period"][:4], []).append(m)
        out.append({"name": name, "employer": ", ".join(employers), "currency": months[-1]["currency"],
                    "months": months, "totals": totals(months),
                    # Newest year first, newest month first within it — the
                    # order a table is read in.
                    "years": [{"year": y, "totals": totals(ms), "months": list(reversed(ms))}
                              for y, ms in sorted(years.items(), reverse=True)],
                    "employer_side_known": all(m["employer_side_known"] for m in months)})
    return out


def totals(months: list[dict]) -> dict:
    gross = sum(m["gross"] for m in months)
    tax = sum(m["tax"] for m in months)
    emp_p = sum(m["employee_pension"] for m in months)
    er_p = sum(m["employer_pension"] for m in months)
    er_s = sum(m["employer_social"] for m in months)
    return {
        "months": len(months),
        "gross": round(gross, 2),
        "net": round(sum(m["net_paid"] for m in months), 2),
        "tax": round(tax, 2),
        "employee_social": round(sum(m["employee_social"] for m in months), 2),
        "employee_pension": round(emp_p, 2),
        "other_deductions": round(sum(m["other_deductions"] for m in months), 2),
        "employer_pension": round(er_p, 2),
        "employer_social": round(er_s, 2),
        "employer_cost": round(gross + er_p + er_s, 2),
        "bonus": round(sum(m["bonus"] for m in months), 2),
        "tax_rate": (abs(tax) / gross) if gross else 0.0,
        "pension_inflow": round(abs(emp_p) + er_p, 2),
    }


def delete(payslip_id: int) -> int:
    """The statement and the rows it booked, together."""
    with get_conn() as conn:
        row = conn.execute("SELECT account_id, import_id FROM payslips WHERE id = ?", (payslip_id,)).fetchone()
        if row is None:
            return 0
        if row["import_id"]:
            conn.execute("DELETE FROM transactions WHERE import_id = ?", (row["import_id"],))
        return conn.execute("DELETE FROM payslips WHERE id = ?", (payslip_id,)).rowcount
