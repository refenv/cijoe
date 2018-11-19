#!/usr/bin/env bash

# Credentials for logging into QEMU simulation

export SSH_USER=root
export SSH_HOST=qemu-localhost
export SSH_PORT=2022

# Credentials for logging into QEMU HOST
export QEMU_HOST=localhost
export QEMU_HOST_USER=$USER
export QMEU_GUEST_NAME=emujoe

export QEMU_BIN="/opt/qemu-nvme/bin/qemu-system-x86_64"
export QEMU_GUESTS="/opt/qemu-guests"
export QEMU_GUEST_NAME=emujoe
export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
export QEMU_GUEST_BOOT_IMG="$QEMU_GUEST_PATH/qatd-u1604.qcow2"
export QEMU_GUEST_BOOT_IMG_FMT="qcow2"
export QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
export QEMU_GUEST_MEM=8G
export QEMU_GUEST_SMP=4
export QEMU_GUEST_CONSOLE="file"

export QEMU_NVME_ID="cij_nvme"
export QEMU_NVME_LINES=80
export QEMU_NVME_NUM_PU=8

export QEMU_NVME_SECS_PER_CHK=3072
export QEMU_NVME_META_SZ=16

export QEMU_NVME_WS_MIN=12
export QEMU_NVME_WS_OPT=24
export QEMU_NVME_CUNITS=0

export QEMU_NVME_CHUNKTABLE="$CIJ_ROOT/testfiles/qemu/chunktable.qemu"
export QEMU_NVME_RESETFAIL="$CIJ_ROOT/testfiles/qemu/resetfail.qemu"
export QEMU_NVME_WRITEFAIL="$CIJ_ROOT/testfiles/qemu/writefail.qemu"

export NVME_DEV_NAME="nvme0n1"
export LNVM_BGN=0
export LNVM_END=$(( $QEMU_NVME_NUM_PU - 1 ))
export BLOCK_DEV_NAME="nvme0n1b000e00"$LNVM_END
