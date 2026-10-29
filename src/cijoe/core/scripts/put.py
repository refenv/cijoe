"""
put
===

Copies a file from the initiator to the step's target.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import SUPPRESS, ArgumentParser

from cijoe.core.misc import deprecated


def add_args(parser: ArgumentParser):
    parser.add_argument("--src", type=str, help="path to the file on initiator")
    parser.add_argument(
        "--dst",
        type=str,
        help="path to where the file should be placed on the remote machine",
    )
    parser.add_argument("--transport", type=str, default=None, help=SUPPRESS)


def main(args, cijoe):
    """Copies the file at args.src on the local machine to args.dst on the remote machine"""

    if not args.src:
        log.error("missing step-argument: with.src")
        return errno.EINVAL

    if args.transport:
        deprecated("core.put's 'transport'", "the step's 'target'")

    return int(not cijoe.put(args.src, args.dst, target=args.transport))
