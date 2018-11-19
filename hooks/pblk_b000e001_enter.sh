#!/usr/bin/env bash
#
# Creates a PBLK device spanning LUNs 0-1
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require nvme
test::enter

function hook::pblk_b000e001_enter {

  LNVM_DEV_TYPE="pblk"
  LNVM_BGN=0
  LNVM_END=1

  lnvm::create
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_b000e001_enter: lnvm::create: FAILED"
    return 1
  fi

  return 0
}

hook::pblk_b000e001_enter
exit $?
