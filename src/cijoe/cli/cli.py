import argparse
import errno
import logging as log
import os
import shutil
import sys
import time
from pathlib import Path

import cijoe.core
from cijoe.core.command import Cijoe, default_output_path
from cijoe.core.monitor import WorkflowMonitor
from cijoe.core.resources import (
    Config,
    Workflow,
    dict_from_yamlfile,
    dict_substitute,
    get_resources,
)

DEFAULT_CONFIG_FILENAME = "cijoe-config.toml"
DEFAULT_WORKFLOW_FILENAME = "cijoe-workflow.yaml"


def log_errors(errors):
    for error in errors:
        log.error(error)


def cli_integrity_check(args):
    """Lint a workflow"""

    log.info("cli: lint")
    log.info(f"workflow: '{args.workflow}'")
    log.info(f"config: '{args.config}'")

    if args.workflow is None:
        log.error("'failed: missing workflow'")
        return errno.EINVAL

    workflow_dict = dict_from_yamlfile(args.workflow.resolve())
    errors = Workflow.dict_normalize(workflow_dict)  # Normalize it
    errors += Workflow.dict_lint(workflow_dict)  # Check the yaml-file

    if args.config:  # Check config/substitutions
        config = Config.from_path(args.config)
        if not config:
            log.error(f"failed: Config.from_path({args.config})")
            return errno.EINVAL

        errors += dict_substitute(workflow_dict, config.options)

    if errors:
        log_errors(errors)
        log.error("failed: 'see errors above'; Failed")
        return errno.EINVAL

    return 0


def cli_resources(args):
    """List the reference configuration files provided with cijoe packages"""

    log.info("cli: resources")
    resources = get_resources()

    print("Resources collected by the CIJOE collector are listed below.")
    for category, category_resources in sorted(resources.items()):
        print(f"{category}:" + ("" if category_resources.items() else " ~"))

        for ident, path in sorted(category_resources.items()):
            print(f"  - ident: {ident}")
            print(f"    path: {path}")

    return 0


def cli_archive(args):
    """Move 'output' directory into archive"""

    if args.output.exists():
        state_path = args.output / "workflow.state"
        state = dict_from_yamlfile(state_path)
        tag = "" if state.get("tag", None) is None else "-".join(state["tag"]) + "-"
        t = str(time.strftime("%Y-%m-%d_%H:%M:%S"))
        archive = args.output.with_name("cijoe-archive") / f"{tag}{t}"
        os.makedirs(archive)
        log.info(f"moving existing output-directory({args.output}) to '{archive}'")
        os.rename(args.output, archive)


def cli_produce_report(args):
    """Produce workflow-report"""

    config_path = args.output / "config.orig"
    state_path = args.output / "workflow.state"

    if not state_path.exists():
        log.error("no workflow.state, nothing to produce a report for")
        return errno.EINVAL

    if not config_path.exists():
        log.error("missing config")
        return errno.EINVAL

    # Check config/substitutions
    config = Config.from_path(config_path)
    if not config:
        log.error(f"failed: Config.from_path({config_path})")
        return errno.EINVAL

    cijoe = Cijoe(config, args.output)

    resources = get_resources()

    reporter = resources["scripts"]["core.reporter"]
    if reporter.func is None:
        reporter.load()

    return reporter.func(
        args,
        cijoe,
        {"name": "report", "uses": "core.reporter", "with": {"report_open": True}},
    )


