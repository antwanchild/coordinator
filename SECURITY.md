# Security Policy

## Supported Versions

Only the latest release is actively supported with security updates.

| Version | Supported |
|---|---|
| Latest | ✅ |
| Older | ❌ |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities privately via [GitHub Security Advisories](../../security/advisories/new).

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You can expect an acknowledgement within 48 hours and a resolution or update within 14 days.

## Browser Storage Note

This app can store working drafts in browser `localStorage` for convenience. That storage is:

- local to the current browser profile
- not encrypted by the application
- not appropriate for secrets or highly sensitive personal data

If draft privacy matters for your environment, clear the draft from the UI and avoid leaving shared browsers signed in with saved schedule data.
