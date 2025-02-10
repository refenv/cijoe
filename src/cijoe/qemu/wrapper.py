"""
    Wraps qemu binaries: system, qemu-img and provides "guest-control"

    NOTE: this wrapper is "local-only". That is, changing transport does not retarget
    the functionality provided here. Most of the code is utilizing Python modules such
    as shutil, pathlib, psutil, download/requests. To make this re-targetable these
    things must be done via command-line utilities. It is certainly doable, however,
    currently not a priority as the intent is to utilize qemu to produce a virtual
    machine to serve as a 'target' for tests.
"""

import errno
import logging as log
import os
import shutil
import time
from pathlib import Path
from pprint import pformat
from typing import Optional

import psutil

from cijoe.core.misc import download_and_verify


def qemu_img(cijoe, args=""):
    """Helper function wrapping around 'qemu-img'"""

    qemu_img_bin_default = "qemu-img"

    qemu_img_bin = cijoe.getconf("qemu.img_bin", None)
    if qemu_img_bin is None:
        log.error("Could not determine 'qemu-img' binary")
        qemu_img_bin = qemu_img_bin_default

    log.info(
        f"qemu_img_bin({qemu_img_bin}), qemu_img_bin_default({qemu_img_bin_default})"
    )

    return cijoe.run_local(f"{qemu_img_bin} {args}")


def qemu_system(cijoe, system_label, args=""):
    """Resolves and invokes the qemu-system by its system_label e.g. 'x86_64'"""

    system_bin = cijoe.getconf(f"qemu.systems.{system_label}.bin", None)
    if system_bin is None:
        log.error(f"Cannot determine system using system_label({system_label})")
        return errno.EINVAL, None

    return cijoe.run_local(f"{system_bin} {args}")


