import pytest

import cijoe.linux.null_blk as null_blk


def skip_when_config_has_no_remote(cijoe):
    """Skip testing when configuration is module not enabled"""

    transport = cijoe.config.options.get("transport", None)
    if not transport:
        pytest.skip(reason="skipping as there is no remote transport defined")


def test_insert(cijoe):
    """Test the creation of null_block via module-load"""

    skip_when_config_has_no_remote(cijoe)

    config = cijoe.config.options.get("null_blk", None)
    assert config, "Invalid environment configuration"

    nr_devices = int(config.get("nr_devices"))
    assert nr_devices, "!nr_devices, only module-load instances are supported"

    err, _ = null_blk.insert(cijoe)
    assert not err, "Failed inserting kernel module"

    err, _ = cijoe.run("lsblk")
    assert not err, "Failed listing block devices"

    for n in range(nr_devices):
        err, _ = cijoe.run(f"file /dev/nullb{n}")
        assert not err


def test_remove(cijoe):

    skip_when_config_has_no_remote(cijoe)

    err, _ = null_blk.remove(cijoe)
    assert not err, "Failed removing kernel module"
