#!/usr/bin/env bash
#
# Ensures exclusive execution of the runner via file-based locking
#
# The a file is used as a file-lock on a remote host When
#
# The enter-hook takes the lock or fails trying
#
# NOTE: this locking methodology will fail eventually but it should work for now
#
CIJ_TEST_NAME=$(basename $BASH_SOURCE)
source $CIJ_ROOT/modules/cijoe.sh
test::require ssh
test::enter

lock::enter
exit $?
