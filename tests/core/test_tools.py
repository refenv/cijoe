import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from cijoe.core.facts import Facts
from cijoe.core.resources import Script, dict_from_tomlfile, dict_from_yamlfile
from cijoe.core.tools import at_least, check, version_of


def test_versions_and_comparison():
    assert version_of("QEMU emulator version 10.2.1 (Debian 1:10.2.1+ds-1)") == "10.2.1"
    assert version_of("fio-3.38") == "3.38"
    assert version_of("no number here") is None

    assert at_least("10.2.1", "9.0") and at_least("3.38", "3.38")
    assert at_least("3.38.1", "3.38") and not at_least("3.37.9", "3.38")
    assert at_least(None, None) and not at_least(None, "1.0")


class Target:
    """A cijoe whose target has the tools in 'have', name to version output"""

    class State:
        def __init__(self, text):
            self.text = text

        def output(self):
            return self.text

    def __init__(self, have, tmp_path, config=None):
        self.have = have
        self.asked = []
        self.config = config or {}
        self.facts = Facts(tmp_path / "facts.toml")

    def getconf(self, key, default=None):
        node = self.config
        for name in key.split("."):
            if not isinstance(node, dict) or name not in node:
                return default
            node = node[name]
        return node

    def run(self, command, transport_name=None):
        self.asked.append(command)
        if "command -v " in command:
            tool = command.split("command -v ")[1].strip("'")
            if tool in self.have:
                return 0, Target.State(f"/usr/bin/{tool}\n")
            return 1, Target.State("")
        tool = command.split()[0]
        if tool in self.have:
            return 0, Target.State(self.have[tool])
        return 127, Target.State("")


def test_check_names_every_tool_missing_or_too_old(tmp_path):
    target = Target({"fio": "fio-3.33\n", "sh": ""}, tmp_path)

    problems = check(target, "guest", {"fio": "3.38", "nvme": None, "sh": None})
    assert problems == [
        "fio >= 3.38, found 3.33 (/usr/bin/fio)",
        "nvme, not found",
    ]
    assert target.facts.get("targets.guest.tools.fio") == {
        "name": "fio",
        "found": True,
        "path": "/usr/bin/fio",
        "version": "3.33",
    }
    assert target.facts.get("targets.guest.tools.nvme") == {
        "name": "nvme",
        "found": False,
    }


def test_known_tools_are_not_asked_again(tmp_path):
    target = Target({"fio": "fio-3.38\n"}, tmp_path)
    assert check(target, "guest", {"fio": "3.38"}) == []
    asked = len(target.asked)

    assert check(target, "guest", {"fio": "3.38"}) == []
    assert len(target.asked) == asked, "the facts answer"
    assert check(target, "guest", {"fio": "3.38"}, refresh=True) == []
    assert len(target.asked) > asked


def test_the_config_describes_a_tool(tmp_path):
    config = {"tools": {"qemu": {"version": "qemu --version", "min": "9.0"}}}
    target = Target({"qemu": "QEMU emulator version 8.2.2\n"}, tmp_path, config)

    assert check(target, "guest", {"qemu": None}) == [
        "qemu >= 9.0, found 8.2.2 (/usr/bin/qemu)"
    ]


DECLARES = '''"""
Needs tools
===========

Writes 'ran' when it runs.

Retargetable: false
-------------------
"""
from pathlib import Path

TOOLS = {TOOLS}


def main(args, cijoe):
    Path("ran").write_text("")
    return 0
'''


def run(cwd: Path, task: dict, *extra, config="", tools="{}"):
    (cwd / "needs_tools.py").write_text(DECLARES.replace("{TOOLS}", tools))
    (cwd / "task.yaml").write_text(yaml.dump(task))
    (cwd / "config.toml").write_text(config)
    path = f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"

    return subprocess.run(
        ["cijoe", "task.yaml", "--config", "config.toml", "--report-skip", *extra],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": path},
    )


TASK = {
    "doc": "A script that needs tools",
    "steps": [{"name": "needs", "uses": "needs_tools"}],
}


def test_tools_check_records_what_the_config_describes(tmp_path):
    task = {
        "doc": "Check tools",
        "steps": [{"name": "tools", "uses": "core.tools_check"}],
    }
    config = '[tools.sh]\nversion = "echo 5.2.1"\nmin = "5.0"\n'

    result = run(tmp_path, task, "-o", "out", config=config)
    assert result.returncode == 0, result.stderr
    sh = dict_from_tomlfile(tmp_path / "out" / "facts.toml")["targets"]["initiator"]
    assert sh["tools"]["sh"]["version"] == "5.2.1"

    too_old = '[tools.sh]\nversion = "echo 4.9"\nmin = "5.0"\n'
    result = run(tmp_path, task, "-o", "old", config=too_old)
    assert result.returncode != 0 and "sh >= 5.0, found 4.9" in result.stderr


