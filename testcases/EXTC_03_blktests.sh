#!/bin/bash
#
# Example of using the SHELL package "blktests"
#
# This example uses the "blktests" package to run a quick test, stores output
# from 'blktests' in CIJ_TEST_AUX_ROOT, and excluding the test of CPU hotplug
# during IO
#
# Using packages often requires defining specific environment variables. The
# variables to define are documented within the package source, e.g.
# modules/blktests.sh
#
# Such variables should be declared within an "env" by doing so the cij_runner
# can run on different "targets" by simply giving it a different env. As such,
# the env is glue between a testcase and the environment that it runs in.
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::require block
test::require blktests
test::enter

if ! blktests::run "$CIJ_TEST_AUX_ROOT" "-q --exclude=block/008"; then
  test::fail
fi

test::pass
