"""

"""

import errno
import logging as log
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Union

import yaml

from cijoe.core import transport
from cijoe.core.misc import ENCODING, sanitize_ident
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

    def __init__(self, config: Config, output_path: Path, monitor: bool):
        """Create a cijoe encapsulation defined by the given config_fpath"""

        self.config = config

        self.run_count = 0
        self.output_path = output_path if output_path else default_output_path()
        self.output_ident = "artifacts"

        self.monitor = monitor

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        self.transports = {}

        config_transports = self.config.options.get("cijoe", {}).get("transport", {})
        for transport_name in config_transports:
            self.transports[transport_name] = transport.SSH(
                self.config, self.output_path, transport_name
            )

        self.transports["initiator"] = transport.Local(self.config, self.output_path)

    def set_output_ident(self, output_ident: str, transport_name=None):
        """
        This sets the output-identifier which is used in order to provide a subfolder
        for artifacts, command-output etc. Additionally, then it reset the command
        run-count
        """

        output_ident = sanitize_ident(output_ident)

        self.run_count = 0
        self.output_ident = output_ident
        self._get_transport(transport_name).output_ident = output_ident

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

    def _get_transport(self, transport_name=None):
        if not transport_name:
            transport_name = next(iter(self.transports))
        if transport_name not in self.transports:
            log.error(
                f"The given transport name ({transport_name}) not valid. Must be defined in the configuration file."
            )

        return self.transports[transport_name]

    def run(self, cmd, cwd=None, env={}, transport_name=None):
        """
        Execute the given shell command/expression via 'config.transport'

        Commands executed using this will write stdout and stderr to file. The location
        of the cmd_output is fixed to: "output_path/output_ident/cmd_XX.output", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self._get_transport(transport_name))

    def run_local(self, cmd, cwd=None, env={}):
        """
        Execute the given shell command/expression via local transport

        Commands executed using this will write stdout and stderr to file. The location
        of the cmd_output is fixed to: "output_path/output_ident/cmd_XX.output", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self._get_transport("initiator"))

    def put(self, src, dst, transport_name=None):
        """Transfer 'src' on 'dev_box' to 'dst' on **test_target**"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self._get_transport(transport_name).put(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False

    def get(self, src, dst, transport_name=None):
        """Transfer 'src' on 'test_target' to 'dst' on **dev_box**"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self._get_transport(transport_name).get(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False

    def getconf(self, key: str, default: Any = None):
        """
        Return value for given key, and return default if no value is found.

        The key must be a sequence of namespaces separated by a point, ex.
        "foo.bar.jazz".

        The value is found in the cijoe configuration file, but is overwritten
        if the key (with points replaced with underscores, ex. FOO_BAR_JAZZ) is
        found in the initiator's environment variables.
        """

        envkey = key.replace(".", "_").upper()
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
