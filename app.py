import os
import platform
import time
from datetime import datetime

from flask import Flask, g, request, jsonify, send_file, render_template
from werkzeug.exceptions import MethodNotAllowed

from constants import APP_VERSION, APP_COMMIT_SHA, APP_COMMIT_SHORT, AM_ROOMS, PM_ROOMS
from schedule import build_xlsx
from renderer import render_preview
from logging_utils import LOG_DIR, LOG_LEVEL, logger
from time_utils import count_brothers_in_room, person_on_sheet
from validation import validate_request_payload

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB max request size


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' blob:; "
        "script-src 'self' 'unsafe-inline'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none';"
    )
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), "
        "autoplay=(), "
        "camera=(), "
        "display-capture=(), "
        "encrypted-media=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "midi=(), "
        "payment=(), "
        "picture-in-picture=(), "
        "usb=()"
    )
    if os.environ.get("ENABLE_HSTS") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.endpoint in {"index", "health", "preview", "export"}:
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

ROUTE_LABELS = {
    "/": "App loaded",
    "/preview": "Preview requested",
    "/export": "Export requested",
    "/health": "Health check",
}

@app.before_request
def before_request():
    g.start_time = time.monotonic()


@app.after_request
def after_request(response):
    start_time = getattr(g, "start_time", time.monotonic())
    duration_ms = int((time.monotonic() - start_time) * 1000)
    label = ROUTE_LABELS.get(request.path, request.path)
    logger.info(f"{label} | method={request.method} | {response.status_code} ({duration_ms}ms)")
    return response


@app.errorhandler(MethodNotAllowed)
def handle_method_not_allowed(error):
    allowed_methods = ", ".join(error.valid_methods or [])
    logger.warning(
        f"Method not allowed | path={request.path} | method={request.method} | "
        f"allowed={allowed_methods or 'unknown'}"
    )
    return (
        jsonify(
            {
                "error": "Method not allowed",
                "path": request.path,
                "method": request.method,
                "allowed_methods": error.valid_methods or [],
            }
        ),
        405,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template(
        "index.html",
        version=APP_VERSION,
        commit_short=APP_COMMIT_SHORT,
        commit_sha=APP_COMMIT_SHA,
        now=datetime.now(),
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": APP_VERSION, "commit": APP_COMMIT_SHA}), 200


@app.route("/preview", methods=["POST"])
def preview():
    data = request.get_json(silent=True)
    payload, error_message = validate_request_payload(data, require_is_pm=True)
    if payload is None or error_message is not None:
        logger.warning(f"Preview request | validation failed | error={error_message}")
        return jsonify({"error": error_message}), 400

    people = payload["people"]
    is_pm = payload["is_pm"]
    room_data = payload["room_data"]
    sheet_name = "PM" if is_pm else "AM"

    try:
        image_buffer = render_preview(people, is_pm, room_data)
        rooms = PM_ROOMS if is_pm else AM_ROOMS
        visible = [p for p in people if person_on_sheet(p, is_pm)]
        sorted_people = sorted(visible, key=lambda p: p["name"])
        brothers = [count_brothers_in_room(sorted_people, room["time"]) for room in rooms]
        logger.info(
            f"Preview generated | sheet={sheet_name}, people={len(visible)}, brothers={brothers}"
        )
        return send_file(image_buffer, mimetype="image/png")
    except FileNotFoundError as e:
        logger.error(f"Template missing: {e}")
        return jsonify({"error": "Template file not found"}), 500
    except Exception as e:
        logger.error(f"Preview failed | sheet={sheet_name}, people={len(people)}, error={e}")
        return jsonify({"error": "Preview generation failed"}), 500


@app.route("/export", methods=["POST"])
def export():
    data = request.get_json(silent=True)
    payload, error_message = validate_request_payload(data)
    if payload is None or error_message is not None:
        logger.warning(f"Export request | validation failed | error={error_message}")
        return jsonify({"error": error_message}), 400

    people = payload["people"]
    room_data = payload["room_data"]

    try:
        xlsx_buffer = build_xlsx(people, room_data)
        am_visible = sorted(
            [p for p in people if person_on_sheet(p, False)], key=lambda p: p["name"]
        )
        pm_visible = sorted(
            [p for p in people if person_on_sheet(p, True)], key=lambda p: p["name"]
        )
        am_brothers = [count_brothers_in_room(am_visible, room["time"]) for room in AM_ROOMS]
        pm_brothers = [count_brothers_in_room(pm_visible, room["time"]) for room in PM_ROOMS]
        logger.info(
            f"Export generated | people={len(people)}, brothers=AM:{am_brothers} PM:{pm_brothers}"
        )
        return send_file(
            xlsx_buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="schedule-output.xlsx",
        )
    except FileNotFoundError as e:
        logger.error(f"Template missing: {e}")
        return jsonify({"error": "Template file not found"}), 500
    except Exception as e:
        logger.error(f"Export failed | people={len(people)}, error={e}")
        return jsonify({"error": "Export generation failed"}), 500


if __name__ == "__main__":
    log_dir_display = LOG_DIR if LOG_DIR else "console only"
    logger.info("=" * 60)
    logger.info(f"Coordinator v{APP_VERSION} ({APP_COMMIT_SHORT}) starting on port 8080")
    logger.info(f"logs={log_dir_display} | log_level={LOG_LEVEL}")
    logger.info(
        f"Python {platform.python_version()} | {platform.system()} {platform.release()} | {platform.machine()}"
    )
    app.run(host="0.0.0.0", port=8080, debug=False)
