"""
The linux package goes away at v1.0; each of its scripts says so when it runs
"""

from argparse import Namespace

import pytest

from cijoe.core.command import Cijoe
from cijoe.core.misc import DEPRECATIONS_WARNED
from cijoe.core.resources import Config
from cijoe.linux.scripts import build_kdebs, null_blk, sysinfo


@pytest.fixture
def cijoe(tmp_path):
    """A cijoe on the initiator, with an empty config"""

    (tmp_path / "config.toml").write_text("")
    return Cijoe(Config.from_path(tmp_path / "config.toml"), tmp_path / "out", False)


@pytest.mark.parametrize(
    "script, args, warning",
    [
        (null_blk, Namespace(do="neither"), "linux.null_blk is deprecated; it will"),
        (build_kdebs, Namespace(), "linux.build_kdebs is deprecated; it will"),
        (sysinfo, Namespace(), "linux.sysinfo is deprecated; use core.facts_gather"),
    ],
)
def test_linux_scripts_are_deprecated(cijoe, script, args, warning, capsys):
    """Each warns; null_blk, told neither to insert nor to remove, and
    build_kdebs, given no repository, run nothing, and sysinfo only lists"""

    DEPRECATIONS_WARNED.clear()
    script.main(args, cijoe)

    assert warning in capsys.readouterr().err
