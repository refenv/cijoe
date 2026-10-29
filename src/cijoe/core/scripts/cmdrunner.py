"""
cmdrunner
=========

Executes a list of commands in the given order. Note that multi-line commands are not
supported; each line or list of strings is treated as an individual command.

Usage from a task
-----------------

The two steps below are equivalent. The first invokes the script directly; the
second uses the ``run:`` shorthand, which is desugared into the same call.
Either form runs the commands on the step's ``target``, by default the config's
``cijoe.default_target``::

    - name: explicit
      target: guest
      uses: core.cmdrunner
      with:
        commands:
        - hostname
        - uname -a

    - name: shorthand
      target: guest
      run: |
        hostname
        uname -a

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import SUPPRESS, ArgumentParser

from cijoe.core.misc import deprecated


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--commands", nargs="+", type=str, help="The commands to be run"
    )
    parser.add_argument("--transport", type=str, default=None, help=SUPPRESS)


def main(args, cijoe):
    """Run commands one at a time via cijoe.run()"""

    err = 0
    if args.commands is None:
        log.error("missing step-argument: with.commands")
        return errno.EINVAL

    if args.transport:
        deprecated("core.cmdrunner's 'transport'", "the step's 'target'")

    for cmd in args.commands:
        err, _ = cijoe.run(cmd, target=args.transport)
        if err:
            break

    return err
