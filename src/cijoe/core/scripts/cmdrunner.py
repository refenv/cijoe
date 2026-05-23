"""
cmdrunner
=========

Executes a list of commands in the given order. Note that multi-line commands are not
supported; each line or list of strings is treated as an individual command.

Usage from a task
-----------------

The two steps below are equivalent. The first invokes the script directly; the
second uses the ``run:`` shorthand, which is desugared into the same call.
Either form can carry the script's arguments (such as ``transport``) via the
``with:`` block::

    - name: explicit
      uses: core.cmdrunner
      with:
        commands:
        - hostname
        - uname -a
        transport: ssh

    - name: shorthand
      run: |
        hostname
        uname -a
      with:
        transport: ssh

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
