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

    conf = cijoe.config.options.get("qemu", None)
    if not conf:
        return errno.EINVAL

    build_dir = Path(conf["repository"]["path"]) / "build"

    err, _ = cijoe.run_local("make install", cwd=build_dir)

    return err
