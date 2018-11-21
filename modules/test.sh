#!/usr/bin/env bash
#
# Test contract, the following environment variables must be set for tests to
# run properly.
#
#  * CIJ_TEST_RES_ROOT -- Must be a valid path to a directory to store test output
#
# Variables REQUIRED:
#
#  * SSH_HOST -- REQUIRED SSH hostname/IP of the machine running tests
#  * SSH_PORT -- REQUIRED port of the SSH machine
#  * SSH_USER -- REQURIED username of the SSH machine
#
# The test contract will then setup the following that must be used in the test
# script
#

test::usage() {
  cij::emph "Test contract -- Usage"

  echo ""
  echo "This should contain useful information on how to write and run a test"
  echo "but it does not, so read the docs instead"
  echo ""

  cij::info "CIJ_TEST_REQS: $CIJ_TEST_REQS"
}

test::require() {
  REQ=$1

  if [[ -z "$REQ" ]]; then
    test::exit 1 "test::require: invalid requirement '$REQ'"
  fi

  if [[ -z "$CIJ_TEST_REQS" ]]; then
    CIJ_TEST_REQS="$REQ"
  else
    CIJ_TEST_REQS="$CIJ_TEST_REQS $REQ"
  fi
}

test::enter() {
  if ! ssh::env; then
    test::usage
    test::fail "invalid SSH environment"
  fi

  for REQ in $CIJ_TEST_REQS; do
    if [[ "$REQ" == "nvme" ]]; then
      if ! nvme::env; then
        test::usage
        test::fail "Invalid NVMe environment"
      fi
      if ! nvme::exists; then
        test::usage
        test::fail "Invalid NVMe environment"
      fi
    elif [[ "$REQ" == "block" ]]; then
      if ! block::env; then
        test::usage
        test::fail "Invalid BLOCK environment"
      fi
      if ! block::exists; then
        test::usage
        test::fail "Invalid BLOCK environment"
      fi
    elif [[ "$REQ" == "fio" ]]; then
      if ! fio::env; then
        test::usage
        test::fail "Invalid FIO environment"
      fi
    fi
  done

  # Verify the test output directories exists
  if [[ -z "$CIJ_TEST_RES_ROOT" ]]; then
    test::usage
    test::fail "invalid directory CIJ_TEST_RES_ROOT: '$CIJ_TEST_RES_ROOT'"
    exit 1
  fi

  export CIJ_TEST_AUX_ROOT="$CIJ_TEST_RES_ROOT/_aux"
  if [[ ! -d "$CIJ_TEST_AUX_ROOT" ]]; then
    if ! mkdir "$CIJ_TEST_AUX_ROOT"; then
      test::fail "could not create CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
    fi
  fi

  # If the testcase is not set, one is created
  if [[ -z "$CIJ_TEST_ARB" ]]; then
    CIJ_TEST_ARB=$( rand_str )
  fi
  export CIJ_TEST_ARB

  if [[ -z "$CIJ_TEST_NAME" ]]; then
    test::fail "CIJ_TEST_NAME is not set"
  fi
  cij::emph "test::enter: CIJ_TEST_NAME: '$CIJ_TEST_NAME'"
  cij::emph "test::enter: CIJ_TEST_ARB: '$CIJ_TEST_ARB'"
  cij::emph "test::enter: CIJ_TEST_RES_ROOT: '$CIJ_TEST_RES_ROOT'"
  cij::emph "test::enter: CIJ_TEST_AUX_ROOT: '$CIJ_TEST_AUX_ROOT'"
}

test::exit() {
  RVAL=$1
  MSG=$2

  # Make sure the test-name does not carry over to the next test
  unset CIJ_TEST_NAME

  if [[ -z "$RVAL" ]]; then     # Incorrect usage => ERR
    cij::err "test::exit: FAILED: no return value, this is always failure!"
    exit 1
  fi

  if [[ -z "$MSG" ]]; then      # Default message when none is provided
    MSG="exiting with return value: '$RVAL'"
  fi

  if [[ $RVAL -eq 0 ]]; then    # Annotate the exit message
    cij::good "test::exit: $MSG"
  else
    cij::err "test::exit: $MSG"
  fi
  exit "$RVAL"                    # Exit
}

test::skip() {
  MSG=$1
  if [[ -z "$MSG" ]]; then
    MSG="SKIPPED"
  else
    MSG="SKIPPED: $MSG"
  fi

  test::exit 2 "$MSG"
}

test::fail() {
  MSG=$1
  if [[ -z "$MSG" ]]; then
    MSG="FAILED"
  else
    MSG="FAILED: $MSG"
  fi

  test::exit 1 "$MSG"
}

test::pass() {
  MSG=$1
  if [[ -z "$MSG" ]]; then
    MSG="PASSED"
  else
    MSG="PASSED: $MSG"
  fi

  test::exit 0 "$MSG"
}

test::info() {
  cij::emph "test::info: $1"
}

