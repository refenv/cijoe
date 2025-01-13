import os
from pathlib import Path

import pytest


def test_cli_example_emit_listing(cijoe):
    err, _ = cijoe.run("cijoe --example")
    assert not err


def test_cli_example_emit_specific(cijoe, tmp_path):
    err, state = cijoe.run("cijoe --example")
    assert not err

    examples = [line.strip() for line in state.output().splitlines()]
    for example in examples:
        err, state = cijoe.run(f"cijoe --example {example}", cwd=tmp_path)
        assert not err


def test_cli_example_emit_all_in_package(cijoe, tmp_path):
    err, state = cijoe.run("cijoe --example")
    assert not err

    examples = [line.strip() for line in state.output().splitlines()]
    for pkg_name in list(set([line.split(".")[0] for line in examples])):
        err, state = cijoe.run(f"cijoe --example {pkg_name}", cwd=tmp_path)
        assert not err


def test_emit_example_core(cijoe, tmp_path):
    err, _ = cijoe.run("cijoe --example core.default", cwd=tmp_path)
    assert not err


def test_cli_version(cijoe):
    err, _ = cijoe.run("cijoe --version")
    assert not err


def test_cli_resources(cijoe):
    err, _ = cijoe.run("cijoe --resources")
    assert not err


def test_cli_integration_check(cijoe, tmp_path):
    # Get a temporary path and change directory so it is possible
    # to rerun test and it wont pollute the test environment

    err, _ = cijoe.run("cijoe --example core.default", cwd=tmp_path)
    assert not err

    err, _ = cijoe.run(
        "cijoe --integrity "
        "-w cijoe-example-core.default/cijoe-workflow.yaml "
        "-c cijoe-example-core.default/cijoe-config.toml",
        cwd=tmp_path,
    )
    assert not err


def test_cli_environment_variables(cijoe):
    # This test needs to be run in a session since we set a environment
    # variable and it should not pollute.
    os.environ["HELLO_WORLD"] = "true"
    message = cijoe.getconf("hello.world", None)
    assert message

    os.environ["HELLO_WORLD"] = "1"
    message = cijoe.getconf("hello.world", None)

    os.environ["HELLO_WORLD"] = "0x1"
    message = cijoe.getconf("hello.world", None)
    assert message == 1

    os.environ["HELLO_WORLD"] = "Hello World!"
    message = cijoe.getconf("hello.world", None)
    assert message == "Hello World!"

    os.environ["HELLO_WORLD"] = "0xg"
    message = cijoe.getconf("hello.world", None)
