#!/bin/bash
#
# Example of using the SHELL package "xfstests"
#
# One can either write a testcase with logic defining the tests within the
# script, or use the script to call another testcase e.g. as a wrapper for other
# tools, and utilities.
#
# This is an example of the latter, a wrapper for "xfstests", running the
# "generic/001" testcase as defined in "xfstests".
#
# This example uses the "xfstests" package to run a quick test, stores output
# from "xfstests" in CIJ_TEST_AUX_ROOT, and excluding the test of CPU hotplug
# during IO
#
# Using packages often requires defining specific environment variables. The
# variables to define are documented within the package source, e.g.
# modules/fs.sh
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
test::require xfstests
test::enter

# Create and define a mount-point
if ! FS_MOUNT_POINT=$(ssh::cmd_output "mktemp -d \"XFSMP_XXXXXX\" -p /tmp"); then
  test::fail
fi

export FS_MOUNT_POINT

if ! xfstests::prepare; then
  test::fail
fi

if ! xfstests::run "generic/001"; then
  xfstests::cleanup

  test::fail
fi

if ! xfstests::cleanup; then
  test::fail
fi

test::pass
