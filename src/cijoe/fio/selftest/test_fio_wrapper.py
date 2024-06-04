import cijoe.linux.null_blk as null_blk
import pytest

import cijoe.fio.wrapper as fio


def skip_when_config_has_no_remote(cijoe):
    """Skip testing when configuration is module not enabled"""

    transport = cijoe.config.options.get("transport", None)
    if not transport:
        pytest.skip(reason="skipping as there is no remote transport defined")


def test_run(cijoe):

    skip_when_config_has_no_remote(cijoe)

    err, _ = null_blk.insert(cijoe)
    assert not err

    err, _ = fio.run(
        cijoe,
        [
            "--filename",
            "/dev/nullb0",
            "--bs",
            "4k",
            "--rw",
            "randread",
            "--size",
            "1G",
            "--name",
            "foo42",
        ],
    )
    assert not err
