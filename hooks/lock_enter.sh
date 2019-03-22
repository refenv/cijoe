#!/usr/bin/env bash
#
# Ensures exclusive execution of the runner via file-based locking
#
# on-enter: take lock via module function lock::enter
# on-exit: release lock via module function lock::exit
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require ssh
test::enter

lock::enter
exit $?
