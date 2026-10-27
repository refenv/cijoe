import platform
import subprocess

import pytest
from test_tools import TASK, run

from cijoe.core.resources import Script, dict_from_tomlfile, dict_from_yamlfile


def test_scripts_declare_their_tools(tmp_path):
    def script(source):
        path = tmp_path / "declares.py"
        path.write_text(source + "\n\ndef main(args, cijoe):\n    return 0\n")
        return Script(path)

    assert script('TOOLS = {"fio": "3.38", "nvme": None}').tools() == {
        "fio": "3.38",
        "nvme": None,
    }
    assert script("X = 1").tools() == {}
    assert script('TOOLS: dict = {"fio": "3.38"}').tools() == {"fio": "3.38"}
    assert script('TOOLS = {"python": "3.14.0rc1"}').tools() == {"python": "3.14.0rc1"}
    with pytest.raises(ValueError, match="version string"):
        script('TOOLS = {"fio": "latest"}').tools()
    with pytest.raises(ValueError):
        script("TOOLS = make_tools()").tools()
    with pytest.raises(ValueError):
        script('TOOLS = ["fio"]').tools()


def test_a_step_lacking_tools_fails_before_its_script_runs(tmp_path):
    result = run(
        tmp_path, TASK, "-o", "out", tools='{"sh": None, "no-such-tool-x": None}'
    )

    assert result.returncode != 0
    assert "needs_tools needs, on target(initiator)" in result.stderr
    assert "no-such-tool-x, not found" in result.stderr
    assert not (tmp_path / "ran").exists(), "the script did not run"
    facts = dict_from_tomlfile(tmp_path / "out" / "facts.toml")
    assert facts["targets"]["initiator"]["tools"]["no-such-tool-x"] == {
        "name": "no-such-tool-x",
        "found": False,
    }


def test_a_step_with_its_tools_runs(tmp_path):
    result = run(tmp_path, TASK, "-o", "out", tools='{"sh": None}')

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "ran").exists()
    state = dict_from_yamlfile(tmp_path / "out" / "task.state")
    assert state["steps"][0]["tools"] == {"sh": None}


def test_the_integrity_check_lists_what_steps_need(tmp_path):
    run(tmp_path, TASK, "-o", "unused", tools='{"fio": "3.38", "nvme": None}')

    result = subprocess.run(
        ["cijoe", "task.yaml", "--config", "config.toml", "--integrity-check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "step(needs) needs: fio >= 3.38, nvme" in result.stdout


def test_a_float_least_version_fails_the_step_not_the_run(tmp_path):
    config = '[tools.sh]\nversion = "echo 5.2.1"\nmin = 5.0\n'
    result = run(tmp_path, TASK, "-o", "out", config=config, tools='{"sh": None}')

    assert result.returncode != 0
    assert "is not one; give it as a string" in result.stderr
    assert "Traceback" not in result.stderr
    assert dict_from_yamlfile(tmp_path / "out" / "task.state")["steps"][0]["status"][
        "failed"
    ]


def test_a_step_needs_the_tools_of_its_targets_os_family(tmp_path):
    here = platform.system().lower()
    other = "freebsd" if here != "freebsd" else "linux"

    tools = f'{{"*": {{"sh": None}}, "{other}": {{"no-such-tool-x": None}}}}'
    result = run(tmp_path, TASK, "-o", "out", tools=tools)
    assert result.returncode == 0, f"the initiator here is not {other}"

    tools = f'{{"*": {{"sh": None}}, "{here}": {{"no-such-tool-x": None}}}}'
    result = run(tmp_path, TASK, "-o", "here", tools=tools)
    assert result.returncode != 0 and "no-such-tool-x, not found" in result.stderr


def test_the_integrity_check_lists_tools_per_os_family(tmp_path):
    run(
        tmp_path,
        TASK,
        "-o",
        "unused",
        tools='{"*": {"fio": "3.38"}, "linux": {"nvme": None}}',
    )
    result = subprocess.run(
        ["cijoe", "task.yaml", "--config", "config.toml", "--integrity-check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert "step(needs) needs: fio >= 3.38; on linux: nvme" in result.stdout
