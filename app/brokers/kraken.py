"""Kraken, through its REST API with a key of your own.

Kraken has no OAuth and needs none: you create an API key under
Settings → API on kraken.com, tick the permissions it may have, and
paste the key and the private key here. Every request is then signed —
the private key never leaves this machine — and the key never expires.

**Give the key only these permissions:**

    Query Funds
    Query Closed Orders & Trades
    Query Ledger Entries

Nothing under Orders, Withdraw, Staking or Transfer. A key that cannot
withdraw or trade cannot lose you a coin even if the machine it lives
on is compromised, and this app only ever reads.

What is read, and what it becomes
---------------------------------
  * **TradesHistory** — every fill. A trade of a pair such as XXBT/ZEUR
    is a buy or a sale of the base asset for the quote currency: the
    quantity is the volume, the price is the fill price, the money is
    the cost plus the fee for a buy and minus it for a sale.
  * **Ledgers** — everything else: a deposit or withdrawal of money, a
    deposit or withdrawal of a coin (units moving with no money — a
    transfer, with the quantity so the holding is right), a staking or
    "earn" reward (income in kind), and fees charged on their own.
  * **Balance** — the cash in the account's currency, recorded as the
    balance reading, and the coin balances, checked against what the
    trades and transfers add up to.

A coin has no ISIN. Its holding is keyed `CRYPTO:BTC`, which the price
feed knows to quote as `BTC-EUR`. Kraken's own asset names are its
history — XXBT is bitcoin, ZEUR is the euro, ETH2.S is staked ether —
and are turned into the plain code before anything is keyed on them.

Signing, for the record: the message is the URI path plus SHA-256 of
(nonce + POST body), the signature is HMAC-SHA-512 of that with the
base64-decoded private key. The nonce is milliseconds and must only go
up per key, so do not share a key with another program.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .. import settings
from ..db import get_conn
from ..importers import ParsedTxn, ParseResult, store
from ..prices import CRYPTO_PREFIX

API_BASE = "https://api.kraken.com"
USER_AGENT = "wealth-dashboard"
TIMEOUT = 30
KEY_FILE = "kraken_key"
SECRET_FILE = "kraken_secret"

# Kraken's codes for the fiat currencies it settles in, and the plain
# codes for its legacy coin names. Anything else is the code as given,
# minus a staking suffix.
_FIAT = {"ZEUR": "EUR", "ZUSD": "USD", "ZGBP": "GBP", "ZCAD": "CAD", "ZJPY": "JPY",
         "ZAUD": "AUD", "CHF": "CHF", "EUR": "EUR", "USD": "USD", "GBP": "GBP",
         "CAD": "CAD", "JPY": "JPY", "AUD": "AUD"}
_LEGACY = {"XXBT": "BTC", "XBT": "BTC", "XETH": "ETH", "XXRP": "XRP", "XLTC": "LTC",
           "XXLM": "XLM", "XXMR": "XMR", "XETC": "ETC", "XZEC": "ZEC", "XXDG": "DOGE",
           "XMLN": "MLN", "XREP": "REP"}
_NAMES = {"BTC": "Bitcoin", "ETH": "Ethereum", "XRP": "XRP", "LTC": "Litecoin",
          "SOL": "Solana", "ADA": "Cardano", "DOT": "Polkadot", "DOGE": "Dogecoin",
          "XLM": "Stellar", "LINK": "Chainlink", "MATIC": "Polygon", "AVAX": "Avalanche"}


class KrakenError(RuntimeError):
    """Kraken's own `error` list, or a transport failure — in a sentence."""


def asset_code(raw: str) -> str:
    """`XXBT` → `BTC`, `ZEUR` → `EUR`, `ETH2.S` → `ETH`, `DOT.S` → `DOT`."""
    code = (raw or "").upper().split(".")[0]
    if code in _FIAT:
        return _FIAT[code]
    if code in _LEGACY:
        return _LEGACY[code]
    if code == "ETH2":
        return "ETH"
    return code


def is_fiat(raw: str) -> bool:
    return asset_code(raw) in set(_FIAT.values())


# ─── Credentials ─────────────────────────────────────────────────────

def credentials_present() -> bool:
    return ((settings.SECRETS_DIR / KEY_FILE).exists()
            and (settings.SECRETS_DIR / SECRET_FILE).exists())


