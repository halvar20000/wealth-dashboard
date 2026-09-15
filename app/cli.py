"""The command line: `wealth-dashboard`, or `python -m app`.

    wealth-dashboard              start it — or, if it is already
                                  running, open it in the browser
    wealth-dashboard install      a menu entry, a desktop shortcut and
                                  start-at-login, for this user
    wealth-dashboard uninstall    remove those three again

Flags over environment variables for the person at a keyboard; the
environment still works, because that is how a container is told the
same things. Everything here happens before `.main` is imported —
settings reads the environment once, on import, and a flag applied
after that would be a flag that does nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from . import __version__

LOOPBACK = ("127.0.0.1", "localhost", "::1")


def running_version(host: str, port: str) -> str | None:
    """The version answering on host:port, if it is this app.

    A second start on a busy port used to die with "address in use",
    which is the right message for a server and the wrong one for a
    person who double-clicked the icon while the service was running.
    """
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/healthz", timeout=1.5) as r:
            body = json.load(r)
    except Exception:                                    # noqa: BLE001
        return None
    return body.get("version") if isinstance(body, dict) and body.get("ok") else None


def _has_display() -> bool:
    """Somewhere a browser could appear. A tty counts on Linux because
    a person typed the command; a headless box under nohup or systemd
    has neither, and webbrowser would fall back to lynx in the log."""
    if sys.platform in ("win32", "darwin"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) \
        or sys.stdout.isatty()


def _open_browser(url: str, delay: float = 0.0) -> None:
    def go() -> None:
        try:
            webbrowser.open(url)
        except Exception:                                # noqa: BLE001
            pass
    if delay:
        threading.Timer(delay, go).start()
    else:
        go()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wealth-dashboard",
        description="Self-hosted net worth tracking. Starts the web app and "
                    "opens it in your browser; `install` adds a shortcut "
                    "and starts it at login.")
    parser.add_argument("action", nargs="?", choices=["start", "install", "uninstall"],
                        default="start",
                        help="start (the default), install a menu entry, desktop "
                             "shortcut and start-at-login for this user, or "
                             "uninstall those")
    parser.add_argument("--host", metavar="ADDRESS",
                        help="address to listen on (default 127.0.0.1: this "
                             "machine only; 0.0.0.0 reaches the whole LAN)")
    parser.add_argument("--port", type=int, metavar="PORT",
                        help="port to listen on (default 8000)")
    parser.add_argument("--data", metavar="DIR",
                        help="folder for the database, settings and secrets "
                             "(default: your user data folder; printed on start)")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open the dashboard in a browser on start")
    parser.add_argument("--version", action="version",
                        version=f"wealth-dashboard {__version__}")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)

    if args.data:
        os.environ["WD_DATA_DIR"] = str(Path(args.data).expanduser().resolve())
    if args.host:
        os.environ["WD_HOST"] = args.host
    if args.port:
        os.environ["WD_PORT"] = str(args.port)
    host = os.environ.get("WD_HOST", "127.0.0.1")
    port = os.environ.get("WD_PORT", "8000")
    url = f"http://{'localhost' if host == '0.0.0.0' else host}:{port}/"

    if args.action in ("install", "uninstall"):
        from . import launcher
        # The shortcut repeats the flags it was installed with, so a
        # dashboard on --port 8001 stays on 8001 after the reboot.
        keep = []
        if args.host:
            keep += ["--host", args.host]
        if args.port:
            keep += ["--port", str(args.port)]
        if args.data:
            keep += ["--data", os.environ["WD_DATA_DIR"]]
        if args.action == "install":
            written = launcher.install(keep)
            print("Wealth Dashboard is in your applications and starts at login:")
            for line in written:
                print(f"  {line}")
            print(f"  it answers on {url}")
            print("Undo with: wealth-dashboard uninstall")
        else:
            removed = launcher.uninstall()
            print("Removed:" if removed else "Nothing to remove.")
            for line in removed:
                print(f"  {line}")
        return

    want_browser = not args.no_browser and host in LOOPBACK and _has_display()
    already = running_version(host, port)
    if already:
        print(f"Wealth Dashboard {already} is already running at {url}", flush=True)
        if want_browser:
            _open_browser(url)
        return

    from .main import main as serve                      # noqa: E402

    if want_browser:
        _open_browser(url, delay=1.5)
    serve()
