"""
cmdrunner
=========

Executes a list of commands in the given order. Note that multi-line commands are not
support, each line or list of strings are treated as individual commands.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--commands", nargs="+", type=str, help="The commands to be run"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default=None,
        help=(
            "The key of the transport from the cijoe config file on which the commands should be run. "
            "Use 'initiator' if the commands should be run locally. "
            "Defaults to the first transport in the config file ('initiator' if none are defined)."
        ),
    )


def main(args, cijoe):
    """Run commands one at a time via cijoe.run()"""

    err = 0
    if "commands" not in args:
        log.error("missing step-argument: with.commands")
        return errno.EINVAL

    for cmd in args.commands:
        err, state = cijoe.run(cmd, transport_name=args.transport)
        if err:
            break

    return err
