"""`wealth-dashboard install`: a way to start the app that is not a
terminal, and a way for it to be running after a reboot without one.

pipx cannot do this at install time — a wheel has no post-install step
— so it is a command, run once. It writes what each desktop already
knows how to read: a menu entry, a shortcut and a start-at-login hook,
per user, nothing needing root. `uninstall` removes exactly those.

Linux   ~/.local/share/applications/wealth-dashboard.desktop, a copy on
        the desktop, and a systemd user service (or, without systemd,
        an XDG autostart entry).
macOS   ~/Applications/Wealth Dashboard.app with an alias on the
        desktop, and a LaunchAgent.
Windows shortcuts in the Start Menu, on the desktop and in the Startup
        folder, made by PowerShell so no extra package is needed.

The shortcut runs the same command as the terminal would. Started twice,
the command notices the running copy and opens the browser on it, so
clicking the icon always ends on the dashboard, service or no service.
"""

from __future__ import annotations

import os
import plistlib
import shutil
import struct
import subprocess
import sys
from pathlib import Path

APP_NAME = "Wealth Dashboard"
SLUG = "wealth-dashboard"
BUNDLE_ID = "com.halvar20000.wealth-dashboard"
ICON = Path(__file__).resolve().parent / "static" / "icon.png"
_ROOT = Path(__file__).resolve().parent.parent
# `python -m app` from a checkout only imports from the repo directory;
# an installed package imports from anywhere, and then home is the
# sensible place for a shortcut to start in.
WORKDIR = _ROOT if (_ROOT / "requirements.txt").is_file() else Path.home()


def command(args: list[str], windowless: bool = False) -> list[str]:
    """How to start the app from a shortcut.

    The interpreter that runs this code, with `-m`, rather than the
    `wealth-dashboard` script on PATH: a desktop session's PATH often
    lacks ~/.local/bin, and a shortcut that says "command not found"
    says it in a window that closes before it can be read.
    """
    exe = Path(sys.executable)
    if windowless and sys.platform == "win32":
        quiet = exe.with_name("pythonw.exe")
        if quiet.exists():
            exe = quiet
    return [str(exe), "-m", __package__, *args]


def _run(cmd: list[str]) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _quote(arg: str) -> str:
    return f'"{arg}"' if " " in arg else arg


# ---------------------------------------------------------------- Linux

def _xdg_desktop() -> Path:
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.home() / "Desktop"


def _linux_paths() -> dict[str, Path]:
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return {
        "entry": data / "applications" / f"{SLUG}.desktop",
        "icon": data / "icons" / "hicolor" / "512x512" / "apps" / f"{SLUG}.png",
        "desktop": _xdg_desktop() / f"{SLUG}.desktop",
        "service": config / "systemd" / "user" / f"{SLUG}.service",
        "autostart": config / "autostart" / f"{SLUG}.desktop",
    }


def _systemd_user_works() -> bool:
    return shutil.which("systemctl") is not None and _run(
        ["systemctl", "--user", "show-environment"])


def _install_linux(args: list[str]) -> list[str]:
    p = _linux_paths()
    done = []
    p["icon"].parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ICON, p["icon"])

    exec_line = " ".join(_quote(a) for a in command(args))
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        "Comment=Self-hosted net worth tracking\n"
        f"Exec={exec_line}\n"
        f"Icon={p['icon']}\n"
        f"Path={WORKDIR}\n"
        "Terminal=false\n"
        "Categories=Office;Finance;\n"
    )
    for key in ("entry", "desktop"):
        p[key].parent.mkdir(parents=True, exist_ok=True)
        p[key].write_text(entry)
        # Executable, because GNOME shows a desktop file it cannot trust
        # as a document until it is.
        p[key].chmod(0o755)
        done.append(str(p[key]))
    _run(["update-desktop-database", str(p["entry"].parent)])

    if _systemd_user_works():
        unit = (
            "[Unit]\n"
            f"Description={APP_NAME}\n"
            "After=network.target\n\n"
            "[Service]\n"
            f"ExecStart={' '.join(_quote(a) for a in command(args + ['--no-browser']))}\n"
            f"WorkingDirectory={WORKDIR}\n"
            "Restart=on-failure\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )
        p["service"].parent.mkdir(parents=True, exist_ok=True)
        p["service"].write_text(unit)
        _run(["systemctl", "--user", "daemon-reload"])
        if _run(["systemctl", "--user", "enable", "--now", f"{SLUG}.service"]):
            done.append(f"{p['service']}  (enabled and started: systemctl --user status {SLUG})")
        else:
            done.append(f"{p['service']}  (written; enable it with: systemctl --user enable --now {SLUG})")
    else:
        p["autostart"].parent.mkdir(parents=True, exist_ok=True)
        p["autostart"].write_text(entry.replace(f"Exec={exec_line}",
                                                f"Exec={exec_line} --no-browser"))
        done.append(f"{p['autostart']}  (starts at login)")
    return done


def _uninstall_linux() -> list[str]:
    p = _linux_paths()
    gone = []
    if p["service"].exists():
        _run(["systemctl", "--user", "disable", "--now", f"{SLUG}.service"])
    for key in ("entry", "desktop", "service", "autostart", "icon"):
        if p[key].exists():
            p[key].unlink()
            gone.append(str(p[key]))
    if gone and p["service"].parent.exists():
        _run(["systemctl", "--user", "daemon-reload"])
    return gone


# ---------------------------------------------------------------- macOS

def _mac_paths() -> dict[str, Path]:
    home = Path.home()
    return {
        "app": home / "Applications" / f"{APP_NAME}.app",
        "alias": home / "Desktop" / f"{APP_NAME}.app",
        "agent": home / "Library" / "LaunchAgents" / f"{BUNDLE_ID}.plist",
    }


def _install_mac(args: list[str]) -> list[str]:
    p = _mac_paths()
    done = []
    app = p["app"]
    (app / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    (app / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)
    launcher = app / "Contents" / "MacOS" / SLUG
    launcher.write_text(f"#!/bin/sh\ncd {_quote(str(WORKDIR))}\nexec "
                        + " ".join(_quote(a) for a in command(args)) + "\n")
    launcher.chmod(0o755)
    icns = app / "Contents" / "Resources" / "icon.icns"
    has_icon = _run(["sips", "-s", "format", "icns", str(ICON), "--out", str(icns)])
    info = {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleExecutable": SLUG,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": _version(),
        "LSUIElement": True,     # no Dock icon: the browser is the window
    }
    if has_icon:
        info["CFBundleIconFile"] = "icon"
    with open(app / "Contents" / "Info.plist", "wb") as fh:
        plistlib.dump(info, fh)
    done.append(str(app))
    if not p["alias"].exists():
        p["alias"].symlink_to(app)
        done.append(str(p["alias"]))

    p["agent"].parent.mkdir(parents=True, exist_ok=True)
    agent = {
        "Label": BUNDLE_ID,
        "ProgramArguments": command(args + ["--no-browser"]),
        "WorkingDirectory": str(WORKDIR),
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
    }
    with open(p["agent"], "wb") as fh:
        plistlib.dump(agent, fh)
    loaded = _run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(p["agent"])]) \
        or _run(["launchctl", "load", "-w", str(p["agent"])])
    done.append(f"{p['agent']}  ({'loaded: starts at login' if loaded else 'written; loads at next login'})")
    return done


