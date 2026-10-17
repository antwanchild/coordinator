import io
import unittest

from PIL import Image, ImageChops
from constants import COL_PX, ROW_PX

from renderer import render_preview


class RendererTests(unittest.TestCase):
    def test_render_preview_returns_png_buffer(self):
        buffer = render_preview(
            [{"name": "Alex", "ranges": [{"start": "11:00", "end": "11:30"}]}],
            is_pm=False,
            room_data={},
        )

        self.assertIsInstance(buffer, io.BytesIO)
        image = Image.open(buffer)
        self.addCleanup(image.close)
        self.assertEqual(image.format, "PNG")
        self.assertGreater(image.width, 0)
        self.assertGreater(image.height, 0)

    def test_render_preview_uses_consistent_dimensions_for_both_sheets(self):
        am_buffer = render_preview(
            [{"name": "Alex", "ranges": [{"start": "11:00", "end": "11:30"}]}],
            is_pm=False,
            room_data={},
        )
        pm_buffer = render_preview(
            [{"name": "Alex", "ranges": [{"start": "14:00", "end": "14:30"}]}],
            is_pm=True,
            room_data={},
        )

        am_image = Image.open(am_buffer)
        self.addCleanup(am_image.close)
        pm_image = Image.open(pm_buffer)
        self.addCleanup(pm_image.close)
        self.assertEqual(am_image.size, pm_image.size)

    def test_rendered_content_and_availability_change_in_expected_regions(self):
        def region(image, col, row, colspan=1):
            x = sum(COL_PX[c] for c in range(1, col))
            y = sum(ROW_PX[r] for r in range(1, row))
            return image.crop(
                (
                    x + 3,
                    y + 3,
                    x + sum(COL_PX[c] for c in range(col, col + colspan)) - 3,
                    y + ROW_PX[row] - 3,
                )
            )

        for is_pm, start, end in [(False, "11:00", "11:30"), (True, "14:00", "14:30")]:
            with self.subTest(is_pm=is_pm):
                with (
                    Image.open(render_preview([], is_pm, {})) as empty,
                    Image.open(
                        render_preview(
                            [{"name": "Alex", "ranges": [{"start": start, "end": end}]}],
                            is_pm,
                            {
                                start: {"b": "4", "s": "2", "off": "Officer A"},
                                "11:30": {"off": "Officer A"},
                            },
                        )
                    ) as populated,
                ):
                    self.assertIsNotNone(
                        ImageChops.difference(
                            region(empty, 3, 7), region(populated, 3, 7)
                        ).getbbox(),
                        "Person name is missing",
                    )
                    self.assertEqual(region(populated, 4, 7).getpixel((2, 2)), (217, 226, 243))
                    self.assertEqual(region(populated, 16, 7).getpixel((2, 2)), (237, 237, 237))
                    for col, row, span in [
                        (6, 3, 2),
                        (12, 3, 2),
                        (7 if is_pm else 19, 4, 9),
                        (4, 26, 2),
                    ]:
                        self.assertIsNotNone(
                            ImageChops.difference(
                                region(empty, col, row, span), region(populated, col, row, span)
                            ).getbbox(),
                            f"Missing content in column {col}, row {row}",
                        )


if __name__ == "__main__":
    unittest.main()
