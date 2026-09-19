"""comdirect — Wertpapierabrechnung, Dividendengutschrift, Finanzreport.

Two quirks decide the shape of this spec. The bank prints its tax
pages, and the security line of every dividend, in letter-spaced type
(`S T K   2 4 ,3 3 4   U ni l e ve r`) — an anti-copy font that
survives extraction as scattered characters. `tighten` squeezes such
lines back together before any anchor is tried, so the same regexes
read both the clean lines and the scattered ones; the price is that a
name from a scattered line has its spaces gone ("UnileverPLC").
"""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"


def tighten(text: str) -> str:
    out = []
    for line in text.splitlines():
        tokens = line.split(" ")
        singles = sum(1 for t in tokens if len(t) == 1)
        if len(tokens) >= 8 and singles / len(tokens) >= 0.45:
            line = line.replace(" ", "")
        out.append(line)
    return "\n".join(out)


TRADE_FIELDS = {
    "security": [
        r"Wertpapier-Bezeichnung WPKNR/ISIN\n(?P<name>.+?) (?P<wkn>[A-Z0-9]{6})\n(?P<name2>.+?) " + ISIN + r"\b",
        r"Wertpapier-Bezeichnung WPKNR/ISIN\n(?P<name>.+?) (?P<wkn>[A-Z0-9]{6})\n" + ISIN + r"\b",
    ],
    "shares": [
        # Several fills add up to a "Summe" line; that is the quantity.
        r"^Summe (?P<notation>St\.|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")",
        r"^(?P<notation>St\.|[A-Z]{3}) (?P<shares>" + NUM + r") (?P<price_currency>[A-Z]{3}|%) (?P<price>" + NUM + r")",
        r"^(?P<notation>St\.|[A-Z]{3}) (?P<shares>" + NUM + r")\b",
    ],
    "date": [r"^Gesch.ftstag : (?P<date>\d{2}\.\d{2}\.\d{4})",
             r"ABRECHNUNG VOM (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [
        r"Zu Ihren (?:Lasten|Gunsten)[^\n]*\n[^\n]*?\d{2}\.\d{2}\.\d{4} (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
        r"Zu Ihren (?:Lasten|Gunsten)[^\n]*\n[^\n]*?(?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")\s*$",
    ],
    "ref": [r"^Gesch.ftsnummer : (?P<ref>[\d ]+)$"],
    "fees": [
        r"^(?:Provision|Gesamtprovision|B.rsenplatzabh.ng\. Entgelt|Abwickl\.entgelt Clearstream|"
        r"Umschreibeentgelt|Fremde Spesen|Maklercourtage|Variable B.rsenspesen|Grundgeb.hr|"
        r"Fremdspesen|Ausgabeaufschlag|Transaktionsentgelt|Entgelt f.r .+?)(?: \S+)* : (?P<currency>[A-Z]{3}) (?P<fee>" + NUM + r")(?P<sign>-?)$",
    ],
    "taxes": [
        r"^Kapitalertragsteuer(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
        r"^Solidarit.tszuschlag(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
        r"^Kirchensteuer(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
    ],
}

DIVIDEND_FIELDS = {
    "security": [
        r"^per \d{2}\.\d{2}\.\d{4} (?P<name>.+?) (?P<wkn>[A-Z0-9]{6})\n(?:STK|St\.) (?P<shares>" + NUM + r") (?P<name2>.+?) " + ISIN + r"\b",
        r"^per\d{2}\.\d{2}\.\d{4}(?P<name>.+?)(?P<wkn>[A-Z0-9]{6})\n(?:STK|St\.)(?P<shares>" + NUM + r")(?P<name2>.*?)" + ISIN + r"\b",
        r"Wertpapier-Bezeichnung WKN/ISIN\n(?P<name>.+?) (?P<wkn>[A-Z0-9]{6})\n(?P<name2>.+?) " + ISIN + r"\b",
    ],
    "date": [
        r"Zu Ihren Gunsten[^\n]*\n[^\n]*? (?P<date>\d{2}\.\d{2}\.\d{4}) [A-Z]{3} " + NUM,
        r"^zahlbar ab (?P<date>\d{2}\.\d{2}\.\d{4})",
        r"^Valuta (?P<date>\d{2}\.\d{2}\.\d{4})",
    ],
    "amount": [
        r"Zu Ihren Gunsten[^\n]*\n[^\n]*?\d{2}\.\d{2}\.\d{4} (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
        r"^Ausmachender Betrag (?P<currency>[A-Z]{3}) (?P<amount>" + NUM + r")",
    ],
    "ref": [r"Referenz-Nr\. ?(?P<ref>[A-Z0-9]+)"],
    "fx": [r"zum Devisenkurs:? (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
    "taxes": [
        r"^[\d,]+ % Quellensteuer (?P<currency>[A-Z]{3}) (?P<tax>" + NUM + r") ?(?P<sign>-?)$",
        r"^Kapitalertragsteuer(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
        r"^Solidarit.tszuschlag(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
        r"^Kirchensteuer(?::)? ?(?P<currency>[A-Z]{3}) ?(?P<tax>" + NUM + r") ?(?P<sign>-?)$",
    ],
}

TAX_PAGE = {
    "security": [r"^Stk\. (?P<shares>" + NUM + r") (?P<name>.+?) ?, WKN / ISIN: (?P<wkn>[A-Z0-9]{6}) / " + ISIN],
    "date": [r"Valuta (?P<date>\d{2}\.\d{2}\.\d{4})", r"^Steuerliche Behandlung: .* vom (?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^ZuIhren(?:Gunsten|Lasten)nachSteuern:(?P<currency>[A-Z]{3})(?P<amount>-?" + NUM + r")"],
    "gross": [r"^ZuIhren(?:Gunsten|Lasten)vorSteuern:(?P<currency>[A-Z]{3})(?P<gross>-?" + NUM + r")"],
    "ref": [r"Referenz-Nummer:(?P<ref>[A-Z0-9]+)"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidaritätszuschlag|Kirchensteuer)(?:\(\d\))?(?P<currency>[A-Z]{3})(?P<sign>[-+]?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="comdirect_pdf",
    label="comdirect — Abrechnung PDF",
    corpus="comdirect",
    marks=[r"comdirect bank AG", r"comdirect", r"25449 Quickborn"],
    number="de",
    preprocess=tighten,
    docs=[
        Doc(kind="skip", when=r"^Storno", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^(?:\* )?Wertpapierkauf\b", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^(?:\* )?Wertpapierverkauf\b", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividendengutschrift|Ertragsgutschrift|Ertr.gnisgutschrift|Zinsgutschrift)\b",
            fields=DIVIDEND_FIELDS),
        # The Steuermitteilung — on its own paper, or printed under the
        # statement it settles. Letter-spaced in the original; `tighten`
        # has squeezed it, hence the anchors without spaces.
        Doc(kind="tax", when=r"^Steuerliche Behandlung:", also=True, merge=True, fields=TAX_PAGE),
        # On its own, the page books the tax itself: the sum of its lines.
        Doc(kind="tax", when=r"^Steuerliche Behandlung:", fields=TAX_PAGE),
    ],
)
