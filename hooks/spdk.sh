#!/usr/bin/env bash
#
# Rebinds NVMe devices from driver "nvme" to "uio_pci_generic" for use with SPDK
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::enter

function hook::spdk_enter {

  ssh::cmd "/opt/spdk/scripts/setup.sh"
  if [[ $? -ne 0 ]]; then
    cij:err "hook::spdk_enter: FAILED: setting up SPDK devices"
    return 1
  fi

  return 0
}

hook::spdk_enter
exit $?
