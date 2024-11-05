"""
    Helper functions for processing the output produced by a workflow
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Union

from cijoe.core.misc import ENCODING, sanitize_ident
from cijoe.core.resources import dict_from_yamlfile


def cmd_number_from_path(path):
    """Extracts the numerical part after 'cmd_' in the filename stem."""

    return int(path.stem.split("_")[1])


def runlog_from_path(path: Path):
    """Produce a dict of command-dicts with paths to .output and .state files"""

    run: Dict[str, Dict[str, Any]] = {}

    if not (path.is_dir() and path.exists()):
        return run

    for cmd_path in sorted(path.glob("cmd_*.*"), key=cmd_number_from_path):
        stem = cmd_path.stem
        suffix = cmd_path.suffix[1:]
        if suffix not in ["output", "state"]:
            continue

        if stem not in run:
            run[stem] = {
                "output_path": None,
                "output": "",
                "state": {},
                "state_path": None,
            }

        run[stem][f"{suffix}_path"] = cmd_path
        if suffix == "output":
            with run[stem][f"{suffix}_path"].open(
                encoding=ENCODING, errors="replace"
            ) as content:
                run[stem][f"{suffix}"] = content.read()
        elif suffix == "state":
            yaml_dict = dict_from_yamlfile(run[stem][f"{suffix}_path"])
            if not yaml_dict["is_done"]:
                yaml_dict["elapsed"] = time.time() - yaml_dict["begin"]
            run[stem][f"{suffix}"] = yaml_dict

    return run


def longrepr_to_string(longrepr):
    """Extract pytest crash/traceback/longrepr info from pytest structure"""

    lines = []

    lines.append("# crashinfo")
    reprcrash = longrepr.get("reprcrash", {})
    for key, value in reprcrash.items():
        lines.append(f"{key}: {value}")

    entries = longrepr.get("reprtraceback", {"reprentries": []}).get("reprentries", [])
    for entry in entries:
        if entry is None:
            continue

        data = entry.get("data")
        if data is None:
            continue

        reprfuncargs = data.get("reprfuncargs")
        if reprfuncargs is None:
            continue

        reprargs = reprfuncargs.get("args")
        if reprargs is None:
            continue

        lines.append("")
        lines.append("# test-args")

        for argline in reprargs:
            lines.append(":".join(argline))

        lines.append("")
        lines.append("# test-output-lines")
        for dataline in entry.get("data", {"lines": []}).get("lines", []):
            lines.append(dataline)

    return "\n".join(lines)


def testreport_from_file(path: Path):
    """Parse the given 'pytest-reportlog' output into a restreport dict"""

    results: Dict[str, Dict[str, Any]] = {
        "status": {"failed": 0, "passed": 0, "skipped": 0, "total": 0},
        "tests": {},
    }

    logpath = path / "testreport.log"
    if not logpath.exists():
        return {}

    with logpath.open() as logfile:
        for count, line in enumerate(logfile.readlines()):
            result = json.loads(line)
            if result["$report_type"] != "TestReport":
                continue

            nodeid: str = result["nodeid"]
            if nodeid not in results["tests"]:
                try:
                    comp = nodeid.split("::")
                    group_left = comp[0]
                    group_right = "".join(comp[1:])
                except Exception:
                    group_left, group_right = (nodeid, nodeid)

                results["tests"][nodeid] = {
                    "group_left": group_left,
                    "group_right": group_right,
                    "count": count,
                    "nodeid": nodeid,
                    "duration": 0.0,
                    "outcome": [],
                    "runlog": {},
                    "longrepr": "",
                }
            if isinstance(result["longrepr"], list):
                results["tests"][nodeid]["longrepr"] += "\n".join(
                    [str(item) for item in result["longrepr"]]
                )
            elif isinstance(result["longrepr"], dict):
                results["tests"][nodeid]["longrepr"] += longrepr_to_string(
                    result["longrepr"]
                )

            results["tests"][nodeid]["duration"] += result["duration"]
            results["tests"][nodeid]["outcome"] += [result["outcome"]]

            runlog = runlog_from_path(path / sanitize_ident(result["nodeid"]))
            if runlog:
                results["tests"][nodeid]["runlog"] = runlog

    for nodeid, testcase in results["tests"].items():
        results["status"]["total"] += 1
        for key in ["failed", "skipped", "passed"]:
            if key in testcase["outcome"]:
                results["status"][key] += 1
                break

    if results["status"]["total"]:
        return results

    return {}


def artifacts_in_path(path: Path):
    """Returns a list of paths to artifacts"""

    if not path.exists():
        return []

    artifacts = []
    for artifact_dir in Path(path).rglob("artifacts"):
        for artifact in artifact_dir.rglob("*"):
            artifacts.append(artifact.relative_to(path))

    return sorted(artifacts)


def process_workflow_output(args, cijoe):
    workflow_state = dict_from_yamlfile(args.output / "workflow.state")
    workflow_state["config"] = cijoe.config.options
    workflow_state["artifacts"] = artifacts_in_path(args.output)

    #    workflow_state["artifacts"] = artifacts_in_path(
    #        args.output, args.output / "artifacts"
    #    )

    for step in workflow_state["steps"]:
        if "extras" not in step:
            step["extras"] = {}

        if step["status"]["started"] > 0 and step["status"]["elapsed"] == 0:
            step["status"]["elapsed"] = time.time() - step["status"]["started"]

        step_path = args.output / step["id"]
        if not step_path.exists():
            continue

        # artifacts = artifacts_in_path(args.output, step_path / "artifacts")
        # artifacts = artifacts_in_path(step_path / "artifacts")
        # if artifacts:
        #    step["extras"]["artifacts"] = artifacts

        runlog = runlog_from_path(step_path)
        if runlog:
            step["extras"]["runlog"] = runlog

        testreport = testreport_from_file(step_path)
        if testreport:
            step["extras"]["testreport"] = testreport

    return workflow_state