def save_credentials(key: str, secret: str) -> None:
    settings.ensure_dirs()
    key, secret = (key or "").strip(), (secret or "").strip()
    if not key or not secret:
        raise ValueError("Both the API key and the private key are needed.")
    try:
        if len(base64.b64decode(secret, validate=True)) < 32:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("The private key does not look like the one Kraken shows — "
                         "it is a long base64 string, shown once when the key is "
                         "created.") from None
    for name, value in ((KEY_FILE, key), (SECRET_FILE, secret)):
        path = settings.SECRETS_DIR / name
        path.write_text(value)
        try:
            path.chmod(0o600)
        except OSError:
            pass


def forget_credentials() -> None:
    for name in (KEY_FILE, SECRET_FILE):
        try:
            (settings.SECRETS_DIR / name).unlink()
        except FileNotFoundError:
            pass


def _credentials() -> tuple[str, str]:
    try:
        return ((settings.SECRETS_DIR / KEY_FILE).read_text().strip(),
                (settings.SECRETS_DIR / SECRET_FILE).read_text().strip())
    except OSError:
        raise KrakenError("Kraken is not set up — add the API key under Settings.") from None


# ─── The client ──────────────────────────────────────────────────────

class Client:
    def __init__(self, key: str, secret: str, transport=None):
        self.key, self.secret = key, secret
        self.transport = transport or _urllib_transport
        self._last_nonce = 0

    def _nonce(self) -> int:
        n = int(time.time() * 1000)
        if n <= self._last_nonce:
            n = self._last_nonce + 1
        self._last_nonce = n
        return n

    def public(self, method: str, params: dict | None = None) -> dict:
        path = f"/0/public/{method}"
        url = API_BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return self._unwrap(self.transport("GET", url, {"User-Agent": USER_AGENT}, None))

    def private(self, method: str, params: dict | None = None) -> dict:
        path = f"/0/private/{method}"
        data = dict(params or {})
        data["nonce"] = str(self._nonce())
        body = urllib.parse.urlencode(data)
        digest = hashlib.sha256((data["nonce"] + body).encode()).digest()
        signature = hmac.new(base64.b64decode(self.secret),
                             path.encode() + digest, hashlib.sha512).digest()
        headers = {"User-Agent": USER_AGENT, "API-Key": self.key,
                   "API-Sign": base64.b64encode(signature).decode(),
                   "Content-Type": "application/x-www-form-urlencoded"}
        return self._unwrap(self.transport("POST", API_BASE + path, headers, body.encode()))

    @staticmethod
    def _unwrap(raw) -> dict:
        status, payload = raw
        try:
            data = json.loads(payload.decode("utf-8")) if isinstance(payload, bytes) else payload
        except ValueError:
            raise KrakenError(f"Kraken answered with something that is not JSON ({status}).") from None
        errors = data.get("error") or []
        if errors:
            raise KrakenError("Kraken: " + "; ".join(str(e) for e in errors))
        if status >= 400:
            raise KrakenError(f"Kraken refused the request ({status}).")
        return data.get("result") or {}

    # Everything paginated the way Kraken paginates: an offset and a count.
    def _pages(self, method: str, key: str, params: dict | None = None) -> dict:
        out: dict = {}
        ofs = 0
        while True:
            page = self.private(method, {**(params or {}), "ofs": ofs})
            items = page.get(key) or {}
            out.update(items)
            total = int(page.get("count") or 0)
            ofs += len(items)
            if not items or ofs >= total:
                return out

    def asset_pairs(self) -> dict[str, tuple[str, str]]:
        """{pair name and altname: (base, quote)} as plain codes."""
        out = {}
        for name, p in self.public("AssetPairs").items():
            pair = (asset_code(p.get("base", "")), asset_code(p.get("quote", "")))
            out[name] = pair
            if p.get("altname"):
                out[p["altname"]] = pair
        return out

    def balance(self) -> dict[str, float]:
        """{plain code: amount}, staked variants folded into the coin."""
        out: dict[str, float] = {}
        for raw, amount in self.private("Balance").items():
            try:
                out[asset_code(raw)] = out.get(asset_code(raw), 0.0) + float(amount)
            except (TypeError, ValueError):
                continue
        return out

    def trades(self) -> dict[str, dict]:
        return self._pages("TradesHistory", "trades")

    def ledgers(self) -> dict[str, dict]:
        return self._pages("Ledgers", "ledger")


def _urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise KrakenError(f"Could not reach Kraken: {exc}") from exc


def client(transport=None) -> Client:
    key, secret = _credentials()
    return Client(key, secret, transport)


# ─── What the API says → rows ────────────────────────────────────────

