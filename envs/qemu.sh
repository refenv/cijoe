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

qemu_bin_root="/opt/qemu-nvme/bin"
export QEMU_BIN="$qemu_bin_root/qemu-system-x86_64"
export QEMU_IMG_BIN="$qemu_bin_root/qemu-img"
export QEMU_GUESTS="/opt/qemu-guests"

# The guest machine
export QEMU_GUEST_NAME=emujoe
export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
export QEMU_GUEST_BOOT_IMG="$QEMU_GUEST_PATH/boot.qcow2"
export QEMU_GUEST_CONSOLE="file"
export QEMU_GUEST_MEM="4G"
#export QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
#export QEMU_GUEST_APPEND="net.ifnames=0 biosdevname=0"

# OCSSD: Define a virtual Open-Channel SSD
export QEMU_NVME_ID="cij_nvme"

# OCSSD: Geometry
export QEMU_NVME_NUM_GRP=2
export QEMU_NVME_NUM_PU=4
export QEMU_NVME_NUM_CHK=60
export QEMU_NVME_NUM_SEC=4096
export QEMU_NVME_LBADS=4096
export QEMU_NVME_MS=16
#export QEMU_NVME_MDTS=7

# OCSSD: constraints
export QEMU_NVME_WS_MIN=4
export QEMU_NVME_WS_OPT=8
export QEMU_NVME_MW_CUNITS=24

# OCSSD: error-injection
#export QEMU_NVME_CHUNKTABLE="$CIJ_ROOT/testfiles/qemu/chunktable.qemu"
#export QEMU_NVME_RESETFAIL="$CIJ_ROOT/testfiles/qemu/resetfail.qemu"
#export QEMU_NVME_WRITEFAIL="$CIJ_ROOT/testfiles/qemu/writefail.qemu"

if [[ -z "$NVME_DEV_NAME" ]]; then
  export NVME_DEV_NAME="nvme0n1"
fi
