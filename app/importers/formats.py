"""What the bank-statement *formats* share — CAMT.053, MT940, OFX.

These are not one bank's file but a standard every bank writes the same
way, so the three importers next to this module have the same problems
in common: a file that may be Latin-1 or UTF-8, a booking text that
has to be turned into a kind, and an id that must survive two
overlapping exports of the same account. Solved once, here.
"""

from __future__ import annotations

import hashlib

# A statement row's kind from its text, in the languages the banks this
# app targets write in. A word list, not a taxonomy: interest, fees and
# taxes are what a bank books on its own initiative and what the user
# most wants told apart from their own payments; the rest is a payment
# in or out and stays "other", for the user's rules to categorise.
INTEREST_WORDS = ("zins", "interest", "intérêt", "interet", "interes", "rente ", "habenzins")
FEE_WORDS = ("entgelt", "gebühr", "gebuhr", "kontoführung", "kontofuhrung", "kartenpreis",
             "fee", "charge", "commission", "frais", "comisión", "comision", "spesen", "kosten")
TAX_WORDS = ("steuer", "kapitalertrag", "solidaritätszuschlag", "kirchensteuer", "tax ", " tax",
             "withholding", "impôt", "impot", "impuesto", "kest", "verrechnungssteuer")


def decode(content: bytes | str) -> str:
    """UTF-8 when it is, Latin-1 when it is not — strictly, so an umlaut
    never comes through as a replacement character."""
    if isinstance(content, str):
        return content.lstrip("﻿")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def kind_of(text: str, amount: float, hint: str | None = None) -> str:
    """The kind a booking is, from the bank's own code when there is one
    (`hint`: an ISO 20022 sub-family or an MT940/OFX transaction type)
    and from its words otherwise."""
    h = (hint or "").upper()
    if h in ("INTR", "INT"):
        return "interest"
    if h in ("CHRG", "FEES", "COMM", "FEE", "SRVCHG"):
        return "fee"
    if h in ("TAXE", "WTAX", "TAX"):
        return "tax"
    low = f" {text.lower()} "
    if any(w in low for w in TAX_WORDS):
        return "tax"
    if amount > 0 and any(w in low for w in INTEREST_WORDS):
        return "interest"
    if amount < 0 and any(w in low for w in FEE_WORDS):
        return "fee"
    return "other"


def row_id(prefix: str, *parts: object) -> str:
    """A stable id for a row that has none: a hash of what identifies it.
    Two exports of the same period agree on it; two identical bookings
    on one day need a counter from the caller."""
    seed = "|".join("" if p is None else str(p) for p in parts)
    return f"{prefix}:{hashlib.sha1(seed.encode()).hexdigest()[:20]}"
