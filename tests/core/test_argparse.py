import copy
import os
import sys
from argparse import Namespace
from pathlib import Path

from cijoe.cli.cli import DEFAULT_CONFIG_FILENAME, DEFAULT_WORKFLOW_FILENAME, parse_args

TEMPLATE_SCRIPT = """def main(args, cijoe):
    return 0
"""


def test_run_group():
    """
    Base test to check all arguments are set
    """

    config = "config.toml"
    output = "output"
    tag = "tag"
    loglevel = "ll"
    example = "example"

    test_args = [
        "cijoe",
        "-c",
        config,
        "-o",
        output,
        f"-{loglevel}",
        "--monitor",
        "--no-report",
        "--skip-report",
        "--tag",
        tag,
        "--archive",
        "--produce-report",
        "--integrity-check",
        "--resources",
        "--example",
        example,
        "--version",
    ]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.config[0].name == config
    assert args.output.name == output
    assert len(args.log_level) == len(loglevel)
    assert args.monitor
    assert args.no_report
    assert not args.skip_report
    assert args.tag == [tag]
    assert args.archive
    assert args.produce_report
    assert args.integrity_check
    assert args.resources
    assert args.example == example
    assert args.version


def test_target_workflow():
    workflow = "workflow.yaml"

    test_args = ["cijoe", workflow]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == workflow


def test_target_workflow_steps():
    workflow = "workflow.yaml"
    steps = ["step1", "step2", "step3"]

    test_args = ["cijoe", workflow, *steps]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == workflow
    assert len(args.step) == len(steps)
    assert all(a == b for a, b in zip(args.step, steps))


def test_target_core_script():
    script = "core.example_script_default"

    test_args = ["cijoe", script]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.script_name == script


def test_target_core_script_args():
    script = "core.example_script_default"

    test_args = ["cijoe", script, "--repeat", "10"]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.script_name == script
    assert args.repeat == 10


def test_target_path_script(tmp_path):
    script = "test"
    script_path = (tmp_path / f"{script}.py").resolve()

    script_path.write_text(TEMPLATE_SCRIPT)

    test_args = ["cijoe", str(script_path)]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.script_name == script


def test_target_path_script_args_fail(tmp_path):
    """
    If given a wrong argument, the argument parser should fail
    """

    script = "test"
    script_path = (tmp_path / f"{script}.py").resolve()

    script_path.write_text(TEMPLATE_SCRIPT)

    test_args = ["cijoe", str(script_path), "--repeat", "10"]
    sys.argv = test_args

    try:
        _ = parse_args()
        assert False
    except SystemExit:
        assert True


def test_target_path_script_step(tmp_path):
    """
    If given additional steps when running a script, the argument parser remove
    the steps
    """

    steps = ["step1", "step2", "step3"]

    script = "test"
    script_path = (tmp_path / f"{script}.py").resolve()

    script_path.write_text(TEMPLATE_SCRIPT)

    test_args = ["cijoe", str(script_path), *steps]
    sys.argv = test_args

    err, args = parse_args()
    assert not err
    assert args.script_name == script
    assert not args.step


def test_workflow_argument():
    """
    For backwards compatibility, the -w / --workflow argument should still work
    """

    workflow = "workflow.yaml"

    test_args = ["cijoe", "-w", workflow]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == workflow


def test_workflow_argument_steps():
    """
    For backwards compatibility, the -w / --workflow argument should still work
    """

    workflow = "workflow.yaml"
    steps = ["step1", "step2", "step3"]

    test_args = ["cijoe", "-w", workflow, *steps]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == workflow
    assert len(args.step) == len(steps)
    assert all(a == b for a, b in zip(args.step, steps))


def test_mixed_order():
    config = "config.toml"
    workflow = "workflow.yaml"
    steps = ["step1", "step2", "step3"]

    test_args = ["cijoe", "-c", config, "--monitor", workflow, *steps, "-l"]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == workflow
    assert args.config[0].name == config
    assert len(args.step) == len(steps)
    assert all(a == b for a, b in zip(args.step, steps))


def test_defaults():
    test_args = ["cijoe"]
    sys.argv = test_args
    err, args = parse_args()
    assert not err
    assert args.workflow.name == os.environ.get(
        "CIJOE_DEFAULT_WORKFLOW", DEFAULT_WORKFLOW_FILENAME
    )
