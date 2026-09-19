"""BBVA — the carta de operaciones de valores: a purchase or sale, a
dividend, the custody fees; the security's currency and the euro
counter-value side by side."""

from __future__ import annotations

from ..statement import Doc, Spec

ISIN = r"(?P<isin>[A-Z]{2}[A-Z0-9]{9}\d)"
NUM = r"[\d.,]+"
DATE = r"\d{2}/\d{2}/\d{4}"

TRADE_FIELDS = {
    "security": [r"^Valor (?P<name>.+)\nISIN Valor " + ISIN],
    "shares": [r"^N. de valores (?P<shares>" + NUM + r")"],
    "price": [r"^Precio unitario (?P<price>" + NUM + r")"],
    "date": [r"^Fecha ejecuci.n (?P<date>" + DATE + r")"],
    "amount": [r"^IMPORTE TOTAL (?P<currency>[A-Z]{3}) +(?P<amount>" + NUM + r")$"],
    "ref": [r"^N. de orden (?P<ref>\d+)"],
    "fees": [r"^IMPORTE TOTAL GASTOS (?P<currency>[A-Z]{3}) +(?P<fee>" + NUM + r")$"],
}
DIVIDEND_FIELDS = {
    "security": [r"^CODIGO CUENTA VALOR VALOR \(" + ISIN + r"\)[^\n]*\n\S+ \S+ \S+ \S+ (?P<name>.+?) (?P<date>" + DATE + r")"],
    "shares": [r"^NUMERO DE VALORES[^\n]*\n(?P<shares>" + NUM + r") "],
    "amount": [r"^IMPORTE TOTAL (?P<currency>[A-Z]{3}) +(?P<amount>" + NUM + r")$"],
    "gross": [r"^CONTRAVALOR EUR IMPORTE EFECTIVO EUR " + NUM + r" " + NUM + r" (?P<gross>" + NUM + r")$", r"^IMPORTE EFECTIVO (?P<currency>EUR) \S+ \S+ (?P<gross>" + NUM + r")$"],
    "fees": [r"^IMPORTE TOTAL GASTOS (?P<currency>[A-Z]{3}) +(?P<fee>" + NUM + r")$"],
}
FEE_FIELDS = {
    "date": [r"(?P<date>" + DATE + r")"],
    "amount": [r"^IMPORTE TOTAL +(?P<amount>" + NUM + r")$"],
}

SPEC = Spec(
    slug="bbva_pdf",
    label="BBVA — carta de operaciones PDF",
    corpus="bancobilbaovizcayaargentaria",
    marks=[r"BANCO BILBAO VIZCAYA ARGENTARIA", r"BBVA", r"CARTA DE (?:ABONO|CARGO) POR OPERACIONES VALORES", r"OPERACI.N (?:COMPRA|VENTA) DE VALORES"],
    docs=[
        Doc(kind="trade", when=r"operaci.n (?:COMPRA|VENTA) DE VALORES", sell=r"operaci.n VENTA DE VALORES", fields=TRADE_FIELDS),
        Doc(kind="dividend", when=r"^ABONO DE DIVIDENDOS", fields=DIVIDEND_FIELDS),
        # A fund subscription or redemption.
        Doc(kind="trade", when=r"OPERACIONES DE FONDOS (?:SUSCRIPCI.N|REEMBOLSO)", sell=r"REEMBOLSO", fields={
            "security": [r"^\S+ \S+ \S+ \S+ (?P<name>.+?) (?P<shares>" + NUM + r") [A-Z]{3}/[A-Z]{3}$", r"NOMBRE DEL FONDO " + ISIN],
            "date": [r"^FECHA EJECUCI.N\n(?P<date>\d{2}-\d{2}-\d{4})"],
            "price": [r"^(?:SUSCRIPCI.N|REEMBOLSO) EFECTIVO [A-Z]{3} (?P<price>" + NUM + r") "],
            "amount": [r"^IMPORTE TOTAL (?P<currency>[A-Z]{3}) +(?P<amount>" + NUM + r")$"],
        }),
        # The half-year custody fee: one line per holding.
        Doc(kind="rows", when=r"^ADMINISTRACION DE DEPOSITOS", block=r"^\S.* [TN] " + NUM + r" [A-Z]{3} " + NUM + r" " + NUM + r" \S+ " + NUM + r"$", fields={
            "date": [r"PER.ODO LIQUIDACI.N: \d{2}/\d{2}/\d{2} - (?P<date>\d{2}/\d{2}/\d{2})"],
            "type": [r"^(?P<type>\S.*?) [TN] "],
            "amount": [r"^\S.* [TN] " + NUM + r" [A-Z]{3} " + NUM + r" " + NUM + r" \S+ (?P<amount>" + NUM + r")$"],
        }, kinds={r".": "fee"}),
    ],
)
