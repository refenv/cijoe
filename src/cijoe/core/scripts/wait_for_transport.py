#!/usr/bin/env python3
"""
Wait for Transport State (Up or Down)
=====================================

This script is useful in CIJOE workflows where execution should block until a
transport becomes available (e.g., after a reboot) or unavailable (e.g., during
shutdown).

Transport Configuration
-----------------------

Transports are defined in ``config.toml`` under the key
``cijoe.transport.{transport_name}``. For example::

    [cijoe.transport.ssh]
    username = "foo"
    hostname = "bar"

Note: ``ssh`` is a transport **name**, not a transport type.
So, ``transport_name = "ssh"``.

Example Use Case
----------------

A typical workflow might look like::

    - name: reboot
      run: shutdown -r now

    - name: wait_for_down
      uses: wait_for_transport
      with:
        state: "down"
        timeout: 60

    - name: wait_for_up
      uses: wait_for_transport
      with:
        state: "up"
        timeout: 300

Transport State Detection
-------------------------

The transport is considered *up* if a simple command can be executed
successfully over it. To ensure portability across Linux, macOS, BSD, and
Windows, the ``hostname`` command is used as the probe.

Retargetable
------------

**True**
"""

import logging as log
import socket
import time
from argparse import ArgumentParser


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--transport_name",
        type=str,
        default=None,
        help=(
            "Name of the transport to be used. If none is given, use the first defined "
            "transport in the config."
        ),
    )
    parser.add_argument(
        "--state",
        choices=("down", "up"),
        default="up",
        help="Desired transport state to wait for: 'down' or 'up'. Default: up.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum seconds to wait for the desired state.",
    )


def main(args, cijoe):
    """
    Wait until the given transport reaches the requested state.
    Return 0 on success, 1 on timeout or invalid transport.
    """

    # Pick transport name: explicit if given, else first defined
    transport_name = args.transport_name or next(
        iter(cijoe.getconf("cijoe.transport", {})), None
    )
    if not transport_name:
        log.error("No transport_name given, and none to select in cijoe.transport")
        return 1

    transport = cijoe.getconf(f"cijoe.transport.{transport_name}", {})
    hostname = transport.get("hostname", "")
    if not transport or not hostname:
        log.error(f"Invalid transport({transport})")
        return 1

    port = int(transport.get("port", 22))
    want_up = args.state == "up"
    start = int(time.monotonic())

    log.info(
        f"Waiting max seconds({args.timeout}) for transport({transport_name}) state({args.state})..."
    )

    while (int(time.monotonic()) - start) < args.timeout:
        time.sleep(2.0)

        try:
            with socket.create_connection((hostname, port), timeout=2.0):
                tcp_up = True
        except OSError:
            tcp_up = False

        # If waiting for DOWN and TCP is closed, we're done immediately.
        if not want_up and not tcp_up:
            log.info("Success: transport(%s) is now down (TCP closed).", transport_name)
            return 0

        # If waiting for UP and TCP is closed, skip SSH probe and try again.
        if want_up and not tcp_up:
            continue

        # TCP is open - verify with the trivial command to distinguish usable vs. unusable SSH.
        try:
            err, _ = cijoe.run("hostname", transport_name=transport_name)
            ssh_up = err == 0
        except Exception as exc:
            log.debug("Probe exception treated as down: %r", exc)
            ssh_up = False

        # Waiting for UP and the command works -> success.
        if want_up and ssh_up:
            log.info("Success: transport(%s) is now up.", transport_name)
            return 0

        # Waiting for DOWN and the command fails despite TCP open -> down.
        if not want_up and not ssh_up:
            log.info(
                "Success: transport(%s) is now down (SSH unusable).", transport_name
            )
            return 0

    log.error(
        f"Timeout after seconds({args.timeout}): transport({transport_name}) did not become {args.state}.",
    )
    return 1
