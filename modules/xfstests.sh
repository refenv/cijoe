#!/usr/bin/env bash
#
# xfstests::env         - Checks environment for FS variables
# xfstests::run         - Run a specific set of tests
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

function xfstests::env {
  ssh::env
  if [[ $? -ne 0 ]]; then
    cij::err "xfstests::env - Invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR definitions

  if [[ -z "$BLOCK_DEV_PATH" ]]; then
    cij::err "xfstests::env BLOCK_DEV_PATH is not defined"
    return 1
  fi

  if [[ -z "$MOUNT_POINT" ]]; then
    cij::err "xfstests::env MOUNT_POINT is not defined"
    return 1
  fi

  if [[ -z "$XFSTESTS_HOME" ]]; then
    cij::err "xfstests::env XFSTESTS_HOME is not defined"
    return 1
  fi

  XFSTESTS_TARGET_DEV_PATH="$BLOCK_DEV_PATH"
  XFSTESTS_TARGET_DIR="$MOUNT_POINT/xfs"

  if [[ -n "$XFSTESTS_SCRATCH_DEV_PATH" ]]; then
    XFSTESTS_SCRATCH_DIR="$MOUNT_POINT/xfs_scratch"
  fi

  if [[ -z "$XFSTESTS_FS_TYPE" ]]; then
    XFSTESTS_FS_TYPE="xfs"
  fi

  return 0
}

function xfstests::prepare {
  xfstests::env
  if [[ $? -ne 0 ]]; then
    cij::err "xsfstests::prepare - Invalid ENV."
    return 1
  fi

  FS_TYPE="$XFSTESTS_FS_TYPE"
  FS_DEV_PATH="$XFSTESTS_TARGET_DEV_PATH"
  FS_MOUNT_POINT="$XFSTESTS_TARGET_DIR"

  fs::create
  if [[ $? -ne 0 ]]; then
     cij::err "xfstests::prepare - Error creating file system"
     return 1
  fi

  fs::mount
  if [[ $? -ne 0 ]]; then
     cij:err "xfstests::prepare - Error mounting file system"
     return 1
  fi

  if [[ -n "$XFSTESTS_SCRATCH_DIR" ]]; then
    ssh::cmd "mkdir -p $XFSTESTS_SCRATCH_DIR"
    if [[ $? -ne 0 ]]; then
       cij:err "xfstests::prepare - failed to create scratch directory"
       return 1
    fi
  fi

  if [[ $? -ne 0 ]]; then
    cij::err "fs::mount: FAILED to create mount point"
    return 1
  fi

}

function xfstests::cleanup {
  xfstests::env
  if [[ $? -ne 0 ]]; then
    cij::err "xsfstests::run - Invalid ENV."
    return 1
  fi

  FS_TYPE="$XFSTESTS_FS_TYPE"
  FS_DEV_PATH="$XFSTESTS_TARGET_DEV_PATH"
  FS_MOUNT_POINT="$XFSTESTS_TARGET_DIR"

  fs::umount
  # We don't care if the unmount fails

  if [[ -n "$XFSTESTS_SCRATCH_DIR" ]]; then
    ssh::cmd "rmdir $XFSTESTS_SCRATCH_DIR"
    if [[ $? -ne 0 ]]; then
       cij:err "xfstests::cleanup - failed to remove scratch directory"
       return 1
    fi
  fi
}

function xfstests::run {
  xfstests::env
  if [[ $? -ne 0 ]]; then
    cij::err "xsfstests::run - Invalid ENV."
    return 1
  fi

  if [[ -z $1 ]]; then
    cij::err "xfstests::run - No tests specified"
    return 1
  fi
  
  TO_RUN=$1
  XFSTESTS_CMD="TEST_DEV=$XFSTESTS_TARGET_DEV_PATH TEST_DIR=$XFSTESTS_TARGET_DIR ./check $TO_RUN "

  if [ -n "$XFSTESTS_SCRATCH_DEV_PATH" ]; then
    XFSTESTS_CMD="SCRATCH_DEV=$XFSTESTS_SCRATCH_DEV_PATH $XFSTESTS_CMD"
  fi

  if [ -n "$XFSTESTS_SCRATCH_DIR" ]; then
    XFSTESTS_CMD="SCRATCH_MNT=$XFSTESTS_SCRATCH_DIR $XFSTESTS_CMD"
  fi
  
  cij::emph "Starting xfstests with specification: $TO_RUN TEST_DEV=$XFSTESTS_TARGET_DEV_PATH SCRATCH_DEV=$XFSTESTS_SCRATCH_DEV_PATH FSTYP=$XFSTESTS_FS_TYPE"
  ssh::cmd "cd $XFSTESTS_HOME && $XFSTESTS_CMD"
  if [[ $? -ne 0 ]]; then
    cij::err "xfstests::run Test failed"
    return 1
  fi

  return 0
}

