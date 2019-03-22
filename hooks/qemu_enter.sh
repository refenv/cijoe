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

hook::qemu_enter() {

  if ! qemu::guest_nvme_create; then
    cij::warn "hook::qemu_enter: FAILED to create test drive"
    return 1
  fi

  if ! qemu::run; then
    cij::warn "hook::qemu_enter: FAILED starting QEMU"
    return 1
  fi

  # Wait for it to boot up
  SSH_CMD_TIMEOUT=5
  while :
  do
      sleep 10
      if ssh::cmd 'exit' 2&> /dev/null; then
        break;
      fi
  done

  return 0
}

hook::qemu_enter
exit $?
