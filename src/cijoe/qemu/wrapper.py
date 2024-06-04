"""
    Wraps qemu binaries: system, qemu-img and provides "guest-control"

    NOTE: this wrapper is "local-only". That is, changing transport does not retarget
    the functionality provided here. Most of the code is utilizing Python modules such
    as shutil, pathlib, psutil, download/requests. To make this re-targetable these
    things must be done via command-line utilities. It is certainly doable, however,
    currently not a priority as the intent is to utilize qemu to produce a virtual
    machine to serve as a 'target' for tests.
"""
import logging as log
import os
import shutil
import time
from pathlib import Path
from pprint import pformat

import psutil
from cijoe.core.misc import download


def qemu_img(cijoe, args=""):
    """Helper function wrapping around 'qemu-img'"""

    return cijoe.run_local(f"{cijoe.config.options['qemu']['img_bin']} {args}")


def qemu_system(cijoe, args=""):
    """Wrapping the qemu system binary"""

    return cijoe.run_local(f"{cijoe.config.options['qemu']['system_bin']} {args}")


class Guest(object):
    def __init__(self, cijoe, config, guest_name=None):
        """."""

        qemu_config = config.options.get("qemu", {})
        qemu_guests = qemu_config.get("guests", [])
        if not (qemu_config and qemu_guests):
            raise ValueError(f"Invalid qemu_config({pformat(qemu_config)})")

        guest_name = qemu_config.get("default_guest", list(qemu_guests.keys())[0])
        if not guest_name:
            raise ValueError(f"Invalid qemu_config({pformat(qemu_config)})")

        guest_config = qemu_guests.get(guest_name, None)
        if not guest_config:
            raise ValueError(f"Invalid qemu_config({pformat(qemu_config)})")

        guest_path = guest_config.get("path", None)
        if not (guest_config and guest_path):
            log.error(f"invalid qemu_config({pformat(qemu_config)})")
            raise ValueError("Invalid configuration")

        self.cijoe = cijoe
        self.qemu_config = qemu_config
        self.guest_config = guest_config
        self.guest_path = Path(guest_path).resolve()
        self.boot_img = self.guest_path / "boot.img"
        self.seed_img = self.guest_path / "seed.img"
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

    def initialize(self):
        """Create a 'home' for the guest'"""

        os.makedirs(self.guest_path, exist_ok=True)

    def is_up(self, timeout=120):
        """Wait at most 'timeout' seconds for the guest to print 'login' to serial"""

        if not self.is_running():
            return False

        began = time.time()
        while True:
            enter = time.time()
            try:
                with self.serial.open() as serialfile:
                    if "login:" in serialfile.read():
                        time.sleep(10)
                        return True
            except Exception as exc:
                log.error(f"{exc}")

            now = time.time()
            elapsed_iter = now - enter
            elapsed_total = now - began

            if elapsed_iter < 5.0:
                time.sleep(5.0 - elapsed_iter)
            if elapsed_total > timeout:
                return False

    def start(self, daemonize=True, extra_args=[]):
        """."""

        args = []

        system_args = self.guest_config.get("system_args", {})

        # Key-word arguments: config.qemu.guest.system_args.kwa
        for key, value in system_args.get("kwa", {}).items():
            args.append(f"-{key}")
            if isinstance(value, dict):
                args.append(next((f"{opt}={val}" for opt, val in value.items())))
            else:
                args.append(str(value))

        # Magic: when 'boot.img' exists, add it is as boot-drive
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
        ports = system_args.get("tcp_forward", None)
        if ports:
            args += [
                "-netdev",
                f"user,id=n1,ipv6=off,hostfwd=tcp::{ports['host']}-:{ports['guest']}",
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

        err, _ = qemu_system(self.cijoe, " ".join(args))

        return err

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

    def init_using_cloudinit(self):
        """Provision a guest OS using cloudinit"""

        self.kill()  # Ensure the guest is *not* running
        self.initialize()  # Ensure the guest has a "home"

        # Ensure the guest has a cloudinit-image available for "installation"
        cloudinit = self.guest_config.get("init_using_cloudinit", {})
        if not cloudinit:
            log.error("missing config([qemu.guest.init_using_cloudinit])")
            return 1

        img = cloudinit.get("img", None)
        if not img:
            log.error("missing config([qemu.guest.init_using_cloudinit.img])")
            return 1

        img = Path(img).resolve()
        if not img.exists():
            url = cloudinit.get("url", None)
            if not url:
                log.error("missing config([qemu.guest.init_using_cloudinit.url])")
                return 1

            img.parent.mkdir(parents=True, exist_ok=True)
            err, path = download(url, img)
            if err:
                log.error(f"download({url}), {path}: failed")
                return err

        # Create the boot.img based on cloudinit_img
        shutil.copyfile(str(img), str(self.boot_img))
        qemu_img(self.cijoe, f"resize {self.boot_img} 10G")

        # Create seed.img, with data and meta embedded
        metadata_path = shutil.copyfile(
            cloudinit["meta"], self.guest_path / "meta-data"
        )
        userdata_path = shutil.copyfile(
            cloudinit["user"], self.guest_path / "user-data"
        )

        # Inject the "pubkey" from config
        if "pubkey" in cloudinit:
            with Path(cloudinit["pubkey"]).resolve().open() as kfile:
                pubkey = kfile.read()
            with userdata_path.open("a") as userdatafile:
                userdatafile.write("ssh_authorized_keys:\n")
                userdatafile.write(f"- {pubkey}\n")

        # This uses mkisofs instead of cloud-localds, such that it works on
        # macOS and Linux, the 'mkisofs' should be available with 'cdrtools'
        cloud_cmd = " ".join(
            [
                "mkisofs",
                "-output",
                str(self.seed_img),
                "-volid",
                "cidata",
                "-joliet",
                "-rock",
                str(userdata_path),
                str(metadata_path),
            ]
        )
        err, _ = self.cijoe.run_local(cloud_cmd)

        # Additional args to pass to the guest when starting it
        system_args = []
        system_args += ["-drive", f"file={self.seed_img},if=virtio,format=raw"]

        err = self.start(daemonize=False, extra_args=system_args)
        if err:
            log.error("failed starting...")
            return err

        return 0

    def init_using_bootimage(self):
        """Provision a guest OS using a bootable disk-image"""

        self.kill()  # Ensure the guest is *not* running
        self.initialize()  # Ensure the guest has a "home"

        # Ensure the guest has an image available to boot from
        boot = self.guest_config.get("init_using_bootimage", {})
        boot["img"] = Path(boot["img"]).resolve()

        if not boot["img"].exists():
            os.makedirs(boot["img"].parent, exist_ok=True)
            err, path = download(boot["url"], str(boot["img"]))
            if err:
                log.error(f"download({boot['url']}), {path}: failed")
                return err

        # Create the boot.img based on cloudinit_img
        shutil.copyfile(str(boot["img"]), str(self.boot_img))
        qemu_img(self.cijoe, f"resize {self.boot_img} 10G")

        return 0
