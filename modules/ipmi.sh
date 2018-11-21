#!/usr/bin/env bash
#
# ipmi.sh - Script providing convenience functions for invoking ipmi
#
# Functions:
#
# ipmi::env - Sets default vars for IPMI wrapping
# ipmi::cmd <CMD> - Execute ipmitool command <CMD>
# ipmi::on    - Power on system
# ipmi::off - Power off system
# ipmi::reset - Power reset system
#
# Variables REQUIRED by module:
#
# IPMI_HOST - hostname of IPMI
#
# Optional Variables:
#
# IPMI_USER - login on server
# IPMI_PASS - password to server
# IPMI_PORT - server port
#

ipmi::env() {
  # shellcheck disable=2153
  if [[ -z "$IPMI_HOST" ]]; then
    cij::err "ipmi::env: IPMI_HOST is unset"
    return 1
  fi

  if [[ -z "$IPMI_USER" ]]; then
    IPMI_USER="admin"
  fi
  if [[ -z "$IPMI_PASS" ]]; then
    IPMI_PASS="admin"
  fi
  if [[ -z "$IPMI_PORT" ]]; then
    IPMI_PORT="623"
  fi

  return 0
}

ipmi::cmd() {
  if ! ipmi::env; then
    cij::err "ipmi::cmd: invalid env"
  fi

  BIN="ipmitool"
  ARGS=""
  if [ -z "$1" ]; then
    echo "err: ipmi::cmd - No command given."
    return 1
  fi
  ARGS="$ARGS -U $IPMI_USER"
  ARGS="$ARGS -P $IPMI_PASS"
  ARGS="$ARGS -H $IPMI_HOST"
  ARGS="$ARGS -p $IPMI_PORT"

  CMD="$BIN $ARGS $1"

  cij::info "ipmi::cmd: $CMD"

  eval "$CMD"
}

ipmi::on() {
  if ! ipmi::env; then
    cij::err "ipmi::on: invalid env"
    return 1
  fi

  ipmi::cmd "power on"
  return $?
}

ipmi::off() {
  if ! ipmi::env; then
    cij::err "ipmi::off: invalid env"
    return 1
  fi

  ipmi::cmd "power off"
  return $?
}

ipmi::reset() {
  if ! ipmi::env; then
    cij::err "ipmi::reset: invalid env"
    return 1
  fi

  ipmi::cmd "power reset"
  return $?
}

ipmi::powercycle() {
  if ! ipmi::env; then
    cij::err "ipmi::console: invalid env"
    return 1
  fi

  ipmi::cmd "chassis power cycle"
  return $?
}

ipmi::console() {
  if ! ipmi::env; then
    cij::err "ipmi::console: invalid env"
    return 1
  fi

  ipmi::cmd "-I lanplus sol activate"
  return $?
}

