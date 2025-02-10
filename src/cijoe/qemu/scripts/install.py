#!/usr/bin/env python3
"""
Install qemu
============

Retargetable: False
-------------------
"""
import errno
from pathlib import Path


def main(args, cijoe, step):
    """Install qemu"""

    path = cijoe.getconf("qemu.repository.path", None)
    if not path:
        return errno.EINVAL

    build_dir = Path(path) / "build"

    err, _ = cijoe.run_local("make install", cwd=build_dir)

    return err
