#!/usr/bin/env bash
#
# Stores and collects the following information:
#
# _aux/hook_sysinf_cpu.txt      (/proc/cpuinfo)
# _aux/hook_sysinf_mem.txt      (free -m)
# _aux/hook_sysinf_uname.txt    (uname -a)
# _aux/hook_sysinf_hw.txt       (lshw)
# _aux/hook_sysinf_os.txt       (/etc/lsb-release)
# _aux/hook_sysinf_env.txt      (shell variables)
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::sysinf_enter() {

  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    cij:err "hook::sysinf: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  HOOK_RES=0

  ssh::cmd_output "cat /proc/cpuinfo" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_cpu.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_enter: FAILED: getting CPU info."
  fi

  ssh::cmd_output "free -m" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_mem.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_enter: FAILED: getting MEM. info."
  fi

  ssh::cmd_output "lshw" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_hw.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_enter: FAILED: getting HW info."
  fi

  ssh::cmd_output "uname -a" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_uname.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_enter: FAILED: getting kernel info."
  fi

  ssh::cmd_output "cat /etc/lsb-release" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_os.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_enter: FAILED: getting kernel info."
  fi

  ssh::cmd_output "( set -o posix ; set )" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_env.txt"
  HOOK_RES=$(( HOOK_RES + $? ))
  if [[ $HOOK_RES -ne 0 ]]; then
    cij:err "hook::sysinf_env: FAILED: getting kernel info."
  fi

  return $HOOK_RES
}

hook::sysinf_enter
exit $?
