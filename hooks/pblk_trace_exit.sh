#!/usr/bin/env bash
#
# hook: Starts / stops pblk tracing
#
# on-exit: retrieves the formatted trace buffer
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::pblk_trace_exit() {
  if ! pblk::trace_get "$CIJ_TEST_AUX_ROOT/hook_pblk_trace.log"; then
    cij::warn "hook::pblk_trace_exit: failed tracebuffer get"
    return 1;
  fi

  return 0
}

hook::pblk_trace_exit
exit $?
