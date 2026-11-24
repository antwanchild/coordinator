# Agent guidance

Before making changes, read [CONTRIBUTING.md](CONTRIBUTING.md) and follow its
development, testing, UI, and commit conventions. Use [README.md](README.md) for
documented user behavior and [tests/README.md](tests/README.md) for test details.
Keep shared workflow instructions in those documents rather than duplicating
them here.

## Project map

- `app.py`: Flask routes, preview/export requests, and response handling.
- `validation.py`: request payload validation.
- `schedule.py`: Excel workbook generation and veil recommendations.
- `renderer.py`: Pillow preview rendering.
- `constants.py`, `time_utils.py`, and `room_utils.py`: shared layout, time,
  availability, and room-header rules.
- `templates/index.html`, `static/app.js`, and `static/app.css`: browser UI.
- `V-COORDINATE--Scheduled.xlsx`: shipped workbook template.
- `tests/unit/`, `tests/integration/`, and `tests/browser/`: automated checks.

## Change guidelines

- Keep preview and Excel export behavior consistent. Prefer shared helpers for
  scheduling, availability, and room-header logic.
- Preserve the workbook template's layout and the AM, PM, and Source Data export
  behavior unless the requested change requires updating them. Check workbook
  integration coverage when changing template or export code.
- Preserve the distinction between manual-entry times and accepted import times
  documented in the README.
- Follow CONTRIBUTING.md for UI feedback, destructive confirmations, and saved
  draft compatibility.
- Leave release version bumps and changelog generation to the release workflow
  unless explicitly asked to change release metadata.

## Verification

Use the commands in CONTRIBUTING.md. Run checks appropriate to the change:
Python unit and integration tests for backend behavior, workbook and renderer
checks for export/preview changes, and the opt-in Playwright suite for browser
behavior. Add or update regression coverage when behavior changes.

Documentation-only edits do not require application tests. Check the diff for
formatting errors and broken references. Report which checks ran and any checks
that could not run.
