#!/usr/bin/env bash
#
# Ensures exclusive execution of the runner via file-based locking
#
# The exit-hook releases the file-lock
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

lock::exit
exit $?
