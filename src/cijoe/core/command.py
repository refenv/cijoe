"""

"""
import errno
import logging as log
import os
import time
import traceback
from pathlib import Path

import yaml

from cijoe.core import transport
from cijoe.core.misc import ENCODING, sanitize_ident
from cijoe.core.resources import Config


def default_output_path():
    """Returns a default output-path"""

    return os.path.join(os.getcwd(), "cijoe-output")


class CommandState(object):
    def __init__(
        self, cmd, cwd, err, begin, end, output_dpath, output_fpath, state_fpath
    ):
        self.cmd = cmd
        self.cwd = cwd
        self.err = err
        self.begin = begin
        self.end = end
        self.elapsed = end - begin
        self.output_dpath = Path(output_dpath)
        self.output_fpath = Path(output_fpath)
        self.state_fpath = Path(state_fpath)

    def output(self):
        """Returns the content of 'output_fpath'"""

        with self.output_fpath.open() as ofd:
            return ofd.read()

    def to_file(self):
        """Dump the command state to file"""

        with self.state_fpath.open("a", encoding=ENCODING) as state_file:
            state = {
                "cmd": self.cmd,
                "cwd": str(self.cwd),
                "err": self.err,
                "begin": self.begin,
                "end": self.end,
                "elapsed": self.elapsed,
                "output_dpath": str(self.output_dpath),
                "output_fpath": str(self.output_fpath),
            }
            yaml.dump(state, state_file)


class Cijoe(object):
    """CIJOE providing retargetable command-line expressions and data-transfers"""

    def __init__(self, config: Config, output_path: Path):
        """Create a cijoe encapsulation defined by the given config_fpath"""

        self.config = config

        self.run_count = 0
        self.output_path = output_path if output_path else default_output_path()
        self.output_ident = "artifacts"

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        self.transport_local = transport.Local(self.config, self.output_path)
        self.transport = self.transport_local

        ssh = self.config.options.get("transport", {}).get("ssh", None)
        if ssh:
            self.transport = transport.SSH(self.config, self.output_path)

    def set_output_ident(self, output_ident: str):
        """
        This sets the output-identifier which is used in order to provide a subfolder
        for artifacts, command-output etc. Additionally, then it reset the command
        run-count
        """

        output_ident = sanitize_ident(output_ident)

        self.run_count = 0
        self.output_ident = output_ident
        self.transport.output_ident = output_ident

    def _run(self, cmd, cwd, env, transport):

        self.run_count += 1
        cmd_output_dpath = os.path.join(self.output_path, self.output_ident)
        cmd_output_fpath = os.path.join(
            cmd_output_dpath, f"cmd_{self.run_count:02}.output"
        )
        cmd_state_fpath = os.path.join(
            cmd_output_dpath, f"cmd_{self.run_count:02}.state"
        )
        os.makedirs(cmd_output_dpath, exist_ok=True)

        with open(cmd_output_fpath, "a", encoding=ENCODING) as logfile:
            begin = time.time()
            err = transport.run(cmd, cwd, env, logfile)
            state = CommandState(
                cmd=cmd,
                cwd=cwd,
                err=err,
                begin=begin,
                end=time.time(),
                output_dpath=cmd_output_dpath,
                output_fpath=cmd_output_fpath,
                state_fpath=cmd_state_fpath,
            )
            state.to_file()

        return err, state

    def run(self, cmd, cwd=None, env={}):
        """
        Execute the given shell command/expression via 'config.transport'

        Commands executed using this will write stdout and stderr to file. The location
        of the logfile is fixed to: "output_path/output_ident/cmd.log", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self.transport)

    def run_local(self, cmd, cwd=None, env={}):
        """
        Execute the given shell command/expression via local transport

        Commands executed using this will write stdout and stderr to file. The location
        of the logfile is fixed to: "output_path/output_ident/cmd.log", such that the
        location is a subfolder of the output_path. Unless somebody wants to break the
        convention and call set_output_ident("../..")
        """

        return self._run(cmd, cwd, env, self.transport_local)

    def put(self, src, dst):
        """Transfer 'src' on 'dev_box' to 'dst' on **test_target**"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self.transport.put(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False

    def get(self, src, dst):
        """Transfer 'src' on 'test_target' to 'dst' on **dev_box**"""

        os.makedirs(os.path.join(self.output_path, self.output_ident), exist_ok=True)

        try:
            return self.transport.get(src, dst)
        except Exception as exc:
            log.error(f"err({exc})")
            log.debug(f"src({src}), dst({dst})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return False
