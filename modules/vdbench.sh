#!/usr/bin/env bash

function vdbench::env
{
  if [[ $VDBENCH_ENV -eq 1 ]]; then
    return 0
  fi

  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "vdbench::env: invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR> definitions
  if [[ -z "$VDBENCH_BIN" ]]; then
    cij::err "vdrbench::env: VDBENCH_BIN is not defined"
    return 1
  fi
  VDBENCH_ENV=1

  return 0
}

function vdbench::run {
  vdbench::env
  if [[ $? -ne 0 ]]; then
    cij::err "vbench::run - Invalid SSH ENV."
    return 1
  fi

  ARGS="-"
  if [ -n "$DATA_VALIDATE" ]; then
    ARGS="-v $ARGS"
  fi
  if [ -n "$DATA_ERRORS" ]; then
    ARGS="$ARGS data_errors=$DATA_ERRORS"
  fi

  if [ -n "$COMPRATIO" ]; then
    ARGS="$ARGS compratio=$COMPRATIO"
  fi

  if [ -n "$HD" ]; then
    ARGS="$ARGS hd=$HD"
  fi

  if [ -n "$JVMS" ]; then
    ARGS="$ARGS jvms=$JVMS"
  fi

  if [ -n "$VALIDATE" ]; then
    ARGS="$ARGS validate=$VALIDATE"
  fi

  if [ -n "$SD" ]; then
    ARGS="$ARGS sd=$SD"
  fi

if [ -n "$LUN" ]; then
    ARGS="$ARGS lun=$LUN"
  fi

 if [ -n "$THREADS" ]; then
    ARGS="$ARGS threads=$THREADS"
  fi

  if [ -n "$OPENFLAGS" ]; then
    ARGS="$ARGS openflags=$OPENFLAGS"
  fi

  if [ -n "$SIZE" ]; then
    ARGS="$ARGS size=$SIZE"
  fi

  if [ -n "$WD" ]; then
    ARGS="$ARGS wd=$WD"
  fi

  if [ -n "$SD" ]; then
    ARGS="$ARGS sd=$SD"
  fi

  if [ -n "$XFERSIZE" ]; then
    ARGS="$ARGS xfersize=$XFERSIZE"
  fi

  if [ -n "$RDPCT" ]; then
    ARGS="$ARGS rdpct=$RDPCT"
  fi

  if [ -n "$SEEKPCT" ]; then
    ARGS="$ARGS seekpct=$SEEKPCT"
  fi

if [ -n "$XFERSIZE" ]; then
    ARGS="$ARGS xfersize=$XFERSIZE"
  fi

  if [ -n "$RD" ]; then
    ARGS="$ARGS rd=$RD"
  fi

if [ -n "$WD" ]; then
    ARGS="$ARGS wd=$WD"
  fi

  if [ -n "$IORATE" ]; then
    ARGS="$ARGS iorate=$IORATE"
  fi

 if [ -n "$ELAPSED" ]; then
    ARGS="$ARGS elapsed=$ELAPSED"
  fi

  if [ -n "$INTERVAL" ]; then
    ARGS="$ARGS interval=$INTERVAL"
  fi

  if [ -n "$FORXFERSIZE" ]; then
    ARGS="$ARGS forxfersize=$FORXFERSIZE"
  fi

  if [ -n "$FORSEEKPCT" ]; then
    ARGS="$ARGS forseekpct=$FORSEEKPCT"
  fi

  if [ -n "$FORRDPCT" ]; then
    ARGS="$ARGS forrdpct=$FORRDPCT"
  fi

  VDBENCH_CMD="$VDBENCH_BIN $ARGS"

  if [ -n "$VDBENCH_CMD_PREFIX" ]; then
    VDBENCH_CMD="$VDBENCH_CMD_PREFIX $VDBENCH_CMD"
  fi

  if [ -n "$VDBENCH_CMD_POSTFIX" ]; then
    VDBENCH_CMD="$VDENCH_CMD $VDBENCH_CMD_POSTFIX"
  fi

  ssh::cmd "ulimit -n 100000"
  if [[ $? -ne 0 ]]; then
    cij::err "vdbench::run setting ulimit failed"
    return 1
  fi

  cij::emph "Running: $VDBENCH_CMD"
  ssh::cmd "$VDBENCH_CMD"
  if [[ $? -ne 0 ]]; then
    cij::err "vdbench::run vdbench returned with an error"
    return 1
  fi
}
