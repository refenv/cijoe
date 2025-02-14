"""
collect Linux system information
================================

Collects a bunch of information about the system kernel and hardware.

Retargetable: True
------------------
"""


def main(args, cijoe):
    """Collect Linux system information"""

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
