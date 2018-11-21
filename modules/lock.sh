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

lock::enter_localhost() {
  LOCK_FILE="/tmp/CIJOE_LOCK"

  if [[ -f "$LOCK_FILE" ]]; then
    cij::err "lock::enter_localhost: failed: LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  if ! touch "$LOCK_FILE"; then
    cij::err "lock::enter_localhost: failed: creating LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::enter_remote() {
  LOCK_FILE="/opt/CIJOE_LOCK"

  if ssh::cmd "[[ -f \"$LOCK_FILE\" ]]"; then
    cij::err "lock::enter_remote: failed, LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  if ! ssh::cmd "touch \"$LOCK_FILE\""; then
    cij::err "lock::enter_remote: failing taking LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::enter_qemu() {
  LOCK_FILE="$QEMU_GUESTS/$QEMU_GUEST_NAME/CIJOE_LOCK"

  if qemu::hostcmd "[[ -f \"$LOCK_FILE\" ]]"; then
    cij::err "lock::enter_qemu: failed, LOCK_FILE: '$LOCK_FILE' exists"
    return 1
  fi

  if ! qemu::hostcmd "touch \"$LOCK_FILE\""; then
    cij::err "lock::enter_qemu: failed: creating LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::enter() {
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

lock::exit_localhost() {
  LOCK_FILE="/tmp/CIJOE_LOCK"

  if ! rm "$LOCK_FILE"; then
    cij::err "lock::exit_localhost: failed releasing LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::exit_remote() {
  LOCK_FILE="/opt/CIJOE_LOCK"

  if ! ssh::cmd "rm \"$LOCK_FILE\""; then
    cij::err "lock::exit_remote: failed releasing LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::exit_qemu() {
  LOCK_FILE="$QEMU_GUESTS/$QEMU_GUEST_NAME/CIJOE_LOCK"

  if ! qemu::hostcmd "rm \"$LOCK_FILE\""; then
    cij::err "lock::exit_qemu: failed releasing LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::exit() {
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

