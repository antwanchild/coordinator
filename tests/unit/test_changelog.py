import unittest

from scripts.promote_changelog import promote_changelog


class ChangelogTests(unittest.TestCase):
    def test_promotes_notes_and_preserves_published_history(self):
        history = "## [1.0.0] - 2026-01-01\n\n### Fixed\n\n- Old entry\n"
        notes = "### Added\n\n- Export both sheets.\n\n### Fixed\n\n- Restore drafts."
        original = f"# Changelog\n\n## [Unreleased]\n\n{notes}\n\n{history}"
        self.assertEqual(
            promote_changelog(original, "1.1.0", "2026-11-24"),
            f"# Changelog\n\n## [Unreleased]\n\n## [1.1.0] - 2026-11-24\n\n{notes}\n\n{history}",
        )

    def test_empty_notes_get_an_explicit_fallback(self):
        result = promote_changelog("# Changelog\n\n## [Unreleased]\n", "1.0.0", "2026-11-24")
        self.assertIn("## [1.0.0] - 2026-11-24\n\nNo user-facing changes.", result)

    def test_rejects_missing_misplaced_or_duplicate_unreleased(self):
        for text in (
            "# Changelog\n",
            "## [1.0.0]\n\n## [Unreleased]\n",
            "## [Unreleased]\n\n## [Unreleased]\n",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                promote_changelog(text, "1.1.0", "2026-11-24")

    def test_rejects_duplicate_release_including_v_prefix(self):
        for version in ("1.0.0", "v1.0.0"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                promote_changelog(
                    f"## [Unreleased]\n\n## [{version}] - 2026-01-01\n",
                    "1.0.0",
                    "2026-11-24",
                )

    def test_rejects_invalid_version_or_date(self):
        for version, date in (("v1.0.0", "2026-11-24"), ("1.0.0", "2026-02-30")):
            with self.subTest(version=version, date=date), self.assertRaises(ValueError):
                promote_changelog("## [Unreleased]\n", version, date)
