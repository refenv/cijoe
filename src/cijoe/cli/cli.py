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


class OverrideDefaultAction(argparse._StoreAction):
    def __call__(self, parser, namespace, values, option_string=None):
        self.default = values
        setattr(namespace, self.dest, values)


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
    errors += Workflow.dict_lint(args, workflow_dict)  # Check the yaml-file

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

    setattr(args, "report_open", args.skip_report)

    return reporter.func(args, cijoe)


def cli_example(args):
    """Create example config.toml and workflow.yaml"""
    log.info("cli: examples")

    resources = get_resources()

    # Print examples when called like "cijoe --example"
    if args.example == "list_examples_and_exit":
        for workflow_name, workflow in sorted(resources.get("workflows").items()):
            if "example" not in workflow_name:
                continue

            pkg_name, tail = workflow_name.split(".", 1)
            example_name = tail.replace("example_workflow_", "")

            print(f"{pkg_name}.{example_name}")
        return 0

    pkg_name, *tail = args.example.split(".")
    if len(tail) > 1:
        log.error(f"Invalid argument: {args.example}")
        return errno.EINVAL

    # Emit examples
    for workflow_name, workflow in sorted(resources.get("workflows").items()):
        if not workflow_name.startswith(pkg_name):  # Not the requested package
            continue
        if "example" not in workflow_name:  # Not an example workflow
            continue

        cur_example_id = workflow_name.replace("example_workflow_", "")
        cur_pkg_name, cur_example_name = cur_example_id.split(".", 1)
        cur_example_dir = Path.cwd() / f"cijoe-example-{cur_example_id}"

        log.info(f"cur_pkg_name{cur_pkg_name} cur_example_name{cur_example_name}")
        if tail and "".join(tail) != cur_example_name:
            log.debug(f"skipping example_name({cur_example_name})")
            continue

        cur_example_dir.mkdir()

        for section, default_filename in [
            ("config", DEFAULT_CONFIG_FILENAME),
            ("workflow", DEFAULT_WORKFLOW_FILENAME),
            ("script", DEFAULT_SCRIPT_FILENAME),
        ]:
            label = f"{pkg_name}.example_{section}_{cur_example_name}"

            log.info(f"{args.example}, label({label})")

            resource = resources.get(f"{section}s", {}).get(label, None)
            if resource is None:
                if section == "script":  # Providing an example script is optional
                    continue

                log.error(f"'No example '{section}' in example({args.example})")
                return errno.EINVAL

            dst = cur_example_dir.joinpath(default_filename)
            if dst.exists():
                log.info(f"skipping dst({dst}); already exists")
                continue

            shutil.copyfile(resource.path, dst)

    return 0


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

    errors = workflow.load(args, config)
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
            script = resources["scripts"][script_ident]

            arguments = []
            if "with" in step:
                for k, v in step["with"].items():
                    if type(v) is list:
                        arguments += [f"--{k}", *[f"{el}" for el in v]]
                    else:
                        if type(v) is bool:
                            v = str(v).lower()
                        arguments += [f"--{k}", f"{v}"]

            parser = argparse.ArgumentParser()
            if script.argparser_func:
                script.argparser_func(parser)
            script_args = parser.parse_args(arguments)
            args = parser.parse_args(arguments, namespace=args)

            try:
                err = script.func(args, cijoe)
                if err:
                    log.error(f"script({script_ident}) : err({err})")
                step["status"]["failed" if err else "passed"] = 1
            except KeyboardInterrupt:
                log.exception(f"script({script_ident}) : failed")
                step["status"]["failed"] = 1
            except Exception:
                log.exception(f"script({script_ident}) : failed")
                step["status"]["failed"] = 1
            finally:
                for k in vars(script_args):
                    delattr(args, k)

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


def create_adhoc_workflow(args):
    target = args.script_name
    if target.endswith(".py"):
        path = Path(target)
        target = path.stem

    resources = get_resources()

    template_path = resources["templates"]["core.example-tmp-workflow.yaml"].path
    jinja_env = jinja2.Environment(
        autoescape=True, loader=jinja2.FileSystemLoader(template_path.parent)
    )
    template = jinja_env.get_template(template_path.name)

    with tempfile.NamedTemporaryFile() as workflow:
        setattr(args, "workflow", Path(workflow.name))
        setattr(args, "step", [])

        content = template.render(steps=[target])
        workflow.write(bytes(content, "utf-8"))
        workflow.seek(0)

        sys.exit(main(args))


