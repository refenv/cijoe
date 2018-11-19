#!/usr/bin/env bash

function hook::lnvm_exit {
  lnvm::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::lnvm_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::lnvm_exit
exit $?
