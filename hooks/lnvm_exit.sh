#!/usr/bin/env bash
#
# Create and remove a lightnvm instance
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

hook::lnvm_exit () {
  if ! lnvm::remove; then
    cij:err "hook::lnvm_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::lnvm_exit
exit $?
