import os
import re
import time
import platform
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.exceptions import MethodNotAllowed

from constants import APP_VERSION, APP_COMMIT_SHA, APP_COMMIT_SHORT, AM_ROOMS, PM_ROOMS, ALL_TIMES
from schedule import build_xlsx, person_on_sheet, count_brothers_in_room
from renderer import render_preview

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max request size
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}$')

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options']        = 'DENY'
    response.headers['Referrer-Policy']        = 'same-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' blob:; "
        "script-src 'self' 'unsafe-inline'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "object-src 'none';"
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
ROOM_TIME_SET = {room['time'] for room in AM_ROOMS + PM_ROOMS}


def to_minutes(time_str):
    hours, minutes = time_str.split(':')
    return int(hours) * 60 + int(minutes)


def is_valid_time_value(value):
    if not isinstance(value, str) or not TIME_PATTERN.match(value):
        return False
    return value in ALL_TIMES


def validate_people(people):
    if not isinstance(people, list):
        return None, 'people must be a list'

    validated_people = []
    for index, person in enumerate(people):
        if not isinstance(person, dict):
            return None, f'people[{index}] must be an object'

        name = person.get('name')
        ranges = person.get('ranges')
        if not isinstance(name, str) or not name.strip():
            return None, f'people[{index}].name must be a non-empty string'
        if not isinstance(ranges, list) or not ranges:
            return None, f'people[{index}].ranges must be a non-empty list'

        validated_ranges = []
        for range_index, time_range in enumerate(ranges):
            if not isinstance(time_range, dict):
                return None, f'people[{index}].ranges[{range_index}] must be an object'

            start = time_range.get('start')
            end = time_range.get('end')
            if not is_valid_time_value(start) or not is_valid_time_value(end):
                return None, f'people[{index}].ranges[{range_index}] must use 15-minute times between 11:00 and 16:45'
            if to_minutes(start) >= to_minutes(end):
                return None, f'people[{index}].ranges[{range_index}] end must be after start'

            validated_ranges.append({'start': start, 'end': end})

        validated_people.append({'name': name.strip(), 'ranges': validated_ranges})

    return validated_people, None


def validate_room_data(room_data):
    if room_data is None:
        return {}, None
    if not isinstance(room_data, dict):
        return None, 'room_data must be an object'

    validated_room_data = {}
    for room_time, raw_room in room_data.items():
        if room_time not in ROOM_TIME_SET:
            return None, f'room_data contains unsupported time "{room_time}"'
        if not isinstance(raw_room, dict):
            return None, f'room_data["{room_time}"] must be an object'

        off = raw_room.get('off', '')
        b_value = raw_room.get('b', '')
        s_value = raw_room.get('s', '')

        if off is None:
            off = ''
        if not isinstance(off, str):
            return None, f'room_data["{room_time}"].off must be a string'

        for field_name, field_value in (('b', b_value), ('s', s_value)):
            if field_value in ('', None):
                continue
            if isinstance(field_value, bool) or not isinstance(field_value, (int, str)):
                return None, f'room_data["{room_time}"].{field_name} must be a non-negative integer or empty'
            if not str(field_value).isdigit():
                return None, f'room_data["{room_time}"].{field_name} must be a non-negative integer or empty'

        validated_room_data[room_time] = {
            'off': off.strip(),
            'b': '' if b_value in ('', None) else str(int(str(b_value))),
            's': '' if s_value in ('', None) else str(int(str(s_value))),
        }

    return validated_room_data, None


def validate_request_payload(data, require_is_pm=False):
    if not data or not isinstance(data, dict):
        return None, 'Invalid request body'

    people, people_error = validate_people(data.get('people', []))
    if people_error:
        return None, people_error

    room_data, room_data_error = validate_room_data(data.get('room_data', {}))
    if room_data_error:
        return None, room_data_error

    is_pm = data.get('is_pm', False)
    if require_is_pm:
        if not isinstance(is_pm, bool):
            return None, 'is_pm must be a boolean'
    else:
        is_pm = bool(is_pm)

    return {'people': people, 'room_data': room_data, 'is_pm': is_pm}, None

@app.before_request
def before_request():
    request.start_time = time.monotonic()

@app.after_request
def after_request(response):
    start_time = getattr(request, 'start_time', time.monotonic())
    duration_ms = int((time.monotonic() - start_time) * 1000)
    label       = ROUTE_LABELS.get(request.path, request.path)
    logger.info(f"{label} | method={request.method} | {response.status_code} ({duration_ms}ms)")
    return response


@app.errorhandler(MethodNotAllowed)
def handle_method_not_allowed(error):
    allowed_methods = ', '.join(error.valid_methods or [])
    logger.warning(
        f"Method not allowed | path={request.path} | method={request.method} | "
        f"allowed={allowed_methods or 'unknown'}"
    )
    return jsonify({
        'error': 'Method not allowed',
        'path': request.path,
        'method': request.method,
        'allowed_methods': error.valid_methods or [],
    }), 405

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION, commit_short=APP_COMMIT_SHORT, now=datetime.now())


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': APP_VERSION, 'commit': APP_COMMIT_SHA}), 200


@app.route('/preview', methods=['POST'])
def preview():
    data = request.get_json(silent=True)
    payload, error_message = validate_request_payload(data, require_is_pm=True)
    if error_message:
        logger.warning(f"Preview request | validation failed | error={error_message}")
        return jsonify({'error': error_message}), 400

    people = payload['people']
    is_pm = payload['is_pm']
    room_data = payload['room_data']
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
    payload, error_message = validate_request_payload(data)
    if error_message:
        logger.warning(f"Export request | validation failed | error={error_message}")
        return jsonify({'error': error_message}), 400

    people = payload['people']
    room_data = payload['room_data']

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
    logger.info(f"Coordinator v{APP_VERSION} ({APP_COMMIT_SHORT}) starting on port 8080")
    logger.info(f"logs={log_dir_display} | log_level={LOG_LEVEL}")
    logger.info(f"Python {platform.python_version()} | {platform.system()} {platform.release()} | {platform.machine()}")
    app.run(host='0.0.0.0', port=8080, debug=False)
