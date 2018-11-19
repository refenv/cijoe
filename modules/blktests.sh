#!/usr/bin/env bash
#
# blktests::env         - Checks environment for variable dependencies
# blktests::run         - Run a specific set of tests
#
# Variables REQUIRED by module
#
# BLOCK_DEV_PATH        - Path do block device to test
# BLKTESTS_HOME         - Path to blktests installation
#
# Optional variables
#

blktests::env() {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "blktests::env - Invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR definitions

  if [[ -z "$BLOCK_DEV_PATH" ]]; then
    cij::err "blktests::env BLOCK_DEV_PATH is not defined"
    return 1
  fi

  BLKTESTS_TARGET_DEV_PATH=$BLOCK_DEV_PATH
  if [[ -z "$BLKTESTS_HOME" ]]; then
    cij::err "blktests::env BLKTESTS_HOME is not defined"
    return 1
  fi

  return 0
}

blktests::run() {
  blktests::env
  if [[ $? -ne 0 ]]; then
    cij::err "blltest::run - Invalid ENV."
    return 1
  fi

  # blktests parameters are all optional
  TO_RUN=$1
  BLKTESTS_CMD="TEST_DEVS=$BLKTESTS_TARGET_DEV_PATH ./check $TO_RUN "

  cij::emph "Starting blktests with specification: $TO_RUN TEST_DEV=$BLKTESTS_TARGET_DEV_PATH"
  ssh::cmd "cd $BLKTESTS_HOME && $BLKTESTS_CMD"
  if [[ $? -ne 0 ]]; then
    cij::err "blktests::run Test failed"
    return 1
  fi

  return 0
}

