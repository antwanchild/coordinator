# 🤝 Contributing

## 🧪 Local Workflow

```bash
pip install -r requirements-dev.txt
pre-commit install
python app.py
```

Open `http://localhost:8080`.

For local checks:

```bash
pre-commit run --all-files
python -c "import app"

python -m unittest discover -s tests -t .
```

Browser tests live in `tests/browser/` and run with Playwright. Install Chromium once, then opt in locally:

```bash
python -m playwright install chromium
RUN_BROWSER_TESTS=1 python -m unittest discover -s tests/browser -t .
```

When explicitly enabled, missing Playwright or Chromium fails the run instead of skipping it.
The browser suite starts its own local Flask server and uses an isolated workbook template; unit tests are in `tests/unit/` and route, workbook, and renderer tests are in `tests/integration/`.
The workbook suite also checks the shipped Excel template. Browser checks cover preview generation,
paste/CSV imports, draft restoration, export downloads, and request failures.

## 📝 Commit Message Format

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) to
automatically bump the version and tag releases when qualifying commits reach `main`.
Changelog entries are written in pull requests, independently of commit subjects.

```
<type>: <short description>
```

### Types and what they do

| Commit prefix | Version bump |
|---|---|
| `feat!:` or any conventional `!:` | Major |
| `feat:` | Minor |
| `fix:` | Patch |
| `perf:`, `refactor:`, `docs:`, `chore:`, or plain messages | None |

### 💡 Examples

```bash
# 🐛 Bug fix → patch bump 1.0.0 to 1.0.1
git commit -m "fix: slot colors not rendering on PM sheet"

# ✨ New feature → minor bump 1.0.0 to 1.1.0
git commit -m "feat: support paste import from Excel clipboard"

# 🚨 Breaking change → major bump 1.0.0 to 2.0.0
git commit -m "feat!: replace Pillow preview with server-side HTML render"

# No version bump — add a curated changelog entry if useful to users
git commit -m "perf: speed up preview image rendering"
git commit -m "refactor: split render_preview into smaller functions"
git commit -m "docs: add usage screenshots to README"
git commit -m "chore: update dependencies"

# No version bump — changelog inclusion is independent of commit wording
git commit -m "just tweaking some stuff"
```

## Changelog entries

For user-facing changes, add a concise bullet under `## [Unreleased]` in
`CHANGELOG.md` in the same PR. Use `Added`, `Changed`, `Fixed`, `Removed`,
`Security`, or `Docs` headings as needed; omit empty headings. Explain the
observable behavior and its benefit or impact, including migration steps for
breaking changes. Link related issues or PRs when useful.

Internal refactors, CI maintenance, and contributor-only documentation can omit
an entry; explain why in the PR's Changelog section. Commit types determine
version bumps, not changelog categories or text.

Do not rewrite published history or manually change `VERSION`, release headings,
or release dates. When a version bump occurs, the workflow moves all accumulated
notes into that release and resets `Unreleased`. Changes without a version bump
leave their notes pending for the next release. If there are no notes at release
time, the release section records that there are no user-facing changes.

## ⚙️ What happens on push

1. Workflow reads your commit message range and bumps `VERSION` if applicable
2. When the version changes, promotes `Unreleased` notes in `CHANGELOG.md` into a
   dated release section and leaves a fresh `Unreleased` section
3. Commits `VERSION` and `CHANGELOG.md` back to `main` with `[skip ci]`
4. Creates a git tag (e.g. `v1.0.1`)
5. Builds and pushes Docker image to `ghcr.io` tagged as `1.0.1`, `1.0.1-build0`, `latest`, and the short SHA
6. Sends a Discord release notice with the semantic version, build number, and combined version footer

## 🔄 CI And Release Flow

- `.github/workflows/ci.yml` runs the `checks` job on pull requests and pushes to `main`
- The `checks` job installs dependencies, verifies `import app`, and runs the unit and integration suites on Python 3.12 and 3.14; it also installs Chromium and runs Playwright browser tests on Python 3.12
- `.github/workflows/docker.yml` is the `Release Publish` workflow and runs after `CI` succeeds on `main`
- Its `prepare-release`, `publish-image`, and `notify-release` jobs handle version bumps, image builds, and Discord notifications
- `.github/workflows/cleanup-tags.yml` is the `Tag Retention` workflow
- Docker publish has concurrency protection so overlapping publish runs do not race each other

## 🖥️ UI Contribution Notes

- Prefer inline status/help text over new modal dialogs unless the action is destructive or truly blocking
- Keep destructive confirmation behavior consistent with the shared app confirmation modal
- Browser drafts are stored in `localStorage`; changes to draft shape should be backward-tolerant or intentionally versioned

If you are changing behavior and expect a version bump, prefer a `fix:` or `feat:` commit instead of a plain commit message.

Commits with no recognized prefix (plain messages) still build and push `latest`
but do not bump the version or promote `Unreleased` notes.

## 💻 VS Code

If you're using VS Code, the [Conventional Commits](https://marketplace.visualstudio.com/items?itemName=vivaxy.vscode-conventional-commits) extension makes writing commit messages easy. Instead of typing the format manually, it walks you through a guided prompt:

1. Open the Source Control panel (`Ctrl+Shift+G`)
2. Stage your changes
3. Click the ✨ icon in the commit message bar (added by the extension)
4. Pick your type (`feat`, `fix`, `chore`, etc.)
5. Write your description
6. Commit and push

Install it by searching `vivaxy.vscode-conventional-commits` in the Extensions panel.

## 🐍 Running locally

```bash
pip install -r requirements-dev.txt
python app.py
# Open http://localhost:8080
```

## 🐳 Running with Docker

```bash
docker build -t coordinator .
docker run -p 8080:8080 coordinator
# Open http://localhost:8080
```
