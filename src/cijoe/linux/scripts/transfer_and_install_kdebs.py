"""
Transfer and install Linux Kernel .deb
======================================

* Remove any files on remote side in directory "/tmp/kdebs"
* Create directory on remote side at "/tmp/kdebs"
* Transfer all .deb files in "step.with.local_kdebs_dir"
  - Store them on the remote side in "/tmp/kdebs"
* Do `dpkg -i` on all .debs in "/tmp/kdebs"

Retargetable: True
------------------

Transfer from local to remote, the config.cijoe.transport determines the remote.
"""

import errno
import logging as log
from argparse import ArgumentParser
from pathlib import Path


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--local_kdebs_dir", type=str, help="Path to local kdebs directory"
    )


def main(args, cijoe):
    if "local_kdebs_dir" not in args:
        log.error("missing step-argument: with.local_kdebs_dir")
        return errno.EINVAL

    deb_root = Path(args.local_kdebs_dir)
    deb_root = (
        deb_root if deb_root.is_absolute() else Path(args.output).parent / deb_root
    )
    remote_kdebs_dir = "/tmp/kdebs"

    log.info(f"deb_root: '{deb_root}'")

    cijoe.run(f"rm  {remote_kdebs_dir}/*.deb || true")
    cijoe.run(f"mkdir -p {remote_kdebs_dir}")

    for path in deb_root.glob("*.deb"):
        cijoe.put(f"{path}", f"{remote_kdebs_dir}/{path.name}")
        err, _ = cijoe.run(f"[ -f {remote_kdebs_dir}/{path.name} ]")
        if err:
            return err

    cijoe.run(f"ls {remote_kdebs_dir} | grep .deb")

    err, _ = cijoe.run(f"dpkg -i {remote_kdebs_dir}/*.deb")
    if err:
        return err

    return 0
