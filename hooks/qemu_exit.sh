#!/usr/bin/env bash
#
# Starts and stops a qemu instance
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

hook::qemu_exit() {

  if ! qemu::poweroff; then
    cij::warn "hook::qemu_exit: error when stopping QEMU"
    return 1;
  fi

  return 0
}

hook::qemu_exit
exit $?
