"""
put
===

Copies a file from local to remote.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument("--src", type=str, help="path to the file on initiator")
    parser.add_argument(
        "--dst",
        type=str,
        help="path to where the file should be placed on the remote machine",
    )
    parser.add_argument(
        "--transport",
        type=str,
        default=None,
        help=(
            "The name of the transport which should be considered as the remote machine. "
            "Use 'initiator' if the commands should be run locally. "
            "Defaults to the first transport in the config file ('initiator' if none are defined)."
        ),
    )


def main(args, cijoe):
    """Copies the file at args.src on the local machine to args.dst on the remote machine"""

    if not ("src" in args and "dst" in args):
        log.error("missing step-argument: with.src and/or with.dst")
        return errno.EINVAL

    return int(not cijoe.put(args.src, args.dst, transport_name=args.transport))
