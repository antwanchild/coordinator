import os
import time
import platform
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, request, jsonify, send_file, render_template

from constants import APP_VERSION, AM_ROOMS, PM_ROOMS
from schedule import build_xlsx, person_on_sheet, count_brothers_in_room
from renderer import render_preview

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options']        = 'DENY'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' blob:; "
        "script-src 'self' 'unsafe-inline';"
    )
    return response

# ── Logging ───────────────────────────────────────────────────────────────────

log_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
logger = logging.getLogger('coordinator')

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

LOG_DIR = '/config/logs' if os.path.isdir('/config') else None

if LOG_DIR:
    os.makedirs(LOG_DIR, exist_ok=True)

    class WeeklyLogHandler(TimedRotatingFileHandler):
        """Rotate logs weekly, keeping .log extension on rotated files."""
        def rotation_filename(self, default_name):
            base   = os.path.join(LOG_DIR, 'coordinator')
            suffix = default_name.split('.')[-1]
            return f"{base}.{suffix}.log"

    file_handler = WeeklyLogHandler(
        os.path.join(LOG_DIR, 'coordinator.log'),
        when='W0', interval=1, backupCount=4, utc=False
    )
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

# ── Request logging ───────────────────────────────────────────────────────────

logging.getLogger('werkzeug').setLevel(logging.ERROR)

ROUTE_LABELS = {
    '/':        'App loaded',
    '/preview': 'Preview requested',
    '/export':  'Export requested',
    '/health':  'Health check',
}

@app.before_request
def before_request():
    request.start_time = time.monotonic()

@app.after_request
def after_request(response):
    duration_ms = int((time.monotonic() - request.start_time) * 1000)
    label       = ROUTE_LABELS.get(request.path, request.path)
    logger.info(f"{label} | {response.status_code} ({duration_ms}ms)")
    return response

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION, now=datetime.now())


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': APP_VERSION}), 200


@app.route('/preview', methods=['POST'])
def preview():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        logger.warning("Preview request | invalid or missing JSON body")
        return jsonify({'error': 'Invalid request body'}), 400

    people = data.get('people', [])
    if not isinstance(people, list):
        return jsonify({'error': 'people must be a list'}), 400

    is_pm      = bool(data.get('is_pm', False))
    room_data  = data.get('room_data', {})
    sheet_name = 'PM' if is_pm else 'AM'

    try:
        image_buffer  = render_preview(people, is_pm, room_data)
        rooms         = PM_ROOMS if is_pm else AM_ROOMS
        visible       = [p for p in people if person_on_sheet(p, is_pm)]
        sorted_people = sorted(visible, key=lambda p: p['name'])
        brothers      = [count_brothers_in_room(sorted_people, room['time']) for room in rooms]
        logger.info(f"Preview generated | sheet={sheet_name}, people={len(visible)}, brothers={brothers}")
        return send_file(image_buffer, mimetype='image/png')
    except FileNotFoundError as e:
        logger.error(f"Template missing: {e}")
        return jsonify({'error': 'Template file not found'}), 500
    except Exception as e:
        logger.error(f"Preview failed | sheet={sheet_name}, people={len(people)}, error={e}")
        return jsonify({'error': 'Preview generation failed'}), 500


@app.route('/export', methods=['POST'])
def export():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        logger.warning("Export request | invalid or missing JSON body")
        return jsonify({'error': 'Invalid request body'}), 400

    people = data.get('people', [])
    if not isinstance(people, list):
        return jsonify({'error': 'people must be a list'}), 400

    room_data = data.get('room_data', {})

    try:
        xlsx_buffer = build_xlsx(people, room_data)
        am_visible  = sorted([p for p in people if person_on_sheet(p, False)], key=lambda p: p['name'])
        pm_visible  = sorted([p for p in people if person_on_sheet(p, True)],  key=lambda p: p['name'])
        am_brothers = [count_brothers_in_room(am_visible, room['time']) for room in AM_ROOMS]
        pm_brothers = [count_brothers_in_room(pm_visible, room['time']) for room in PM_ROOMS]
        logger.info(f"Export generated | people={len(people)}, brothers=AM:{am_brothers} PM:{pm_brothers}")
        return send_file(
            xlsx_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='schedule-output.xlsx'
        )
    except FileNotFoundError as e:
        logger.error(f"Template missing: {e}")
        return jsonify({'error': 'Template file not found'}), 500
    except Exception as e:
        logger.error(f"Export failed | people={len(people)}, error={e}")
        return jsonify({'error': 'Export generation failed'}), 500


if __name__ == '__main__':
    log_dir_display = LOG_DIR if LOG_DIR else 'console only'
    logger.info("=" * 60)
    logger.info(f"Coordinator v{APP_VERSION} starting on port 8080")
    logger.info(f"logs={log_dir_display} | log_level={LOG_LEVEL}")
    logger.info(f"Python {platform.python_version()} | {platform.system()} {platform.release()} | {platform.machine()}")
    app.run(host='0.0.0.0', port=8080, debug=False)
