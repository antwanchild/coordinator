import os

TEMPLATE_PATH = "V-COORDINATE--Scheduled.xlsx"
APP_VERSION   = os.environ.get('APP_VERSION', 'dev')

# ── Layout helpers ────────────────────────────────────────────────────────────

def chars_to_pixels(char_width):
    """Convert Excel character-width units to pixels (approximate)."""
    return max(4, int(char_width * 7 + 5))

def points_to_pixels(point_height):
    """Convert Excel point height to pixels at 96 DPI."""
    return max(4, int(point_height * 96 / 72))

# ── Row / column dimensions ───────────────────────────────────────────────────

ROW_HEIGHTS_PT = {1: 17.25, 2: 15.0, 3: 15.0, 4: 15.75, 5: 20.25, 6: 20.25}
for _row in range(7, 25):
    ROW_HEIGHTS_PT[_row] = 18.0
for _row in range(25, 32):
    ROW_HEIGHTS_PT[_row] = 15.0
ROW_HEIGHTS_PT[25] = 16.5
ROW_HEIGHTS_PT[31] = 15.75

COL_PX = {}
COL_PX[1] = 10   # A: spacer
COL_PX[2] = 31   # B: row numbers
COL_PX[3] = 100  # C: names
for _col in range(4, 66):
    COL_PX[_col] = 24  # D onward: uniform slot columns

ROW_PX = {row: points_to_pixels(height) for row, height in ROW_HEIGHTS_PT.items()}

SLOTS           = 12
ROWS            = 19
ROOM_START_COLS = [4, 16, 28, 40, 52]

# ── Room definitions ──────────────────────────────────────────────────────────

AM_ROOMS = [
    {'label': 'Room: 1', 'time': '11:00', 'time_raw': ' 11:00+', 'n25': 'Skip V6 if possible',  'red': True,  'letter': 'B', 'wlkr': '(#2/#3)', 'thin': 'THIN RECEIVERS'},
    {'label': 'Room: 2', 'time': '11:30', 'time_raw': ' 11:30+', 'n25': '',                     'red': False, 'letter': '',  'wlkr': '',         'thin': ''},
    {'label': 'Room: 3', 'time': '12:00', 'time_raw': ' 12:00+', 'n25': '',                     'red': False, 'letter': '',  'wlkr': '',         'thin': ''},
    {'label': 'Room: 4', 'time': '12:30', 'time_raw': ' 12:30+', 'n25': 'Skip V3 if possible',  'red': True,  'letter': 'S', 'wlkr': '(#6/#7)', 'thin': 'THIN RECEIVERS'},
    {'label': 'Room: 1', 'time': '13:00', 'time_raw': ' 1:00+',  'n25': 'Skip V6 if possible',  'red': True,  'letter': 'B', 'wlkr': '(#2/#3)', 'thin': 'THIN RECEIVERS'},
]

PM_ROOMS = [
    {'label': 'Room: 3', 'time': '14:00', 'time_raw': ' 2:00+', 'n25': '',                     'red': False, 'letter': '',  'wlkr': '',         'thin': ''},
    {'label': 'Room: 4', 'time': '14:30', 'time_raw': ' 2:30+', 'n25': 'Skip V3 if possible',  'red': True,  'letter': 'S', 'wlkr': '(#6/#7)', 'thin': 'THIN RECEIVERS'},
    {'label': 'Room: 1', 'time': '15:00', 'time_raw': ' 3:00+', 'n25': 'Skip V6 if possible',  'red': True,  'letter': 'B', 'wlkr': '(#2/#3)', 'thin': 'THIN RECEIVERS'},
    {'label': 'Room: 2', 'time': '15:30', 'time_raw': ' 3:30+', 'n25': '',                     'red': False, 'letter': '',  'wlkr': '',         'thin': ''},
    {'label': 'Room: 3', 'time': '16:00', 'time_raw': ' 4:00+', 'n25': '',                     'red': False, 'letter': '',  'wlkr': '',         'thin': ''},
]

# ── Slot styling ──────────────────────────────────────────────────────────────

SLOT_COLORS = [
    '#D9E2F3', '#FFFFFF', '#FFF2CC', '#E2EEDA',
    '#D9E2F3', '#D9E2F3',
    '#FFFFFF', '#FFFFFF',
    '#FFF2CC', '#FFF2CC',
    '#E2EEDA', '#E2EEDA',
]
SLOT_LABELS       = ['1', '2', '3', '4', '5P', '5', '6P', '6', '7P', '7', '8P', '8']
UNAVAILABLE_COLOR = '#EDEDED'
