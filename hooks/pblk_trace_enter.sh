#!/usr/bin/env bash
#
# hook: Starts / stops pblk tracing
#
# on-enter: signals pblk tracing to start
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::pblk_trace_enter() {
  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij:err "hook::pblk_trace_enter: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  if ! pblk::trace_all; then
    cij.warn "hook::pblk_trace_enter: FAILED err: '$?'"
    return 1
  fi

  return 0
}

hook::pblk_trace_enter
exit $?
