#!/usr/bin/env bash
#
# hook: removes a PBLK device and re-creates it with recovery
#
# NOTE: hans / javier? Does this still make sense?
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::pblk_recov_all_exit() {
  if ! lnvm::remove; then
    cij:err "hook::pblk_recov_all_exit: lnvm::remove FAILED"
    return 1
  fi

  if ! lnvm::recover; then
    cij:err "hook::pblk_recov_all_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::pblk_recov_all_exit
exit $?
