#!/usr/bin/env bash
#
# ssh.sh - Script providing convenience functions for invoking SSH
#
# Functions:
#
# ssh.env       - Sets default vars for ssh wrapping
# ssh.cmd <CMD> - Execute <CMD> using optional "SSH_CMD_TIMEOUT"
# ssh.shell     - Get the regular shell using current environment
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
# SSH_CMD_TIMEOUT       - Max wall-clock for ssh.cmd
#                         DEFAULT=0, DISABLE=0, ENABLE=N seconds
#
# OPTIONAL variables:
#
# SSH_KEY               - Path to private key
# SSH_NO_CHECKS         - When 1, disable known_hosts and StrictHostKeyChecking
# SSH_CMD_QUIET         - When 1, do the following
#                         * SSH_CMD_TIME=0
#                         * SSH_CMD_ECHO=0

ssh.env() {
  if [[ -v SSH_KEY && -n "$SSH_KEY" && ! -f "$SSH_KEY" ]]; then
    cij.err "ssh.env: Invalid SSH_KEY($SSH_KEY)"
    return 1
  fi

  if [[ ! -v SSH_HOST || -z "$SSH_HOST" ]]; then
    cij.err "ssh.env: SSH_HOST is not set or is empty"
    return 1
  fi

  : "${SSH_BIN:=ssh}"
  : "${SSH_NO_CHECKS:=0}"
  : "${SSH_USER:=root}"
  : "${SSH_PORT:=22}"
  : "${SSH_CMD_ECHO:=1}"
  : "${SSH_CMD_TIME:=1}"
  : "${SSH_CMD_TIMEOUT:=0}"

  if [[ -v SSH_CMD_QUIET && $SSH_CMD_QUIET -eq 1 ]]; then
    SSH_CMD_ECHO=0
    SSH_CMD_TIME=0
  fi

  return 0
}

ssh.cmd() {
  if [[ -z "$1" ]]; then
    cij.err "ssh.cmd - No command given."
    return 1
  fi
  if ! ssh.env; then
    cij.err "ssh.cmd - Invalid ENV."
    return 1
  fi

  local _prefix="";
  local _args="";
  local _cmd="";

  if [[ -v SSH_CMD_TIMEOUT && $SSH_CMD_TIMEOUT -gt 0 ]]; then   # TIME maximum
    _prefix="timeout $SSH_CMD_TIMEOUT $_prefix "
  fi
  if [[ -v SSH_CMD_TIME && $SSH_CMD_TIME -eq 1 ]]; then         # TIME measure
    _prefix="/usr/bin/time $_prefix "
  fi

  if [[ -v SSH_KEY && -n "$SSH_KEY" ]]; then                    # KEY
    _args="$_args -i $SSH_KEY"
  fi
  if [[ -v SSH_PORT && -n "$SSH_PORT" ]]; then                  # PORT
    _args="$_args -p $SSH_PORT"
  fi
  if [[ -v SSH_NO_CHECKS && $SSH_NO_CHECKS -eq 1 ]]; then       # NO_CHECK
    _args="$_args -o UserKnownHostsFile=/dev/null"
    _args="$_args -o StrictHostKeyChecking=no"
  fi
  if [[ -v SSH_EXTRA_ARGS ]]; then                              # Extras
    _args="$_args $SSH_EXTRA_ARGS"
  fi
  _args="$_args $SSH_USER@$SSH_HOST"                            # USER and HOST

  # Construct ssh-command
  _cmd="$_prefix $SSH_BIN $_args '$1'"                          # Create CMD
  if [[ -v SSH_CMD_ECHO && $SSH_CMD_ECHO -eq 1 ]]; then         # Print CMD
    cij.emph "ssh:cmd: $_cmd"
  fi

  eval "$_cmd"                                                  # Execute CMD
  return $?
}

ssh.cmd_output() {
  SSH_CMD_QUIET=1 ssh.cmd "$1"
}

ssh.cmd_t() {
  SSH_EXTRA_ARGS="-t" ssh.cmd "$1"
}

