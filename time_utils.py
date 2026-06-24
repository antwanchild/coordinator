from constants import AM_SHEET_TIMES, PM_SHEET_TIMES


def to_minutes(time_str):
    """Convert a 'HH:MM' string to total minutes since midnight."""
    if not time_str:
        return 0
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def covers_slot(time_ranges, room_time):
    """Return True if any of the person's time ranges covers the entire 30-minute slot."""
    room_minutes = to_minutes(room_time)
    return any(
        to_minutes(time_range["start"]) <= room_minutes
        and to_minutes(time_range["end"]) >= room_minutes + 30
        for time_range in time_ranges
    )


def person_on_sheet(person, is_pm, am_sheet_times=AM_SHEET_TIMES, pm_sheet_times=PM_SHEET_TIMES):
    """Return True if the person has any availability overlapping the given sheet's time domain."""
    domain_times = pm_sheet_times if is_pm else am_sheet_times
    domain_start = to_minutes(domain_times[0])
    domain_end = to_minutes(domain_times[-1]) + 30
    return any(
        to_minutes(time_range["start"]) < domain_end
        and to_minutes(time_range["end"]) > domain_start
        for time_range in person["ranges"]
    )


def count_brothers_in_room(sorted_people, room_time):
    """Count brothers assigned to a room slot, including the Off row.

    A brother counts if they fully cover the room's 30-minute slot.
    The Off row always counts as 1.
    """
    brothers_from_people = sum(
        1 for person in sorted_people if covers_slot(person["ranges"], room_time)
    )
    return brothers_from_people + 1  # +1 for the Off row
