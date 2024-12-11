"""
cijoe example script
====================

The script is a modified "Hello, World!" example. It repeatedly prints a message a set
number of times and allows parameterization of the message content.

The purpose of this script is to demonstrate how to run commands and supply input to the
script using a configuration file, environment variables, and workflow step arguments.

An example of using the core infrastructure of cijoe:

* cijoe.run(command)

  - Error-handling; checking return-code
  - Output processing state.output()

Input is given to scripts via configuration-files, environment variables and from
workflow-step-arguments, this is demonstrated as the first thing in the script.

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

    # Grab message from configuration-file
    message = cijoe.getconf("example.message", "Hello World!")

    # When executed via workflow, grab the step-argument
    repeat = int(step.get("with", {}).get("repeat", 1))
    if repeat < 1:
        log.error(f"Invalid step-argument: repeat({repeat}) < 1")
        return 1

    log.info(f"Will echo the message({message}), repeat({repeat}) times")

    # Now, execute a command that echoes the 'message' 'repeat' number of times
    for _ in range(1, repeat + 1):
        err, state = cijoe.run(f"echo '{message}'")
        if "Hello" not in state.output():
            log.error("Something went wrong")
            return 1

    log.info("Success!")

    return 0
