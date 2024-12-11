#!/usr/bin/env python3
"""
Build qemu system and default tools
===================================

In the build, virtfs and debugging enabled.

Arguments
---------

* repository.path
* build.prefix

Retargetable: True
------------------
"""
import errno
import logging as log
from pathlib import Path


def main(args, cijoe, step):
    """Build qemu"""

    conf_qemu = cijoe.getconf("qemu", None)
    if not conf_qemu:
        log.error("config is missing 'qemu' section")
        return errno.EINVAL

    repos = cijoe.getconf("qemu.repository", None)
    if not repos:
        log.error("missing qemu.repository")
        return errno.EINVAL

    err, _ = cijoe.run(f'[ -d "{repos["path"]}" ]')
    if err:
        log.error(f"No qemu git-repository at repos({repos['path']})")
        return err

    build_dir = Path(repos["path"]) / "build"

    err, _ = cijoe.run(f"mkdir -p {build_dir}")
    if err:
        return err

    configure_args = [
        f"--prefix={conf_qemu['build']['prefix']}",
        "--audio-drv-list=''",
        "--disable-docs",
        "--disable-glusterfs",
        "--disable-libnfs",
        "--disable-libusb",
        "--disable-opengl",
        "--disable-sdl",
        "--disable-smartcard",
        "--disable-spice",
        "--disable-virglrenderer",
        "--disable-vnc",
        "--disable-vte",
        "--disable-xen",
        "--enable-debug",
        "--enable-virtfs",
        "--target-list=x86_64-softmmu,aarch64-softmmu",
    ]
    err, _ = cijoe.run("../configure " + " ".join(configure_args), cwd=build_dir)
    if err:
        return err

    err, _ = cijoe.run("make -j $(nproc)", cwd=build_dir)
    if err:
        return err

    return 0
