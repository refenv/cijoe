"""
liblight.py  - Script providing operation of liblightnvm for Spec 2.0
"""
import os
import re
from cij.struct.geometry import Geometry
from cij.struct.identify import IdentifyNDS
from cij.struct.chunk_info import get_descriptor_table, get_sizeof_descriptor_table
import cij.util
import cij.nvme
import cij.ssh
import cij.bin
import cij


class Nvm(object):
    """Operation of liblightnvm"""

    def __init__(self):
        if cij.ssh.env():
            raise RuntimeError("cij.liblight: invalid SSH environment")

        cij.nvme.env()
        nvme = cij.env_to_dict("NVME", ["DEV_NAME", "SPEC_VERSION"])

        self.envs = dict()
        self.envs["DEV_PATH"] = os.path.join("/dev", nvme["DEV_NAME"])

        self.envs["CHUNK_META_STRUCT"] = get_descriptor_table(nvme["SPEC_VERSION"])
        self.envs["CHUNK_META_SIZEOF"] = get_sizeof_descriptor_table(nvme["SPEC_VERSION"])

        cmd = ["nvme", "lnvm", "id-ns", self.envs["DEV_PATH"], "--raw-binary"]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.liblight: lnvm id-ns fail")

        buff = cij.bin.Buffer(types=Geometry, length=1)
        buff.memcopy(stdout)
        geometry = buff[0]

        self.envs["MJR"] = geometry.MJR
        self.envs["NUM_GRP"] = geometry.NUM_GRP
        self.envs["NUM_PU"] = geometry.NUM_PU
        self.envs["NUM_CHK"] = geometry.NUM_CHK
        self.envs["CLBA"] = geometry.CLBA
        self.envs["CHUNKS"] = geometry.NUM_GRP * geometry.NUM_PU * geometry.NUM_CHK

        cmd = ["nvme", "id-ns", self.envs["DEV_PATH"], "--raw-binary"]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.liblight: nvme id-ns fail")

        buff = cij.bin.Buffer(types=IdentifyNDS, length=1)
        buff.memcopy(stdout)
        identify = buff[0]

        self.envs["NBYTES"] = 2 ** identify.LBAF[identify.FLBAS].LBADS
        self.envs["NBYTES_OOB"] = identify.LBAF[identify.FLBAS].MS
        self.envs["FLBAS"] = identify.FLBAS

    def get_envs(self, key):
        """Get environment of liblightnvm"""
        return self.envs[key]

    def get_chunk_meta(self, meta_file):
        """Get chunk meta table"""
        chunks = self.envs["CHUNKS"]
        if cij.nvme.get_meta(0, chunks * self.envs["CHUNK_META_SIZEOF"], meta_file):
            raise RuntimeError("cij.liblight.get_chunk_meta: fail")

        chunk_meta = cij.bin.Buffer(types=self.envs["CHUNK_META_STRUCT"], length=chunks)
        chunk_meta.read(meta_file)
        return chunk_meta

    def get_chunk_meta_item(self, chunk_meta, grp, pug, chk):
        """Get item of chunk meta table"""
        num_chk = self.envs["NUM_CHK"]
        num_pu = self.envs["NUM_PU"]
        index = grp * num_pu * num_chk + pug * num_chk + chk
        return chunk_meta[index]

    def is_free_chunk(self, chunk_meta, grp, pug, chk):
        """Check the chunk is free or not"""
        meta = self.get_chunk_meta_item(chunk_meta, grp, pug, chk)
        if meta.CS & 0x1 != 0:
            return True
        return False

    def is_closed_chunk(self, chunk_meta, grp, pug, chk):
        """Check the chunk is free or not"""
        meta = self.get_chunk_meta_item(chunk_meta, grp, pug, chk)
        if meta.CS & 0x2 != 0:
            return True
        return False

    def is_open_chunk(self, chunk_meta, grp, pug, chk):
        """Check the chunk is free or not"""
        meta = self.get_chunk_meta_item(chunk_meta, grp, pug, chk)
        if meta.CS & 0x4 != 0:
            return True
        return False

    def is_bad_chunk(self, chunk_meta, grp, pug, chk):
        """Check the chunk is offline or not"""
        meta = self.get_chunk_meta_item(chunk_meta, grp, pug, chk)
        if meta.CS & 0x8 != 0:
            return True
        return False

    def s20_to_gen(self, pugrp, punit, chunk, sectr):
        """S20 unit to generic address"""
        cmd = ["nvm_addr s20_to_gen", self.envs["DEV_PATH"],
               "%d %d %d %d" % (pugrp, punit, chunk, sectr)]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.liblight.s20_to_gen: cmd fail")

        return int(re.findall(r"val: ([0-9a-fx]+)", stdout)[0], 16)

    def gen_to_dev(self, address):
        """Generic address to device address"""
        cmd = ["nvm_addr gen2dev", self.envs["DEV_PATH"], "0x{:x}".format(address)]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.liblight.gen_to_dev: cmd fail")

        return int(re.findall(r"dev: ([0-9a-fx]+)", stdout)[0], 16)

    def vblk_erase(self, address):
        """nvm_vblk erase"""
        cmd = ["nvm_vblk erase", self.envs["DEV_PATH"], "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vblk_write(self, address, meta=False):
        """nvm_vblk write"""
        cmd = list()
        if meta:
            cmd.append("NVM_CLI_META_MODE=1")
        cmd += ["nvm_vblk write", self.envs["DEV_PATH"], "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vblk_read(self, address, meta=False):
        """nvm_vblk read"""
        cmd = list()
        if meta:
            cmd.append("NVM_CLI_META_PR=1")
        cmd += ["nvm_vblk read", self.envs["DEV_PATH"], "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_erase(self, address):
        """nvm_cmd erase"""
        cmd = ["nvm_cmd erase", self.envs["DEV_PATH"], "0x{:x}".format(address)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_write(self, address_list, file_name=None):
        """nvm_cmd write"""
        address = ["0x{:x}".format(i) for i in address_list]
        cmd = ["nvm_cmd write", self.envs["DEV_PATH"], " ".join(address)]
        if file_name:
            cmd += ["-i {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_read(self, address_list, file_name=None):
        """nvm_cmd read"""
        address = ["0x{:x}".format(i) for i in address_list]
        cmd = ["nvm_cmd read", self.envs["DEV_PATH"], " ".join(address)]
        if file_name:
            cmd += ["-o {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def scalar_write(self, address, block_count, data_file, meta_file):
        """nvme write"""
        cmd = ["nvme", "write", self.envs["DEV_PATH"], "-s 0x{:x}".format(address),
               "-c {}".format(block_count-1), "-d {}".format(data_file), "-M {}".format(meta_file),
               "-z 0x{:x}".format(block_count * self.envs["NBYTES"]),
               "-y 0x{:x}".format(block_count * self.envs["NBYTES_OOB"])]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def scalar_read(self, address, block_count, data_file, meta_file):
        """nvme read"""
        cmd = ["nvme", "read", self.envs["DEV_PATH"], "-s 0x{:x}".format(address),
               "-c {}".format(block_count - 1), "-d {}".format(data_file),
               "-M {}".format(meta_file),
               "-z 0x{:x}".format(block_count * self.envs["NBYTES"]),
               "-y 0x{:x}".format(block_count * self.envs["NBYTES_OOB"])]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_scalar_ewr(self, seed=0x0, rmode=0x2, be_id=0x1):
        """nvm_test_cmd_ewr_scalar"""
        cmd = ["nvm_test_cmd_ewr_scalar", self.envs["DEV_PATH"], str(seed), str(rmode), str(be_id)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_vector_ewr(self, seed=0x0, rmode=0x2, be_id=0x1):
        """nvm_test_cmd_ewr_vector"""
        cmd = ["nvm_test_cmd_ewr_vector", self.envs["DEV_PATH"], str(seed), str(rmode), str(be_id)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status
