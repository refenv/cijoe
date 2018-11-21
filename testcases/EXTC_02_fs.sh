#!/bin/bash
#
# Example of using the SHELL package "fs"
#
# This example uses the "fs" package to run a quick test, stores output
# from 'fs' in CIJ_TEST_AUX_ROOT, and excluding the test of CPU hotplug
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
test::require fs
test::enter

FS_DEV_PATH=$BLOCK_DEV_PATH
FS_TYPE=ext4
FS_MOUNT_POINT=$(ssh::cmd_output "mktemp -d \"FSMP_XXXXXX\" -p /tmp")

if ! ssh::cmd "[[ -d \"$FS_MOUNT_POINT\" ]]"; then
  test::fail "could not create fs mount-point"
fi

if ! fs::create; then
  test::fail "failed creating '$FS_TYPE' on '$FS_DEV_PATH'"
fi

if ! fs::mount; then
  test::fail "failed mounting '$FS_TYPE' on '$FS_MOUNT_POINT'"
fi

if ! fs::umount; then
  test::fail "failed unmounting '$FS_TYPE' on '$FS_MOUNT_POINT'"
fi

test::pass
