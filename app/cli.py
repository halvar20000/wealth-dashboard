"""The command line: `wealth-dashboard`, or `python -m app`.

Flags over environment variables for the person at a keyboard; the
environment still works, because that is how a container is told the
same things. Everything here happens before `.main` is imported —
settings reads the environment once, on import, and a flag applied
after that would be a flag that does nothing.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__

LOOPBACK = ("127.0.0.1", "localhost", "::1")


def _open_browser(url: str, delay: float = 1.5) -> None:
    """A moment after the server is up. From a terminal only: under
    systemd, nohup or Docker there is no browser to open, and a failed
    attempt would be the first line of every log."""
    def go() -> None:
        try:
            webbrowser.open(url)
        except Exception:                                # noqa: BLE001
            pass
    threading.Timer(delay, go).start()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="wealth-dashboard",
        description="Self-hosted net worth tracking. Starts the web app and "
                    "opens it in your browser.")
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
    args = parser.parse_args(argv)

    if args.data:
        os.environ["WD_DATA_DIR"] = str(Path(args.data).expanduser().resolve())
    if args.host:
        os.environ["WD_HOST"] = args.host
    if args.port:
        os.environ["WD_PORT"] = str(args.port)

    from .main import main as serve                      # noqa: E402

    host = os.environ.get("WD_HOST", "127.0.0.1")
    port = os.environ.get("WD_PORT", "8000")
    if not args.no_browser and host in LOOPBACK and sys.stdout.isatty():
        _open_browser(f"http://{host}:{port}/")
    serve()
