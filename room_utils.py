from time_utils import count_brothers_in_room


def get_room_header_state(sorted_people, room, room_data):
    """Return the shared room-header values used by the workbook and PNG renderers."""
    room_time = room["time"]
    rd = room_data.get(room_time, {})
    b_val = rd.get("b", "")
    s_val = rd.get("s", "")
    workers = count_brothers_in_room(sorted_people, room_time)
    bv = sv = None

    if b_val or s_val:
        from schedule import recommend_veils

        bv, sv = recommend_veils(b_val, s_val, workers)

    return rd, b_val, s_val, bv, sv
