#!/usr/bin/env bash
#
# Create and removes a lightnvm target via lnvm::create / lnvm::remove
#
# on-enter: create instance via lnvm::create
# on-exit: remove instance via lnvm::remove
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::lnvm_enter () {
  if ! lnvm::create; then
    cij:err "hook::lnvm_enter: FAILED: lnvm::create"
    return 1
  fi

  return 0
}

hook::lnvm_enter
exit $?
