#!/usr/bin/env bash
#
# QEMU environment skeleton
#
# The SSH configuration is overwritten such that everything using the "ssh::"
# module will be targeted towards the QEMU guest and to access the QEMU host and
# explicit "QEMU_HOST" and utility functions are provided by the "qemu::" module
#

# REQUIRED: SSH config for logging into QEMU guest
#export SSH_USER=root
#export SSH_HOST=localhost
#export SSH_PORT=2022

# REQUIRED: SSH config for logging into QEMU host
#export QEMU_HOST=localhost
#export QEMU_HOST_USER=root

#
# QEMU definitions
#
export QEMU_BIN="/opt/qemu-nvme/bin/qemu-system-x86_64"
export QEMU_GUESTS="/opt/qemu-guests"
# The guest machine
export QEMU_GUEST_NAME=emujoe
export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
export QEMU_GUEST_BOOT_IMG="$QEMU_GUEST_PATH/boot.qcow2"
export QEMU_GUEST_CONSOLE="file"
export QEMU_GUEST_MEM="12GB"
#export QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"

# OCSSD: Define a virtual Open-Channel SSD
export QEMU_NVME_ID="cij_nvme"

# OCSSD: Geometry
export QEMU_NVME_LINES=100
export QEMU_NVME_NUM_GRP=4
export QEMU_NVME_NUM_PU=4
export QEMU_NVME_NUM_SEC=528
export QEMU_NVME_SEC_SIZE=4096
export QEMU_NVME_MS=16
#export QEMU_NVME_MDTS=7
#export QEMU_NVME_NLBAF=6

# OCSSD: constraints
export QEMU_NVME_WS_MIN=12
export QEMU_NVME_WS_OPT=24
export QEMU_NVME_MW_CUNITS=0

# OCSSD: error-injection
#export QEMU_NVME_CHUNKTABLE="$CIJ_ROOT/testfiles/qemu/chunktable.qemu"
#export QEMU_NVME_RESETFAIL="$CIJ_ROOT/testfiles/qemu/resetfail.qemu"
#export QEMU_NVME_WRITEFAIL="$CIJ_ROOT/testfiles/qemu/writefail.qemu"

if [[ -z "$NVME_DEV_NAME" ]]; then
  export NVME_DEV_NAME="nvme0n1"
fi

export LNVM_BGN=0
export LNVM_END=$(( $QEMU_NVME_NUM_PU - 1 ))

export PBLK_DEV_NAME="nvme0n1b000e00"$LNVM_END
if [[ -z "$BLOCK_DEV_NAME" ]]; then
  export BLOCK_DEV_NAME="nvme0n1b000e00"$LNVM_END
fi
