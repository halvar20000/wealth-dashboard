"""A scan, made readable — when the machine has the tools for it.

A PDF downloaded from a bank carries its text: the letters are stored
with their coordinates, and every reader in this app asks pypdf for
them. A scanned sheet carries a picture and no text at all, so there
is nothing to read and nothing a reader can do about it.

`ocrmypdf` fixes exactly that: it recognises the letters and writes
them back into the same PDF as a text layer, leaving the picture
alone. Then the readers work unchanged — including the ones that read
by column, because the recognised words keep their positions.

It is not a dependency of this app. The image ships without it,
because a tesseract and a ghostscript are a few hundred megabytes for
something most people never need: a statement downloaded from the
bank is already text. Where the binary is on PATH, this module uses
it; where it is not, the app says so in as many words instead of
"not recognised" — see `looks_scanned`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

# Enough text on a page to call it text: a scan often yields a stray
# character or two from a logo, which is not a statement.
MIN_CHARS = 40


def available() -> bool:
    """Whether this machine can OCR a scan."""
    return bool(shutil.which("ocrmypdf")) and os.environ.get("WD_OCR", "1") != "0"


def looks_scanned(content: bytes, text: str | None) -> bool:
    """A PDF with no text worth the name — a picture of a page."""
    return bool(content[:4] == b"%PDF" and len((text or "").strip()) < MIN_CHARS)


def text_layer(content: bytes, language: str | None = None, timeout: int = 300) -> bytes | None:
    """The same PDF with a text layer added, or None when that cannot
    be done here. The original is never modified: ocrmypdf writes a
    copy, and `--skip-text` leaves pages that already carry text as
    they are."""
    if not available():
        return None
    lang = language or os.environ.get("WD_OCR_LANGUAGE") or "eng+deu+fra"
    with tempfile.TemporaryDirectory(prefix="wd-ocr-") as tmp:
        src, dst = os.path.join(tmp, "in.pdf"), os.path.join(tmp, "out.pdf")
        with open(src, "wb") as fh:
            fh.write(content)
        try:
            subprocess.run(["ocrmypdf", "--skip-text", "--quiet", "-l", lang, src, dst],
                           check=True, timeout=timeout, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except (subprocess.SubprocessError, OSError):
            return None
        try:
            with open(dst, "rb") as fh:
                return fh.read()
        except OSError:
            return None
