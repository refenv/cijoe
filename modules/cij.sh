#!/usr/bin/env bash
#
# cij.sh - Miscellaneous helper functions
#
# cij::info   - Prints an information message to stdout
# cij::good   - Prints an 'good'/'success' message to stdout
# cij::warn   - Print a warning message to stdout
# cij::err    - Prints an error message to stderr
# cij::emph   - Prints an emphasized message to stdout
#
# cij::throttle - Equivalent of `sleep` except it emits "." each second
#
# cij::watchf           - Tails a path indefinitely
# cij::watchf_for       - Tails a file until it contains a "$1"
#
# cij::repeat   - Repeat the given command the given number of times
#
# cij::isint    - Determine whether given input is an integer
#

#
# Uncomment below for strict-mode, note, this is not yet possible since CIJOE
# was originally not implemented using the 'unofficial strict-mode'
#
#set -euo pipefail

: "${CIJ_COLORIZE:=1}"
if [[ $CIJ_COLORIZE -eq 0 ]]; then
  PR_EMPH_CC=''
  PR_GOOD_CC=''
  PR_WARN_CC=''
  PR_ERR_CC=''
  PR_NC=''
else
  PR_EMPH_CC='\033[0;36m'
  PR_GOOD_CC='\033[0;32m'
  PR_WARN_CC='\033[0;33m'
  PR_ERR_CC='\033[0;31m'
  PR_NC='\033[0m'
fi

: "${CIJ_ECHO_TIME_STAMP:=1}"
export CIJ_ECHO_TIME_STAMP

: "${CIJ_EMPH_DEFAULT:=}"
export CIJ_EMPH_DEFAULT

cij::info() {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_EMPH_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_EMPH_CC}# $1${PR_NC}"
  fi
}

cij::good() {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_GOOD_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_GOOD_CC}# $1${PR_NC}"
  fi
}

cij::warn() {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_WARN_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_WARN_CC}# $1${PR_NC}"
  fi
}

cij::err() {
  if [[ $CIJ_ECHO_TIME_STAMP -eq 1 ]]; then
    echo -e "${PR_ERR_CC}# [$(/bin/date '+%F %T')] $1${PR_NC}"
  else
    echo -e "${PR_ERR_CC}# $1${PR_NC}"
  fi
}

cij::emph() {
  if [[ -z ${2+x} ]]; then
    cij::info "$1"
  elif [[ $2 -eq 0 ]]; then
    cij::good "$1"
  else
    cij::err "$1"
  fi
}

cij::throttle() {
  local remaining="$1"

  if [[ "$remaining" -gt 0 ]]; then
    echo -n "Throttling($remaining)"
    while [[ "$remaining" -gt 0 ]]; do
      echo -n "."
      sleep 1
      remaining=$(( "$remaining" - 1))
    done
    echo "!"
  fi
}

cij::watchf() {
  if [[ -z ${1+x} ]]; then
    cij::err "cij::watchf: missing first argument"
    return 0
  fi

  local watchf_file="$1"

  if [[ -z "$watchf_file" || ! -f "$watchf_file" ]]; then
    cij::err "cij::watchf: Invalid file."
    return 0
  fi

  tail -f --follow=name --retry "$watchf_file"
}

#
# Watch a file until a message appear or timing out
#
# cij::watchf_for /tmp/jazz "foo" 10
#
cij::watchf_for() {
  local watchf_file=$1
  local watchf_msg=$2
  local watchf_timeout=$3
  local watchf_elapsed=0
  local nlines

  if [[ -z "$watchf_file" || ! -f "$watchf_file" ]]; then
    cij::err "cij::watchf_for: Invalid file: '$watchf_file'"
    return 0
  fi
  if [[ -z "$watchf_msg" ]]; then
    cij::err "cij::watchf_for: No message provided"
    return 0
  fi
  : "${watchf_timeout:=60}"

  sync
  nlines=$(wc -l < "$watchf_file") # Watch for "additions" to file

  echo -n "Watching($watchf_file) for($watchf_msg) timeout($watchf_timeout)"
  while [[ "$watchf_elapsed" -lt "$watchf_timeout" ]]; do
    echo -n "."
    if tail -n+"$nlines" "$watchf_file" | grep -q "$watchf_msg" ; then
      echo ""
      return 1
    fi
    sleep 1
    watchf_elapsed=$(( "$watchf_elapsed" + 1 ))
  done

  echo ""
  cij::err "cij::watchf_for: timeout($watchf_timeout) exceeded."
  return 0
}

# Repeat the given command the given number of times, e.g.:
#
# cij::repeat 10 echo "Hello There"
#
cij::repeat() {
  if [[ -z ${1+x} ]]; then
    cij::err "cij::repeat: missing first argument"
    return 0
  fi

  if [[ -z ${2+x} ]]; then
    cij::err "cij::repeat: missing command argument"
    return 0
  fi

  local number="$1"
  shift

  for _ in $(seq "$number"); do
    "$@"
  done
}

# Determine whether given input is an integer
#
# returncode 0 when input is an integer, 1 when it is not
cij::isint() {
  if [[ -z ${1+x} ]]; then
    cij::err "no input given"
    return 0
  fi

  [[ "$1" =~ ^[0-9]+$ ]]
  return $?
}

#
# Transform files from cijoe-local storage to target
#
cij::push() {
  local _src=$1
  local _dst=$2

  if [[ ! -v _src ]]; then
    cij::err "cij.push: missing first argument (src)"
    return 1
  fi
  if [[ ! -v _dst ]]; then
    cij::err "cij.push: missing second argument (dst)"
    return 1
  fi

  if [[ -v CIJ_TARGET_TRANSPORT && "${CIJ_TARGET_TRANSPORT}" == "ssh" ]] || [[ -v SSH_HOST ]]; then
    ssh::push "${_src}" "${_dst}"
    return $?
  else
    cp -r "${_src}" "${_dst}"
    return $?
  fi
}

#
# Transform files from target to cijoe-local storage
#
cij::pull() {
  local _src=$1
  local _dst=$2

  if [[ ! -v _src ]]; then
    cij::err "cij.pull: missing first argument (src)"
    return 1
  fi
  if [[ ! -v _dst ]]; then
    cij::err "cij.pull: missing second argument (dst)"
    return 1
  fi

  if [[ -v CIJ_TARGET_TRANSPORT && "${CIJ_TARGET_TRANSPORT}" == "ssh" ]] || [[ -v SSH_HOST ]]; then
    ssh::pull "${_src}" "${_dst}"
    return $?
  else
    cp -r "${_src}" "${_dst}"
    return $?
  fi
}

cij::cmd() {
  if [[ -v CIJ_TARGET_TRANSPORT && "${CIJ_TARGET_TRANSPORT}" == "ssh" ]] || [[ -v SSH_HOST ]]; then
    ssh::cmd "$@"
    return $?
  else
    "$@"
    return $?
  fi
}
