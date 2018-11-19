#!/usr/bin/env bash
#
# Starts pblk tracing
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::pblk_trace_enter {

  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij:err "hook::pblk_trace_enter: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  pblk::trace_all
  if [[ $? -ne 0 ]]; then
    cij.warn "hook::pblk_trace_enter: FAILED err: '$?'"
    return 1
  fi

  return 0
}

hook::pblk_trace_enter
exit $?
