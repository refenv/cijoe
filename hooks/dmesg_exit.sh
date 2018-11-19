#!/usr/bin/env bash
#
# kills the dmesg log process spawned by the dmesg_enter hook
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::enter

function hook::dmesg_exit {
  ssh::cmd 'pkill -f "dmesg -w"'
  if [[ $? -ne 0 ]]; then
    cij::warn "hook::dmesg_exit: error when killing dmesg"
    return 1;
  fi

  return 0
}

hook::dmesg_exit
exit $?
