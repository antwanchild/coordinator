# Changelog

All notable changes are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.23.6] - 2026-03-28

### 🐛 Bug Fixes

- Add 3rd sheet on export with table data
## [1.23.5] - 2026-03-28

### 🐛 Bug Fixes

- Logic for veil count and proper layout on export
## [1.23.4] - 2026-03-27

### 🐛 Bug Fixes

- Exporting of the officiator name was crammed with the "Off:"
## [1.23.3] - 2026-03-20

### 🐛 Bug Fixes

- Changed case on hint in paste box
- Edit hint on csv import
## [1.23.2] - 2026-03-20

### 🐛 Bug Fixes

- Update minor changes on code
## [1.23.1] - 2026-03-18

### 🐛 Bug Fixes

- Added favicon
## [1.23.0] - 2026-03-17

### ♻️ Refactoring

- Move datetime import to top level, add scoring comments to recommend_veils

### ✨ Features

- Use native file picker for export on supported browsers, fallback for Safari
## [1.22.3] - 2026-03-17

### 🐛 Bug Fixes

- Restore margin-top auto on generate section
## [1.22.2] - 2026-03-17

### 🐛 Bug Fixes

- Set sidebar height so generate section stays pinned to bottom
## [1.22.1] - 2026-03-17

### 🐛 Bug Fixes

- Include sheet name in overflow warning toast
## [1.22.0] - 2026-03-17

### ✨ Features

- Warn when more names than available rows on current sheet
## [1.21.4] - 2026-03-17

### 🐛 Bug Fixes

- Use JS-positioned tooltip popup to escape sidebar overflow clipping
## [1.21.3] - 2026-03-17

### 🐛 Bug Fixes

- Shorten tooltip text
## [1.21.2] - 2026-03-17

### 🐛 Bug Fixes

- Allow tooltip to overflow sidebar and card boundaries

### 📖 Documentation

- Update README with veil recommendation, help modal, and usage notes
## [1.21.1] - 2026-03-17

### 🐛 Bug Fixes

- Toggle pill stays vertically centered using fixed positioning
## [1.21.0] - 2026-03-17

### ✨ Features

- Confirm before replacing existing data on paste or CSV import
## [1.20.2] - 2026-03-17

### 🐛 Bug Fixes

- Prefer more total veils when rotation difference is within 0.5
## [1.20.1] - 2026-03-17

### 🐛 Bug Fixes

- Rewrite veil recommendation for equal rotations instead of proportional split
## [1.20.0] - 2026-03-17

### ✨ Features

- Separate B:/S: count and veil recommendation into individual cells in row 3
## [1.19.1] - 2026-03-17

### 🐛 Bug Fixes

- Veil recommendation based on B:/S: ratio and available workers
## [1.19.0] - 2026-03-17

### ✨ Features

- Split B:/S: counts and veil recommendations into separate cells in row 3
## [1.18.0] - 2026-03-17

### ✨ Features

- Veil recommendation based on B:/S: ratio and available workers
## [1.17.5] - 2026-03-17

### 🐛 Bug Fixes

- Increase tooltip width, z-index, and allow overflow on section labels
## [1.17.4] - 2026-03-16

### 🐛 Bug Fixes

- Tooltip shows below element and wraps text to prevent overflow
## [1.17.3] - 2026-03-16

### ✨ Features

- Add help modal with inline tooltips and paste format hint

### 🐛 Bug Fixes

- Set paste as default active tab, hide manual panel on load

### 📖 Documentation

- Update README with room data format and paste tab default
- Update README with room data format, paste default, LOG_LEVEL, health check, themes
## [1.17.2] - 2026-03-16

### 🐛 Bug Fixes

- Officiator names in correct cell in blue, remove duplicate row 4 block
## [1.17.1] - 2026-03-16

### 🐛 Bug Fixes

- AM room 1 always shows Off: with AM Shift, no officiator
## [1.17.0] - 2026-03-16

### ✨ Features

- Add room data support for officiators and estimated B:/S: counts
## [1.16.7] - 2026-03-16

### 🐛 Bug Fixes

- Brothers available box correct borders, no dividing line
## [1.16.6] - 2026-03-16

### 🐛 Bug Fixes

- Remove right border from col 2 of Bros Available box
## [1.16.5] - 2026-03-16

### 🐛 Bug Fixes

- Convert all draw_text calls to positional args, fix footer font sizes and wlkr label
## [1.16.4] - 2026-03-16

### 🐛 Bug Fixes

- Row 25 red two-line label, brothers box divider, THIN RECEIVERS color and position, wlkr labels
## [1.16.3] - 2026-03-16

### 🐛 Bug Fixes

- Correct header rows 2-4 alignment, B:/S: positions, AM Shift blue color and PM sheet
## [1.16.2] - 2026-03-16

### 🐛 Bug Fixes

- Rewrite footer rendering to match exact template border and fill layout
## [1.16.1] - 2026-03-16

### 🐛 Bug Fixes

- Correct header rows 1-4 and footer rows 25-31 rendering to match template
## [1.16.0] - 2026-03-16

### ✨ Features

- Update template layout, slot colors, gray unavailable, THIN RECEIVERS footer

### 📖 Documentation

