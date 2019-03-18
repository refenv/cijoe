#!/usr/bin/env bash
#
# ipmi.sh - Script providing convenience functions for invoking IPMI commands
#
# Functions:
#
# ipmi::env             - Sets default vars for IPMI wrapping
# ipmi::command <CMD>   - Execute ipmitool command <CMD>
# ipmi::pwr_on          - Power on system
# ipmi::pwr_off         - Power off system
# ipmi::pwr_reset       - Power reset system
# ipmi::pwr_cycle       - Power cycle the system
# ipmi::console         - Start serial console
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

  : "${IPMI_USER:=admin}"
  export IPMI_USER

  : "${IPMI_PASS:=admin}"
  export IPMI_PASS

  : "${IPMI_PORT:=623}"
  export IPMI_PORT

  return 0
}

ipmi::command() {
  if ! ipmi::env; then
    cij::err "ipmi::command: invalid env"
  fi

  if [[ -z "$1" ]]; then
    echo "err: ipmi::command - No command given."
    return 1
  fi

  local bin="ipmitool"
  local args=""

  args="$args -U $IPMI_USER"
  args="$args -P $IPMI_PASS"
  args="$args -H $IPMI_HOST"
  args="$args -p $IPMI_PORT"

  local cmd="$bin $args $1"

  cij::info "ipmi::command: $cmd"

  eval "$cmd"
}

ipmi::pwr_on() {
  if ! ipmi::env; then
    cij::err "ipmi::pwr_on: invalid env"
    return 1
  fi

  ipmi::command "power on"
  return $?
}

ipmi::pwr_off() {
  if ! ipmi::env; then
    cij::err "ipmi::pwr_off: invalid env"
    return 1
  fi

  ipmi::command "power off"
  return $?
}

ipmi::pwr_reset() {
  if ! ipmi::env; then
    cij::err "ipmi::pwr_reset: invalid env"
    return 1
  fi

  ipmi::command "power reset"
  return $?
}

ipmi::pwr_cycle() {
  if ! ipmi::env; then
    cij::err "ipmi::pwer_cycle: invalid env"
    return 1
  fi

  ipmi::command "chassis power cycle"
  return $?
}

ipmi::console() {
  if ! ipmi::env; then
    cij::err "ipmi::console: invalid env"
    return 1
  fi

  ipmi::command "-I lanplus sol activate"
  return $?
}

