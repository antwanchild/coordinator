# Changelog

All notable changes are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.1.6] - 2026-03-11

### 🐛 Bug Fixes

- Input validation, template check, remove unused imports
## [1.1.5] - 2026-03-11

### ✨ Features

- Switch to weekly rotating logs with .log extension

### 🐛 Bug Fixes

- Scale down slot column widths in preview
- Uniform slot column widths matching original spreadsheet proportions.​​​​​​​​​​​​​​​​
- Uniform slot column widths matching original spreadsheet proportions
- Widen name column for readability.​​​​​​​​​​​​​​​​
- Room labels and time rows now render in red
- Room number and time value render in red, labels in black.​​​​​​​​​​​​​​​​
- Add leading indent to Time, B:, S:, and Off: rows.​​​​​​​​​​​​​​​​
- Indent Time, B:, S:, Off: by one real column.​​​​​​​​​​​​​​​​
- Refresh preview when switching AM/PM sheet
- Fall back to console logging if /config not mounted
- Use env vars in bash if block for changelog commit
- Remove conflicting OUTPUT env from git-cliff step
- Test changelog generation
- Explicitly push tag after version bump

### 📖 Documentation

- Update README with port 8080 and /config volume docs.​​​​​​​​​​​​​​​​
- Update README with port 8080 and /config volume docs
- Clean chore entries from changelog
- Switch changelog to unreleased-only mode
- Restore clean changelog and limit git-cliff to version bumps
## [1.1.5] - 2026-03-11

### ✨ Features

- Add rotating file logging to /config/logs

### 🐛 Bug Fixes

- Change internal port to 8080
- Scale down slot column widths in preview
- Uniform slot column widths matching original spreadsheet proportions
- Widen name column for readability
- Room number and time value render in red, labels in black
- Indent Time, B:, S:, Off: by one real column
- Refresh preview when switching AM/PM sheet
- Fall back to console logging if /config not mounted
- Explicitly push tag after version bump

### 📖 Documentation

- Update README with port 8080 and /config volume docs
