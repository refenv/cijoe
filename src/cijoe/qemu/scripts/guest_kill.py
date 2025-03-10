#!/usr/bin/env python3
"""
Kill a qemu guest
=================

Shutdown qemu guests by killing the process using the pid associated with the
given guest name. 

Note: The script will not fail if the guest does not exist.

Retargetable: False
-------------------
"""
import logging as log
from argparse import ArgumentParser

from cijoe.qemu.wrapper import Guest


def add_args(parser: ArgumentParser):
    parser.add_argument("--guest_name", type=str, help="Name of the qemu guest.")


def main(args, cijoe):
    """Kill a qemu guest"""

    if "guest_name" not in args:
        log.error("missing argument: guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, args.guest_name)

    return guest.kill()
