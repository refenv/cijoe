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

Configuration
-------------

* ``qemu.guests.<GUEST NAME>.system_image_name``: str

  Name of the system image. This will be overwritten if also given as script
  argument.

* ``system-imaging.images.<SYSTEM IMAGE NAME>.disk``: dict

  A dictionary containing the path to the disk image and, if this path does not
  exist, a URL from where the disk image cna be downloaded.

Retargetable: False
-------------------
"""
import errno
import logging as log
from argparse import ArgumentParser
from pathlib import Path

from cijoe.core.misc import download, download_and_verify
from cijoe.qemu.wrapper import Guest


def add_args(parser: ArgumentParser):
    parser.add_argument("--guest_name", type=str, help="Name of the qemu guest.")
    parser.add_argument(
        "--system_image_name",
        type=str,
        help="Name of the system image. This will overwrite any system image name defined in the configuration file.",
    )


def main(args, cijoe):
    """Provision using an existing boot image"""

    if "guest_name" not in args:
        log.error("missing argument: guest_name")
        return errno.EINVAL

    guest = Guest(cijoe, cijoe.config, args.guest_name)

    system_image_name = cijoe.getconf(
        f"qemu.guests.{args.guest_name}.system_image_name", None
    )
    if "system_image_name" in args:
        system_image_name = args.system_image_name

    if system_image_name is None:
        log.error("qemu.guests.THIS.system_image_name is not set")
        return errno.EINVAL

    if (
        disk := cijoe.getconf(f"system-imaging.images.{system_image_name}.disk", None)
    ) is None:
        log.error(f"system-imaging.images.{system_image_name}.disk is not set")
        return errno.EINVAL

    if not (diskimage_path := Path(disk.get("path"))).exists():
        if (disk_url := disk.get("url", None)) is None:
            log.error(
                f"Cannot download; no 'url' in configuration-file for disk({disk})"
            )
            return errno.EINVAL

        diskimage_path.parent.mkdir(exist_ok=True, parents=True)

        disk_url_checksum = disk.get("url_checksum", None)
        err, path = (
            download_and_verify(disk_url, disk_url_checksum, diskimage_path)
            if disk_url_checksum
            else download(disk_url, diskimage_path)
        )
        if err:
            log.error(f"err({err}, path({path})")
            return err

    err = guest.initialize(diskimage_path)
    if err:
        log.error(f"guest.initialize({diskimage_path}); err({err})")
        return err

    return 0
