"""
    Environment for LNVM
"""
import cij.util
import cij.ssh
import cij

PREFIX = "LNVM"
REQUIRED = ["BGN", "END", "DEV_TYPE"]
EXPORTED = ["DEV_NAME", "DEV_PATH"]


def env():
    """Verify LNVM variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.lnvm.env: invalid SSH environment")
        return 1

    lnvm = cij.env_to_dict(PREFIX, REQUIRED)
    nvme = cij.env_to_dict("NVME", ["DEV_NAME"])

    if "BGN" not in lnvm.keys():
        cij.err("cij.lnvm.env: invalid LNVM_BGN")
        return 1
    if "END" not in lnvm.keys():
        cij.err("cij.lnvm.env: invalid LNVM_END")
        return 1
    if "DEV_TYPE" not in lnvm.keys():
        cij.err("cij.lnvm.env: invalid LNVM_DEV_TYPE")
        return 1

    lnvm["DEV_NAME"] = "%sb%03de%03d" % (nvme["DEV_NAME"], int(lnvm["BGN"]), int(lnvm["END"]))
    lnvm["DEV_PATH"] = "/dev/%s" % lnvm["DEV_NAME"]

    cij.env_export(PREFIX, EXPORTED, lnvm)

    return 0


def create():
    """Create LNVM device"""

    if env():
        cij.err("cij.lnvm.create: Invalid LNVM ENV")
        return 1

    nvme = cij.env_to_dict("NVME", ["DEV_NAME"])
    lnvm = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)
    cij.emph("lnvm.create: LNVM_DEV_NAME: %s" % lnvm["DEV_NAME"])

    cmd = ["nvme lnvm create -d %s -n %s -t %s -b %s -e %s -f" % (
        nvme["DEV_NAME"], lnvm["DEV_NAME"], lnvm["DEV_TYPE"], lnvm["BGN"], lnvm["END"])]
    rcode, _, _ = cij.ssh.command(cmd, shell=True)
    if rcode:
        cij.err("cij.lnvm.create: FAILED")
        return 1

    return 0


def recover():
    """Recover LNVM device"""

    if env():
        cij.err("cij.lnvm.create: Invalid LNVM ENV")
        return 1

    nvme = cij.env_to_dict("NVME", ["DEV_NAME"])
    lnvm = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)
    cij.emph("lnvm.recover: LNVM_DEV_NAME: %s" % lnvm["DEV_NAME"])

    cmd = ["nvme lnvm create -d %s -n %s -t %s -b %s -e %s" % (
        nvme["DEV_NAME"], lnvm["DEV_NAME"], lnvm["DEV_TYPE"], lnvm["BGN"], lnvm["END"])]
    rcode, _, _ = cij.ssh.command(cmd, shell=True)
    if rcode:
        cij.err("cij.lnvm.recover: FAILED")
        return 1

    return 0


def remove():
    """Remove LNVM device"""

    if env():
        cij.err("cij.lnvm.create: Invalid LNVM ENV")
        return 1

    lnvm = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)
    cij.emph("lnvm.remove: LNVM_DEV_NAME: %s" % lnvm["DEV_NAME"])

    cmd = ["nvme lnvm remove -n %s" % (lnvm["DEV_NAME"])]
    rcode, _, _ = cij.ssh.command(cmd, shell=True)
    if rcode:
        cij.err("cij.lnvm.remove: FAILED")
        return 1

    return 0


def exists():
    """Verify that the ENV defined LNVM device exists"""

    if env():
        cij.err("cij.nvme.exists: Invalid NVMe ENV.")
        return 1

    lnvm = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ['[[ -b "%s" ]]' % lnvm["DEV_PATH"]]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)
    if rcode:
        return False

    return True
