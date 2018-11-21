#!/usr/bin/env bash
#
# bin::read_byte        - Read a byte from bin file
#       $1              - binary file path
#       $2              - size
#       $3              - offset

bin::read() {
  if ! ssh::env; then
    cij::err "bin::read: invalid ssh environment"
    return 1
  fi

  if [[ $# != 3 ]]; then
    cij::err "bin::read: invalid input parameters"
    return 1
  fi

  BIN_PATH=$1
  BIN_SIZE=$2
  BIN_OFFSET=$3

  BIN_CMD="od -j $BIN_OFFSET -N $BIN_SIZE -t d1 -An $BIN_PATH"

  if [[ $BIN_SSH_CMD == 1 ]]; then
    if ! OUTPUT=$(ssh::cmd "$BIN_CMD"); then
      cij::err "bin::read: Error read file"
    fi
  else
    if ! OUTPUT=$("$BIN_CMD"); then
      cij::err "bin::read: Error read file"
    fi
  fi

  echo "$OUTPUT"
  return 0
}

bin::read_byte() {
  if [[ $# != 2 ]]; then
    cij::err "bin::read_byte: invalid input parameters"
    return 1
  fi

  bin::read "$1" "$2" 1
  return $?
}

bin::read_word() {
  if [[ $# != 2 ]]; then
    cij::err "bin::read_byte: invalid input parameters"
    return 1
  fi

  bin::read "$1" "$2" 2
  return $?
}

function bin::read_dword {
  if [[ $# != 2 ]]; then
    cij::err "bin::read_byte: invalid input parameters"
    return 1
  fi

  bin::read "$1" "$2" 4
  return $?
}

