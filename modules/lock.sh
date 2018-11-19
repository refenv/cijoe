#!/usr/bin/env bash
#
# lock.sh - Helpers for locking environments for mutually exclusive access
#
# Function:
#
# ...
#
# Variables:
#
# ...
#

function lock::enter_localhost
{
  LOCK_FILE="/tmp/CIJOE_LOCK"

  [[ -f $LOCK_FILE ]]
  if [[ $? -eq 0 ]]; then
    cij::err "lock::enter: FAILED: LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  touch $LOCK_FILE
  if [[ $? -ne 0 ]]; then
    cij::err "lock::enter: FAILED: creating LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::enter_remote
{
  LOCK_FILE="/opt/CIJOE_LOCK"

  ssh::cmd "[[ -f $LOCK_FILE ]]"
  if [[ $? -eq 0 ]]; then
    cij::err "lock::enter: FAILED: LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  ssh::cmd "touch $LOCK_FILE"
  if [[ $? -ne 0 ]]; then
    cij::err "lock::enter: FAILED: creating LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::enter_qemu
{
  LOCK_FILE="$QEMU_GUESTS/$QEMU_GUEST_NAME/CIJOE_LOCK"

  qemu::hostcmd "[[ -f $LOCK_FILE ]]"
  if [[ $? -eq 0 ]]; then
    cij::err "lock::enter: FAILED: LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  qemu::hostcmd "touch $LOCK_FILE"
  if [[ $? -ne 0 ]]; then
    cij::err "lock::enter: FAILED: creating LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::enter
{
  if [[ -n "$QEMU_HOST" ]]; then
    lock::enter_qemu;
    return $?;
  fi

  if [[ "$SSH_HOST" == "localhost" ]]; then
    lock::enter_localhost;
    return $?;
  else
    lock::enter_remote;
    return $?;
  fi
}

function lock::exit_localhost
{
  LOCK_FILE="/tmp/CIJOE_LOCK"

  rm $LOCK_FILE
  if [[ $? -ne 0 ]]; then
    cij::err "lock::exit: FAILED: rm LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::exit_remote
{
  LOCK_FILE="/opt/CIJOE_LOCK"

  ssh::cmd "rm $LOCK_FILE"
  if [[ $? -ne 0 ]]; then
    cij::err "lock::exit: FAILED: rm LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::exit_qemu
{
  LOCK_FILE="$QEMU_GUESTS/$QEMU_GUEST_NAME/CIJOE_LOCK"

  qemu::hostcmd "rm $LOCK_FILE"
  if [[ $? -ne 0 ]]; then
    cij::err "lock::exit: FAILED: rm LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

function lock::exit
{
  if [[ -n "$QEMU_HOST" ]]; then
    lock::exit_qemu;
    return $?;
  fi

  if [[ "$SSH_HOST" == "localhost" ]]; then
    lock::exit_localhost;
    return $?;
  else
    lock::exit_remote;
    return $?;
  fi
}

