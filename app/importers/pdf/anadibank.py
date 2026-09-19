"""Austrian Anadi Bank — the Kontoauszug: booking rows "dd.mm text dd.mm
amount[-]" with the year printed once in the header; a Festgeld
settlement row is split into the capital coming back and its interest."""

from __future__ import annotations

import re

from ..statement import Doc, Spec, parse_number

NUM = r"[\d.]+,\d{2}"
ROW = r"^\d{2}\.\d{2} .+? \d{2}\.\d{2} " + NUM + r"-?$"


def settle(text: str) -> str:
    """'ABRECHNUNG ZU KONTO' pays the Festgeld capital and its net
    interest in one figure: two rows, so the interest keeps its tax."""
    def fix(m):
        row, block = m.group(1), m.group(0)
        capital = re.search(r"VERANLAGUNGSBETRAG\s+(" + NUM + r")", block)
        rm = re.match(r"^(\d{2}\.\d{2}) .+? (\d{2}\.\d{2}) (" + NUM + r")$", row)
        if not capital or not rm:
            return block
        net = parse_number(rm.group(3), "de") - parse_number(capital.group(1), "de")
        kest = re.search(r"^KESt\s+(" + NUM + r")-", block, re.M)
        figure = f"{net:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return (f"{rm.group(1)} VERANLAGUNGSBETRAG {rm.group(2)} {capital.group(1)}\n"
                f"{rm.group(1)} Habenzinsen Festgeld {rm.group(2)} {figure}"
                + (f"\nKESt {kest.group(1)}-" if kest else "") + "\n")
    return re.sub(r"^(\d{2}\.\d{2} ABRECHNUNG ZU KONTO .+? \d{2}\.\d{2} " + NUM + r")\n(?:(?!" + ROW[1:] + r")[^\n]*\n)*",
                  fix, text, flags=re.M)


FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}) "],
    "year": [r"vom \d{2}\.\d{2}\.(?P<year>\d{4})", r"Alter Saldo per \d{2}\.\d{2}\.(?P<year>\d{4})"],
    "type": [r"^\d{2}\.\d{2} (?P<type>.+?) \d{2}\.\d{2} " + NUM + r"-?$"],
    "amount": [r"^\d{2}\.\d{2} .+? \d{2}\.\d{2} (?P<amount>" + NUM + r")(?P<sign>-?)$"],
    "taxes": [r"^KESt\s+(?P<tax>" + NUM + r")-"],
}

SPEC = Spec(
    slug="anadibank_pdf",
    label="Austrian Anadi Bank — Kontoauszug PDF",
    corpus="austriananadibank",
    marks=[r"anadibank\.at", r"Anadi Bank", r"HAABAT2K", r"Klagenfurt a\.W\.,Inglitschstra"],
    number="de",
    preprocess=settle,
    docs=[
        Doc(kind="rows", when=r"^Datum Buchungstext Wert Betrag", block=ROW, fields=FIELDS,
            kinds={r"^Abschluss|Habenzinsen": "interest", r"^VERANLAGUNGSBETRAG": "deposit"}),
    ],
)
