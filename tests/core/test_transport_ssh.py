"""
The SSH transport over a fake paramiko client, thus without a remote host: one
connection kept for many commands and transfers, made again after it dropped,
and closed by Cijoe.close()
"""

import io
from pathlib import Path

import pytest

from cijoe.core import transport
from cijoe.core.command import Cijoe
from cijoe.core.resources import Config


class FakeChannel:
    def __init__(self):
        self.closed = False

    def set_combine_stderr(self, combine):
        pass

    def exit_status_ready(self):
        return True

    def recv_exit_status(self):
        return 0

    def close(self):
        self.closed = True


class FakeStdout:
    def __init__(self, output):
        self.channel = FakeChannel()
        self.output = io.BytesIO(output)

    def read(self, size=-1):
        return self.output.read(size)


class FakeTransport:
    def __init__(self):
        self.active = True
        self.keepalive = 0

    def is_active(self):
        return self.active

    def set_keepalive(self, interval):
        self.keepalive = interval


class FakeSSHClient:
    """The parts of paramiko.SSHClient that the transport uses, counting connects"""

    def __init__(self):
        self.transport = None
        self.connects = 0
        self.commands = []
        self.channels = []

    def set_missing_host_key_policy(self, policy):
        pass

    def connect(self, **params):
        self.connects += 1
        self.transport = FakeTransport()

    def get_transport(self):
        return self.transport

    def close(self):
        self.transport = None

    def exec_command(self, cmd, environment=None):
        assert self.transport and self.transport.active, "command without connection"
        self.commands.append(cmd)
        stdout = FakeStdout(b"output\n")
        self.channels.append(stdout.channel)
        return None, stdout, None


class FakeSCPClient:
    def __init__(self, ssh_transport):
        self.ssh_transport = ssh_transport
        self.transfers = []

    def put(self, src, dst, recursive=False):
        assert self.ssh_transport.active, "transfer without connection"
        self.transfers.append(("put", src, dst))

    def get(self, src, dst, recursive=False):
        assert self.ssh_transport.active, "transfer without connection"
        self.transfers.append(("get", src, dst))

    def close(self):
        pass


@pytest.fixture
def remote_cijoe(tmp_path, monkeypatch):
    """A Cijoe instance with one SSH transport over FakeSSHClient"""

    monkeypatch.setattr(transport.paramiko, "SSHClient", FakeSSHClient)
    monkeypatch.setattr(transport, "SCPClient", FakeSCPClient)

    config = Config(Path("fake.toml"))
    config.options = {"cijoe": {"transport": {"remote": {"hostname": "remote"}}}}

    instance = Cijoe(config, tmp_path, False)
    instance.set_output_ident("test")
    yield instance
    instance.close()


def test_one_connection(remote_cijoe):
    """Commands and transfers share the connection made by the first"""

    commands = ["true", "id -u", "hostname"]
    for cmd in commands:
        err, _ = remote_cijoe.run(cmd)
        assert err == 0

    assert remote_cijoe.put("/tmp/src", "dst")
    assert remote_cijoe.get("src", "/tmp/dst")

    ssh = remote_cijoe.transports["remote"].ssh
    assert ssh.connects == 1
    assert ssh.commands == commands
    assert ssh.transport.keepalive == transport.KEEPALIVE_SECONDS
    assert all(channel.closed for channel in ssh.channels)
    assert [kind for kind, _, _ in remote_cijoe.transports["remote"].scp.transfers] == [
        "put",
        "get",
    ]


def test_reconnect_after_drop(remote_cijoe):
    """A connection that dropped is made again on next use, for commands and transfers"""

    ssh = remote_cijoe.transports["remote"].ssh

    err, _ = remote_cijoe.run("true")
    assert err == 0 and ssh.connects == 1

    ssh.transport.active = False
    err, _ = remote_cijoe.run("true")
    assert err == 0 and ssh.connects == 2

    ssh.transport.active = False
    assert remote_cijoe.put("/tmp/src", "dst")
    assert ssh.connects == 3


def test_closed(remote_cijoe):
    """Cijoe.close() closes the connection, and a later command connects again"""

    ssh = remote_cijoe.transports["remote"].ssh

    err, _ = remote_cijoe.run("true")
    assert err == 0 and ssh.transport is not None

    remote_cijoe.close()
    assert ssh.transport is None
    assert remote_cijoe.transports["remote"].scp is None

    err, _ = remote_cijoe.run("true")
    assert err == 0 and ssh.connects == 2


def test_wait_for_transport_probes_a_fresh_connection(remote_cijoe, monkeypatch):
    """
    wait_for_transport's probe connects afresh, rather than riding the kept
    connection, which may outlive the remote accepting new ones
    """
    import argparse

    from cijoe.core.scripts import wait_for_transport

    monkeypatch.setattr(wait_for_transport.time, "sleep", lambda secs: None)
    monkeypatch.setattr(
        wait_for_transport.socket, "create_connection", lambda *a, **k: io.BytesIO()
    )

    err, _ = remote_cijoe.run("true", transport_name="remote")
    assert not err
    ssh = remote_cijoe.transports["remote"].ssh
    assert ssh.connects == 1

    args = argparse.Namespace(transport_name="remote", state="up", timeout=10)
    assert wait_for_transport.main(args, remote_cijoe) == 0
    assert ssh.connects == 2, "the probe reused the kept connection"
