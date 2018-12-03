#!/usr/bin/env bash
#
# Detaches NVMe devices from kernel NVMe driver to uio_generic or vfio-pci and
# configures HUGEMEM
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

function hook::spdk_enter {

  if ! ssh::cmd "$SPDK_HOME/scripts/setup.sh"; then
    cij:err "hook::spdk_enter: FAILED: setting up SPDK devices"
    return 1
  fi

  return 0
}

hook::spdk_enter
exit $?
