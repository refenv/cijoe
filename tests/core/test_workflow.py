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
        {"name": "foo", "uses": "core.example_script_default"},
    ],
}


def test_workflow_load():
    resources = get_resources()

    config = resources["configs"]["core.example_config_default"]
    assert config

    errors = config.load()
    assert not errors

    workflow = resources["workflows"]["core.example_workflow_default"]
    assert workflow

    errors = workflow.load(config, [])
    assert not errors


def test_workflow_lint_valid_workflow(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(WORKFLOW_SKELETON)

    workflow_file = (tmp_path / "workflow.yaml").resolve()
    workflow_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(workflow_file),
            "--integrity-check",
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
    data.get("steps", []).append(
        {"name": "cannot have spaces", "with": "core.example_script_default"}
    )

    workflow_file = (tmp_path / "workflow.yaml").resolve()
    workflow_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(workflow_file),
            "--integrity-check",
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
        {
            "name": "many_commands",
            "uses": "core.example_script_default",
            "with": {"repeat": 100},
        }
    )

    output_path = (tmp_path / "output").resolve()
    workflow_file = (tmp_path / "workflow.yaml").resolve()
    workflow_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(workflow_file),
            "--output",
            str(output_path),
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