class Guest(object):
    def __init__(self, cijoe, config, guest_name):
        """."""

        qemu_config = config.options.get("qemu", {})
        qemu_guests = qemu_config.get("guests", [])
        if not (qemu_config and qemu_guests):
            raise ValueError(f"Invalid qemu_config({pformat(qemu_config)})")

        guest_config = qemu_guests.get(guest_name, None)
        if not guest_config:
            raise ValueError(f"Invalid guest_config({pformat(guest_config)})")

        guest_path = guest_config.get("path", None)
        if not (guest_config and guest_path):
            log.error(f"invalid qemu_config({pformat(qemu_config)})")
            raise ValueError("Invalid configuration")

        self.cijoe = cijoe
        self.qemu_config = qemu_config
        self.guest_config = guest_config
        self.guest_path = Path(guest_path).resolve()

        self.bios_img = self.guest_path / "bios.img"
        self.boot_img = self.guest_path / "boot.img"
        self.pid = self.guest_path / "guest.pid"
        self.monitor = self.guest_path / "monitor.sock"
        self.serial = self.guest_path / "serial.output"

    def image_create(self, filename, fmt="raw", size="8GB"):
        """
        Creates an image-file in the guest_path. Returns 0 on succes, errno to
        indicate the error.
        """

        img_path = self.guest_path / filename
        err, _ = qemu_img(self.cijoe, f"create -f {fmt} {img_path} {size}")

        return err

    def is_initialized(self):
        """Check that the guest is initialized"""

        return self.guest_path.exists()

    def is_running(self):
        """Check whether the guest is running"""

        pid = self.get_pid()

        return pid and psutil.pid_exists(pid)

    def get_pid(self):
        """Returns pid from 'guest.pid', returns 0 when 'guest.pid' is not found"""

        if not self.pid.exists():
            return 0

        with self.pid.open() as pidfile:
            pid = int(pidfile.read().strip())

        return pid

    def initialize(self, diskimage_path: Optional[Path] = None):
        """Create a 'home' for the guest'"""

        os.makedirs(self.guest_path, exist_ok=True)

        if diskimage_path:
            err, _ = self.cijoe.run_local(f"cp {diskimage_path} {self.boot_img}")
            if err:
                log.error(f"Failed copying diskimage({diskimage_path}); err({err})")
                return err

        if self.guest_config.get("system_label", None) != "aarch64":
            return 0

        # aarch64
        bios_path = None
        for location in [
            "/usr/share/edk2/aarch64/QEMU_EFI.fd",
            "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd",
        ]:
            if (cand_path := Path(location)).exists():
                bios_path = cand_path

        if bios_path is None:
            log.error("Could not find aarch64 bios/firmware")
            return errno.EINVAL

        err, _ = self.cijoe.run_local(f"cp {bios_path} {self.bios_img}")
        if err:
            log.error("copy failed")
            return errno.EINVAL

        err, _ = self.cijoe.run_local(f"truncate -s 64m {self.bios_img}")
        if err:
            log.error("truncate failed")
            return errno.EINVAL

        return 0

    def is_up(self, timeout=120):
        """Wait at most 'timeout' seconds for the guest to print 'login' to serial"""

        if not self.is_running():
            log.error("is_running(), check via pid, is False")
            return False

        began = time.time()
        while True:
            enter = time.time()
            try:
                if "login:" in self.serial.read_text(
                    encoding="utf-8", errors="replace"
                ):
                    return True
            except Exception as exc:
                log.error(f"{exc}")

            now = time.time()
            elapsed_iter = now - enter
            elapsed_total = now - began

            if elapsed_iter < 5.0:
                time.sleep(5.0 - elapsed_iter)
            if elapsed_total > timeout:
                log.error(f"System did not come up within timeout({timeout}) seconds")
                return False

    def start(self, daemonize=True, extra_args=[]):
        """."""

        system_label = self.guest_config.get("system_label", None)
        if system_label is None:
            log.error(f"invalid qemu.guests.GUEST.system_label({system_label})")
            return errno.EINVAL

        args = []

        system_args = self.guest_config.get("system_args", {})

        # Key-word arguments: config.qemu.guest.system_args.kwa
        for key, value in system_args.get("kwa", {}).items():
            args.append(f"-{key}")
            if isinstance(value, dict):
                args.append(next((f"{opt}={val}" for opt, val in value.items())))
            else:
                args.append(str(value))

        #
        # Managed: when 'bios.img' exists, add it as a 'pflash'
        #
        if self.bios_img.exists():
            args += [
                "-drive",
                f"file={self.bios_img},format=raw,if=pflash,readonly=on",
            ]

        #
        # Managed: when 'boot.img' exists, add it is as boot-drive
        #
        if self.boot_img.exists():
            args += [
                "-blockdev",
                f"qcow2,node-name=boot,file.driver=file,file.filename={self.boot_img}",
            ]
            args += ["-device", "virtio-blk-pci,drive=boot"]

        # Process Management stuff
        args += ["-pidfile", str(self.pid)]
        args += ["-monitor", f"unix:{self.monitor},server,nowait"]

        if daemonize:
            args += ["-display", "none"]
            args += ["-serial", f"file:{self.serial}"]
            args += ["-daemonize"]
        else:
            args += ["-nographic"]
            args += ["-serial", "mon:stdio"]

        #
        # Managed: config.qemu.guest.system_args.host_share
        #
        host_share = system_args.get("host_share", None)
        if host_share:
            host_share = Path(host_share).resolve()
            args += [
                "-virtfs",
                "fsdriver=local,id=fsdev0,security_model=mapped,mount_tag=hostshare"
                f",path={host_share}",
            ]

        #
        # Managed: config.qemu.guest.system_args.tcp_forward
        #
        tcp_forward = system_args.get("tcp_forward", None)
        if tcp_forward:
            host_addr = tcp_forward.get("host_address", "127.0.0.1")
            host_port = tcp_forward.get("host", None)
            guest_port = tcp_forward.get("guest", None)

            if None in [host_port, guest_port]:
                log.error(f"Invalid tcp_forward({tcp_forward})")
                return errno.EINVAL

            args += [
                "-netdev",
                f"user,id=n1,ipv6=off,hostfwd=tcp:{host_addr}:{host_port}-:{guest_port}",
            ]
            args += ["-device", "virtio-net-pci,netdev=n1"]

        #
        # Arguments provided via wrapper-class
        #
        args += extra_args

        #
        # Raw: config.qemu.guest.system_args.raw
        #
        args += [system_args.get("raw", "")]

        err, _ = qemu_system(self.cijoe, system_label, " ".join(args))
        if err:
            log.error(f"qemu_system failed with err({err})")
            return err

        return 0

    def kill(self):
        """Shutdown qemu guests by killing the process using the 'guest.pid'"""

        err = 0

        try:
            pid = self.get_pid()
            if pid:
                qemu_proc = psutil.Process(pid)
                qemu_proc.terminate()

                gone, alive = psutil.wait_procs([qemu_proc], timeout=3)
                for proc in alive:
                    proc.kill()
        except psutil.NoSuchProcess:
            log.info("Got 'NoSuchProcess', that is OK, continue.")

        return err
