#!/bin/sh
# The container's first process.
#
# Started as root, which is Docker's default: give the data folder (and
# the secrets folder, when it is mounted apart) to PUID:PGID, then drop
# to that user and run the app. A folder Docker created as root on the
# first start is made usable in the same breath, so there is no init
# container and no "chown appdata" step in the install guide. Unraid
# passes 99:100 (nobody:users), the default matches the first user on a
# desktop Linux, and PUID=0 keeps root for the one mount that will not
# take a chown.
#
# Started as somebody else (docker run --user, a rootless engine, the
# Home Assistant supervisor when it chooses to): nothing to do, the
# folders must already be writable, run the app.

set -eu

if [ "$(id -u)" != "0" ]; then
    exec "$@"
fi

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

case "$PUID$PGID" in
    *[!0-9]*|"") echo "PUID and PGID must be numbers (got PUID=$PUID PGID=$PGID)" >&2; exit 1 ;;
esac

if [ "$PUID" = "0" ]; then
    echo "  running as root (PUID=0)" >&2
    exec "$@"
fi

for dir in "${WD_DATA_DIR:-/data}" "${WD_SECRETS_DIR:-}"; do
    [ -n "$dir" ] || continue
    mkdir -p "$dir"
    # Only what is not already right: a restart on a large folder must
    # not spend its first minute in chown.
    if ! find "$dir" \( ! -user "$PUID" -o ! -group "$PGID" \) -exec chown "$PUID:$PGID" {} + 2>/dev/null; then
        echo "Warning: could not give $dir to $PUID:$PGID; the app may not be able to write there. PUID=0 keeps root." >&2
    fi
done

# No home for this uid in the image, and nothing needs one — but
# libraries that look one up should find a writable answer.
export HOME=/tmp
exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups "$@"
