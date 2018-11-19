#!/usr/bin/env bash

function hook::lnvm_enter {
  lnvm::create
  if [[ $? -ne 0 ]]; then
    cij:err "hook::lnvm_enter: lnvm::create: FAILED"
    return 1
  fi

  return 0
}

hook::lnvm_enter
exit $?
