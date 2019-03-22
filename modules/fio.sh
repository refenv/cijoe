#!/usr/bin/env bash
#
# fio.sh - Wrapper for the Flexible I/O tester
#
# Functions:
#
# fio::env              - Setup basic variables
# fio::run              - Translate ENV. VARS. into FIO_ARGS and run fio
#
#
## Variables EXPORTED by module:
#
# FIO_BIN               - Absolute PATH to fio binary (DEFAULT - see code)
# FIO_SSH               - Whether or not to use SSH as tranport (DEFAULT 1)
#                         1: Run remotely, 0: Run locally
#
## Variables REQUIRED by fio::run:
#
# FIO_FILENAME          - Absolute path to block device
#
## Variables OPTIONAL by fio::run
#
# FIO_READWRITE
# FIO_BLOCKSIZE
# FIO_NAME
# FIO_IODEPTH
# FIO_RUNTIME
# FIO_SIZE
# FIO_OFFSET
# FIO_DO_VERIFY
# FIO_VERIFY
# FIO_VERIFY_FATAL
# FIO_VERIFY_INTERVAL
# FIO_VERIFY_PATTERN
# FIO_VERIFY_BACKLOG
# FIO_NUMJOBS
# FIO_IOENGINE

# FIO_DIRECT
# FIO_RWMIXREAD
# FIO_OUTPUT
# FIO_FSYNC
#
# FIO_ARGS_EXTRA        - Use for fio ARGS not covered above
#
# FIO_DOLOGS            - 1: Do a bunch of magic
#
# Variables EXPORTED by fio::run:
#
# FIO_ARGS              - Complete set of arguments for fio command
#

fio::env() {
  # DEFAULT variables
  FIO_BIN=${FIO_BIN:-/usr/local/bin/fio}
  FIO_SSH=${FIO_SSH:-1}

  # MAGIC VAR
  if [[ $FIO_DOLOGS -eq 1 ]]; then
    if [[ -z "$FIO_DOLOGS_ROOT" ]]; then
      FIO_DOLOGS_ROOT=/tmp/FIOLOGS_$(rand_str)_
    fi
    FIO_LOG_AVG_MSEC=1000
    FIO_WRITE_BW_LOG=$FIO_DOLOGS_ROOT
    FIO_WRITE_LAT_LOG=$FIO_DOLOGS_ROOT
    FIO_WRITE_IOPS_LOG=$FIO_DOLOGS_ROOT
    #FIO_WRITE_HIST_LOG=$FIO_DOLOGS_ROOT
  fi

  return 0
}

