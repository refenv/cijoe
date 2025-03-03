#!/usr/bin/env python3
"""
Install qemu
============

Configuration
-------------

* qemu.repository.path: str

  Path to the qemu repository on the target machine.

Retargetable: False
-------------------
"""
import errno
import logging as log
from pathlib import Path


def main(args, cijoe):
    """Install qemu"""

    path = cijoe.getconf("qemu.repository.path", None)
    if not path:
        log.error("missing 'qemu.repository.path' in configuration file")
        return errno.EINVAL

    build_dir = Path(path) / "build"

    err, _ = cijoe.run_local("make install", cwd=build_dir)

    return err
