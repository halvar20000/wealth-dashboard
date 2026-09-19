"""Directa SIM (Italy) — the nota informativa of an order: the security
on the "per l'acquisto di" line, the execution row, the totals."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{1,2}\.\d{2}\.\d{4}"

FIELDS = {
    "security": [r"^per (?:l'acquisto|la vendita) di: (?P<shares>" + NUM + r") (?P<name>.+?) ISIN " + ISIN],
    "date": [r"^(?P<date>" + DATE + r") \d{2}:\d{2}:\d{2} Eseguito "],
    "price": [r"^" + DATE + r" \d{2}:\d{2}:\d{2} Eseguito (?:\([^)]*\) )?" + NUM + r" (?P<price>" + NUM + r") "],
    "amount": [r"^Totale a Vs\. (?:Debito|Credito) ?:? (?:" + NUM + r" )?(?P<amount>" + NUM + r")$"],
    "ref": [r"per l'ordine (?P<ref>\S+)"],
    "fees": [r"^Commissioni: (?P<sign>-?)(?P<fee>" + NUM + r")$"],
    "taxes": [r"^Ritenuta: (?P<sign>-?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="directa_pdf",
    label="Directa SIM — Nota informativa PDF",
    corpus="directasim",
    marks=[r"DIRECTA SIM", r"Directa"],
    number="de",
    docs=[
        Doc(kind="trade", when=r"^Tipo di Operazione: (?:Acquisto|Vendita)", sell=r"^Tipo di Operazione: Vendita", fields=FIELDS),
    ],
)
