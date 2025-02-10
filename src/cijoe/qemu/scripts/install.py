#!/usr/bin/env python3
"""
Install qemu
============

Retargetable: False
-------------------
"""
import errno
import logging as log
from pathlib import Path


def main(args, cijoe, step):
    """Install qemu"""

    path = cijoe.getconf("qemu.repository.path", None)
    if not path:
        log.error("missing 'qemu.repository.path' in configuration file")
        return errno.EINVAL

    build_dir = Path(path) / "build"

    err, _ = cijoe.run_local("make install", cwd=build_dir)

    return err
