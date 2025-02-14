#!/usr/bin/env python3
"""
Determine version of qemu-img and qemu-system-bins
==================================================

This script records the qemu-img, qemu-system-x86_64, qemu-system-aarch64, etc. versions
in the runlogs, ensuring the version used by the qemu.wrapper is always available for
inspection in reports.

Retargetable: False
-------------------
"""
from cijoe.qemu.wrapper import qemu_img, qemu_system


def main(args, cijoe):
    """Install qemu"""

    errors = []

    err, _ = qemu_img(cijoe, "--version")
    errors.append(err)

    for system_label in cijoe.getconf("qemu.systems", {}).keys():
        err, _ = qemu_system(cijoe, system_label, "--version")
        errors.append(err)

    for err in errors:
        if err:
            return err

    return 0
