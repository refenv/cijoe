#!/usr/bin/env python3
"""
    Resources
    =========

    The following constitutes the base-logic of CIJOE:

    * cijoe.core.command (Cijoe)
    * cijoe.core.transport (Transport, Local, SSH)
    * cijoe.core.misc (As the name suggests; various helper-functions)
    * cijoe.cli (Command-Line Tool and utilization of the above for task execution)

    Everything else, literally everything, is implemented as dynamically
    collectable and loadable resources. That is, cijoe
    configuration-files/scripts/tasks/templates, and auxiliary files.

    The base-representation of these resources are the cijoe.core.resources.Resource
    class, with content-specific subclasses (Config, Script, and Task).

    These resources are collected from installed and locally available Packages, as well
    as for path by the cijoe.core.resources.Collector.

    The Collector is a SingleTon, since it is used extensively everywhere and the tasks
    of doing collection can be somewhat time-consuming.

    Intended usage
    --------------

    From Python::

        from cijoe.core.resources import get_resources
        resources = get_resources()

    From command-line::

        cijoe --resources
"""
import ast
import importlib
import inspect
import logging as log
import os
import pkgutil
import re
import sys
from argparse import Namespace
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any, Dict, List, Union

try:
    from importlib.resources import files as importlib_files
except ImportError:
    from importlib_resources import files as importlib_files_fallback

    importlib_files = importlib_files_fallback

import jinja2
import yaml

import cijoe

if sys.version_info >= (3, 11):
    import tomllib  # Python 3.11 and newer
else:
    import tomli as tomllib  # For older Python versions

import tomli_w


def dict_from_yamlfile(path: Path):
    """Returns content of yamlfile at 'path' as dict and {} on empty document."""

    with path.open("rb") as yamlfile:
        return yaml.safe_load(yamlfile) or {}


def dict_from_tomlfile(path: Path):
    """Returns content of tomfile at 'path' as dict and {} on empty document."""

    with path.open("rb") as tomlfile:
        return tomllib.load(tomlfile) or {}


def dict_to_tomlfile(data, path: Path):
    """Dumps the given 'data' to the given 'path'"""

    with path.open("wb") as tomlfile:
        return tomli_w.dump(data, tomlfile)


def default_context(config=None, resources=None):
    """Return a default context for dict-substitution"""

    if resources is None:
        resources = get_resources()

    return {
        "local": {
            "env": os.environ,
        },
        "config": config.options if config else {},
        "resources": resources,
    }


# A {{ ... }} or {% ... %} that names the facts, or 'target', the facts of the
# default target, which exist once steps write them; 'config.x.facts' is not one
FACTS_REFERENCE = re.compile(r"\{[{%][^}]*(?<![\w.])(?:facts|target)\b")


def dict_substitute(topic: dict, context: dict, defer_facts: bool = False) -> list:
    """
    Traverse the given 'topic' replacing {{ foo.bar }} entities with ctx. values.

    With 'defer_facts', as when a task is loaded, a string referring to facts is
    only checked for syntax and left as it is, for its step to substitute when
    it starts; see facts_templates() and substitute_templates().
    """

    errors = []

    def render(text):
        if defer_facts and FACTS_REFERENCE.search(text):
            jinja_env.parse(text)
            return text
        return jinja_env.from_string(text).render(context)

    jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    for key, value in topic.items():
        try:
            if isinstance(value, str):
                topic[key] = render(value)
            elif isinstance(value, list):
                for i, entity in enumerate(value):
                    if isinstance(entity, str):
                        value[i] = render(entity)
                    elif isinstance(entity, dict):
                        errors += dict_substitute(entity, context, defer_facts)
            elif isinstance(value, dict):
                errors += dict_substitute(value, context, defer_facts)
        except jinja2.exceptions.TemplateError as exc:
            errors.append(f"Substitution-error: {exc}")

    return errors


