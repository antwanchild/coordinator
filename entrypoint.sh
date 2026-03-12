#!/bin/bash
set -e

# ── PUID / PGID support ───────────────────────────────────────────────────────
PUID=${PUID:-0}
PGID=${PGID:-0}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
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
        chown -R coordinator:coordinator /config
    fi

    # Re-execute as the specified user
    exec gosu coordinator python app.py
else
    log "Entrypoint | running as root (no PUID/PGID set)"
    exec python app.py
fi
