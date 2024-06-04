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

import cijoe.linux.null_blk as null_blk


def main(args, cijoe, step):
    """Insert or remove the null_blk"""

    do = step.get("with", {"do": "insert"}).get("do", "insert")
    if do == "insert":
        err, _ = null_blk.insert(cijoe)
    elif do == "remove":
        err, _ = null_blk.remove(cijoe)
    else:
        err = errno.EINVAL

    return err
