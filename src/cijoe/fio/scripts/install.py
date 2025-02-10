#!/usr/bin/env python3
"""
install fio
===========

Just a plain 'make install' within 'repository.path'

Retargetable: True
------------------
"""
from pathlib import Path


def main(args, cijoe, step):
    """Install fio"""

    path = cijoe.getconf("fio.repository.path")

    err, _ = cijoe.run("make install", cwd=Path(path))
    return err
