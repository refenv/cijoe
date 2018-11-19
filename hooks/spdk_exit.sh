#!/usr/bin/env bash
#
# Rebinds NVMe devices from driver "nvme" to "uio_pci_generic" for use with SPDK
# And attempt to rebind again after
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require pci
test::enter

function hook::spdk_exit {

  pci::remove
  if [[ $? -ne 0 ]]; then
    cij:err "hook::spdk_exit: FAILED: PCI_DEV_NAME: '$PCI_DEV_NAME' remove"
    return 1
  fi

  pci::rescan
  if [[ $? -ne 0 ]]; then
    cij:err "hook::spdk_exit: FAILED: rescanning PCI bus"
    return 1
  fi

  return 0
}

hook::spdk_exit
exit $?
