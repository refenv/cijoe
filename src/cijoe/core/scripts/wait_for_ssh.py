#!/usr/bin/env python3
"""
Wait for transport SSH to be ready
==================================

Note: The script will not fail if the transport does not exist.

Retargetable: False
-------------------
"""
import logging as log
import time
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--transport_name",
        type=str,
        default=None,
        help="Name of the transport to be used. If none given, it uses the first defined transport in the config.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Amount of seconds to wait for SHH to be ready.",
    )


def main(args, cijoe):
    """Wait for SSH to be ready on a given transport"""

    began = time.time()
    while True:
        enter = time.time()
        try:
            err, state = cijoe.run(
                "echo 'It is alive!'",
                transport_name=args.transport_name,
            )
            if not err and "It is alive!" in state.output():
                break
        except Exception:
            # do nothing
            ...

        now = time.time()
        elapsed_iter = now - enter
        elapsed_total = now - began

        if elapsed_iter < 5.0:
            time.sleep(5.0 - elapsed_iter)
        if elapsed_total > args.timeout:
            log.error(f"System did not come up within timeout({args.timeout}) seconds")
            return False

    return 0
