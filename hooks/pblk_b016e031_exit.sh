#!/usr/bin/env bash
#
# Removes a PBLK device as LUNs 16-31
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::pblk_b016e031_exit {
  LNVM_BGN=16
  LNVM_END=31

  lnvm::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_b016e031_exit: lnvm::remove FAILED"
    return 1
  fi

  return 0
}

hook::pblk_b016e031_exit
exit $?
