#!/usr/bin/env bash
#
# block.sh - Convenience functions for block devices
#
# Functions:
#
# block::env            - Check and export variables
# block::exists         - Chech whether the given BLOCK_DEV_NAME exists
#
# Variables required by module:
#
# BLOCK_DEV_NAME        - Name of the block device, e.g. "sda"
#
# Variables EXPORTED by module:
#
# BLOCK_DEV_PATH        - Path to the device, e.g. "/dev/sda"
#

block::env() {
  if ! ssh::env; then
    cij::err "block::env - Invalid SSH ENV."
    return 1
  fi

  if [[ -z "$BLOCK_DEV_NAME" ]]; then
    cij::err "block::env: BLOCK_DEV_NAME is not defined"
    return 1
  fi

  BLOCK_DEV_PATH="/dev/${BLOCK_DEV_NAME}"

  return 0
}

block::exists() {
  if ! block::env; then
    cij::err "block::env - Invalid NVMe ENV."
    return 1
  fi

  if ! ssh::cmd "[[ -b $BLOCK_DEV_PATH ]]"; then
    cij::err "block::env: BLOCK_DEV_PATH: '$BLOCK_DEV_PATH', does not exist"
    return 1
  fi

  return 0
}

