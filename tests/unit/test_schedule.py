import unittest
from typing import TypedDict

from schedule import count_brothers_in_room, covers_slot, person_on_sheet, recommend_veils


class TimeRange(TypedDict):
    start: str
    end: str


class Person(TypedDict):
    name: str
    ranges: list[TimeRange]


def make_person(name: str, ranges: list[TimeRange]) -> Person:
    return {"name": name, "ranges": ranges}


class ScheduleLogicTests(unittest.TestCase):
    def test_covers_slot_requires_full_coverage(self):
        self.assertTrue(covers_slot([{"start": "11:00", "end": "11:30"}], "11:00"))
        self.assertFalse(covers_slot([{"start": "11:00", "end": "11:15"}], "11:00"))
        self.assertFalse(covers_slot([{"start": "11:30", "end": "12:00"}], "11:00"))

    def test_person_on_sheet_filters_am_and_pm_ranges(self):
        person = make_person("Alex", [{"start": "11:00", "end": "11:30"}])
        self.assertTrue(person_on_sheet(person, False))
        self.assertFalse(person_on_sheet(person, True))

        person = make_person("Blake", [{"start": "14:00", "end": "14:30"}])
        self.assertFalse(person_on_sheet(person, False))
        self.assertTrue(person_on_sheet(person, True))

    def test_count_brothers_in_room_includes_off_row(self):
        people = [
            make_person("Alex", [{"start": "11:00", "end": "11:30"}]),
            make_person("Blake", [{"start": "11:30", "end": "12:00"}]),
            make_person("Casey", [{"start": "12:00", "end": "12:30"}]),
        ]
        self.assertEqual(count_brothers_in_room(people, "11:00"), 2)
        self.assertEqual(count_brothers_in_room(people, "11:30"), 2)
        self.assertEqual(count_brothers_in_room(people, "12:00"), 2)

    def test_recommend_veils_prefers_balanced_split_within_limits(self):
        self.assertEqual(recommend_veils(4, 4, 6), (2, 2))
        self.assertEqual(recommend_veils(8, 2, 6), (2, 1))
        self.assertEqual(recommend_veils(0, 0, 6), (None, None))

    def test_recommend_veils_handles_edge_cases(self):
        self.assertEqual(recommend_veils("3", "2", "5"), (2, 1))
        self.assertEqual(recommend_veils(1, 0, 1), (0, 0))
        self.assertEqual(recommend_veils(None, None, None), (None, None))


if __name__ == "__main__":
    unittest.main()
