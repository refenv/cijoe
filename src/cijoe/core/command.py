"""

"""

import logging as log
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from cijoe.core import transport
from cijoe.core.facts import Facts
from cijoe.core.misc import ENCODING, deprecated, sanitize_ident
from cijoe.core.resources import Config


def convert_str(value: str) -> Union[str, int, bool]:
    # Strip and lowercase the input to make checks more robust
    lower_value = value.lower().strip()

    # Check for boolean values
    if lower_value in ("true", "false"):
        return lower_value == "true"

    # Check for hexadecimal numbers (starting with '0x' or '0X')
    if lower_value.startswith("0x"):
        try:
            return int(value, 16)  # Convert hex to int
        except ValueError:
            pass  # In case the hex is invalid, we just fall through

    # Check for integer conversion (decimal numbers)
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    # If no conversion is possible, return the original string
    return value


def default_output_path():
    """Returns a default output-path"""

    return os.path.join(os.getcwd(), "cijoe-output")


class Tee:
    def __init__(self, file_path, monitor):
        self.file = open(file_path, "w")
        self.monitor = monitor
        self.buffer = []
        self.buffer_size = 0

    def write(self, data: bytes):
        decoded = data.decode(ENCODING, errors="replace")
        self.buffer.append(decoded)
        self.buffer_size += len(decoded)

        if "\n" in decoded or self.buffer_size >= 4096:
            self.flush()

    def flush(self):
        output = "".join(self.buffer)

        self.file.write(output)
        self.file.flush()

        if self.monitor:
            sys.stdout.write(output)
            sys.stdout.flush()

        self.buffer = []
        self.buffer_size = 0

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class CommandState(object):
    def __init__(self, cijoe, cmd, cwd, err, begin, end, is_done, monitor):
        self.cmd = cmd
        self.cwd = cwd
        self.err = err
        self.begin = begin
        self.end = end
        self.elapsed = end - begin
        self.is_done = is_done

        cmd_output_dpath = os.path.join(cijoe.output_path, cijoe.output_ident)
        cmd_output_fpath = os.path.join(
            cmd_output_dpath, f"cmd_{cijoe.run_count:02}.output"
        )
        cmd_state_fpath = os.path.join(
            cmd_output_dpath, f"cmd_{cijoe.run_count:02}.state"
        )
        os.makedirs(cmd_output_dpath, exist_ok=True)

        self.output_dpath = Path(cmd_output_dpath)
        self.output_fpath = Path(cmd_output_fpath)
        self.state_fpath = Path(cmd_state_fpath)

        self.cmd_output = Tee(self.output_fpath, monitor)

    def output(self):
        """Returns the content of 'output_fpath'"""

        with self.output_fpath.open() as ofd:
            return ofd.read()

    def to_file(self):
        """Dump the command state to file"""

        with self.state_fpath.open("w", encoding=ENCODING) as state_file:
            state = {
                "cmd": self.cmd,
                "cwd": str(self.cwd),
                "err": self.err,
                "begin": self.begin,
                "end": self.end,
                "elapsed": self.elapsed,
                "output_dpath": str(self.output_dpath),
                "output_fpath": str(self.output_fpath),
                "is_done": self.is_done,
            }
            yaml.dump(state, state_file)


