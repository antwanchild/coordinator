# Changelog

All notable changes are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

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
