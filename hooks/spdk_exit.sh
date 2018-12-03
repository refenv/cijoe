#!/usr/bin/env bash
#
# Rebinds NVMe devices from driver "nvme" to "uio_pci_generic" for use with SPDK
# And attempt to rebind again after
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
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
