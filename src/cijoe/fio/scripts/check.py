#!/usr/bin/env python3
"""
check fio
=========

Check the version of the wrapped fio. This is useful for reference and as a check that
fio-wrapper has the correct options set.

Retargetable: True
------------------
"""
from cijoe.fio.wrapper import fio


def main(args, cijoe, step):
    """Check version of fio"""

    err, _ = fio(cijoe, "--help")

    return err
