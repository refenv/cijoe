import copy
import subprocess
from argparse import Namespace
from pathlib import Path

import yaml

from cijoe.core.processing import runlog_from_path
from cijoe.core.resources import get_resources

TASK_SKELETON = {
    "doc": "Some description",
    "steps": [
        {"name": "foo", "uses": "core.example_script_default"},
    ],
}


def test_task_load():
    resources = get_resources()

    config = resources["configs"]["core.example_config_default"]
    assert config

    errors = config.load()
    assert not errors

    task = resources["tasks"]["core.example_task_default"]
    assert task

    errors = task.load(Namespace(), config, [])
    assert not errors


def test_task_lint_valid_task(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(TASK_SKELETON)

    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(task_file),
            "--integrity-check",
            "--config",
            str(config_path),
        ],
        cwd=str(tmp_path),
    )
    assert result.returncode == 0


def test_task_lint_invalid_step_name(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(TASK_SKELETON)
    data.get("steps", []).append(
        {"name": "cannot have spaces", "with": "core.example_script_default"}
    )

    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(task_file),
            "--integrity-check",
            "--config",
            str(config_path),
        ],
        cwd=str(tmp_path),
    )
    assert result.returncode != 0


def test_task_report_command_ordering(tmp_path):

    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(TASK_SKELETON)
    data["steps"].append(
        {
            "name": "many_commands",
            "uses": "core.example_script_default",
            "with": {"repeat": 100},
        }
    )

    output_path = (tmp_path / "output").resolve()
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(task_file),
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


def test_task_run(tmp_path):
    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(TASK_SKELETON)
    data["steps"].append(
        {
            "name": "cmdrunner",
            "run": """
                echo hello
                echo world
            """,
        }
    )

    output_path = (tmp_path / "output").resolve()
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(task_file),
            "--output",
            str(output_path),
            "--config",
            str(config_path),
        ],
        cwd=str(tmp_path),
    )
    assert result.returncode == 0

    runlog = runlog_from_path(output_path / "002_cmdrunner")

    assert len(runlog) == 2

    for i, v in enumerate(runlog.values()):
        if i == 0:
            assert "hello" in v["output"]
        elif i == 1:
            assert "world" in v["output"]


def test_task_run_multiline(tmp_path):
    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    data = copy.deepcopy(TASK_SKELETON)
    data["steps"].append(
        {
            "name": "cmdrunner",
            "run": """
                echo hello \
                  world
            """,
        }
    )

    output_path = (tmp_path / "output").resolve()
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        [
            "cijoe",
            str(task_file),
            "--output",
            str(output_path),
            "--config",
            str(config_path),
        ],
        cwd=str(tmp_path),
    )
    assert result.returncode == 0

    runlog = runlog_from_path(output_path / "002_cmdrunner")

    assert len(runlog) == 1
    assert "hello world" in runlog["cmd_01"]["output"]
