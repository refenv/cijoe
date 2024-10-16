"""
cijoe example script
====================

An example of using the core infrastructure of cijoe:

* cijoe.run(command)

  - Error-handling; checking return-code
  - Output processing state.output()

cijoe also has primitives for transferring data:

* cijoe.get(src, dst)

  - Transfer 'src' directory or file from **target** to 'dst' on **initiator** 

* cijoe.put(src, dst)

  - Transfer 'src' directory or file from **initiator** to 'dst' on **target** 

These are not used in the example code below, but you can experiment and try adding
them yourself.
"""

import logging as log
from argparse import Namespace

from cijoe.core.command import Cijoe


def main(args: Namespace, cijoe: Cijoe, step: dict):
    """Entry-point of the cijoe-script"""

    err, state = cijoe.run("echo 'Hello World!'")
    if "Hello" not in state.output():
        log.error("Something went wrong")
        return 1

    log.info(f"All is good? err({err})")

    return err
