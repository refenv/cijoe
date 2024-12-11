#!/usr/bin/env python3
"""
Run qemu-system version
=======================

This script records the qemu-system version in the logs, ensuring the version used by
the qemu.wrapper is always available for inspection in reports.

Retargetable: False
-------------------
"""
import errno
from pathlib import Path

from cijoe.qemu.wrapper import qemu_system


def main(args, cijoe, step):
    """Install qemu"""

    err, _ = qemu_system(cijoe, "--version")

    return err
