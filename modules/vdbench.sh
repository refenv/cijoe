#!/usr/bin/env bash
#
# Please add some documentation here
#

vdbench::env() {
  if [[ "$VDBENCH_ENV" == "1" ]]; then
    return 0
  fi

  if ! ssh::env; then
    cij::err "vdbench::env: invalid SSH ENV."
    return 1
  fi

  # shellcheck disable=2153
  if [[ -z "$VDBENCH_BIN" ]]; then
    cij::err "vdbench::env: VDBENCH_BIN is not defined"
    return 1
  fi

  VDBENCH_ENV=1

  return 0
}

vdbench::run() {
  if ! vdbench::env; then
    cij::err "vdbench::run - Invalid SSH ENV."
    return 1
  fi

  VDBENCH_LUN=$1
  if [[ -z "$VDBENCH_LUN" ]]; then
    cij::err "vdbench::run: Usage: vdbench::run \"/dev/nvme0n1\""
    return 1
  fi

  ARGS="-"
  if [[ -n "$VDBENCH_LUN" ]]; then
    ARGS="$ARGS lun=$VDBENCH_LUN"
  fi
  if [[ -n "$VDBENCH_DATA_VALIDATE" ]]; then
    ARGS="-v $ARGS"
  fi
  if [[ -n "$VDBENCH_DATA_ERRORS" ]]; then
    ARGS="$ARGS data_errors=$VDBENCH_DATA_ERRORS"
  fi
  if [[ -n "$VDBENCH_COMPRATIO" ]]; then
    ARGS="$ARGS compratio=$VDBENCH_COMPRATIO"
  fi

  # shellcheck disable=2153
  if [[ -n "$VDBENCH_HD" ]]; then
    ARGS="$ARGS hd=$VDBENCH_HD"
  fi
  if [[ -n "$VDBENCH_JVMS" ]]; then
    ARGS="$ARGS jvms=$VDBENCH_JVMS"
  fi
  if [[ -n "$VDBENCH_VALIDATE" ]]; then
    ARGS="$ARGS validate=$VDBENCH_VALIDATE"
  fi
  # shellcheck disable=2153
  if [[ -n "$VDBENCH_SD" ]]; then
    ARGS="$ARGS sd=$VDBENCH_SD"
  fi
  if [[ -n "$VDBENCH_THREADS" ]]; then
    ARGS="$ARGS threads=$VDBENCH_THREADS"
  fi
  if [[ -n "$VDBENCH_OPENFLAGS" ]]; then
    ARGS="$ARGS openflags=$VDBENCH_OPENFLAGS"
  fi
  if [[ -n "$VDBENCH_SIZE" ]]; then
    ARGS="$ARGS size=$VDBENCH_SIZE"
  fi
  # shellcheck disable=2153
  if [[ -n "$VDBENCH_WD" ]]; then
    ARGS="$ARGS wd=$VDBENCH_WD"
  fi
  if [[ -n "$VDBENCH_SD" ]]; then
    ARGS="$ARGS sd=$VDBENCH_SD"
  fi
  if [[ -n "$VDBENCH_XFERSIZE" ]]; then
    ARGS="$ARGS xfersize=$VDBENCH_XFERSIZE"
  fi
  if [[ -n "$VDBENCH_RDPCT" ]]; then
    ARGS="$ARGS rdpct=$VDBENCH_RDPCT"
  fi
  if [[ -n "$VDBENCH_SEEKPCT" ]]; then
    ARGS="$ARGS seekpct=$VDBENCH_SEEKPCT"
  fi
  if [[ -n "$VDBENCH_XFERSIZE" ]]; then
    ARGS="$ARGS xfersize=$VDBENCH_XFERSIZE"
  fi
  # shellcheck disable=2153
  if [[ -n "$VDBENCH_RD" ]]; then
    ARGS="$ARGS rd=$VDBENCH_RD"
  fi
  if [[ -n "$VDBENCH_WD" ]]; then
    ARGS="$ARGS wd=$VDBENCH_WD"
  fi
  if [[ -n "$VDBENCH_IORATE" ]]; then
    ARGS="$ARGS iorate=$VDBENCH_IORATE"
  fi
  if [[ -n "$VDBENCH_ELAPSED" ]]; then
    ARGS="$ARGS elapsed=$VDBENCH_ELAPSED"
  fi
  if [[ -n "$VDBENCH_INTERVAL" ]]; then
    ARGS="$ARGS interval=$VDBENCH_INTERVAL"
  fi
  if [[ -n "$VDBENCH_FORXFERSIZE" ]]; then
    ARGS="$ARGS forxfersize=$VDBENCH_FORXFERSIZE"
  fi
  if [[ -n "$VDBENCH_FORSEEKPCT" ]]; then
    ARGS="$ARGS forseekpct=$VDBENCH_FORSEEKPCT"
  fi
  if [[ -n "$VDBENCH_FORRDPCT" ]]; then
    ARGS="$ARGS forrdpct=$VDBENCH_FORRDPCT"
  fi

  VDBENCH_CMD="$VDBENCH_BIN $ARGS"

  if [[ -n "$VDBENCH_CMD_PREFIX" ]]; then
    VDBENCH_CMD="$VDBENCH_CMD_PREFIX $VDBENCH_CMD"
  fi

  if [[ -n "$VDBENCH_CMD_POSTFIX" ]]; then
    VDBENCH_CMD="$VDBENCH_CMD $VDBENCH_CMD_POSTFIX"
  fi

  if ! ssh::cmd "ulimit -n 100000"; then
    cij::err "vdbench::run: setting ulimit failed"
    return 1
  fi

  cij::emph "Running: $VDBENCH_CMD"
  if ! ssh::cmd "$VDBENCH_CMD"; then
    cij::err "vdbench::run: vdbench returned with an error"
    return 1
  fi
}