def _day(ts) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).date().isoformat()


def _crypto_key(code: str) -> str:
    return f"{CRYPTO_PREFIX}{code}"


def _name(code: str) -> str:
    return _NAMES.get(code, code)


def normalise(trades: dict[str, dict], ledgers: dict[str, dict],
              pairs: dict[str, tuple[str, str]], account_currency: str) -> ParseResult:
    """Kraken's trades and ledger → the rows the account will hold.

    A fill is one row. A ledger entry of type `trade` is that same fill
    seen from one asset's side, so those are skipped; every other type
    is a row of its own, in money or in units depending on the asset.
    """
    result = ParseResult()
    ccy = account_currency.upper()

    for txid, t in sorted(trades.items(), key=lambda kv: float(kv[1].get("time") or 0)):
        base, quote = pairs.get(t.get("pair") or "", (None, None))
        if base is None:
            # A pair the reference list does not know: split the name
            # by the fiat suffix as a last resort.
            raw = (t.get("pair") or "").upper()
            quote = next((f for f in ("ZEUR", "EUR", "ZUSD", "USD", "ZGBP", "GBP", "CHF")
                          if raw.endswith(f)), None)
            if not quote:
                result.problems.append(f"trade {txid}: unknown pair {raw!r}, skipped")
                continue
            base, quote = asset_code(raw[:-len(quote)]), asset_code(quote)
        try:
            vol, cost, fee = float(t["vol"]), float(t["cost"]), float(t.get("fee") or 0)
            price = float(t.get("price") or (cost / vol if vol else 0))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            result.problems.append(f"trade {txid}: unreadable figures, skipped")
            continue
        side = (t.get("type") or "").lower()
        if side not in ("buy", "sell"):
            result.problems.append(f"trade {txid}: type {side!r}, skipped")
            continue
        if quote not in set(_FIAT.values()):
            # Coin for coin. The units of both sides move, no money does:
            # a sale of the quote coin and a purchase of the base coin,
            # each priced in the other, and neither in money the account
            # can add up. Recorded as two transfers so the holdings are
            # right; the cost basis of a coin-for-coin swap is not.
            for code, qty in ((base, vol if side == "buy" else -vol),
                              (quote, -cost if side == "buy" else cost)):
                result.rows.append(ParsedTxn(
                    txn_date=_day(t.get("time")), description=f"{side} {vol:g} {base} for {quote}",
                    amount=0.0, currency=ccy, kind="transfer",
                    external_id=f"kraken:trade:{txid}:{code}",
                    isin=_crypto_key(code), security_name=_name(code), quantity=qty))
            continue
        amount = -(cost + fee) if side == "buy" else (cost - fee)
        result.rows.append(ParsedTxn(
            txn_date=_day(t.get("time")),
            description=f"{'Bought' if side == 'buy' else 'Sold'} {vol:g} {base}",
            amount=round(amount, 2), currency=quote, kind=side,
            external_id=f"kraken:trade:{txid}",
            isin=_crypto_key(base), security_name=_name(base),
            quantity=vol if side == "buy" else -vol, price=price,
            fee=round(fee, 2) or None))

    for lid, e in sorted(ledgers.items(), key=lambda kv: float(kv[1].get("time") or 0)):
        kind = (e.get("type") or "").lower()
        if kind == "trade":
            continue                                   # the fill above
        code = asset_code(e.get("asset") or "")
        try:
            amount, fee = float(e.get("amount") or 0), float(e.get("fee") or 0)
        except (TypeError, ValueError):
            result.problems.append(f"ledger {lid}: unreadable amount, skipped")
            continue
        if abs(amount) < 1e-12 and abs(fee) < 1e-12:
            result.skipped += 1
            continue
        day = _day(e.get("time"))
        if code in set(_FIAT.values()):
            net = amount - fee
            if kind in ("deposit", "withdrawal"):
                row_kind = "deposit" if net > 0 else "withdrawal"
            elif kind in ("staking", "earn", "reward", "dividend"):
                row_kind = "interest"
            elif kind in ("fee", "margin", "rollover", "settled"):
                row_kind = "fee"
            else:
                row_kind = "deposit" if net > 0 else "withdrawal"
            result.rows.append(ParsedTxn(
                txn_date=day, description=f"{kind} {code}".strip(),
                amount=round(net, 2), currency=code, kind=row_kind,
                external_id=f"kraken:ledger:{lid}", fee=round(fee, 2) or None))
            continue
        # A coin: units move, money does not — unless it is a fee taken
        # in the coin, which is units gone for nothing.
        qty = amount - fee
        if kind in ("staking", "earn", "reward", "dividend"):
            row_kind = "interest"
        elif kind in ("deposit", "withdrawal", "transfer", "spend", "receive"):
            row_kind = "transfer"
        else:
            row_kind = "transfer"
        result.rows.append(ParsedTxn(
            txn_date=day, description=f"{kind} {qty:g} {code}",
            amount=0.0, currency=ccy, kind=row_kind,
            external_id=f"kraken:ledger:{lid}",
            isin=_crypto_key(code), security_name=_name(code), quantity=qty))
    return result


