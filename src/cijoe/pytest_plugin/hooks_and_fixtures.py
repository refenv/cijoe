"""
pytest-plugin API
=================

The plugin provides a cijoe-instance readily available as a test-fixture, setup per
test with a nodeid-defined output-directory. For example::

    def test_foo(cijoe):
        err, _ = cijoe.run("hostname")
        asssert not err

To provide the cijoe-instance a configuration and output directory must be provided.
These are given via pytest, e.g.::

    pytest --config default.toml --output /tmp/foo

In case no arguments are provided, defaults are used.
"""

from pathlib import Path

import pytest

from cijoe.core.command import Cijoe, default_output_path
from cijoe.core.resources import Collector, Config

pytest.cijoe_instance = None


def pytest_addoption(parser):
    """
    Add options ``--config`` and ``--output`` to pytest, these will be used for the
    instantiation of cijoe.
    """

    collector = Collector()
    collector.collect()

    parser.addoption(
        "--config",
        action="store",
        type=Path,
        help="Path to cijoe configuration",
        default=str(collector.resources["configs"]["core.example_config_default"]),
    )
    parser.addoption(
        "--output",
        action="store",
        type=Path,
        help="Path to cijoe output directory",
        default=default_output_path(),
    )


def pytest_configure(config):
    """
    Initializes the cijoe instance using pytest-options ``--config`` and ``--output``

    The cijoe-instance is stored in ``pytest.cijoe_instance``, this might appear as bad
    form. However, it is a common pytest-pattern for enabling access to state otherwise
    only accessible to tests and fixtures.

    Why would this be needed? Well, for large paramaterizations, e.g. to generate input
    to pytest.mark.parametrize(). Here it is convenient to be able to access the same
    cijoe instance, and for example generate test-parametrization based on the content
    of the cijoe-configuration.
    """

    cijoe_config_path = config.getoption("--config")

    cijoe_config = Config.from_path(cijoe_config_path)
    if cijoe_config is None:
        raise Exception(f"Failed loading config({cijoe_config_path})")

    pytest.cijoe_instance = Cijoe(
        cijoe_config,
        config.getoption("--output"),
        False,
    )
    if pytest.cijoe_instance is None:
        raise Exception("Failed instantiating cijoe")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Prints out a notice that cijoe is beeing used along with the values of the
    ``--config`` and ``--output`` options.
    """

    terminalreporter.ensure_newline()
    terminalreporter.section(
        "-={[ CIJOE pytest-plugin ]}=-", sep="-", blue=True, bold=True
    )
    terminalreporter.line("config: %r" % config.getoption("--config"))
    terminalreporter.line("output: %r" % config.getoption("--output"))


@pytest.fixture
def cijoe(request):
    """
    Provides a cijoe-instance, initialized with the pytest-options: ``--config``, and
    ``--output`` and with a per-test customization of the output directory.
    """

    if pytest.cijoe_instance is None:
        raise Exception("Invalid configuration or instance")

    pytest.cijoe_instance.set_output_ident(request.node.nodeid)

    return pytest.cijoe_instance
