"""
insert / remove null_blk
========================

Insert or remove null_blk instances, based on the value of step.args.do

* steps.args.do == "insert"
  - Insert the nullblk module

* step.args.do == "remove"
  - Remove the nullblk module

Retargetable: True
------------------
"""

import errno
from argparse import ArgumentParser

import cijoe.linux.null_blk as null_blk


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--do",
        choices=["insert", "remove"],
        default="insert",
        help="The commands to be run",
    )


def main(args, cijoe):
    """Insert or remove the null_blk"""

    do = args.do
    if do == "insert":
        err, _ = null_blk.insert(cijoe)
    elif do == "remove":
        err, _ = null_blk.remove(cijoe)
    else:
        err = errno.EINVAL

    return err
