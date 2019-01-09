#!/usr/bin/env bash
#
# lnvm::env     - Checks and exports LigthNVM variables (LNVM_*)
# lnvm::create  - Create a LNVM device
# lnvm::recover - Create a LNVM device with recovery
# lnvm::remove  - Remove a LNVM device
#
# Variables REQUIRED by module:
#
# NVME_DEV_NAME - Name of the NVMe Device to use e.g. "nvme0n1", this is
#                 actually the device namespace, not the root NVMe device.
#
# LNVM_BGN      - LNVM lun begin e.g. 0
# LNVM_END      - LNVM lun begin e.g. 127
#
# Variables OPTIONAL by module:
#
# LNVM_DEV_TYPE - DEFAULT: pblk
#
# Variables EXPORTED by module:
#
# LNVM_DEV_NAME - Name of the LNVM instance e.g. nvme0n1b000e127
# LNVM_DEV_PATH - Name of the LNVM instance e.g. /dev/nvme0n1b000e127
#

lnvm::env() {
  if ! ssh::env; then
    cij::err "lnvm::env: invalid SSH environment"
    return 1
  fi
  if ! nvme::env; then
    cij::err "lnvm::env: invalid NVMe environment"
    return 1
  fi

  if [[ -z "$LNVM_BGN" ]]; then
    cij::err "lnvm::env: LNVM_BGN is not defined"
    return 1
  fi
  if ! cij::isint "$LNVM_BGN"; then
    cij::err "lnvm::env: LNVM_BGN: ${LNVM_BGN} is not an integer"
    return 1
  fi
  LNVM_BGN_STR=$(printf "%03d" "$LNVM_BGN")

  # shellcheck disable=2153
  if [[ -z "$LNVM_END" ]]; then
    cij::err "lnvm::env: LNVM_END is not defined"
    return 1
  fi
  if ! cij::isint "$LNVM_END"; then
    cij::err "lnvm::env: LNVM_END: ${LNVM_END} is not an integer"
    return 1
  fi
  LNVM_END_STR=$(printf "%03d" "$LNVM_END")

  # DEFAULT variables
  if [[ -z "$LNVM_DEV_TYPE" ]]; then
    LNVM_DEV_TYPE="pblk"
    cij::warn "lnvm::env: LNVM_DEV_TYPE is not set, assigned '$LNVM_DEV_TYPE'"
  fi

  # shellcheck disable=2153
  export LNVM_DEV_NAME="${NVME_DEV_NAME}b${LNVM_BGN_STR}e${LNVM_END_STR}"
  export LNVM_DEV_PATH="/dev/${LNVM_DEV_NAME}"

  return 0
}

lnvm::create() {
  if ! lnvm::env; then
    cij::err "lnvm::create: invalid environment"
    return 1
  fi

  cij::emph "lnvm::create: LNVM_DEV_NAME: '$LNVM_DEV_NAME'"

  LNVM_CMD="nvme lnvm create"
  LNVM_CMD="$LNVM_CMD -d $NVME_DEV_NAME"
  LNVM_CMD="$LNVM_CMD -n $LNVM_DEV_NAME"
  LNVM_CMD="$LNVM_CMD -t $LNVM_DEV_TYPE"
  LNVM_CMD="$LNVM_CMD -b $LNVM_BGN"
  LNVM_CMD="$LNVM_CMD -e $LNVM_END"
  LNVM_CMD="$LNVM_CMD -f"

  if ! ssh::cmd "$LNVM_CMD"; then
    cij::err "lnvm::create: FAILED"
    return 1
  fi

  return 0
}

lnvm::recover() {
  if ! lnvm::env; then
    cij::err "lnvm::recover: invalid environment"
    return 1
  fi

  cij::emph "lnvm::recover: LNVM_DEV_NAME: '$LNVM_DEV_NAME'"

  LNVM_CMD="nvme lnvm create"
  LNVM_CMD="$LNVM_CMD -d $NVME_DEV_NAME"
  LNVM_CMD="$LNVM_CMD -n $LNVM_DEV_NAME"
  LNVM_CMD="$LNVM_CMD -t $LNVM_DEV_TYPE"
  LNVM_CMD="$LNVM_CMD -b $LNVM_BGN"
  LNVM_CMD="$LNVM_CMD -e $LNVM_END"

  if ! ssh::cmd "$LNVM_CMD"; then
    cij::err "lnvm::recover: FAILED"
    return 1
  fi

  return 0
}

lnvm::remove() {
  if ! lnvm::env; then
    cij::err "lnvm::remove: invalid environment"
    return 1
  fi

  cij::emph "lnvm::remove: LNVM_DEV_NAME: '$LNVM_DEV_NAME'"

  LNVM_CMD="nvme lnvm remove"
  LNVM_CMD="$LNVM_CMD -n $LNVM_DEV_NAME"

  if ! ssh::cmd "$LNVM_CMD"; then
    cij::err "lnvm::remove: FAILED"
    return 1
  fi

  return 0
}

lnvm::exists() {
  if ! lnvm::env; then
    cij::err "lnvm::create: invalid environment"
    return 1
  fi

  if ! ssh::cmd "[[ -b \"$LNVM_DEV_PATH\" ]]"; then
    cij::err "lnvme::exists: LNVM_DEV_PATH: '$LNVM_DEV_PATH', does not exist"
    return 1
  fi

  return 0
}
