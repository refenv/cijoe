#!/usr/bin/env bash
#
# ipmi.sh - Script providing convenience functions for invoking ipmi
#
# Functions:
#
# ipmi::env - Sets default vars for ipmi wrapping
# ipmi::cmd <CMD> - Execute ipmitool command <CMD>
# ipmi::on    - Power on system
# ipmi::off - Power off system
# ipmi::reset - Power reset system
#
# Variables:
#
# IPMI_USER - login on server
# IPMI_PASS - password to server
# IPMI_HOST - server host
# IPMI_PORT - server port
#

function ipmi::env
{
  if [ -z "$IPMI_USER" ]; then
    IPMI_USER="admin"
    echo "ipmi::env: IPMI_USER was unset, assigned '$IPMI_USER'"
  fi

  if [ -z "$IPMI_PASS" ]; then
    IPMI_PASS="admin"
    echo "ipmi::env: IPMI_PASS was unset, assigned '$IPMI_PASS'"
  fi

  if [ -z "$IPMI_HOST" ]; then
    IPMI_HOST="localhost"
    echo "ipmi::env: IPMI_HOST was unset, assigned '$IPMI_HOST'"
  fi

  if [ -z "$IPMI_PORT" ]; then
    IPMI_PORT="623"
    echo "ipmi::env: IPMI_PORT was unset, assigned '$IPMI_PORT'"
  fi

  return 0
}

function ipmi::cmd
{
  ipmi::env

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

  echo $CMD
  eval $CMD
}

function ipmi::on
{
  ipmi::env
  ipmi::cmd "power on"
}

function ipmi::off
{
  ipmi::env
  ipmi::cmd "power off"
}

function ipmi::reset
{
  ipmi::env
  ipmi::cmd "power reset"
}


function ipmi::powercycle
{
  ipmi::env
  ipmi::cmd "chassis power cycle"
}

function ipmi::console
{
  ipmi::env
  ipmi::cmd "-I lanplus sol activate"
}

