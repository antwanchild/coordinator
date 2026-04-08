import os

TEMPLATE_PATH = "V-COORDINATE--Scheduled.xlsx"
APP_VERSION   = os.environ.get('APP_VERSION', 'dev')
AM_SHEET_TIMES = ['11:00', '11:30', '12:00', '12:30', '13:00']
PM_SHEET_TIMES = ['14:00', '14:30', '15:00', '15:30', '16:00']
ALLOWED_INPUT_TIMES = [
    '11:00', '11:15', '11:30', '11:45',
    '12:00', '12:15', '12:30', '12:45',
    '13:00', '13:15', '13:30', '13:45',
    '14:00', '14:15', '14:30', '14:45',
    '15:00', '15:15', '15:30', '15:45',
    '16:00', '16:15', '16:30', '16:45',
]
ALL_TIMES      = ALLOWED_INPUT_TIMES

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
    {'label': 'Room: 1', 'time': '11:00', 'time_raw': ' 11:00+', 'footer_note': 'Skip V6 if possible',  'highlight_narrow_side': True,  'narrow_side_marker': 'B', 'wheelchair_walker_note': '(#2/#3)', 'thin_receivers_note': 'THIN RECEIVERS'},
    {'label': 'Room: 2', 'time': '11:30', 'time_raw': ' 11:30+', 'footer_note': '',                     'highlight_narrow_side': False, 'narrow_side_marker': '',  'wheelchair_walker_note': '',         'thin_receivers_note': ''},
    {'label': 'Room: 3', 'time': '12:00', 'time_raw': ' 12:00+', 'footer_note': '',                     'highlight_narrow_side': False, 'narrow_side_marker': '',  'wheelchair_walker_note': '',         'thin_receivers_note': ''},
    {'label': 'Room: 4', 'time': '12:30', 'time_raw': ' 12:30+', 'footer_note': 'Skip V3 if possible',  'highlight_narrow_side': True,  'narrow_side_marker': 'S', 'wheelchair_walker_note': '(#6/#7)', 'thin_receivers_note': 'THIN RECEIVERS'},
    {'label': 'Room: 1', 'time': '13:00', 'time_raw': ' 1:00+',  'footer_note': 'Skip V6 if possible',  'highlight_narrow_side': True,  'narrow_side_marker': 'B', 'wheelchair_walker_note': '(#2/#3)', 'thin_receivers_note': 'THIN RECEIVERS'},
]

PM_ROOMS = [
    {'label': 'Room: 3', 'time': '14:00', 'time_raw': ' 2:00+', 'footer_note': '',                     'highlight_narrow_side': False, 'narrow_side_marker': '',  'wheelchair_walker_note': '',         'thin_receivers_note': ''},
    {'label': 'Room: 4', 'time': '14:30', 'time_raw': ' 2:30+', 'footer_note': 'Skip V3 if possible',  'highlight_narrow_side': True,  'narrow_side_marker': 'S', 'wheelchair_walker_note': '(#6/#7)', 'thin_receivers_note': 'THIN RECEIVERS'},
    {'label': 'Room: 1', 'time': '15:00', 'time_raw': ' 3:00+', 'footer_note': 'Skip V6 if possible',  'highlight_narrow_side': True,  'narrow_side_marker': 'B', 'wheelchair_walker_note': '(#2/#3)', 'thin_receivers_note': 'THIN RECEIVERS'},
    {'label': 'Room: 2', 'time': '15:30', 'time_raw': ' 3:30+', 'footer_note': '',                     'highlight_narrow_side': False, 'narrow_side_marker': '',  'wheelchair_walker_note': '',         'thin_receivers_note': ''},
    {'label': 'Room: 3', 'time': '16:00', 'time_raw': ' 4:00+', 'footer_note': '',                     'highlight_narrow_side': False, 'narrow_side_marker': '',  'wheelchair_walker_note': '',         'thin_receivers_note': ''},
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
