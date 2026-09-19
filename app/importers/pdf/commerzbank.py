"""Commerzbank — comdirect's paper (the same house), printed entirely in
the letter-spaced anti-copy font. Every line is squeezed to no spaces
at all before reading, and the anchors are written without them:

    Wertpapierkauf
    Geschäftstag:18.04.2017Ausführungsplatz:XETRA
    St.0,572EUR43,64
    DE26100400480680403302EUR20.04.2017EUR24,96

A trade names the security by WKN only; the ISIN is on the dividend
and tax pages.
"""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"


def squeeze(text: str) -> str:
    return "\n".join(line.replace(" ", "") for line in text.splitlines())


TRADE_FIELDS = {
    "security": [r"^Wertpapier-BezeichnungWertpapierkennnummer\n(?P<name>.+?)(?P<wkn>[A-Z0-9]{6})\n(?P<name2>(?!Nennwert)[^\n]+)",
                 r"^Wertpapier-BezeichnungWPKNR/ISIN\n(?P<name>.+?)(?P<wkn>[A-Z0-9]{6})\n(?P<name2>.+?)" + ISIN + r"$"],
    "shares": [r"^(?:Summe)?(?P<notation>St\.|[A-Z]{3})(?P<shares>" + NUM + r")(?P<price_currency>[A-Z]{3}|%)(?P<price>" + NUM + r")$",
               r"^(?P<notation>St\.)(?P<shares>" + NUM + r")$"],
    "date": [r"^Geschäftstag:(?P<date>\d{2}\.\d{2}\.\d{4})", r"^GESCHÄFTSABRECHNUNGVOM(?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"ZuIhren(?:Lasten|Gunsten)vorSteuern\n[^\n]*?\d{2}\.\d{2}\.\d{4}(?P<currency>[A-Z]{3})(?P<amount>" + NUM + r")$",
               r"ZuIhren(?:Lasten|Gunsten)\n[^\n]*?\d{2}\.\d{2}\.\d{4}(?P<currency>[A-Z]{3})(?P<amount>" + NUM + r")$"],
    "ref": [r"^Geschäftsnummer:(?P<ref>\d+)"],
    "fees": [r"^(?:Provision|Gesamtprovision|Börsenplatzabhäng\.Entgelt|Abwickl\.entgeltClearstream|Umschreibeentgelt|FremdeSpesen|"
             r"Maklercourtage|VariableBörsenspesen|Grundgebühr|Fremdspesen|Ausgabeaufschlag|Transaktionsentgelt):(?P<currency>[A-Z]{3})(?P<fee>" + NUM + r")(?P<sign>-?)$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidaritätszuschlag|Kirchensteuer)(?:\(\d\))?:?(?P<currency>[A-Z]{3})(?P<sign>[-+]?)(?P<tax>" + NUM + r")$"],
}
DIVIDEND_FIELDS = {
    "security": [r"^per\d{2}\.\d{2}\.\d{4}(?P<name>.+?)(?P<wkn>[A-Z0-9]{6})\n(?:STK|St\.)(?P<shares>" + NUM + r")(?P<name2>.*?)" + ISIN + r"$"],
    "date": [r"ZuIhrenGunstenvorSteuern\n[^\n]*?[A-Z]{3}(?P<date>\d{2}\.\d{2}\.\d{4})[A-Z]{3}" + NUM + r"$", r"^zahlbarab(?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"ZuIhrenGunstenvorSteuern\n[^\n]*?\d{2}\.\d{2}\.\d{4}(?P<currency>[A-Z]{3})(?P<amount>" + NUM + r")$"],
    "ref": [r"Referenz-Nr\.(?P<ref>[A-Z0-9]+)"],
    "fx": [r"zumDevisenkurs:(?P<fx_pair>[A-Z]{3}/[A-Z]{3})(?P<fx_rate>" + NUM + r")"],
    "taxes": [r"^[\d,]+%Quellensteuer(?P<currency>[A-Z]{3})(?P<tax>" + NUM + r")-?$"],
}
TAX_PAGE = {
    "security": [r"^Stk\.(?P<shares>" + NUM + r")(?P<name>.+?),WKN/ISIN:(?P<wkn>[A-Z0-9]+)/" + ISIN],
    "date": [r"Valuta(?P<date>\d{2}\.\d{2}\.\d{4})", r"^SteuerlicheBehandlung:.*vom(?P<date>\d{2}\.\d{2}\.\d{4})"],
    "amount": [r"^ZuIhren(?:Gunsten|Lasten)nachSteuern:(?P<currency>[A-Z]{3})(?P<amount>-?" + NUM + r")"],
    "gross": [r"^ZuIhren(?:Gunsten|Lasten)vorSteuern:(?P<currency>[A-Z]{3})(?P<gross>-?" + NUM + r")"],
    "ref": [r"Referenz-Nummer:(?P<ref>[A-Z0-9]+)"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidaritätszuschlag|Kirchensteuer)(?:\(\d\))?(?P<currency>[A-Z]{3})(?P<sign>[-+]?)(?P<tax>" + NUM + r")$"],
}

SPEC = Spec(
    slug="commerzbank_pdf",
    label="Commerzbank — Abrechnung PDF",
    corpus="commerzbank",
    marks=[r"COMMERZBANK", r"Commerzbank", r"COBADE"],
    preprocess=squeeze,
    docs=[
        Doc(kind="skip", when=r"^Storno", note="A Storno (cancellation) — not imported."),
        Doc(kind="buy", when=r"^(?:\*)?Wertpapierkauf$", fields=TRADE_FIELDS),
        Doc(kind="sell", when=r"^(?:\*)?Wertpapierverkauf", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:Dividendengutschrift|Ertragsgutschrift|Erträgnisgutschrift|Zinsgutschrift)$", fields=DIVIDEND_FIELDS),
        Doc(kind="tax", when=r"^SteuerlicheBehandlung:", also=True, merge=True, fields=TAX_PAGE),
        Doc(kind="tax", when=r"^SteuerlicheBehandlung:", fields=TAX_PAGE),
    ],
)
