import re
from typing import TypedDict

from constants import AM_ROOMS, PM_ROOMS, ALL_TIMES
from time_utils import to_minutes

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
ROOM_TIME_SET = {room["time"] for room in AM_ROOMS + PM_ROOMS}


class TimeRange(TypedDict):
    start: str
    end: str


class Person(TypedDict):
    name: str
    ranges: list[TimeRange]


class RoomData(TypedDict, total=False):
    off: str
    b: str
    s: str


class RequestPayload(TypedDict):
    people: list[Person]
    room_data: dict[str, RoomData]
    is_pm: bool


def is_valid_time_value(value: object) -> bool:
    if not isinstance(value, str) or not TIME_PATTERN.match(value):
        return False
    return value in ALL_TIMES


def validate_people(people: object) -> tuple[list[Person] | None, str | None]:
    if not isinstance(people, list):
        return None, "people must be a list"

    validated_people: list[Person] = []
    for index, person in enumerate(people):
        if not isinstance(person, dict):
            return None, f"people[{index}] must be an object"

        name = person.get("name")
        ranges = person.get("ranges")
        if not isinstance(name, str) or not name.strip():
            return None, f"people[{index}].name must be a non-empty string"
        if not isinstance(ranges, list) or not ranges:
            return None, f"people[{index}].ranges must be a non-empty list"

        validated_ranges: list[TimeRange] = []
        for range_index, time_range in enumerate(ranges):
            if not isinstance(time_range, dict):
                return None, f"people[{index}].ranges[{range_index}] must be an object"

            start = time_range.get("start")
            end = time_range.get("end")
            if not isinstance(start, str) or not isinstance(end, str):
                return (
                    None,
                    f"people[{index}].ranges[{range_index}] must use 15-minute times between 11:00 and 16:45",
                )
            if not is_valid_time_value(start) or not is_valid_time_value(end):
                return (
                    None,
                    f"people[{index}].ranges[{range_index}] must use 15-minute times between 11:00 and 16:45",
                )
            if to_minutes(start) >= to_minutes(end):
                return None, f"people[{index}].ranges[{range_index}] end must be after start"

            validated_ranges.append({"start": start, "end": end})

        validated_people.append({"name": name.strip(), "ranges": validated_ranges})

    return validated_people, None


def validate_room_data(room_data: object) -> tuple[dict[str, RoomData] | None, str | None]:
    if room_data is None:
        return {}, None
    if not isinstance(room_data, dict):
        return None, "room_data must be an object"

    validated_room_data: dict[str, RoomData] = {}
    for room_time, raw_room in room_data.items():
        if room_time not in ROOM_TIME_SET:
            return None, f'room_data contains unsupported time "{room_time}"'
        if not isinstance(raw_room, dict):
            return None, f'room_data["{room_time}"] must be an object'

        off = raw_room.get("off", "")
        b_value = raw_room.get("b", "")
        s_value = raw_room.get("s", "")

        if off is None:
            off = ""
        if not isinstance(off, str):
            return None, f'room_data["{room_time}"].off must be a string'

        for field_name, field_value in (("b", b_value), ("s", s_value)):
            if field_value in ("", None):
                continue
            if isinstance(field_value, bool) or not isinstance(field_value, (int, str)):
                return (
                    None,
                    f'room_data["{room_time}"].{field_name} must be a non-negative integer or empty',
                )
            if not str(field_value).isdigit():
                return (
                    None,
                    f'room_data["{room_time}"].{field_name} must be a non-negative integer or empty',
                )

        validated_room_data[room_time] = {
            "off": off.strip(),
            "b": "" if b_value in ("", None) else str(int(str(b_value))),
            "s": "" if s_value in ("", None) else str(int(str(s_value))),
        }

    return validated_room_data, None


def validate_request_payload(
    data: object, require_is_pm: bool = False
) -> tuple[RequestPayload | None, str | None]:
    if not data or not isinstance(data, dict):
        return None, "Invalid request body"

    people, people_error = validate_people(data.get("people", []))
    if people_error:
        return None, people_error

    room_data, room_data_error = validate_room_data(data.get("room_data", {}))
    if room_data_error:
        return None, room_data_error

    is_pm = data.get("is_pm", False)
    if require_is_pm:
        if not isinstance(is_pm, bool):
            return None, "is_pm must be a boolean"
    else:
        is_pm = bool(is_pm)

    assert people is not None
    assert room_data is not None
    payload: RequestPayload = {"people": people, "room_data": room_data, "is_pm": is_pm}
    return payload, None
