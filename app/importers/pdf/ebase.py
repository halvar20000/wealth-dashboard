"""ebase (European Bank for Financial Services) — the Umsatzabrechnung:
one section per booking, each opened by a line that says what it is,
how much, and on which day — "Kauf 300,00 EUR mit Kursdatum 20.11.2019
in Depotposition …" — with the ISIN, units and price on the data line
below the column headings. A reinvested distribution is income and a
purchase; a Vorabpauschale is a tax and the sale that paid it; a fee
charged by selling units is a fee and that sale."""

from __future__ import annotations

import re

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

HEAD = (r"^(?:Kauf|Verkauf(?: wegen Vorabpauschale)?|Ansparplan|Entnahmeplan|Wiederanlage Fondsertrag \d[\d.,]*|Entgeltbelastung Verkauf|Entgelt Verkauf"
        r"|Vorabpauschale zum Stichtag|(?:Eingang|Ausgang) externer .bertrag|Fondsumschichtung \((?:Abgang|Zugang)\)|Fondsertrag \((?:Aussch.ttung|Thesaurierung)\)) ")
PAYOUT_FIELDS = {
    "security": [r"^" + ISIN + r" (?P<shares>" + NUM + r") " + NUM + r" [A-Z]{3} " + NUM + r" [A-Z]{3}$"],
    "date": [r"Buchungsdatum (?P<date>" + DATE + r")"],
    "amount": [r"^Zahlungsbetrag nach W.hrungskonvertierung mit Devisenkurs " + NUM + r" (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^Zahlungsbetrag in Fremdw.hrung (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^Zahlungsbetrag (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^Abwicklung .ber IBAN[^\n]*\n[^\n]*? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    # Kapitalertragsteuer, Solidaritätszuschlag, Kirchensteuer on one line, each in euros.
    "taxes": [r"^(?P<tax>" + NUM + r") (?P<currency>EUR) " + NUM + r" EUR " + NUM + r" EUR",
              r"^" + NUM + r" EUR (?P<tax>" + NUM + r") (?P<currency>EUR) " + NUM + r" EUR",
              r"^" + NUM + r" EUR " + NUM + r" EUR (?P<tax>" + NUM + r") (?P<currency>EUR)"],
    "type": [r"^(?P<type>Fondsertrag)"],
}
# The cash account: booking day, voucher, value day, text, amount.
CASH_ROW = r"^" + DATE + r" \d+ " + DATE + r" .+ -?" + NUM + r" [A-Z]{3}$"
CASH_FIELDS = {
    "date": [r"^(?P<date>" + DATE + r") \d+ "],
    "amount": [r"^" + DATE + r" \d+ " + DATE + r" (?P<type>.+?) (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "type": [r"^" + DATE + r" \d+ " + DATE + r" (?P<type>.+?) -?" + NUM + r" [A-Z]{3}$"],
}
# The 2016 table: rows under "position name (ISIN X)", written out with the ISIN.
TABLE_ROW = r"^EBROW "
TABLE_FIELDS = {
    "security": [r"^EBROW " + ISIN + r" \| (?P<name>.*?) \| "],
    "type": [r"^EBROW \S+ \| .*? \| (?P<type>.+?) \S+/\d+ "],
    "ref": [r"^EBROW \S+ \| .*? \| .+? (?P<ref>\S+/\d+) "],
    "date": [r" (?P<date>" + DATE + r") " + NUM + r" -?" + NUM + r" " + NUM + r" [A-Z]{3}$"],
    "price": [r" " + DATE + r" (?P<price>" + NUM + r") -?" + NUM + r" " + NUM + r" [A-Z]{3}$"],
    "shares": [r" " + DATE + r" " + NUM + r" (?P<shares>-?" + NUM + r") " + NUM + r" [A-Z]{3}$"],
    "amount": [r" (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}


def table(text: str) -> str:
    if "Umsatzart Buchungs-Nr. Datum" not in text:
        return text
    out, isin, name = [], None, None
    for line in text.split("\n"):
        m = re.match(r"^\S+\.\d+ (?P<name>.+?) \(ISIN (?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)\)", line)
        if m:
            isin, name = m.group("isin"), m.group("name")
        elif isin and re.match(r"^\S.+ \S+/\d+ " + DATE + r" " + NUM + r" -?" + NUM + r" " + NUM + r" [A-Z]{3}$", line):
            line = f"EBROW {isin} | {name} | {line}"
        out.append(line)
    return "\n".join(out)

FIELDS = {
    "security": [r"^" + ISIN + r" (?P<shares>-?" + NUM + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3})(?: (?P<fx_rate>" + NUM + r"))? " + NUM + r" [A-Z]{3}$",
                 r"^" + ISIN + r" (?P<shares>-?" + NUM + r")$", r"^" + ISIN + r"\b"],
    "type": [r"^(?P<type>[^\n]+)"],
    "date": [r"Buchungsdatum (?P<date>" + DATE + r")", r"mit Kursdatum (?P<date>" + DATE + r")"],
    "amount": [r"^Zahlungsbetrag(?: Verkauf| aus .berweisung)? (?P<amount>(?!0,00 )" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^Abwicklung .ber IBAN[^\n]*\n[^\n]*? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^[A-Z]{2}[A-Z0-9]{9}\d -?" + NUM + r" " + NUM + r" [A-Z]{3}(?: " + NUM + r")? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
               r"^Gegenwert der Anteile: (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"Ref\. Nr\. (?P<ref>\S+),"],
    "fees": [r"^(?:ETF-Transaktionsentgelt|Transaktionsentgelt|Depotf.hrungsentgelt[^\n]*|Entgelt[^\n]*?|Provision[^\n]*?|Vertriebsprovision) (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})"],
    "taxes": [r"^(?P<tax>" + NUM + r") EUR " + NUM + r" EUR " + NUM + r" EUR (?P<currency>EUR)$"],
    "fx": [r"^[A-Z]{2}[A-Z0-9]{9}\d -?" + NUM + r" " + NUM + r" (?P<fx_pair>[A-Z]{3}) (?P<fx_rate>" + NUM + r") " + NUM + r" EUR$"],
}

SPEC = Spec(
    slug="ebase_pdf",
    label="ebase — Umsatzabrechnung PDF",
    corpus="ebase",
    marks=[r"European Bank for Financial Services", r"ebase", r"FNZ Bank"],
    preprocess=lambda t: table(t.replace("Depotführungsentgelt inkl. 19 %\nUSt ", "Depotführungsentgelt inkl. 19 % USt ")),
    docs=[
        Doc(kind="rows", when=r"^Kontoauszug", block=CASH_ROW, fields=CASH_FIELDS,
            kinds={r"Entgelt": "fee", r"Zins": "interest", r"Wertpapier": "skip", r"Lastschrift Einzug": "withdrawal"}),
        Doc(kind="rows", when=r"^Umsatzart Buchungs-Nr\. Datum", block=TABLE_ROW, fields=TABLE_FIELDS,
            kinds={r"Verkauf|Entnahme": "sell", r"Kauf|Wiederanlage|Sparplan": "buy"}),
        Doc(kind="rows", when=r"^Umsatzart Buchungs-Nr\. Datum", block=TABLE_ROW + r"\S+ \| .*? \| Wiederanlage", fields=TABLE_FIELDS,
            kinds={r".": "dividend"}, also=True),
        Doc(kind="rows", when=r"^(?:Umsatzabrechnung|Depotauszug)", block=HEAD, fields=FIELDS,
            kinds={r"^Fondsertrag|^Vorabpauschale": "skip", r"externer": "transfer",
                   r"^(?:Verkauf|Entgeltbelastung|Entgelt Verkauf|Entnahmeplan|Fondsumschichtung \(Abgang)": "sell", r".": "buy"}),
        Doc(kind="rows", when=r"^(?:Umsatzabrechnung|Depotauszug)", block=r"^Fondsertrag \((?:Aussch.ttung|Thesaurierung)\)", also=True, kinds={r".": "dividend"},
            fields=PAYOUT_FIELDS),
        Doc(kind="rows", when=r"^(?:Umsatzabrechnung|Depotauszug)", block=r"^Wiederanlage Fondsertrag \d[\d.,]* ", also=True, kinds={r".": "dividend"},
            fields={**FIELDS, "type": [r"^(?P<type>Wiederanlage)"],
                    "amount": [r"^Wiederanlage Fondsertrag (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3}) mit"]}),
        Doc(kind="rows", when=r"^(?:Umsatzabrechnung|Depotauszug)", block=r"^Vorabpauschale zum Stichtag", also=True, kinds={r".": "tax"},
            fields={**FIELDS, "type": [r"^(?P<type>Vorabpauschale)"],
                    "amount": [r"Belastung der angefallenen Steuern in H.he von (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})"]}),
        Doc(kind="rows", when=r"^(?:Umsatzabrechnung|Depotauszug)", block=r"^(?:Entgeltbelastung Verkauf|Entgelt Verkauf)", also=True, kinds={r".": "fee"},
            fields={**FIELDS, "type": [r"^(?P<type>Entgelt)"], "fees": [],
                    "amount": [r"^Summe (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$",
                               r"^Depotf.hrungsentgelt[^\n]*? (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"]}),
    ],
)
