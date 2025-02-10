"""
get
===

Copies a file from remote to local.

Step Arguments
--------------

step.with.src: path to the file on remote machine
step.with.dst: path to where the file should be placed on the local machine

Retargetable: True
------------------
"""

import errno
import logging as log


def main(args, cijoe, step):
    """Copies the file at step.with.src on the remote machine to step.with.dst on the local machine"""

    if not ("with" in step and "src" in step["with"] and "dst" in step["with"]):
        log.error("missing step-argument: with.src and/or with.dst")
        return errno.EINVAL

    return int(not cijoe.get(step["with"]["src"], step["with"]["dst"]))
