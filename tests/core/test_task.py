import copy
import subprocess
from argparse import Namespace
from pathlib import Path

import yaml

from cijoe.core.processing import runlog_from_path
from cijoe.core.resources import Task, dict_from_tomlfile, get_resources

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


def test_task_lint_substitutes_as_a_run_does(tmp_path):
    """The task sees 'config' and 'local', as it does when it is run"""

    config_path = (tmp_path / "test-config.toml").resolve()
    config_path.write_text('[example]\nvalue = "abc"\n')

    data = copy.deepcopy(TASK_SKELETON)
    data["steps"].append(
        {
            "name": "templated",
            "run": "echo {{ config.example.value }} {{ local.env.HOME }}",
        }
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


UNREACHABLE_DEFAULT = '[cijoe.targets.nowhere.ssh]\nhostname = "127.0.0.1"\nport = 1\n'


def test_task_step_target(tmp_path):
    """A step's 'target' is where it runs; the step after it is back on the
    default, here one that nothing answers on"""

    config_path = (tmp_path / "config.toml").resolve()
    config_path.write_text(UNREACHABLE_DEFAULT)

    data = {
        "doc": "Steps on a target of their own",
        "steps": [
            {"name": "local", "target": "initiator", "run": "echo hello"},
            {"name": "default", "run": "echo hello"},
        ],
    }
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))
    output_path = (tmp_path / "output").resolve()

    subprocess.run(
        ["cijoe", str(task_file), "-o", str(output_path), "-c", str(config_path)],
        cwd=str(tmp_path),
    )

    state = yaml.safe_load((output_path / "task.state").read_text())
    status = {step["name"]: step["status"] for step in state["steps"]}
    assert status["local"]["passed"] == 1
    assert status["default"]["failed"] == 1

    runlog = runlog_from_path(output_path / state["steps"][0]["id"])
    assert "hello" in list(runlog.values())[0]["output"]


def test_task_lint_step_target(tmp_path):
    """-i accepts a step 'target' the config describes, and no other"""

    config_path = (tmp_path / "config.toml").resolve()
    config_path.write_text(UNREACHABLE_DEFAULT)

    for target, returncode in [("nowhere", 0), ("initiator", 0), ("elsewhere", 22)]:
        data = copy.deepcopy(TASK_SKELETON)
        data["steps"][0]["target"] = target
        task_file = (tmp_path / "task.yaml").resolve()
        task_file.write_text(yaml.dump(data))

        result = subprocess.run(
            ["cijoe", str(task_file), "-i", "-c", str(config_path)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert result.returncode == returncode, result.stderr
        if returncode:
            assert "no target(elsewhere); known: nowhere, initiator" in result.stderr


def test_task_step_transport_is_a_deprecated_target(tmp_path):
    """A step's 'with: transport:' still picks where it runs, with a warning"""

    config_path = (tmp_path / "config.toml").resolve()
    config_path.write_text(UNREACHABLE_DEFAULT)

    data = {
        "doc": "A step on the initiator, the old way",
        "steps": [{"name": "local", "run": "true", "with": {"transport": "initiator"}}],
    }
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump(data))

    result = subprocess.run(
        ["cijoe", str(task_file), "-o", "output", "-c", str(config_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (
        "WARNING: core.cmdrunner's 'transport' is deprecated; use the step's 'target'"
        in result.stderr
    )


def run_task(tmp_path, steps):
    """Run 'steps' with UNREACHABLE_DEFAULT; their status by name, and the facts"""

    config_path = (tmp_path / "config.toml").resolve()
    config_path.write_text(UNREACHABLE_DEFAULT)
    task_file = (tmp_path / "task.yaml").resolve()
    task_file.write_text(yaml.dump({"doc": "Steps", "steps": steps}))

    subprocess.run(
        ["cijoe", str(task_file), "-o", "output", "-c", str(config_path)],
        cwd=str(tmp_path),
    )

    output = tmp_path / "output"
    state = yaml.safe_load((output / "task.state").read_text())
    status = {step["name"]: step["status"] for step in state["steps"]}
    facts = dict_from_tomlfile(output / "facts.toml")

    return state, status, facts


def test_task_step_target_facts(tmp_path):
    """{{ target.* }} in a step is about the step's target"""

    state, status, facts = run_task(
        tmp_path,
        [
            {
                "name": "local",
                "target": "initiator",
                "run": "echo family={{ target.os.family }}",
            },
            {"name": "default", "run": "echo family={{ target.os.family }}"},
        ],
    )
    family = facts["targets"]["initiator"]["os"]["family"]

    assert status["local"]["passed"] == 1
    runlog = runlog_from_path(tmp_path / "output" / state["steps"][0]["id"])
    assert f"family={family}" in list(runlog.values())[0]["output"]
    assert status["default"]["failed"] == 1, "'nowhere' has no facts to read"


def test_task_step_target_tools(tmp_path):
    """A script's TOOLS are checked on the step's target, and recorded there"""

    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "needs_sh.py").write_text(
        'TOOLS = {"sh": None}\n\n\ndef main(args, cijoe):\n    return 0\n'
    )

    _, status, facts = run_task(
        tmp_path, [{"name": "local", "target": "initiator", "uses": "needs_sh"}]
    )

    assert status["local"]["passed"] == 1
    assert facts["targets"]["initiator"]["tools"]["sh"]["found"]
    assert "nowhere" not in facts.get("targets", {})


def test_task_lint_step_target_is_a_name():
    topic = {
        "doc": "A step whose target is not a name",
        "steps": [{"name": "a", "uses": "core.cmdrunner", "target": ["guest"]}],
    }
    errors = Task.dict_lint(Namespace(), topic)
    assert errors == ["Invalid step(1); 'target' must be a target's name"]


def test_runlog_skips_files_that_only_look_like_commands(tmp_path):
    """A step may leave a file such as cmd_log.txt among its command files"""

    (tmp_path / "cmd_01.output").write_text("hello\n")
    (tmp_path / "cmd_01.state").write_text("err: 0\nis_done: true\n")
    (tmp_path / "cmd_log.txt").write_text("not a command\n")
    (tmp_path / "cmd_log.output").write_text("not a command\n")

    assert list(runlog_from_path(tmp_path)) == ["cmd_01"]


def test_task_state_starts_from_zero_for_each_load(tmp_path):
    """A task run in the same process does not start with an earlier run's counts"""

    resources = get_resources()
    config = resources["configs"]["core.example_config_default"]
    assert not config.load()

    path = tmp_path / "task.yaml"
    path.write_text(yaml.dump(TASK_SKELETON))

    first = Task(path)
    assert not first.load(Namespace(), config, [])
    first.state["status"]["failed"] += 1

    second = Task(path)
    assert not second.load(Namespace(), config, [])
    assert second.state["status"]["failed"] == 0
