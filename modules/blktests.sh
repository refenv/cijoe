#!/usr/bin/env bash
#
# Wrapping the Linux kernel block layer testing framework AKA blktests
#
# Helper functions provided to aid running in CTRL <-> TARGET setup
#
# blktests::env         - Checks environment for variable dependencies
# blktests::run         - Run blktests targeting $BLOCK_DEV_PATH
#
# Variables REQUIRED by module
#
# BLOCK_DEV_PATH        - Path to block device to test
# BLKTESTS_HOME         - Path to blktests installation
#

blktests::env() {
  if ! ssh::env; then
    cij::err "blktests::env - Invalid SSH ENV."
    return 1
  fi

  # Check for EVAR required by package
  if [[ -z "$BLOCK_DEV_PATH" ]]; then
    cij::err "blktests::env BLOCK_DEV_PATH is not defined"
    return 1
  fi
  if [[ -z "$BLKTESTS_HOME" ]]; then
    cij::err "blktests::env BLKTESTS_HOME is not defined"
    return 1
  fi

  return 0
}

#
# Run the blktests 'check' command in the following CTRL <-> TRGT setup:
#
# * restricted to run only on BLOCK_DEV_PATH
# * results stored in temp folder (/tmp/blktests.XXXXX) on TRGT
# * results pulled from TRGT tempt folder to CTRL folder post run
#
# blktests::run PATH [AUX]
#
blktests::run() {
  if ! blktests::env; then
    cij::err "blktests::run - Invalid ENV."
    return 1
  fi

  # Path to blktests results
  BLKTESTS_CTRL_OUTPUT=$1
  if [[ -z "$BLKTESTS_CTRL_OUTPUT" ]]; then
    cij::err "blktests::run please provide path to result directory on CTRL"
    return 1
  fi
  if [[ ! -d "$BLKTESTS_CTRL_OUTPUT" ]]; then
    cij::err "blktests::run invalid path to result directory on CTRL"
    return 1
  fi

  # Optional auxilary arguments to blktests ./check
  BLKTESTS_CMD_AUX=$2

  cij::info "Creating result directory on TRGT"
  BLKTESTS_TRGT_OUTPUT=$(ssh::cmd_output "mktemp -d blktests_XXXXXX -p /tmp")
  if ! ssh::cmd "[[ -d $BLKTESTS_TRGT_OUTPUT ]]"; then
    cij::err "blktests::run failed creating result directory on TRGT"
    return 1
  fi

  cij::info "Starting blktests"
  BLKTESTS_CMD="TEST_DEVS=$BLOCK_DEV_PATH ./check"
  BLKTESTS_CMD="$BLKTESTS_CMD -d"
  BLKTESTS_CMD="$BLKTESTS_CMD --output=$BLKTESTS_TRGT_OUTPUT"
  BLKTESTS_CMD="$BLKTESTS_CMD $BLKTESTS_CMD_AUX"

  ssh::cmd "cd $BLKTESTS_HOME && $BLKTESTS_CMD"
  CHECK_RCODE=$?
  if [[ "$CHECK_RCODE" -ne 0 ]]; then
    cij::err "blktests::run ./check exited with error"
  fi

  cij::info "Pulling blktests results from TRGT"
  if ! ssh::pull "$BLKTESTS_TRGT_OUTPUT" "$BLKTESTS_CTRL_OUTPUT"; then
    cij::err "blktests::run failed pulling results from TRGT"
    return 1
  fi

  return $CHECK_RCODE
}
