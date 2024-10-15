#!/usr/bin/env python3
"""
Create ``boot.img`` from a cloud-init image
===========================================

Initialize the guest's boot image (``boot.img``) using a
cloud-init image. When the cloud-init image at
``qemu.guest.init_using_cloudinit.img`` does not
exist, then it is downloaded from
``qemu.guest.init_using_cloudinit.url`` and stored at
``qemu.guest.init_using_cloudinit.img`` for re-use.

Config::

    [qemu.guest.init_using_cloudinit]
    url = # URL of cloud-init image, e.g. on https://cloud.debian.org/images/cloud/
    img = # Path to cloud-init image
    meta = # Path to cloud-init meta-file
    user = # Path to cloud-init user-file
    pubkey = # SSH public-key to inject into guest, (when provided)

Retargetable: False
-------------------
"""
from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Provision a qemu-guest using a cloud-init image"""

    guest = Guest(cijoe, cijoe.config)

    return guest.init_using_cloudinit()
