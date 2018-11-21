#!/usr/bin/env bash
#
# tftp.sh - Script providing convenience functions tftp booted machines
#
# Functions:
#
# tftp::provision_kernel - provisions a kernel to a tftp server
#
# Required variables
#
# TFTP_KERNEL_PATH -  scp path to where thee tftp server picks up the kernel
# image i.e tfp-server:/srv/tftpboot/pxelinux.bzi/testmachine.bzImage

tftp::env() {
  if [[ -z "$TFTP_KERNEL_PATH" ]]; then
    cij::err "qemu::env: TFTP_KERNEL_PATH not set"
    return 1
  fi
}

tftp::provision_kernel() {
  if ! tftp::env; then
    cij::err "tftp::env failed"
    return 1
  fi

  LOCAL_KERNEL=$1
  if [[ -z "$LOCAL_KERNEL" ]]; then
    cij::info "Local kernel path not supplied. Defaulting to: arch/x86/boot/bzImage"
    LOCAL_KERNEL="arch/x86/boot/bzImage"
  fi

  scp "$LOCAL_KERNEL" "$TFTP_KERNEL_PATH"
}

