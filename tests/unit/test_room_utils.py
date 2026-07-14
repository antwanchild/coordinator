import unittest

from room_utils import get_room_header_state


class RoomUtilsTests(unittest.TestCase):
    def test_get_room_header_state_returns_shared_header_values(self):
        sorted_people = [
            {"name": "Alex", "ranges": [{"start": "11:00", "end": "11:30"}]},
            {"name": "Blake", "ranges": [{"start": "11:00", "end": "11:30"}]},
        ]
        room = {"time": "11:00"}
        room_data = {"11:00": {"off": "Taylor", "b": "4", "s": "4"}}

        rd, b_val, s_val, bv, sv = get_room_header_state(sorted_people, room, room_data)

        self.assertEqual(rd["off"], "Taylor")
        self.assertEqual(b_val, "4")
        self.assertEqual(s_val, "4")
        self.assertEqual((bv, sv), (1, 1))

    def test_get_room_header_state_handles_missing_values(self):
        sorted_people = [{"name": "Alex", "ranges": [{"start": "11:00", "end": "11:30"}]}]
        room = {"time": "11:30"}

        rd, b_val, s_val, bv, sv = get_room_header_state(sorted_people, room, {})

        self.assertEqual(rd, {})
        self.assertEqual(b_val, "")
        self.assertEqual(s_val, "")
        self.assertEqual((bv, sv), (None, None))


if __name__ == "__main__":
    unittest.main()
