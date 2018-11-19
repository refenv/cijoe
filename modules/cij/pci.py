"""
    Environment for PCI devices
"""
import os
import cij.util
import cij.ssh
import cij

PREFIX = "PCI"
REQUIRED = ["DEV_NAME"]
EXPORTED = ["DEV_PATH"]


def env():
    """Verify PCI variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.pci.env: invalid SSH environment")
        return 1

    pci = cij.env_to_dict(PREFIX, REQUIRED)

    pci["BUS_PATH"] = "/sys/bus/pci"
    pci["DEV_PATH"] = os.sep.join([pci["BUS_PATH"], "devices", pci["DEV_NAME"]])

    cij.env_export(PREFIX, EXPORTED, pci)

    return 0


def exists():
    """Verify that the ENV defined PCI device exists"""

    if env():
        cij.err("cij.pci.exists: invalid PCI environment")
        return 1

    pci = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ['[[ -b "%s" ]]' % pci["DEV_PATH"]]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)

    return rcode
