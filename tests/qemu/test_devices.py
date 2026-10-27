"""Unit tests for a guest's PCIe topology and devices.

The argument tests check what Guest.start() would pass qemu, so they need no
qemu. The server and QMP tests run a stand-in server and a stand-in QMP socket,
so they need none either.
"""

import json
import socket
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from cijoe.core.command import Cijoe
from cijoe.core.resources import Config
from cijoe.qemu import devices
from cijoe.qemu.devices import QMP, Server, Topology

SWITCHED = {
    "pcie": {"switches": {"sw": {"downstream_ports": 2}}},
    "devices": [
        {
            "name": "nvme0",
            "provider": "qemu",
            "port": "sw_dn0",
            "device": "nvme,serial=deadbeef",
            "drives": ["file=nvme0.img,if=none,id=nvm0,format=raw"],
            "children": ["nvme-ns,drive=nvm0,nsid=1"],
        },
        {
            "name": "gpu0",
            "provider": "vfio-user",
            "port": "sw_dn1",
            "boot": False,
            "socket": "/tmp/gpu0.sock",
            "server": "server --socket {socket}",
            "props": {"x-msg-timeout": 1000},
        },
        {
            "name": "nvme1",
            "provider": "qemu",
            "device": "nvme,serial=cafe",
            "boot": False,
        },
    ],
}


def test_no_topology():
    assert not Topology({})


def test_ports_in_order():
    assert Topology(SWITCHED).port_args() == [
        "-device",
        "pcie-root-port,id=sw_rp,chassis=1,slot=0",
        "-device",
        "x3130-upstream,id=sw_up,bus=sw_rp",
        "-device",
        "xio3130-downstream,id=sw_dn0,bus=sw_up,chassis=2,slot=0",
        "-device",
        "xio3130-downstream,id=sw_dn1,bus=sw_up,chassis=3,slot=1",
        "-device",
        "pcie-root-port,id=nvme1_rp,chassis=4,slot=0",
    ]


def test_drives_present_whether_booted_or_not():
    assert Topology(SWITCHED).drive_args() == [
        "-drive",
        "file=nvme0.img,if=none,id=nvm0,format=raw",
    ]


def test_only_boot_devices_at_boot():
    assert Topology(SWITCHED).boot_device_args() == [
        "-device",
        "nvme,serial=deadbeef,id=nvme0,bus=sw_dn0",
        "-device",
        "nvme-ns,drive=nvm0,nsid=1,id=nvme0_c0,bus=nvme0",
    ]


def test_vfio_user_props_typed():
    topo = Topology(SWITCHED)
    assert topo.vfio_user_props(topo.device("gpu0")) == {
        "rombar": 0,
        "x-msg-timeout": 1000,
        "driver": "vfio-user-pci",
        "id": "gpu0",
        "bus": "sw_dn1",
        "socket": {"type": "unix", "path": "/tmp/gpu0.sock"},
    }


def test_vfio_user_at_boot_is_json():
    topo = Topology(
        {
            "devices": [
                {"name": "d", "provider": "vfio-user", "socket": "/s", "server": "x"}
            ]
        }
    )
    args = topo.boot_device_args()
    assert args[0] == "-device"
    assert args[1].startswith("'") and args[1].endswith("'")
    assert json.loads(args[1][1:-1])["bus"] == "d_rp"
    assert topo.has_vfio_user()


@pytest.mark.parametrize(
    "guest_config",
    [
        {
            "devices": [
                {"name": "a", "provider": "qemu"},
                {"name": "a", "provider": "qemu"},
            ]
        },
        {"devices": [{"provider": "qemu"}]},
        {"devices": [{"name": "a", "provider": "vfio-pci"}]},
        {"devices": [{"name": "a", "provider": "qemu", "port": "nowhere"}]},
        {
            "pcie": {"switches": {"sw": {}}},
            "devices": [
                {"name": "a", "provider": "qemu", "port": "sw_dn0"},
                {"name": "b", "provider": "qemu", "port": "sw_dn0"},
            ],
        },
    ],
    ids=["duplicate-name", "no-name", "unknown-provider", "unknown-port", "port-twice"],
)
def test_invalid(guest_config):
    with pytest.raises(ValueError):
        Topology(guest_config)


def make_cijoe(tmp_path):
    config = Config(Path("guest.toml"))
    config.options = {}
    cijoe = Cijoe(config, tmp_path / "output", False)
    cijoe.set_output_ident("test")
    return cijoe


# Creates the socket it is given, then waits to be stopped
FAKE_SERVER = """
import socket, sys, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.bind(sys.argv[1])
s.listen()
time.sleep(600)
"""


def fake_server_dev(tmp_path, script=FAKE_SERVER):
    path = tmp_path / "server.py"
    path.write_text(script)
    return {
        "name": "d",
        "provider": "vfio-user",
        "socket": str(tmp_path / "d.sock"),
        "server": f"{sys.executable} {path} {{socket}}",
    }


def test_server_start_and_stop(tmp_path):
    server = Server(make_cijoe(tmp_path), tmp_path, fake_server_dev(tmp_path))

    assert server.start() == 0
    pid = server.pid()
    assert pid
    assert server.socket.is_socket()

    assert server.start() == 0, "a second start replaces the first server"
    assert server.pid() != pid

    assert server.stop() == 0
    assert not server.pid()
    assert not server.pidfile.exists()


def test_server_that_exits(tmp_path):
    dev = fake_server_dev(tmp_path, "import sys; sys.exit(1)")
    server = Server(make_cijoe(tmp_path), tmp_path, dev)

    assert server.start() != 0


