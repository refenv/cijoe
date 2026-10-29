#!/usr/bin/env python3
"""
Whether a commit on main releases a version, and the notes to release it with

Given the subject of the commit, 'ver: bump to vX.Y.Z', this checks that X.Y.Z is
the version in src/cijoe/core/__init__.py and that CHANGELOG.md has a section
for it, writes that section to stdout as the release notes, and 'version=X.Y.Z'
to $GITHUB_OUTPUT. It exits non-zero, saying why, when any of that is not so.
"""

import os
import re
import sys
from pathlib import Path

SUBJECT = re.compile(r"^ver: bump to v(\d+\.\d+\.\d+)$")
VERSION = re.compile(r'^__version__ = "([^"]+)"$', re.MULTILINE)


def notes_for(changelog: str, version: str) -> str:
    """The text of the '## <version>' section, or '' when there is none"""

    section = re.search(
        rf"^## {re.escape(version)}\n(.*?)(?=^## |\Z)", changelog, re.M | re.S
    )
    return section.group(1).strip() if section else ""


def check(subject: str, root: Path):
    """The version and its notes; raises ValueError saying what is wrong"""

    bump = SUBJECT.match(subject.strip())
    if not bump:
        raise ValueError(f"not a version bump: {subject!r}")
    version = bump.group(1)

    found = VERSION.search((root / "src/cijoe/core/__init__.py").read_text())
    if not found or found.group(1) != version:
        raise ValueError(
            f"the commit bumps to {version}, but __version__ is"
            f" {found.group(1) if found else 'missing'}"
        )

    notes = notes_for((root / "CHANGELOG.md").read_text(), version)
    if not notes:
        raise ValueError(f"CHANGELOG.md has no '## {version}' section")

    return version, notes


def main():
    try:
        version, notes = check(sys.argv[1], Path.cwd())
    except (IndexError, ValueError) as exc:
        print(f"release: {exc}", file=sys.stderr)
        return 1

    print(notes)
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"version={version}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
