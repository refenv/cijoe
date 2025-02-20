from argparse import Namespace

from cijoe.core.command import Cijoe
from cijoe.core.scripts.testrunner import pytest_remote


def test_hello_world(cijoe: Cijoe):
    err, state = cijoe.run("echo 'Hello World!'")

    assert not err
    assert "Hello" in state.output()


def test_config_message(cijoe: Cijoe):
    message = cijoe.getconf("testrunner.message")
    assert message

    cijoe.run("hostname")
    cijoe.run("lspci")

    err, state = cijoe.run(f"echo '{message}'")

    assert not err
    assert "Hello" in state.output()


def test_true(cijoe: Cijoe):
    assert True


def main(args: Namespace, cijoe: Cijoe):
    """
    This main function is not run as part of the example workflow in the
    core.testrunner example, but must be here in order for it to be
    elicited as script when running `cijoe --example core.testrunner`.
    """

    return 0
