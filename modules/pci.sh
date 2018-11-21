#!/usr/bin/env bash
#
# pci.sh - Helpers for various PCI function
#
# Variables REQUIRED by module:
#
# PCI_DEV_NAME          - e.g. 0000:00:04.0
#
# Variables EXPORTED by module:
#
# PCI_BUS_PATH          - e.g. /sys/bus/pci
# PCI_DEV_PATH          - e.g. /sys/bus/pci/devices/0000:00:04.0
#

pci::env() {
  if ! ssh::env; then
    cij::err "pci::env: invalid SSH environment"
    return 1
  fi

  PCI_BUS_PATH="/sys/bus/pci"
  PCI_DEV_PATH="${PCI_BUS_PATH}/devices/${PCI_DEV_NAME}"
}

pci::exists() {
  if ! pci::env; then
    cij::err "pci::exists: invalid PCI environment"
    return 1
  fi

  cij::emph "pci::exists: TODO"
}

pci::remove() {
  if ! pci::env; then
    cij::err "pci::remove: invalid PCI environment"
    return 1
  fi

  cij::emph "pci::remove: PCI_DEV_NAME: ${PCI_DEV_NAME} .."
  ssh::cmd "echo 1 > ${PCI_DEV_PATH}/remove"
}

pci::rescan() {
  if ! pci::env; then
    cij::err "pci::rescan: invalid PCI environment"
    return 1
  fi

  cij::emph "pci::rescan: PCI_DEV_NAME: ${PCI_DEV_NAME} .."
  ssh::cmd "echo 1 > ${PCI_BUS_PATH}/rescan"
}
