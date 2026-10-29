"""
Gather facts about a target
===========================

Records what a target is and has under 'targets.<target>' in the facts: its
operating system, kernel, CPUs and memory, PCI functions and NVMe controllers.
The target is reached through its transport, so it may be a QEMU guest or
hardware alike, and the facts have the same layout whatever its OS:

* os: family, id, version_id, name, pretty_name
* kernel: name, release, machine
* system: cpus, memory_kib
* pci: a list of bdf, vendor, device, class, driver, by bdf; a list, as a
  bdf has a dot, which a dotted key cannot hold
* nvme.<controller>: bdf, serial, namespaces [{bdev and/or cdev, and nsid
  where the kernel or nvme-cli gives it}]
* gpu: a list of the PCI functions of class display or accelerator, each with
  its 'render' nodes on Linux
* nic: a list of the PCI functions of class network, each with its 'netdevs'
  and, on Linux, its 'rdma' devices

The OS is found by probing the target, 'uname -s', or PowerShell where there is
no 'uname'. Before each section, the tools it runs on that OS are checked, as
core.tools_check does, and recorded as facts; a section whose tools the target
lacks, or that its OS has no way of gathering here, is left out, with a log
line, so one task gathers what each target offers. A section that was gathered
and found nothing, such as no NVMe controllers, is empty. 'sections' picks the
sections to gather and 'skip' leaves some out. Other packages
add sections of their own the same way, with cijoe.facts.target().set().

A task reads the facts as '{{ target.os.id }}', for the step's target, or as
'{{ facts.targets.<name>.os.id }}'. The gathering is cijoe.core.facts.gather(),
for a script that gathers facts of its own.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import SUPPRESS, ArgumentParser

from cijoe.core.facts import SECTIONS, gather
from cijoe.core.misc import deprecated


def add_args(parser: ArgumentParser):
    parser.add_argument("--target_name", type=str, default=None, help=SUPPRESS)
    parser.add_argument(
        "--sections",
        type=str,
        default=",".join(SECTIONS),
        help=f"Comma-separated sections to gather; default: {','.join(SECTIONS)}.",
    )
    parser.add_argument(
        "--skip",
        type=str,
        default="",
        help="Comma-separated sections to leave out of those gathered.",
    )


def main(args, cijoe):
    """Gather the facts about the target"""

    if args.target_name:
        deprecated("core.facts_gather's 'target_name'", "the step's 'target'")
    target = args.target_name or cijoe.default_target
    if target not in cijoe.targets:
        log.error(f"no target({target}); known: {', '.join(cijoe.targets)}")
        return errno.EINVAL
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    skip = [s.strip() for s in args.skip.split(",") if s.strip()]
    unknown = [s for s in sections + skip if s not in SECTIONS]
    if unknown:
        log.error(
            f"unknown sections({', '.join(unknown)}); known: {', '.join(SECTIONS)}"
        )
        return errno.EINVAL
    if not gather(cijoe, target, [s for s in sections if s not in skip]):
        log.error(f"target({target}): neither 'uname -s' nor PowerShell answers")
        return errno.EIO

    return 0
