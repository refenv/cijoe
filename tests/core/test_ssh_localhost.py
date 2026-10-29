"""
cijoe over real SSH, to an sshd the test starts on 127.0.0.1 as the current
user, with keys of its own; skipped where there is no sshd or ssh-keygen
"""

import contextlib
import getpass
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
from argparse import Namespace
from pathlib import Path
from typing import Optional

import pytest
import yaml

from cijoe.core.command import Cijoe
from cijoe.core.processing import runlog_from_path
from cijoe.core.resources import Config, dict_to_tomlfile

SSHD = shutil.which("sshd") or "/usr/sbin/sshd"


def unavailable(reason: str):
    """Skip, or in CI, where the SSH tests must run, fail"""

    if os.environ.get("CI"):
        pytest.fail(reason)
    pytest.skip(reason)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def running_sshd(path: Path, port: Optional[int] = None):
    """An sshd on 127.0.0.1 as the current user, with its keys in 'path', made
    there unless they are, on 'port' or a free one: the SSH settings of a target
    reaching it, and its process"""

    if not Path(SSHD).exists() or not shutil.which("ssh-keygen"):
        unavailable("no sshd or ssh-keygen")

    path.mkdir(parents=True, exist_ok=True)
    for key in [k for k in ["host_key", "client_key"] if not (path / k).exists()]:
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path / key)],
            check=True,
        )
    (path / "authorized_keys").write_text((path / "client_key.pub").read_text())
    port = port or free_port()
    (path / "sshd_config").write_text(
        f"Port {port}\n"
        "ListenAddress 127.0.0.1\n"
        f"HostKey {path / 'host_key'}\n"
        f"AuthorizedKeysFile {path / 'authorized_keys'}\n"
        f"PidFile {path / 'sshd.pid'}\n"
        "StrictModes no\n"
        "UsePAM no\n"
        "PasswordAuthentication no\n"
    )

    log = (path / "sshd.log").open("w")
    server = subprocess.Popen(
        [SSHD, "-D", "-e", "-f", str(path / "sshd_config")], stderr=log
    )
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        server.kill()
        log.close()
        unavailable(f"sshd did not start: {(path / 'sshd.log').read_text()}")

    settings = {
        "hostname": "127.0.0.1",
        "port": port,
        "username": getpass.getuser(),
        "key_filename": str(path / "client_key"),
        "look_for_keys": False,
        "allow_agent": False,
    }
    try:
        yield settings, server
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait()
        log.close()


@pytest.fixture(scope="module")
def sshd(tmp_path_factory):
    """The SSH settings of a target reaching the sshd this starts"""

    with running_sshd(tmp_path_factory.mktemp("sshd")) as (settings, _):
        yield settings


@pytest.fixture
def ssh_cijoe(sshd, tmp_path):
    """A cijoe whose default target is reached over SSH to localhost"""

    config = tmp_path / "config.toml"
    dict_to_tomlfile({"cijoe": {"targets": {"localhost": {"ssh": sshd}}}}, config)
    cijoe = Cijoe(Config.from_path(config), tmp_path / "output", False)

    yield cijoe

    cijoe.close()


def test_run(ssh_cijoe):
    """Commands run over SSH, with their output and exit status"""

    err, state = ssh_cijoe.run("echo $SSH_CONNECTION")
    assert err == 0
    assert state.output().startswith("127.0.0.1 ")

    err, _ = ssh_cijoe.run("exit 3")
    assert err == 3


def test_put_and_get(ssh_cijoe, tmp_path):
    """A file goes to the target and comes back as it was"""

    src, remote, back = tmp_path / "src", tmp_path / "remote", tmp_path / "back"
    src.write_text("over ssh\n")

    assert ssh_cijoe.put(str(src), str(remote))
    assert ssh_cijoe.get(str(remote), str(back))
    assert back.read_text() == "over ssh\n"


def test_reconnect_after_close(ssh_cijoe):
    """A command after close() connects again"""

    assert ssh_cijoe.run("true")[0] == 0
    ssh_cijoe.close()
    assert ssh_cijoe.run("true")[0] == 0


def test_wait_for_target(ssh_cijoe):
    """The target is up, as wait_for_target finds by its probe"""

    from cijoe.core.scripts import wait_for_target

    args = Namespace(state="up", timeout=20)
    assert wait_for_target.main(args, ssh_cijoe) == 0


def test_facts_over_ssh(ssh_cijoe):
    """facts_gather gathers about the target over SSH"""

    from cijoe.core.scripts import facts_gather

    args = Namespace(target_name=None, sections="os,kernel", skip="")
    assert facts_gather.main(args, ssh_cijoe) == 0

    uname = subprocess.run(["uname", "-s"], capture_output=True, text=True)
    kernel = ssh_cijoe.facts.get("targets.localhost.kernel.name")
    assert kernel == uname.stdout.strip()


