#!/usr/bin/env bash
#
# Removes a PBLK device as LUNs 0-3
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::pblk_b000e003_exit {
  LNVM_BGN=0
  LNVM_END=3

  lnvm::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_b000e003_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::pblk_b000e003_exit
exit $?
