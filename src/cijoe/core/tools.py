"""
Checking that a target has the tools a task needs, at the versions it needs.

Which tools a target has is a fact, kept as 'targets.<target>.tools.<tool>',
the tool's name with a dot as an underscore: its 'name', 'found', and when
found its 'path' and 'version'. A least version is a string of dotted numbers,
optionally with a pre-release such as 'rc1', which comes before its release; a
release with a bare letter, as OpenSSL's 1.0.2a, is given as its numbers. What a run needs is intent:
the configuration describes a tool once, as '[tools.<tool>]' with the command
that prints its version, 'version', by default '<tool> --version', and the
least version it must be, 'min'; a script declares the tools it needs as
'TOOLS', and core.tools_check checks those a step names. A tool whose facts
already satisfy what is needed is not asked again, so a run started with the
facts of an earlier one asks the target nothing it already knows.
"""

import re
import shlex
from typing import Optional

from cijoe.core.misc import powershell, sh

# A pre-release, such as 'rc1', 'beta' or 'a2'; a bare 'a' or 'b', as in
# OpenSSL's 1.0.2a, is a release, not a pre-release
PRE_RELEASE = r"(?:-?(?:(?:rc|alpha|beta|pre)\.?\d*|(?:a|b)\.?\d+))"

# A version as tools print it: dotted numbers, and a pre-release
VERSION = re.compile(r"\d+(?:\.\d+)+" + PRE_RELEASE + "?")

# A least version as configurations and TOOLS give it
LEAST = re.compile(r"\d+(?:\.\d+)*" + PRE_RELEASE + "?")

# The order of pre-releases, before the release, which is last
STAGES = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "pre": 2, "rc": 2}


def version_of(text: str) -> Optional[str]:
    """The first version in 'text', as tools print their versions, or None"""

    match = VERSION.search(text)
    return match.group(0) if match else None


def is_version(least) -> bool:
    """Whether 'least' is a least version cijoe can compare: a string, as a TOML
    float such as 5.10 would lose its zero"""

    return isinstance(least, str) and bool(LEAST.fullmatch(least))


def at_least(version: Optional[str], least: Optional[str]) -> bool:
    """Whether 'version' is 'least' or later, compared number by number, a
    pre-release before its release; any version will do when 'least' is None,
    and none when 'version' is"""

    if least is None:
        return True
    if version is None:
        return False

    def key(text):
        numbers = re.match(r"\d+(?:\.\d+)*", text).group(0)
        rest = re.match(r"-?([a-z]+)\.?(\d*)", text[len(numbers) :])
        if not rest:
            return [int(n) for n in numbers.split(".")], (len(STAGES), 0)
        stage, number = rest.groups()
        return [int(n) for n in numbers.split(".")], (STAGES[stage], int(number or 0))

    (have, have_stage), (want, want_stage) = key(version), key(least)
    width = max(len(have), len(want))
    have, want = have + [0] * (width - len(have)), want + [0] * (width - len(want))
    if have != want:
        return have > want

    return have_stage >= want_stage


def configured(cijoe):
    """The configuration's '[tools]', {} when there is none, and None when it is
    not a table"""

    tools = cijoe.getconf("tools", {}) or {}
    return tools if isinstance(tools, dict) else None


def described(cijoe, tool: str):
    """The configuration's '[tools.<tool>]', by the tool's exact name, as a name
    may hold a dot that getconf() would split; {} when there is none, and None
    when it, or '[tools]', is not a table"""

    tools = configured(cijoe)
    entry = tools.get(tool, {}) if tools is not None else None
    return entry if isinstance(entry, dict) else None


def wanted(cijoe, tools: dict):
    """'tools', tool to least version, with the configuration's '[tools.<tool>]'
    filling in a least version a declaration leaves open; and the problems with
    the configuration, one line per tool it describes wrongly"""

    found: dict = {}
    problems: list = []
    if configured(cijoe) is None:
        return found, ["tools: [tools] is not a table"]
    for tool, least in tools.items():
        entry = described(cijoe, tool)
        if entry is None:
            problems.append(f"{tool}: [tools.{tool}] is not a table")
            continue
        found[tool] = least if least is not None else entry.get("min")

    return found, problems


def fact_key(tool: str) -> str:
    """The key of a tool's facts: its name, with a dot, which a dotted key
    cannot hold, as an underscore, so python3.12 is kept as python3_12"""

    return tool.replace(".", "_")


def ask(cijoe, target: str, tool: str) -> dict:
    """The facts about 'tool' on 'target', asked of the target"""

    family = cijoe.facts.target(target).get("os.family")
    if family == "windows":
        name = tool.replace("'", "''")
        where = powershell(f"(Get-Command '{name}' -ErrorAction Stop).Source")
    else:
        where = sh(f"command -v {shlex.quote(tool)}")
    err, state = cijoe.run(where, transport_name=target)
    if err:
        return {"name": tool, "found": False}

    lines = state.output().strip().splitlines()
    found = {"name": tool, "found": True, "path": lines[0] if lines else tool}
    command = (described(cijoe, tool) or {}).get("version") or f"{tool} --version"
    err, state = cijoe.run(command, transport_name=target)
    text = state.output() if not err else ""
    version = version_of(text)
    if version:
        found["version"] = version
    elif text.strip():
        found["version_text"] = text.strip().splitlines()[0]

    return found


def check(cijoe, target: str, tools: dict, refresh: bool = False) -> list:
    """
    Check that 'target' has 'tools', tool to least version or None, recording
    what it has as facts; the problems, one line per tool, empty when it has
    them all. A tool whose facts satisfy what is needed is not asked again
    unless 'refresh'.
    """

    facts = cijoe.facts.target(target)
    wants, problems = wanted(cijoe, tools)
    for tool, least in wants.items():
        if least is not None and not is_version(least):
            problems.append(
                f"{tool}: least version {least!r} is not one; give it as a string"
                ' of dotted numbers, such as "5.10"'
            )
            continue
        key = f"tools.{fact_key(tool)}"
        known = facts.get(key)
        if (
            refresh
            or not known
            or not known.get("found")
            or not at_least(known.get("version"), least)
        ):
            known = ask(cijoe, target, tool)
            facts.set(key, known)

        need = f"{tool} >= {least}" if least else tool
        if not known.get("found"):
            problems.append(f"{need}, not found")
        elif not at_least(known.get("version"), least):
            have = known.get("version") or known.get("version_text", "no version")
            problems.append(f"{need}, found {have} ({known['path']})")

    return problems
