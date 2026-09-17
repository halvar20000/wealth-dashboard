# Small, no build step, no compiler at runtime. `cryptography` ships
# manylinux wheels, so the slim image is enough on amd64 and arm64.
FROM python:3.12-slim

# Points the GHCR package at this repository, which is what makes the
# "Source" link on the package page work and what Unraid's update check
# reads the labels from.
LABEL org.opencontainers.image.source="https://github.com/halvar20000/wealth-dashboard" \
      org.opencontainers.image.description="Self-hosted net worth tracking. One SQLite file, no cloud, no account with anybody." \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

ENV PYTHONUNBUFFERED=1 \
    WD_DATA_DIR=/data \
    WD_HOST=0.0.0.0 \
    WD_PORT=8000 \
    TZ=UTC

# tzdata alone, and only because the app asks the operating system what
# month it is. Without it TZ is ignored, and a cash flow "this month"
# rolls over at UTC midnight for somebody who is not on UTC.
# setpriv comes with util-linux, which Debian cannot do without; the
# check is there so a base image that one day drops it fails the build
# rather than every container start.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && command -v setpriv

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY docker/entrypoint.sh /entrypoint.sh
# Read at runtime by the changelog page. In the image because a
# dashboard that cannot say what changed in the version you are
# running is asking you to go and find out on GitHub.
COPY CHANGELOG.md ./
# app/static/icon.png is a link to ../../icon.png, so the favicon needs
# the file at /app/icon.png — without it every page names an icon that
# is a 404, which is what the smoke test in the workflow first found.
COPY icon.png ./

# The image holds no data. Everything the user owns is in the volume,
# which is what makes "back up /data" a complete instruction — the bank
# credentials included: they sit in /data/secrets unless WD_SECRETS_DIR
# says otherwise.
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3).status==200 else 1)"

# The entrypoint starts as root, gives /data to PUID:PGID (1000 unless
# told otherwise; Unraid says 99:100) and drops to that user before the
# app runs — so the process that holds your finances is not root, and a
# folder Docker made as root on the first start still works. See
# docker/entrypoint.sh; `--user` skips all of it.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "app"]
