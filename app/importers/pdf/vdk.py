"""vdk bank (Belgium) — the transaction overview of a purchase, a sale
or a dividend, in Dutch."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}/\d{2}/\d{4}"

TRADE_FIELDS = {
    "security": [r"^ISIN: " + ISIN + r"\nJe (?:aankoop|verkoop) van: (?P<name>.+)"],
    "shares": [r"^Aantal delen: (?P<shares>" + NUM + r")", r"^Nominaal bedrag: (?P<shares>" + NUM + r") (?P<notation>[A-Z]{3})"],
    "price": [r"^Koers: (?P<price>" + NUM + r") (?:(?P<price_currency>[A-Z]{3})|%)"],
    "date": [r"^Uitvoering op: (?P<date>" + DATE + r")"],
    "amount": [r"^Netto afrekening op \S+ \S+ \S+ \S+ door \w+ van: (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})"],
    "ref": [r"Orderreferentie: (?P<ref>\d+)"],
    "fees": [r"^(?:Makelaarsloon|Vaste kosten|Kosten)[^\n]*?: (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Beurstaks|Roerende voorheffing|Belgische roerende voorheffing|Buitenlandse bronheffing)[^\n]*?: (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "fx": [r"^Wisselkoers (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
DIVIDEND_FIELDS = {
    "security": [r"^Uitbetaling dividend in contanten van " + ISIN + r"\n(?:.*\n){0,3}?Naam: (?P<name>.+)"],
    "shares": [r"^Positie op ex-datum: (?P<shares>" + NUM + r")"],
    "date": [r"^Betaaldatum: (?P<date>" + DATE + r")"],
    "amount": [r"^Netto afrekening op \S+ \S+ \S+ \S+ door \w+ van: (?P<amount>-?" + NUM + r") (?P<currency>[A-Z]{3})"],
    "taxes": [r"^(?:Belgische roerende voorheffing|Roerende voorheffing|Buitenlandse bronheffing)[^\n]*?: (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "fx": [r"^Wisselkoers (?P<fx_pair>[A-Z]{3}/[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}

SPEC = Spec(
    slug="vdk_pdf",
    label="vdk bank — Overzicht transactie PDF",
    corpus="vdkbanknv",
    marks=[r"vdk bank", r"vdk\.be", r"VDSPBE91"],
    number="de",
    # "Wisselkoers USD/EUR 1,146626" is dollars per euro: the pair the engine's way round.
    preprocess=lambda t: __import__("re").sub(r"Wisselkoers ([A-Z]{3})/([A-Z]{3}) ", r"Wisselkoers \2/\1 ", t),
    docs=[
        Doc(kind="trade", when=r"^Je (?:aankoop|verkoop) van:", sell=r"^Je verkoop van:", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^Uitbetaling dividend", fields=DIVIDEND_FIELDS),
    ],
)
