"""
The scripts that act on a target: core.wait_for_target given a target it cannot
reach, and core.put, core.get and core.tools_check on the step's target, and
with the arguments they took before
"""

import errno
from argparse import Namespace
from pathlib import Path

import pytest

from cijoe.core.command import Cijoe
from cijoe.core.resources import Config
from cijoe.core.scripts import get, put, tools_check, wait_for_target


@pytest.fixture
def cijoe(tmp_path):
    """A cijoe with a target whose SSH settings name no host"""

    config = Config(Path("fake.toml"))
    config.options = {"cijoe": {"targets": {"nameless": {"ssh": {}}}}}
    return Cijoe(config, tmp_path, False)


def test_a_target_needs_a_hostname(cijoe):
    assert wait_for_target.main(Namespace(state="up", timeout=10), cijoe) == 1


@pytest.fixture
def initiator(tmp_path):
    """A cijoe with no targets but the initiator"""

    (tmp_path / "config.toml").write_text("")
    return Cijoe(Config.from_path(tmp_path / "config.toml"), tmp_path / "out", False)


@pytest.mark.parametrize("script", [put, get])
def test_put_and_get_on_the_step_target(initiator, tmp_path, script, capsys):
    src = tmp_path / "src"
    src.write_text("moved\n")

    args = Namespace(src=str(src), dst=str(tmp_path / "dst"), transport=None)
    assert script.main(args, initiator) == 0
    assert (tmp_path / "dst").read_text() == "moved\n"
    assert "deprecated" not in capsys.readouterr().err

    args = Namespace(src=str(src), dst=str(tmp_path / "again"), transport="initiator")
    assert script.main(args, initiator) == 0
    name = script.__name__.rsplit(".", 1)[-1]
    assert f"core.{name}'s 'transport' is deprecated" in capsys.readouterr().err


def test_tools_check_on_the_step_target(initiator, capsys):
    args = Namespace(tools="sh", target_name=None, refresh="false")
    assert tools_check.main(args, initiator) == 0
    assert initiator.facts.get("targets.initiator.tools.sh.found")
    assert "deprecated" not in capsys.readouterr().err

    args = Namespace(tools="sh", target_name="initiator", refresh="false")
    assert tools_check.main(args, initiator) == 0
    assert "core.tools_check's 'target_name' is deprecated" in (capsys.readouterr().err)

    args = Namespace(tools="sh", target_name="nope", refresh="false")
    assert tools_check.main(args, initiator) == errno.EINVAL
