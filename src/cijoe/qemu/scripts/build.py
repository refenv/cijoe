#!/usr/bin/env python3
"""
Build qemu system and default tools
===================================

In the build, virtfs and debugging enabled.

Configuration
-------------

* qemu.repository.path: str

  Path to the qemu repository on the target machine.

* qemu.build.prefix: str

  Prefix given to the qemu configuration in the `--prefix` argument

Retargetable: True
------------------
"""
import errno
import logging as log
from pathlib import Path


def main(args, cijoe):
    """Build qemu"""

    repos_path = cijoe.getconf("qemu.repository.path", None)
    if not repos_path:
        log.error("missing qemu.repository.path")
        return errno.EINVAL

    prefix = cijoe.getconf("qemu.build.prefix")
    if not prefix:
        log.error("missing qemu.build.prefix")
        return errno.EINVAL

    err, _ = cijoe.run(f'[ -d "{repos_path}" ]')
    if err:
        log.error(f"No qemu git-repository at repos({repos_path})")
        return err

    build_dir = Path(repos_path) / "build"

    err, _ = cijoe.run(f"mkdir -p {build_dir}")
    if err:
        return err

    configure_args = [
        f"--prefix={prefix}",
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
