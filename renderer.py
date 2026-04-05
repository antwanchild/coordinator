import io

from PIL import Image, ImageDraw, ImageFont

from constants import (
    AM_ROOMS, PM_ROOMS,
    COL_PX, ROW_PX,
    SLOTS, ROWS, ROOM_START_COLS,
    SLOT_COLORS, SLOT_LABELS, UNAVAILABLE_COLOR,
    chars_to_pixels, points_to_pixels,
)
from schedule import covers_slot, person_on_sheet, count_brothers_in_room, recommend_veils

# ── Colour helper ─────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color):
    """Convert a hex color string like '#RRGGBB' to an (R, G, B) tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

# ── Preview renderer ──────────────────────────────────────────────────────────

def render_preview(people, is_pm, room_data=None):
    """Render the schedule as a PNG image and return a BytesIO buffer."""
    if room_data is None:
        room_data = {}
    rooms          = PM_ROOMS if is_pm else AM_ROOMS
    visible_people = [person for person in people if person_on_sheet(person, is_pm)]
    sorted_people  = sorted(visible_people, key=lambda person: person['name'])

    # Build cumulative x positions for each column
    x_positions = {}
    x = 0
    for col in range(1, 66):
        x_positions[col] = x
        x += COL_PX.get(col, chars_to_pixels(13.0))
    total_width = x

    # Build cumulative y positions for each row
    y_positions = {}
    y = 0
    for row in range(1, 33):
        y_positions[row] = y
        y += ROW_PX.get(row, points_to_pixels(15.0))
    total_height = y

    image = Image.new('RGB', (total_width, total_height), 'white')
    draw  = ImageDraw.Draw(image)

    # Load fonts — fall back to default if DejaVu is not available
    try:
        font_small  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
        font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        font_bold   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 11)
        font_bold14 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
        font_bold18 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except Exception:
        font_small = font_medium = font_bold = font_bold14 = font_bold18 = ImageFont.load_default()

    # ── Drawing helpers ───────────────────────────────────────────────────────

    def cell_rect(col, row, colspan=1, rowspan=1):
        """Return the (x1, y1, x2, y2) pixel bounds of a cell or merged range."""
        x1 = x_positions[col]
        y1 = y_positions[row]
        x2 = x_positions[col + colspan] if (col + colspan) in x_positions else total_width
        y2 = y_positions[row + rowspan] if (row + rowspan) in y_positions else total_height
        return x1, y1, x2, y2

    def fill_cell(col, row, color, colspan=1, rowspan=1):
        """Fill a cell or merged range with a solid color."""
        x1, y1, x2, y2 = cell_rect(col, row, colspan, rowspan)
        draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill=hex_to_rgb(color))

    def draw_text(col, row, text, font, color='#000000', align='left', colspan=1, rowspan=1):
        """Draw text inside a cell, truncating if it overflows."""
        x1, y1, x2, y2 = cell_rect(col, row, colspan, rowspan)
        rgb     = hex_to_rgb(color)
        padding = 3

        while text and draw.textlength(text, font=font) > (x2 - x1 - padding * 2):
            text = text[:-1]

        text_width  = draw.textlength(text, font=font)
        cell_height = y2 - y1

        if align == 'center':
            tx = x1 + (x2 - x1 - text_width) // 2
        elif align == 'right':
            tx = x2 - text_width - padding
        else:
            tx = x1 + padding

        font_height = (font.getbbox(text)[3] - font.getbbox(text)[1]) if text else 10
        ty = y1 + (cell_height - font_height) // 2
        draw.text((tx, ty), text, fill=rgb, font=font)

    def draw_border(col, row, colspan=1, rowspan=1, left=None, right=None, top=None, bottom=None):
        """Draw borders on one or more sides of a cell range."""
        x1, y1, x2, y2 = cell_rect(col, row, colspan, rowspan)
        x2 -= 1
        y2 -= 1

        def border_style(style):
            if style in ('double', 'medium'):
                return hex_to_rgb('#595959'), 2
            if style == 'thin':
                return hex_to_rgb('#aaaaaa'), 1
            return None

        if left:
            color, width = border_style(left)
            draw.line([(x1, y1), (x1, y2)], fill=color, width=width)
        if right:
            color, width = border_style(right)
            draw.line([(x2, y1), (x2, y2)], fill=color, width=width)
        if top:
            color, width = border_style(top)
            draw.line([(x1, y1), (x2, y1)], fill=color, width=width)
        if bottom:
            color, width = border_style(bottom)
            draw.line([(x1, y2), (x2, y2)], fill=color, width=width)

    # ── Header rows 1–5 ───────────────────────────────────────────────────────

    sheet_label = 'P.M.' if is_pm else 'A.M.'
    fill_cell(3, 1, '#FFFFFF', colspan=1, rowspan=4)
    draw_text(3, 1, sheet_label, font_bold18, '#FF0000', 'center', 1, 4)
    draw_border(3, 1, colspan=1, rowspan=4, left='medium', right='medium', top='double', bottom='double')

    for room_index, room in enumerate(rooms):
        start_col    = ROOM_START_COLS[room_index]
        is_last_room = (room_index == len(rooms) - 1)

        # Row 1: "Room:" right-aligned in left 7 cols, number left-aligned red in right 5 cols
        fill_cell(start_col, 1, '#FFFFFF', colspan=SLOTS)
        room_number  = room['label'].split(': ')[1] if ': ' in room['label'] else ''
        x1l, y1l, x2l, y2l = cell_rect(start_col, 1, 7, 1)
        x1r, y1r, x2r, y2r = cell_rect(start_col + 7, 1, 5, 1)
        ty = y1l + (y2l - y1l - font_bold14.getbbox('A')[3]) // 2
        room_label_w = draw.textlength('Room:', font=font_bold14)
        draw.text((x2l - room_label_w - 3, ty), 'Room:', fill=hex_to_rgb('#000000'), font=font_bold14)
        draw.text((x1r + 3, ty), room_number, fill=hex_to_rgb('#FF0000'), font=font_bold14)
        draw_border(start_col, 1, colspan=SLOTS, left='medium', top='double', bottom='thin',
                    right='medium' if is_last_room else 'thin')

        # Row 2: "Time:" centered in relative cols 1-3, time value left in relative cols 4-7
        fill_cell(start_col, 2, '#FFFFFF', colspan=SLOTS)
        x1l, y1l, x2l, y2l = cell_rect(start_col + 1, 2, 3, 1)
        x1r, y1r, x2r, y2r = cell_rect(start_col + 4, 2, 4, 1)
        ty = y1l + (y2l - y1l - font_bold.getbbox('A')[3]) // 2
        draw.text((x1l + (x2l - x1l - draw.textlength('Time:', font=font_bold)) // 2, ty),
                  'Time:', fill=hex_to_rgb('#000000'), font=font_bold)
        draw.text((x1r + 3, ty), room['time_raw'], fill=hex_to_rgb('#FF0000'), font=font_bold)
        draw_border(start_col, 2, colspan=SLOTS, left='medium', top='thin', bottom='thin',
                    right='medium' if is_last_room else 'thin')

        # Row 3: B: cols 0-1, count cols 2-3, rec cols 4-5, S: cols 6-7, count cols 8-9, rec cols 10-11
        rd      = room_data.get(room['time'], {})
        b_val   = rd.get('b', '')
        s_val   = rd.get('s', '')
        workers = count_brothers_in_room(sorted_people, room['time'])
        fill_cell(start_col, 3, '#FFFFFF', colspan=SLOTS)
        draw_text(start_col, 3, 'B:', font_bold, '#000000', 'right', 2)
        draw_text(start_col + 6, 3, 'S:', font_bold, '#000000', 'right', 2)
        if b_val or s_val:
            bv, sv = recommend_veils(b_val, s_val, workers)
            if b_val:
                draw_text(start_col + 2, 3, str(b_val), font_bold, '#000000', 'center', 2)
            if s_val:
                draw_text(start_col + 8, 3, str(s_val), font_bold, '#000000', 'center', 2)
            if bv is not None:
                draw_text(start_col + 4, 3, f"{bv}B", font_bold, '#000000', 'center', 2)
            if sv is not None:
                draw_text(start_col + 10, 3, f"{sv}S", font_bold, '#000000', 'center', 2)
        draw_border(start_col, 3, colspan=SLOTS, left='medium', top='thin', bottom='thin',
                    right='medium' if is_last_room else 'thin')

        # Row 4: "Off:" centered in cols 0-2, officiator name blue in cols 3-11
        rd = room_data.get(room['time'], {})
        fill_cell(start_col, 4, '#FFFFFF', colspan=3)
        draw_text(start_col, 4, 'Off:', font_bold, '#000000', 'center', 3)
        draw_border(start_col, 4, colspan=3, left='medium', top='thin', bottom='double')
        fill_cell(start_col + 3, 4, '#FFFFFF', colspan=9)
        if not is_pm and room_index == 0:
            draw_text(start_col + 3, 4, 'AM Shift', font_bold, '#335593', 'left', 9)
        elif rd.get('off'):
            draw_text(start_col + 3, 4, rd['off'], font_bold, '#335593', 'left', 9)
        draw_border(start_col + 3, 4, colspan=9, top='thin', bottom='double',
                    right='medium' if is_last_room else 'thin')

        # Row 5: Slot number labels
        for slot_index, slot_label in enumerate(SLOT_LABELS):
            col          = start_col + slot_index
            is_last_slot = (slot_index == SLOTS - 1)
            fill_cell(col, 5, '#FFFFFF')
            draw_text(col, 5, slot_label, font_small, '#000000', 'center')
            draw_border(col, 5,
                        left='medium' if slot_index == 0 else 'thin',
                        top='double',
                        bottom='thin',
                        right='medium' if (is_last_room and is_last_slot) else ('thin' if is_last_slot else None))

    draw_border(2, 5, left='thin', right='double', top='double', bottom='thin')
    draw_border(3, 5, left='double', top='double', bottom='thin')

    # ── Data rows 6–24 ────────────────────────────────────────────────────────

    for row_index in range(ROWS):
        sheet_row   = 6 + row_index
        is_off_row  = (row_index == 0)
        is_last_row = (row_index == ROWS - 1)
        person      = None if is_off_row else (sorted_people[row_index - 1] if row_index - 1 < len(sorted_people) else None)
        name_value  = 'Off.' if is_off_row else (person['name'] if person else '')

        fill_cell(2, sheet_row, '#FFFFFF')
        draw_text(2, sheet_row, str(row_index + 1), font_medium, '#000000', 'right')
        draw_border(2, sheet_row, left='thin', right='double', top='thin',
                    bottom='thin' if is_last_row else None)

        fill_cell(3, sheet_row, '#FFFFFF')
        draw_text(3, sheet_row, name_value, font_medium, '#000000', 'center')
        draw_border(3, sheet_row, left='double', right='medium', top='thin',
                    bottom='thin' if is_last_row else None)

        for room_index, room in enumerate(rooms):
            start_col    = ROOM_START_COLS[room_index]
            is_last_room = (room_index == len(rooms) - 1)
            is_available = person and covers_slot(person['ranges'], room['time'])

            for slot_index in range(SLOTS):
                col          = start_col + slot_index
                is_last_slot = (slot_index == SLOTS - 1)
                slot_color   = SLOT_COLORS[slot_index] if (is_off_row or not person or is_available) else UNAVAILABLE_COLOR
                fill_cell(col, sheet_row, slot_color)
                draw_border(col, sheet_row,
                            left='medium' if slot_index == 0 else 'thin',
                            top='thin',
                            bottom='thin' if is_last_row else None,
                            right='medium' if (is_last_room and is_last_slot) else ('thin' if is_last_slot else None))

    for row_index in range(ROWS):
        draw_border(2, 6 + row_index, left='thin', right='double', top='thin')

    # ── Footer rows 25–31 ─────────────────────────────────────────────────────

    FOOTER_LABELS = [
        'Low voice, Gentle,\nReverence, 5 Min',
        "Bros Available?",
        'Narrow Side?',
        'Live?',
        'Wchr/Wlkr?',
        'Language?',
        'Other?',
    ]

    for footer_index, footer_label in enumerate(FOOTER_LABELS):
        sheet_row      = 25 + footer_index
        is_last_footer = (footer_index == len(FOOTER_LABELS) - 1)

        fill_cell(3, sheet_row, '#FFFFFF')
        if footer_index == 0:
            x1, y1, x2, y2 = cell_rect(3, sheet_row)
            lines  = footer_label.split('\n')
            line_h = font_small.getbbox('A')[3] - font_small.getbbox('A')[1]
            total_h = line_h * len(lines) + 2 * (len(lines) - 1)
            ty = y1 + (y2 - y1 - total_h) // 2
            for line in lines:
                lw = draw.textlength(line, font=font_small)
                draw.text((x1 + (x2 - x1 - lw) // 2, ty), line, fill=hex_to_rgb('#FF0000'), font=font_small)
                ty += line_h + 2
        elif footer_label:
            draw_text(3, sheet_row, footer_label, font_small, '#000000', 'center')
        draw_border(3, sheet_row, left='double', bottom='double' if is_last_footer else None)

        for room_index, room in enumerate(rooms):
            start_col    = ROOM_START_COLS[room_index]
            is_last_room = (room_index == len(rooms) - 1)
            right_border = 'medium' if is_last_room else None

            if footer_index == 0:
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=SLOTS)
                if room['n25']:
                    draw_text(start_col, sheet_row, room['n25'], font_medium, '#000000', 'center', SLOTS)
                top = 'thin' if room_index == 0 else None
                draw_border(start_col, sheet_row, colspan=SLOTS, left='medium', top=top,
                            right=right_border)

            elif footer_index == 1:
                room_count = count_brothers_in_room(sorted_people, room['time'])
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=2)
                draw_text(start_col, sheet_row, str(room_count), font_bold, '#000000', 'center', 2)
                draw_border(start_col, sheet_row, left='medium', top='thin', bottom='thin')
                draw_border(start_col + 1, sheet_row, right='thin', top='thin', bottom='thin')
                fill_cell(start_col + 2, sheet_row, '#FFFFFF', colspan=SLOTS - 2)
                draw_border(start_col + SLOTS - 1, sheet_row, right=right_border)

            elif footer_index == 2:
                checkbox_color = '#FF0000' if room['red'] else '#FFFFFF'
                fill_cell(start_col, sheet_row, checkbox_color)
                draw_border(start_col, sheet_row, left='medium', right='thin', top='thin', bottom='thin')
                fill_cell(start_col + 1, sheet_row, '#FFFFFF')
                if room['letter']:
                    draw_text(start_col + 1, sheet_row, room['letter'], font_bold)
                draw_border(start_col + 1, sheet_row, left='thin', top='thin')
                fill_cell(start_col + 2, sheet_row, '#FFFFFF', colspan=SLOTS - 2)
                if room['thin']:
                    draw_text(start_col + 3, sheet_row, room['thin'], font_medium, '#FF0000', 'left', 8)
                draw_border(start_col + SLOTS - 1, sheet_row, right=right_border)

            elif footer_index == 3:
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=SLOTS)
                draw_border(start_col, sheet_row, left='medium', right='thin')
                draw_border(start_col + 1, sheet_row, left='thin')
                draw_border(start_col + SLOTS - 1, sheet_row, right=right_border)

            elif footer_index == 4:
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=SLOTS)
                draw_border(start_col, sheet_row, left='medium', right='thin', top='thin', bottom='thin')
                if room['wlkr']:
                    draw_text(start_col + 1, sheet_row, room['wlkr'], font_bold, '#000000', 'left', SLOTS - 1)
                draw_border(start_col + 1, sheet_row, left='thin')
                draw_border(start_col + SLOTS - 1, sheet_row, right=right_border)

            elif footer_index == 5:
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=SLOTS)
                draw_border(start_col, sheet_row, left='medium', right='thin', top='thin', bottom='thin')
                draw_border(start_col + 1, sheet_row, left='thin')
                draw_border(start_col + SLOTS - 1, sheet_row, right=right_border)

            else:
                fill_cell(start_col, sheet_row, '#FFFFFF', colspan=SLOTS)
                draw_border(start_col, sheet_row, left='medium', right='thin', bottom='double')
                draw_border(start_col + 1, sheet_row, left='thin', bottom='double')
                for slot_index in range(2, SLOTS):
                    draw_border(start_col + slot_index, sheet_row, bottom='double')
                draw_border(start_col + SLOTS - 1, sheet_row,
                            right='double' if is_last_room else 'medium',
                            bottom='double')

    image_buffer = io.BytesIO()
    image.save(image_buffer, format='PNG', optimize=True)
    image_buffer.seek(0)
    return image_buffer
