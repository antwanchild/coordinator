# Tests

This directory is split by concern so the suite stays easy to extend:

- `test_app.py` covers app-level behavior like security headers and error handling.
- `test_constants.py` covers small conversion helpers in `constants.py`.
- `test_renderer.py` covers PNG preview generation.
- `test_routes.py` covers HTTP routes and status codes.
- `test_schedule.py` covers scheduling logic like slot coverage and veil recommendations.
- `test_security.py` covers formula-injection safety helpers.
- `test_validation.py` covers request and payload validation.
- `test_workbook.py` covers Excel export behavior.

When adding new tests, prefer the smallest file that matches the behavior being tested.
