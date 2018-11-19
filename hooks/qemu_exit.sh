#!/usr/bin/env bash
#
# Stops a running QEMU machine
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::enter

function hook::qemu_exit {
  
  qemu::poweroff
  if [[ $? -ne 0 ]]; then
    cij::warn "hook::qemu_exit: error when stopping QEMU"
    return 1;
  fi

  return 0
}

hook::qemu_exit
exit $?