def parse_args():
    """Parse command-line interface."""

    parent_dirs = set()
    is_workflow = False

    for i, argv in enumerate(sys.argv):
        if i == 0 or sys.argv[i - 1].startswith("-"):
            continue
        if argv.endswith(".py"):
            path = Path(argv).resolve()
            parent_dirs.add(path.parent)
            sys.argv[i] = path.stem
            break
        if argv.endswith(".yaml"):
            is_workflow = True
            sys.argv.insert(i, "--workflow")
            sys.argv.insert(i, "workflow_path")
            break

    resource_scripts = get_resources(list(parent_dirs))["scripts"]

    parent_parser = argparse.ArgumentParser(add_help=False)

    run_group = parent_parser.add_argument_group(
        "run", "Options for running a workflow script."
    )

    run_group.add_argument(
        "step",
        nargs="*",
        default=[],
        help="Given a workflow, the steps of the workflow it should run. If none are given, all steps are run.",
    )

    run_group.add_argument(
        "--workflow",
        "-w",
        type=Path,
        default=Path(
            os.environ.get("CIJOE_DEFAULT_WORKFLOW", DEFAULT_WORKFLOW_FILENAME)
        ),
        help=argparse.SUPPRESS,
    )
    run_group.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(os.environ.get("CIJOE_DEFAULT_CONFIG", DEFAULT_CONFIG_FILENAME)),
        help="Path to the Configuration file.",
        action=OverrideDefaultAction,
    )
    run_group.add_argument(
        "--output",
        "-o",
        type=Path,
        default=default_output_path(),
        help="Path to output directory.",
        action=OverrideDefaultAction,
    )
    run_group.add_argument(
        "--log-level",
        "-l",
        action="append_const",
        const=1,
        help="Increase log-level. Provide '-l' for info and '-ll' for debug.",
    )
    run_group.add_argument(
        "--monitor",
        "-m",
        action="store_true",
        help="Dump command output to stdout",
    )
    run_group.add_argument(
        "--no-report",
        "-n",
        action="store_true",
        help="Skip the producing, and opening, a report at the end of the workflow-run",
    )
    run_group.add_argument(
        "--skip-report",
        "-s",
        action="store_false",
        help="Skip the report opening at the end of the workflow-run",
    )
    run_group.add_argument(
        "--tag",
        "-t",
        type=str,
        action="append",
        help="Tags to identify a workflow-run."
        " This will be prefixed while storing in archive",
    )

    utils_group = parent_parser.add_argument_group(
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
        help="Check integrity of workflow given as positional argument and exit.",
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
        type=str,
        nargs="?",
        const="list_examples_and_exit",
        default=None,
        help=(
            "Emits the given example. When no example is given, "
            "then it prints a list of available examples."
        ),
    )
    utils_group.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Print the version number of 'cijoe' and exit.",
    )

    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).stem,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent_parser],
    )

    subparsers = parser.add_subparsers()

    # Create subparser for workflows
    subparsers.add_parser(
        "workflow_path", parents=[parent_parser], help="Path to a cijoe workflow file."
    )
    subparsers.add_parser("script_path", help="Path to a cijoe script.")
    subparsers.add_parser(
        "script_name",
        help="Name of a cijoe script. You can see all reachable cijoe scripts with command 'cijoe -r'.",
    )

    # Create subparser for scripts
    # Adding the subparser requires loading the whole script, so
    # we only add the subparser to the script given in the arguments
    if not is_workflow:
        for i, argv in enumerate(sys.argv):
            if i == 0 or argv.startswith("-") or sys.argv[i - 1].startswith("-"):
                continue

            # The first positional argument is the script identifier
            ident = argv

            script = resource_scripts.get(ident, None)
            if not script:
                log.error(f"Invalid target({ident})")
                return errno.EINVAL, None
            script.load()
            help_text = (
                next(line for line in script.docs.splitlines() if line)
                if script.docs
                else ""
            )
            subparser = subparsers.add_parser(
                ident,
                parents=[parent_parser],
                help=help_text,
                epilog=script.docs,
                formatter_class=argparse.RawTextHelpFormatter,
            )
            subparser.add_argument(
                "--script-name", default=ident, help=argparse.SUPPRESS
            )
            if script.argparser_func:
                script.argparser_func(subparser)

            break

    return 0, parser.parse_args()


def main(args=None):
    """Main entry point for the CLI"""

    if args is None:
        err, args = parse_args()
        if err:
            log.error("Couldn't parse args; exiting")
            return err
        if getattr(args, "script_name", None):
            # Running stand-alone script
            create_adhoc_workflow(args)

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

    if not getattr(args, "workflow", None):
        log.error("No target given; exiting")
        return errno.EINVAL

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
