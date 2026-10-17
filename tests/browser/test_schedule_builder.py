import io
import os
import threading
import unittest

from werkzeug.serving import make_server

from app import app
from openpyxl import load_workbook
from tests.helpers import temporary_workbook_template

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


RUN_BROWSER_TESTS = os.environ.get("RUN_BROWSER_TESTS") == "1"


@unittest.skipUnless(
    RUN_BROWSER_TESTS,
    "Browser tests require RUN_BROWSER_TESTS=1",
)
class ScheduleBuilderBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sync_playwright is None:
            raise RuntimeError(
                "RUN_BROWSER_TESTS=1 requires Playwright; install requirements-dev.txt"
            )
        cls.template = temporary_workbook_template()
        cls.template.__enter__()
        cls.addClassCleanup(cls.template.__exit__, None, None, None)
        cls.server = make_server("127.0.0.1", 0, app)
        cls.addClassCleanup(cls.server.server_close)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.addClassCleanup(cls.server_thread.join)
        cls.addClassCleanup(cls.server.shutdown)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.page_errors: list[str] = []
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))

    def test_add_person_and_build_preview(self):
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.locator("#tab-manual").click()
        self.page.locator("#nameInput").fill("Alex")
        self.page.locator("#addNameBtn").click()

        self.assertIn("Alex", self.page.locator("#nameList").inner_text())

        self.page.locator("#buildBtn").click()
        self.page.locator("#previewArea img").wait_for(state="visible")
        self.page.wait_for_function("""() => {
                const image = document.querySelector('#previewArea img');
                return image && image.complete;
            }""")
        self.assertTrue(
            self.page.locator("#previewArea img").evaluate(
                "image => image.naturalWidth > 0 && image.naturalHeight > 0"
            ),
            "Preview image failed to load",
        )
        self.assertEqual(self.page_errors, [])

    def test_switching_sheets_uses_external_script(self):
        self.page.goto(self.base_url, wait_until="domcontentloaded")

        self.assertEqual(self.page.locator('link[href="/static/app.css"]').count(), 1)
        self.assertEqual(self.page.locator('script[src="/static/app.js"]').count(), 1)
        self.page.locator("#tab-sheet-PM").click()

        self.assertIn("PM Sheet", self.page.locator("#headerStatus").inner_text())
        self.assertTrue(
            self.page.locator("#tab-sheet-PM").evaluate(
                "element => element.classList.contains('active')"
            )
        )
        self.assertEqual(self.page_errors, [])

    def tearDown(self):
        self.assertEqual(self.page_errors, [])

    def import_people(self, text="Alex, 11:00, 11:30"):
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.locator("#pasteInput").fill(text)
        self.page.locator("#importPasteBtn").click()
        self.page.locator("#tab-manual").click()

    def test_paste_import_merges_ranges_and_reports_skipped_lines(self):
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.locator("#pasteInput").fill("Alex, 11:00, 11:30\nAlex, 14:00, 14:30\ninvalid row")
        self.page.locator("#importPasteBtn").click()
        self.assertIn("invalid row", self.page.locator("#skipped-paste").inner_text())
        self.page.locator("#tab-manual").click()
        self.assertEqual(self.page.locator(".name-entry").count(), 1)
        self.assertEqual(self.page.locator(".name-entry-range").count(), 2)
        self.assertIn("1 total · 1 AM · 1 PM", self.page.locator("#peopleCount").inner_text())
        self.page.locator("#tab-paste").click()
        self.page.locator("#pasteInput").fill("invalid row")
        self.page.locator("#importPasteBtn").click()
        self.page.locator("#confirmCancelBtn").click()
        self.page.locator("#tab-manual").click()
        self.assertEqual(self.page.locator(".name-entry-range").count(), 2)

    def test_csv_import_reports_invalid_rows(self):
        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.locator("#tab-csv").click()
        self.page.locator("#csvInput").set_input_files(
            {
                "name": "schedule.csv",
                "mimeType": "text/csv",
                "buffer": b"Name, start, end\nBlake, 14:00, 14:30\ninvalid row",
            }
        )
        self.page.locator("#skipped-csv.visible").wait_for()
        self.assertIn("invalid row", self.page.locator("#skipped-csv").inner_text())
        self.page.locator("#tab-manual").click()
        self.assertIn("Blake", self.page.locator("#nameList").inner_text())
        self.assertIn("1 total · 0 AM · 1 PM", self.page.locator("#peopleCount").inner_text())

    def test_draft_restores_people_sheet_and_room_data_after_reload(self):
        self.import_people("Blake, 14:00, 14:30\n14:00, Officer B, 2, 1")
        self.page.locator("#tab-sheet-PM").click()
        self.page.reload(wait_until="domcontentloaded")
        self.assertIn("Blake", self.page.locator("#nameList").inner_text())
        self.assertIn("PM Sheet", self.page.locator("#headerStatus").inner_text())
        with self.page.expect_request("**/preview") as request:
            self.page.locator("#buildBtn").click()
        payload = request.value.post_data_json
        assert payload is not None
        self.assertTrue(payload["is_pm"])
        self.assertEqual(payload["room_data"]["14:00"], {"off": "Officer B", "b": "2", "s": "1"})
        self.page.locator("#previewArea img").wait_for(state="visible")

    def test_export_download_contains_both_schedules(self):
        # Exercise the download fallback consistently, including on secure localhost.
        self.page.add_init_script("window.showSaveFilePicker = undefined")
        self.import_people("Alex, 11:00, 11:30\nBlake, 14:00, 14:30")
        self.page.on("dialog", lambda dialog: dialog.accept("schedule.xlsx"))
        with self.page.expect_download() as pending:
            self.page.locator("#exportBtn").click()
        download = pending.value
        self.assertEqual(download.suggested_filename, "schedule.xlsx")
        path = download.path()
        self.assertIsNotNone(path)
        with open(str(path), "rb") as file:
            workbook = load_workbook(io.BytesIO(file.read()))
        self.addCleanup(workbook.close)
        self.assertEqual(workbook["AM"]["C7"].value, "Alex")
        self.assertEqual(workbook["PM"]["C7"].value, "Blake")

    def test_failed_requests_show_errors_and_allow_retry(self):
        self.import_people()
        for endpoint, button, message in [
            ("preview", "buildBtn", "Preview unavailable"),
            ("export", "exportBtn", "Export unavailable"),
        ]:
            with self.subTest(endpoint=endpoint):
                self.page.route(
                    f"**/{endpoint}",
                    lambda route: route.fulfill(
                        status=500,
                        content_type="application/json",
                        json={"error": message},
                    ),
                )
                self.page.locator(f"#{button}").click()
                self.page.wait_for_function(
                    "message => document.querySelector('#inlineStatus').textContent === message",
                    arg=message,
                )
                self.assertNotIn("show", self.page.locator("#spinner").get_attribute("class") or "")
                self.page.unroute(f"**/{endpoint}")
        self.page.locator("#buildBtn").click()
        self.page.locator("#previewArea img").wait_for(state="visible")
