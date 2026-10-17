import unittest

from schedule import recommend_veils


class ScheduleLogicTests(unittest.TestCase):
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