class FakeQMP(threading.Thread):
    """Answers QMP commands on 'path', recording them, as QEMU would"""

    def __init__(self, path: Path):
        super().__init__(daemon=True)
        self.commands: list[dict] = []
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(path))
        self.listener.listen()
        self.start()

    def run(self):
        while True:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            with conn, conn.makefile("rw") as stream:
                stream.write(json.dumps({"QMP": {"version": {}}}) + "\n")
                stream.flush()
                for line in stream:
                    msg = json.loads(line)
                    self.commands.append(msg)
                    if msg["execute"] == "device_del":
                        device = msg["arguments"]["id"]
                        event = {"event": "DEVICE_DELETED", "data": {"device": device}}
                        stream.write(json.dumps(event) + "\n")
                    reply = "" if msg["execute"] == "human-monitor-command" else {}
                    stream.write(json.dumps({"return": reply}) + "\n")
                    stream.flush()

    def executed(self):
        return [msg for msg in self.commands if msg["execute"] != "qmp_capabilities"]


def test_qmp_event_before_reply(tmp_path):
    fake = FakeQMP(tmp_path / "qmp.sock")
    with QMP(tmp_path / "qmp.sock", timeout=5) as qmp:
        assert qmp.execute("device_del", {"id": "x"}) == {"return": {}}
        assert qmp.wait_event("DEVICE_DELETED", "x", timeout=1)
        assert not qmp.wait_event("DEVICE_DELETED", "y", timeout=0.2)
    fake.listener.close()


def fake_guest(tmp_path, guest_config):
    return SimpleNamespace(
        guest_config=guest_config, guest_path=tmp_path, qmp=tmp_path / "qmp.sock"
    )


def test_plug_and_unplug_qemu_device(tmp_path):
    fake = FakeQMP(tmp_path / "qmp.sock")
    guest = fake_guest(tmp_path, SWITCHED)

    assert devices.plug(None, guest, "nvme1") == 0
    assert devices.unplug(None, guest, "nvme1", timeout=1) == 0
    assert fake.executed() == [
        {
            "execute": "human-monitor-command",
            "arguments": {
                "command-line": "device_add nvme,serial=cafe,id=nvme1,bus=nvme1_rp"
            },
        },
        {"execute": "device_del", "arguments": {"id": "nvme1"}},
    ]
    fake.listener.close()


def test_plug_and_unplug_vfio_user_device(tmp_path):
    fake = FakeQMP(tmp_path / "qmp.sock")
    dev = fake_server_dev(tmp_path)
    guest = fake_guest(tmp_path, {"devices": [dev]})
    cijoe = make_cijoe(tmp_path)

    assert devices.plug(cijoe, guest, "d") == 0
    server = Server(cijoe, tmp_path, dev)
    assert server.pid(), "plug starts the server"

    assert devices.unplug(cijoe, guest, "d", timeout=1) == 0
    assert not server.pid(), "unplug stops the server"

    added = fake.executed()[0]
    assert added["execute"] == "device_add"
    assert added["arguments"]["socket"] == {"type": "unix", "path": dev["socket"]}
    fake.listener.close()


def test_unplug_that_times_out(tmp_path, monkeypatch):
    fake = FakeQMP(tmp_path / "qmp.sock")
    monkeypatch.setattr(QMP, "wait_event", lambda *args: False)

    assert devices.unplug(None, fake_guest(tmp_path, SWITCHED), "nvme1", timeout=0) != 0
    fake.listener.close()


@pytest.mark.parametrize("devices", [True, False])
def test_guest_start_with_and_without_devices(tmp_path, monkeypatch, devices):
    from cijoe.qemu.wrapper import Guest

    guest_config = {"path": str(tmp_path / "g"), "system_label": "x86_64", **SWITCHED}
    config = Config(Path("guest.toml"))
    config.options = {
        "qemu": {"systems": {"x86_64": {"bin": "qemu"}}, "guests": {"g": guest_config}}
    }
    cijoe = Cijoe(config, tmp_path / "output", False)
    cijoe.set_output_ident("test")

    commands: list[str] = []
    monkeypatch.setattr(
        cijoe, "run_local", lambda cmd, *a, **kw: (commands.append(cmd), (0, None))[1]
    )

    assert Guest(cijoe, config, "g").start(devices=devices) == 0
    assert len(commands) == 1
    for arg in ["-qmp", "bus=sw_dn0", "x3130-upstream", "id=nvm0"]:
        assert (arg in commands[0]) == devices, arg


def test_plug_takes_the_device_out_when_a_child_fails(tmp_path, monkeypatch):
    fake = FakeQMP(tmp_path / "qmp.sock")
    guest_config = {
        "devices": [
            {
                "name": "n",
                "provider": "qemu",
                "boot": False,
                "device": "nvme,serial=x",
                "children": ["nvme-ns,drive=d,nsid=1"],
            }
        ]
    }
    replies = iter(
        [{"return": ""}, {"return": "Error: Bus 'n' does not support hotplugging"}]
    )
    execute = QMP.execute

    def fail_child(qmp, command, arguments=None):
        if command == "human-monitor-command":
            execute(qmp, command, arguments)
            return next(replies)
        return execute(qmp, command, arguments)

    monkeypatch.setattr(QMP, "execute", fail_child)

    assert devices.plug(None, fake_guest(tmp_path, guest_config), "n") != 0
    assert fake.executed()[-1] == {"execute": "device_del", "arguments": {"id": "n"}}
    fake.listener.close()