def facts_templates(topic: dict) -> dict:
    """
    The strings of 'topic' that refer to facts, as written, where 'topic' has
    them: a list's by index. A step keeps them from before the task is
    substituted, so that what is substituted when it starts is what the task
    said, never a value that substitution produced.
    """

    templates: dict = {}
    for key, value in topic.items():
        if isinstance(value, str) and FACTS_REFERENCE.search(value):
            templates[key] = value
        elif isinstance(value, list):
            found: dict = {}
            for i, entity in enumerate(value):
                if isinstance(entity, str) and FACTS_REFERENCE.search(entity):
                    found[i] = entity
                elif isinstance(entity, dict) and (inner := facts_templates(entity)):
                    found[i] = inner
            if found:
                templates[key] = found
        elif isinstance(value, dict) and (inner := facts_templates(value)):
            templates[key] = inner

    return templates


def substitute_templates(topic: dict, templates: dict, context: dict) -> list:
    """Substitute 'templates', from facts_templates(), into 'topic' with 'context'"""

    errors = []

    jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    for key, template in templates.items():
        try:
            if isinstance(template, str):
                topic[key] = jinja_env.from_string(template).render(context)
            elif isinstance(topic[key], list):
                for i, entity in template.items():
                    if isinstance(entity, str):
                        topic[key][i] = jinja_env.from_string(entity).render(context)
                    else:
                        errors += substitute_templates(topic[key][i], entity, context)
            else:
                errors += substitute_templates(topic[key], template, context)
        except jinja2.exceptions.TemplateError as exc:
            errors.append(f"Substitution-error: {exc}")

    return errors


class Resource(object):
    """Base representation of a Resource"""

    def __init__(self, path: Path, pkg=None):
        self.path = path.resolve()
        self.pkg = pkg

        self.path = path
        self.content = None

        prefix = ".".join(pkg.name.split(".")[1:-1]) + "." if pkg else ""

        self.ident = f"{prefix}{self.path.stem}"

    def __repr__(self):
        return str(self.path)

    def content_from_file(self):
        """Load resource-content from 'self.path'"""

        with self.path.open("r") as resource_file:
            self.content = resource_file.read()


class Config(Resource):
    """
    Encapsulation of a CIJOE config-file, e.g. 'example_config_default.toml'

    ivar: options: dict of configuration options populated by load() / from_path()
    """

    SUFFIX = ".toml"

    def __init__(self, path: Path, pkg=None):
        super().__init__(path, pkg)

        self.options: Dict[str, Any] = {}

    def load(self):
        """Populates self.options on success. Returns a list of errors otherwise"""

        # config_dict = dict_from_yamlfile(self.path)
        config_dict = dict_from_tomlfile(self.path)

        errors = dict_substitute(config_dict, default_context())
        if errors:
            return errors

        if config_dict.get("cijoe", {}).get("transport", {}).get("initiator"):
            errors.append("The key cijoe.transport.initiator is reserved.")
            return errors

        if "facts" in config_dict:
            errors.append("The key facts is reserved; steps write facts, see --facts.")
            return errors

        self.options = config_dict
        return []

    @staticmethod
    def from_path(path, pkg=None):
        """Instantiate a Config from path, returning None on error"""

        path = Path(path).resolve()
        if not path.exists():
            return None

        config = Config(path, pkg)
        errors = config.load()
        if errors:
            return None

        return config


