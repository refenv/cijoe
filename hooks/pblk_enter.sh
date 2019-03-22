#!/usr/bin/env bash
#
# Create and remove a PBLK instance
#
# hook-enter: create the PBLK instance
# hook-exit: remove the PBLK instance
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::pblk_enter() {
  export LNVM_DEV_TYPE="pblk"

  if ! lnvm::create; then
    cij:err "hook::pblk_enter: lnvm::create: FAILED"
    return 1
  fi

  return 0
}

hook::pblk_enter
exit $?
