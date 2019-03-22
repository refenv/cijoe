#!/usr/bin/env bash
#
# Detaches / Re-attached NVMe devices from kernel to SPDK and configures HUGEMEM
#
# on-enter: de-attach from kernel NVMe driver
# on-exit: re-attach to kernel NVMe driver
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require pci
test::enter

hook::spdk_exit() {

  if ! ssh::cmd "$SPDK_HOME/scripts/setup.sh reset"; then
    cij:err "hook::spdk_enter: FAILED: setting up SPDK devices"
    return 1
  fi

  return 0
}

hook::spdk_exit
exit $?