class Script(Resource):
    """Script representation and encapsulation"""

    SUFFIX = ".py"
    NAMING_CONVENTION = ["worklet_entry", "script_entry", "main"]
    ARGPARSER_FUNC = "add_args"

    def __init__(self, path, pkg=None):
        super().__init__(path, pkg)

        self.func = None
        self.argparser_func = None
        self.mod = None
        self.mod_name = None
        self.docs = None

    def content_has_script_func(self):
        """Checks whether the resource-content has the script entry-function"""

        try:
            tree = ast.parse(self.content)
        except SyntaxError:
            return False

        for node in [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]:
            if node.name not in Script.NAMING_CONVENTION:
                log.debug(f"skipping; invalid entry-name({node.name})")
                continue

            argnames = [arg.arg for arg in node.args.args]
            if argnames != ["args", "cijoe"]:
                log.debug(f"skipping; invalid argnames({argnames})")
                continue

            return True

        return False

    def content_has_argparser_func(self):
        """Checks whether the resource-content has a function to add cli arguments"""

        try:
            tree = ast.parse(self.content)
        except SyntaxError:
            return False

        for node in [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]:
            if node.name != Script.ARGPARSER_FUNC:
                log.debug(f"skipping; invalid argparser function name({node.name})")
                continue

            argnames = [arg.arg for arg in node.args.args]
            if argnames != ["parser"]:
                log.debug(f"skipping; invalid argnames({argnames})")
                continue

            return True

        return False

    def tools(self) -> dict:
        """
        The tools the script declares it needs on its target, as a module-level
        literal, 'TOOLS = {"fio": "3.38", "nvme": None}', tool to its least
        version or None for any, or per OS family, '{"*": {...}, "linux": {...}}'; read from the source, as the entry function is,
        so it is known before the script is run. Raises ValueError for a 'TOOLS'
        of another form.
        """

        if not self.content:
            self.content_from_file()

        from cijoe.core.tools import invalid

        for node in ast.parse(self.content or "").body:
            if isinstance(node, ast.Assign):
                names, value = [
                    getattr(t, "id", None) for t in node.targets
                ], node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                names, value = [getattr(node.target, "id", None)], node.value
            else:
                continue
            if names != ["TOOLS"]:
                continue
            try:
                tools = ast.literal_eval(value)
            except ValueError as exc:
                raise ValueError(f"{self.path}: TOOLS is not a literal") from exc
            problem = invalid(tools)
            if problem:
                raise ValueError(f"{self.path}: {problem}")
            return tools

        return {}

    def load(self):
        """Loads the module and the script-entry function"""

        if self.func:
            return []

        if not self.content:
            self.content_from_file()

        if not self.content_has_script_func():
            return ["Missing script_entry() function in ast"]

        has_argparser_func = self.content_has_argparser_func()

        path = Path(self.path).resolve()

        mod_path = str(path)
        mod_name = ".".join(
            [
                path.parent.parent.parent.stem,  # This should be cijoe
                path.parent.parent.stem,  # This should be the "package" name
                path.parent.stem,  # This should be "scripts"
                path.stem,  # This is the name of the module
            ]
        )

        parent_path = str(Path(self.path).resolve().parent)
        if parent_path not in sys.path:
            sys.path.append(parent_path)

        spec = importlib.util.spec_from_loader(
            mod_name, SourceFileLoader(mod_name, mod_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        docstring = mod.__doc__

        # mod = SourceFileLoader("", str(self.path)).load_module()
        for function_name, function in inspect.getmembers(mod, inspect.isfunction):
            if function_name == Script.ARGPARSER_FUNC and has_argparser_func:
                self.argparser_func = function

            if function_name not in Script.NAMING_CONVENTION:
                continue

            if self.func:
                continue

            self.mod = mod
            self.mod_name = mod_name
            self.func = function
            self.docs = docstring

        return ["Missing script_entry() function in loaded module"]


class Task(Resource):
    SUFFIX = ".yaml"
    STATE_FILENAME = "task.state"
    STATE: Dict[str, Any] = {
        "doc": "",
        "tag": "",
        "config": {},
        "steps": [],
        "status": {
            "skipped": 0,
            "failed": 0,
            "passed": 0,
            "elapsed": 0.0,
            "started": 0.0,
        },
    }

    def __init__(self, path, pkg=None):
        super().__init__(path, pkg)

        self.state = None
        self.config = None

    def state_dump(self, path):
        """Dump the current task-state to yaml-file"""

        with path.open("w+") as state_file:
            yaml.dump(self.state, state_file)

    @staticmethod
    def dict_normalize(topic: dict):
        """Normalize the task-dict, transformation of the 'run' shorthand"""

        errors = []

        if "steps" not in topic:
            errors.append("Missing required top-level key: 'steps'")
            return errors

        for step in topic["steps"]:
            if step["name"].endswith(".py"):
                errors.append(
                    "Illegal step name: Suffix .py reserved for Python scripts"
                )
                return errors

            if "run" not in step.keys():
                continue

            step["uses"] = "core.cmdrunner"

            if "with" not in step:
                step["with"] = {}

            if "commands" in step["with"]:
                errors.append(
                    "Cannot define step.run and step.with.commands simultaneously."
                )
                return errors

            # non-empty lines in "run"
            lines: filter[str] = filter(
                None, map(lambda s: s.strip(), step["run"].splitlines())
            )
            step["with"]["commands"] = []
            buffer = []

            for line in lines:
                buffer.append(line)
                if not line.strip().endswith("\\"):
                    step["with"]["commands"].append("\n".join(buffer))
                    buffer = []

            del step["run"]

        return errors

    @staticmethod
    def dict_lint(args: Namespace, topic: dict):
        """Returns a list of integrity-errors for the given task-dict(topic)"""

        resources = get_resources()

        errors = []

        for top in set(topic.keys()) - set(["doc", "config", "steps"]):
            errors.append(f"Unsupported top-level key: '{top}'")
            return errors
        for top in ["doc", "steps"]:
            if top not in topic:
                errors.append(f"Missing required top-level key: '{top}'")
                return errors

        step_names = []
        duplicate_names = []
        for step in topic["steps"]:
            if step["name"] in step_names:
                duplicate_names.append(step["name"])
            step_names.append(step["name"])

        if len(duplicate_names):
            errors.append(f"Duplicate step-names: {duplicate_names}")
            return errors

        valid = set(["name", "uses", "with"])
        required = set(["name", "uses"])

        for nr, step in enumerate(topic["steps"], 1):
            keys = set(step.keys())

            missing = required - keys
            if missing:
                errors.append(f"Invalid step({nr}); required key(s): {missing}")
                continue

            if not re.match(r"^([a-zA-Z][a-zA-Z0-9\.\-_]*)", step["name"]):
                errors.append(f"Invalid step({nr}); invalid chars in 'name'")
                continue

            unsupported = keys - valid
            if unsupported:
                errors.append(f"Invalid step({nr}); unsupported keys({unsupported})")
                continue

            if step["uses"] not in resources["scripts"]:
                errors.append(
                    f"Invalid step({nr}); unknown resource: script({step['uses']})"
                )
                continue

            if "with" in step:
                reserved = [key for key in step["with"] if key in args]
                if reserved:
                    errors.append(
                        f"Invalid step({nr}): 'with' keys reserved({','.join(reserved)})"
                    )
                    continue

                for key, value in step["with"].items():
                    if (
                        type(value) is dict
                        or type(value) is list
                        and any(type(el) in [dict, list] for el in value)
                    ):
                        errors.append(
                            f"Invalid step({nr}): 'with' values can only be primitive or lists of primitive types({key}: {value})"
                        )
                        continue

        return errors

    def load(self, args: Namespace, config: Config, extra_steps: list = []):
        """
        Load the task-yamlfile, normalize it, lint it, substitute, then construct
        the object properties
        """

        errors: List[Any] = []

        if self.state:
            return errors

        task_dict = dict_from_yamlfile(self.path)
        task_dict["steps"] += extra_steps

        errors += Task.dict_normalize(task_dict)
        if errors:
            return errors

        errors += Task.dict_lint(args, task_dict)
        if errors:
            return errors

        templates = [
            facts_templates(step.get("with", {})) for step in task_dict["steps"]
        ]

        errors += dict_substitute(task_dict, default_context(config), defer_facts=True)
        if errors:
            return errors

        for step, step_templates in zip(task_dict["steps"], templates):
            if step_templates:
                step["with_facts"] = step_templates

        state = Task.STATE.copy()
        state["doc"] = task_dict.get("doc")
        state["config"] = task_dict.get("config", {})
        state["steps"] = list(state["steps"])
        for nr, step in enumerate(task_dict["steps"], 1):
            step["nr"] = nr
            step["status"] = {
                "skipped": 0,
                "passed": 0,
                "failed": 0,
                "elapsed": 0.0,
                "started": 0.0,
            }
            step["id"] = f"{nr:03}_{step['name']}"

            state["steps"].append(step)

        self.state = state

        return errors


class Collector(object):
    """Collects resources from installed packages and the current working directory"""

    RESOURCES = [
        ("configs", Config.SUFFIX),
        ("templates", ".jinja2"),
        ("tasks", Task.SUFFIX),
        ("scripts", Script.SUFFIX),
        ("auxiliary", ".*"),
    ]
    LEGACY_CATEGORIES = {"workflows": "tasks"}
    IGNORE = ["__init__.py", "__pycache__", "setup.py"]

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Collector, cls).__new__(cls)
            cls.instance.reset()
        return cls.instance

    def __process_candidate(self, candidate: Path, category: str, pkg):
        """Inserts the given candidate"""

        resource: Union[Script, Config, Task, Resource]

        if category == "scripts":
            resource = Script(candidate, pkg)
            resource.content_from_file()

            if not resource.content_has_script_func():
                category = "auxiliary"
        elif category == "configs":
            resource = Config(candidate, pkg)
        elif category == "tasks":
            resource = Task(candidate, pkg)
        else:
            resource = Resource(candidate, pkg)

        self.resources[category][resource.ident] = resource

    def reset(self):
        self.resources = {category: {} for category, _ in Collector.RESOURCES}
        self.is_done = False

    def collect_from_path(self, path=None, max_depth=2):
        """Collects non-packaged scripts from the given 'path'"""

        path = Path(path).resolve() if path else Path.cwd().resolve()

        base = len(str(path).split(os.sep))

        for candidate in list(path.glob("*")) + list(path.glob("*/*")):
            level = len(str(candidate).split(os.sep))
            if max_depth and level > base + max_depth:
                continue

            if candidate.parent.stem == "auxiliary":
                self.__process_candidate(candidate, "auxiliary", None)
                continue

            for category, suffix in Collector.RESOURCES:
                if candidate.name in Collector.IGNORE:
                    continue
                if candidate.suffix != suffix:
                    continue

                self.__process_candidate(candidate, category, None)

    def collect_from_packages(self, path=None, prefix=None):
        """Collect resources from CIJOE packages at the given 'path'"""

        if prefix is None:
            prefix = ""

        canonical_categories = {cat for cat, _ in Collector.RESOURCES}

        for pkg in pkgutil.walk_packages(path, prefix):
            comp = pkg.name.split(".")[1:]  # drop the 'cijoe.' prefix
            if not (pkg.ispkg and len(comp) == 2):
                continue

            _, category = comp
            if category in Collector.LEGACY_CATEGORIES:
                log.warning(
                    f"package({pkg.name}): "
                    f"'{category}/' subdir is deprecated; "
                    f"rename to '{Collector.LEGACY_CATEGORIES[category]}/'"
                )
                category = Collector.LEGACY_CATEGORIES[category]
            elif category not in canonical_categories:
                continue

            for candidate in importlib_files(f"{pkg.name}").iterdir():
                if candidate.name in Collector.IGNORE:
                    continue

                self.__process_candidate(candidate, category, pkg)

    def collect(self, paths=[]):
        """Collect from all implemented resource "sources" """

        if self.is_done:
            return

        self.collect_from_packages(cijoe.__path__, "cijoe.")
        self.collect_from_path()

        for path in paths:
            self.collect_from_path(path, 0)

        cwd = Path().cwd() / ".cijoe"
        if cwd.exists():
            self.collect_from_path(cwd)

        home = Path().home() / ".cijoe"
        if home.exists():
            self.collect_from_path(home)

        self.is_done = True


def get_resources(paths=[]):
    """Returns resources collected by Collector"""

    collector = Collector()
    collector.collect(paths)

    return collector.resources


# Deprecated alias for backwards compatibility; prefer Task.
Workflow = Task
