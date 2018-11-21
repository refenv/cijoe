#!/usr/bin/env bash
#
# board::env     - Checks environment for BOARD variables and sets up additiona
#
# Variables REQUIRED by module:
#
# BOARD_FORMFACTOR      - BOARD lun begin e.g. 0
#
# Variables EXPORTED by module:
#
# BOARD_CLASS           - BOARD identifier
# BOARD_IDENT           - BOARD identifier
#

board::env() {
  if ! ssh::env; then
    cij::err "board::env: Invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR. definitions
  if [[ -z "$BOARD_FORMFACTOR" ]]; then
    cij::err "board::env: BOARD_FORMFACTOR is not defined"
    return 1
  fi
  if [[ -z "$BOARD_MEMORY" ]]; then
    cij::err "board::env: BOARD_MEMORY is not defined"
    return 1
  fi
  if [[ -z "$BOARD_CHIP" ]]; then
    cij::err "board::env: BOARD_CHIP is not defined"
    return 1
  fi
  if [[ -z "$BOARD_ALIAS" ]]; then
    cij::err "board::env: BOARD_ALIAS is not defined"
    return 1
  fi

  # Exported variables
  BOARD_CLASS="${BOARD_FORMFACTOR}"
  BOARD_CLASS="${BOARD_CLASS}_${BOARD_MEMORY}"
  BOARD_CLASS="${BOARD_CLASS}_${BOARD_CHIP}"

  BOARD_IDENT="${BOARD_CLASS}-${BOARD_ALIAS}"

  cij::emph "BOARD_IDENT: '${BOARD_IDENT}'"
  cij::emph "BOARD_CLASS: '${BOARD_CLASS}'"

  return 0
}

