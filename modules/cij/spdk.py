"""
spdk.py  - Script providing operation of spdk
"""
import os
import re
import yaml
# from cij.struct.geometry import Geometry
# from cij.struct.identify import IdentifyNDS
# from cij.struct.chunk_info import DescriptorTable, get_sizeof_descriptor_table
import cij.util
import cij.nvme
import cij.ssh
import cij.bin
import cij


class Spdk(object):
    """spdk parameter"""
    def __init__(self):
        self.envs = cij.ENV.get("NVM_DEV_NAME")
        cmd = ["/opt/spdk/scripts/setup.sh"]
        STA, _, _ = cij.test.command(cmd)
        if STA != 0:
            raise RuntimeError("setup error: %r != expected: %r" % (STA, 0))
        cmd = ["nvm_dev info", self.envs]
        status, output, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("nvm_cmd idfy fail")

        result_list = output.split('\n')
        temp_list = []
        for i in range(0, len(result_list)):
            if result_list[i].startswith('#'):
                pass
            elif result_list[i].startswith('EAL'):
                pass
            elif result_list[i].startswith('['):
                pass
            elif result_list[i].startswith('Starting'):
                pass
            else:
                temp_list.append(result_list[i])
        strings = '\n'.join(temp_list)
        self.yml = yaml.load(strings)

    def get_env(self, key1, key2):
        return self.yml[key1][key2]

    @staticmethod
    def get_chunk_status(chk, yml):
        """Get item of chunk meta table"""
        cs = yml['rprt_descr'][chk]['cs']
        return cs

    def get_chunk_information(self, chk, lun, chunk_name):
        """Get chunk information"""
        cmd = ["nvm_cmd rprt_lun", self.envs,
               "%d %d > %s" % (chk, lun, chunk_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def is_bad_chunk(self, chk, yml):
        """Check the chunk is offline or not"""
        cs = self.get_chunk_status(chk, yml)
        if cs >= 8:
            return True
        return False

    def is_free_chunk(self, chk):
        """Check the chunk is free or not"""
        cs = self.get_chunk_status(chk)
        if cs & 0x1 != 0:
            return True
        return False

    def is_closed_chunk(self, chk):
        """Check the chunk is free or not"""
        cs = self.get_chunk_status(chk)
        if cs & 0x2 != 0:
            return True
        return False

    def is_open_chunk(self, chk):
        """Check the chunk is free or not"""
        cs = self.get_chunk_status(chk)
        if cs & 0x4 != 0:
            return True
        return False

    def s20_to_gen(self, pugrp, punit, chunk, sectr):
        """S20 unit to gen address"""
        cmd = ["nvm_addr s20_to_gen", self.envs,
               "%d %d %d %d" % (pugrp, punit, chunk, sectr)]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.spdk.s20_to_gen: cmd fail")

        return int(re.findall(r"val: ([0-9a-fx]+)", stdout)[0], 16)

    def gen_to_dev(self, address):
        """Generic address to device address"""
        cmd = ["nvm_addr gen2dev", self.envs, "0x{:x}".format(address)]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.spdk.gen_to_dev: cmd fail")

        return int(re.findall(r"dev: ([0-9a-fx]+)", stdout)[0], 16)

    def dev_to_gen(self, address):
        """Generic address to device address"""
        cmd = ["nvm_addr dev2gen", self.envs, "{:s}".format(address)]
        status, stdout, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("cij.spdk.dev_to_gen: cmd fail")
        return int(re.findall(r"gen: (0x\w+)", stdout)[0], 16)

    def vblk_erase(self, address):
        """nvm_vblk erase"""
        cmd = ["nvm_vblk erase", self.envs, "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vblk_write(self, address, file_name=None):
        """nvm_vblk write"""
        cmd = ["nvm_vblk write", self.envs, "0x%x" % address]
        if file_name:
            cmd += ["-i {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vblk_read(self, address, file_name=None):
        """nvm_vblk read"""
        cmd = ["nvm_vblk read", self.envs, "0x%x" % address]
        if file_name:
            cmd += ["-o {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_erase(self, address):
        """vector erase"""
        cmd = ["nvm_cmd erase", self.envs, "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_write(self, address_list, file_name):
        """nvm_cmd write"""
        address = ["0x{:x}".format(i) for i in address_list]
        cmd = ["nvm_cmd write", self.envs, " ".join(address), "-i {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def vector_read(self, address_list, file_name):
        """nvm_cmd read"""
        address = ["0x{:x}".format(i) for i in address_list]
        cmd = ["nvm_cmd read", self.envs, " ".join(address),
               "-o {}".format(file_name)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def scalar_write(self, address, block_count, data_file, meta_file):
        """nvme write"""
        cmd = ["nvme", "write", self.envs, "-s 0x{:x}".format(address),
               "-c {}".format(block_count-1), "-d {}".format(data_file), "-M {}".format(meta_file),
               "-z 0x{:x}".format(block_count * self.get_env("dev_geo", "nbytes")),
               "-y 0x{:x}".format(block_count * self.get_env("dev_geo", "nbytes_oob"))]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def scalar_read(self, address, block_count, data_file, meta_file):
        """nvme read"""
        cmd = ["nvme", "read", self.envs, "-s 0x{:x}".format(address),
               "-c {}".format(block_count - 1), "-d {}".format(data_file),
               "-M {}".format(meta_file),
               "-z 0x{:x}".format(block_count * self.get_env("dev_geo", "nbytes")),
               "-y 0x{:x}".format(block_count * self.get_env("dev_geo", "nbytes_oob"))]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_scalar_ewr(self, seed=0x0, rmode=0x2, be_id=0x0):
        """nvm_test_cmd_ewr_scalar"""
        cmd = ["nvm_test_cmd_wre_scalar", self.envs, str(seed), str(rmode), str(be_id)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_vector_ewr(self, seed=0x0, rmode=0x2, be_id=0x0):
        """nvm_test_cmd_ewr_vector"""
        cmd = ["nvm_test_cmd_wre_vector", self.envs, str(seed), str(rmode), str(be_id)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_tlc_convert_slc(self, be_id=8):
        """ test tlc convert slc"""
        cmd = ["nvm_examples_slc-ex02-convert", self.envs, str(be_id)]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status

    def test_nvm_examples_slc_scan(self, be_id=8):
        """test nvm_examples_slc-ex01-scan"""
        cmd = ["nvm_examples_slc-ex01-scan", self.envs, str(be_id)]
        status, output, _ = cij.ssh.command(cmd, shell=True)
        if status:
            raise RuntimeError("nvm_examples_slc-ex01-scan fail")
        return int(re.findall(r"nslc: ([0-9]+)", output)[0]), (re.findall(r"slba: (0x\w+)", output))

    def slc_erase(self, address, BE_ID=0x1, PMODE=0x0100):
        """slc erase"""
        cmd = ["NVM_CLI_BE_ID=0x%x" % BE_ID, "NVM_CLI_PMODE=0x%x" % PMODE, "nvm_cmd erase", self.envs, "0x%x" % address]
        status, _, _ = cij.ssh.command(cmd, shell=True)
        return status