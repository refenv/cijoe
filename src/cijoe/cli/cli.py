import argparse
import errno
import logging as log
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import jinja2

import cijoe.core
from cijoe.core.command import Cijoe, default_output_path
from cijoe.core.resources import (
    Config,
    Workflow,
    dict_from_yamlfile,
    dict_substitute,
    get_resources,
)

DEFAULT_CONFIG_FILENAME = "cijoe-config.toml"
DEFAULT_WORKFLOW_FILENAME = "cijoe-workflow.yaml"
DEFAULT_SCRIPT_FILENAME = "cijoe-script.py"
SEARCH_PATHS = [
    Path.cwd(),
    Path.cwd() / ".cijoe",
    Path.home() / ".config" / "cijoe",
    Path.home() / ".cijoe",
]
STEP_NAME_REGEX = r"^(?!\d)[a-z0-9_-]+$"


def search_for_file(path: Path) -> Optional[Path]:
    """
    Search for a file named path.name. In case the given 'path' does not
    have a directory path, then SEARCH_PATH is used.

    Returns a resolved Path object on success and None on error.
    """

    # Has a directory part; resolve it and check that it exists
    if path.is_absolute() or len(path.parts) != 1:
        path = path.resolve()
        if path.exists():
            return path

        return None

    # Only a filename; look in search paths
    for spath in SEARCH_PATHS:
        candidate = (spath / path).resolve()
        if candidate.exists():
            return candidate

    return None


def log_errors(errors):
    for error in errors:
        log.error(error)


