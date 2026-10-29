"""Unit tests for the boot image that Guest.initialize prepares.

A real Cijoe from a real Config, as in the other tests; the command-level tests
record what run_local would run instead of running it, so they need no qemu. The
last one creates real qcow2 images, and is skipped where qemu-img is not
installed.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from cijoe.core.command import Cijoe
from cijoe.core.resources import Config
from cijoe.qemu.wrapper import Guest


def make_guest(tmp_path, monkeypatch=None):
    """A Guest named 'g' under tmp_path; with monkeypatch, its commands are recorded"""

    config = Config(Path("guest.toml"))
    config.options = {
        "qemu": {
            "img_bin": "qemu-img",
            "guests": {"g": {"path": str(tmp_path / "guest")}},
        }
    }
    cijoe = Cijoe(config, tmp_path / "output", False)
    cijoe.set_output_ident("test")

    commands = []

    def record(cmd, *args, **kwargs):
        commands.append(cmd)
        return 0, None

    if monkeypatch is not None:
        monkeypatch.setattr(cijoe, "run_local", record)

    return Guest(cijoe, config, "g"), commands


def test_copy_without_overlay(tmp_path, monkeypatch):
    guest, commands = make_guest(tmp_path, monkeypatch)

    assert guest.initialize(tmp_path / "disk.qcow2", overlay=False) == 0
    assert commands == [f"cp {tmp_path / 'disk.qcow2'} {guest.boot_img}"]


def test_overlay_by_default(tmp_path, monkeypatch):
    guest, commands = make_guest(tmp_path, monkeypatch)

    assert guest.initialize(tmp_path / "disk.qcow2") == 0
    assert commands == [
        f"qemu-img create -f qcow2 -F qcow2 -b {(tmp_path / 'disk.qcow2').resolve()}"
        f" {guest.boot_img}"
    ]


def test_overlay_backing_path_is_absolute(tmp_path, monkeypatch):
    """qemu reads a relative backing path from the overlay's directory, not the cwd"""

    monkeypatch.chdir(tmp_path)
    guest, commands = make_guest(tmp_path, monkeypatch)

    assert guest.initialize("disk.qcow2") == 0
    assert f"-b {tmp_path.resolve() / 'disk.qcow2'} " in commands[0]


@pytest.mark.skipif(shutil.which("qemu-img") is None, reason="needs qemu-img")
def test_overlay_is_a_qcow2_backed_by_the_disk_image(tmp_path):
    disk = tmp_path / "disk.qcow2"
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "64M"], check=True)

    guest, _ = make_guest(tmp_path)
    assert guest.initialize(disk) == 0

    info = subprocess.run(
        ["qemu-img", "info", "--output=json", str(guest.boot_img)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert f'"backing-filename": "{disk.resolve()}"' in info
    assert '"virtual-size": 67108864' in info


def test_script_takes_the_system_image_name_from_the_config(tmp_path, monkeypatch):
    from argparse import ArgumentParser

    from cijoe.qemu.scripts import guest_initialize

    disk = tmp_path / "disk.qcow2"
    disk.write_bytes(b"")
    config = Config(Path("guest.toml"))
    config.options = {
        "qemu": {"guests": {"g": {"path": str(tmp_path), "system_image_name": "i"}}},
        "system-imaging": {"images": {"i": {"disk": {"path": str(disk)}}}},
    }
    cijoe = Cijoe(config, tmp_path / "output", False)
    initialized = []
    monkeypatch.setattr(
        Guest, "initialize", lambda self, path, overlay: initialized.append(path)
    )

    parser = ArgumentParser()
    guest_initialize.add_args(parser)
    args = parser.parse_args(["--guest_name", "g"])

    assert guest_initialize.main(args, cijoe) == 0
    assert initialized == [disk]


def test_start_passes_every_option_of_a_kwa_table(tmp_path, monkeypatch):
    guest, commands = make_guest(tmp_path, monkeypatch)
    guest.guest_config["system_label"] = "x86_64"
    guest.guest_config["system_args"] = {
        "kwa": {"machine": {"type": "q35", "accel": "kvm"}, "m": "2G"}
    }
    guest.cijoe.config.options["qemu"]["systems"] = {"x86_64": {"bin": "qemu"}}

    assert guest.start() == 0
    assert commands[0].startswith("qemu -machine type=q35,accel=kvm -m 2G ")


def test_wait_for_termination_of_a_guest_that_left_its_pidfile(tmp_path):
    """qemu leaves guest.pid behind when it is killed or crashes"""

    guest, _ = make_guest(tmp_path)
    guest.guest_path.mkdir(parents=True)
    gone = subprocess.Popen(["true"])
    gone.wait()
    guest.pid.write_text(f"{gone.pid}\n")

    assert guest.wait_for_termination(timeout=3) == (0, True)


def test_wait_for_termination_of_a_running_guest(tmp_path):
    guest, _ = make_guest(tmp_path)
    guest.guest_path.mkdir(parents=True)
    guest.pid.write_text(f"{os.getpid()}\n")

    assert guest.wait_for_termination(timeout=1) == (0, False)
