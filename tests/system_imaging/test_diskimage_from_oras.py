"""Unit tests for the system_imaging.diskimage_from_oras script.

These cover the parts that need neither network nor qemu: the digest-keyed skip
and the image-selection in ``main``. Any unexpected ``run_local`` fails the test.
"""

import shlex
from pathlib import Path

from cijoe.system_imaging.scripts import diskimage_from_oras as mod

DIGEST = "sha256:" + "a" * 64
REF = f"oras://ghcr.io/safl/nosi/example@{DIGEST}"


class FakeCijoe:
    def __init__(self, conf=None):
        self._conf = conf or {}

    def getconf(self, key, default=None):
        return self._conf.get(key, default)

    def run_local(self, cmd):
        raise AssertionError(f"unexpected run_local: {cmd}")


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_skip_when_already_staged(tmp_path):
    disk = tmp_path / "image.qcow2"
    disk.write_bytes(b"staged")
    (tmp_path / "image.qcow2.digest").write_text(DIGEST)

    image = {"oras": {"url": REF}, "disk": {"path": str(disk)}}

    # The stamp matches the pinned digest, so it returns without pulling; the
    # FakeCijoe asserts if any command is run.
    assert mod.diskimage_from_oras(FakeCijoe(), image) == 0


def test_main_ignores_images_without_oras():
    images = {"debian": {"cloud": {"url": "x"}, "disk": {"path": "/x"}}}
    cijoe = FakeCijoe({"system-imaging.images": images})

    # No oras source means nothing is built and no command is run.
    assert mod.main(Args(pattern="*"), cijoe) == 0


def test_main_requires_images_config():
    import errno

    assert mod.main(Args(pattern="*"), FakeCijoe({})) == errno.EINVAL


TAG = "oras://ghcr.io/safl/nosi/example:v1.2.3"


class Resolved:
    def __init__(self, digest):
        self.digest = digest
        self.blob_url = f"https://ghcr.io/v2/safl/nosi/example/blobs/{digest}"
        self.headers = {}


def test_tag_skips_when_the_digest_it_names_is_staged(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.oras, "resolve_ref", lambda ref: Resolved(DIGEST))
    disk = tmp_path / "image.qcow2"
    disk.write_bytes(b"staged")
    (tmp_path / "image.qcow2.digest").write_text(DIGEST)

    image = {"oras": {"url": TAG}, "disk": {"path": str(disk)}}

    assert mod.diskimage_from_oras(FakeCijoe(), image) == 0


def test_tag_pulls_when_it_names_another_digest(tmp_path, monkeypatch):
    moved = "sha256:" + "b" * 64
    monkeypatch.setattr(mod.oras, "resolve_ref", lambda ref: Resolved(moved))
    disk = tmp_path / "image.qcow2"
    disk.write_bytes(b"staged")
    (tmp_path / "image.qcow2.digest").write_text(DIGEST)

    class Pulling(FakeCijoe):
        commands = []

        def run_local(self, cmd):
            self.commands.append(cmd)
            if cmd.startswith("curl"):
                Path(shlex.split(cmd)[shlex.split(cmd).index("-o") + 1]).write_bytes(
                    b"qcow"
                )
            return 0, None

    monkeypatch.setattr(mod, "qemu_img", lambda cijoe, args: (0, None))
    cijoe = Pulling()
    image = {"oras": {"url": TAG}, "disk": {"path": str(disk)}}

    assert mod.diskimage_from_oras(cijoe, image) == 0
    assert moved in cijoe.commands[0]
    assert (tmp_path / "image.qcow2.digest").read_text() == moved


class Unreachable:
    def __init__(self, ref):
        raise mod.oras.OrasError("no route to ghcr.io")


def test_staged_tag_is_used_when_the_registry_is_unreachable(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.oras, "resolve_ref", Unreachable)
    disk = tmp_path / "image.qcow2"
    disk.write_bytes(b"staged")
    (tmp_path / "image.qcow2.digest").write_text(DIGEST)

    image = {"oras": {"url": TAG}, "disk": {"path": str(disk)}}

    assert mod.diskimage_from_oras(FakeCijoe(), image) == 0


def test_unstaged_tag_fails_when_the_registry_is_unreachable(tmp_path, monkeypatch):
    import errno

    monkeypatch.setattr(mod.oras, "resolve_ref", Unreachable)
    image = {"oras": {"url": TAG}, "disk": {"path": str(tmp_path / "image.qcow2")}}

    assert mod.diskimage_from_oras(FakeCijoe(), image) == errno.EHOSTUNREACH


def test_a_growth_other_than_the_default_is_stamped_and_applied(tmp_path, monkeypatch):
    moved = "sha256:" + "c" * 64
    monkeypatch.setattr(mod.oras, "resolve_ref", lambda ref: Resolved(moved))
    resized = []
    monkeypatch.setattr(
        mod, "qemu_img", lambda cijoe, args: resized.append(args) or (0, None)
    )

    class Pulling(FakeCijoe):
        def run_local(self, cmd):
            Path(shlex.split(cmd)[shlex.split(cmd).index("-o") + 1]).write_bytes(b"x")
            return 0, None

    disk = tmp_path / "image.qcow2"
    image = {"oras": {"url": TAG}, "disk": {"path": str(disk), "grow": "32G"}}

    assert mod.diskimage_from_oras(Pulling(), image) == 0
    assert any(args.startswith("resize") and args.endswith("+32G") for args in resized)
    assert (tmp_path / "image.qcow2.digest").read_text() == f"{moved} +32G"


def test_changing_the_growth_restages(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.oras, "resolve_ref", lambda ref: Resolved(DIGEST))
    disk = tmp_path / "image.qcow2"
    disk.write_bytes(b"staged")
    (tmp_path / "image.qcow2.digest").write_text(DIGEST)

    staged = {"oras": {"url": TAG}, "disk": {"path": str(disk)}}
    assert mod.diskimage_from_oras(FakeCijoe(), staged) == 0, "the default is staged"

    grown = {"oras": {"url": TAG}, "disk": {"path": str(disk), "grow": "32G"}}

    class Refusing(FakeCijoe):
        def run_local(self, cmd):
            return 9, None

    assert mod.diskimage_from_oras(Refusing(), grown) == 9, "another growth pulls"
