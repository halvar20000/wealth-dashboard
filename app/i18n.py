"""Four languages, and the number and date shapes that go with them.

No gettext, no .po files, no compile step. The catalogues are plain
Python dicts keyed on the English string, which buys three things worth
more here than the tooling would be:

  * a template stays readable — `{{ _("Net worth") }}` says what it will
    render, and a reviewer who does not have the catalogue open can
    still see the page;
  * a missing translation falls back to English rather than to a blank
    or a msgid, so an incomplete catalogue is a partly-translated app
    and never a broken one;
  * there is nothing to build. `pybabel compile` in the Dockerfile would
    be a build step in an image whose selling point is that it has none,
    and a translation nobody can fix without installing a toolchain is a
    translation nobody fixes.

The cost is that two different English strings that happen to be equal
share one translation. Where that bites, the key carries a context in
brackets — `"Balance [account]"` — which `_()` strips before falling
back, so English still reads correctly with no catalogue at all.

The reader is addressed informally: du, tu, tú. This is an app somebody
runs on their own server for themselves.
"""

from __future__ import annotations

from datetime import date

from .lang import de, es, fr

# Order is the order of the picker. English first because it is the
# source; the rest alphabetically by their own name.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
}

CATALOGUES: dict[str, dict[str, str]] = {
    "de": de.STRINGS,
    "es": es.STRINGS,
    "fr": fr.STRINGS,
}

# How each language writes a thousand and a half.
#
#   en   1,234.56        de   1.234,56
#   fr   1 234,56        es   1.234,56
#
# French groups with a narrow no-break space, which is what the
# Imprimerie nationale asks for and what every French keyboard-adjacent
# reader expects; the others get a normal no-break space or a full stop.
# No separator may be a plain space: a number that can wrap in half is
# worse than one that is grouped wrongly.
NBSP = "\u00a0"
NARROW_NBSP = "\u202f"

FORMATS: dict[str, dict[str, str]] = {
    "en": {"group": NBSP, "decimal": ".", "date": "iso"},
    "de": {"group": ".", "decimal": ",", "date": "dmy."},
    "es": {"group": ".", "decimal": ",", "date": "dmy/"},
    "fr": {"group": NARROW_NBSP, "decimal": ",", "date": "dmy/"},
}

MONTHS_SHORT: dict[str, tuple[str, ...]] = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "de": ("Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
           "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"),
    "es": ("ene", "feb", "mar", "abr", "may", "jun",
           "jul", "ago", "sep", "oct", "nov", "dic"),
    "fr": ("janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."),
}

DEFAULT = "en"


def active() -> str:
    """The language of the request in flight.

    Here rather than in main.py because the modules that raise the
    sentences a user reads — categories.py refusing a name, auth.py
    refusing a password — are below the web layer and must not have to
    reach up into it to say something in the right language.

    Cached on `g`, which is per-request and therefore safe under the
    threaded server: resolving it costs a read of settings.json, and a
    table of two hundred rows would otherwise do that two hundred times.
    Outside a request — a script, the test suite calling straight in —
    it is English, because there is nobody to have a preference.
    """
    from flask import g, has_request_context, request

    if not has_request_context():
        return DEFAULT
    lang = getattr(g, "_language", None)
    if lang is None:
        from . import settings
        lang = resolve(settings.get("language"),
                       request.headers.get("Accept-Language"))
        g._language = lang
    return lang


def t(text: str) -> str:
    """Translate one string into the language of this request."""
    return translate(text, active())


def f(text: str, **values) -> str:
    """Translate, then fill its `{}` slots."""
    return fill(text, active(), **values)


def n(count: int, one: str, many: str, **values) -> str:
    """Translate the form that matches the count."""
    return plural(count, one, many, active(), **values)


def known(code: str | None) -> bool:
    return bool(code) and code in LANGUAGES


def from_accept_header(header: str | None) -> str | None:
    """The browser's preference, if we speak any of it.

    Only the language subtag is read: somebody asking for de-AT gets
    German, because a dashboard in a language they read beats one in
    English on the grounds that Austria is not Germany.
    """
    if not header:
        return None
    ranked: list[tuple[float, str]] = []
    for part in header.split(","):
        bits = part.strip().split(";")
        tag = bits[0].strip().lower()
        if not tag or tag == "*":
            continue
        quality = 1.0
        for extra in bits[1:]:
            extra = extra.strip()
            if extra.startswith("q="):
                try:
                    quality = float(extra[2:])
                except ValueError:
                    quality = 0.0
        ranked.append((quality, tag.split("-")[0]))
    for _quality, base in sorted(ranked, key=lambda p: -p[0]):
        if base in LANGUAGES:
            return base
    return None


