"""Promote curated Unreleased notes without rewriting published history."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re


def promote_changelog(text: str, version: str, release_date: str) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected a semantic version such as 1.2.3")
    datetime.strptime(release_date, "%Y-%m-%d")
    headings = list(re.finditer(r"^## \[([^\]\n]+)\][^\n]*$", text, re.MULTILINE))
    if not headings or headings[0].group(1) != "Unreleased":
        raise ValueError("The first release section must be ## [Unreleased]")
    if sum(h.group(1) == "Unreleased" for h in headings) != 1:
        raise ValueError("Expected exactly one Unreleased section")
    if any(h.group(1).removeprefix("v") == version for h in headings):
        raise ValueError(f"Release {version} already exists")

    start = headings[0]
    end = headings[1].start() if len(headings) > 1 else len(text)
    notes = text[start.end() : end].strip()
    if not notes:
        notes = "No user-facing changes."
    return (
        text[: start.start()]
        + f"## [Unreleased]\n\n## [{version}] - {release_date}\n\n{notes}\n\n"
        + text[end:]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    args = parser.parse_args()
    try:
        updated = promote_changelog(
            args.changelog.read_text(encoding="utf-8"),
            args.version,
            datetime.now(timezone.utc).date().isoformat(),
        )
    except ValueError as exc:
        parser.error(str(exc))
    args.changelog.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
