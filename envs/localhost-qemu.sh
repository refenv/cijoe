#!/usr/bin/env bash
#
# QEMU target environment skeleton
#
# The SSH configuration is overwritten such that everything using the "ssh::"
# module will be targeted towards the QEMU guest.
#
# To access the QEMU host an explicit "QEMU_HOST" and utility functions are
# provided by the "qemu::" module
#

# CIJOE: QEMU_* environment variables
: "${QEMU_HOST:=localhost}"; export QEMU_HOST
: "${QEMU_HOST_USER:=$USER}"; export QEMU_HOST_USER
: "${QEMU_HOST_PORT:=22}"; export QEMU_HOST_PORT
: "${QEMU_HOST_SYSTEM_BIN:=/opt/qemu/x86_64-softmmu/qemu-system-x86_64}"; export QEMU_HOST_SYSTEM_BIN
: "${QEMU_HOST_IMG_BIN:=qemu-img}"; export QEMU_HOST_IMG_BIN

: "${QEMU_GUESTS:=/opt/guests}"; export QEMU_GUESTS
: "${QEMU_GUEST_NAME:=emujoe}"; export QEMU_GUEST_NAME
: "${QEMU_GUEST_SSH_FWD_PORT:=2222}"; export QEMU_GUEST_SSH_FWD_PORT
: "${QEMU_GUEST_CONSOLE:=file}"; export QEMU_GUEST_CONSOLE
: "${QEMU_GUEST_MEM:=4G}"; export QEMU_GUEST_MEM
#: "${QEMU_GUEST_KERNEL:=1}"; export QEMU_GUEST_KERNEL
#: "${QEMU_GUEST_APPEND:=net.ifnames=0 biosdevname=0}"; export QEMU_GUEST_APPEND

# CIJOE: SSH_* environment variables
: "${SSH_HOST:=localhost}"; export SSH_HOST
: "${SSH_PORT:=$QEMU_GUEST_SSH_FWD_PORT}"; export SSH_PORT
: "${SSH_USER:=root}"; export SSH_USER
: "${SSH_NO_CHECKS:=1}"; export SSH_NO_CHECKS
