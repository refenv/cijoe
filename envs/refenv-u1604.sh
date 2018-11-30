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
export RBENCH_BIN=/opt/rocksdb/db_bench

export BLKTESTS_HOME=/opt/blktests
export XFSTESTS_HOME=/var/lib/xfstests

export FIO_2_2_8_HOME=/opt/fio-2.2.8
export FIO_2_2_10_HOME=/opt/fio-2.2.10

export ACT_HOME=/opt/act
export SPDK_HOME=/opt/spdk
export YCSB_HOME=/opt/YCSB

export BLOCK_STORAGE_HOME=/opt/block-storage

#
# Sensitive Region
#
#export CIJ_TRGT=localhost
#export SSH_HOST=$CIJ_TRGT
#export SSH_USER=root
#export IPMI_HOST=${CIJ_TRGT}-ipmi
#export IPMI_USER=ADMIN
#export IPMI_PASS=ADMIN

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