def _uninstall_mac() -> list[str]:
    p = _mac_paths()
    gone = []
    if p["agent"].exists():
        _run(["launchctl", "bootout", f"gui/{os.getuid()}", str(p["agent"])]) \
            or _run(["launchctl", "unload", "-w", str(p["agent"])])
        p["agent"].unlink()
        gone.append(str(p["agent"]))
    if p["alias"].is_symlink():
        p["alias"].unlink()
        gone.append(str(p["alias"]))
    if p["app"].exists():
        shutil.rmtree(p["app"])
        gone.append(str(p["app"]))
    return gone


# -------------------------------------------------------------- Windows

def _ico_from_png(png: Path, ico: Path) -> None:
    """An .ico that is the PNG in an envelope — allowed since Vista,
    and the only way to get one without an image library."""
    data = png.read_bytes()
    width, height = struct.unpack(">II", data[16:24])
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", width % 256, height % 256, 0, 0, 1, 32,
                        len(data), 6 + 16)
    ico.write_bytes(header + entry + data)


def _win_paths() -> dict[str, Path]:
    appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    programs = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return {
        "icon": local / SLUG / f"{SLUG}.ico",
        "menu": programs / f"{APP_NAME}.lnk",
        "startup": programs / "Startup" / f"{APP_NAME}.lnk",
        "desktop": Path("DESKTOP") / f"{APP_NAME}.lnk",   # resolved by PowerShell
    }


def _ps_shortcut(path: Path, cmd: list[str], icon: Path) -> str:
    target = cmd[0]
    arguments = " ".join(_quote(a) for a in cmd[1:])
    where = ("[Environment]::GetFolderPath('Desktop') + '\\" + path.name + "'"
             if path.parts[0] == "DESKTOP" else f"'{path}'")
    return (
        f"$s = $ws.CreateShortcut({where}); "
        f"$s.TargetPath = '{target}'; $s.Arguments = '{arguments}'; "
        f"$s.IconLocation = '{icon}'; $s.WorkingDirectory = '{WORKDIR}'; "
        "$s.WindowStyle = 7; $s.Save(); "
    )


def _install_windows(args: list[str]) -> list[str]:
    p = _win_paths()
    p["icon"].parent.mkdir(parents=True, exist_ok=True)
    _ico_from_png(ICON, p["icon"])
    p["startup"].parent.mkdir(parents=True, exist_ok=True)
    script = "$ws = New-Object -ComObject WScript.Shell; " + \
        _ps_shortcut(p["menu"], command(args, windowless=True), p["icon"]) + \
        _ps_shortcut(p["desktop"], command(args, windowless=True), p["icon"]) + \
        _ps_shortcut(p["startup"], command(args + ["--no-browser"], windowless=True), p["icon"])
    if not _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script]):
        raise RuntimeError("PowerShell could not create the shortcuts")
    return [str(p["menu"]), "the desktop", f"{p['startup']}  (starts at login)"]


def _uninstall_windows() -> list[str]:
    p = _win_paths()
    gone = []
    desktop = Path.home() / "Desktop" / f"{APP_NAME}.lnk"
    for path in (p["menu"], p["startup"], desktop, p["icon"]):
        if path.exists():
            path.unlink()
            gone.append(str(path))
    return gone


# ---------------------------------------------------------------- entry

def _version() -> str:
    from . import __version__
    return __version__


def install(args: list[str]) -> list[str]:
    """Write the shortcuts and the start-at-login hook; return what was written."""
    if sys.platform == "win32":
        return _install_windows(args)
    if sys.platform == "darwin":
        return _install_mac(args)
    return _install_linux(args)


def uninstall() -> list[str]:
    if sys.platform == "win32":
        return _uninstall_windows()
    if sys.platform == "darwin":
        return _uninstall_mac()
    return _uninstall_linux()
