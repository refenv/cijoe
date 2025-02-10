#!/usr/bin/env python3
"""
install fio
===========

Just a plain 'make install' within 'repository.path'

Retargetable: True
------------------
"""
import logging as log
from pathlib import Path


def main(args, cijoe, step):
    """Install fio"""

    path = cijoe.getconf("fio.repository.path")
    if not path:
        log.error("missing config: fio.repository.path")
        return 1

    err, _ = cijoe.run("make install", cwd=Path(path))
    return err