def cli_example(args):
    """Create example config.toml and workflow.yaml"""

    log.info("cli: examples")
    err = 0

    resources = get_resources()

    resource = resources["configs"].get(f"{args.example}.default-config", None)
    if resource is None:
        log.error(
            f"'default-config{Config.SUFFIX}' from '{args.example}'; not available"
        )
        return errno.EINVAL
    src_config = resource.path

    resource = resources["workflows"].get(f"{args.example}.example-workflow", None)
    if resource is None:
        log.error(
            f"'example-workflow{Workflow.SUFFIX}' from '{args.example}'; not available"
        )
        return errno.EINVAL

    src_workflow = resource.path

    dst_config = Path.cwd().joinpath(DEFAULT_CONFIG_FILENAME)
    dst_workflow = Path.cwd().joinpath(DEFAULT_WORKFLOW_FILENAME)

    log.info(f"config: {dst_config}")
    log.info(f"workflow: {dst_workflow}")

    if not src_config.exists():
        log.error(
            f"'default-config{Config.SUFFIX}' from '{args.example}'; not available"
        )
        return errno.EINVAL
    if not src_workflow.exists():
        log.error(
            f"example-workflow{Workflow.SUFFIX}' from '{args.example}'; not available"
        )
        return errno.EINVAL

    if dst_config.exists():
        err = errno.EEXIST
        log.error(f"skipping config({dst_config}); already exists")
    else:
        shutil.copyfile(src_config, dst_config)

    if dst_workflow.exists():
        err = errno.EEXIST
        log.error(f"skipping workflow({dst_workflow}); already exists")
    else:
        shutil.copyfile(src_workflow, dst_workflow)

    return err


def cli_version(args):
    """Print version and exit"""

    print(f"cijoe {cijoe.core.__version__}")

    return 0


def cli_monitor(args):
    """Start workflow monitor"""

    monitor = WorkflowMonitor()
    monitor.start()
    monitor.join()

    return 0


def cli_workflow(args):
    """Process workflow"""

    log.info("cli: run")
    log.info(f"workflow: {args.workflow}")
    log.info(f"config: {args.config}")
    log.info(f"output: {args.output}")

    if args.workflow is None:
        log.error("missing workflow")
        return errno.EINVAL
    if args.config is None:
        log.error("missing config")
        return errno.EINVAL

    cli_archive(args)

    state_path = args.output / "workflow.state"
    if state_path.exists():
        log.error(f"aborting; output({args.output}) directory already exists")
        return errno.EPERM

    config = Config(args.config.resolve())
    errors = config.load()
    if errors:
        log_errors(errors)
        log.error("failed: Config(args.config).load()")
        return errno.EINVAL

    workflow = Workflow(args.workflow)

    errors = workflow.load(config)
    if errors:
        log_errors(errors)
        log.error("workflow.load(): see errors above or run 'cijoe -i'")
        return errno.EINVAL

    workflow.state["tag"] = args.tag
    step_names = [step["name"] for step in workflow.state["steps"]]
    for step_name in args.step:
        if step_name in step_names:
            continue

        log.error(f"step({step_name}) not in workflow")
        return errno.EINVAL

    os.makedirs(args.output)
    shutil.copyfile(args.config, args.output / "config.orig")
    shutil.copyfile(args.workflow, args.output / "workflow.orig")
    resources = get_resources()

    # pre-load scripts and augment state with step-descriptions.
    # TODO: for some reason when mod.__doc__ is None, then the docstring from a previous
    # mod trickles in. This should be fixed...
    for step in workflow.state["steps"]:
        script_ident = step["uses"]
        resources["scripts"][script_ident].load()

        step["description"] = "Undocumented"
        if resources["scripts"][script_ident].mod.__doc__:
            step["description"] = str(resources["scripts"][script_ident].mod.__doc__)

    workflow.state["status"]["started"] = time.time()

    workflow.state_dump(args.output / Workflow.STATE_FILENAME)

    fail_fast = False

    cijoe = Cijoe(config, args.output)
    for step in workflow.state["steps"]:
        log.info(f"step({step['name']}) - begin")

        begin = time.time()

        cijoe.set_output_ident(step["id"])
        os.makedirs(os.path.join(cijoe.output_path, step["id"]), exist_ok=True)

        if args.step and step["name"] not in args.step:
            step["status"]["skipped"] = 1
        else:
            script_ident = step["uses"]

            try:
                err = resources["scripts"][script_ident].func(args, cijoe, step)
                if err:
                    log.error(f"script({script_ident}) : err({err})")
                step["status"]["failed" if err else "passed"] = 1
            except KeyboardInterrupt:
                log.exception(f"script({script_ident}) : failed")
                step["status"]["failed"] = 1
            except Exception:
                log.exception(f"script({script_ident}) : failed")
                step["status"]["failed"] = 1

        for key in ["failed", "passed", "skipped"]:
            workflow.state["status"][key] += step["status"][key]

        step["status"]["elapsed"] = time.time() - begin
        workflow.state["status"]["elapsed"] += step["status"]["elapsed"]
        workflow.state_dump(args.output / Workflow.STATE_FILENAME)

        for text, status in step["status"].items():
            if text != "elapsed" and status:
                log.info(f"step({step['name']}) : {text}")

        if step["status"]["failed"] and fail_fast:
            log.error(f"exiting, fail_fast({fail_fast})")
            break

    err = errno.EIO if workflow.state["status"]["failed"] else 0
    if err:
        log.error("one or more steps failed")

    return err


