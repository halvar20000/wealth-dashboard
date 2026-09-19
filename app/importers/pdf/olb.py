"""Oldenburgische Landesbank — the FNZ-made Wertpapierabrechnung,
Ertragsausschüttung and Vorabpauschale, and the Girokonto's Auszug
with its bookings in a two-date column."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}\.\d{2}\.\d{4}"

TRADE_FIELDS = {
    "security": [r"^(?:Kauf|Verkauf|Aussch.ttung|Dividende)(?: -| –|:) (?P<name>.+)$"],
    "shares": [r"^" + ISIN + r" \([A-Z0-9]{6}\) (?P<shares>" + NUM + r") (?P<price>" + NUM + r") (?P<price_currency>[A-Z]{3}) " + NUM + r" [A-Z]{3}$",
               r"^" + ISIN + r" \([A-Z0-9]{6}\) (?P<shares>" + NUM + r")"],
    "date": [r"\bAusf.hrung (?P<date>" + DATE + r")", r"^Zahlbarkeitstag (?P<date>" + DATE + r")", r"^Zahltag (?P<date>" + DATE + r")"],
    "amount": [r"^Ausmachender Betrag:? (?:[-+] )?(?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "ref": [r"^Orderreferenz (?P<ref>\d+)"],
    "fees": [r"^(?:Orderentgelt|Provision|Handelsplatzentgelt|Fremde Spesen|Ausgabeaufschlag)[^\n]*?: (?P<fee>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "taxes": [r"^(?:Kapitalertragsteuer|Solidarit.tszuschlag|Kirchensteuer|Quellensteuer)[^\n]*?:? (?P<tax>" + NUM + r") (?P<currency>[A-Z]{3})$"],
    "fx": [r"^Devisenkurs (?P<fx_pair>[A-Z]{3}/ ?[A-Z]{3}) (?P<fx_rate>" + NUM + r")"],
}
TAX_FIELDS = {
    "security": [r"^" + ISIN + r" \([A-Z0-9]{6}\) (?P<name>.+?) (?P<shares>" + NUM + r")$"],
    "date": [r"werden am (?P<date>" + DATE + r") von Ihrem Konto", r"^Zahltag (?P<date>" + DATE + r")"],
    "amount": [r"^Summe Steuern (?P<amount>" + NUM + r") (?P<currency>[A-Z]{3})$"],
}

ROW = r"^\d{2}\.\d{2}\.(?:\d{2})? \d{2}\.\d{2}\. \S.* -?[\d.]+,\d{2}\+?$"
ROW_FIELDS = {
    "date": [r"^(?P<date>\d{2}\.\d{2}\.(?:\d{2})?) "],
    "year": [r"^Auszug +Euro-Konto[^\n]* \d{2}\.\d{2}\.(?P<year>\d{2}) "],
    "amount": [r"^\d{2}\.\d{2}\.(?:\d{2})? \d{2}\.\d{2}\. (?P<type>.+?) (?P<amount>-?[\d.]+,\d{2})\+?$"],
    "type": [r"^\d{2}\.\d{2}\.(?:\d{2})? \d{2}\.\d{2}\. (?P<type>.+?) -?[\d.]+,\d{2}\+?$"],
}


def sign(text: str) -> str:
    """"10,00-" is a debit: put the minus where the engine reads it."""
    import re
    return re.sub(r"(\d,\d{2})-$", r"-\1", text, flags=re.M)


SPEC = Spec(
    slug="olb_pdf",
    label="OLB — Wertpapierabrechnung PDF",
    corpus="oldenburgischelandesbankag",
    marks=[r"Oldenburgische Landesbank", r"olb\.de", r"OLBODEH2"],
    preprocess=sign,
    docs=[
        Doc(kind="skip", when=r"^STORNO\b|^Storno\b", note="A Storno (cancellation) — not imported."),
        Doc(kind="trade", when=r"^WERTPAPIERABRECHNUNG", sell=r"^Verkauf(?: -| –|:)", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^(?:ERTRAGSAUSSCH.TTUNG|DIVIDENDENGUTSCHRIFT|ERTR.GNISGUTSCHRIFT)", fields=TRADE_FIELDS),
        Doc(kind="tax", when=r"^VORABPAUSCHALE", fields=TAX_FIELDS),
        Doc(kind="rows", when=r"^Auszug +Euro-Konto", block=ROW, fields=ROW_FIELDS,
            kinds={r"WERTPAPIERE": "skip", r"ZINSEN|Zinsen": "interest", r"ENTGELT|GEB.HR|Entgelt": "fee", r"STEUER": "tax"}),
    ],
)
