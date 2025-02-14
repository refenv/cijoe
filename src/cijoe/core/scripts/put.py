"""
put
===

Copies a file from local to remote.

Step Arguments
--------------

step.with.src: path to the file on local machine
step.with.dst: path to where the file should be placed on the remote machine

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument("--src", type=str, help="path to the file on local machine")
    parser.add_argument(
        "--dst",
        type=str,
        help="path to where the file should be placed on the remote machine",
    )


def main(args, cijoe):
    """Copies the file at args.src on the local machine to args.dst on the remote machine"""

    if not ("src" in args and "dst" in args):
        log.error("missing step-argument: with.src and/or with.dst")
        return errno.EINVAL

    return int(not cijoe.put(args.src, args.dst))
