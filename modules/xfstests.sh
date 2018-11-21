#!/usr/bin/env bash
#
# xfstests::env         - Checks environment for FS variables
# xfstests::run         - Run a specific set of tests
# xfstests::prepare     - Mount fs etc.
# xfstests::cleanup     - Unmount fs etc.
#
# Variables REQUIRED by module
#
# BLOCK_DEV_PATH        - Path do block device to test
# FS_MOUNT_POINT        - Path to filesystem mount point
# XFSTESTS_HOME         - Path to xfstests installation
#
# Optional variables
#
# XSFSTESTS_SCRATCH_DEV_PATH    - Scratch device path
# XSFSTESTS_FS_TYPE             - file system type to test, default is xfs
#

xfstests::env() {
  if ! ssh::env; then
    cij::err "xfstests::env - Invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR definitions

  if [[ -z "$BLOCK_DEV_PATH" ]]; then
    cij::err "xfstests::env BLOCK_DEV_PATH is not defined"
    return 1
  fi
  if [[ -z "$FS_MOUNT_POINT" ]]; then
    cij::err "xfstests::env FS_MOUNT_POINT is not defined"
    return 1
  fi
  if [[ -z "$XFSTESTS_HOME" ]]; then
    cij::err "xfstests::env XFSTESTS_HOME is not defined"
    return 1
  fi

  XFSTESTS_TARGET_DEV_PATH="$BLOCK_DEV_PATH"
  XFSTESTS_TARGET_DIR="$FS_MOUNT_POINT"

  if [[ -n "$XFSTESTS_SCRATCH_DEV_PATH" ]]; then
    XFSTESTS_SCRATCH_DIR="$FS_MOUNT_POINT/xfs_scratch"
  fi
  if [[ -z "$XFSTESTS_FS_TYPE" ]]; then
    XFSTESTS_FS_TYPE="xfs"
  fi

  return 0
}

xfstests::prepare() {
  if ! xfstests::env; then
    cij::err "xsfstests::prepare - Invalid ENV."
    return 1
  fi

  FS_TYPE="$XFSTESTS_FS_TYPE"
  FS_DEV_PATH="$XFSTESTS_TARGET_DEV_PATH"
  FS_MOUNT_POINT="$XFSTESTS_TARGET_DIR"

  if ! fs::create; then
     cij::err "xfstests::prepare - Error creating file system"
     return 1
  fi

  if ! fs::mount; then
     cij:err "xfstests::prepare - Error mounting file system"
     return 1
  fi

  if [[ -n "$XFSTESTS_SCRATCH_DIR" ]]; then
    if ! ssh::cmd "mkdir -p $XFSTESTS_SCRATCH_DIR"; then
       cij:err "xfstests::prepare - failed to create scratch directory"
       return 1
    fi
  fi

  return 0
}

xfstests::cleanup() {
  if ! xfstests::env; then
    cij::err "xsfstests::run - Invalid ENV."
    return 1
  fi

  # shellcheck disable=SC2034
  FS_TYPE="$XFSTESTS_FS_TYPE"
  # shellcheck disable=SC2034
  FS_DEV_PATH="$XFSTESTS_TARGET_DEV_PATH"
  # shellcheck disable=SC2034
  FS_MOUNT_POINT="$XFSTESTS_TARGET_DIR"

  if ! fs::umount; then
    cij::err "xfstests::cleanup: fs::umount failed -- this is okay"
  fi

  if [[ -n "$XFSTESTS_SCRATCH_DIR" ]]; then
    if ! ssh::cmd "rmdir $XFSTESTS_SCRATCH_DIR"; then
       cij:err "xfstests::cleanup: failed to remove scratch directory"
       return 1
    fi
  fi
}

xfstests::run() {
  if ! xfstests::env; then
    cij::err "xsfstests::run - Invalid ENV."
    return 1
  fi

  XFSTESTS_TEST=$1
  if [[ -z "$XFSTESTS_TEST" ]]; then
    cij::err "xfstests::run - No tests specified"
    return 1
  fi

  XFSTESTS_CMD=""
  XFSTESTS_CMD="$XFSTESTS_CMD TEST_DEV=$XFSTESTS_TARGET_DEV_PATH"
  XFSTESTS_CMD="$XFSTESTS_CMD TEST_DIR=$XFSTESTS_TARGET_DIR"

  if [[ -n "$XFSTESTS_SCRATCH_DEV_PATH" ]]; then
    XFSTESTS_CMD=" $XFSTESTS_CMD SCRATCH_DEV=$XFSTESTS_SCRATCH_DEV_PATH"
  fi
  if [[ -n "$XFSTESTS_SCRATCH_DIR" ]]; then
    XFSTESTS_CMD="$XFSTESTS_CMD SCRATCH_MNT=$XFSTESTS_SCRATCH_DIR"
  fi

  XFSTESTS_CMD="$XFSTESTS_CMD ./check $XFSTESTS_TEST"

  if ! ssh::cmd "cd $XFSTESTS_HOME && $XFSTESTS_CMD"; then
    cij::err "xfstests::run Test failed"
    return 1
  fi

  return 0
}

