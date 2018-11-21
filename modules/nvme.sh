#!/usr/bin/env bash
#
# nvme.sh - Script providing convenience functions for NVMe
#
# Functions:
#
# nvme::exists - Test whether the given NVME_DEV_NAME exists
#
# Variables required by module:
#
# NVME_DEV_NAME         -- Name of the NVMe Device, e.g. "nvme0n1"
#
# Variables EXPORTED by module:
#
# NVME_DEV_PATH         -- Path to the device, e.g. "/dev/nvme0n1"
#
# NVME_LNVM             -- Device supports LightNVM: 1=YES, 0=NO
# NVME_LNVM_NUM_LUNS    -- Number of LUNS (when NVME_LNVM == 1)
# NVME_LNVM_NUM_CH      -- Number of Channels (when NVME_LNVM == 1)
# NVME_LNVM_TOTAL_LUNS  -- Number of LUNS in total (when NVME_LNVM == 1)
#

nvme::env() {
  if ! ssh::env; then
    cij::err "nvme::env - Invalid SSH ENV."
    return 1
  fi

  if [[ -z "$NVME_DEV_NAME" ]]; then
    cij::err "nvme::env: NVME_DEV_NAME is not defined"
    return 1
  fi

  NVME_DEV_PATH="/dev/${NVME_DEV_NAME}"
  LNVM_SYSFS="/sys/class/block/$NVME_DEV_NAME/lightnvm"

  NVME_LNVM=0
  if ! ssh::cmd "[[ -d '$LNVM_SYSFS' ]]"; then
    cij::warn "NVME_DEV_PATH: ${NVME_DEV_PATH} is not a LightNVM device"
    return 0
  fi
  NVME_LNVM=1

  if ! NVME_LNVM_VERSION=$(ssh::cmd_output "cat $LNVM_SYSFS/version"); then
    cij:err "nvme:env: FAILED - could not read sysfs version"
    return 1
  fi

  if [[ "$NVME_LNVM_VERSION" == "2.0" ]]; then
    LUN_ATTR="punits"
    CH_ATTR="groups"
  elif [[ "$NVME_LNVM_VERSION" == "1.2" ]]; then
    LUN_ATTR="num_luns"
    CH_ATTR="num_channels"
  else
    cij::err "nvme::env: FAILED invalid NVME_LNVM_VERSION: '$NVME_LNVM_VERSION'"
    return 1
  fi

  if ! NVME_LNVM_NUM_CHUNKS=$(ssh::cmd_output "cat $LNVM_SYSFS/chunks"); then
    cij::err "nvme::env: FAILED - could not read number of chunks"
    return 1
  fi

  if ! NVME_LNVM_NUM_LUNS=$(ssh::cmd_output "cat $LNVM_SYSFS/$LUN_ATTR"); then
    cij::err "nvme::env: FAILED - could not read number of luns"
    return 1
  fi

  if ! NVME_LNVM_NUM_CH=$(ssh::cmd_output "cat $LNVM_SYSFS/$CH_ATTR"); then
    cij::err "nvme::env: FAILED - could not read number of channels"
    return 1
  fi

  export NVME_LNVM
  export NVME_LNVM_TOTAL_LUNS=$(( NVME_LNVM_NUM_LUNS * NVME_LNVM_NUM_CH ))
  export NVME_LNVM_TOTAL_CHUNKS=$(( NVME_LNVM_NUM_LUNS * NVME_LNVM_NUM_CH * NVME_LNVM_NUM_CHUNKS ))
  export NVME_LNVM_CHUNK_META_LENGTH=32
  export NVME_LNVM_CHUNK_META_SIZE=$(( NVME_LNVM_TOTAL_CHUNKS * NVME_LNVM_CHUNK_META_LENGTH ))
  export NVME_ENV=1

  return 0
}

nvme::exists() {
  if ! nvme::env; then
    cij::err "nvme::env - Invalid NVMe ENV."
    return 1
  fi

  if ! ssh::cmd "[[ -b $NVME_DEV_PATH ]]"; then
    cij::err "nvme::env: NVME_DEV_PATH: '$NVME_DEV_PATH', does not exist"
    return 1
  fi

  return 0
}

nvme::chunk_meta() {
  NVME_OFFSET=$1
  NVME_LENGTH=$2
  NVME_OUTPUT=$3
  NVME_GET_LOG_MAX_SIZE=0x80000

  if ! nvme::env; then
    cij::err "nvme::env - Invalid NVMe ENV."
    return 1
  fi

  ssh::cmd ": > $NVME_OUTPUT"
  for (( NVME_GET_OFFSET=NVME_OFFSET; NVME_GET_OFFSET<NVME_LENGTH; NVME_GET_OFFSET+=NVME_GET_LOG_MAX_SIZE )); do
    if [[ $(( NVME_LENGTH - NVME_GET_OFFSET )) -gt NVME_GET_LOG_MAX_SIZE ]]; then
      NVME_GET_LENGTH=$NVME_GET_LOG_MAX_SIZE
    else
      NVME_GET_LENGTH=$(( NVME_LENGTH - NVME_GET_OFFSET ))
    fi

    if ! ssh::cmd "nvme get-log $NVME_DEV_PATH -i 0xca -o $NVME_GET_OFFSET -l $NVME_GET_LENGTH -b >> $NVME_OUTPUT"; then
      cij::err "nvme::getmeta: Error Get Chunk Meta"
      return 1
    fi
  done

  return 0
}
