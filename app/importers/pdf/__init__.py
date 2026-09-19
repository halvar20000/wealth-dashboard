"""The statement readers written as specs — one file per bank.

Each module defines `SPEC`, a `statement.Spec`; `READERS` below turns
them into importers. To add a bank: copy the closest spec, point it at
the bank's own words, and score it with `tools/statement_scoreboard.py`
until the corpus reads. Order matters only where two banks share
wording — the first mark that fits wins on the import page.
"""

from __future__ import annotations

from importlib import import_module

from ..statement import Reader

BANKS = ["traderepublic", "degiro", "dekabank", "wirbank", "ebase", "swissquote", "quirin", "saxobank", "hbl", "findependent", "olb", "ffb", "tradegate", "bondora", "boursobank", "renaultbank", "akfbank", "lgt", "llb", "neon", "tigerbrokers", "questrade", "unicredit", "sunrise", "bankslm", "dreibanken", "n26", "c24", "estateguru", "boursedirect", "bbva", "vanguard", "sydbank", "selfwealth", "schelhammer", "pictet", "creditsuisse", "barclays", "bison", "apobank", "solaris", "revolut", "fidelity", "kantonalbank", "comdirect", "ingdiba", "consorsbank", "baaderbank", "scalablecapital", "flatex", "dwpbank", "dab", "deutschebank", "targobank", "commerzbank", "bawag", "erstebank", "postfinance", "zkb", "ubs", "keytrade", "kbc", "arkea"]


def _specs(name: str) -> list:
    module = import_module(f".{name}", __name__)
    return list(getattr(module, "SPECS", [])) or [module.SPEC]


READERS = [Reader(spec) for name in BANKS for spec in _specs(name)]
