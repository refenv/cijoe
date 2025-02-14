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

    # This will build all those starting with "debian"
    with:
      pattern: "debian*"

Retargetable: False
-------------------

This script only runs on the iniator; due to the use of 'shutil', 'download' etc.
"""
import errno
import logging as log
import shutil
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path
from pprint import pformat

from cijoe.core.misc import download
from cijoe.qemu.wrapper import Guest, qemu_img


def add_args(parser: ArgumentParser):
    parser.add_argument("--pattern", type=str, help="Pattern for image names to build")


def diskimage_from_cloudimage(cijoe, image: dict):
    """
    Build a diskimage, using qemu and cloudimage, and copy it to the diskimage location
    """

    if not (cloud := image.get("cloud", {})):
        log.error("missing .cloud entry in configuration file")
        return errno.EINVAL

    cloud_image_path = Path(cloud.get("path"))
    cloud_image_url = cloud.get("url")
    cloud_image_metadata_path = Path(cloud.get("metadata_path"))
    cloud_image_userdata_path = Path(cloud.get("userdata_path"))

    if not (disk := image.get("disk", {})):
        log.error("missing .disk entry in configuration file")
        return errno.EINVAL

    if not cloud_image_path.exists():
        cloud_image_path.parent.mkdir(parents=True, exist_ok=True)

        err, path = download(cloud_image_url, cloud_image_path)
        if err:
            log.error(f"download({cloud_image_url}), {cloud_image_path}: failed")
            return err

    if (system_label := image.get("system_label", None)) is None:
        log.error("missing .system_label entry in configuration file")
        pass

    # Get the first guest with a matching system_label
    guest_name = None
    for cur_guest_name, cur_guest in cijoe.getconf("qemu.guests", {}).items():
        guest_system_label = cur_guest.get("system_label", None)
        if guest_system_label is None:
            log.error(f"guest_name({cur_guest_name}) is missing 'system_label'")
            return errno.EINVAL

        if guest_system_label == system_label:
            guest_name = cur_guest_name
            break

    if guest_name is None:
        log.error("Could not find a guest to use for diskimage creation")
        return errno.EINVAL

    guest = Guest(cijoe, cijoe.config, guest_name)
    guest.kill()  # Ensure the guest is *not* running
    guest.initialize(cloud_image_path)  # Initialize using the cloudimage

    # Create seed.img, with data and meta embedded
    guest_metadata_path = guest.guest_path / "meta-data"
    err, _ = cijoe.run_local(f"cp {cloud_image_metadata_path} {guest_metadata_path}")
    guest_userdata_path = guest.guest_path / "user-data"
    err, _ = cijoe.run_local(f"cp {cloud_image_userdata_path} {guest_userdata_path}")

    # This uses mkisofs instead of cloud-localds, such that it works on macOS and Linux,
    # the 'mkisofs' should be available with 'cdrtools'
    seed_img = guest.guest_path / "seed.img"
    cloud_cmd = " ".join(
        [
            "mkisofs",
            "-output",
            f"{seed_img}",
            "-volid",
            "cidata",
            "-joliet",
            "-rock",
            str(guest_userdata_path),
            str(guest_metadata_path),
        ]
    )
    err, _ = cijoe.run_local(cloud_cmd)
    if err:
        log.error(f"Failed creating {seed_img}")
        return err

    # Additional args to pass to the guest when starting it
    system_args = []

    system_args += ["-cdrom", f"{seed_img}"]

    # When not daemonized then this will block until the machine shuts down, which is
    # what we want, as we want to wait for the cloudinit process to finalize
    err = guest.start(daemonize=False, extra_args=system_args)
    if err:
        log.error("Failure starting guest or during cloudinit process")
        return err

    # Copy to disk-location
    disk_path = Path(disk.get("path"))
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    err, _ = cijoe.run_local(f"cp {guest.boot_img} {disk_path}")
    if err:
        log.error(f"Failed copying to {disk_path}")
        return err

    # Resize the .qcow file This still requires that the partitions are resized with
    # e.g. growpart as part of the cloud-init process
    cijoe.run_local(f"qemu-img info {disk_path}")

    err, _ = cijoe.run_local(f"qemu-img resize {disk_path} 12G")
    if err:
        log.error("Failed resizing .qcow image")
        return err

    cijoe.run_local(f"qemu-img info {disk_path}")

    # Compute sha256sum of the disk-image
    err, _ = cijoe.run_local(f"sha256sum {disk_path} > {disk_path}.sha256")
    if err:
        log.error(f"Failed computing sha256 sum of disk_path({disk_path})")
        return err

    cijoe.run_local(f"ls -la {disk_path}")
    cijoe.run_local(f"cat {disk_path}.sha256")

    return 0


def main(args, cijoe):
    """Provision a qemu-guest using a cloud-init image"""

    if "pattern" not in args:
        log.error("missing step-argument: with.pattern")
        return errno.EINVAL
    pattern = args.pattern

    log.info(f"Got pattern({pattern})")

    entry_name = "system-imaging.images"
    images = cijoe.getconf(entry_name, {})
    if not images:
        log.error(f"missing: '{entry_name}' in configuration file")
        return errno.EINVAL

    build_status = {}
    for image_name, image in images.items():
        if not fnmatch(image_name.lower(), pattern.lower()):
            log.info(f"image_name({image_name}); did not match pattern({pattern}")
            continue

        build_status[image_name] = False
        log.info(f"image_name({image_name}); matched pattern({pattern})")

        err = diskimage_from_cloudimage(cijoe, image)
        if err:
            log.error(f"failed build_and_copy(); err({err})")
            return err

        build_status[image_name] = True

    count = sum([1 for status in build_status.values() if status])
    log.info(f"Build count({count}) disk images; status: {pformat(build_status)}")

    if not count:
        log.error(f"did not build anything, count({count}); invalid with.pattern?")
        return errno.EINVAL

    return 0
