# Cutting a release

The version lives in **three places** and they must agree. The build refuses a
tag where they do not, because a version number that means nothing is worse
than no version number.

| Where | What |
|---|---|
| `app/__init__.py` | `__version__ = "0.8.0"` — the one place it is written |
| `CHANGELOG.md` | a `## [0.8.0] — YYYY-MM-DD` section saying what changed |
| the git tag | `v0.8.0` |

## The steps

```bash
# 1. Bump the version.
$EDITOR app/__init__.py

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

The tag build runs the suite, checks the three places against each other, then
publishes `ghcr.io/halvar20000/wealth-dashboard` as `0.8.0`, `0.8` and — only
from `main` — `latest`.

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

In Unraid that is the **Repository** field on the container.
