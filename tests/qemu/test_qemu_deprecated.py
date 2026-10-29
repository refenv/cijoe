"""
Building QEMU from source goes away at v1.0; its scripts say so when they run
"""

from argparse import Namespace

import pytest

from cijoe.core.command import Cijoe
from cijoe.core.misc import DEPRECATIONS_WARNED
from cijoe.core.resources import Config
from cijoe.qemu.scripts import build, install


@pytest.mark.parametrize("script, name", [(build, "build"), (install, "install")])
def test_building_qemu_is_deprecated(tmp_path, script, name, capsys):
    """Each warns, and given no repository, runs nothing"""

    (tmp_path / "config.toml").write_text("")
    cijoe = Cijoe(Config.from_path(tmp_path / "config.toml"), tmp_path / "out", False)

    DEPRECATIONS_WARNED.clear()
    assert script.main(Namespace(), cijoe) != 0, "no qemu.repository.path"

    assert f"qemu.{name} is deprecated; it will be removed in v1.0" in (
        capsys.readouterr().err
    )
