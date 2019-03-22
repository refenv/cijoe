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

hook::dmesg_enter() {
  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij:err "hook::dmesg_enter: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  ssh::cmd "dmesg -w -T" > "$CIJ_TEST_AUX_ROOT/hook_dmesg.log" &
  SSH_DMESG_PID="$!"

  # If the background process fails early then we can catch it here do note that
  # in case it is timing out, then that will be a false positive
  if ! ps -p "$SSH_DMESG_PID"; then
    cij::warn "hook::dmesg_enter: FAILED starting dmesg log err: '$?'"
    return 1
  fi

  return 0
}

hook::dmesg_enter
exit $?