- Update README with new features, LOG_LEVEL, health check, and theme picker`
## [1.15.3] - 2026-03-15

### 🐛 Bug Fixes

- Explicitly fetch all tags before cleanup
## [1.15.2] - 2026-03-15

### 🐛 Bug Fixes

- Pass repository as env var for gh api tag deletion
## [1.15.1] - 2026-03-15

### 🐛 Bug Fixes

- Use gh api to delete tags in cleanup workflow
## [1.15.0] - 2026-03-15

### ✨ Features

- Replace accent swatches with named dropdown, add cyan/orange/pink/teal themes
## [1.14.0] - 2026-03-13

### ✨ Features

- Add health check endpoint and Dockerfile HEALTHCHECK
## [1.13.0] - 2026-03-13

### ✨ Features

- Accent theme picker with localStorage persistence for theme and accent

### 📖 Documentation

- Add print hint below export button
## [1.12.0] - 2026-03-12

### ✨ Features

- Dynamic copyright year in credits footer
## [1.11.7] - 2026-03-12

### 🐛 Bug Fixes

- Add 1:30 PM and 4:30 PM as valid end times for full slot coverage

### 📖 Documentation

- Update credits footer
## [1.11.6] - 2026-03-12

### 🐛 Bug Fixes

- Split startup log lines for readability
## [1.11.5] - 2026-03-12

### 🐛 Bug Fixes

- Correct log formatter style and add timezone to timestamp
## [1.11.4] - 2026-03-12

### 🐛 Bug Fixes

- Uniform log format between entrypoint and app
## [1.11.3] - 2026-03-12

### 🐛 Bug Fixes

- Add config volume and startup path logging to entrypoint
## [1.11.2] - 2026-03-12

### 🐛 Bug Fixes

- Add timezone to entrypoint log timestamps
## [1.11.1] - 2026-03-12

### 🐛 Bug Fixes

- Match entrypoint log format to app log style
## [1.11.0] - 2026-03-12

### ✨ Features

- Configurable log level via LOG_LEVEL environment variable
## [1.10.0] - 2026-03-12

### ✨ Features

- Log Python version, OS, and architecture on startup
## [1.9.0] - 2026-03-12

### ✨ Features

- Add separator line to log on app startup
## [1.8.2] - 2026-03-12

### 🐛 Bug Fixes

- Switch log formatter to brace style to avoid percent interpolation errors
## [1.8.1] - 2026-03-12

### ♻️ Refactoring

- Remove duplicate timing from route handlers, handled by after_request

### 🐛 Bug Fixes

- Replace em dash in log messages to avoid formatter error​​​​​​​​​​​​​​
## [1.8.0] - 2026-03-12

### ✨ Features

- Add auto-refresh toggle with accent border styling
## [1.7.0] - 2026-03-12

### ✨ Features

- Add auto-refresh toggle for preview on name changes
## [1.6.0] - 2026-03-12

### ✨ Features

- Add request timing, brothers count, and startup info to logs
## [1.5.3] - 2026-03-12

### 🐛 Bug Fixes

- Brothers count as number in footer row 25, fix header row layout to match template
## [1.5.2] - 2026-03-12

### 🐛 Bug Fixes

- Move brothers count to footer row 25, fix row 4 full-width Off label
## [1.5.1] - 2026-03-11

### 🐛 Bug Fixes

- Detect CSV format in manual name input and reroute to parser
## [1.5.0] - 2026-03-11

### ✨ Features

- Brothers count per room, sheet badges, export improvements, import validation​​​​​​​​​​​​​​​
## [1.4.4] - 2026-03-11

### ♻️ Refactoring

- Rename variables, functions, and classes for readability
- Rename variables and add docstrings to app.py

### 🐛 Bug Fixes

- Require full 30-minute coverage for slot availability

### 📖 Documentation

- Add credits footer
## [1.4.3] - 2026-03-11

### 🐛 Bug Fixes

- Improve dark mode muted text contrast and preserve version in header
- Increase muted text brightness in dark mode
## [1.4.2] - 2026-03-11

### 🐛 Bug Fixes

- Improve sidebar toggle contrast in light mode
## [1.4.1] - 2026-03-11

### 🐛 Bug Fixes

- Improve header title contrast in light mode
## [1.4.0] - 2026-03-11

### ✨ Features

- Add light/dark mode toggle
## [1.3.1] - 2026-03-11

### 🐛 Bug Fixes

- Make sidebar toggle more visible
## [1.3.0] - 2026-03-11

### ✨ Features

- Add sidebar collapse toggle

## [1.2.0] - 2026-03-11

### ✨ Features

- Add TZ, PUID, PGID support

## [1.1.6] - 2026-03-11

### 🐛 Bug Fixes

- Input validation, template check, remove unused imports

## [1.1.5] - 2026-03-11

### ✨ Features

- Add rotating file logging to /config/logs

### 🐛 Bug Fixes

- Change internal port to 8080
- Scale down and uniform slot column widths
- Widen name column for readability
- Room number and time value render in red, labels in black
- Indent Time, B:, S:, Off: by one real column
- Refresh preview when switching AM/PM sheet
- Fall back to console logging if /config not mounted
- Explicitly push tag after version bump

### 📖 Documentation

- Update README with port 8080 and /config volume docs
