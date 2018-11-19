#!/usr/bin/env bash
#
# bin::read_byte      - Read a byte from bin file
#      $1             - offset of file with byte
#      $2             - binary file path

BIN_SSH_CMD=0

function bin::read_byte {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_byte: invalid ssh environment"
    return 1
  fi

  if [[ $# != 2 ]]; then
    cij::err "bin::read_byte: invalid input parameters"
    return 1
  fi

  if [[ $BIN_SSH_CMD == 1 ]]; then
    OUTPUT=$(ssh::cmd "od -j $1 -N 1 -t d -An $2")
  else
    OUTPUT=$(od -j $1 -N 1 -t d -An $2)
  fi
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_word: Error read file"
    return 1
  fi

  echo $OUTPUT
  return 0
}

function bin::read_word {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_word: invalid ssh environment"
    return 1
  fi

  if [[ $# != 2 ]]; then
    cij::err "bin::read_word: invalid input parameters"
    return 1
  fi

  if [[ $BIN_SSH_CMD == 1 ]]; then
    OUTPUT=$(ssh::cmd "od -j $1 -N 2 -t d -An $2")
  else
    OUTPUT=$(od -j $1 -N 2 -t d -An $2)
  fi
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_word: Error read file"
    return 1
  fi

  echo $OUTPUT
  return 0
}

function bin::read_dword {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_dword: invalid ssh environment"
    return 1
  fi

  if [[ $# != 2 ]]; then
    cij::err "bin::read_dword: invalid input parameters"
    return 1
  fi

  if [[ $BIN_SSH_CMD == 1 ]]; then
    OUTPUT=$(ssh::cmd "od -j $1 -N 4 -t d -An $2")
  else
    OUTPUT=$(od -j $1 -N 4 -t d -An $2)
  fi
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_word: Error read file"
    return 1
  fi

  echo "$OUTPUT"
  return 0
}

function bin::read {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_dword: invalid ssh environment"
    return 1
  fi

  if [[ $# != 3 ]]; then
    cij::err "bin::read_dword: invalid input parameters"
    return 1
  fi

  if [[ $BIN_SSH_CMD == 1 ]]; then
    OUTPUT=$(ssh::cmd "od -j $1 -N $2 -t d1 -An $3")
  else
    OUTPUT=$(od -j $1 -N $2 -t d1 -An $3)
  fi
  if [[ $? -ne 0 ]]; then
    cij::err "bin::read_word: Error read file"
    return 1
  fi

  echo $OUTPUT
  return 0
}