class Cijoe(object):
    """CIJOE providing retargetable command-line expressions and data-transfers"""

    def __init__(
        self,
        config: Config,
        output_path: Path,
        monitor: bool,
        facts: Optional[Facts] = None,
    ):
        """Create a cijoe encapsulation defined by the given config_fpath"""

        self.config = config

        self.run_count = 0
        self.output_path = output_path if output_path else default_output_path()
        # Without facts of its own, those already saved in its output, as a cijoe
        # made by the pytest plugin has the run's when core.testrunner runs it
        self.facts = facts or Facts.load(Path(self.output_path) / Facts.FILENAME)
        self.output_ident = "artifacts"

        self.monitor = monitor

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        self.targets: dict = {}

        targets = self.config.options.get("cijoe", {}).get("targets", {})
        for name, target in targets.items():
            self.targets[name] = transport.SSH(
                self.config, self.output_path, target["ssh"]
            )

        self.targets["initiator"] = transport.Local(self.config, self.output_path)
        self.default_target = self.config.options.get("cijoe", {}).get(
            "default_target", next(iter(self.targets))
        )

    @property
    def transports(self) -> dict:
        """Deprecated name of 'targets'"""

        deprecated("Cijoe.transports", "Cijoe.targets")
        return self.targets

    @property
    def default_target(self) -> str:
        """
        The name of the target that run(), put() and get() reach when given no
        'target': the config's 'cijoe.default_target', else the first in its
        'cijoe.targets', or the initiator when there is none. A task step's
        'target' sets it while the step runs.
        """

        return self._default_target

    @default_target.setter
    def default_target(self, name: str):
        if name not in self.targets:
            raise ValueError(f"no target({name}); known: {', '.join(self.targets)}")
        self._default_target = name
        self.facts.default_target = name

    def set_output_ident(self, output_ident: str, target=None, transport_name=None):
        """
        This sets the output-identifier which is used in order to provide a subfolder
        for artifacts, command-output etc. Additionally, then it reset the command
        run-count
        """

        output_ident = sanitize_ident(output_ident)

        self.run_count = 0
        self.output_ident = output_ident
        self._get_target(target, transport_name).output_ident = output_ident

    def _run(self, cmd, cwd, env, transport):
        self.run_count += 1

        begin = time.time()
        state = CommandState(
            cijoe=self,
            cmd=cmd,
            cwd=cwd,
            err=0,
            begin=begin,
            end=0,
            is_done=False,
            monitor=self.monitor,
        )
        state.to_file()

        with state.cmd_output as cmd_output:
            err = transport.run(cmd, cwd, env, cmd_output)
            state.err = err
            state.end = time.time()
            state.elapsed = state.end - state.begin
            state.is_done = True
            state.to_file()

        return err, state

    def _get_target(self, target=None, transport_name=None):
        if transport_name:
            deprecated("transport_name=", "target=")
            target = target or transport_name
        if not target:
            target = self.default_target
        if target not in self.targets:
            log.error(
                f"The given target ({target}) not valid. Must be defined in the configuration file."
            )

        return self.targets[target]

    def run(self, cmd, cwd=None, env={}, target=None, transport_name=None):
        """
        Execute the given shell command/expression on 'target', by default the
        default target

        Commands executed using this will write stdout and stderr to file. The location
        of the cmd_output is fixed to: "output_path/output_ident/cmd_XX.output", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self._get_target(target, transport_name))

    def run_local(self, cmd, cwd=None, env={}):
        """
        Execute the given shell command/expression via local transport

        Commands executed using this will write stdout and stderr to file. The location
        of the cmd_output is fixed to: "output_path/output_ident/cmd_XX.output", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self._get_target("initiator"))

    def put(self, src, dst, target=None, transport_name=None):
        """Transfer 'src' on the initiator to 'dst' on 'target', by default the
        default target"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self._get_target(target, transport_name).put(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False

    def get(self, src, dst, target=None, transport_name=None):
        """Transfer 'src' on 'target', by default the default target, to 'dst' on
        the initiator"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self._get_target(target, transport_name).get(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False

    def close(self, target=None, transport_name=None):
        """
        Close the connections the targets' transports keep, or only the one of the
        named target; a later call connects again
        """

        if target is not None or transport_name is not None:
            self._get_target(target, transport_name).close()
            return

        for tport in self.targets.values():
            tport.close()

    def getconf(self, key: str, default: Any = None):
        """
        Return value for given key, and return default if no value is found.

        The key must be a sequence of namespaces separated by a point, ex.
        "foo.bar.jazz".

        The value is found in the cijoe configuration file, but is overwritten
        if the key, with points and dashes replaced with underscores, ex.
        FOO_BAR_JAZZ, is found in the initiator's environment variables.
        """

        envkey = key.replace(".", "_").replace("-", "_").upper()
        envvar = os.getenv(envkey)
        if envvar:
            log.debug(f"found {key} ({envkey}) in environment variables.")
            return convert_str(envvar)

        dict_keys = key.split(".")
        config = self.config.options

        try:
            # fold over the list of dict keys, to iterate through nested dicts
            [config := config.get(key, {}) for key in dict_keys[:-1]]
            return config.get(dict_keys[-1], default)
        except AttributeError as exc:
            # AttributeError is raised if one of the keys are associated to a
            # value that is not a dict.
            log.debug(f"{key} not in config: {exc}")
            return default
