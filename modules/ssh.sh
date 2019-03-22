#!/usr/bin/env bash
#
# ssh.sh - Script providing convenience functions for invoking SSH
#
# Functions:
#
# ssh::env       - Sets default vars for ssh wrapping
# ssh::cmd <CMD> - Execute <CMD> using optional "SSH_CMD_TIMEOUT"
# ssh::shell     - Get the regular shell using current environment
#
# REQUIRED variables:
#
# SSH_USER              - SSH login on server
# SSH_HOST              - SSH server host
#
# DEFAULT variables:
#
# SSH_PORT              - SSH server port
#                         DEFAULT=22
# SSH_CMD_ECHO          - Print the CMD prior to execution
#                         DEFAULT=1, DISABLE=0, ENABLE=1
# SSH_CMD_TIME          - Measure wall-clock using "/usr/bin/time"
#                         DEFAULT=1, DISABLE=0, ENABLE=1
# SSH_CMD_TIMEOUT       - Max wall-clock for ssh::cmd
#                         DEFAULT=0, DISABLE=0, ENABLE=N seconds
#
# OPTIONAL variables:
#
# SSH_KEY               - Path to private key
# SSH_CMD_QUIET         - When 1, do the following
#                         * SSH_CMD_TIME=0
#                         * SSH_CMD_ECHO=0

ssh::env() {
  if [[ -n "$SSH_KEY" && ! -f "$SSH_KEY" ]]; then
    cij::err "ssh::env: Invalid SSH_KEY($SSH_KEY)"
    return 1
  fi

  # shellcheck disable=2153
  if [[ -z "$SSH_HOST" ]]; then
    cij::err "ssh::env: SSH_HOST is not set"
    return 1
  fi

  if [[ -z "$SSH_USER" ]]; then
    SSH_USER=root
  fi
  if [[ -z "$SSH_PORT" ]]; then
    SSH_PORT=22
  fi
  if [[ -z "$SSH_CMD_ECHO" ]]; then
    SSH_CMD_ECHO=1
  fi
  if [[ -z "$SSH_CMD_TIME" ]]; then
    SSH_CMD_TIME=1
  fi
  if [[ -z "$SSH_CMD_TIMEOUT" ]]; then
    SSH_CMD_TIMEOUT=0
  fi

  if [[ $SSH_CMD_QUIET -eq 1 ]]; then
    SSH_CMD_ECHO=0
    SSH_CMD_TIME=0
  fi

  return 0
}

ssh::cmd() {
  if [[ -z "$1" ]]; then
    cij::err "ssh::cmd - No command given."
    return 1
  fi

  if ! ssh::env; then
    cij::err "ssh::cmd - Invalid ENV."
    return 1
  fi

  SSH_BIN="ssh"

  if [[ $SSH_CMD_TIMEOUT -gt 0 ]]; then                 # TIME maximum
    SSH_BIN="timeout $SSH_CMD_TIMEOUT $SSH_BIN"
  fi

  if [[ $SSH_CMD_TIME -eq 1 ]]; then                    # TIME measure
    SSH_BIN="/usr/bin/time $SSH_BIN"
  fi

  SSH_CMD_ARGS=""                                       # SSH KEY
  if [[ -n "$SSH_KEY" ]]; then
    SSH_CMD_ARGS="$SSH_CMD_ARGS -i $SSH_KEY"
  fi

  if [[ -n "$SSH_PORT" ]]; then                       # SSH PORT
    SSH_CMD_ARGS="$SSH_CMD_ARGS -p $SSH_PORT"
  fi

  SSH_CMD_ARGS="$SSH_CMD_ARGS $SSH_USER@$SSH_HOST"      # SSH USER and HOST

  SSH_CMD="$SSH_BIN $SSH_EXTRA_ARGS $SSH_CMD_ARGS '$1'" # SSH command

  if [[ $SSH_CMD_ECHO -eq 1 ]]; then                    # SSH print CMD
    cij::emph "ssh:cmd: $SSH_CMD"
  fi

  eval "$SSH_CMD"                                       # Execute it
}

ssh::cmd_output() {
  SSH_CMD_QUIET=1 ssh::cmd "$1"
}

ssh::cmd_t() {
  SSH_EXTRA_ARGS="-t" ssh::cmd "$1"
}

ssh::shell() {
  if ! ssh::env; then
    cij::err "ssh::shell - Invalid ENV."
    return 1
  fi

  SSH_SHELL_ARGS=""
  SSH_SHELL_ARGS="$SSH_SHELL_ARGS -p $SSH_PORT"
  SSH_SHELL_ARGS="$SSH_SHELL_ARGS $SSH_USER@$SSH_HOST"

  if [[ -n "$SSH_KEY" ]]; then
    SSH_SHELL_ARGS="$SSH_SHELL_ARGS -i $SSH_KEY"
  fi

  SSH_SHELL="ssh $SSH_SHELL_ARGS"

  eval "$SSH_SHELL"
}

