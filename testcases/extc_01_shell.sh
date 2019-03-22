#!/bin/bash
#
# Example of a testcase implemented as a SHELL script
#
# The test implementation itself just verifies whether it can execute a command
# without error, it is just a demonstration on how commands should be invoked
# and how test-status must be communicated
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

# Everything above is mandatory, that is, you MUST:
#
# * Provide a short and long description of the testcase
# * Provide a CIJ_TEST_NAME
# * source in CIJOE
# * Begin the test with "test::enter"
#
# The remainder is the implementation of the test itself. Notice that commands
# are prefixed with 'ssh::cmd' such that they can run on localhost or remotely
# by changing the environment and thereby point it to a different target
#
# Test status is indicated with 'test::fail' or 'test::pass'

cij::info "Example of outputting an annotated 'information' message"
cij::good "Example of outputting an annotated 'good' message"
cij::warn "Example of outputting an annotated 'warning' message"
cij::err "Example of outputting an annotated 'error' message"

if [[ -n "$FOO" ]]; then
  cij::emph "Looks like the variable FOO is set, have a look FOO: '$FOO'"
fi

cij::info "Let us test that we can execute 'lspci'"

if ! ssh::cmd "lspci"; then
  test::fail "failed executing 'lspci'"
fi

test::pass
