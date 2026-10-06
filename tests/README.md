# Tests

This directory is split by concern so the suite stays easy to extend:

- `unit/test_constants.py` covers small conversion helpers in `constants.py`.
- `unit/test_room_utils.py` covers room header values and veil recommendations.
- `unit/test_schedule.py` covers scheduling logic like slot coverage and veil recommendations.
- `unit/test_security.py` covers formula-injection safety helpers.
- `unit/test_validation.py` covers request and payload validation.
- `integration/test_app.py` covers app-level behavior like security headers and error handling.
- `integration/test_renderer.py` covers PNG preview generation.
- `integration/test_routes.py` covers HTTP routes and status codes.
- `integration/test_workbook.py` covers Excel export behavior.
- `browser/test_schedule_builder.py` covers adding people, loading previews, and switching sheets.
- `helpers.py` provides an isolated AM/PM workbook template shared by export tests.

When adding new tests, prefer the smallest file that matches the behavior being tested.

Run commands from the repository root. Install development dependencies first:

```bash
python -m pip install -r requirements-dev.txt
```

Run the regular suite (browser tests are skipped by default):

```bash
python -m unittest discover -s tests -t .
```

Install Chromium, then run browser tests:

```bash
python -m playwright install chromium
RUN_BROWSER_TESTS=1 python -m unittest discover -s tests/browser -t .
```

Use `RUN_BROWSER_TESTS=1 python -m unittest discover -s tests -t .` to run all tests.
Browser tests require Playwright and Chromium; minimal Linux environments may also
need system dependencies installed with `python -m playwright install --with-deps chromium`.
