"""
PCIe topology and devices of a qemu guest
=========================================

A guest's config can describe the PCIe topology it gets and the devices on it,
in place of '-device' arguments in 'system_args.raw':

    [qemu.guests.<guest>.pcie.switches.<switch>]
    downstream_ports = 2

    [[qemu.guests.<guest>.devices]]
    name = "nvme0"
    provider = "qemu"
    port = "<switch>_dn0"
    device = "nvme,serial=deadbeef"
    drives = ["file=/path/nvme0.img,if=none,id=nvm0,format=raw"]
    children = ["nvme-ns,drive=nvm0,nsid=1"]

    [[qemu.guests.<guest>.devices]]
    name = "gpu0"
    provider = "vfio-user"
    port = "<switch>_dn1"
    boot = false
    socket = "/tmp/gpu0.sock"
    server = "/usr/bin/some-server --socket {socket}"

Each switch sits on a root port of its own, and its downstream ports are named
'<switch>_dn<i>'. A device without a 'port' gets a root port of its own, named
'<device>_rp'. Ports are created in the order the switches, then the devices,
are listed, so a guest's PCIe addresses stay the same from boot to boot.

A device of provider 'qemu' is a device QEMU emulates: 'device' is its
'-device' argument without 'id' and 'bus', which are added, 'drives' are
'-drive' arguments, and 'children' are '-device' arguments put on the bus the
device provides, such as an NVMe controller's namespaces. A device of provider
'vfio-user' is served by a process on the initiator: 'server' is its command
line, with '{socket}' replaced by 'socket', and the server is started before the
device is added and stopped when the guest is killed. Its 'driver' defaults to
'vfio-user-pci', and 'props' is a table of further properties, typed as QEMU
wants them, as they are passed as JSON; 'rombar' defaults to 0, as a vfio-user
server rarely has a ROM to give.

A device with 'boot = false' is not present at boot: its port and drives are,
and 'plug()' adds it to the running guest, over QMP, as 'unplug()' removes it.
Its children are plugged after it, onto its bus, which only works where that
bus takes hot-plugged devices; an NVMe controller's does not, so a controller
plugged later takes its drive itself, 'nvme,drive=...', rather than through
'nvme-ns' children.
"""

import errno
import json
import logging as log
import os
import signal
import socket as sockets
import time
from pathlib import Path

PROVIDERS = ("qemu", "vfio-user")


