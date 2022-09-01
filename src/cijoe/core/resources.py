#!/usr/bin/env python3
"""
    Resources
    =========

    The following constitutes the base-logic of CIJOE:

    * cijoe.core.command (Cijoe)
    * cijoe.core.transport (Transport, Local, SSH)
    * jore.core.misc (As the name suggests; various helper-functions)
    * cijoe.cli (Command-Line Tool and utilization of the above for workflow execution)

    Everything else, literally everything, is implemented as a dynamically collectable
    and loadable resources. That is, configuration-files, worklets, workflows,
    templates, and auxilary files.

    The base-representation of these resources is the cijoe.core.resources.Resource
    class, with content-specific subclasses (Config, Worklet, and Workflow).

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
import os
import pkgutil
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

import jinja2
import setuptools  # noqa
import yaml

import cijoe


def dict_from_yamlfile(path: Path):
    """Returns content of yamlfile at 'path' as dict and {} on empty document."""

    with path.open() as yamlfile:
        return yaml.safe_load(yamlfile) or {}


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


def dict_substitute(topic: dict, context: dict) -> list:
    """Traverse the given 'topic' replacing {{ foo.bar }} entities with ctx. values"""

    errors = []

    jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    for key, value in topic.items():
        try:
            if isinstance(value, str):
                topic[key] = jinja_env.from_string(value).render(context)
            elif isinstance(value, list) and all(
                isinstance(line, str) for line in value
            ):
                topic[key] = [
                    jinja_env.from_string(line).render(context) for line in value
                ]
            elif isinstance(value, dict):
                errors += dict_substitute(value, context)
        except jinja2.exceptions.UndefinedError as exc:
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
    Encapsulation of a CIJOE config-file, e.g. 'default.config'

    ivar: options: dict of configuration options populated by load() / from_path()
    """

    SUFFIX = ".config"

    def __init__(self, path: Path, pkg=None):
        super().__init__(path, pkg)

        self.options = {}

    def load(self):
        """Populates self.options on success. Returns a list of errors otherwise"""

        config_dict = dict_from_yamlfile(self.path)

        errors = dict_substitute(config_dict, default_context())
        if errors:
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


class Worklet(Resource):
    """Worklet representation and encapsulation"""

    SUFFIX = ".py"
    NAMING_CONVENTION = "worklet_entry"

    def __init__(self, path, pkg=None):
        super().__init__(path, pkg)

        self.func = None
        self.mod = None
        self.mod_name = None

    def content_has_worklet_func(self):
        """Checks whether the resource-content has the worklet entry-function"""

        try:
            tree = ast.parse(self.content)
        except SyntaxError:
            return False

        for node in [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]:
            if node.name != Worklet.NAMING_CONVENTION:
                continue

            return True

        return False

    def load(self):
        """Loads the module and the worklet-entry function"""

        if self.func:
            return []

        if not self.content:
            self.content_from_file()

        if not self.content_has_worklet_func():
            return ["Missing worklet_entry() function in ast"]

        mod = SourceFileLoader("", str(self.path)).load_module()
        for function_name, function in inspect.getmembers(mod, inspect.isfunction):
            if function_name != Worklet.NAMING_CONVENTION:
                continue

            self.mod = mod
            self.mod_name = Path(self.path).stem
            self.func = function
            return []

        return ["Missing worklet_entry() function in loaded module"]


class Workflow(Resource):

    SUFFIX = ".workflow"
    STATE_FILENAME = "workflow.state"
    STATE = {
        "doc": "",
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
        """Dump the current workflow-state to yaml-file"""

        with path.open("w+") as state_file:
            yaml.dump(self.state, state_file)

    @staticmethod
    def dict_normalize(topic: dict):
        """Normalize the workflow-dict, transformation of the 'run' shorthand"""

        errors = []

        if "steps" not in topic:
            errors.append("Missing required top-level key: 'steps'")
            return errors

        for step in topic["steps"]:
            if "run" not in step.keys():
                continue

            step["uses"] = "core.cmdrunner"
            step["with"] = {"commands": step["run"].splitlines()}

            del step["run"]

        return errors

    @staticmethod
    def dict_lint(topic: dict):
        """Returns a list of integrity-errors for the given workflow-dict(topic)"""

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

            if step["uses"] not in resources["worklets"]:
                errors.append(
                    f"Invalid step({nr}); unknown resource: worklet({step['uses']})"
                )
                continue

        return errors

    def load(self, config: Config, extra_steps: list = []):
        """
        Load the workflow-yamlfile, normalize it, lint it, substitute, then construct
        the object properties
        """

        errors = []

        if self.state:
            return errors

        workflow_dict = dict_from_yamlfile(self.path)
        workflow_dict["steps"] += extra_steps

        errors += Workflow.dict_normalize(workflow_dict)
        if errors:
            return errors

        errors += Workflow.dict_lint(workflow_dict)
        if errors:
            return errors

        errors += dict_substitute(workflow_dict, default_context(config))
        if errors:
            return errors

        state = Workflow.STATE.copy()
        state["doc"] = workflow_dict.get("doc")
        state["config"] = workflow_dict.get("config", {})
        for nr, step in enumerate(workflow_dict["steps"], 1):
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
        ("perf_reqs", ".perfreq"),
        ("templates", ".html"),
        ("workflows", ".workflow"),
        ("worklets", Worklet.SUFFIX),
        ("auxilary", ".*"),
    ]
    IGNORE = ["__init__.py", "__pycache__", "setup.py"]

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Collector, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.resources = {category: {} for category, _ in Collector.RESOURCES}
        self.is_done = False

    def __process_candidate(self, candidate: Path, category: str, pkg):
        """Inserts the given candidate"""

        if category == "worklets":
            resource = Worklet(candidate, pkg)
            resource.content_from_file()

            if not resource.content_has_worklet_func():
                category = "auxilary"
        elif category == "configs":
            resource = Config(candidate, pkg)
        elif category == "workflows":
            resource = Workflow(candidate, pkg)
        else:
            resource = Resource(candidate, pkg)

        self.resources[category][resource.ident] = resource

    def collect_from_path(self, path=None, max_depth=2):
        """Collects non-packaged worklets from the given 'path'"""

        path = Path(path).resolve() if path else Path.cwd().resolve()

        base = len(str(path).split(os.sep))

        for candidate in list(path.glob("*")) + list(path.glob("*/*")):
            level = len(str(candidate).split(os.sep))
            if max_depth and level > base + max_depth:
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

        for pkg in pkgutil.walk_packages(path, prefix):
            comp = pkg.name.split(".")[1:]  # drop the 'cijoe.' prefix
            if not (
                pkg.ispkg
                and any(cat in comp for cat, _ in Collector.RESOURCES)
                and len(comp) == 2
            ):  # skip non-resource packages
                continue

            _, category = comp
            for candidate in importlib.resources.files(f"{pkg.name}").iterdir():
                if candidate.name in Collector.IGNORE:
                    continue

                self.__process_candidate(candidate, category, pkg)

    def collect(self):
        """Collect from all implemented resource "sources" """

        if self.is_done:
            return

        self.collect_from_packages(cijoe.__path__, "cijoe.")
        self.collect_from_path()
        self.is_done = True


def get_resources():
    """Returns resources collected by Collector"""

    collector = Collector()
    collector.collect()

    return collector.resources
