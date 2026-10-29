#!/usr/bin/env python3
"""
Wait for a target to be up or down
==================================

Blocks until the step's target becomes reachable, e.g. after a reboot, or
unreachable, e.g. during shutdown. The target is the step's 'target', by
default the config's 'cijoe.default_target', and must be one reached over SSH,
'[cijoe.targets.<name>.ssh]'.

Example Use Case
----------------

A typical task might look like::

    - name: reboot
      target: guest
      run: shutdown -r now

    - name: wait_for_down
      target: guest
      uses: core.wait_for_target
      with:
        state: "down"
        timeout: 60

    - name: wait_for_up
      target: guest
      uses: core.wait_for_target
      with:
        state: "up"
        timeout: 300

State Detection
---------------

The target is considered *up* when its SSH port accepts a connection and a
simple command succeeds over it. To ensure portability across Linux, macOS,
BSD, and Windows, the ``hostname`` command is used as the probe. It is
*down* when the port is closed, or open while the command fails.

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
        "--state",
        choices=("down", "up"),
        default="up",
        help="Desired target state to wait for: 'down' or 'up'. Default: up.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum seconds to wait for the desired state.",
    )


def main(args, cijoe):
    """
    Wait until the target reaches the requested state.
    Return 0 on success, 1 on timeout or invalid target.
    """

    target = cijoe.default_target
    if target == "initiator":
        log.error("target(initiator) is cijoe's own machine; wait on a target")
        return 1

    ssh = cijoe.getconf(f"cijoe.targets.{target}.ssh", {})
    hostname = ssh.get("hostname", "")
    if not hostname:
        log.error(f"No hostname in [cijoe.targets.{target}.ssh]")
        return 1

    port = int(ssh.get("port", 22))
    want_up = args.state == "up"
    start = int(time.monotonic())

    log.info(
        f"Waiting max seconds({args.timeout}) for target({target}) state({args.state})..."
    )

    while True:
        try:
            with socket.create_connection((hostname, port), timeout=2.0):
                tcp_up = True
        except OSError:
            tcp_up = False

        # If waiting for DOWN and TCP is closed, we're done immediately.
        if not want_up and not tcp_up:
            log.info("Success: target(%s) is now down (TCP closed).", target)
            return 0

        if tcp_up:
            # TCP is open - verify with the trivial command to distinguish usable vs. unusable SSH.
            # The target keeps its connection between commands; closing it first makes the probe
            # a fresh connect, which is what tells a host that went down or came up.
            try:
                cijoe.close(target)
                err, _ = cijoe.run("hostname", target=target)
                ssh_up = err == 0
            except Exception as exc:
                log.debug("Probe exception treated as down: %r", exc)
                ssh_up = False

            # Waiting for UP and the command works -> success.
            if want_up and ssh_up:
                log.info("Success: target(%s) is now up.", target)
                return 0

            # Waiting for DOWN and the command fails despite TCP open -> down.
            if not want_up and not ssh_up:
                log.info("Success: target(%s) is now down (SSH unusable).", target)
                return 0

        if (int(time.monotonic()) - start) >= args.timeout:
            break
        time.sleep(2.0)

    log.error(
        f"Timeout after seconds({args.timeout}): target({target}) did not become {args.state}.",
    )
    return 1
