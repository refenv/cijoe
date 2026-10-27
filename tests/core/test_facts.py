import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from cijoe.core.command import Cijoe
from cijoe.core.facts import Facts
from cijoe.core.processing import facts_written
from cijoe.core.resources import (
    Config,
    dict_from_tomlfile,
    dict_from_yamlfile,
    dict_substitute,
    facts_templates,
    substitute_templates,
)


def at_load_and_at_the_step(topic: dict, config: dict, facts: dict):
    """Substitute 'topic' as a step's 'with' is: at task load, then when it starts"""

    templates = facts_templates(topic)
    loaded = dict_substitute(topic, {"config": config}, defer_facts=True)
    if loaded:
        return loaded
    return substitute_templates(topic, templates, {"config": config, "facts": facts})


# A script in the run's directory, which cijoe collects as 'write_fact'
WRITE_FACT = '''"""
Write a fact
============

Sets the fact 'key' to 'value'.

Retargetable: false
-------------------
"""
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument("--key", type=str)
    parser.add_argument("--value", type=str)
    parser.add_argument("--facts", type=str, default="")


def main(args, cijoe):
    cijoe.facts.set(args.key, args.value)
    return 0
'''


def test_facts_set_get_update_delete_save(tmp_path):
    facts = Facts(tmp_path / "facts.toml")

    facts.set("guest.devices.nvme0", {"bdf": "0000:01:00.0", "serial": "beef0000"})
    facts.update("guest.devices.nvme0", {"controller": "nvme9"})
    assert facts.get("guest.devices.nvme0.bdf") == "0000:01:00.0"
    assert facts.get("guest.devices.nvme0.controller") == "nvme9"
    assert facts.get("guest.devices.gpu0.bdf", "absent") == "absent"
    assert facts.get("guest.devices.nvme0.bdf.deeper") is None

    facts.set("guest.kernel", "7.3.0")
    facts.delete("guest.devices.nvme0")
    facts.delete("guest.never.there")
    assert facts.get("guest.devices") == {}
    assert facts.changed == {"guest.devices.nvme0", "guest.kernel"}

    assert dict_from_tomlfile(tmp_path / "facts.toml") == {
        "guest": {"devices": {}, "kernel": "7.3.0"}
    }
    assert not list(tmp_path.glob(".*partial")), "a write leaves no partial file"


