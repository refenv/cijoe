#!/usr/bin/env python3
"""
Wait for a transport to be up or down
=====================================

Deprecated: use ``core.wait_for_target``, with the step's ``target`` in place
of ``transport_name``. This waits as that does, on ``transport_name`` when it
is given.

Retargetable
------------

**True**
"""

import logging as log
from argparse import ArgumentParser

from cijoe.core.misc import deprecated
from cijoe.core.scripts import wait_for_target


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--transport_name",
        type=str,
        default=None,
        help="Name of the target to wait for; default: the step's target.",
    )
    wait_for_target.add_args(parser)


def main(args, cijoe):
    """Wait as core.wait_for_target does, on 'transport_name' when given"""

    deprecated("core.wait_for_transport", "core.wait_for_target")
    if not args.transport_name:
        return wait_for_target.main(args, cijoe)

    deprecated("core.wait_for_transport's 'transport_name'", "the step's 'target'")
    step_target = cijoe.default_target
    try:
        cijoe.default_target = args.transport_name
    except ValueError as exc:
        log.error(exc)
        return 1
    try:
        return wait_for_target.main(args, cijoe)
    finally:
        cijoe.default_target = step_target
