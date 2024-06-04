#!/usr/bin/env python3
"""
build qemu-system(x86_64 aarch64)
=================================

In the build, virtfs and debugging enabled.

Arguments
---------

* repository.path
* build.prefix

Retargetable: False
-------------------
"""
import errno
import logging as log
from pathlib import Path


def main(args, cijoe, step):
    """Build qemu"""

    conf = cijoe.config.options.get("qemu", None)
    if not conf:
        log.error("config is missing 'qemu' section")
        return errno.EINVAL

    build_dir = Path(conf["repository"]["path"]) / "build"

    configure_args = [
        f"--prefix={conf['build']['prefix']}",
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

    err, _ = cijoe.run_local(f"mkdir -p {build_dir}")
    if err:
        return err

    err, _ = cijoe.run_local("../configure " + " ".join(configure_args), cwd=build_dir)
    if err:
        return err

    err, _ = cijoe.run_local("make -j $(nproc)", cwd=build_dir)
    if err:
        return err

    return 0
