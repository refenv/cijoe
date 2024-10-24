import errno
import logging as log
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import paramiko
from scp import SCPClient

from cijoe.core.misc import ENCODING
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


class Local(Transport):
    """Provide cmd/push/pull locally"""

    def __init__(self, config: Config, output_path: Path):
        self.config = config
        self.output_path = output_path
        self.output_ident = "artifacts"

    def run(self, cmd, cwd, env, cmd_output):
        """Invoke the given command"""

        env = dict(os.environ)
        env.update(env)

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            cwd=cwd,
            env=env,
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


class SSH(Transport):
    """Provide cmd/push/pull over SSH"""

    def __init__(self, config, output_path, transport_name):
        """Initialize the CIJOE SSH Transport"""

        self.config = config
        self.shell = (
            self.config.options.get("cijoe", {}).get("run", {}).get("shell", "sh")
        )
        self.output_path = output_path

        self.ssh = paramiko.SSHClient()
        self.ssh_params = (
            self.config.options.get("cijoe", {}).get("transport").get(transport_name)
        )

        # Using the 'AutoAddPolicy()' *without* load_system_host_keys(), by doing so,
        # then Paramiko does not know any hosts, and simply adds them first time they
        # are connected to.
        # It was attempted to use load_system_host_keys() with WarningPolicy(), however,
        # when a host changed, e.g. re-provisioned virtual machine, then the host-key
        # changes and Paramiko cannot connect.
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.scp = None

        # Not connecting at this point, since the remote side might be ready at the time
        # the transport is initialized. For example, when a qemu-guest is booted, then
        # cijoe.run_local() is used, and not until the guest is up will the cij.run() be
        # used. Also, when a system reboots etc. then dropped connections must be
        # handled, lastly connection close must happen as Python terminates, dangling
        # connections will make it hang.
        # Thus, __connect()/__disconnect() is called for each call to run()/get()/put().
        # Current short-coming is of course that then these cannot happen in parallel.

        log.getLogger("paramiko.transport").setLevel(log.CRITICAL)
        paramiko.util.log_to_file(
            self.output_path / "paramiko.log", level=log.root.level
        )

    def __connect(self):
        self.ssh.connect(**self.ssh_params)
        self.scp = SCPClient(self.ssh.get_transport())

    def __disconnect(self):
        self.scp.close()
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
        if cwd:
            cmd = f"cd {cwd}; {cmd}"

        try:
            self.__connect()

            _, stdout, _ = self.ssh.exec_command(cmd, environment=env)
            stdout.channel.set_combine_stderr(True)

            while not stdout.channel.exit_status_ready():
                cmd_output.write(stdout.read(1))

            cmd_output.write(stdout.read())
            cmd_output.flush()

            err = stdout.channel.recv_exit_status()

            self.__disconnect()
        except paramiko.ssh_exception.SSHException as exc:
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

        self.scp.put(src, dst, recursive=True)

        self.__disconnect()

        return True

    def get(self, src, dst=None):
        """Hmm... no return-value just exceptions"""

        self.__connect()

        if dst is None:
            dst = os.path.basename(src)
        if not os.path.isabs(src):
            dst = os.path.join(self.output_path, self.output_ident, dst)

        self.scp.get(src, dst, recursive=True)

        self.__disconnect()

        return True
