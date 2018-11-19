#!/usr/bin/env bash
#
# utils.sh - Miscelanous helper functions
#
# cij::info   - Prints an information message to stdout
# cij::emph   - Prints an emphasized message to stdout
# cij::warn   - Print a warning message to stdout
# cij::err    - Prints an error message to stderr
#
# cij::throttle  - Equivalent of `sleep` except it emits "." each second
#
# cij::watchf    - Tails a path indefinately
# cij::watchf_for  - Tails a file until it contains a "$1"
#

PR_EMPH_CC='\033[0;36m'
PR_GOOD_CC='\033[0;32m'
PR_WARN_CC='\033[0;33m'
PR_ERR_CC='\033[0;31m'
PR_NC='\033[0m'

if [[ -z "$CIJ_ECHO_TIME_STAMP" ]]; then
  CIJ_ECHO_TIME_STAMP=1
fi

function cij::info {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_EMPH_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_EMPH_CC}# $1${PR_NC}"
  fi
}

function cij::good {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_GOOD_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_GOOD_CC}# $1${PR_NC}"
  fi
}

function cij::warn {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_WARN_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_WARN_CC}# $1${PR_NC}"
  fi
}

function cij::err {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_ERR_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_ERR_CC}# $1${PR_NC}"
  fi
}

function cij::emph {
  if [[ -z "$2" ]]; then
    cij::info "$1"
  elif [[ $2 -eq 0 ]]; then
    cij::good "$1"
  else
    cij::err "$1"
  fi
}

function cij::throttle {
  REMAINING=$1
  if [ $REMAINING -gt 0 ]; then
    echo -n "Throttling($REMAINING)"
    while [ $REMAINING -gt 0 ]; do
      echo -n "."
      sleep 1
      REMAINING=`expr $REMAINING - 1`
    done
    echo "!"
  fi
}

function cij::watchf {
  WATCHF_FILE=$1

  if [ -z "$WATCHF_FILE" -o ! -f "$WATCHF_FILE" ]; then
    cij::err "cij::watchf: Invalid file."
    return 0
  fi

  tail -f --follow=name --retry $WATCHF_FILE
}

function cij::watchf_for {
  WATCHF_FILE=$1
  WATCHF_MSG=$2
  WATCHF_TIMEOUT=$3

  WATCHF_ELAPSED=0

  if [ -z "$WATCHF_FILE" -o ! -f "$WATCHF_FILE" ]; then
    cij::err "cij::watchf_for: Invalid file"
    return 0
  fi

  if [ -z "$WATCHF_MSG" ]; then
    cij::err "cij::watchf_for: No message provided"
    return 0
  fi

  if [ -z "$WATCHF_TIMEOUT" ]; then
    WATCHF_TIMEOUT=60
  fi

  sync
  NLINES=`wc -l < $WATCHF_FILE` # Watch for "additions" to file

  echo -n "Watching($WATCHF_FILE) for($WATCHF_MSG) timeout($WATCHF_TIMEOUT)"
  while [ "$WATCHF_ELAPSED" -lt "$WATCHF_TIMEOUT" ]; do
    echo -n "."
    if tail -n+$NLINES $WATCHF_FILE | grep -q "$WATCHF_MSG" ; then
      echo ""
      return 1
    fi
    sleep 1
    WATCHF_ELAPSED=`expr $WATCHF_ELAPSED + 1`
  done

  cij::err "cij::watchf_for: timeout($WATCHF_TIMEOUT) exceeded."
  return 0
}

function cij::repeat {
  number=$1
  shift
  for i in `seq $number`; do
    $@
  done
}

# get fibonacci-range, between(and including) <start> and <stop>
function get_fib_range {
  start_val=$1
  stop_val=$2
  unset range
  if [ "$start_val" ==  "$stop_val" ];
  then
    range[0]=$start_val
  else
    a=1
    b=1
    c=2
    let "n = $a + $start_val"
    range[0]=$start_val
    index=1
    while [ "$n" -lt "$stop_val" ]; do
      range[$index]=$b
      a=$b
      b=$c
      let "c = $a + $b"
      let "n = $b + $start_val"
      let "index = $index + 1"
    done
    range[$index]=$stop_val
  fi
}

# get power-of-two-range, between(and including) <start> and <stop> 
function get_exp_2_range {
  start_val=$1
  stop_val=$2
  unset range
  if [ "$start_val" ==  "$stop_val" ];
  then
    range[0]=$start_val
  else
    a=1
    let "n = $a + $start_val"
    range[0]=$start_val
    index=1
    while [ "$n" -lt "$stop_val" ]; do
      range[$index]=$n
      let "a = $a * 2"
      let "n = $a + $start_val"
      let "index = $index + 1"
    done
    range[$index]=$stop_val
  fi
}

function cij::isint {
  VAR=$1

  if [[ -z "$VAR" ]]; then
    cij::err "no input givent"
    return 0
  fi

  [[ $VAR =~ ^[0-9]+$ ]];
  return $?
}