ssh::shutdown() {
  if ! ssh::env; then
    cij::err "ssh::shutdown - Invalid ENV."
    return 1
  fi

  ssh::cmd 'shutdown now'
}

ssh::check() {
  if ! ssh::env; then
    cij::err "ssh::check - Invalid ENV."
    return 1
  fi

  ssh::cmd 'hostname'
  return $?
}

ssh::push() {
  SRC=$1
  if [[ -z "$SRC" ]]; then
    cij::err "ssh::copy: local path SRC: '$SRC'"
    return 1
  fi

  DST=$2
  if [[ -z "$DST" ]]; then
    cij::err "ssh::copy: remote path DST: '$DST'"
    return 1
  fi

  if ! ssh::env; then
    cij::err "ssh::copy: invalid environment"
    return 1
  fi

  SCP_CMD_ARGS=""
  if [[ -n "$SSH_PORT" ]]; then
    SCP_CMD_ARGS="${SCP_CMD_ARGS} -P $SSH_PORT"
  fi
  if [[ -n "$SSH_KEY" ]]; then
    SCP_CMD_ARGS="${SCP_CMD_ARGS} -i $SSH_KEY"
  fi

  SCP_CMD="scp $SCP_CMD_ARGS $SRC ${SSH_USER}@${SSH_HOST}:$DST"

  eval "$SCP_CMD"
}

ssh::pull() {
  SRC=$1
  if [[ -z "$SRC" ]]; then
    cij::err "ssh::copy: remote path SRC: '$SRC'"
    return 1
  fi

  DST=$2
  if [[ -z "$DST" ]]; then
    cij::err "ssh::copy: local path DST: '$DST'"
    return 1
  fi

  if ! ssh::env; then
    cij::err "ssh::copy: invalid environment"
    return 1
  fi

  SCP_CMD_ARGS="-r"
  if [[ -n "$SSH_PORT" ]]; then
    SCP_CMD_ARGS="${SCP_CMD_ARGS} -P $SSH_PORT"
  fi
  if [[ -n "$SSH_KEY" ]]; then
    SCP_CMD_ARGS="${SCP_CMD_ARGS} -i $SSH_KEY"
  fi

  SCP_CMD="scp $SCP_CMD_ARGS ${SSH_USER}@${SSH_HOST}:$SRC $DST"

  eval "$SCP_CMD"
}

ssh::reboot() {
  if ! ssh::env; then
    cij::err "ssh::reboot - Invalid ENV."
    return 1
  fi

  if [[ -z $1 ]]; then
    cij::err "ssh::reboot - No Timeout."
    return 1
  fi

  SSH_CMD_TIMEOUT_BACKUP=$SSH_CMD_TIMEOUT
  SSH_CMD_TIMEOUT=3
  SSH_REBOOT_START_TIME=$(/bin/date +%s)
  SSH_REBOOT_CONNECT_TIMEOUT=$1

  if ! SSH_REBOOT_LAST_BOOT_TIME=$(ssh::cmd '/usr/bin/uptime -s'); then
    cij::err "ssh::reboot cannot get the target boot time."
    SSH_CMD_TIMEOUT=$SSH_CMD_TIMEOUT_BACKUP
    return 1
  fi

  cij::emph "ssh::reboot: Reboot TARGET($CIJ_TEST_HOST)..."
  ssh::cmd 'reboot'

  while :
  do
    sleep 1

    SSH_REBOOT_CURRENT_TIME=$(/bin/date +%s)
    SSH_REBOOT_TIME_ELAPSED=$(( SSH_REBOOT_CURRENT_TIME - SSH_REBOOT_START_TIME))
    if [[ $SSH_REBOOT_TIME_ELAPSED -gt $SSH_REBOOT_CONNECT_TIMEOUT ]]; then
      SSH_REBOOT_RCODE=1
      cij::err "ssh::reboot - Timeout: $SSH_REBOOT_TIME_ELAPSED seconds."
      break
    fi

    if ! ssh::cmd 'exit' 2&> /dev/null; then
      if ! SSH_REBOOT_CURRENT_BOOT_TIME=$(ssh::cmd_output '/usr/bin/uptime -s'); then
        continue    # Cannot get the boot time, continue waiting
      fi
      if [[ "$SSH_REBOOT_LAST_BOOT_TIME" == "$SSH_REBOOT_CURRENT_BOOT_TIME" ]]; then
        continue    # Not reboot completely, continue waiting
      fi

      SSH_REBOOT_RCODE=0
      cij::emph "ssh::reboot: Time elapsed: $SSH_REBOOT_TIME_ELAPSED seconds."
      break
    fi
  done

  SSH_CMD_TIMEOUT=$SSH_CMD_TIMEOUT_BACKUP
  return $SSH_REBOOT_RCODE
}
