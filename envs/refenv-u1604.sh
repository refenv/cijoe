#!/usr/bin/env bash
#
# Paths packages installed from source in the Ubuntu 1604 reference environment
#
# NOTE:
# - fio 3.12 is installed on the system, additional versions in /opt
# - SPDK is installed on the system. However, the repos remains in /opt/spdk
#
# See the reference environments for additional information
#

#
# The following are paths in the TARGET used by their respective hooks, modules,
# and testcases
#

# See module "rbench::" in modules/rbench.sh
export RBENCH_BIN=/opt/rocksdb/db_bench

# See module "blktests::" in modules/blktests.sh
export BLKTESTS_HOME=/opt/blktests

# See module "xfstests::" in modules/xfstests.sh
export XFSTESTS_HOME=/var/lib/xfstests

# See hook "spdk" in hooks/spdk.sh and hooks/spdk_exit.sh
export SPDK_HOME=/opt/spdk

# These are used by testcases that rely on specific version of fio, the "fio::"
# module uses the fio version installed on the system
export FIO_2_2_8_HOME=/opt/fio-2.2.8
export FIO_2_2_10_HOME=/opt/fio-2.2.10

# These are defined for testcases implemented as wrappers
export YCSB_HOME=/opt/YCSB
export ACT_HOME=/opt/act
export BLOCK_STORAGE_HOME=/opt/block-storage

#
# Hazardous Region
#
# As most tests will write to devices, then it is important that you make sure
# to define them correctly to around purging your operating system installation
# or your precious data.
#
#export PCI_DEV_NAME=0000:01:00.0
#export NVME_DEV_NAME=nvme0n1
#export BLOCK_DEV_NAME=$NVME_DEV_NAME

#
# Sensitive Region
#
#export CIJ_TRGT=localhost

#export SSH_HOST=$CIJ_TRGT
#export SSH_USER=root

#export IPMI_HOST=${CIJ_TRGT}-ipmi
#export IPMI_USER=ADMIN
#export IPMI_PASS=ADMIN
