"""Where things live, and the handful of settings that are not secrets.

Two directories, and the split between them is deliberate:

    DATA_DIR     the database and settings.json — the folder to back up
    SECRETS_DIR  credentials only, default DATA_DIR/secrets

They are separate so that "back up your data" and "copy your API keys to
another machine" are different actions. A user who syncs DATA_DIR to a
NAS should not thereby have copied a bank credential to it.

Everything is overridable by environment variable, because that is how a
container is configured and the user cannot edit a file inside one.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent


def user_data_dir() -> Path:
    """Where the operating system says a program keeps a person's data.

    Used when the app was installed as a package rather than cloned: a
    `data/` folder next to the code would then be inside site-packages,
    which the next `pipx upgrade` replaces."""
    if sys.platform == "win32":
        base = (os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
                or str(Path.home() / "AppData" / "Local"))
        return Path(base) / "wealth-dashboard"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "wealth-dashboard"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "wealth-dashboard"


def _data_dir() -> Path:
    env = os.environ.get("WD_DATA_DIR")
    if env:
        return Path(env)
    # In a container /data is the mounted volume. Outside one, a folder
    # beside the repo, so `git clone && python -m app` works with no
    # arguments — the most common way somebody tries an app for the
    # first time, and the one most likely to be abandoned if it asks a
    # question before it shows anything.
    if Path("/data").is_dir() and os.access("/data", os.W_OK):
        return Path("/data")
    # A checkout has requirements.txt beside the package; an installed
    # copy in site-packages does not, and its data belongs to the user,
    # not to the package.
    if (ROOT_DIR / "requirements.txt").is_file():
        return ROOT_DIR / "data"
    return user_data_dir()


DATA_DIR = _data_dir()
SECRETS_DIR = Path(os.environ.get("WD_SECRETS_DIR") or (DATA_DIR / "secrets"))
DB_PATH = Path(os.environ.get("WD_DB_PATH") or (DATA_DIR / "wealth.db"))
SETTINGS_FILE = DATA_DIR / "settings.json"

# Credentials inside the data folder are copied by every backup of it.
# Not an error — it is the sane default for a single-volume install —
# but the UI says so rather than letting the user assume otherwise.
SECRETS_INSIDE_DATA = SECRETS_DIR.resolve() == DATA_DIR.resolve() or \
    SECRETS_DIR.resolve().is_relative_to(DATA_DIR.resolve())

DEFAULTS: dict[str, Any] = {
    "version": 1,
    "base_currency": "EUR",
    # Empty means "whatever the browser asks for, English if it asks for
    # nothing we speak". A fresh install in a German browser should be
    # in German before anybody finds a setting to put it there.
    "language": "",
    # Where the bank sends the user back after they authenticate. It has
    # to match a URL registered in the Enable Banking control panel
    # EXACTLY, so it is a setting rather than something derived from the
    # request — a user reaching the app on a LAN IP and on localhost
    # would otherwise generate two different values and only one of them
    # would be registered.
    "redirect_url": "http://localhost:8000/connect/callback",
    # How long to ask the bank to keep the consent alive. PSD2 caps this
    # at 90 days for most banks; asking for more is refused outright.
    "consent_days": 90,
    # Pull every connected account once a day, at this local time. A
    # bank's overnight batch has usually landed by noon, and a sync at
    # noon is one nobody has to remember.
    "auto_sync": True,
    "sync_time": "12:00",
    # Which units a sale sells: "fifo" (the oldest first — Germany's
    # rule) or "average" (every unit at the average paid — France's
    # prix moyen pondéré). A tax question, so a setting, never a guess.
    "gains_method": "fifo",
    # Ask PyPI once a day whether there is a newer version. One public
    # GET with nothing about the user in it; still, a switch, because
    # the promise is that the app talks to nobody it has not named.
    "check_updates": True,
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        SECRETS_DIR.chmod(0o700)
    except OSError:
        pass                      # a mounted volume may refuse; not fatal


def load() -> dict:
    cfg = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            user = json.loads(SETTINGS_FILE.read_text())
            if isinstance(user, dict):
                cfg.update(user)
        except (json.JSONDecodeError, OSError):
            # A broken settings file must not stop the app starting: a
            # user who cannot start the app cannot fix the file.
            pass
    for key, env in (("base_currency", "WD_BASE_CURRENCY"),
                     ("redirect_url", "WD_REDIRECT_URL")):
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    return cfg


def save(cfg: dict) -> None:
    ensure_dirs()
    tmp = SETTINGS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n")
    tmp.replace(SETTINGS_FILE)          # atomic: never a half-written config


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)
