#!/usr/bin/env bash
#
# retrieves the formatted trace buffer
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::enter

function hook::pblk_trace_exit {
  pblk::trace_get $CIJ_TEST_AUX_ROOT/hook_pblk_trace.log
  if [[ $? -ne 0 ]]; then
    cij::warn "hook::pblk_trace_exit: failed tracebuffer get"
    return 1;
  fi

  return 0
}

hook::pblk_trace_exit
exit $?
