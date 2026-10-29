"""A script whose required step-argument is missing says so, rather than crashing"""

import errno
from argparse import ArgumentParser
from importlib import import_module

import pytest

REQUIRED = [
    "cijoe.core.scripts.cmdrunner",
    "cijoe.core.scripts.get",
    "cijoe.core.scripts.put",
    "cijoe.qemu.scripts.guest_initialize",
    "cijoe.qemu.scripts.guest_kill",
    "cijoe.qemu.scripts.guest_start",
    "cijoe.qemu.scripts.guest_wait_for_termination",
    "cijoe.system_imaging.scripts.diskimage_from_cloudimage",
    "cijoe.system_imaging.scripts.dockerimage_from_diskimage",
]


def parse(module, argv=()):
    parser = ArgumentParser()
    module.add_args(parser)
    return parser.parse_args(list(argv))


@pytest.mark.parametrize("name", REQUIRED)
def test_missing_required_argument_fails_the_step(name):
    module = import_module(name)

    # No cijoe is given, so anything past the argument check fails the test
    assert module.main(parse(module), None) in (errno.EINVAL, 1)


def test_testrunner_without_args_builds_a_cmdline():
    from cijoe.core.scripts import testrunner

    args = parse(testrunner)
    args.config = None  # from cijoe's own command-line, which a step's args extend

    cmdline = testrunner.pytest_cmdline(args, "c.toml", "out", "log")

    assert cmdline[0] == "pytest"


def test_put_and_get_need_no_dst(cijoe, tmp_path):
    """Without a dst, the file keeps its name in the step's directory"""

    from cijoe.core.scripts import get, put

    src = tmp_path / "file.txt"
    src.write_text("content")

    assert put.main(parse(put, ["--src", str(src)]), cijoe) == 0
    assert get.main(parse(get, ["--src", str(src)]), cijoe) == 0


def test_cmdrunner_with_no_commands_runs_nothing(cijoe):
    from cijoe.core.scripts import cmdrunner

    args = parse(cmdrunner)
    args.commands = []

    assert cmdrunner.main(args, cijoe) == 0
