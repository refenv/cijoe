#!/usr/bin/env python3
"""
Determine version of qemu-img and system-bins in use by qemu-guests
===================================================================

This script records the qemu-img version in the logs, ensuring the version used by the
qemu.wrapper is always available for inspection in reports. Additionally, then it goes
through the list of qemu.guests, to retrieve the version of the system bins that they
are using.

Retargetable: False
-------------------
"""
import errno
from pathlib import Path

from cijoe.qemu.wrapper import qemu_img, qemu_system


def main(args, cijoe, step):
    """Install qemu"""

    errors = []

    err, _ = qemu_img(cijoe, "--version")
    errors.append(err)

    err, _ = qemu_system(cijoe, "--version")
    errors.append(err)

    for err in errors:
        if err:
            return err

    return 0
