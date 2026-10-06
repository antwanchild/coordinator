import unittest
from typing import TypedDict, cast

import validation


class TimeRange(TypedDict):
    start: str
    end: str


class ValidatedPerson(TypedDict):
    name: str
    ranges: list[TimeRange]


class NormalizedRoomData(TypedDict):
    off: str
    b: str
    s: str


class ValidationTests(unittest.TestCase):
    def test_validate_people_normalizes_values(self):
        people, error = validation.validate_people(
            [
                {"name": "  Alex  ", "ranges": [{"start": "11:00", "end": "11:30"}]},
            ]
        )

        self.assertIsNone(error)
        self.assertIsNotNone(people)
        validated_people = cast(list[ValidatedPerson], people)
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
        validated_room_data = cast(dict[str, NormalizedRoomData], room_data)
        room = validated_room_data["11:00"]
        self.assertEqual(room["off"], "Officer A")
        self.assertEqual(room["b"], "2")
        self.assertEqual(room["s"], "1")

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
        room = cast(NormalizedRoomData, payload["room_data"]["11:00"])
        self.assertEqual(room["off"], "Officer A")
        self.assertEqual(room["b"], "2")
        self.assertEqual(room["s"], "1")
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


if __name__ == "__main__":
    unittest.main()
