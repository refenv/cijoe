#!/usr/bin/env bash
#
# Creates a PBLK device
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require nvme
test::enter

function hook::pblk_enter {

  LNVM_DEV_TYPE="pblk"
  lnvm::create
  if [[ $? -ne 0 ]]; then
    cij:err "hook::pblk_enter: lnvm::create: FAILED"
    return 1
  fi

  return 0
}

hook::pblk_enter
exit $?