def resolve(configured: str | None, accept_header: str | None = None) -> str:
    """Which language this request is in.

    A configured language wins. An empty setting means "follow the
    browser", which is the default: somebody who installs this and opens
    it in a German browser should not have to find a setting before the
    app speaks to them.
    """
    if known(configured):
        return configured                            # type: ignore[return-value]
    from_browser = from_accept_header(accept_header)
    return from_browser or DEFAULT


def _strip_context(text: str) -> str:
    """`"Balance [account]"` is the English string `"Balance"`.

    The bracket exists to keep two same-spelled English strings apart in
    the catalogues. It must never reach a page.
    """
    if text.endswith("]") and " [" in text:
        return text[:text.rindex(" [")]
    return text


def translate(text: str, lang: str) -> str:
    catalogue = CATALOGUES.get(lang)
    if catalogue:
        hit = catalogue.get(text)
        if hit:
            return hit
    return _strip_context(text)


def fill(text: str, lang: str, **values) -> str:
    """A translated string with values in it.

    `{}` placeholders rather than `%s`, because a catalogue is written by
    people and a stray percent sign in a translation is then a crash on a
    page rather than a typo on a page. A stray brace still is one, so a
    translation that will not fill is dropped for the English, which
    will.
    """
    translated = translate(text, lang)
    try:
        return translated.format(**values)
    except (KeyError, IndexError, ValueError):
        return _strip_context(text).format(**values)


def group(number: str, lang: str) -> str:
    """Re-punctuate a Python-formatted number for the language."""
    fmt = FORMATS.get(lang, FORMATS[DEFAULT])
    # Python gives 1,234.56. Swap through placeholders, because doing it
    # in two steps turns 1,234.56 into 1.234.56 whenever the group and
    # decimal separators trade places.
    return (number.replace(",", "\x00").replace(".", "\x01")
                  .replace("\x00", fmt["group"]).replace("\x01", fmt["decimal"]))


def money(amount, currency: str, lang: str) -> str:
    if amount is None:
        return "—"
    sign = "-" if amount < 0 else ""
    # NBSP before the currency: an amount that wraps between the number
    # and its currency is unreadable, and a table cell on a phone is
    # exactly where that happens.
    return (f"{sign}{group(f'{abs(amount):,.2f}', lang)}"
            f"{NBSP}{currency.upper()}")


def qty(value, lang: str) -> str:
    """Share counts. Fractional shares are normal now, and trailing
    zeroes on a whole number are noise."""
    if value is None:
        return "—"
    text = f"{value:,.4f}"
    # Trim the fraction before the separators move, so the rstrip is
    # looking at a full stop wherever it runs.
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return group(text or "0", lang)


def plural(count: int, one: str, many: str, lang: str, **values) -> str:
    """Two forms, which is all four of these languages need.

    English, German, French and Spanish all take the singular for one
    and the plural for everything else, so there is no plural-rule
    engine here and no `nplurals` header to get wrong. A language that
    needs more forms needs more than this function, and can have it
    then.

    `{n}` in the string is the count, grouped for the language; any
    other `{}` slots come from the keywords, as in `fill`.
    """
    return fill(one if count == 1 else many, lang,
                n=group(f"{count:,}", lang), **values)


def fmt_date(value, lang: str) -> str:
    """An ISO date as the language writes it.

    English keeps ISO. It is what the app has always shown, it is what
    the database holds, and 2026-09-05 is unambiguous in a way that
    09/05/2026 is not — which matters more on a page listing money than
    looking native does.
    """
    if not value:
        return "—"
    text = str(value)[:10]
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return text                       # not a date; show it as it is
    shape = FORMATS.get(lang, FORMATS[DEFAULT])["date"]
    if shape == "dmy.":
        return f"{parsed.day:02d}.{parsed.month:02d}.{parsed.year}"
    if shape == "dmy/":
        return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"
    return parsed.isoformat()


def fmt_month(value, lang: str) -> str:
    """`2026-09` as `Sep 2026`, in the language's own abbreviation."""
    if not value:
        return "—"
    text = str(value)
    try:
        year, month = int(text[:4]), int(text[5:7])
        name = MONTHS_SHORT.get(lang, MONTHS_SHORT[DEFAULT])[month - 1]
    except (ValueError, IndexError):
        return text
    return f"{name} {year}"
