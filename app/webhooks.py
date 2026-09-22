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
KINDS = ("json", "ntfy")
TIMEOUT = 5

# What a phone should see on its lock screen. The JSON payload is for a
# program; ntfy carries a line of prose, a title and a priority, and
# nothing else is needed to get a notification on Android.
_NTFY = {
    "sync.completed": ("Sync done", "white_check_mark", 2),
    "sync.failed": ("Sync failed", "warning", 4),
    "bill.missed": ("Bill missed", "rotating_light", 4),
}


def all_hooks() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM webhooks ORDER BY id")]


def add(url: str, events: list[str] | None = None, kind: str = "json") -> int:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("A webhook needs an http:// or https:// URL.")
    chosen = [e for e in (events or EVENTS) if e in EVENTS] or list(EVENTS)
    kind = kind if kind in KINDS else "json"
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO webhooks (url, events, secret, kind) VALUES (?, ?, ?, ?)",
                           (url, ",".join(chosen), secrets.token_urlsafe(24), kind))
        return int(cur.lastrowid)


def delete(hook_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM webhooks WHERE id = ?", (hook_id,))


def message(event: str, data: dict) -> str:
    """One line for a phone. The data a sync sends is a list of what
    each account did; a bill sends the bill."""
    if event == "sync.completed":
        rows = data.get("results") or data.get("accounts") or []
        got = sum((r.get("inserted") or 0) for r in rows if isinstance(r, dict))
        names = ", ".join(str(r.get("account")) for r in rows if isinstance(r, dict) and r.get("account"))
        return f"{got} new rows" + (f" — {names}" if names else "")
    if event == "sync.failed":
        who = data.get("account") or data.get("aspsp_name") or "a connection"
        return f"{who}: {data.get('error') or 'the sync failed'}"
    if event == "bill.missed":
        name = data.get("name") or "a bill"
        due = data.get("due") or data.get("due_on") or ""
        amount = data.get("amount")
        return f"{name} was due {due}".strip() + (f" — {amount}" if amount is not None else "")
    return json.dumps(data, ensure_ascii=False, default=str)[:300]


def _post(hook: dict, event: str, body: bytes, data: dict | None = None) -> None:
    if (hook.get("kind") or "json") == "ntfy":
        title, tag, priority = _NTFY.get(event, ("Wealth Dashboard", "money_with_wings", 3))
        body = message(event, data or {}).encode()
        headers = {"Content-Type": "text/plain; charset=utf-8", "Title": title,
                   "Tags": tag, "Priority": str(priority), "X-Wealth-Event": event,
                   "User-Agent": "wealth-dashboard"}
        req = urllib.request.Request(hook["url"], data=body, method="POST", headers=headers)
    else:
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
        t = threading.Thread(target=_post, args=(h, event, body, data), daemon=True)
        t.start()
        if wait:
            t.join(TIMEOUT + 1)
    return len(hooks)
