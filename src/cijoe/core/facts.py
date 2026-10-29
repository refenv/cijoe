"""
Facts are what the steps of a run observe, as the config is what is wanted: the
names a guest gave its devices, the kernel it booted, whether the host's IOMMU
translates. A script writes them with set(), update() and delete() on the
'facts' of the Cijoe it is given, and the steps after it read them with get()
and as '{{ facts.* }}' in their 'with'. Keys are dotted, as for getconf(), and
values are what TOML can hold. get() returns a copy, so the facts change only
through the calls that write them.

Facts about a machine are kept under 'targets.<name>', where the name is the
one the config gives the machine as 'cijoe.targets.<name>', or 'initiator',
whether it is a QEMU guest or hardware; target() reads and writes them, by
default for the target cijoe.run() reaches, and a task reads them as
'{{ target.* }}'.

Every write saves the whole set to 'facts.toml' in the output directory, so the
report shows what was observed, and a later run can start from it with
'--facts'. A fact never overrides config, and config never sets a fact.
"""

import copy
import os
import sys
from pathlib import Path
from typing import Any, Optional

import tomli_w

if sys.version_info >= (3, 11):
    import tomllib  # Python 3.11 and newer
else:
    import tomli as tomllib  # For older Python versions


class Facts(object):
    """The facts of a run, saved to 'path' on every write"""

    FILENAME = "facts.toml"

    def __init__(self, path: Path, data: Optional[dict] = None):
        self.path = Path(path)
        self.data: dict = data if data is not None else {}
        self.changed: set = set()
        self.default_target = "initiator"

    def target(self, name: Optional[str] = None):
        """The facts about the target 'name', by default the one cijoe.run()
        reaches, as 'targets.<name>'"""

        return TargetFacts(self, name or self.default_target)

    @staticmethod
    def load(path: Path):
        """The facts saved at 'path', or none when nothing is saved there yet"""

        path = Path(path)
        if not path.exists():
            return Facts(path)

        try:
            with path.open("rb") as tomlfile:
                return Facts(path, tomllib.load(tomlfile))
        except (OSError, ValueError) as exc:
            raise ValueError(f"facts({path}) cannot be read: {exc}") from exc

    def get(self, key: str, default: Any = None):
        """A copy of the value at the dotted 'key', or 'default' when there is none"""

        node: Any = self.data
        for name in key.split("."):
            if not isinstance(node, dict) or name not in node:
                return default
            node = node[name]

        return copy.deepcopy(node)

    def set(self, key: str, value: Any):
        """Set the dotted 'key' to 'value', replacing what was there"""

        data = copy.deepcopy(self.data)
        parent, name = parent_of(data, key)
        parent[name] = value
        self._commit(data, [key])

    def update(self, key: str, value: dict):
        """Merge 'value' into the table at the dotted 'key', table by table"""

        if not isinstance(value, dict):
            raise TypeError(f"update({key}): a table is merged, not {type(value)}")

        data = copy.deepcopy(self.data)
        parent, name = parent_of(data, key)
        if not isinstance(parent.get(name), dict):
            parent[name] = {}
        merge(parent[name], value)
        self._commit(data, [key])

    def merge(self, table: dict):
        """Merge 'table' into the facts, as 'facts.toml' of another run holds them;
        the keys it changed are its leaves whose values differ from the facts'"""

        changed = [key for key, value in leaves(table) if self.get(key) != value]
        if not changed:
            return

        data = copy.deepcopy(self.data)
        merge(data, table)
        self._commit(data, changed)

    def delete(self, key: str):
        """Remove the dotted 'key', when it is there"""

        names = key.split(".")
        parent = self.get(".".join(names[:-1])) if len(names) > 1 else self.data
        if isinstance(parent, dict) and names[-1] in parent:
            data = copy.deepcopy(self.data)
            parent, name = parent_of(data, key)
            del parent[name]
            self._commit(data, [key])

    def save(self, data: Optional[dict] = None):
        """
        Write the facts, or 'data' in their place, to 'path' whole, so a reader
        never sees half a write. Raises TypeError, writing nothing, when they hold
        a value TOML cannot.
        """

        text = tomli_w.dumps(self.data if data is None else data)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        partial = self.path.with_name(f".{self.path.name}.partial")
        partial.write_text(text, encoding="utf-8")
        os.replace(partial, self.path)

    def _commit(self, data: dict, keys: list):
        """Take 'data' as the facts once it is saved, so a write that TOML cannot
        hold leaves the facts as they were"""

        self.save(data)
        self.data = data
        self.changed.update(keys)


class TargetFacts(object):
    """The facts about one target, 'targets.<name>', with the calls of Facts on
    keys within it; the empty key is the target's whole table"""

    def __init__(self, facts: Facts, name: str):
        self.facts = facts
        self.name = name
        self.prefix = f"targets.{name}"

    def key(self, key: str) -> str:
        return f"{self.prefix}.{key}" if key else self.prefix

    def get(self, key: str = "", default: Any = None):
        return self.facts.get(self.key(key), default)

    def set(self, key: str, value: Any):
        self.facts.set(self.key(key), value)

    def update(self, key: str, value: dict):
        self.facts.update(self.key(key), value)

    def delete(self, key: str):
        self.facts.delete(self.key(key))


def parent_of(data: dict, key: str):
    """The table holding the dotted 'key' in 'data', made where missing, and its
    last name"""

    names = key.split(".")
    node = data
    for name in names[:-1]:
        if not isinstance(node.get(name), dict):
            node[name] = {}
        node = node[name]

    return node, names[-1]


def leaves(table: dict, prefix: str = ""):
    """The dotted keys of 'table' that hold values rather than tables, with them"""

    for name, value in table.items():
        key = f"{prefix}{name}"
        if isinstance(value, dict) and value:
            yield from leaves(value, f"{key}.")
        else:
            yield key, value


def merge(into: dict, value: dict):
    """Merge 'value' into 'into', recursing where both hold a table"""

    for key, val in value.items():
        if isinstance(val, dict) and isinstance(into.get(key), dict):
            merge(into[key], val)
        else:
            into[key] = val
