"""
cijoe example of facts
======================

Observes the **target**, its kernel release and the number of CPUs it has, and
keeps what it found as facts, for the steps after it to use.

The configuration says what a task wants, and a run never changes it. What a
step finds out is a fact: the script writes it with cijoe.facts.set(), and the
steps after it read it as {{ facts.<key> }} in their 'with', or with
cijoe.facts.get() in a script. Every write saves the facts to 'facts.toml' in the
output directory, and a later run can start from them with '--facts'.

* cijoe.facts.set(key, value)

  - Replace the value at the dotted 'key'

* cijoe.facts.update(key, table)

  - Merge 'table' into the table at the dotted 'key'

* cijoe.facts.delete(key)

  - Remove the dotted 'key'

* cijoe.facts.get(key, default)

  - Read a copy of a fact back, as cijoe.getconf() reads the configuration
"""

import errno
import logging as log
from argparse import Namespace

from cijoe.core.command import Cijoe


def main(args: Namespace, cijoe: Cijoe):
    """Observe the target's kernel release and CPU count, as facts"""

    err, state = cijoe.run("uname -r")
    if err:
        log.error("uname -r failed")
        return err
    cijoe.facts.set("target.kernel", state.output().strip())

    err, state = cijoe.run("getconf _NPROCESSORS_ONLN")
    if err:
        log.error("getconf _NPROCESSORS_ONLN failed")
        return err
    try:
        cijoe.facts.set("target.cpus", int(state.output().strip()))
    except ValueError:
        log.error(f"not a CPU count: {state.output()!r}")
        return errno.EINVAL

    log.info(f"target: {cijoe.facts.get('target')}")

    return 0