def test_step_target_over_ssh(sshd, tmp_path):
    """A step with 'target:' runs over SSH; the step after it, on the default"""

    config = tmp_path / "config.toml"
    dict_to_tomlfile(
        {
            "cijoe": {
                "default_target": "initiator",
                "targets": {"localhost": {"ssh": sshd}},
            }
        },
        config,
    )
    steps = [
        {"name": "remote", "target": "localhost", "run": "echo at=$SSH_CONNECTION"},
        {"name": "local", "run": "echo at=$SSH_CONNECTION"},
    ]
    (tmp_path / "task.yaml").write_text(yaml.dump({"doc": "SSH", "steps": steps}))

    result = subprocess.run(
        ["cijoe", "task.yaml", "-c", str(config), "-o", "output", "--report-skip"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    state = yaml.safe_load((tmp_path / "output" / "task.state").read_text())
    remote, local = (
        list(runlog_from_path(tmp_path / "output" / step["id"]).values())[0]
        for step in state["steps"]
    )
    assert remote["output"].startswith("at=127.0.0.1 ")
    assert not local["output"].startswith("at=127.0.0.1 ")


def cijoe_reaching(ssh: dict, path: Path) -> Cijoe:
    """A cijoe whose default target is reached with the SSH settings 'ssh'"""

    config = path / "config.toml"
    dict_to_tomlfile({"cijoe": {"targets": {"guest": {"ssh": ssh}}}}, config)
    return Cijoe(Config.from_path(config), path / "output", False)


def test_wait_for_target_down_when_sshd_stops(tmp_path):
    from cijoe.core.scripts import wait_for_target

    with running_sshd(tmp_path / "sshd") as (ssh, server):
        cijoe = cijoe_reaching(ssh, tmp_path)
        assert wait_for_target.main(Namespace(state="up", timeout=20), cijoe) == 0

        server.terminate()
        server.wait()
        assert wait_for_target.main(Namespace(state="down", timeout=20), cijoe) == 0
        cijoe.close()


def test_wait_for_target_down_when_the_port_is_not_ssh(tmp_path):
    """A port that accepts connections, and closes them without speaking SSH"""

    from cijoe.core.scripts import wait_for_target

    listener = socket.create_server(("127.0.0.1", 0))

    def accept():
        while True:
            try:
                listener.accept()[0].close()
            except OSError:
                return

    threading.Thread(target=accept, daemon=True).start()
    ssh = {"hostname": "127.0.0.1", "port": listener.getsockname()[1]}
    cijoe = cijoe_reaching({**ssh, "username": getpass.getuser()}, tmp_path)

    assert wait_for_target.main(Namespace(state="down", timeout=20), cijoe) == 0
    listener.close()


def test_wait_for_target_gives_up(tmp_path):
    """A port nobody listens on is not up, however long one waits"""

    from cijoe.core.scripts import wait_for_target

    ssh = {"hostname": "127.0.0.1", "port": free_port(), "username": "nobody"}
    cijoe = cijoe_reaching(ssh, tmp_path)

    assert wait_for_target.main(Namespace(state="up", timeout=3), cijoe) == 1


def test_one_connection_for_commands_and_transfers(sshd, tmp_path):
    """The connection the first command makes is kept for those after it"""

    cijoe = cijoe_reaching(sshd, tmp_path)
    ssh = cijoe.targets["guest"].ssh

    assert cijoe.run("true")[0] == 0
    connection = ssh.get_transport()
    assert cijoe.run("id -u")[0] == 0
    assert cijoe.put(str(tmp_path / "config.toml"), str(tmp_path / "copied"))
    assert cijoe.get(str(tmp_path / "copied"), str(tmp_path / "back"))
    assert ssh.get_transport() is connection
    cijoe.close()


def test_close_and_connect_again(sshd, tmp_path):
    cijoe = cijoe_reaching(sshd, tmp_path)
    ssh = cijoe.targets["guest"].ssh

    assert cijoe.run("true")[0] == 0
    cijoe.close()
    assert ssh.get_transport() is None
    assert cijoe.targets["guest"].scp is None

    assert cijoe.run("true")[0] == 0
    assert ssh.get_transport().is_active()
    cijoe.close()


def test_close_one_target(sshd, tmp_path):
    config = tmp_path / "config.toml"
    dict_to_tomlfile(
        {"cijoe": {"targets": {"a": {"ssh": sshd}, "b": {"ssh": sshd}}}}, config
    )
    cijoe = Cijoe(Config.from_path(config), tmp_path / "output", False)

    assert cijoe.run("true", target="a")[0] == 0
    assert cijoe.run("true", target="b")[0] == 0
    cijoe.close("a")
    assert cijoe.targets["a"].ssh.get_transport() is None
    assert cijoe.targets["b"].ssh.get_transport().is_active()
    cijoe.close()


def test_connect_again_after_the_server_restarts(tmp_path):
    """A connection the server dropped is made again on next use"""

    with running_sshd(tmp_path / "sshd") as (ssh, server):
        cijoe = cijoe_reaching(ssh, tmp_path)
        assert cijoe.run("true")[0] == 0
        kept = cijoe.targets["guest"].ssh.get_transport()

        sessions = subprocess.run(
            ["pgrep", "-P", str(server.pid)], capture_output=True, text=True
        ).stdout.split()
        assert sessions, "the kept connection is served by a session of its own"
        for pid in sessions:
            os.kill(int(pid), signal.SIGTERM)
        server.terminate()
        server.wait()

        for _ in range(50):
            if not kept.is_active():
                break
            time.sleep(0.1)
        assert not kept.is_active()

    with running_sshd(tmp_path / "sshd", ssh["port"]):
        assert cijoe.run("true")[0] == 0
        assert cijoe.targets["guest"].ssh.get_transport() is not kept
        cijoe.close()


def test_a_failed_login_is_not_kept(sshd, tmp_path):
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(tmp_path / "other")],
        check=True,
    )
    cijoe = cijoe_reaching(
        {**sshd, "key_filename": str(tmp_path / "other"), "look_for_keys": False},
        tmp_path,
    )
    ssh = cijoe.targets["guest"]

    assert not cijoe.put(str(tmp_path / "config.toml"), str(tmp_path / "copied"))
    assert ssh.ssh.get_transport() is None

    ssh.ssh_params["key_filename"] = sshd["key_filename"]
    assert cijoe.put(str(tmp_path / "config.toml"), str(tmp_path / "copied"))
    cijoe.close()


