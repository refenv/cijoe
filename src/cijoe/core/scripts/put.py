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


def main(args, cijoe, step):
    """Copies the file at step.with.src on the local machine to step.with.dst on the remote machine"""

    if not ("with" in step and "src" in step["with"] and "dst" in step["with"]):
        log.error("missing step-argument: with.src and/or with.dst")
        return errno.EINVAL

    return int(not cijoe.put(step["with"]["src"], step["with"]["dst"]))
