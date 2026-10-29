"""
get
===

Copies a file from the step's target to the initiator.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import SUPPRESS, ArgumentParser

from cijoe.core.misc import deprecated


def add_args(parser: ArgumentParser):
    parser.add_argument("--src", type=str, help="path to the file on remote machine")
    parser.add_argument(
        "--dst",
        type=str,
        help="path to where the file should be placed on the initiator",
    )
    parser.add_argument("--transport", type=str, default=None, help=SUPPRESS)


def main(args, cijoe):
    """Copies the file at args.src on the remote machine to args.dst on the local machine"""

    if not ("src" in args and "dst" in args):
        log.error("missing step-argument: with.src and/or with.dst")
        return errno.EINVAL

    if args.transport:
        deprecated("core.get's 'transport'", "the step's 'target'")

    return int(not cijoe.get(args.src, args.dst, target=args.transport))
