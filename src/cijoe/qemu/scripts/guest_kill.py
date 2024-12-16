#!/usr/bin/env python3
"""
Kill a qemu guest
=================

Retargetable: False
-------------------
"""
import logging as log

from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Kill a qemu guest"""

    guest_name = step.get("with", {}).get("guest_name", None)
    if guest_name is None:
        log.error("missing step-argument: with.guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, guest_name)

    return guest.kill()