class Topology:
    """The ports and devices a guest's config describes"""

    def __init__(self, guest_config: dict):
        self.switches = guest_config.get("pcie", {}).get("switches", {})
        self.devices = guest_config.get("devices", [])

        names = [dev.get("name") for dev in self.devices]
        if None in names or len(set(names)) != len(names):
            raise ValueError(f"devices need unique names; got {names}")

        self.ports = {}
        for switch, cfg in self.switches.items():
            for i in range(int(cfg.get("downstream_ports", 1))):
                self.ports[f"{switch}_dn{i}"] = switch

        for dev in self.devices:
            if dev.get("provider") not in PROVIDERS:
                raise ValueError(f"device {dev['name']}: provider not in {PROVIDERS}")
            port = dev.get("port")
            if port is not None and port not in self.ports:
                raise ValueError(f"device {dev['name']}: no port named {port}")

        taken = [dev["port"] for dev in self.devices if dev.get("port")]
        if len(set(taken)) != len(taken):
            raise ValueError(f"two devices on one port; ports {taken}")

    def __bool__(self):
        return bool(self.switches or self.devices)

    def device(self, name: str):
        """The device named 'name'; raises KeyError when there is none"""

        for dev in self.devices:
            if dev["name"] == name:
                return dev

        raise KeyError(name)

    def has_vfio_user(self):
        return any(dev["provider"] == "vfio-user" for dev in self.devices)

    @staticmethod
    def bus(dev: dict):
        """The bus 'dev' goes on"""

        return dev.get("port") or f"{dev['name']}_rp"

    def port_args(self):
        """The '-device' arguments creating the root ports and switches"""

        args = []
        chassis = 0

        def root_port(name):
            nonlocal chassis
            chassis += 1
            return ["-device", f"pcie-root-port,id={name},chassis={chassis},slot=0"]

        for switch, cfg in self.switches.items():
            args += root_port(f"{switch}_rp")
            args += ["-device", f"x3130-upstream,id={switch}_up,bus={switch}_rp"]
            for i in range(int(cfg.get("downstream_ports", 1))):
                chassis += 1
                args += [
                    "-device",
                    f"xio3130-downstream,id={switch}_dn{i},bus={switch}_up"
                    f",chassis={chassis},slot={i}",
                ]

        for dev in self.devices:
            if not dev.get("port"):
                args += root_port(self.bus(dev))

        return args

    def drive_args(self):
        """The '-drive' arguments of every device, present or not"""

        args = []
        for dev in self.devices:
            for drive in dev.get("drives", []):
                args += ["-drive", drive]

        return args

    def qemu_device_specs(self, dev: dict):
        """The '-device' arguments, as strings, of a 'qemu' device and its children"""

        specs = [f"{dev['device']},id={dev['name']},bus={self.bus(dev)}"]
        for i, child in enumerate(dev.get("children", [])):
            specs.append(f"{child},id={dev['name']}_c{i},bus={dev['name']}")

        return specs

    def vfio_user_props(self, dev: dict):
        """The QMP/JSON properties of a 'vfio-user' device"""

        props = {"rombar": 0, **dev.get("props", {})}
        props.update(
            {
                "driver": dev.get("driver", "vfio-user-pci"),
                "id": dev["name"],
                "bus": self.bus(dev),
                "socket": {"type": "unix", "path": dev["socket"]},
            }
        )

        return props

    def boot_device_args(self):
        """The '-device' arguments of the devices present at boot"""

        args = []
        for dev in self.devices:
            if not dev.get("boot", True):
                continue
            if dev["provider"] == "qemu":
                for spec in self.qemu_device_specs(dev):
                    args += ["-device", spec]
            else:
                # Single-quoted, as qemu is run through a shell
                args += ["-device", f"'{json.dumps(self.vfio_user_props(dev))}'"]

        return args


def memory_args(guest_config: dict):
    """A shared memory backend, which a vfio-user server needs to map guest memory;
    sized as the guest's '-m', which qemu requires it to match"""

    mem = guest_config.get("system_args", {}).get("kwa", {}).get("m", "128M")

    return [
        "-object",
        f"memory-backend-memfd,id=cijoe_mem,size={mem},share=on",
        "-machine",
        "memory-backend=cijoe_mem",
    ]


class Server:
    """The process serving a 'vfio-user' device, its pid kept in the guest's home"""

    def __init__(self, cijoe, guest_path: Path, dev: dict):
        self.cijoe = cijoe
        self.dev = dev
        self.socket = Path(dev["socket"])
        self.pidfile = guest_path / f"{dev['name']}.server.pid"
        self.log = guest_path / f"{dev['name']}.server.log"

    def pid(self):
        try:
            pid = int(self.pidfile.read_text().strip())
        except (OSError, ValueError):
            return 0
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return 0
        except PermissionError:
            pass

        return pid

    def stop(self, timeout=10):
        """Stop the server; returns 0, as a server not running is stopped"""

        pid = self.pid()
        if pid:
            os.kill(pid, signal.SIGTERM)
            began = time.time()
            while self.pid() and time.time() - began < timeout:
                time.sleep(0.1)
            if self.pid():
                os.kill(pid, signal.SIGKILL)
        self.pidfile.unlink(missing_ok=True)

        return 0

    def start(self, timeout=30):
        """Start the server, replacing one left running, and wait for its socket

        A vfio-user session does not survive its server, so a stale one is
        stopped rather than reused.
        """

        self.stop()
        self.socket.unlink(missing_ok=True)

        command = self.dev["server"].replace("{socket}", str(self.socket))
        err, _ = self.cijoe.run_local(
            f"setsid {command} > {self.log} 2>&1 < /dev/null & echo $! > {self.pidfile}"
        )
        if err:
            log.error(f"{self.dev['name']}: could not start server; err({err})")
            return err

        began = time.time()
        while not self.socket.is_socket():
            if not self.pid():
                log.error(f"{self.dev['name']}: server exited; see {self.log}")
                return errno.EIO
            if time.time() - began > timeout:
                log.error(
                    f"{self.dev['name']}: no socket {self.socket}; see {self.log}"
                )
                return errno.ETIMEDOUT
            time.sleep(0.1)

        return 0