def test_config_refuses_a_facts_table(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[facts.guest]\nkernel = "7.3.0"\n')

    errors = Config(path).load()
    assert errors and "facts is reserved" in errors[0]


def test_substitution_leaves_facts_to_the_step():
    step = {"commands": ["echo {{ facts.guest.kernel }}", "echo {{ config.x }}"]}

    assert dict_substitute(step, {"config": {"x": "a"}}, defer_facts=True) == []
    assert step["commands"] == ["echo {{ facts.guest.kernel }}", "echo a"]

    step = {"commands": ["echo {{ facts.guest.kernel }}", "echo {{ config.x }}"]}
    facts = {"guest": {"kernel": "7.3.0"}}
    assert at_load_and_at_the_step(step, {"x": "a"}, facts) == []
    assert step["commands"] == ["echo 7.3.0", "echo a"]


def test_config_is_substituted_whole_and_refers_to_no_facts(tmp_path, monkeypatch):
    monkeypatch.setenv("facts", "v")
    path = tmp_path / "config.toml"
    path.write_text('[x]\nref = "{{ local.env.facts }}"\n')
    config = Config(path)
    assert config.load() == []
    assert config.options["x"]["ref"] == "v", "the word facts is no reference"

    path.write_text('[x]\nref = "{{ facts.guest.kernel }}"\n')
    assert Config(path).load(), "facts do not exist when a config is loaded"


def run(cwd: Path, task: dict, *extra, config="") -> subprocess.CompletedProcess:
    (cwd / "write_fact.py").write_text(WRITE_FACT)
    (cwd / "task.yaml").write_text(yaml.dump(task))
    (cwd / "config.toml").write_text(config)

    # core.testrunner runs 'pytest' from PATH: the one beside this cijoe
    path = f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"

    return subprocess.run(
        ["cijoe", "task.yaml", "--config", "config.toml", "--report-skip", *extra],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": path},
    )


TASK = {
    "doc": "A fact one step writes, which the next step reads",
    "steps": [
        {
            "name": "observe",
            "uses": "write_fact",
            "with": {"key": "guest.kernel", "value": "7.3.0"},
        },
        {"name": "read", "run": 'test "{{ facts.guest.kernel }}" = "7.3.0"'},
    ],
}


def test_a_step_reads_the_facts_an_earlier_step_wrote(tmp_path):
    result = run(tmp_path, TASK, "--output", "first")
    assert result.returncode == 0, result.stderr

    state = dict_from_yamlfile(tmp_path / "first" / "task.state")
    assert [step["facts"] for step in state["steps"]] == [["guest.kernel"], []]
    facts = dict_from_tomlfile(tmp_path / "first" / "facts.toml")
    assert facts["guest"] == {"kernel": "7.3.0"}


def test_a_run_starts_from_an_earlier_runs_facts(tmp_path):
    assert run(tmp_path, TASK, "--output", "first").returncode == 0

    reader = {"doc": "Reads a fact", "steps": [TASK["steps"][1]]}
    facts = str(tmp_path / "first" / "facts.toml")

    same = run(tmp_path, reader, "--output", "same", "--facts", facts)
    assert same.returncode == 0, same.stderr
    assert "another config" not in same.stderr

    other = run(
        tmp_path, reader, "--output", "other", "--facts", facts, config="[x]\ny=1\n"
    )
    assert other.returncode == 0, other.stderr
    assert "another config" in other.stderr


@pytest.mark.parametrize("seed", [None, "missing.toml"])
def test_a_missing_fact_fails_its_step(tmp_path, seed):
    reader = {"doc": "Reads a fact", "steps": [TASK["steps"][1]]}
    extra = ["--facts", str(tmp_path / seed)] if seed else []

    result = run(tmp_path, reader, "--output", "out", *extra)
    assert result.returncode != 0


def test_the_facts_example_runs(tmp_path):
    emitted = subprocess.run(["cijoe", "--example", "core.facts"], cwd=tmp_path)
    assert emitted.returncode == 0

    example = tmp_path / "cijoe-example-core.facts"
    result = subprocess.run(
        ["cijoe", "--report-skip", "--output", "out"],
        cwd=example,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    target = dict_from_tomlfile(example / "out" / "facts.toml")["targets"]["initiator"]
    assert target["system"]["cpus"] >= 1 and target["kernel"]["release"]
    assert target["os"]["family"], "the OS family is recorded"
    state = dict_from_yamlfile(example / "out" / "task.state")
    assert "targets.initiator.kernel" in state["steps"][0]["facts"]


def test_a_write_toml_cannot_hold_changes_nothing(tmp_path):
    facts = Facts(tmp_path / "facts.toml")
    facts.set("guest.kernel", "7.3.0")

    with pytest.raises(TypeError):
        facts.set("guest.ip", None)
    with pytest.raises(TypeError):
        facts.update("guest", {"ips": {1: "a"}})
    with pytest.raises(TypeError):
        facts.update("guest.kernel", "not a table")

    assert facts.data == {"guest": {"kernel": "7.3.0"}}
    assert facts.changed == {"guest.kernel"}
    assert not list(tmp_path.glob(".*partial"))
    facts.set("guest.cpus", 4)
    assert dict_from_tomlfile(tmp_path / "facts.toml") == {
        "guest": {"kernel": "7.3.0", "cpus": 4}
    }


def test_facts_merge_a_table_at_the_root(tmp_path):
    facts = Facts(tmp_path / "facts.toml", {"guest": {"kernel": "7.3.0"}})
    facts.merge({"guest": {"cpus": 4}, "tests": {"passed": 3}})

    assert facts.data == {
        "guest": {"kernel": "7.3.0", "cpus": 4},
        "tests": {"passed": 3},
    }
    assert facts.changed == {"guest.cpus", "tests.passed"}

    facts.changed.clear()
    facts.merge({"guest": {"kernel": "7.3.0"}})
    assert facts.changed == set(), "a merge that changes nothing records nothing"


def test_facts_get_returns_a_copy(tmp_path):
    facts = Facts(tmp_path / "facts.toml", {"guest": {"cpus": 4, "ips": ["a"]}})

    facts.get("guest")["cpus"] = 8
    facts.get("guest.ips").append("b")
    assert facts.data == {"guest": {"cpus": 4, "ips": ["a"]}}


def test_a_cijoe_without_facts_has_those_already_saved(tmp_path):
    (tmp_path / "config.toml").write_text("")
    Facts(tmp_path / "out" / "facts.toml", {"guest": {"kernel": "7.3.0"}}).save()

    cijoe = Cijoe(Config.from_path(tmp_path / "config.toml"), tmp_path / "out", False)
    assert cijoe.facts.get("guest.kernel") == "7.3.0"
    cijoe.facts.set("guest.cpus", 4)
    assert dict_from_tomlfile(tmp_path / "out" / "facts.toml") == {
        "guest": {"kernel": "7.3.0", "cpus": 4}
    }


def test_a_value_is_substituted_once():
    # Values a template produces, which read as templates themselves, stay as they are
    step = {
        "commands": [
            "echo {{ config.literal }}",
            "echo {{ config.mentions }}",
            "echo {{ facts.x }} {{ config.y }}",
        ],
        "nested": {"items": [{"v": "{{ facts.x }}"}, {"v": "{{ config.y }}"}]},
    }
    config = {"literal": "{{ literal }}", "mentions": "{{ facts.x }}", "y": "b"}

    assert at_load_and_at_the_step(step, config, {"x": "a"}) == []
    assert step["commands"] == ["echo {{ literal }}", "echo {{ facts.x }}", "echo a b"]
    assert step["nested"]["items"] == [{"v": "a"}, {"v": "b"}]


def test_facts_in_blocks_are_left_to_the_step():
    step = {"commands": ["{% if facts.gpu %}echo gpu{% endif %}"]}

    assert at_load_and_at_the_step(step, {}, {"gpu": True}) == []
    assert step["commands"] == ["echo gpu"]


def test_a_broken_reference_to_facts_is_an_error_at_load_and_at_the_step():
    syntax = {"commands": ["echo {{ facts.x }} {% if %}"]}
    assert dict_substitute(syntax, {"config": {}}, defer_facts=True), "at load"

    unknown_filter = {"commands": ["echo {{ facts.x | nosuchfilter }}"]}
    assert at_load_and_at_the_step(unknown_filter, {}, {"x": 1}), "at the step"

    missing = {"commands": ["echo {{ facts.x }}"]}
    assert at_load_and_at_the_step(missing, {}, {}), "at the step"


def test_an_environment_value_is_not_rendered_again(tmp_path, monkeypatch):
    task = copy.deepcopy(TASK)
    task["steps"].append({"name": "env", "run": 'test "{{ local.env.E }}" = "$E"'})

    monkeypatch.setenv("E", "{{ facts.guest.kernel }}")
    result = run(tmp_path, task, "--output", "out")
    assert result.returncode == 0, result.stderr


def test_a_script_may_take_a_facts_argument(tmp_path):
    task = copy.deepcopy(TASK)
    task["steps"][0]["with"]["facts"] = "its own"

    result = run(tmp_path, task, "--output", "out")
    assert result.returncode == 0, result.stderr


TESTS_USING_FACTS = """
from pathlib import Path


def test_reads_and_writes_facts(cijoe):
    assert cijoe.facts.get("guest.kernel") == "7.3.0"
    cijoe.facts.set("from_tests.answer", 42)

    # Another facts.toml among the tests' artifacts is not the tests' facts
    stray = Path(cijoe.output_path) / "artifacts" / "facts.toml"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text("stray = 1\\n")
"""


def test_tests_read_the_runs_facts_and_theirs_reach_the_run(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_facts_user.py").write_text(TESTS_USING_FACTS)
    task = copy.deepcopy(TASK)
    task["steps"] += [
        {
            "name": "tests",
            "uses": "core.testrunner",
            "with": {"run_local": True, "random_order": False, "args": "tests"},
        },
        {"name": "after", "run": "test {{ facts.from_tests.answer }} -eq 42"},
    ]

    result = run(tmp_path, task, "--output", "out")
    assert result.returncode == 0, result.stderr

    state = dict_from_yamlfile(tmp_path / "out" / "task.state")
    assert state["steps"][2]["facts"] == ["from_tests.answer"], "what tests changed"
    assert "stray" not in dict_from_tomlfile(tmp_path / "out" / "facts.toml")


def test_the_report_shows_who_wrote_each_fact(tmp_path):
    facts = Facts(tmp_path / "facts.toml", {"guest": {"kernel": "7.3.0", "cpus": 4}})
    steps = [
        {"name": "observe", "facts": ["guest"]},
        {"name": "count", "facts": ["guest.cpus"]},
        {"name": "read", "facts": []},
    ]

    assert facts_written(facts, steps) == [
        {"key": "guest.kernel", "value": "7.3.0", "step": "observe"},
        {"key": "guest.cpus", "value": 4, "step": "count"},
    ]
    assert steps[1]["extras"]["facts"] == {"guest.cpus": 4}
    assert steps[2]["extras"]["facts"] == {}


def test_mixed_lists_substitute_their_strings():
    step = {"vals": ["{{ facts.x }}", 3, "{{ config.y }}", {"v": "{{ facts.x }}"}]}

    assert at_load_and_at_the_step(step, {"y": "b"}, {"x": "a"}) == []
    assert step["vals"] == ["a", 3, "b", {"v": "a"}]


def test_a_corrupt_facts_file_is_named(tmp_path):
    (tmp_path / "facts.toml").write_text("not toml =")

    with pytest.raises(ValueError, match="facts.toml"):
        Facts.load(tmp_path / "facts.toml")


def test_the_report_marks_deleted_facts(tmp_path):
    facts = Facts(tmp_path / "facts.toml", {"guest": {"cpus": 4}})
    steps = [{"name": "observe", "facts": ["guest.cpus", "guest.kernel"]}]

    facts_written(facts, steps)
    assert steps[0]["extras"]["facts"] == {"guest.cpus": 4, "guest.kernel": "(deleted)"}


def test_a_corrupt_facts_file_ends_a_report_or_tests_with_its_name(tmp_path):
    assert run(tmp_path, TASK, "--output", "out").returncode == 0
    (tmp_path / "out" / "facts.toml").write_text("not toml =")

    report = subprocess.run(
        ["cijoe", "--report-only", "--output", "out"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert report.returncode != 0
    assert "facts.toml" in report.stderr and "Traceback" not in report.stderr

    (tmp_path / "test_nothing.py").write_text("def test_nothing():\n    pass\n")
    tests = subprocess.run(
        [str(Path(sys.executable).parent / "pytest"), "test_nothing.py"]
        + ["--config", "config.toml", "--output", "out"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert tests.returncode != 0
    assert "facts.toml" in tests.stderr and "INTERNALERROR" not in tests.stderr


def test_the_report_shows_listed_facts_as_yaml(tmp_path):
    subprocess.run(["cijoe", "--example", "core.facts"], cwd=tmp_path, check=True)
    example = tmp_path / "cijoe-example-core.facts"
    result = subprocess.run(
        ["cijoe", "--output", "out"], cwd=example, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr

    report = (example / "out" / "report.html").read_text()
    pane = report[report.index('id="facts-tab-pane"') :]
    assert "<td><code>[{" not in pane, "a list is not shown as its repr"


def test_every_run_records_the_initiator(tmp_path):
    reader = {
        "doc": "Reads the initiator",
        "steps": [
            {"name": "read", "run": 'test -n "{{ facts.targets.initiator.os.family }}"'}
        ],
    }

    result = run(tmp_path, reader, "--output", "on")
    assert result.returncode == 0, result.stderr
    initiator = dict_from_tomlfile(tmp_path / "on" / "facts.toml")["targets"][
        "initiator"
    ]
    assert set(initiator) >= {"os", "kernel", "system"}
    assert "pci" not in initiator, "only the cheap sections by default"

    off = run(
        tmp_path, TASK, "--output", "off", config="[cijoe.facts]\ninitiator = []\n"
    )
    assert off.returncode == 0, off.stderr
    assert "targets" not in dict_from_tomlfile(tmp_path / "off" / "facts.toml")


def test_the_initiators_facts_are_not_artifacts_and_have_a_writer(tmp_path):
    from cijoe.core.processing import facts_written

    result = run(tmp_path, TASK, "--output", "out")
    assert result.returncode == 0, result.stderr
    out = tmp_path / "out"
    assert not list((out / "artifacts").glob("cmd_*")), "not in the artifacts"
    assert list((out / "initiator").glob("cmd_*.output"))

    state = dict_from_yamlfile(out / "task.state")
    assert "targets.initiator.os" in state["facts_at_start"]
    facts = Facts.load(out / "facts.toml")
    start = {"name": "(start of run)", "facts": state["facts_at_start"]}
    rows = facts_written(facts, [start] + state["steps"])
    kernel = [r for r in rows if r["key"] == "targets.initiator.kernel.release"]
    assert kernel and kernel[0]["step"] == "(start of run)"
