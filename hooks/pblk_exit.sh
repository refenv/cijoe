#!/usr/bin/env bash
#
# Removes a PBLK device
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::pblk_exit {
  lnvm::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::pblk_exit
exit $?
