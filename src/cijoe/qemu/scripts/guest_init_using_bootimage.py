#!/usr/bin/env python3
"""
Create ``boot.img`` from a bootable disk-image
==============================================

Initialize the guest's boot image (``boot.img``) using an existing bootable
disk-image at ``qemu.guest.init_using_bootimage.img``. When the image-file is not
available, then it will be downloaded from ``qemu.guest.init_using_bootimage.url``.

Config::

    [qemu.guest.init_using_bootimage]
    url = # URL pointing to download location of the bootable disk-image
    img = # Absolute path to disk-image file"

Retargetable: False
-------------------
"""
from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Provision using an existing boot image"""

    guest = Guest(cijoe, cijoe.config)

    return guest.init_using_bootimage()
