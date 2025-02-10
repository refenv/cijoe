#!/usr/bin/env python3
"""
check fio
=========

Check the version of the wrapped fio. This is useful for reference and as a check that
fio-wrapper has the correct options set.

Retargetable: True
------------------
"""
import logging as log


def main(args, cijoe, step):
    """Check version of fio"""

    fio_bin = cijoe.getconf("fio.bin")
    if not fio_bin:
        log.error("missing config: fio.bin")
        return 1

    err, _ = cijoe.run(f"{fio_bin} --version")

    return err
