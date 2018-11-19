#!/usr/bin/env bash
#
# Sets up and starts a QEMU machine
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

function hook::qemu_enter {

  qemu::guest_nvme_create
  if [[ $? -ne 0 ]]; then
    cij::warn "hook::qemu_enter: FAILED to create test drive"
    return 1
  fi

  qemu::run
  if [[ $? -ne 0 ]]; then
    cij::warn "hook::qemu_enter: FAILED starting QEMU"
    return 1
  fi

  SSH_CMD_TIMEOUT=5 
  while :
  do
      sleep 10
      ssh::cmd 'exit' 2&> /dev/null
      if [[ $? == 0 ]]; then
	break
      fi
  done

  return 0
}

hook::qemu_enter
exit $?