def parse_args():
    """Parse command-line interface."""

    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).stem,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    workflow_group = parser.add_argument_group(
        "workflow", "Run workflow at '-w', using config at '-c', and output at '-o'"
    )

    workflow_group.add_argument(
        "step", nargs="*", help="One or more workflow steps to run."
    )

    workflow_group.add_argument(
        "--config",
        "-c",
        type=Path,
        default=os.environ.get("CIJOE_DEFAULT_CONFIG", DEFAULT_CONFIG_FILENAME),
        help="Path to the Configuration file.",
    )
    workflow_group.add_argument(
        "--workflow",
        "-w",
        type=Path,
        default=os.environ.get("CIJOE_DEFAULT_WORKFLOW", DEFAULT_WORKFLOW_FILENAME),
        help="Path to workflow file.",
    )
    workflow_group.add_argument(
        "--output",
        "-o",
        type=Path,
        default=default_output_path(),
        help="Path to output directory.",
    )
    workflow_group.add_argument(
        "--log-level",
        "-l",
        action="append_const",
        const=1,
        help="Increase log-level.",
    )
    workflow_group.add_argument(
        "--no-report",
        "-n",
        action="store_true",
        help="Skip the producing, and opening, a report at the end of the workflow-run",
    )

    workflow_group.add_argument(
        "--tag",
        "-t",
        type=str,
        action="append",
        help="Tags to identify a workflow-run."
        " This will be prefixed while storing in archive",
    )

    utils_group = parser.add_argument_group(
        "utilities", "Workflow, and workflow-related utilities"
    )
    utils_group.add_argument(
        "--archive",
        "-a",
        action="store_true",
        help="Move the output at '-o / --output' to 'cijoe-archive/YYYY-MM-DD_HH:MM:SS",
    )
    utils_group.add_argument(
        "--produce-report",
        "-p",
        action="append_const",
        const=1,
        help="Produce report, and open it, for output at '-o / --output' and exit.",
    )
    utils_group.add_argument(
        "--monitor",
        "-m",
        action="store_true",
        help="Monitor workflow-output in the current-workdir-directory (cwd).",
    )
    utils_group.add_argument(
        "--integrity-check",
        "-i",
        action="store_true",
        help="Check integrity of workflow at '-w / --workflow' and exit.",
    )
    utils_group.add_argument(
        "--resources",
        "-r",
        action="store_true",
        help="List collected resources and exit.",
    )
    utils_group.add_argument(
        "--example",
        "-e",
        action="store",
        const="core",
        type=str,
        nargs="?",
        default=None,
        help="Create 'default-config.toml' and 'example-workflow.yaml' and exit.",
    )
    utils_group.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Print the version number of 'cijoe' and exit.",
    )

    return parser.parse_args()


def main():
    """Main entry point for the CLI"""

    args = parse_args()

    log.basicConfig(
        format="%(levelname)s:%(module)s:%(funcName)s(): %(message)s",
        level=[log.ERROR, log.INFO, log.WARNING, log.DEBUG][
            sum(args.log_level) if args.log_level else 0
        ],
    )

    if args.integrity_check:
        return cli_integrity_check(args)

    if args.resources:
        return cli_resources(args)

    if args.example:
        return cli_example(args)

    if args.version:
        return cli_version(args)

    if args.produce_report:
        return cli_produce_report(args)

    if args.archive:
        return cli_archive(args)

    if args.monitor:
        return cli_monitor(args)

    err = cli_workflow(args)

    if not args.no_report:
        report_err = cli_produce_report(args)
        err = err if err else report_err

    return err
