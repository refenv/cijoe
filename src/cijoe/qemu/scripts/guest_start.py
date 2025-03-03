#!/usr/bin/env python3
"""
Start a qemu guest
==================

Retargetable: false
-------------------
"""
import errno
import logging as log
from argparse import ArgumentParser

from cijoe.qemu.wrapper import Guest


def add_args(parser: ArgumentParser):
    parser.add_argument("--guest_name", type=str, help="Name of the qemu guest.")


def main(args, cijoe):
    """Start a qemu guest"""

    if "guest_name" not in args:
        log.error("missing argument: guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, args.guest_name)

    err = guest.start()
    if err:
        log.error(f"guest.start() : err({err})")
        return err

    started = guest.is_up(timeout=180)
    if not started:
        log.error("guest.is_up() : False")
        return errno.EAGAIN

    return 0
