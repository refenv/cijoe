"""
.github/scripts/release.py, which decides whether a commit on main releases
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent.parent / ".github" / "scripts" / "release.py"
spec = importlib.util.spec_from_file_location("release", SCRIPT)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

CHANGELOG = """# Changelog

## 1.2.3

What 1.2.3 brings.

* and a list

## 1.2.2

What came before.
"""


def project(tmp_path, version="1.2.3"):
    (tmp_path / "src/cijoe/core").mkdir(parents=True)
    (tmp_path / "src/cijoe/core/__init__.py").write_text(f'__version__ = "{version}"\n')
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG)
    return tmp_path


def test_a_bump_releases_with_its_changelog_section(tmp_path):
    version, notes = release.check("ver: bump to v1.2.3", project(tmp_path))
    assert version == "1.2.3"
    assert notes == "What 1.2.3 brings.\n\n* and a list"


@pytest.mark.parametrize(
    "subject, version, problem",
    [
        ("fix(core): something", "1.2.3", "not a version bump"),
        ("ver: bump to v1.2.3 and more", "1.2.3", "not a version bump"),
        ("ver: bump to v1.2.3", "1.2.4", "__version__ is 1.2.4"),
        ("ver: bump to v1.2.4", "1.2.4", "no '## 1.2.4' section"),
    ],
)
def test_what_does_not_release(tmp_path, subject, version, problem):
    with pytest.raises(ValueError, match=problem):
        release.check(subject, project(tmp_path, version))
