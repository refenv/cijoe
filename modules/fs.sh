#!/usr/bin/env bash
#
# fs::env     - Checks environment for FS variables
# fs::create  - Creates a filesystem
# fs::mount   - Mounts a file system
# fs::umount  - Unmounts a file system
#
# Variables REQUIRED by module
#
# FS_DEV_PATH           - Path do block device
# FS_TYPE               - Type of filesystem to create
# FS_MOUNT_POINT        - Path to filesystem mount point
#

fs::env() {
  if ! ssh::env; then
    cij::err "fs::env: invalid SSH environment"
    return 1
  fi

  # REQUIRED variables
  if [[ -z "$FS_DEV_PATH" ]]; then
    cij::err "fs::env: FS_DEV_PATH is not defined"
    return 1
  fi

  if [[ -z "$FS_TYPE" ]]; then
    cij::err "fs::env: FS_TYPE is not defined"
    return 1
  fi
  if [[ -z "$FS_MOUNT_POINT" ]]; then
    cij::err "fs::env: FS_MOUNT_POINT is not defined"
    return 1
  fi

  return 0
}

fs::create() {
  if ! fs::env; then
    cij::err "fs::create: - Invalid ENV."
    return 1
  fi

  if ! ssh::cmd "wipefs --all $FS_DEV_PATH"; then
    cij::err "fs::create: FAILED to create file system"
    return 1
  fi

  if ! ssh::cmd "mkfs.$FS_TYPE $BLOCK_DEV_PATH"; then
    cij::err "fs::create: FAILED to create file system"
    return 1
  fi

  return 0
}

fs::mount() {
  if ! fs::env; then
    cij::err "fs::mount - Invalid ENV."
    return 1
  fi

  if ! ssh::cmd "mkdir -p $FS_MOUNT_POINT"; then
    cij::err "fs::mount: FAILED to create mount point"
    return 1
  fi

  if ! ssh::cmd "mount $BLOCK_DEV_PATH $FS_MOUNT_POINT"; then
    cij::err "fs::mount: FAILED to mount file system"
    return 1
  fi

  return 0
}

fs::umount() {
  if ! fs::env; then
    cij::err "fs::umount: - Invalid ENV."
    return 1
  fi

  if ! ssh::cmd "umount $FS_MOUNT_POINT"; then
    cij::err "fs::umount: FAILED to unmount file system"
    return 1
  fi

  if ! ssh::cmd "rmdir $FS_MOUNT_POINT"; then
    cij::err "fs::umount: FAILED to remove mount point"
    return 1
  fi

  return 0
}

