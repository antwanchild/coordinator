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
    _, room_counts = room_coverage_by_person(sorted_people, [room_time])
    return room_counts[0]


def room_coverage_by_person(people, room_times):
    """Return each person's room availability and room counts, including the Off row."""
    room_starts = [to_minutes(room_time) for room_time in room_times]
    availability = []
    room_counts = [1] * len(room_times)

    for person in people:
        person_availability = [False] * len(room_times)
        for time_range in person["ranges"]:
            start = to_minutes(time_range["start"])
            end = to_minutes(time_range["end"])
            for room_index, room_start in enumerate(room_starts):
                if (
                    not person_availability[room_index]
                    and start <= room_start
                    and end >= room_start + 30
                ):
                    person_availability[room_index] = True
                    room_counts[room_index] += 1
        availability.append(person_availability)

    return availability, room_counts
