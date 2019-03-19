#!/usr/bin/env python
#coding=utf-8
import os
import re
import commands
import cij.ssh
class libCfg(object):
    def __init__(self, fio):
        self.cfg_list = [['System Configuration','Information']]
        self.fio = fio
        
    def __getCpu(self):
        if not os.path.exists("/usr/sbin/dmidecode"):
            return
        
        status, output = cij.ssh.command("dmidecode -t 4")
        if status:
            print output
            print "[ERR] get CPU information failed!"
            return
        
        if "Version:" in output:
            cpu_name = re.findall("Version: ([^\n]+)", output)[0].strip()
            self.cfg_list.append(["CPU Mode Name", cpu_name])
        if "Current Speed:" in output:
            cpu_speed = re.findall("Current Speed: ([^\n]+)", output)[0].strip()
            self.cfg_list.append(["CPU Frequency", cpu_speed])
        if "Core Count:" in output:
            cpu_core = re.findall("Core Count: ([^\n]+)", output)[0].strip()
            self.cfg_list.append(["CPU Cores", "%sC" % cpu_core])
        if "Thread Count:" in output:
            cpu_thread = re.findall("Thread Count: ([^\n]+)", output)[0].strip()
            self.cfg_list.append(["CPU Threads", "%sT" % cpu_thread])

    def __getMem(self):
        if not os.path.exists("/usr/sbin/dmidecode"):
            return
        
        status, output = cij.ssh.command("dmidecode -t 17")
        if status:
            print output
            print "[ERR] get memory information failed!"
            return
        
        if "Type:" in output:
            type_list = re.findall("Type: ([^\n]+)", output)
            for mem_type in type_list:
                if "DDR" in mem_type:
                    mem_type = mem_type.strip()
                    break
            self.cfg_list.append(["Memory Type", mem_type])
        
        size_list = re.findall("Size: ([\d]+)", output)
        mem_uint = re.findall("Size: [\d]+ ([^\n]+)", output)[0].strip()
        mem_size = sum(map(int, size_list))
        self.cfg_list.append(["Memory Size", "%s %s" % (mem_size, mem_uint)])
    
    def __getPcie(self):
        if not os.path.exists("/usr/sbin/lspci"):
            return
        
        status, output = cij.ssh.command("lspci")
        if status:
            print output
            print "[ERR] get pcie information failed!"
            return
        
        if "Non-Volatile memory controller:" in output:
            pci_slot = re.findall("([^\n]+) Non-Volatile memory controller", output)[0].strip()
            self.cfg_list.append(["PCIe Slots", pci_slot])
    
    def __getRelease(self):
        if not os.path.exists("/usr/bin/lsb_release"):
            return
        
        status, output = cij.ssh.command("lsb_release -a")
        if status:
            print output
            print "[ERR] get linux release information failed!"
            return
        
        if "Description:" in output:
            release_info = re.findall("Description:([^\n]+)", output)[0].strip()
            self.cfg_list.append(["OS Release", release_info])
    
        status, output = cij.ssh.command("uname -r")
        if status:
            print output
            print "[ERR] get linux release information failed!"
            return
        self.cfg_list.append(["OS Kernel", output])
        
    def __getCnex(self):
        self.cfg_list.append(['Board Type',                  ''])
        self.cfg_list.append(['HW Accelerate Mode',          ''])
        self.cfg_list.append(['LBA Capacity',                ''])
        self.cfg_list.append(['NAND Type',                   ''])
        self.cfg_list.append(['NAND Capacity',               ''])
        self.cfg_list.append(['Over Provision Percentage',   ''])
        self.cfg_list.append(['PCIe Interface',              ''])
        self.cfg_list.append(['DDR type',                    ''])
        self.cfg_list.append(['NAND Clock',                  ''])
        self.cfg_list.append(['DDR clock',                   ''])
        self.cfg_list.append(['Core clock',                  ''])
        self.cfg_list.append(['Cache Hit',                   ''])
        self.cfg_list.append(['DDR Cache',                   ''])
        self.cfg_list.append(['FW Version',                  ''])
    
    def __getFio(self):
        if not os.path.exists(self.fio):
            return
        
        status, output = cij.ssh.command("%s --version" % self.fio)
        if status:
            print output
            print "[ERR] get fio information failed!"
            return
        
        self.cfg_list.append(["FIO Version", output])
    
    def __getBlankLine__(self):
        self.cfg_list.append([""])
    
    def getCfg(self):
        self.__getCpu()
        self.__getMem()
        self.__getPcie()
        
        self.__getBlankLine__()
        self.__getRelease()
        self.__getFio()
        
        self.__getBlankLine__()
        self.__getCnex()
        
        return self.cfg_list

class libTool(object):
    fio_2_1_10 = "../../tools/fio_2.1.10/fio"
    fio_2_19 = "../../tools/fio_2.19/fio"
    vdbench_504 = "../../tools/vdbench504/vdbench"

if __name__ == '__main__':
    cfg_list = libCfg("../../tools/fio_2.1.10/fio")
    for line in cfg_list.getCfg():
        print line
    