def sync_link(link: dict, api: Client | None = None) -> int:
    """Pull everything, store it, record the cash balance. Returns how
    many rows were new."""
    api = api or client()
    pairs = api.asset_pairs()
    parsed = normalise(api.trades(), api.ledgers(), pairs, link["account_currency"])
    balances = api.balance()
    cash = balances.get(link["account_currency"].upper())
    if cash is not None:
        parsed.closing_balance = {"amount": round(cash, 2), "currency": link["account_currency"].upper(),
                                  "as_of": datetime.now(timezone.utc).date().isoformat()}
    # A coin sent to the user's own wallet — an account here, named on
    # the link — is a move between two of their accounts: the units
    # leave Kraken and arrive there, at the cost they carried, so the
    # holding and its cost basis survive the trip. A coin sent back in
    # is the same the other way round. Without a wallet named, the
    # units simply leave, which is what Kraken's balance says.
    wallet = link.get("wallet_account_id")
    to_wallet = []
    if wallet:
        with get_conn() as conn:
            seen = {r["external_id"] for r in conn.execute(
                "SELECT external_id FROM transactions WHERE account_id = ? AND external_id LIKE 'kraken:ledger:%'",
                (link["account_id"],))}
        for r in parsed.rows:
            if r.kind != "transfer" or not r.isin or not r.quantity or not r.description.startswith(("withdrawal", "deposit")):
                continue
            if r.external_id in seen:
                continue                 # booked before the wallet was named; the past is not rewritten
            code = r.isin.split(":")[-1]
            to_wallet.append(ParsedTxn(
                txn_date=r.txn_date,
                description=f"{'From' if r.quantity < 0 else 'To'} Kraken: {abs(r.quantity):g} {code}",
                amount=0.0, currency=r.currency, kind="transfer", external_id=f"{r.external_id}:wallet",
                isin=r.isin, security_name=r.security_name, quantity=-r.quantity,
                price=_carried_cost(link["account_id"], r.isin) if r.quantity < 0 else None))
    report = store(link["account_id"], parsed, "kraken")
    if to_wallet:
        store(int(wallet), ParseResult(rows=to_wallet), "kraken")
    # Kraken's own coin balances against what the rows add up to. A gap
    # is a movement the ledger did not carry — reported, never patched.
    with get_conn() as conn:
        held = {r["isin"]: r["q"] for r in conn.execute(
            "SELECT isin, SUM(quantity) AS q FROM transactions WHERE account_id = ? "
            "AND isin LIKE ? AND quantity IS NOT NULL GROUP BY isin",
            (link["account_id"], f"{CRYPTO_PREFIX}%"))}
    drift = []
    for code, amount in balances.items():
        if code in set(_FIAT.values()) or abs(amount) < 1e-9:
            continue
        have = held.get(_crypto_key(code), 0.0)
        if abs(have - amount) > max(1e-8, abs(amount) * 1e-6):
            drift.append(f"{code}: Kraken says {amount:g}, the rows add up to {have:g}")
    if drift:
        raise KrakenError("Synced, but the holdings do not add up — " + "; ".join(drift)
                          + ". A key without 'Query Ledger Entries' cannot see transfers.")
    return report["inserted"]


def _carried_cost(account_id: int, key: str) -> float | None:
    """What a unit of the coin cost, on average, over the lots still
    open here — the price a transfer to the wallet carries with it."""
    from .. import gains
    r = gains.realised(key, [account_id])
    if r["open_quantity"] > 1e-12:
        return r["open_cost"] / r["open_quantity"]
    return None


def describe() -> dict:
    """For the Settings page."""
    return {"configured": credentials_present()}


def check() -> dict:
    """A live look: the key works, and what the balances are."""
    api = client()
    bal = api.balance()
    return {"ok": True, "assets": {k: v for k, v in bal.items() if abs(v) > 1e-9}}
