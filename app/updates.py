"""Is there a newer version — and what would this install do about it.

Unraid checks its containers and Home Assistant its add-ons, but a
`pipx install` is silent: nothing ever tells the person that 0.51.0
exists. So, once a day, the app asks PyPI what the newest version is —
one small GET of a public JSON document, with nothing about the person
in it — and the version badge in the menu grows a dot when the answer
is newer than what is running.

Off the request path, like the rates: the check runs in the background
thread and stores its answer in app_state, and pages read the stored
answer. A failed check is silent — the newest version is an
improvement to the page, never a condition of it. Under Settings it is
a switch, on by default, because the app's promise is that it talks to
nobody it has not told you about.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from . import __version__
from .db import get_state, set_state

PYPI_URL = "https://pypi.org/pypi/wealth-dashboard/json"
USER_AGENT = f"wealth-dashboard/{__version__} (+https://github.com/halvar20000/wealth-dashboard)"
TIMEOUT = 10
EVERY = timedelta(hours=24)

_KEY_VERSION = "latest_version"
_KEY_CHECKED = "latest_checked_at"


def parse(version: str) -> tuple[int, ...]:
    """"0.50.0" < "0.51.0" < "0.51.10": as numbers, or "0.9" beats "0.50"."""
    return tuple(int(p) for p in re.findall(r"\d+", version)[:3])


def is_newer(candidate: str, running: str = __version__) -> bool:
    try:
        return parse(candidate) > parse(running)
    except ValueError:
        return False


def is_stale() -> bool:
    checked = get_state(_KEY_CHECKED)
    if not checked:
        return True
    try:
        return datetime.fromisoformat(checked) < datetime.now() - EVERY
    except ValueError:
        return True


def check() -> str | None:
    """Ask PyPI. Returns the newest version, or None if it could not be
    asked — and records the attempt either way, so a machine with no
    route to PyPI asks once a day, not once a minute."""
    set_state(_KEY_CHECKED, datetime.now().isoformat(timespec="seconds"))
    request = urllib.request.Request(PYPI_URL, headers={"User-Agent": USER_AGENT,
                                                        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            latest = json.loads(response.read().decode("utf-8"))["info"]["version"]
    except (urllib.error.URLError, OSError, TimeoutError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(latest, str) or not re.fullmatch(r"[\d.]+", latest):
        return None
    set_state(_KEY_VERSION, latest)
    return latest


def available() -> str | None:
    """The newer version the last check found, if any. No network."""
    latest = get_state(_KEY_VERSION)
    return latest if latest and is_newer(latest) else None


def install_kind(ingress: bool = False) -> str:
    """How this copy got here, which is how it gets updated.

    `ingress` is whether the request came through Home Assistant — the
    only reliable tell, since the add-on runs the same image Unraid does.
    """
    if ingress:
        return "hass"
    if Path("/.dockerenv").exists() or os.environ.get("WD_HOST") == "0.0.0.0":
        return "container"
    if "pipx" in sys.prefix:
        return "pipx"
    return "source"
