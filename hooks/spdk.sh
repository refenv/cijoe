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
  SPDK_CMD="$SPDK_HOME/scripts/setup.sh"
  if [[ ! -z "$HUGEMEM" ]]; then
    SPDK_CMD="HUGEMEM=$HUGEMEM $SPDK_CMD"
  fi
  if [[ ! -z "$NRHUGE" ]]; then
    SPDK_CMD="NRHUGE=$NRHUGE $SPDK_CMD"
  fi
  if [[ ! -z "$HUGENODE" ]]; then
    SPDK_CMD="HUGENODE=$HUGENODE $SPDK_CMD"
  fi

  if ! ssh::cmd "$SPDK_CMD"; then
    cij:err "hook::spdk_enter: FAILED: setting up SPDK devices"
    return 1
  fi

  return 0
}

hook::spdk_enter
exit $?