ssh.shell() {
  if ! ssh.env; then
    cij.err "ssh.shell - Invalid ENV."
    return 1
  fi

  local _prefix="";
  local _args="";
  local _cmd="";

  if [[ -v SSH_KEY && -n "$SSH_KEY" ]]; then                    # KEY
    _args="$_args -i $SSH_KEY"
  fi
  if [[ -v SSH_PORT && -n "$SSH_PORT" ]]; then                  # PORT
    _args="$_args -p $SSH_PORT"
  fi
  if [[ -v SSH_NO_CHECKS && $SSH_NO_CHECKS -eq 1 ]]; then
    _args="$_args -o UserKnownHostsFile=/dev/null"
    _args="$_args -o StrictHostKeyChecking=no"
  fi
  _args="$_args $SSH_USER@$SSH_HOST"                            # USER and HOST

  if [[ -v SSH_EXTRA_ARGS ]]; then
    _args="$_args $SSH_EXTRA_ARGS"
  fi

  _cmd="$_prefix $SSH_BIN $_args"                               # Create CMD
  if [[ -v SSH_CMD_ECHO && $SSH_CMD_ECHO -eq 1 ]]; then         # Print CMD
    cij.emph "ssh:cmd: $_cmd"
  fi

  eval "$_cmd"                                                  # Execute CMD
}

ssh.push() {
  local _src=$1
  local _dst=$2
  local _args=""
  local _cmd=""

  if [[ ! -v _src ]]; then
    cij.err "ssh.push: local path _src: '$_src'"
    return 1
  fi
  if [[ ! -v _dst ]]; then
    cij.err "ssh.push: remote path _dst: '$_dst'"
    return 1
  fi
  if ! ssh.env; then
    cij.err "ssh.push: invalid environment"
    return 1
  fi

  _args=""
  if [[ -v SSH_KEY && -n "$SSH_KEY" ]]; then                    # KEY
    _args="$_args -i $SSH_KEY"
  fi
  if [[ -v SSH_PORT && -n "$SSH_PORT" ]]; then                  # PORT
    _args="$_args -P $SSH_PORT"
  fi
  if [[ -v SSH_NO_CHECKS && $SSH_NO_CHECKS -eq 1 ]]; then
    _args="$_args -o UserKnownHostsFile=/dev/null"
    _args="$_args -o StrictHostKeyChecking=no"
  fi

  _cmd="scp $_args $_src ${SSH_USER}@${SSH_HOST}:$_dst"
  if [[ -v SSH_CMD_ECHO && $SSH_CMD_ECHO -eq 1 ]]; then         # Print CMD
    cij.emph "ssh:push:cmd: $_cmd"
  fi

  eval "$_cmd"
}

ssh.pull() {
  local _src=$1
  local _dst=$2
  local _args=""
  local _cmd=""

  if [[ ! -v _src ]]; then
    cij.err "ssh.pull: local path _src: '$_src'"
    return 1
  fi
  if [[ ! -v _dst ]]; then
    cij.err "ssh.pull: remote path _dst: '$_dst'"
    return 1
  fi
  if ! ssh.env; then
    cij.err "ssh.pull: invalid environment"
    return 1
  fi

  _args="-r"
  if [[ -v SSH_KEY && -n "$SSH_KEY" ]]; then                    # KEY
    _args="$_args -i $SSH_KEY"
  fi
  if [[ -v SSH_PORT && -n "$SSH_PORT" ]]; then                  # PORT
    _args="$_args -P $SSH_PORT"
  fi
  if [[ -v SSH_NO_CHECKS && $SSH_NO_CHECKS -eq 1 ]]; then
    _args="$_args -o UserKnownHostsFile=/dev/null"
    _args="$_args -o StrictHostKeyChecking=no"
  fi

  _cmd="scp $_args ${SSH_USER}@${SSH_HOST}:$_src $_dst"

  eval "$_cmd"
}

ssh.check() {
  if ! ssh.env; then
    cij.err "ssh.check: invalid environment"
    return 1
  fi

  ssh.cmd "hostname"
  return $?
}
