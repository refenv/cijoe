"""
core.repository_prep given a checkout that exists, cloned from another remote
than the config now names
"""

import subprocess
from argparse import Namespace
from pathlib import Path

from cijoe.core.command import Cijoe
from cijoe.core.resources import Config
from cijoe.core.scripts import repository_prep


def git(*args, cwd=None):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def prep(tmp_path, repository):
    config = Config(Path("fake.toml"))
    config.options = {"fil": {"repository": repository}}
    cijoe = Cijoe(config, tmp_path / "out", False)
    args = Namespace(depth=None, single_branch=False, recursive=False)
    return repository_prep.main(args, cijoe)


def test_a_changed_remote_is_fetched_from(tmp_path):
    work = tmp_path / "work"
    git("init", "-q", "-b", "main", str(work))
    git("commit", "-q", "--allow-empty", "-m", "one", cwd=work)
    old = tmp_path / "old.git"
    git("clone", "-q", "--bare", str(work), str(old))

    git("commit", "-q", "--allow-empty", "-m", "two", cwd=work)
    git("tag", "v2", cwd=work)
    new = tmp_path / "new.git"
    git("clone", "-q", "--bare", str(work), str(new))

    path = tmp_path / "fil"
    assert prep(tmp_path, {"remote": str(old), "path": str(path)}) == 0

    repository = {"remote": str(new), "path": str(path), "tag": "v2"}
    assert prep(tmp_path, repository) == 0
    assert git("remote", "get-url", "origin", cwd=path) == str(new)
    assert git("rev-parse", "HEAD", cwd=path) == git("rev-parse", "v2", cwd=work)


def test_a_tag_moved_on_the_new_remote_is_fetched(tmp_path):
    work = tmp_path / "work"
    git("init", "-q", "-b", "main", str(work))
    git("commit", "-q", "--allow-empty", "-m", "one", cwd=work)
    git("tag", "v1", cwd=work)
    old = tmp_path / "old.git"
    git("clone", "-q", "--bare", str(work), str(old))

    git("commit", "-q", "--allow-empty", "-m", "two", cwd=work)
    git("tag", "-f", "v1", cwd=work)
    new = tmp_path / "new.git"
    git("clone", "-q", "--bare", str(work), str(new))

    path = tmp_path / "fil"
    assert prep(tmp_path, {"remote": str(old), "path": str(path), "tag": "v1"}) == 0

    repository = {"remote": str(new), "path": str(path), "tag": "v1"}
    assert prep(tmp_path, repository) == 0
    assert git("rev-parse", "HEAD", cwd=path) == git("rev-parse", "v1", cwd=work)


def test_a_checkout_without_origin_gets_one(tmp_path):
    work = tmp_path / "work"
    git("init", "-q", "-b", "main", str(work))
    git("commit", "-q", "--allow-empty", "-m", "one", cwd=work)
    git("tag", "v1", cwd=work)
    remote = tmp_path / "remote.git"
    git("clone", "-q", "--bare", str(work), str(remote))

    path = tmp_path / "fil"
    git("init", "-q", str(path))

    repository = {"remote": str(remote), "path": str(path), "tag": "v1"}
    assert prep(tmp_path, repository) == 0
    assert git("remote", "get-url", "origin", cwd=path) == str(remote)
    assert git("rev-parse", "HEAD", cwd=path) == git("rev-parse", "v1", cwd=work)


def test_a_failed_clone_is_reported_as_such(tmp_path, caplog):
    path = tmp_path / "fil"
    repository = {"remote": str(tmp_path / "nosuch.git"), "path": str(path)}
    assert prep(tmp_path, repository) != 0
    assert "cloning failed" in caplog.text
