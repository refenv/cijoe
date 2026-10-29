"""
cijoe over real SSH, to an sshd the test starts on 127.0.0.1 as the current
user, with keys of its own; skipped where there is no sshd or ssh-keygen
"""

import getpass
import os
import shutil
import socket
import subprocess
import time
from argparse import Namespace
from pathlib import Path

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


@pytest.fixture(scope="module")
def sshd(tmp_path_factory):
    """The SSH settings of a target reaching the sshd this starts"""

    if not Path(SSHD).exists() or not shutil.which("ssh-keygen"):
        unavailable("no sshd or ssh-keygen")

    path = tmp_path_factory.mktemp("sshd")
    for key in ["host_key", "client_key"]:
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path / key)],
            check=True,
        )
    (path / "authorized_keys").write_text((path / "client_key.pub").read_text())
    port = free_port()
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
        unavailable(f"sshd did not start: {(path / 'sshd.log').read_text()}")

    yield {
        "hostname": "127.0.0.1",
        "port": port,
        "username": getpass.getuser(),
        "key_filename": str(path / "client_key"),
        "look_for_keys": False,
        "allow_agent": False,
    }

    server.terminate()
    server.wait()
    log.close()


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
