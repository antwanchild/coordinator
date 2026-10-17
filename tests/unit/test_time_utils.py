import unittest

from time_utils import covers_slot, person_on_sheet, count_brothers_in_room, to_minutes
from tests.helpers import make_person


class TimeUtilsTests(unittest.TestCase):
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

    def test_sheet_boundaries_and_multiple_ranges(self):
        for start, end, am, pm in [
            ("13:30", "14:00", False, False),
            ("13:15", "14:15", True, True),
            ("16:30", "16:45", False, False),
        ]:
            with self.subTest(start=start, end=end):
                person = make_person("Alex", [{"start": start, "end": end}])
                self.assertEqual(person_on_sheet(person, False), am)
                self.assertEqual(person_on_sheet(person, True), pm)
        self.assertTrue(
            covers_slot(
                [
                    {"start": "11:00", "end": "11:15"},
                    {"start": "14:00", "end": "14:30"},
                ],
                "14:00",
            )
        )
        self.assertFalse(covers_slot([], "11:00"))
        self.assertEqual(count_brothers_in_room([], "11:00"), 1)

    def test_to_minutes(self):
        self.assertEqual(to_minutes("14:15"), 855)
        self.assertEqual(to_minutes(""), 0)
