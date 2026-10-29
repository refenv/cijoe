"""
collect Linux system information
================================

Collects a bunch of information about the system kernel and hardware.

Deprecated: use core.facts_gather, which records the target's OS, kernel, CPUs,
memory, PCI functions and NVMe controllers as facts. This will be removed in v1.0,
with the rest of the linux package.

Retargetable: True
------------------
"""

from cijoe.core.misc import deprecated


def main(args, cijoe):
    """Collect Linux system information"""

    deprecated("linux.sysinfo", "core.facts_gather")

    commands = [
        "hostname",
        "lsb_release --all || cat /etc/os-release",
        "uname -a",
        "cat /boot/config-$(uname -r)",
        "set",
        "lsblk",
        "lscpu",
        "lslocks",
        "lslogins",
        "lsmem",
        "lsmod",
        "lspci",
    ]

    err = 0
    for cmd in commands:
        err, state = cijoe.run(cmd)
        if err:
            err = err

    return err
