import errno
import logging as log
import os
import shlex
import shutil
import subprocess
import weakref
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

import paramiko
from scp import SCPClient

from cijoe.core.misc import deprecated
from cijoe.core.resources import Config


class Transport(ABC):
    @abstractmethod
    def run(self, cmd, cwd, env: dict, cmd_output):
        pass

    @abstractmethod
    def get(self, src, dst=None):
        pass

    @abstractmethod
    def put(self, src, dst=None):
        pass

    def close(self):
        """Release what the transport holds open; it may be used again afterwards"""


class Local(Transport):
    """Provide cmd/push/pull locally"""

    def __init__(self, config: Config, output_path: Path):
        self.config = config
        self.output_path = output_path
        self.output_ident = "artifacts"

    def run(self, cmd, cwd, env, cmd_output):
        """Invoke the given command"""

        full_env = dict(os.environ)
        full_env.update(env or {})

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            cwd=cwd,
            env=full_env,
        ) as process:
            while process.poll() is None:
                cmd_output.write(process.stdout.read(1))

            cmd_output.write(process.stdout.read())
            cmd_output.flush()
            process.wait()

            return process.returncode

    def put(self, src, dst=None):
        """..."""

        if dst is None:
            dst = os.path.basename(src)
        if not os.path.isabs(src):
            src = os.path.join(self.output_path, self.output_ident, src)
        if not os.path.isabs(dst):
            dst = os.path.join(self.output_path, self.output_ident, dst)

        if src == dst:
            return True

        if os.path.isdir(src):
            shutil.copytree(src, dst)
            return True

        shutil.copy(src, dst)
        return True

    def get(self, src, dst=None):
        """..."""

        return self.put(src, dst)


# Keeps the NAT and firewall state of an idle kept connection alive
KEEPALIVE_SECONDS = 30


class SSH(Transport):
    """Provide cmd/push/pull over SSH"""

    def __init__(self, config, output_path, ssh_params: Union[dict, str]):
        """Initialize the CIJOE SSH Transport, 'ssh_params' as a target's
        [cijoe.targets.<name>.ssh] gives them; a target's name, as it once took a
        transport's, is deprecated"""

        if isinstance(ssh_params, str):
            deprecated("transport.SSH(config, output_path, <name>)", "its ssh table")
            targets = config.options.get("cijoe", {}).get("targets", {})
            ssh_params = targets.get(ssh_params, {}).get("ssh") or config.options.get(
                "cijoe", {}
            ).get("transport", {}).get(ssh_params)

        self.config = config
        self.shell = (
            self.config.options.get("cijoe", {}).get("run", {}).get("shell", "sh")
        )
        self.output_path = output_path

        self.ssh = paramiko.SSHClient()
        self.ssh_params = ssh_params

        # Using the 'AutoAddPolicy()' *without* load_system_host_keys(), by doing so,
        # then Paramiko does not know any hosts, and simply adds them first time they
        # are connected to.
        # It was attempted to use load_system_host_keys() with WarningPolicy(), however,
        # when a host changed, e.g. re-provisioned virtual machine, then the host-key
        # changes and Paramiko cannot connect.
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.scp = None

        # Not connecting here, the remote might not be up yet, e.g. a qemu guest that
        # run_local() boots. The connection is made on first use and kept, rather than
        # paying a key exchange per command. One that dropped, e.g. on a reboot of the
        # remote, is made again on next use. Calls on one transport cannot overlap.
        weakref.finalize(self, self.ssh.close)

        log.getLogger("paramiko.transport").setLevel(log.CRITICAL)
        paramiko.util.log_to_file(
            self.output_path / "paramiko.log", level=log.root.level
        )

    def __connect(self):
        """Connect, unless the connection made before is still up"""

        transport = self.ssh.get_transport()
        if transport is not None and transport.is_active():
            return

        self.close()
        try:
            self.ssh.connect(**self.ssh_params)
            transport = self.ssh.get_transport()
            transport.set_keepalive(KEEPALIVE_SECONDS)
            self.scp = SCPClient(transport)
        except BaseException:
            # paramiko starts the transport before it authenticates, so a failed
            # connect can leave one active, which the next use must not take
            self.close()
            raise

    def close(self):
        """Close the connection; the next run()/get()/put() connects again"""

        if self.scp is not None:
            self.scp.close()
            self.scp = None
        self.ssh.close()

    def run(self, cmd, cwd, env, cmd_output):
        """Invoke the given command"""

        # Add environment variables defined in config.
        env = self.config.options.get("cijoe", {}).get("run", {}).get("env", {}) | env

        # Seems like paramiko 'exec_command' or just SSH Accept-something... does not
        # like setting environment variables... thus.. this injection of them...
        # unfortunately then this is shell-dependent and probably breaks.
        # This is why the CIJOE_DISABLE_SSH_ENV_INJECT is here.
        if self.shell == "csh":
            prefix_env = "".join(
                [f'setenv {key} "{val}"; ' for key, val in env.items()]
            )
        elif self.shell == "cmd":
            prefix_env = "".join([f"set {key}={val} && " for key, val in env.items()])
        elif self.shell == "pwsh":
            prefix_env = "".join(
                [f"$env:{key} = '{val}'; " for key, val in env.items()]
            )
        else:
            prefix_env = "".join([f'{key}="{val}" ' for key, val in env.items()])
        if os.environ.get("CIJOE_DISABLE_SSH_ENV_INJECT", None):
            prefix_env = ""

        cmd = f"{prefix_env}{cmd}"
        # shlex quotes for POSIX shells and csh; cmd and pwsh quote differently
        if cwd and self.shell in ("cmd", "pwsh"):
            cmd = f"cd {cwd}; {cmd}"
        elif cwd:
            cmd = f"cd {shlex.quote(str(cwd))} && {cmd}"

        try:
            self.__connect()

            _, stdout, _ = self.ssh.exec_command(cmd, environment=env)
            stdout.channel.set_combine_stderr(True)

            while not stdout.channel.exit_status_ready():
                cmd_output.write(stdout.read(1))

            cmd_output.write(stdout.read())
            cmd_output.flush()

            err = stdout.channel.recv_exit_status()
            stdout.channel.close()
        except paramiko.ssh_exception.SSHException as exc:
            self.close()
            err = (
                exc.errno
                if hasattr(exc, "errno")
                and isinstance(exc.errno, int)
                and exc.errno > 0
                else errno.EIO
            )
            log.error(f"ssh-err({exc})")
            log.debug(f"cmd({cmd}), env({env})")
            log.debug(
                f"run():{type(exc).__name__}, {__file__}:{exc.__traceback__.tb_lineno}"
            )

        return err

    def put(self, src, dst=None):
        """Hmm... no return-value just exceptions"""

        self.__connect()

        if dst is None:
            dst = os.path.basename(src)
        if not os.path.isabs(src):
            src = os.path.join(self.output_path, self.output_ident, src)

        try:
            self.scp.put(src, dst, recursive=True)
        except Exception:
            self.close()
            raise

        return True

    def get(self, src, dst=None):
        """Hmm... no return-value just exceptions"""

        self.__connect()

        if dst is None:
            dst = os.path.basename(src)
        if not os.path.isabs(src):
            dst = os.path.join(self.output_path, self.output_ident, dst)

        try:
            self.scp.get(src, dst, recursive=True)
        except Exception:
            self.close()
            raise

        return True
