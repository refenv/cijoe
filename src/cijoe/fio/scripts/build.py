#!/usr/bin/env python3
"""
build fio
=========

Build fio in fio.repository.path, using prefix fio.build.prefix.

Retargetable: True
------------------
"""
import logging as log
from pathlib import Path


def main(args, cijoe, step):
    """Build fio"""

    prefix = cijoe.getconf("fio.build.prefix")
    path = cijoe.getconf("fio.repository.path")

    if None in [prefix, path]:
        log.error("missing configs: fio.build.prefix and fio.repository.path")
        return 1

    commands = [
        "make clean",
        f"./configure --prefix={prefix}",
        "make -j $(nproc)",
    ]
    for cmd in commands:
        err, _ = cijoe.run(cmd, cwd=Path(path))
        if err:
            return err

    return err
