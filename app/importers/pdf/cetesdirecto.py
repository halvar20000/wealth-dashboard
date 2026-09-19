"""cetesdirecto (Mexico) — the Estado de Cuenta's Movimientos del
período: COMPRA, AMORTIZACION (redemption), the ISR withheld on it as a
row of its own under the same folio, COMPSI reinvestments."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

NUM = r"[\d,]+\.\d+"
DATE = r"\d{2}/\d{2}/\d{2}"
ROW = re.compile(r"^(" + DATE + r") (" + DATE + r") ([A-Z]{3}\d+)([A-Z]+) (\S+) (\S+) ([\d,]+) (.*?)(" + NUM + r") (" + NUM + r") (-?" + NUM + r")$")


def movimientos(text: str) -> str:
    """Every row gets its cash movement (Abono − Cargo) and currency at
    the end; an ISR row goes onto the redemption of the same folio as
    [tax x], the proceeds netted."""
    lines = text.splitlines()
    rows = {i: m for i, m in ((i, ROW.match(l)) for i, l in enumerate(lines)) if m}
    taxes = {m.group(3): float(m.group(9).replace(",", "")) for m in rows.values() if m.group(4) == "ISR"}
    drop = {i for i, m in rows.items() if m.group(4) == "ISR" and any(
        r.group(3) == m.group(3) and r.group(4) == "AMORTIZACION" for r in rows.values())}
    for i, m in rows.items():
        if i in drop:
            continue
        cash = float(m.group(10).replace(",", "")) - float(m.group(9).replace(",", ""))
        tax = taxes.get(m.group(3), 0.0) if m.group(4) == "AMORTIZACION" else 0.0
        lines[i] += f" AMT {cash - tax:.2f} MXN" + (f" [tax {tax:.2f}]" if tax else "")
    return "\n".join(l for i, l in enumerate(lines) if i not in drop)


FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") "],
    "type": [r"^" + DATE + r" " + DATE + r" [A-Z]{3}\d+(?P<type>[A-Z]+) "],
    "security": [r"^" + DATE + r" " + DATE + r" [A-Z]{3}\d+[A-Z]+ (?P<name>\S+ \S+) (?P<shares>[\d,]+) (?:(?P<price>" + NUM + r") )?"],
    "ref": [r"^" + DATE + r" " + DATE + r" (?P<ref>[A-Z]{3}\d+)"],
    "amount": [r" AMT (?P<amount>-?[\d.]+) (?P<currency>MXN)"],
    "taxes": [r"\[tax (?P<tax>" + NUM + r")\]"],
}

SPEC = Spec(
    slug="cetesdirecto_pdf",
    label="cetesdirecto — Estado de Cuenta PDF",
    corpus="cetesdirecto",
    marks=[r"cetesdirecto", r"Contrato/Cuenta CLABE"],
    number="en",
    preprocess=movimientos,
    docs=[
        Doc(kind="rows", when=r"^Movimientos del per.odo", block=r"^" + DATE + r" " + DATE + r" [A-Z]{3}\d+", fields=FIELDS,
            kinds={r"^COMPRA|^COMPSI": "buy", r"^AMORTIZACION|^VENTA": "sell", r"^ISR": "tax"}),
    ],
)
