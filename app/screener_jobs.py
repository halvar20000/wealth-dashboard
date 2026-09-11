"""The Share Ideas refresh, as a job the app runs itself.

The boards read a cache; something has to fill it. There is no cron in a
container and no operator to run one, so the same daemon-thread pattern
that keeps the exchange rates and the prices current keeps this current
too: `main()` starts a loop that calls `refresh_all()` every hour, and
each module refreshes only the rows older than its `max_age_hours`, so
in practice the universe is refetched once a day and nothing happens on
the other twenty-three ticks.

A refresh is ~440 Yahoo requests with a polite pause between them —
several minutes. Hence:

  * **one at a time.** The Settings button and the hourly tick share a
    lock; a second request while one runs is answered "already running"
    rather than doubling the load on Yahoo.
  * **off the request path.** The button starts the job on a thread and
    returns; nobody waits minutes on a form post.
  * **fail-soft.** A symbol that fails keeps its old row with the error
    stamped; the loop goes on; the summary says how many failed.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from . import screener, screener_etf
from .db import get_conn, get_state, set_state

STATE_KEY = "screener_last_run"
_lock = threading.Lock()
_stop = threading.Event()


def is_running() -> bool:
    return _lock.locked()


def refresh_all(force: bool = False, log=None, pause: float | None = None) -> dict | None:
    """Both caches, in order: shares, then ETFs. None if one is already
    running — the caller decides whether that is worth mentioning."""
    if not _lock.acquire(blocking=False):
        return None
    try:
        _stop.clear()
        pause = screener.REQUEST_PAUSE if pause is None else pause
        with get_conn() as conn:
            shares = screener.refresh(conn, force=force, sleep_s=pause, log=log,
                                      stop=_stop.is_set)
            etfs = screener_etf.refresh(conn, force=force, sleep_s=pause, log=log,
                                        stop=_stop.is_set)
        set_state(STATE_KEY, datetime.now(timezone.utc).isoformat(timespec="seconds"))
        return {"shares": shares, "etfs": etfs}
    finally:
        _lock.release()


def start_background(force: bool = False, log=print) -> bool:
    """Kick off a refresh on its own thread. False if one is running."""
    if is_running():
        return False

    def run() -> None:
        try:
            info = refresh_all(force=force, log=lambda m: log(f"  ideas: {m}"))
            if info:
                log(f"  ideas: shares {info['shares']['ok']} ok, "
                    f"{info['shares']['failed']} failed; ETFs {info['etfs']['ok']} ok, "
                    f"{info['etfs']['failed']} failed", flush=True)
        except Exception as exc:                      # noqa: BLE001
            log(f"  ideas: unexpected: {exc}", flush=True)

    threading.Thread(target=run, name="ideas-refresh", daemon=True).start()
    return True


def loop(log=print) -> None:
    """The hourly tick. The first one is a minute after start-up, so a
    fresh install has boards to look at without anybody pressing
    anything — and a restart does not pile a refresh onto the start."""
    time.sleep(60)
    while True:
        try:
            info = refresh_all(log=lambda m: log(f"  ideas: {m}"))
            if info and (info["shares"]["attempted"] or info["etfs"]["attempted"]):
                log(f"  ideas: shares {info['shares']['ok']} ok, "
                    f"{info['shares']['failed']} failed; ETFs {info['etfs']['ok']} ok, "
                    f"{info['etfs']['failed']} failed", flush=True)
        except Exception as exc:                      # noqa: BLE001
            log(f"  ideas: unexpected: {exc}", flush=True)
        time.sleep(3600)


def last_run() -> str | None:
    return get_state(STATE_KEY)


def status() -> dict:
    """For the Settings page: when each cache was last filled, how many
    rows it holds, how many carry an error."""
    with get_conn() as conn:
        shares = conn.execute(
            "SELECT COUNT(*) AS n, SUM(last_error IS NOT NULL) AS errors, "
            "MAX(fetched_at) AS latest FROM screener_fundamentals").fetchone()
        etfs = conn.execute(
            "SELECT COUNT(*) AS n, SUM(last_error IS NOT NULL) AS errors, "
            "MAX(fetched_at) AS latest FROM screener_etfs").fetchone()
    return {"shares": dict(shares), "etfs": dict(etfs),
            "running": is_running(), "last_run": last_run()}
