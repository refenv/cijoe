"""
testrunner
==========

This is the CIJOE testrunner, it is implemented as a pytest-plugin. By doing
so, then there is little to nothing to learn, assuming, that you have used
pytest before.

The "special" thing is the pytest-plugin, it provides pytest command-line
arguments: ``-c / --config`` and ``-o / --output``. These behave just like the
``cijoe`` counter-part. Within, your tests, then a ``cijoe`` fixture is
provided. It will give the tests access to a cijoe-instance with the given
config. Quite neat :)

Thus, arbitrary testing of third-party test-suites, tools benchmarks etc. is
possible with something as simple as::

    def test_foo(cijoe):

        err, state = cijoe.run("execute-some-testsuite")
        assert not err

Requires the following pytest plugins for correct behaviour:

* cijoe, fixtures providing 'cijoe' object and "--config" and "--output"
  pytest-arguments to instantiate cijoe.

* report-log, dump testnode-status as JSON, this is consumed by 'core.report'
  to produce an overview of testcases and link them with the cijoe-captured
  output and auxiliary files.

Invocation of pytest is done in one of the following two ways, and controlled
by ``args.run_local``, with boolean value True / False. The default is
True.

* args.run_local: True

  This is the most common, invoking pytest locally, which in turn will be using
  the same config as all other cijoe-scripts. To clarify, cijoe will execute
  'pytest' in the same environment/system where the ``cijoe`` cli was executed.

* args.run_local: False

  This is a special-case, where a collection of pytests uses cijoe, but only the
  configuration, the that the pytest verify is Python code / statements /
  expressions, not CIJOE command executions cijoe.run(). In order ot run these
  remotely, then the code must be available, and then it does the following:

  - Create a copy of the currently used cijoe-config and remove the transport section if any is there
  - Transfer cijoe-config-copy to remote
  - Invoke pytest remotely using cijoe-config-copy
  - Download the testreport.log from remote

  Why this? This allows for executing pytests on a remote system which does not
  use cijoe.run(). Such as tests implemented in Python.
"""

import copy
import logging as log
import uuid
from argparse import ArgumentParser, _StoreAction
from pathlib import Path

from cijoe.core.resources import dict_to_tomlfile


def add_args(parser: ArgumentParser):
    class StringToBoolAction(_StoreAction):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values == "true")

    parser.add_argument(
        "--run_local",
        choices=["true", "false"],
        default=True,
        action=StringToBoolAction,
        help="Whether 'pytest' should be executed in same environment as 'cijoe'",
    )
    parser.add_argument(
        "--random_order",
        choices=["true", "false"],
        default=True,
        action=StringToBoolAction,
        help="Whether the tests should be run in random order",
    )
    parser.add_argument("--args", type=str, help="Additional args given to 'pytest'")


def pytest_cmdline(args, config_path, output_path, reportlog_path):
    """Contruct pytest command-line arguments given args and paths"""

    log.info(f"config_path({config_path})")
    log.info(f"output_path({output_path})")
    log.info(f"reportlog_path({reportlog_path})")

    cmdline = ["pytest"]
    if args.config:
        cmdline.append("--config")
        cmdline.append(config_path)
    cmdline += ["--output", output_path]
    cmdline += ["--report-log", reportlog_path]

    if "args" in args:
        cmdline += args.args.split(" ")

    random_order = args.random_order
    cmdline += ["--random-order"] if random_order else []

    return cmdline


def pytest_remote(args, cijoe):
    """
    Run pytest on remote, that is, transfer config, execute pytest on the
    remote and transfer the testreport.log from remote to local
    """

    err, state = cijoe.run("pwd")
    if err:
        log.error("Failed querying 'pwd'")
        return err

    cwd = Path(state.output().strip())
    rand = str(uuid.uuid4())[:8]

    # Construct config based on current config, but without "ssh" transport
    config_stem = f"cijoe-config-{rand}.toml"
    config_path = cwd / config_stem
    config_path_local = args.output / cijoe.output_ident / config_stem

    config = copy.deepcopy(cijoe.config.options)
    if "transport" in config.get("cijoe", {}):
        del config["cijoe"]["transport"]

    dict_to_tomlfile(config, config_path_local)
    cijoe.put(str(config_path_local), config_path)

    # Construct pytest command-line and execute it
    reportlog_stem = f"cijoe-testreport-{rand}.log"
    reportlog_path = cwd / reportlog_stem
    reportlog_path_local = args.output / cijoe.output_ident / "testreport.log"

    # Construct the output-path and the equivalent local-path
    output_stem = f"cijoe-output-{rand}"
    output_path = cwd / output_stem
    output_path_local = args.output / cijoe.output_ident / "output_pytest"

    cmdline = pytest_cmdline(
        args,
        str(config_path),
        str(output_path),
        str(reportlog_path),
    )

    err, _ = cijoe.run(" ".join(cmdline))

    # Retrieve testlog
    cijoe.get(str(reportlog_path), str(reportlog_path_local))
    log.info(reportlog_path_local)

    # TODO: Retrieve output
    cijoe.get(str(output_path), str(output_path_local))

    # Cleanup: remove "artifacts" on remote
    cijoe.run(f"rm {config_path}")
    cijoe.run(f"rm {reportlog_path}")
    cijoe.run(f"rm -r {output_path}")

    return err


def pytest_local(args, cijoe):
    """
    Run pytest locally, that is, execute on the same system on which cijoe-cli
    was executed. The cijoe config provided via 'args.config' is forwarded to
    the pytest-cijoe-plugin unmodified.
    """

    cmdline = pytest_cmdline(
        args,
        str(args.config),
        str(args.output / cijoe.output_ident),
        str(args.output / cijoe.output_ident / "testreport.log"),
    )

    err, _ = cijoe.run_local(" ".join(cmdline))

    return err


def main(args, cijoe):
    """Invoke the pytest + cijoe-plugin test-runner"""
    return (pytest_local if args.run_local else pytest_remote)(args, cijoe)
