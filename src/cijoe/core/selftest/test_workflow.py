import copy
import subprocess
from pathlib import Path

import yaml

from cijoe.cli.cli import cli_integrity_check
from cijoe.core.processing import runlog_from_path
from cijoe.core.resources import get_resources

WORKFLOW_SKELETON = {
    "doc": "Some description",
    "steps": [
        {"name": "foo", "uses": "core.example"},
    ],
}


def test_workflow_load():
    resources = get_resources()

    config = resources["configs"]["core.default-config"]
    assert config

    errors = config.load()
    assert not errors

    workflow = resources["workflows"]["core.example-workflow"]
    assert workflow

    errors = workflow.load(config, [])
    assert not errors


def test_workflow_lint_valid_workflow(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(WORKFLOW_SKELETON)

    with (tmp_path / "workflow.yaml").resolve() as workflow_file:
        workflow_file.write_text(yaml.dump(data))

        result = subprocess.run(
            [
                "cijoe",
                "--integrity-check",
                "--workflow",
                str(workflow_file),
                "--config",
                str(config_path),
            ],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0


def test_workflow_lint_invalid_step_name(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(WORKFLOW_SKELETON)
    data.get("steps", []).append({"name": "cannot have spaces", "with": "core.example"})

    with (tmp_path / "workflow.yaml").resolve() as workflow_file:
        workflow_file.write_text(yaml.dump(data))

        result = subprocess.run(
            [
                "cijoe",
                "--integrity-check",
                "--workflow",
                str(workflow_file),
                "--config",
                str(config_path),
            ],
            cwd=str(tmp_path),
        )
        assert result.returncode != 0


def test_workflow_report_command_ordering(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(WORKFLOW_SKELETON)
    data["steps"].append(
        {"name": "many_commands", "uses": "core.example", "with": {"repeat": 100}}
    )

    output_path = (tmp_path / "output").resolve()
    with (tmp_path / "workflow.yaml").resolve() as workflow_file:
        workflow_file.write_text(yaml.dump(data))

        result = subprocess.run(
            [
                "cijoe",
                "--output",
                str(output_path),
                "--workflow",
                str(workflow_file),
                "--config",
                str(config_path),
            ],
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    for count, key in enumerate(
        runlog_from_path(output_path / "002_many_commands").keys(), 1
    ):
        val = int(Path(key).stem.split("_")[1])
        assert count == val
