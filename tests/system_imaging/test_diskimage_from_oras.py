"""Unit tests for the system_imaging.diskimage_from_oras script.

These cover the parts that need neither network nor qemu: the digest-keyed skip
and the image-selection in ``main``. Any unexpected ``run_local`` fails the test.
"""

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
