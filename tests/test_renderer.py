import io
import unittest

from PIL import Image

from renderer import render_preview


class RendererTests(unittest.TestCase):
    def test_render_preview_returns_png_buffer(self):
        buffer = render_preview(
            [{'name': 'Alex', 'ranges': [{'start': '11:00', 'end': '11:30'}]}],
            is_pm=False,
            room_data={},
        )

        self.assertIsInstance(buffer, io.BytesIO)
        image = Image.open(buffer)
        self.assertEqual(image.format, 'PNG')
        self.assertGreater(image.width, 0)
        self.assertGreater(image.height, 0)

    def test_render_preview_uses_consistent_dimensions_for_both_sheets(self):
        am_buffer = render_preview(
            [{'name': 'Alex', 'ranges': [{'start': '11:00', 'end': '11:30'}]}],
            is_pm=False,
            room_data={},
        )
        pm_buffer = render_preview(
            [{'name': 'Alex', 'ranges': [{'start': '14:00', 'end': '14:30'}]}],
            is_pm=True,
            room_data={},
        )

        am_image = Image.open(am_buffer)
        pm_image = Image.open(pm_buffer)
        self.assertEqual(am_image.size, pm_image.size)


if __name__ == '__main__':
    unittest.main()
