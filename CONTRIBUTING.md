# 🤝 Contributing

## 📝 Commit Message Format

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) to
automatically bump the version, tag releases, and generate the changelog on every push to `main`.

```
<type>: <short description>
```

### Types and what they do

| Commit prefix | Changelog group | Version bump |
|---|---|---|
| `feat!:` or any `!` | 🚨 Breaking Changes | Major `1.0.0→2.0.0` |
| `feat:` | ✨ Features | Minor `1.0.0→1.1.0` |
| `fix:` | 🐛 Bug Fixes | Patch `1.0.0→1.0.1` |
| `perf:` | ⚡ Performance | None |
| `refactor:` | ♻️ Refactoring | None |
| `docs:` | 📖 Documentation | None |
| `chore:` | 🔧 Chores | None |
| plain message | Not in changelog | None |

### 💡 Examples

```bash
# 🐛 Bug fix → patch bump 1.0.0 to 1.0.1
git commit -m "fix: slot colors not rendering on PM sheet"

# ✨ New feature → minor bump 1.0.0 to 1.1.0
git commit -m "feat: support paste import from Excel clipboard"

# 🚨 Breaking change → major bump 1.0.0 to 2.0.0
git commit -m "feat!: replace Pillow preview with server-side HTML render"

# No version bump — still appears in changelog
git commit -m "perf: speed up preview image rendering"
git commit -m "refactor: split render_preview into smaller functions"
git commit -m "docs: add usage screenshots to README"
git commit -m "chore: update dependencies"

# No version bump — does NOT appear in changelog
git commit -m "just tweaking some stuff"
```

## ⚙️ What happens on push

1. Workflow reads your commit message and bumps `VERSION` if applicable
2. Generates `CHANGELOG.md` using [git-cliff](https://git-cliff.org/) from `cliff.toml`
3. Commits `VERSION` and `CHANGELOG.md` back to `main` with `[skip ci]`
4. Creates a git tag (e.g. `v1.0.1`)
5. Builds and pushes Docker image to `ghcr.io` tagged as `1.0.1`, `latest`, and the short SHA

Commits with no recognized prefix (plain messages) still build and push `latest`
but do not bump the version or update the changelog.

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
pip install flask openpyxl Pillow
python app.py
# Open http://localhost:8080
```

## 🐳 Running with Docker

```bash
docker build -t coordinator .
docker run -p 8080:8080 coordinator
# Open http://localhost:8080
```
