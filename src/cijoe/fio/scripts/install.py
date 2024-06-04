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

    err, _ = cijoe.run(
        "make install", cwd=Path(cijoe.config.options["fio"]["repository"]["path"])
    )
    return err
