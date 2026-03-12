#!/bin/bash
set -e

# ── PUID / PGID support ───────────────────────────────────────────────────────
PUID=${PUID:-0}
PGID=${PGID:-0}

log() {
    echo "$(TZ=${TZ:-UTC} date '+%Y-%m-%d %H:%M:%S %Z') [INFO] $1"
}

if [ "$PUID" != "0" ] || [ "$PGID" != "0" ]; then
    log "Entrypoint | PUID=${PUID} PGID=${PGID}"

    # Create group if it doesn't exist
    if ! getent group coordinator > /dev/null 2>&1; then
        groupadd -g "$PGID" coordinator
    fi

    # Create user if it doesn't exist
    if ! getent passwd coordinator > /dev/null 2>&1; then
        useradd -u "$PUID" -g "$PGID" -d /app -s /sbin/nologin coordinator
    fi

    # Ensure /config is writable by the new user if mounted
    if [ -d "/config" ]; then
        chown -R "${PUID}:${PGID}" /config
        log "Config volume found | chowned to ${PUID}:${PGID}"
    else
        log "No config volume mounted | logs will go to console only"
    fi

    log "Starting app as PUID=${PUID} PGID=${PGID}"
    exec gosu coordinator python app.py
else
    log "Entrypoint | running as root (no PUID/PGID set)"
    log "Starting app as root"
    exec python app.py
fi
