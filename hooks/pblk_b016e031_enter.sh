#!/usr/bin/env bash
#
# Creates a PBLK device spanning LUNs 16-31
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require nvme
test::enter

function hook::pblk_b016e031_enter {

  LNVM_DEV_TYPE="pblk"
  LNVM_BGN=16
  LNVM_END=31

  lnvm::create
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_b016e031_enter: lnvm::create: FAILED"
    return 1
  fi

  return 0
}

hook::pblk_b016e031_enter
exit $?