def test_a_failed_transfer_drops_the_connection(sshd, tmp_path):
    cijoe = cijoe_reaching(sshd, tmp_path)
    ssh = cijoe.targets["guest"].ssh

    assert cijoe.run("true")[0] == 0
    assert not cijoe.put(str(tmp_path / "config.toml"), "/nonexistent/dir/file")
    assert ssh.get_transport() is None

    assert cijoe.put(str(tmp_path / "config.toml"), str(tmp_path / "copied"))
    cijoe.close()


def test_wait_for_target_probes_a_fresh_connection(sshd, tmp_path):
    """The probe connects afresh rather than riding the kept connection, which
    may outlive the server accepting new ones"""

    from cijoe.core.scripts import wait_for_target

    cijoe = cijoe_reaching(sshd, tmp_path)
    assert cijoe.run("true")[0] == 0
    kept = cijoe.targets["guest"].ssh.get_transport()

    assert wait_for_target.main(Namespace(state="up", timeout=20), cijoe) == 0
    assert cijoe.targets["guest"].ssh.get_transport() is not kept
    cijoe.close()


def test_wait_for_target_needs_a_target(tmp_path):
    """There is nothing to wait for on the initiator"""

    from cijoe.core.scripts import wait_for_target

    (tmp_path / "config.toml").write_text("")
    cijoe = Cijoe(Config.from_path(tmp_path / "config.toml"), tmp_path / "out", False)

    assert wait_for_target.main(Namespace(state="up", timeout=20), cijoe) == 1


def test_wait_for_transport_is_a_deprecated_wait_for_target(sshd, tmp_path, capsys):
    """wait_for_transport waits on 'transport_name', and leaves the step's
    target as it was"""

    from cijoe.core.scripts import wait_for_transport

    config = tmp_path / "config.toml"
    dict_to_tomlfile(
        {"cijoe": {"default_target": "initiator", "targets": {"guest": {"ssh": sshd}}}},
        config,
    )
    cijoe = Cijoe(Config.from_path(config), tmp_path / "output", False)

    args = Namespace(transport_name="guest", state="up", timeout=20)
    assert wait_for_transport.main(args, cijoe) == 0
    assert cijoe.default_target == "initiator"
    err = capsys.readouterr().err
    assert "core.wait_for_transport is deprecated; use core.wait_for_target" in err
    assert "'transport_name' is deprecated; use the step's 'target'" in err

    args = Namespace(transport_name="nope", state="up", timeout=20)
    assert wait_for_transport.main(args, cijoe) == 1
    cijoe.close()


def test_transport_name_is_a_deprecated_target(sshd, tmp_path, capsys):
    cijoe = cijoe_reaching(sshd, tmp_path)

    err, state = cijoe.run("echo $SSH_CONNECTION", transport_name="guest")
    assert err == 0 and state.output().startswith("127.0.0.1 ")
    assert capsys.readouterr().err == (
        "WARNING: transport_name= is deprecated; use target=\n"
    )

    assert cijoe.transports is cijoe.targets
    assert "Cijoe.transports is deprecated; use Cijoe.targets" in (
        capsys.readouterr().err
    )
    cijoe.close()


def test_run_in_a_cwd_with_a_space(ssh_cijoe, tmp_path):
    """A cwd is quoted, and a cwd that cannot be entered fails the command"""

    spaced = tmp_path / "my dir"
    spaced.mkdir()

    err, state = ssh_cijoe.run("pwd", cwd=spaced)
    assert err == 0
    assert state.output().strip() == str(spaced)

    err, _ = ssh_cijoe.run("touch ran", cwd=tmp_path / "missing")
    assert err != 0
    assert not (Path.home() / "ran").exists()
