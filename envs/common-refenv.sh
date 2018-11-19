#!/usr/bin/env bash
#
# Paths packages installed from source in the Ubuntu reference environment
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

export FIO_2.2.8_HOME=/opt/fio-2.2.8
export FIO_2.2.10_HOME=/opt/fio-2.2.10

export ACT_HOME=/opt/act
export SPDK_HOME=/opt/spdk
export YCSB_HOME=/opt/YCSB

export BLOCK_STORAGE_HOME=/opt/block-storage
