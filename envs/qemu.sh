#!/usr/bin/env bash
#
# QEMU environment skeleton
#
# The SSH configuration is overwritten such that everything using the "ssh::"
# module will be targeted towards the QEMU guest. To access the QEMU host an
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

qemu_bin_root="/opt/qemu/bin"
export QEMU_HOST_SYSTEM_BIN="$qemu_bin_root/qemu-system-x86_64"
export QEMU_HOST_IMG_BIN="$qemu_bin_root/qemu-img"
export QEMU_GUESTS="/opt/qemu-guests"

# The guest machine
export QEMU_GUEST_NAME=emujoe
export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
export QEMU_GUEST_BOOT_IMG="$QEMU_GUEST_PATH/boot.qcow2"
export QEMU_GUEST_CONSOLE="file"
export QEMU_GUEST_MEM="4G"
#export QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
#export QEMU_GUEST_APPEND="net.ifnames=0 biosdevname=0"
