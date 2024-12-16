#!/usr/bin/env python3
"""
Start a qemu guest
==================


Retargetable: false
-------------------
"""
import errno
import logging as log

from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Start a qemu guest"""

    guest_name = step.get("with", {}).get("guest_name", None)
    if guest_name is None:
        log.error("missing step-argument: with.guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, guest_name)

    err = guest.start()
    if err:
        log.error(f"guest.start() : err({err})")
        return err

    started = guest.is_up(timeout=180)
    if not started:
        log.error("guest.is_up() : False")
        return errno.EAGAIN

    return 0
