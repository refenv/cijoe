#!/usr/bin/env python3
"""
Guest initialization
====================

This script initializes a guest environment by setting up the necessary resources 
for guest-instance management. It creates a directory structure to store files 
related to the guest, such as:

- PID files
- Monitor files
- Serial input/output logs
- Other instance-specific metadata

Additionally, the script prepares guest storage, including the boot drive, 
using an existing `.qcow2` image (e.g., created via Cloud-init, Packer, etc.).

Retargetable: False
-------------------
"""
import errno
import logging as log
from pathlib import Path

from cijoe.core.misc import download_and_verify
from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Provision using an existing boot image"""

    guest_name = step.get("with", {}).get("guest_name", None)
    if guest_name is None:
        log.error("missing step-argument: with.guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, guest_name)

    diskimage_name = (
        cijoe.config.options.get("qemu", {})
        .get("guests", {})
        .get(guest_name, {})
        .get("system_args", {})
        .get("diskimage", None)
    )
    if diskimage_name is None:
        log.error("qemu.guests.THIS.system_args.diskimage is not set")
        return errno.EINVAL

    disk = (
        cijoe.config.options.get("system-imaging", {})
        .get("images", {})
        .get(diskimage_name, {})
        .get("disk", None)
    )
    if disk is None:
        log.error(f"system-imaging.images.{diskimage_name}.disk is not set")
        return errno.EINVAL

    disk_path = Path(disk.get("path"))
    if not disk_path.exists():
        disk_path.parent.mkdir(exist_ok=True, parents=True)
        err, path = download_and_verify(
            disk.get("url"), disk.get("url_checksum"), disk_path
        )
        log.info(f"err({err}, path({path})")
        if err:
            return err

    return guest.initialize(disk_path)