def cli_integrity_check(args):
    """Lint a workflow"""

    log.info("cli: lint")
    log.info(f"workflow: '{args.workflow}'")
    log.info(f"config: '{args.config}'")

    workflow_dict = dict_from_yamlfile(args.workflow.resolve())

    steps = workflow_dict.get("steps", None)
    if steps is None:
        log.error("No steps in workflow, nothing to do.")
        return errno.EINVAL

    for nr, step in enumerate(steps, 1):
        step_name = step.get("name", None)
        if step_name is None:
            log.error(f"Step number({nr}) is missing mandatory 'name'")
            return errno.EINVAL

        if not re.match(STEP_NAME_REGEX, step_name):
            log.error(
                f"Invalid step_name({step_name}); must match regex({STEP_NAME_REGEX})"
            )
            return errno.EINVAL

    errors = Workflow.dict_normalize(workflow_dict)  # Normalize it
    errors += Workflow.dict_lint(workflow_dict)  # Check the yaml-file

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
        tag = ""
        if state_path.exists():
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

    cijoe = Cijoe(config, args.output, args.monitor)

    resources = get_resources()

    reporter = resources["scripts"]["core.reporter"]
    if reporter.func is None:
        reporter.load()

    return reporter.func(
        args,
        cijoe,
        {
            "name": "report",
            "uses": "core.reporter",
            "with": {"report_open": args.skip_report},
        },
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

    resource = resources["scripts"].get("core.example", None)
    if resource is None:
        log.error(f"example.py' from '{args.example}'; not available")
        return errno.EINVAL
    src_script = resource.path

    dst_config = Path.cwd().joinpath(DEFAULT_CONFIG_FILENAME)
    dst_workflow = Path.cwd().joinpath(DEFAULT_WORKFLOW_FILENAME)
    dst_script = Path.cwd().joinpath(DEFAULT_SCRIPT_FILENAME)

    log.info(f"config: {dst_config}")
    log.info(f"workflow: {dst_workflow}")
    log.info(f"script: {dst_script}")

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
    if not src_script.exists():
        log.error(f"example.py' from '{args.example}'; not available")
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

    if dst_script.exists():
        err = errno.EEXIST
        log.error(f"skipping script({dst_script}); already exists")
    else:
        shutil.copyfile(src_script, dst_script)

    return err


def cli_version(args):
    """Print version and exit"""

    print(f"cijoe {cijoe.core.__version__}")

    return 0


def cli_workflow(args):
    """Process workflow"""

    log.info("cli: run")
    log.info(f"workflow: {args.workflow}")
    log.info(f"config: {args.config}")
    log.info(f"output: {args.output}")

    cli_archive(args)

    state_path = args.output / "workflow.state"
    if state_path.exists():
        log.error(f"aborting; output({args.output}) directory already exists")
        return errno.EPERM

    config = Config(args.config)
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

    cijoe = Cijoe(config, args.output, args.monitor)
    fail_fast = cijoe.getconf("cijoe.workflow.fail_fast", False)

    for step in workflow.state["steps"]:
        log.info(f"step({step['name']}) - begin")

        begin = time.time()
        step["status"]["started"] = begin
        workflow.state_dump(args.output / Workflow.STATE_FILENAME)

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

        for text, status in step["status"].items():
            if text != "elapsed" and status:
                log.info(f"step({step['name']}) : {text}")

        if step["status"]["failed"] and fail_fast:
            log.error(f"exiting, fail_fast({fail_fast})")
            break

    workflow.state_dump(args.output / Workflow.STATE_FILENAME)

    err = errno.EIO if workflow.state["status"]["failed"] else 0
    if err:
        log.error("one or more steps failed")

    return err


def create_adhoc_workflow(args, paths):
    paths = list(map(Path, paths))
    if len(set(path.stem for path in paths)) != len(paths):
        log.error("Duplicate script file names not allowed.")
        sys.exit(1)

    resources = get_resources([step.parent for step in paths])

    template_path = resources["templates"]["core.example-tmp-workflow.yaml"].path
    jinja_env = jinja2.Environment(
        autoescape=True, loader=jinja2.FileSystemLoader(template_path.parent)
    )
    template = jinja_env.get_template(template_path.name)

    with tempfile.NamedTemporaryFile() as workflow:
        setattr(args, "workflow", Path(workflow.name))
        setattr(args, "step", [])

        content = template.render(paths=paths)
        workflow.write(bytes(content, "utf-8"))
        workflow.seek(0)

        sys.exit(main(args))


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
        "step",
        nargs="*",
        help="Given a workflow; one or more workflow steps to run. Else; one or more cijoe Python scripts to run.",
    )

    workflow_group.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(os.environ.get("CIJOE_DEFAULT_CONFIG", DEFAULT_CONFIG_FILENAME)),
        help="Path to the Configuration file.",
    )
    workflow_group.add_argument(
        "--workflow",
        "-w",
        type=Path,
        default=Path(
            os.environ.get("CIJOE_DEFAULT_WORKFLOW", DEFAULT_WORKFLOW_FILENAME)
        ),
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
        help="Increase log-level. Provide '-l' for info and '-ll' for debug.",
    )
    workflow_group.add_argument(
        "--monitor",
        "-m",
        action="store_true",
        help="Dump command output to stdout",
    )
    workflow_group.add_argument(
        "--no-report",
        "-n",
        action="store_true",
        help="Skip the producing, and opening, a report at the end of the workflow-run",
    )
    workflow_group.add_argument(
        "--skip-report",
        "-s",
        action="store_false",
        help="Skip the report opening at the end of the workflow-run",
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
        help="Create 'default-config.toml', 'example-workflow.yaml' and 'cijoe-script.py' and exit.",
    )
    utils_group.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Print the version number of 'cijoe' and exit.",
    )

    return parser.parse_args()


def main(args=None):
    """Main entry point for the CLI"""

    if args is None:
        args = parse_args()
        if args.step and all(step.endswith(".py") for step in args.step):
            create_adhoc_workflow(args, args.step)

    levels = [log.ERROR, log.INFO, log.DEBUG]
    log.basicConfig(
        format="%(levelname)s:%(module)s:%(funcName)s(): %(message)s",
        level=levels[
            min(sum(args.log_level), len(levels) - 1) if args.log_level else 0
        ],
    )

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

    for filearg in ["config", "workflow"]:
        argv = getattr(args, filearg)
        path = search_for_file(argv)
        if path is None:
            log.error(f"{filearg}({argv}) does not exist; exiting")
            return errno.EINVAL

        setattr(args, filearg, path)

    if args.integrity_check:
        return cli_integrity_check(args)

    # At this point all Path objects are resolved, except for output, do that
    # that here.
    args.output = args.output.resolve()

    err = cli_workflow(args)

    if not args.no_report:
        report_err = cli_produce_report(args)
        err = err if err else report_err

    return err
