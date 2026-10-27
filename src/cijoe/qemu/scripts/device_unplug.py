#!/usr/bin/env python3
"""
Unplug a device from a running qemu guest
=========================================

Removes the device named 'device_name' from the running guest over its QMP
socket, waits for the guest to release it, and stops its server when it is a
vfio-user device.

Retargetable: False
-------------------
"""
import errno
import logging as log
from argparse import ArgumentParser

from cijoe.qemu.devices import unplug
from cijoe.qemu.wrapper import Guest


def add_args(parser: ArgumentParser):
    parser.add_argument("--guest_name", type=str, help="Name of the qemu guest.")
    parser.add_argument("--device_name", type=str, help="Name of the device.")


def main(args, cijoe):
    """Unplug a device from a running qemu guest"""

    for arg in ("guest_name", "device_name"):
        if not getattr(args, arg, None):
            log.error(f"missing argument: {arg}")
            return errno.EINVAL

    guest = Guest(cijoe, cijoe.config, args.guest_name)
    if not guest.is_running():
        log.error(f"guest {args.guest_name} is not running")
        return errno.ENODEV

    try:
        return unplug(cijoe, guest, args.device_name)
    except KeyError:
        log.error(f"guest {args.guest_name} has no device {args.device_name}")
        return errno.ENODEV