def test_pre_releases_come_before_their_release():
    assert version_of("Python 3.14.0rc1") == "3.14.0rc1"
    assert not at_least("3.14.0rc1", "3.14.0")
    assert at_least("3.14.0", "3.14.0rc1") and at_least("3.14.0rc1", "3.14.0rc1")
    assert at_least("3.14.1rc1", "3.14.0")


def test_a_least_version_that_is_not_one_is_a_problem_not_a_crash(tmp_path):
    config = {"tools": {"sh": {"min": 5.0}, "fio": {"min": "latest"}, "nvme": "2.0"}}
    target = Target({"sh": "5.2\n", "fio": "fio-3.38\n"}, tmp_path, config)

    problems = check(target, "guest", {"sh": None, "fio": None, "nvme": None})
    assert problems[0] == "nvme: [tools.nvme] is not a table"
    assert len(problems) == 3
    assert all("is not one; give it as a string" in p for p in problems[1:])


def test_a_dotted_tool_name_is_one_fact(tmp_path):
    target = Target({"python3.12": "Python 3.12.4\n"}, tmp_path)

    assert check(target, "guest", {"python3.12": "3.12"}) == []
    tools = target.facts.get("targets.guest.tools")
    assert list(tools) == ["python3_12"] and tools["python3_12"]["name"] == "python3.12"


def test_tool_names_are_quoted(tmp_path):
    target = Target({}, tmp_path)
    check(target, "guest", {"a b;c": None})

    import shlex

    assert shlex.split(target.asked[0]) == ["sh", "-c", "command -v 'a b;c'"]


def test_a_release_with_a_letter_is_a_release_and_pre_releases_are_ordered():
    assert version_of("OpenSSL 1.0.2a  19 Mar 2015") == "1.0.2"
    assert not at_least("3.14.0a1", "3.14.0b1") and at_least("3.14.0b1", "3.14.0a1")
    assert not at_least("3.14.0rc1", "3.14.0rc2") and at_least("3.14.0rc2", "3.14.0rc1")
    assert at_least("3.14.0beta", "3.14.0a2")


def test_a_dotted_tool_name_finds_its_own_version_command(tmp_path):
    config = {"tools": {"python3.12": {"version": "python3.12 -V"}}}
    target = Target({"python3.12": "Python 3.12.4\n"}, tmp_path, config)

    assert check(target, "guest", {"python3.12": None}) == []
    assert "python3.12 -V" in target.asked


def test_tools_that_is_not_a_table_is_a_problem_not_a_crash(tmp_path):
    target = Target({"fio": "fio-3.38\n"}, tmp_path, {"tools": "fio"})

    assert check(target, "guest", {"fio": None}) == ["tools: [tools] is not a table"]


def test_declarations_per_os_family():
    from cijoe.core.tools import for_family, invalid, per_family

    tools = {
        "*": {"fio": "3.38"},
        "freebsd": {"nvmecontrol": None},
        "linux": {"nvme": "2.0"},
    }
    assert per_family(tools) and not per_family({"fio": "3.38"})
    assert for_family(tools, "freebsd") == {"fio": "3.38", "nvmecontrol": None}
    assert for_family(tools, "darwin") == {"fio": "3.38"}
    assert for_family({"fio": None}, "linux") == {"fio": None}
    assert invalid(tools) == ""
    assert "no OS family plan9" in invalid({"plan9": {"x": None}})
    assert "version string" in invalid({"linux": {"x": 5.0}})


def test_the_config_says_where_a_tool_is_needed(tmp_path):
    config = {"tools": {"pciconf": {"os": ["freebsd"]}}}
    target = Target({"uname": "Linux\n"}, tmp_path, config)
    target.facts.set("targets.guest.os.family", "linux")

    assert check(target, "guest", {"pciconf": None}) == [], "not needed on linux"
    target.facts.set("targets.guest.os.family", "freebsd")
    assert check(target, "guest", {"pciconf": None}) == ["pciconf, not found"]


def test_a_target_of_unknown_family_is_checked_for_every_tool_and_asked_once(tmp_path):
    config = {"tools": {"pciconf": {"os": ["freebsd"]}}}
    target = Target({}, tmp_path, config)

    assert check(target, "guest", {"pciconf": None}) == ["pciconf, not found"]
    assert target.facts.get("targets.guest.os.family") == "unknown"
    asked = len(target.asked)
    check(target, "guest", {"pciconf": None})
    assert not any("uname -s" == c for c in target.asked[asked:]), "asked once"


def test_os_must_be_a_list_of_families(tmp_path):
    for os_ in ("freebsd", ["plan9"]):
        config = {"tools": {"pciconf": {"os": os_}}}
        target = Target({}, tmp_path, config)
        problems = check(target, "guest", {"pciconf": None})
        assert problems and "is not a list of OS families" in problems[0]