class QMP:
    """A minimal client for the guest's QMP socket"""

    def __init__(self, path: Path, timeout=30):
        self.sock = sockets.socket(sockets.AF_UNIX, sockets.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect(str(path))
        self.stream = self.sock.makefile("rw")
        self.events: list[dict] = []
        self._read()  # the greeting
        self.execute("qmp_capabilities")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stream.close()
        self.sock.close()

    def _read(self):
        line = self.stream.readline()
        if not line:
            raise ConnectionError("QMP socket closed")
        return json.loads(line)

    def execute(self, command: str, arguments=None):
        """Run 'command'; returns its reply, keeping the events read meanwhile"""

        msg = {"execute": command}
        if arguments is not None:
            msg["arguments"] = arguments
        self.stream.write(json.dumps(msg) + "\n")
        self.stream.flush()

        while True:
            reply = self._read()
            if "event" in reply:
                self.events.append(reply)
                continue
            return reply

    def wait_event(self, name: str, device: str, timeout: float):
        """Wait for event 'name' about 'device'; True when it came"""

        def match(ev):
            return ev["event"] == name and ev.get("data", {}).get("device") == device

        if any(match(ev) for ev in self.events):
            return True

        began = time.time()
        while time.time() - began < timeout:
            self.sock.settimeout(max(0.1, timeout - (time.time() - began)))
            try:
                ev = self._read()
            except (TimeoutError, sockets.timeout):
                break
            if "event" in ev:
                self.events.append(ev)
                if match(ev):
                    return True

        return False


def plug(cijoe, guest, name: str):
    """Add the device 'name' to the running guest"""

    topo = Topology(guest.guest_config)
    dev = topo.device(name)

    if dev["provider"] == "vfio-user":
        err = Server(cijoe, guest.guest_path, dev).start()
        if err:
            return err

    with QMP(guest.qmp) as qmp:
        if dev["provider"] == "qemu":
            # As on the command line; QMP's own device_add wants typed values
            for i, spec in enumerate(topo.qemu_device_specs(dev)):
                reply = qmp.execute(
                    "human-monitor-command", {"command-line": f"device_add {spec}"}
                )
                if "error" in reply or reply.get("return"):
                    log.error(f"device_add {spec}: {reply}")
                    if i:  # the device went in, a child did not; take it out
                        qmp.execute("device_del", {"id": name})
                    return errno.EIO
        else:
            reply = qmp.execute("device_add", topo.vfio_user_props(dev))
            if "error" in reply:
                log.error(f"device_add {name}: {reply['error']}")
                return errno.EIO

    return 0


def unplug(cijoe, guest, name: str, timeout=60):
    """Remove the device 'name' from the running guest, and stop its server

    The guest has to release the device, so this waits for QEMU to report it
    deleted, at most 'timeout' seconds.
    """

    topo = Topology(guest.guest_config)
    dev = topo.device(name)

    with QMP(guest.qmp) as qmp:
        reply = qmp.execute("device_del", {"id": name})
        if "error" in reply:
            log.error(f"device_del {name}: {reply['error']}")
            return errno.EIO
        if not qmp.wait_event("DEVICE_DELETED", name, timeout):
            log.error(f"{name} was not deleted within {timeout} seconds")
            return errno.ETIMEDOUT

    if dev["provider"] == "vfio-user":
        return Server(cijoe, guest.guest_path, dev).stop()

    return 0
