#!/usr/bin/env bash
#
# Logs dmesg to file $CIJ_TEST_RES_ROOT/hook_dmesg.log
#
# on-enter: start 'dmesg -w' process on TRGT and pipe to file on CTRL
# on-exit: kill the dmesg process on TRGT
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::dmesg_exit() {
  if ! ssh::cmd 'pgrep dmesg | xargs kill'; then
    cij::warn "hook::dmesg_exit: error killing dmesg"
    return 1;
  fi

  return 0
}

hook::dmesg_exit
exit $?
