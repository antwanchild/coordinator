import unittest

from constants import chars_to_pixels, points_to_pixels


class ConstantsTests(unittest.TestCase):
    def test_chars_to_pixels_scales_reasonably(self):
        self.assertEqual(chars_to_pixels(0), 5)
        self.assertEqual(chars_to_pixels(1), 12)
        self.assertEqual(chars_to_pixels(10), 75)

    def test_points_to_pixels_scales_reasonably(self):
        self.assertEqual(points_to_pixels(0), 4)
        self.assertEqual(points_to_pixels(15), 20)
        self.assertEqual(points_to_pixels(18), 24)


if __name__ == "__main__":
    unittest.main()
