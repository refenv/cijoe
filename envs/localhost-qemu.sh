#!/usr/bin/env bash
source $CIJ_ROOT/envs/common.sh

export SSH_USER=root
export SSH_HOST=localhost
export SSH_PORT=2022
export QEMU_BIN="/opt/bin/qemu-system-x86_64"
export QEMU_GUESTS="/opt/emulation/cijoe"
export QEMU_GUEST_NAME=emujoe
export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
export QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
export QEMU_GUEST_MEM=3G
export QEMU_GUEST_SMP=4
export QEMU_GUEST_HOSTFWD="tcp::$SSH_PORT-:22"
export QEMU_GUEST_CONSOLE="file"
export QEMU_NVME_CHUNKTABLE="$CIJ_ROOT/testfiles/qemu/chunktable.qemu"
export QEMU_NVME_RESETFAIL="$CIJ_ROOT/testfiles/qemu/resetfail.qemu"
export QEMU_NVME_WRITEFAIL="$CIJ_ROOT/testfiles/qemu/writefail.qemu"

export QEMU_DRIVE_COUNT=4200
export QEMU_NVME_NUM_LUNS=4
export NVME_DEV_NAME="nvme0n1"
export LNVM_BGN=0
export LNVM_END=3
export BLOCK_DEV_NAME="nvme0n1b000e003"
