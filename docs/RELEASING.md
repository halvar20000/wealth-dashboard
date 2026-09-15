# Cutting a release

The version lives in **four places** and they must agree. The build refuses a
tag where they do not, because a version number that means nothing is worse
than no version number.

| Where | What |
|---|---|
| `app/__init__.py` | `__version__ = "0.8.0"` — the one place it is written |
| `CHANGELOG.md` | a `## [0.8.0] — YYYY-MM-DD` section saying what changed |
| `homeassistant/wealth-dashboard/config.yaml` | `version: 0.8.0` — the image tag the Home Assistant add-on pulls |
| the git tag | `v0.8.0` |

The add-on entry is why **a tag is not optional any more**: Home Assistant
installs `ghcr.io/halvar20000/wealth-dashboard:<version>`, and only a tag
publishes that. `latest` alone leaves Home Assistant users on the previous
release.

## The steps

```bash
# 1. Bump the version, in both places it is typed.
$EDITOR app/__init__.py homeassistant/wealth-dashboard/config.yaml

# 2. Write the entry. Newest at the top, under Added / Changed / Fixed /
#    Removed. Say what changed and why, not which files moved.
$EDITOR CHANGELOG.md

# 3. Check it before GitHub does. The suite verifies that the code, the
#    changelog and the ordering all agree.
python3 tests/test_all.py

# 4. Commit, tag, push both.
git commit -am "..."
git tag v0.8.0
git push && git push --tags
```

The tag build runs the suite, checks the four places against each other, then
publishes `ghcr.io/halvar20000/wealth-dashboard` as `0.8.0`, `0.8` and — only
from `main` — `latest`. The same tag runs `pypi.yml`, which builds the wheel,
installs it into a clean interpreter to prove it runs, and uploads it to PyPI
as `wealth-dashboard 0.8.0` — the version is read from `app/__init__.py`, so
there is no fifth place to type it.

PyPI publishing uses *trusted publishing*: the PyPI project trusts this
repository's `pypi.yml` workflow in the `pypi` environment, and no token is
stored anywhere. It is set up once, under the project's **Publishing** page
on PyPI (owner `halvar20000`, repository `wealth-dashboard`, workflow
`pypi.yml`, environment `pypi`).

## Which number to bump

While the major is `0`, nothing here is a stable API:

- **minor** (`0.7.0` → `0.8.0`) — a feature, or a change somebody will notice.
- **patch** (`0.8.0` → `0.8.1`) — a fix that changes nothing else.

A release that only touches `README.md`, `ROADMAP.md` or `docs/` does not need
a version at all; those paths do not rebuild the image. `CHANGELOG.md` does,
because the app reads it to render its own history.

## What the user sees

The version sits in the header of every page and links to the changelog,
rendered inside the app from the same `CHANGELOG.md` that ships in the image.
`/healthz` reports it too, so a monitor can spot a container that never
restarted after an update — which looks identical to a healthy one otherwise.

Release notes are written once, in English, and are **not** translated. A
translation of a note about a fix is one more thing that can be wrong about the
fix.

## Pinning, for the people installing it

`latest` follows `main`. Anyone who would rather updates were a decision pins
the tag instead:

```
ghcr.io/halvar20000/wealth-dashboard:0.8.0
```

In Unraid that is the **Repository** field on the container. The Home
Assistant add-on is always pinned: it pulls the version in its `config.yaml`,
and the next tag is what offers it an update.
