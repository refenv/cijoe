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

lock::exit_qemu() {
  LOCK_FILE="$QEMU_GUESTS/$QEMU_GUEST_NAME/CIJOE_LOCK"

  if ! qemu::hostcmd "rm \"$LOCK_FILE\""; then
    cij::err "lock::exit_qemu: failed releasing LOCK_FILE: '$LOCK_FILE'"
    return 1
  fi

  return 0
}

lock::enter() {
  if [[ -v QEMU_HOST && -n "$QEMU_HOST" ]]; then
    lock::enter_qemu;
    return $?;
  fi

  local lock_file="/tmp/CIJOE_LOCK"

  if [[ -f "$lock_file" ]]; then
    cij::err "lock::enter_localhost: failed: lock_file: '$lock_file' exists"
    return 1
  fi

  if ! touch "$lock_file"; then
    cij::err "lock::enter_localhost: failed: creating lock_file: '$lock_file'"
    return 1
  fi

  return 0
}

lock::exit() {
  if [[ -n "$QEMU_HOST" ]]; then
    lock::exit_qemu;
    return $?;
  fi

  local lock_file="/tmp/CIJOE_LOCK"

  if ! rm "$lock_file"; then
    cij::err "lock::exit_localhost: failed releasing lock_file: '$lock_file'"
    return 1
  fi

  return 0;
}
