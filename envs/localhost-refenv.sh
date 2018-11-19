#!/usr/bin/env bash
source $CIJ_ROOT/envs/common.sh

export CIJ_TEST_RES_ROOT="/opt/testing"
export CIJ_CTRL="localhost"
export CIJ_TRGT="localhost"

export SSH_USER=root
export SSH_HOST=localhost
export SSH_PORT=22

export NVME_NAME="nvme0n1"
export DEV_ALIAS="UNKNOWN"

export BOARD_FORMFACTOR="NONE"
export BOARD_MEMORY="NONE"
export BOARD_CHIP="NONE"
export BOARD_PCB="NONE"
export BOARD_ALIAS="NONE"

export PCI_DEV_NAME="0000:01:00.0"
export NVME_DEV_NAME="nvme0n1"

export MOUNT_POINT=/opt

nvme::env

# Allow to provide pblk LUN configurations at a testplan level
if [ -z $LNVM_BGN ]; then
  LNVM_BGN=0
fi
if [ -z $LNVM_END ]; then
  LNVM_END=$(($NVME_LNVM_TOTAL_LUNS - 1))
fi
lnvm::env

export BLOCK_DEV_NAME=$LNVM_DEV_NAME

# liblightnvm: assume SPDK backend
export NVM_DEV_NAME="traddr:$PCI_DEV_NAME"

# liblightnvm: change if the NVMe device still exists this means that the device
# have not been rebound from 'nvme' to 'uio_pci_generic', in other words. The
# "SPDK" hook have not been used.
nvme::exists
if [[ $? -eq 0 ]]; then
  NVM_DEV_NAME="/dev/$NVME_DEV_NAME"
fi
