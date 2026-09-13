"""Webhooks: a POST to a URL of yours when something happened.

Home Assistant, n8n, a Telegram bot, a script — anything that can
take a JSON POST. Events:

    sync.completed   a bank or broker sync ran: rows imported, balance
    sync.failed      a sync raised — the consent lapsed, the bank refused
    bill.missed      a bill is past due with nothing seen (checked daily)

The payload is {event, at, data}; the header `X-Wealth-Event` names
the event and `X-Wealth-Signature` is an HMAC-SHA256 of the body with
the hook's secret, so the receiver can tell this app from anyone who
found the URL. Delivery is one attempt, in a thread, five seconds'
patience: a webhook that is down loses that event, and the
Assistants chapter under Settings says when it last failed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .db import get_conn

EVENTS = ("sync.completed", "sync.failed", "bill.missed")
TIMEOUT = 5


def all_hooks() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM webhooks ORDER BY id")]


def add(url: str, events: list[str] | None = None) -> int:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("A webhook needs an http:// or https:// URL.")
    chosen = [e for e in (events or EVENTS) if e in EVENTS] or list(EVENTS)
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO webhooks (url, events, secret) VALUES (?, ?, ?)",
                           (url, ",".join(chosen), secrets.token_urlsafe(24)))
        return int(cur.lastrowid)


def delete(hook_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM webhooks WHERE id = ?", (hook_id,))


def _post(hook: dict, event: str, body: bytes) -> None:
    sig = hmac.new(hook["secret"].encode(), body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(hook["url"], data=body, method="POST", headers={
        "Content-Type": "application/json", "X-Wealth-Event": event,
        "X-Wealth-Signature": f"sha256={sig}", "User-Agent": "wealth-dashboard"})
    error = None
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status >= 300:
                error = f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        error = f"HTTP {exc.code}"
    except Exception as exc:                            # noqa: BLE001
        error = str(exc)[:200]
    with get_conn() as conn:
        conn.execute("UPDATE webhooks SET last_at = ?, last_error = ? WHERE id = ?",
                     (datetime.now(timezone.utc).isoformat(timespec="seconds"), error, hook["id"]))


def fire(event: str, data: dict, wait: bool = False) -> int:
    """Send `event` to every hook subscribed to it. Returns how many."""
    if event not in EVENTS:
        raise ValueError(f"Unknown event {event!r}")
    hooks = [h for h in all_hooks() if event in (h["events"] or "").split(",")]
    if not hooks:
        return 0
    body = json.dumps({"event": event, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "data": data}, ensure_ascii=False, default=str).encode()
    for h in hooks:
        t = threading.Thread(target=_post, args=(h, event, body), daemon=True)
        t.start()
        if wait:
            t.join(TIMEOUT + 1)
    return len(hooks)
