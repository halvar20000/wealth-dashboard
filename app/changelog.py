"""CHANGELOG.md, read back out for the page that shows it.

One file, two readers: a person on GitHub and the app itself. The
alternative — a Python list of releases, with the markdown generated
from it — means the thing you edit is not the thing anyone reads, and
the two drift the first time somebody fixes a typo in the wrong one.

So this parses the subset of Markdown the changelog actually uses:

    ## [1.2.3] — 2026-09-10     a release
    ### Added                   a section within it
    - text, with `code`,        a bullet, possibly wrapped over
      **bold** and a [link](x)  several lines

Anything else in the file is ignored rather than shown wrongly. If the
file is missing entirely — a container built from a stripped context,
say — the page says so and the app carries on: nobody should lose their
dashboard because a documentation file did not ship.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from markupsafe import Markup

from .settings import APP_DIR, ROOT_DIR

# Beside the repo in a checkout and in the image; inside the package
# when installed from PyPI, where there is no repo to be beside.
CHANGELOG_PATH = next((p for p in (ROOT_DIR / "CHANGELOG.md", APP_DIR / "CHANGELOG.md")
                       if p.is_file()), ROOT_DIR / "CHANGELOG.md")

# "## [0.8.0] — 2026-09-10", with either kind of dash and the date
# optional, because a release written in a hurry still has to parse.
_RELEASE = re.compile(r"^##\s+\[?([0-9][^\]\s]*)\]?\s*[—–-]?\s*(.*)$")
_SECTION = re.compile(r"^###\s+(.+)$")
_BULLET = re.compile(r"^[-*]\s+(.+)$")
_LINK_DEF = re.compile(r"^\[[^\]]+\]:\s")

# The four Keep a Changelog headings this project uses. Named here
# rather than only in the file, because the page translates them —
# `_(name + " [changelog]")` is a key no extractor can see, so the test
# suite reads this tuple to know which keys the catalogues owe.
SECTIONS = ("Added", "Changed", "Fixed", "Removed")

# The class that colours each. Added and Fixed take the default chip,
# which is already the green one, so they name no class rather than
# naming one the stylesheet does not define. An unknown heading still
# renders, plainly.
SECTION_TONE = {"changed": "warn", "removed": "error"}


def _inline(text: str) -> Markup:
    """`code`, **bold** and [links] — escaped first, so a release note
    can contain a `<` without becoming markup."""
    out = html.escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    # Only http(s) links, and only ones written in full. A relative link
    # in a changelog points at the repository, not at this app, and
    # would 404 on a page that is not GitHub.
    out = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                 r'<a href="\2" rel="noreferrer">\1</a>', out)
    return Markup(out)


def load(path: Path | None = None) -> list[dict]:
    """Every release, newest first, as the template wants it."""
    path = path or CHANGELOG_PATH
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    releases: list[dict] = []
    section: dict | None = None
    bullet: list[str] | None = None

    def flush() -> None:
        """A bullet can wrap over several lines; it is finished by
        whatever comes next, including the end of the file."""
        nonlocal bullet
        if bullet and section is not None:
            section["items"].append(_inline(" ".join(bullet)))
        bullet = None

    for raw in lines:
        line = raw.rstrip()
        if _LINK_DEF.match(line):
            continue                     # the link definitions at the end
        m = _RELEASE.match(line)
        if m:
            flush()
            releases.append({"version": m.group(1),
                             "date": m.group(2).strip(),
                             "sections": []})
            section = None
            continue
        if not releases:
            continue                     # the preamble above the first release
        m = _SECTION.match(line)
        if m:
            flush()
            name = m.group(1).strip()
            section = {"name": name, "tone": SECTION_TONE.get(name.lower(), ""),
                       "items": []}
            releases[-1]["sections"].append(section)
            continue
        m = _BULLET.match(line.strip())
        if m and section is not None:
            flush()
            bullet = [m.group(1).strip()]
            continue
        if bullet is not None and line.strip():
            bullet.append(line.strip())  # a wrapped continuation line
            continue
        flush()
    flush()
    return releases


def latest() -> str | None:
    """The newest version named in the file, whatever the code thinks it
    is. The check that the two agree lives in the test suite and in CI —
    here it is only reported."""
    entries = load()
    return entries[0]["version"] if entries else None
