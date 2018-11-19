"""
    Environment for liblightnvm
"""
import cij.util
import cij.test
import cij.ssh
import cij

PREFIX = "NVM"
REQUIRED = ["DEV_NAME"]
EXPORTED = ["DEV_PATH"]

CHUNK_STATE_FREE = 0x1 << 0
CHUNK_STATE_CLOSED = 0x1 << 1
CHUNK_STATE_OPEN = 0x1 << 2
CHUNK_STATE_OFFLINE = 0x1 << 3
CHUNK_STATE_RSVD4 = 0x1 << 4
CHUNK_STATE_RSVD5 = 0x1 << 5
CHUNK_STATE_RSVD6 = 0x1 << 6
CHUNK_STATE_RSVD7 = 0x1 << 7


def env():
    """Verify NVME variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.nvm.env: invalid SSH environment")
        return 1

    nvm = cij.env_to_dict(PREFIX, REQUIRED)

    if "nvme" in nvm["DEV_NAME"]:
        nvm["DEV_PATH"] = "/dev/%s" % nvm["DEV_NAME"]
    else:
        nvm["DEV_PATH"] = "traddr:%s" % nvm["DEV_NAME"]

    cij.env_export(PREFIX, EXPORTED, nvm)

    return 0


def exists():
    """Verify that the ENV defined NVMe device exists"""

    if env():
        cij.err("cij.nvm.exists: Invalid NVMe ENV.")
        return 1

    nvm = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ['[[ -b "%s" ]]' % nvm["DEV_PATH"]]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)

    return rcode


def dev_get_rprt(dev_name, pugrp=None, punit=None):
    """
    Get-log-page chunk information

    If the pugrp and punit is set, then provide report only for that pugrp/punit

    @returns the first chunk in the given state if one exists, None otherwise
    """

    cmd = ["nvm_cmd", "rprt_all", dev_name]
    if not (pugrp is None and punit is None):
        cmd = ["nvm_cmd", "rprt_lun", dev_name, str(pugrp), str(punit)]

    _, _, _, struct = cij.test.command_to_struct(cmd)
    if not struct:
        return None

    return struct["rprt_descr"]


def dev_get_chunk(dev_name, state, pugrp=None, punit=None):
    """
    Get a chunk-descriptor for the first chunk in the given state.

    If the pugrp and punit is set, then search only that pugrp/punit

    @returns the first chunk in the given state if one exists, None otherwise
    """

    rprt = dev_get_rprt(dev_name, pugrp, punit)
    if not rprt:
        return None

    return next((d for d in rprt if d["cs"] == state), None)


def addr_dev2gen(dev_name, addr):
    """Converts the given device address to gen-format"""

    return None
