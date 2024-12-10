#!/usr/bin/env python3
"""
Create disk image using a cloud image
=====================================

This will produce disk images for all the system images described in config. section:

* ``system_imaging.images``

You can reduce this by providing a case-incensitive fnmatch pattern as input to the
script via workflow, such as these::

    # This will build all images
    with:
      pattern: "*"

    # This will build all those starting with alpine
    with:
      pattern: "alpine*"

Retargetable: False
-------------------

This script only runs on the iniator; due to the use of 'shutil', 'download' etc.
"""
import logging as log
import shutil
from fnmatch import fnmatch
from pathlib import Path

from cijoe.core.misc import download
from cijoe.qemu.wrapper import Guest, qemu_img


def diskimage_from_cloudimage(cijoe, image: dict):
    """
    Build a diskimage, using qemu and cloudimage, and copy it to the diskimage location
    """

    guest = Guest(cijoe, cijoe.config)
    guest.kill()  # Ensure the guest is *not* running
    guest.initialize()  # Ensure the guest has a "home"

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

    # When not daemonized then this will block until the machine shuts down, which is
    # what we want, as we want to wait for the cloudinit process to finalize
    err = guest.start(daemonize=False, extra_args=system_args)
    if err:
        log.error("Failure starting guest or during cloudinit process")
        return err

    # Copy to disk-location
    disk_path = Path(disk.get("path"))
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cloud_image_path, disk_path)

    # Compute sha256sum of the disk-image
    err, _ = cijoe.run_local(f"sha256sum {disk_path} > {disk_path}.sha256")
    if err:
        log.error("Failed computing sha256 sum")
        return err

    cijoe.run_local(f"ls -la {disk_path}")
    cijoe.run_local(f"cat {disk_path}.sha256")

    return 0


def main(args, cijoe, step):
    """Provision a qemu-guest using a cloud-init image"""

    pattern = step.get("with", {}).get("pattern", None)
    if pattern is None:
        log.error("missing step-argument: with.pattern")
        return 1

    log.info(f"Got pattern({pattern})")

    entry_name = "system-imaging.images"
    images = cijoe.getconf(entry_name, {})
    if not images:
        log.error(f"missing: '{entry_name}' in configuration file")
        return 1

    count = 0
    for image_name, image in cijoe.getconf("system-imaging.images", {}).items():
        if not fnmatch(image_name.lower(), pattern.lower()):
            log.info(f"image_name({image_name}); did not match pattern({pattern}")
            continue

        log.info(f"image_name({image_name}); matched pattern({pattern})")

        err = diskimage_from_cloudimage(cijoe, image)
        if err:
            log.error(f"failed build_and_copy(); err({err})")
            return err

        count += 1

    if not count:
        log.error(f"did not build anything, count({count}); invalid with.pattern?")
        return err

    return 0
