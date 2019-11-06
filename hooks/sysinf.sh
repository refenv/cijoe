#!/usr/bin/env bash
#
# Stores and collects the following information:
#
# _aux/hook_sysinf_cpu.txt      (/proc/cpuinfo)
# _aux/hook_sysinf_mem.txt      (free -m)
# _aux/hook_sysinf_uname.txt    (uname -a)
# _aux/hook_sysinf_hw.txt       (lshw)
# _aux/hook_sysinf_os.txt       (/etc/os-release)
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
    cij::err "hook::sysinf: FAILED: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    return 1
  fi

  local res=0

  if ! ssh::cmd_output "cat /proc/cpuinfo" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_cpu.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_enter: FAILED: getting CPU info."
  fi

  if ! ssh::cmd_output "free -m" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_mem.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_enter: FAILED: getting MEM. info."
  fi

  if ! ssh::cmd_output "lshw" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_hw.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_enter: FAILED: getting HW info."
  fi

  if ! ssh::cmd_output "uname -a" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_uname.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_enter: FAILED: getting kernel info."
  fi

  if ! ssh::cmd_output "cat /etc/os-release" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_os.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_enter: FAILED: getting OS release info."
  fi

  if ! ssh::cmd_output "( set -o posix ; set )" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_env.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_env: FAILED: getting env.var. info."
  fi

  if ! ssh::cmd_output "[[ -r '/proc/config.gz' ]] && zcat /proc/config.gz || echo 'MISSING: CONFIG_IKCONFIG=y'" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_kiconfig.txt"; then
    res=$(( res + 1 ))
    cij::err "hook::sysinf_env: FAILED: getting /proc/config.gz"
  fi

  uname=$(ssh::cmd_output "uname -r")
  if ! ssh::cmd_output "[[ -r /boot/config-$uname ]] && cat /boot/config-$uname || echo 'MISSING: /boot/config-*'" > "$CIJ_TEST_AUX_ROOT/hook_sysinf_kbconfig.txt"; then
    res=$(( res + 1 ))
    cij:: "hook::sysinf_env: FAILED: getting /boot/config-*"
  fi

  return $res
}

hook::sysinf_enter
exit $?
