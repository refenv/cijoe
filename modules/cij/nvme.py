"""
nvme.py    - Script providing operation of NVMe

Functions:
    nvme.env()          - Prepare environment for NVMe
    nvme.fmt()          - Format NVMe device
    nvme.exists()       - Check NVMe device is exists or not
    nvme.get_meta()     - Get chunk meta to file
    nvme.comp_meta()    - Compare chunk meta

Require:
    NVME_DEV_NAME       - NVMe device name
"""
import os
import traceback
from cij.struct.identify import IdentifyCDS
from cij.struct.chunk_info import get_descriptor_table, get_sizeof_descriptor_table
import cij.util
import cij.ssh
import cij.bin
import cij

PREFIX = "NVME"
REQUIRED = ["DEV_NAME"]
EXPORTED = ["DEV_PATH", "LNVM_VERSION", "SPEC_VERSION", "LNVM_NUM_CHUNKS", "LNVM_NUM_LUNS",
            "LNVM_NUM_CHS", "LNVM_TOTAL_LUNS", "LNVM_TOTAL_CHUNKS", "LNVM_CHUNK_META_SIZE",
            "LNVM_CHUNK_META_LENGTH"]


def cat_file(path):
    """Cat file and return content"""

    cmd = ["cat", path]
    status, stdout, _ = cij.ssh.command(cmd, shell=True, echo=True)
    if status:
        raise RuntimeError("cij.nvme.env: cat %s failed" % path)
    return stdout.strip()


def env():
    """Verify NVME variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.nvme.env: invalid SSH environment")
        return 1

    nvme = cij.env_to_dict(PREFIX, REQUIRED)

    nvme["DEV_PATH"] = os.path.join("/dev", nvme["DEV_NAME"])

    # get version, chunks, luns and chs
    try:
        sysfs = os.path.join("/sys/class/block", nvme["DEV_NAME"], "lightnvm")

        nvme["LNVM_VERSION"] = cat_file(os.path.join(sysfs, "version"))
        if nvme["LNVM_VERSION"] == "2.0":
            luns = "punits"
            chs = "groups"
        elif nvme["LNVM_VERSION"] == "1.2":
            luns = "num_luns"
            chs = "num_channels"
        else:
            raise RuntimeError("cij.nvme.env: invalid lnvm version: %s" % nvme["LNVM_VERSION"])

        nvme["LNVM_NUM_CHUNKS"] = cat_file(os.path.join(sysfs, "chunks"))
        nvme["LNVM_NUM_LUNS"] = cat_file(os.path.join(sysfs, luns))
        nvme["LNVM_NUM_CHS"] = cat_file(os.path.join(sysfs, chs))

        nvme["LNVM_TOTAL_LUNS"] = str(int(nvme["LNVM_NUM_LUNS"]) * int(nvme["LNVM_NUM_CHS"]))
        nvme["LNVM_TOTAL_CHUNKS"] = str(int(nvme["LNVM_TOTAL_LUNS"]) * int(nvme["LNVM_NUM_CHUNKS"]))

        # get spec version by identify namespace data struct
        if nvme["LNVM_VERSION"] == "2.0":
            cmd = ["nvme", "id-ctrl", nvme["DEV_PATH"], "--raw-binary"]
            status, stdout, _ = cij.ssh.command(cmd, shell=True)
            if status:
                raise RuntimeError("cij.nvme.env: nvme id-ctrl fail")

            buff = cij.bin.Buffer(types=IdentifyCDS, length=1)
            buff.memcopy(stdout)

            if buff[0].VS[1023] == 0x5a:
                nvme["SPEC_VERSION"] = "Denali"
            else:
                nvme["SPEC_VERSION"] = "Spec20"
        else:
            nvme["SPEC_VERSION"] = "Spec12"

        # get chunk meta information
        nvme["LNVM_CHUNK_META_LENGTH"] = str(get_sizeof_descriptor_table(nvme["SPEC_VERSION"]))
        nvme["LNVM_CHUNK_META_SIZE"] = str(int(nvme["LNVM_CHUNK_META_LENGTH"]) *
                                           int(nvme["LNVM_TOTAL_CHUNKS"]))

    except StandardError:
        traceback.print_exc()
        return 1

    cij.env_export(PREFIX, EXPORTED, nvme)

    return 0


def fmt(lbaf=3):
    """Do format for NVMe device"""

    if env():
        cij.err("cij.nvme.exists: Invalid NVMe ENV.")
        return 1

    nvme = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ["nvme", "format", nvme["DEV_PATH"], "-l", str(lbaf)]
    rcode, _, _ = cij.ssh.command(cmd, shell=True)

    return rcode


def exists():
    """Verify that the ENV defined NVMe device exists"""

    if env():
        cij.err("cij.nvme.exists: Invalid NVMe ENV.")
        return 1

    nvme = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = ["[[", "-b", nvme["DEV_PATH"], "]]"]
    rcode, _, _ = cij.ssh.command(cmd, shell=True, echo=False)
    if rcode:
        return False

    return True


def get_meta(offset, length, output):
    """Get chunk meta of NVMe device"""

    if env():
        cij.err("cij.nvme.meta: Invalid NVMe ENV.")
        return 1

    nvme = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    max_size = 0x40000
    with open(output, "wb") as fout:
        for off in range(offset, length, max_size):
            size = min(length - off, max_size)
            cmd = ["nvme get-log",
                   nvme["DEV_PATH"],
                   "-i 0xca",
                   "-o 0x%x" % off,
                   "-l 0x%x" % size,
                   "-b"]
            status, stdout, _ = cij.ssh.command(cmd, shell=True)
            if status:
                cij.err("cij.nvme.meta: Error get chunk meta")
                return 1

            fout.write(stdout)

    return 0


def comp_meta(file_bef, file_aft, mode="pfail"):
    """Compare chunk meta, mode=[pfail, power, reboot]"""
    if env():
        cij.err("cij.nvme.comp_meta: Invalid NVMe ENV.")
        return 1

    nvme = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)
    num_chk = int(nvme["LNVM_TOTAL_CHUNKS"])

    meta_bef = cij.bin.Buffer(types=get_descriptor_table(nvme['SPEC_VERSION']), length=num_chk)
    meta_aft = cij.bin.Buffer(types=get_descriptor_table(nvme['SPEC_VERSION']), length=num_chk)
    meta_bef.read(file_bef)
    meta_aft.read(file_aft)

    for chk in range(num_chk):
        ignore = ["WL", "RSV0"]

        # PFAIL: BEFORE IS OPEN CHUNK, WRITE POINTER IS NOT SURE, IGNORE
        if mode == "pfail" and meta_bef[chk].CS == 4:
            ignore.append("WP")

        # COMPARE CHUNK META
        if meta_bef.compare(meta_aft, chk, ignore=ignore):
            cij.warn("META_BUFF_BEF[%s]:" % chk)
            meta_bef.dump(chk)
            cij.warn("META_BUFF_AFT[%s]:" % chk)
            meta_aft.dump(chk)
            cij.err("Error compare, CHUNK: %s" % chk)
            return 1

    return 0
