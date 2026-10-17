import unittest
from typing import cast

import validation


class ValidationTests(unittest.TestCase):
    def test_validate_people_normalizes_values(self):
        people, error = validation.validate_people(
            [
                {"name": "  Alex  ", "ranges": [{"start": "11:00", "end": "11:30"}]},
            ]
        )

        self.assertIsNone(error)
        self.assertIsNotNone(people)
        validated_people = cast(list[validation.Person], people)
        self.assertEqual(validated_people[0]["name"], "Alex")
        self.assertEqual(validated_people[0]["ranges"][0]["start"], "11:00")
        self.assertEqual(validated_people[0]["ranges"][0]["end"], "11:30")

    def test_validate_people_rejects_non_list(self):
        _, error = validation.validate_people("not-a-list")
        self.assertEqual(error, "people must be a list")

    def test_validate_people_rejects_reversed_range(self):
        _, error = validation.validate_people(
            [
                {"name": "Alex", "ranges": [{"start": "11:30", "end": "11:15"}]},
            ]
        )
        self.assertEqual(error, "people[0].ranges[0] end must be after start")

    def test_validate_room_data_normalizes_values(self):
        room_data, error = validation.validate_room_data(
            {
                "11:00": {"off": "  Officer A  ", "b": 2, "s": "1"},
            }
        )

        self.assertIsNone(error)
        self.assertIsNotNone(room_data)
        validated_room_data = cast(dict[str, validation.RoomData], room_data)
        room = validated_room_data["11:00"]
        self.assertEqual(room, {"off": "Officer A", "b": "2", "s": "1"})

    def test_validate_room_data_rejects_unsupported_time(self):
        _, error = validation.validate_room_data({"10:00": {"off": "Officer A"}})
        self.assertEqual(error, 'room_data contains unsupported time "10:00"')

    def test_validate_room_data_rejects_non_string_officer(self):
        _, error = validation.validate_room_data({"11:00": {"off": 123}})
        self.assertEqual(error, 'room_data["11:00"].off must be a string')

    def test_validate_request_payload_normalizes_values(self):
        payload, error = validation.validate_request_payload(
            {
                "people": [{"name": "  Alex  ", "ranges": [{"start": "11:00", "end": "11:30"}]}],
                "room_data": {"11:00": {"off": "  Officer A  ", "b": 2, "s": "1"}},
                "is_pm": True,
            },
            require_is_pm=True,
        )

        self.assertIsNone(error)
        self.assertIsNotNone(payload)
        payload = cast(validation.RequestPayload, payload)
        self.assertEqual(payload["people"][0]["name"], "Alex")
        room = cast(validation.RoomData, payload["room_data"]["11:00"])
        self.assertEqual(room, {"off": "Officer A", "b": "2", "s": "1"})
        self.assertTrue(payload["is_pm"])

    def test_validate_request_payload_rejects_non_boolean_is_pm(self):
        _, error = validation.validate_request_payload(
            {
                "people": [],
                "room_data": {},
                "is_pm": "yes",
            },
            require_is_pm=True,
        )
        self.assertEqual(error, "is_pm must be a boolean")

    def test_validate_request_payload_rejects_non_quarter_hour_range(self):
        _, error = validation.validate_request_payload(
            {
                "people": [{"name": "Alex", "ranges": [{"start": "11:00", "end": "11:10"}]}],
                "room_data": {},
                "is_pm": False,
            }
        )
        self.assertEqual(
            error, "people[0].ranges[0] must use 15-minute times between 11:00 and 16:45"
        )

    def test_rejects_malformed_people_and_ranges(self):
        for person, expected in [
            (None, "people[0] must be an object"),
            ({"name": " ", "ranges": []}, "people[0].name must be a non-empty string"),
            ({"name": "Alex", "ranges": []}, "people[0].ranges must be a non-empty list"),
            ({"name": "Alex", "ranges": "invalid"}, "people[0].ranges must be a non-empty list"),
            ({"name": "Alex", "ranges": [None]}, "people[0].ranges[0] must be an object"),
        ]:
            with self.subTest(person=person):
                people, error = validation.validate_people([person])
                self.assertIsNone(people)
                self.assertEqual(error, expected)
        for start, end in [
            (None, "11:30"),
            ("11:00", 12),
            ("10:45", "11:30"),
            ("11:00", "17:00"),
            ("11:00", "11:00"),
        ]:
            with self.subTest(start=start, end=end):
                people, error = validation.validate_people(
                    [{"name": "Alex", "ranges": [{"start": start, "end": end}]}]
                )
                self.assertIsNone(people)
                self.assertIsNotNone(error)

    def test_room_counts_reject_invalid_values(self):
        for field in ("b", "s"):
            for value in (True, False, -1, "-1", 1.5, "1.5", "abc", [], {}):
                with self.subTest(field=field, value=value):
                    rooms, error = validation.validate_room_data({"11:00": {field: value}})
                    self.assertIsNone(rooms)
                    self.assertEqual(
                        error, f'room_data["11:00"].{field} must be a non-negative integer or empty'
                    )

    def test_room_counts_normalize_zero_empty_and_leading_zeros(self):
        for value, expected in [(0, "0"), ("0002", "2"), (None, ""), ("", "")]:
            with self.subTest(value=value):
                rooms, error = validation.validate_room_data(
                    {"11:00": {"off": None, "b": value, "s": value}}
                )
                self.assertIsNone(error)
                self.assertEqual(rooms, {"11:00": {"off": "", "b": expected, "s": expected}})

    def test_room_data_requires_objects(self):
        self.assertEqual(validation.validate_room_data(None), ({}, None))
        self.assertEqual(validation.validate_room_data([]), (None, "room_data must be an object"))
        self.assertEqual(
            validation.validate_room_data({"11:00": None}),
            (None, 'room_data["11:00"] must be an object'),
        )


if __name__ == "__main__":
    unittest.main()
