#!/usr/bin/env python3
"""
Wait for qemu guest termination
===============================

Note: The script will not fail if the guest does not exist.
Note: This script does not itself terminate the qemu guest.

Retargetable: False
-------------------
"""
import logging as log
import time
from argparse import ArgumentParser

from cijoe.qemu.wrapper import Guest


def add_args(parser: ArgumentParser):
    parser.add_argument("--guest_name", type=str, help="Name of the qemu guest.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Amount of seconds to wait for the qemu guest to terminate.",
    )


def main(args, cijoe):
    """Wait for termination of qemu guest"""

    if "guest_name" not in args:
        log.error("missing argument: guest_name")
        return 1

    guest = Guest(cijoe, cijoe.config, args.guest_name)

    start = time.time()
    err, terminated = guest.wait_for_termination(args.timeout)
    end = time.time()

    if terminated:
        log.info(
            f"Guest({args.guest_name}) terminated gracefully in {end-start} seconds"
        )
    else:
        log.warning(
            f"Guest({args.guest_name}) was not terminated within {args.timeout} seconds"
        )

    return err
