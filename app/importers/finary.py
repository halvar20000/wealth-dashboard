"""Finary — the crypto transaction export.

Finary is an aggregator: this file lists what happened on the
exchanges and wallets connected to it — Kraken, Coinbase, a hardware
wallet — in one shape. Export it under Crypto → Transactions.

One row per event, with what was received and what was sent, each with
its currency, so a buy, a sale and a swap are the same columns filled
differently: a buy receives a coin and sends fiat, a sale the other way
round, a swap sends one coin and receives another. `eur_value` is
what the event was worth in euros, fees included; `external_id` is
Finary's own UUID, which is what a row is recognised by.

How each becomes rows here:

* **Buy** — a buy of the coin received, `CRYPTO:<code>`, at the fiat
  sent per unit; the amount is the euro value, which is what left the
  pocket. **Sell** the mirror image.
* **Swap** — a sale of the coin sent and a buy of the one received,
  both at the euro value, under `<uuid>:sell` and `<uuid>:buy`. A
  swap is a disposal for tax and the cost basis of what was received;
  booking it as one row would lose both.
* **Withdrawal / Deposit of a coin** — units moving between the user's
  own places: from the exchange to a hardware wallet, say. Not a sale,
  not a purchase: the units are still theirs. Skipped, and counted
  as such. Fiat in and out are deposits and withdrawals.
* A **fee in a coin** (a swap's) is units, not money; it is left off
  the row rather than written as if it were euros.
"""

from __future__ import annotations

import csv
import io

from .base import ParsedTxn, ParseResult, normalise_csv_text, parse_date, parse_decimal

SLUG = "finary"
LABEL = "Finary — crypto transaction export"

REQUIRED_COLUMNS = {"type", "date", "received_amount", "received_currency", "sent_amount",
                    "sent_currency", "fee_amount", "fee_currency", "external_id"}

FIAT = {"EUR", "USD", "CHF", "GBP", "AUD", "CAD", "JPY", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF"}

NAMES = {"BTC": "Bitcoin", "ETH": "Ethereum", "XRP": "XRP", "SOL": "Solana", "ADA": "Cardano",
         "DOT": "Polkadot", "LTC": "Litecoin", "DOGE": "Dogecoin", "BNB": "BNB", "USDT": "Tether",
         "USDC": "USD Coin", "LINK": "Chainlink", "AVAX": "Avalanche", "MATIC": "Polygon"}


def matches(header: list[str], sample: str) -> bool:
    return REQUIRED_COLUMNS.issubset({h.strip().lower() for h in header})


def _coin(code: str) -> tuple[str, str]:
    code = code.upper()
    return f"CRYPTO:{code}", NAMES.get(code, code)


def parse(content: bytes | str, account_currency: str = "EUR") -> ParseResult:
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    text = normalise_csv_text(text)
    reader = csv.DictReader(io.StringIO(text))
    result = ParseResult()
    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset({f.strip().lower() for f in reader.fieldnames}):
        result.problems.append("This is not a Finary export — expected columns include "
                               + ", ".join(sorted(REQUIRED_COLUMNS)))
        return result

    for line_no, row in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        date = parse_date(row.get("date", "")[:10])
        if not date:
            result.problems.append(f"line {line_no}: unreadable date")
            continue
        uid = row.get("external_id") or None
        recv, recv_ccy = parse_decimal(row.get("received_amount")), row.get("received_currency", "").upper()
        sent, sent_ccy = parse_decimal(row.get("sent_amount")), row.get("sent_currency", "").upper()
        fee, fee_ccy = parse_decimal(row.get("fee_amount")), row.get("fee_currency", "").upper()
        value = parse_decimal(row.get("eur_value"))
        fee_money = abs(fee) if fee and fee_ccy in FIAT else None
        text_ = row.get("description") or row.get("type") or ""
        recv_fiat, sent_fiat = recv_ccy in FIAT, sent_ccy in FIAT

        if recv and sent and not recv_fiat and not sent_fiat:
            # A swap: one coin out, another in, both at the euro value.
            key_out, name_out = _coin(sent_ccy)
            key_in, name_in = _coin(recv_ccy)
            worth = value if value is not None else 0.0
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"Swap {sent_ccy} -> {recv_ccy}", amount=worth,
                currency=account_currency, kind="sell", external_id=f"{uid}:sell" if uid else None,
                isin=key_out, security_name=name_out, quantity=-abs(sent),
                price=(worth / abs(sent)) if sent else None))
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"Swap {sent_ccy} -> {recv_ccy}", amount=-worth,
                currency=account_currency, kind="buy", external_id=f"{uid}:buy" if uid else None,
                isin=key_in, security_name=name_in, quantity=abs(recv),
                price=(worth / abs(recv)) if recv else None))
            continue
        if recv and not recv_fiat and (sent_fiat or not sent):
            if not sent:
                # A coin arriving from the user's own wallet: still theirs
                # before, still theirs now. Not a purchase.
                result.skipped += 1
                continue
            key, name = _coin(recv_ccy)
            worth = value if value is not None else abs(sent) + (fee_money or 0.0)
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"Buy {recv_ccy} via Finary", amount=-worth,
                currency=sent_ccy or account_currency, kind="buy", external_id=uid,
                isin=key, security_name=name, quantity=abs(recv), price=abs(sent) / abs(recv),
                fee=fee_money))
            continue
        if sent and not sent_fiat and (recv_fiat or not recv):
            if not recv:
                # Sent to the user's own wallet — a hardware wallet, say.
                result.skipped += 1
                continue
            key, name = _coin(sent_ccy)
            worth = value if value is not None else abs(recv) - (fee_money or 0.0)
            result.rows.append(ParsedTxn(
                txn_date=date, description=f"Sell {sent_ccy} via Finary", amount=worth,
                currency=recv_ccy or account_currency, kind="sell", external_id=uid,
                isin=key, security_name=name, quantity=-abs(sent), price=abs(recv) / abs(sent),
                fee=fee_money))
            continue
        if recv and recv_fiat and not sent:
            result.rows.append(ParsedTxn(txn_date=date, description=text_ or "Deposit", amount=abs(recv),
                                         currency=recv_ccy, kind="deposit", external_id=uid))
            continue
        if sent and sent_fiat and not recv:
            result.rows.append(ParsedTxn(txn_date=date, description=text_ or "Withdrawal", amount=-abs(sent),
                                         currency=sent_ccy, kind="withdrawal", external_id=uid, fee=fee_money))
            continue
        result.skipped += 1
    return result
