#!/usr/bin/env python3
"""
Create disk-image using a cloud-image
=====================================

This will produce disk images for all the system images described in config. section:

* ``system_imaging.collection``

You can reduce this by providing a glob expression as input to the script via workflow.

This will start a temporary qemu-guest, providing it with a cloud bla bla.

Todo
----

Add glob-expression as input argument

Retargetable: False
-------------------
"""
import logging as log
import shutil
from pathlib import Path

from cijoe.core.misc import download
from cijoe.qemu.wrapper import Guest, qemu_img


def main(args, cijoe, step):
    """Provision a qemu-guest using a cloud-init image"""

    guest = Guest(cijoe, cijoe.config)
    guest.kill()  # Ensure the guest is *not* running
    guest.initialize()  # Ensure the guest has a "home"

    entry_name = "system-imaging.images"
    entry = next(iter(cijoe.getconf(entry_name, {}).items()), None)
    if entry is None:
        log.error(f"missing entry({entry_name}) in configuration file")
        return 1

    image_name, image = entry

    log.error(entry)
    log.error(image_name)
    log.error(image)

    cloud = image.get("cloud", {})
    if not cloud:
        log.error("missing entry({entry}.cloud) in configuration file")
        return 1

    cloud_image_path = Path(cloud.get("path"))
    cloud_image_url = cloud.get("url")
    cloud_image_metadata_path = Path(cloud.get("metadata_path"))
    cloud_image_userdata_path = Path(cloud.get("userdata_path"))

    disk = image.get("disk", {})
    if not disk:
        log.error("missing entry({entry}.disk) in configuration file")
        return 1

    # disk_url = disk.get("url")
    # disk_path = Path(disk.get("path"))

    if not cloud_image_path.exists():
        cloud_image_path.parent.mkdir(parents=True, exist_ok=True)

        err, path = download(cloud_image_url, cloud_image_path)
        if err:
            log.error(f"download({cloud_image_url}), {cloud_image_path}: failed")
            return err

    # Copy cloudimage into guest as "boot.img" and grow it to 10G
    shutil.copyfile(str(cloud_image_path), str(guest.boot_img))
    qemu_img(cijoe, f"resize {guest.boot_img} 10G")

    # Create seed.img, with data and meta embedded
    metadata_path = shutil.copyfile(
        cloud_image_metadata_path, guest.guest_path / "meta-data"
    )
    userdata_path = shutil.copyfile(
        cloud_image_userdata_path, guest.guest_path / "user-data"
    )

    # This uses mkisofs instead of cloud-localds, such that it works on macOS and Linux,
    # the 'mkisofs' should be available with 'cdrtools'
    cloud_cmd = " ".join(
        [
            "mkisofs",
            "-output",
            str(guest.seed_img),
            "-volid",
            "cidata",
            "-joliet",
            "-rock",
            str(userdata_path),
            str(metadata_path),
        ]
    )
    err, _ = cijoe.run_local(cloud_cmd)

    # Additional args to pass to the guest when starting it
    system_args = []
    system_args += ["-drive", f"file={guest.seed_img},if=virtio,format=raw"]

    err = guest.start(daemonize=False, extra_args=system_args)
    if err:
        log.error("failed starting...")
        return err

    return 0