fio::run() {
  if ! fio::env; then
    cij::err "fio::env failed"
    return 1
  fi

  # REQUIRED variables
  if [[ -z "$FIO_FILENAME" ]]; then
    cij::err "fio::run: FIO_FILENAME is not set"
    return 1
  fi

  FIO_ARGS=""

  FIO_ARGS="$FIO_ARGS --filename=$FIO_FILENAME"

  if [[ -n "$FIO_LOG_AVG_MSEC" ]]; then
    FIO_ARGS="$FIO_ARGS --log_avg_msec=${FIO_LOG_AVG_MSEC}"
  fi
  if [[ -n "$FIO_WRITE_BW_LOG" ]]; then
    FIO_ARGS="$FIO_ARGS --write_bw_log=${FIO_WRITE_BW_LOG}"
  fi
  if [[ -n "$FIO_WRITE_LAT_LOG" ]]; then
    FIO_ARGS="$FIO_ARGS --write_lat_log=${FIO_WRITE_LAT_LOG}"
  fi
  if [[ -n "$FIO_WRITE_IOPS_LOG" ]]; then
    FIO_ARGS="$FIO_ARGS --write_iops_log=${FIO_WRITE_IOPS_LOG}"
  fi
  #if [[ -n "$FIO_WRITE_HIST_LOG" ]]; then
  #  FIO_ARGS="$FIO_ARGS --write_hist_log=${FIO_WRITE_HIST_LOG}"
  #fi

  if [[ -n "$FIO_READWRITE" ]]; then
    FIO_ARGS="$FIO_ARGS --readwrite=$FIO_READWRITE"
  fi
  if [[ -n "$FIO_BLOCKSIZE" ]]; then
    FIO_ARGS="$FIO_ARGS --blocksize=$FIO_BLOCKSIZE"
  fi
  if [[ -n "$FIO_BLOCKSIZE_RANGE" ]]; then
    FIO_ARGS="$FIO_ARGS --blocksize_range=$FIO_BLOCKSIZE_RANGE"
  fi
  if [[ -n "$FIO_IODEPTH" ]]; then
    FIO_ARGS="$FIO_ARGS --iodepth=$FIO_IODEPTH"
  fi
  if [[ -n "$FIO_NAME" ]]; then
    FIO_ARGS="$FIO_ARGS --name=$FIO_NAME"
  fi
  if [[ -n "$FIO_RAMP_TIME" ]]; then
    FIO_ARGS="$FIO_ARGS --ramp_time=$FIO_RAMP_TIME"
  fi
  if [[ -n "$FIO_RUNTIME" ]]; then
    FIO_ARGS="$FIO_ARGS --time_based --runtime=$FIO_RUNTIME"
  fi
  if [[ -n "$FIO_SIZE" ]]; then
    FIO_ARGS="$FIO_ARGS --size=$FIO_SIZE"
  fi
  if [[ -n "$FIO_OFFSET" ]]; then
    FIO_ARGS="$FIO_ARGS --offset=$FIO_OFFSET"
  fi
  if [[ -n "$FIO_NUMJOBS" ]]; then
    FIO_ARGS="$FIO_ARGS --numjobs=$FIO_NUMJOBS"
  fi
  if [[ -n "$FIO_DO_VERIFY" ]]; then
    FIO_ARGS="$FIO_ARGS --do_verify=$FIO_DO_VERIFY"
  fi
  if [[ -n "$FIO_VERIFY" ]]; then
    FIO_ARGS="$FIO_ARGS --verify=$FIO_VERIFY"
  fi
  if [[ -n "$FIO_VERIFY_FATAL" ]]; then
    FIO_ARGS="$FIO_ARGS --verify_fatal=$FIO_VERIFY_FATAL"
  fi
  if [[ -n "$FIO_VERIFY_INTERVAL" ]]; then
    FIO_ARGS="$FIO_ARGS --verify_interval=$FIO_VERIFY_INTERVAL"
  fi
  if [[ -n "$FIO_VERIFY_PATTERN" ]]; then
    FIO_ARGS="$FIO_ARGS --verify_pattern=$FIO_VERIFY_PATTERN"
  fi
  if [[ -n "$FIO_VERIFY_BACKLOG" ]]; then
    FIO_ARGS="$FIO_ARGS --verify_backlog=$FIO_VERIFY_BACKLOG"
  fi
  if [[ -n "$FIO_DIRECT" ]]; then
    FIO_ARGS="$FIO_ARGS --direct=$FIO_DIRECT"
  fi
  if [[ -n "$FIO_IOENGINE" ]]; then
    FIO_ARGS="$FIO_ARGS --ioengine=$FIO_IOENGINE"
  fi
  if [[ -n "$FIO_RWMIXREAD" ]]; then
    FIO_ARGS="$FIO_ARGS --rwmixread=$FIO_RWMIXREAD"
  fi
  if [[ -n "$FIO_OUTPUT" ]]; then
    FIO_ARGS="$FIO_ARGS --output=$FIO_OUTPUT"
  fi
  if [[ -n "$FIO_FSYNC" ]]; then
    FIO_ARGS="$FIO_ARGS --fsync=$FIO_SYNC"
  fi
  if [[ -n "$FIO_END_FSYNC" ]]; then
    FIO_ARGS="$FIO_ARGS --end_fsync=$FIO_END_FSYNC"
  fi
  if [[ -n "$FIO_ARGS_EXTRA" ]]; then
    FIO_ARGS="$FIO_ARGS $FIO_ARGS_EXTRA"
  fi

  if [[ $FIO_SSH -eq 1 ]]; then
    ssh::cmd "$FIO_BIN $FIO_ARGS"
    return $?
  fi

  eval "$FIO_BIN $FIO_ARGS"
  return $?
}

fio::run_jobfile() {
  FIO_JOBFILE=$1
  if [[ -z "$FIO_JOBFILE" ]]; then
    cij::err "fio::run_jobfile: No jobfile provided"
    return 1
  fi

  if [[ ! -f "$FIO_JOBFILE" ]]; then
    cij::err "fio::run_jobfile: Invalid FIO_JOBFILE: $FIO_JOBFILE"
    return 1
  fi

  if ! fio::env; then
    cij::err "fio::env failed"
    return 1
  fi

  SHOWCMD=$($FIO_BIN --showcmd "$FIO_JOBFILE")    # Grab arguments from file
  SHOWCMD=${SHOWCMD#*fio}                       # Remove "fio" from cmd-string

  FIO_ADRGS_EXTRA_BU="$FIO_ARGS_EXTRA"

  FIO_ARGS_EXTRA="$FIO_ARGS_EXTRA $SHOWCMD"

  FIO_JOBFILE_NAME=$(basename "$FIO_JOBFILE")
  cij::emph "FIO_JOBFILE_NAME: '$FIO_JOBFILE_NAME'"

  fio::run
  RCODE="$?"

  FIO_ARGS_EXTRA="$FIO_ADRGS_EXTRA_BU"

  return $RCODE
}

