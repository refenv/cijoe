#!/usr/bin/env python3
"""
Install qemu
============

Deprecated: this will be removed in v1.0, along with building QEMU from source. Install
QEMU from your distribution, or as upstream provides it, and point the
qemu.systems and qemu.img_bin configuration at its binaries.

This script installs qemu on the host machine. It is assumed that qemu has been
built in advance at the given repository path.

Configuration
-------------

* ``qemu.repository.path``: str

  Path to the qemu repository on the target machine.

Retargetable: False
-------------------
"""
import errno
import logging as log
from pathlib import Path

from cijoe.core.misc import deprecated


def main(args, cijoe):
    """Install qemu"""

    deprecated("qemu.install")

    path = cijoe.getconf("qemu.repository.path", None)
    if not path:
        log.error("missing 'qemu.repository.path' in configuration file")
        return errno.EINVAL

    build_dir = Path(path) / "build"

    err, _ = cijoe.run_local("make install", cwd=build_dir)

    return err
