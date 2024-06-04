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

    guest = Guest(cijoe, cijoe.config)

    err = guest.start()
    if err:
        log.error(f"guest.start() : err({err})")
        return err

    started = guest.is_up()
    if not started:
        log.error("guest.is_up() : False")
        return errno.EAGAIN

    return 0
