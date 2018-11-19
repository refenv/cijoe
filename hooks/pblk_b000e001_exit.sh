#!/usr/bin/env bash
#
# Removes a PBLK device as LUNs 0-1
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::pblk_b000e001_exit {
  LNVM_BGN=0
  LNVM_END=1

  lnvm::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_b000e001_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::pblk_b000e001_exit
exit $?
