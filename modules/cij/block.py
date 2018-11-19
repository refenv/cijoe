"""
    Environment for BLOCK devices
"""
import cij.util
import cij.ssh
import cij

PREFIX = "BLOCK"
REQUIRED = ["DEV_NAME"]
EXPORTED = ["DEV_PATH"]


def env():
    """Verify BLOCK variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.block.env: invalid SSH environment")
        return 1

    block = cij.env_to_dict(PREFIX, REQUIRED)

    block["DEV_PATH"] = "/dev/%s" % block["DEV_NAME"]

    cij.env_export(PREFIX, EXPORTED, block)

    return 0


def exists():
    """Verify that the ENV defined BLOCK device exists"""

    if env():
        cij.err("cij.block.exists: invalid BLOCK environment")
        return 1

    block = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ['[[ -b "%s" ]]' % block["DEV_PATH"]]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)

    return rcode
