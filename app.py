import io, copy, json, re, os, logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_file, render_template
import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont
import math

app = Flask(__name__)
TEMPLATE_PATH = "V-COORDINATE--Scheduled.xlsx"
APP_VERSION = os.environ.get('APP_VERSION', 'dev')

# ── Logging ───────────────────────────────────────────────────────────────────
from logging.handlers import TimedRotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('coordinator')
logger.setLevel(logging.INFO)

# File logging — only if /config is mounted, otherwise console only
LOG_DIR = '/config/logs' if os.path.isdir('/config') else None
if LOG_DIR:
    os.makedirs(LOG_DIR, exist_ok=True)

    class WeeklyLogHandler(TimedRotatingFileHandler):
        def rotation_filename(self, default_name):
            # Rename rotated files from coordinator.log.YYYY-MM-DD to coordinator.YYYY-MM-DD.log
            base = os.path.join(LOG_DIR, 'coordinator')
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
logger.addHandler(​​​​​​​​​​​​​​​​


# ── Layout constants (Excel units → pixels at 96dpi) ──────────────────────────
# Excel col width in chars → pixels scaled for compact preview display
# Full formula (chars*7+5) produces 96px per slot which is too wide
# Scale factor of 0.25 gives ~24px per slot — compact and readable
def col_px(chars):
    return max(4, int(chars * 7 + 5))

def row_px(pts):
    # Excel row height in points → pixels at 96dpi: px = pts * 96/72
    return max(4, int(pts * 96 / 72))

# Col widths from file
COL_WIDTHS_CHARS = {
    1: 5.28,   # A - spacer
    2: 3.85,   # B - row numbers
    3: 11.28,  # C - names
    4: 1.85,   # D - slot 1 (narrow)
}
# Cols 5-65: all 13.0 chars
for c in range(5, 66):
    COL_WIDTHS_CHARS[c] = 13.0

# Row heights from file (pts), defaults where None
ROW_HEIGHTS_PT = {
    1: 17.25, 2: 15.0, 3: 15.0, 4: 15.75, 5: 20.25,
}
for r in range(6, 24):
    ROW_HEIGHTS_PT[r] = 18.0
for r in range(24, 31):
    ROW_HEIGHTS_PT[r] = 15.0
ROW_HEIGHTS_PT[30] = 15.75

# Pre-compute pixel widths — matched to original xlsx proportions
COL_PX = {}
COL_PX[1] = 10   # A spacer (narrow)
COL_PX[2] = 31   # B row numbers — exact from file (3.85 chars)
COL_PX[3] = 100  # C names — slightly wider for readability
for c in range(4, 66):
    COL_PX[c] = 24  # all slot columns uniform — including narrow slot 1
ROW_PX = {r: row_px(h) for r, h in ROW_HEIGHTS_PT.items()}

# Room structure
SLOTS = 12
ROWS = 18  # data rows
ROOM_START_COLS = [4, 16, 28, 40, 52]  # 1-indexed col D, P, AB, AN, AZ

AM_ROOMS = [
    {'label':'Room: 1','time':'11:00','time_raw':'  Time: 11:00+','n24':'#5--tight fit to Cel Room','n25':'','red':True,'letter':'B','wlkr':'(#2/#3)'},
    {'label':'Room: 2','time':'11:30','time_raw':'  Time: 11:30+','n24':'','n25':'','red':False,'letter':'','wlkr':''},
    {'label':'Room: 3','time':'12:00','time_raw':'  Time: 12:00+','n24':'','n25':'','red':False,'letter':'','wlkr':''},
    {'label':'Room: 4','time':'12:30','time_raw':'  Time: 12:30+','n24':'#4--tight fit to Cel Room','n25':'Use thin rec. for #1-#4','red':True,'letter':'S','wlkr':'(#6/#7)'},
    {'label':'Room: 1','time':'13:00','time_raw':'  Time: 1:00+', 'n24':'#5--tight fit to Cel Room','n25':'','red':True,'letter':'B','wlkr':'(#2/#3)'},
]
PM_ROOMS = [
    {'label':'Room: 3','time':'14:00','time_raw':'  Time: 2:00+','n24':'','n25':'','red':False,'letter':'','wlkr':''},
    {'label':'Room: 4','time':'14:30','time_raw':'  Time: 2:30+','n24':'#4--tight fit to Cel Room','n25':'Use thin rec. for #1-#4','red':True,'letter':'S','wlkr':'(#6/#7)'},
    {'label':'Room: 1','time':'15:00','time_raw':'  Time: 3:00+','n24':'#5--tight fit to Cel Room','n25':'','red':True,'letter':'B','wlkr':'(#2/#3)'},
    {'label':'Room: 2','time':'15:30','time_raw':'  Time: 3:30+','n24':'','n25':'','red':False,'letter':'','wlkr':''},
    {'label':'Room: 3','time':'16:00','time_raw':'  Time: 4:00+','n24':'','n25':'','red':False,'letter':'','wlkr':''},
]

# Slot colors (12 slots per room)
SLOT_COLORS = [
    '#B4C6E7','#FFFFFF','#FFE598','#C5DEB5',
    '#B4C6E7','#B4C6E7',
    '#FFFFFF','#FFFFFF',
    '#FFE598','#FFE598',
    '#C5DEB5','#C5DEB5',
]
SLOT_LABELS = ['1','2','3','4','5P','5','6P','6','7P','7','8P','8']
YELLOW = '#FFFF00'

# ── Time helpers ──────────────────────────────────────────────────────────────
def to_min(t):
    if not t: return 0
    h, m = t.split(':')
    return int(h)*60 + int(m)

def covers(ranges, room_time):
    rt = to_min(room_time)
    return any(to_min(r['start']) <= rt < to_min(r['end']) for r in ranges)

def person_on_sheet(person, is_pm):
    domain = ['14:00','14:30','15:00','15:30','16:00'] if is_pm else ['11:00','11:30','12:00','12:30','13:00']
    d_min = to_min(domain[0])
    d_max = to_min(domain[-1]) + 30
    return any(to_min(r['start']) < d_max and to_min(r['end']) > d_min for r in person['ranges'])

# ── Build xlsx from template ──────────────────────────────────────────────────
def build_xlsx(people):
    wb = load_workbook(TEMPLATE_PATH)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        is_pm = 'PM' in sheet_name.upper()
        rooms = PM_ROOMS if is_pm else AM_ROOMS
        visible = [p for p in people if person_on_sheet(p, is_pm)]
        sorted_people = sorted(visible, key=lambda p: p['name'])

        for i in range(ROWS):
            is_off = (i == 0)
            p = None if is_off else (sorted_people[i-1] if i-1 < len(sorted_people) else None)
            row = 6 + i  # Excel row (1-indexed), data starts row 6

            # Row number (col B = col 2)
            ws.cell(row=row, column=2).value = i + 1
            # Name (col C = col 3)
            ws.cell(row=row, column=3).value = 'Off.' if is_off else (p['name'] if p else '')

            # Slot fills
            if p:
                for ri, room in enumerate(rooms):
                    avail = covers(p['ranges'], room['time'])
                    if not avail:
                        start_col = ROOM_START_COLS[ri]
                        fill = PatternFill(patternType='solid', fgColor='FFFF00')
                        for s in range(SLOTS):
                            ws.cell(row=row, column=start_col + s).fill = fill
            elif not is_off:
                # Empty row — clear any yellow (restore base colors)
                pass

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ── Render preview image ──────────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def render_preview(people, is_pm):
    rooms = PM_ROOMS if is_pm else AM_ROOMS
    visible = [p for p in people if person_on_sheet(p, is_pm)]
    sorted_people = sorted(visible, key=lambda p: p['name'])

    # Build column x-positions (1-indexed cols 1..65)
    total_cols = 65
    x_pos = {}
    x = 0
    for c in range(1, total_cols + 1):
        x_pos[c] = x
        x += COL_PX.get(c, col_px(13.0))
    total_w = x

    # Build row y-positions (rows 1..30)
    total_rows = 30
    y_pos = {}
    y = 0
    for r in range(1, total_rows + 1):
        y_pos[r] = y
        y += ROW_PX.get(r, row_px(15.0))
    total_h = y

    img = Image.new('RGB', (total_w, total_h), 'white')
    draw = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
        font_md = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        font_bd = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 11)
        font_bd14 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
        font_red = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except:
        font_sm = font_md = font_bd = font_bd14 = font_red = ImageFont.load_default()

    def cell_rect(col, row, colspan=1, rowspan=1):
        x1 = x_pos[col]
        y1 = y_pos[row]
        x2 = x_pos[col + colspan] if (col + colspan) in x_pos else total_w
        y2 = y_pos[row + rowspan] if (row + rowspan) in y_pos else total_h
        return x1, y1, x2, y2

    def fill_cell(col, row, color, colspan=1, rowspan=1):
        x1,y1,x2,y2 = cell_rect(col, row, colspan, rowspan)
        draw.rectangle([x1,y1,x2-1,y2-1], fill=hex_to_rgb(color))

    def draw_text(col, row, text, font, color='#000000', align='left', colspan=1, rowspan=1):
        x1,y1,x2,y2 = cell_rect(col, row, colspan, rowspan)
        rgb = hex_to_rgb(color)
        pad = 3
        tw = x2 - x1 - pad*2
        th = y2 - y1
        while text and draw.textlength(text, font=font) > tw:
            text = text[:-1]
        tl = draw.textlength(text, font=font)
        if align == 'center':
            tx = x1 + (x2-x1-tl)//2
        elif align == 'right':
            tx = x2 - tl - pad
        else:
            tx = x1 + pad
        bbox = font.getbbox(text)
        fh = bbox[3] - bbox[1] if text else 10
        ty = y1 + (th - fh)//2
        draw.text((tx, ty), text, fill=rgb, font=font)

    def border(col, row, colspan=1, rowspan=1, left=None, right=None, top=None, bottom=None):
        x1,y1,x2,y2 = cell_rect(col, row, colspan, rowspan)
        x2-=1; y2-=1
        def bstyle(s):
            if s == 'double': return (hex_to_rgb('#595959'), 2)
            if s == 'medium': return (hex_to_rgb('#595959'), 2)
            if s == 'thin':   return (hex_to_rgb('#aaaaaa'), 1)
            return None
        if left:
            c,w = bstyle(left)
            draw.line([(x1,y1),(x1,y2)], fill=c, width=w)
        if right:
            c,w = bstyle(right)
            draw.line([(x2,y1),(x2,y2)], fill=c, width=w)
        if top:
            c,w = bstyle(top)
            draw.line([(x1,y1),(x2,y1)], fill=c, width=w)
        if bottom:
            c,w = bstyle(bottom)
            draw.line([(x1,y2),(x2,y2)], fill=c, width=w)

    # ── Draw header rows 1-5 ─────────────────────────────────────────────────
    label = 'P.M.' if is_pm else 'A.M.'

    # AM/PM cell col C rows 1-4
    fill_cell(3, 1, '#FFFFFF', colspan=1, rowspan=4)
    draw_text(3, 1, label, font_red, color='#FF0000', align='center', colspan=1, rowspan=4)
    border(3, 1, colspan=1, rowspan=4, left='medium', right='medium', top='double', bottom='double')

    for ri, room in enumerate(rooms):
        sc = ROOM_START_COLS[ri]
        last = (ri == len(rooms)-1)

        # Row 1: Room label
        fill_cell(sc, 1, '#FFFFFF', colspan=SLOTS)
        # Room label: "Room: " black + number red, centered together
        room_prefix = room['label'].split(':')[0] + ': '
        room_num = room['label'].split(': ')[1] if ': ' in room['label'] else ''
        x1,y1,x2,y2 = cell_rect(sc, 1, SLOTS, 1)
        total_w_cell = x2 - x1
        prefix_w = draw.textlength(room_prefix, font=font_bd14)
        num_w = draw.textlength(room_num, font=font_bd14)
        total_text_w = prefix_w + num_w
        tx = x1 + (total_w_cell - total_text_w) // 2
        fh = font_bd14.getbbox('A')[3]
        ty = y1 + (y2 - y1 - fh) // 2
        draw.text((tx, ty), room_prefix, fill=hex_to_rgb('#000000'), font=font_bd14)
        draw.text((tx + int(prefix_w), ty), room_num, fill=hex_to_rgb('#FF0000'), font=font_bd14)
        border(sc, 1, colspan=SLOTS, left='medium', top='double', bottom='thin',
               right='medium' if last else 'thin')

        # Row 2: Time
        fill_cell(sc, 2, '#FFFFFF', colspan=SLOTS)
        # Time row: "Time: " black + time value red
        time_parts = room['time_raw'].strip().split(': ', 1)
        time_prefix = time_parts[0] + ': ' if len(time_parts) > 1 else room['time_raw'].strip()
        time_val = time_parts[1] if len(time_parts) > 1 else ''
        x1,y1,x2,y2 = cell_rect(sc+1, 2, SLOTS-1, 1)
        pad = 5
        tx = x1 + pad
        fh = font_bd.getbbox('A')[3]
        ty = y1 + (y2 - y1 - fh) // 2
        draw.text((tx, ty), time_prefix, fill=hex_to_rgb('#000000'), font=font_bd)
        draw.text((tx + int(draw.textlength(time_prefix, font=font_bd)), ty), time_val, fill=hex_to_rgb('#FF0000'), font=font_bd)
        border(sc, 2, colspan=SLOTS, left='medium', top='thin', bottom='thin',
               right='medium' if last else 'thin')

        # Row 3: B: / S:
        half = SLOTS // 2
        fill_cell(sc, 3, '#FFFFFF', colspan=half)
        draw_text(sc+1, 3, 'B:', font_bd, colspan=half-1)
        border(sc, 3, colspan=half, left='medium', top='thin', bottom='thin')
        fill_cell(sc+half, 3, '#FFFFFF', colspan=half)
        draw_text(sc+half+1, 3, 'S:', font_bd, colspan=half-1)
        border(sc+half, 3, colspan=half, top='thin', bottom='thin',
               right='medium' if last else 'thin')

        # Row 4: Off:
        fill_cell(sc, 4, '#FFFFFF', colspan=SLOTS)
        draw_text(sc+1, 4, 'Off:', font_bd, colspan=SLOTS-1)
        border(sc, 4, colspan=SLOTS, left='medium', top='thin', bottom='double',
               right='medium' if last else 'thin')

        # Row 5: Slot numbers
        for si, slbl in enumerate(SLOT_LABELS):
            col = sc + si
            fill_cell(col, 5, '#FFFFFF')
            draw_text(col, 5, slbl, font_sm, align='center')
            border(col, 5, left='medium' if si==0 else 'thin', top='double', bottom='thin',
                   right='medium' if (last and si==SLOTS-1) else ('thin' if si==SLOTS-1 else None))

    # Col B row 5
    border(2, 5, left='thin', right='double', top='double', bottom='thin')
    # Col C row 5 (slot num area under ampm)
    border(3, 5, left='double', top='double', bottom='thin')

    # ── Draw data rows 6-23 ──────────────────────────────────────────────────
    for i in range(ROWS):
        row = 6 + i
        is_off = (i == 0)
        p = None if is_off else (sorted_people[i-1] if i-1 < len(sorted_people) else None)
        last_row = (i == ROWS-1)
        name_val = 'Off.' if is_off else (p['name'] if p else '')

        # Col B: row number
        fill_cell(2, row, '#FFFFFF')
        draw_text(2, row, str(i+1), font_md, align='right')
        border(2, row, left='thin', right='double', top='thin',
               bottom='thin' if last_row else None)

        # Col C: name
        fill_cell(3, row, '#FFFFFF')
        draw_text(3, row, name_val, font_md, align='center')
        border(3, row, left='double', right='medium', top='thin',
               bottom='thin' if last_row else None)

        # Slot cells
        for ri, room in enumerate(rooms):
            sc = ROOM_START_COLS[ri]
            last_r = (ri == len(rooms)-1)
            avail = p and covers(p['ranges'], room['time'])
            for si in range(SLOTS):
                col = sc + si
                base = SLOT_COLORS[si]
                color = base if (is_off or not p or avail) else YELLOW
                fill_cell(col, row, color)
                border(col, row,
                       left='medium' if si==0 else 'thin',
                       top='thin',
                       bottom='thin' if last_row else None,
                       right='medium' if (last_r and si==SLOTS-1) else ('thin' if si==SLOTS-1 else None))

    # ── Draw footer rows 24-30 ───────────────────────────────────────────────
    FOOTER_LABELS = ['', '', 'Narrow Side?', 'Live?', 'Wchr/Wlkr?', 'Language?', 'Other?']
    for fi, flbl in enumerate(FOOTER_LABELS):
        row = 24 + fi
        is_last_f = (fi == len(FOOTER_LABELS)-1)

        # Col C label
        fill_cell(3, row, '#FFFFFF')
        if flbl:
            draw_text(3, row, flbl, font_sm, align='center')
        border(3, row, left='double', bottom='double' if is_last_f else None)

        for ri, room in enumerate(rooms):
            sc = ROOM_START_COLS[ri]
            last_r = (ri == len(rooms)-1)

            if fi == 0:  # n24
                fill_cell(sc, row, '#FFFFFF', colspan=SLOTS)
                if room['n24']:
                    draw_text(sc, row, room['n24'], font_sm, colspan=SLOTS)
                border(sc, row, colspan=SLOTS, left='medium', top='thin',
                       right='medium' if last_r else 'thin')
            elif fi == 1:  # n25
                fill_cell(sc, row, '#FFFFFF', colspan=SLOTS)
                if room['n25']:
                    draw_text(sc, row, room['n25'], font_bd, colspan=SLOTS)
                border(sc, row, colspan=SLOTS, left='medium',
                       right='medium' if last_r else 'thin')
            else:  # box rows
                box_color = '#FF0000' if (room['red'] and fi == 2) else '#FFFFFF'
                fill_cell(sc, row, box_color)
                border(sc, row, left='medium', right='thin', top='thin', bottom='thin' if not is_last_f else 'double')

                fill_cell(sc+1, row, '#FFFFFF', colspan=SLOTS-1)
                if fi == 2 and room['letter']:
                    draw_text(sc+1, row, room['letter'], font_bd, colspan=SLOTS-1)
                elif fi == 4 and room['wlkr']:
                    draw_text(sc+1, row, room['wlkr'], font_bd, colspan=SLOTS-1)
                border(sc+1, row, colspan=SLOTS-1, left='thin',
                       right='medium' if last_r else 'thin',
                       bottom='double' if is_last_f else None)

    # ── Col A and Col B borders ───────────────────────────────────────────────
    for i in range(ROWS):
        row = 6 + i
        border(2, row, left='thin', right='double', top='thin')

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION)

@app.route('/preview', methods=['POST'])
def preview():
    data = request.json
    people = data.get('people', [])
    is_pm = data.get('is_pm', False)
    sheet = 'PM' if is_pm else 'AM'
    try:
        img_buf = render_preview(people, is_pm)
        logger.info(f"Preview generated — sheet={sheet}, people={len(people)}")
        return send_file(img_buf, mimetype='image/png')
    except Exception as e:
        logger.error(f"Preview failed — sheet={sheet}, people={len(people)}, error={e}")
        raise

@app.route('/export', methods=['POST'])
def export():
    data = request.json
    people = data.get('people', [])
    try:
        buf = build_xlsx(people)
        logger.info(f"Export generated — people={len(people)}")
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='schedule-output.xlsx')
    except Exception as e:
        logger.error(f"Export failed — people={len(people)}, error={e}")
        raise

if __name__ == '__main__':
    logger.info(f"Coordinator v{APP_VERSION} starting on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
