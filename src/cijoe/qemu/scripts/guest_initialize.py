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
        return errno.EINVAL

    guest = Guest(cijoe, cijoe.config, guest_name)

    system_image_name = (
        cijoe.config.options.get("qemu", {})
        .get("guests", {})
        .get(guest_name, {})
        .get("system_image_name", step.get("with", {}).get("system_image_name", None))
    )
    if system_image_name is None:
        log.error("qemu.guests.THIS.system_args.system_image_name is not set")
        return errno.EINVAL

    disk = (
        cijoe.config.options.get("system-imaging", {})
        .get("images", {})
        .get(system_image_name, {})
        .get("disk", None)
    )
    if disk is None:
        log.error(f"system-imaging.images.{system_image_name}.disk is not set")
        return errno.EINVAL

    diskimage_path = Path(disk.get("path"))
    if not diskimage_path.exists():
        diskimage_path.parent.mkdir(exist_ok=True, parents=True)
        err, path = download_and_verify(
            disk.get("url"), disk.get("url_checksum"), diskimage_path
        )
        log.info(f"err({err}, path({path})")
        if err:
            return err

    return guest.initialize(diskimage_path)
