#!/usr/bin/env bash
#
# Logs dmesg to file $CIJ_TEST_RES_ROOT/hook_dmesg.log
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::dmesg_enter() {
  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij:err "hook::dmesg_enter: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  ssh::cmd "dmesg -w -T" > $CIJ_TEST_AUX_ROOT/hook_dmesg.log &
  if [[ $? -ne 0 ]]; then
    cij.warn "hook::dmesg_enter: FAILED starting dmesg log err: '$?'"
    return 1
  fi

  return 0
}

hook::dmesg_enter
exit $?
