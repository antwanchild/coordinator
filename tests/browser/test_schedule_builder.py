import os
import threading
import unittest

from werkzeug.serving import make_server

from app import app

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


RUN_BROWSER_TESTS = os.environ.get("RUN_BROWSER_TESTS") == "1"


@unittest.skipUnless(
    RUN_BROWSER_TESTS and sync_playwright is not None,
    "Browser tests require RUN_BROWSER_TESTS=1 and Playwright",
)
class ScheduleBuilderBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert sync_playwright is not None
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
