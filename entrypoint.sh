#!/bin/bash
set -e

# ── PUID / PGID support ───────────────────────────────────────────────────────
PUID=${PUID:-0}
PGID=${PGID:-0}
RUNTIME_USER=coordinator
RUNTIME_GROUP=coordinator

log() {
    echo "$(TZ=${TZ:-UTC} date '+%Y-%m-%d %H:%M:%S %Z') [INFO] $1"
}

if [ "$PUID" != "0" ] || [ "$PGID" != "0" ]; then
    log "Entrypoint | PUID=${PUID} PGID=${PGID}"

    # Create a mapped runtime group/user if the requested IDs are available.
    if ! getent group "$PGID" > /dev/null 2>&1; then
        groupadd -g "$PGID" coordinator-runtime
        RUNTIME_GROUP=coordinator-runtime
    else
        RUNTIME_GROUP="$(getent group "$PGID" | cut -d: -f1)"
    fi

    if ! getent passwd "$PUID" > /dev/null 2>&1; then
        useradd -u "$PUID" -g "$RUNTIME_GROUP" -d /app -s /sbin/nologin coordinator-runtime
        RUNTIME_USER=coordinator-runtime
    else
        RUNTIME_USER="$(getent passwd "$PUID" | cut -d: -f1)"
    fi

    # Ensure /config is writable by the new user if mounted
    if [ -d "/config" ]; then
        chown -R "${PUID}:${PGID}" /config
        log "Config volume found | chowned to ${PUID}:${PGID}"
    else
        log "No config volume mounted | logs will go to console only"
    fi

    log "Starting app as PUID=${PUID} PGID=${PGID}"
    exec gosu "$RUNTIME_USER" gunicorn --bind 0.0.0.0:8080 --access-logfile - --error-logfile - --worker-tmp-dir /tmp --workers "${WEB_CONCURRENCY:-2}" --threads "${GUNICORN_THREADS:-4}" app:app
else
    log "Entrypoint | running as root (no PUID/PGID set)"
    log "Starting app as coordinator"
    exec gosu coordinator gunicorn --bind 0.0.0.0:8080 --access-logfile - --error-logfile - --worker-tmp-dir /tmp --workers "${WEB_CONCURRENCY:-2}" --threads "${GUNICORN_THREADS:-4}" app:app
fi
