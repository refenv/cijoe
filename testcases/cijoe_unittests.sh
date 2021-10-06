#!/usr/bin/env bash
#
# Run the CIJOE unittests
#
# This runs CIJOE unittest of cijoe itself via module execution, e.g. running the unittests
# packages with CIJOE.
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test.enter

# shellcheck disable=SC2086
if ! python3 -m cij.unittests; then
  test.fail
fi

test.pass
