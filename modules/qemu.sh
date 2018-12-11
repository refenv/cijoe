#!/usr/bin/env bash
#
# qemu.sh - Script providing convenience functions for invoking qemu
#
# Functions:
#
# qemu::run                     - Run qemu
# qemu::kill                    - Send SIGTERM to qemu
# qemu::poweroff                - Send poweroff via qemu-monitor
# qemu::reset                   - Send reset via qemu-monitor
# qemu::env                     - Sets default vars for qemu wrapping
# qemu::console                 - Displays guest console monitor
# qemu::monitor                 - ?
# qemu::guest_nvme_create       - Create a block-device for LightNVM
#
# qemu::hostcmd                 - ?
# qemu::hostcmd_output          - ?
# qemu::host_push               - ?
# qemu::provision_kernel        - ?
# qemu::is_running              - ?
# qemu::guest_nvme_dev_del      - ?
# qemu::guest_nvme_exists       - ?
# qemu::guest_nvme_create       - ?
# qemu::guest_nvme_config       - ?
#
# Guest configuration and QEMU arguments are managed via variables. Define them
# as exported environment variables or make sure they are in scope.
#
# Variables:
#
# QEMU_BIN              - Path to qemu binary, no default, MUST be set.
# QEMU_GUESTS           - Path to qemu guests, default /tmp/guests.
# QEMU_ARGS_EXTRA       - Wildcard for options which aren't wrapped below.
#
# The "QEMU_GUESTS" is just a directory containing subdirectories,
# one subdirectory for each guests. Within each guest directory files such
# as "guest.pid", "console.out", "guest.monitor", "boot.img", "nvme00.img", and
# the like.
#
# QEMU_HOST             - Host hosting the guest
# QEMU_HOST_USER        - Host user
# QEMU_HOST_PORT        - Guest host ssh port
#
# QEMU_GUEST_NAME       - Default "default-guest"
# QEMU_GUEST_PATH       - Default "QEMU_GUESTS/QEMU_GUEST_NAME"
# QEMU_GUEST_BOOT_ISO   - Boot from provided ISO instead of IMG
# QEMU_GUEST_BOOT_IMG   - Default "QEMU_GUEST_PATH/boot.img"
# QEMU_GUEST_BOOT_IMG_FMT - Default "qcow2"
# QEMU_GUEST_CPU        - Adds "-cpu $QEMU_GUEST_CPU", DEFAULT: "host"
# QEMU_GUEST_MEM        - Adds "-m QEMU_GUEST_MEM", DEFAULT: "2G"
# QEMU_GUEST_SMP        - Adds "-smp $QEMU_GUEST_SMP", OPTIONAL, no DEFAULT
# QEMU_GUEST_KERNEL     - Adds "-kernel $QEMU_GUEST_KERNEL" and additional args
# QEMU_GUEST_SSH_FWD_PORT - Port to forward port 22 to host. Default: 2022
# QEMU_GUEST_CONSOLE    - Default: "file"
#
#   "stdio":  Console mapped to stdio
#   "file": Console output piped to file "QEMU_GUEST_PATH/console.out"
#   "foo":  The SDL interface pops up.
#
# The QEMU_NVME_* environment variables defines the Open-Channel SSD device to
# emulate. The drive will be backed by files storing data, metadata, various
# error-injection files, and monitor.
#
# QEMU_NVME_ID          - Name of drive to simulate
#                         Defaults to nvme0
# QEMU_NVME_MDTS        - Maximum data transfer size
#                       - DEFAULT: governed by qemu
# QEMU_NVME_MS          - Meta-data size
#                       - DEFAULT: governed by qemu
# QEMU_NVME_NLBAF       - Number of NVMe LBA formats
#                       - DEFAULT: governed by qemu
#
# QEMU_NVME_LINES       - Number of lines(chunks per PU)
#                         DEFAULT: 80
#
# QEMU_NVME_NUM_GRP     - Number of OCSSD groups on device
#                         DEFAULT: governed by qemu
# QEMU_NVME_NUM_PU      - Number of parallel units
#                         DEFAULT: governed by qemu
# QEMU_NVME_NUM_SEC     - Number of parallel units
#                         DEFAULT: govered by qemu
# QEMU_NVME_SEC_SIZE    - Number of bytes in a sector
#                         DEFAULT: governed by qemu
#
# QEMU_NVME_WS_MIN      - Minimum write size, in sectors
#                         DEFAULT: governed by qemu
# QEMU_NVME_WS_OPT      - Optimal write size
#                         DEFAULT: governed by qemu
# QEMU_NVME_MW_CUNITS   - Min write/read-distance
#                         DEFAULT: governed by qemu
# QEMU_NVME_CHUNKTABLE  - Chunk status table file
# QEMU_NVME_RESETFAIL   - Reset fail configuration file
# QEMU_NVME_WRITEFAIL   - Write fail configuration file

qemu::env() {
  if [[ -z "$QEMU_HOST" ]]; then
    cij::err "qemu::env: QEMU_HOST not set"
    return 1
  fi

  if [[ -z "$QEMU_HOST_USER" ]]; then
    cij::err "qemu::env: QEMU_HOST_USER not set"
    return 1
  fi

  if [[ -z "$QEMU_HOST_PORT" ]]; then
    QEMU_HOST_PORT=22
  fi

  if [[ -z "$QEMU_GUESTS" ]]; then
    cij::info "QEMU_GUESTS is unset using '/tmp/guests'"
    QEMU_GUESTS="/tmp/guests"
  fi

  if [[ -z "$QEMU_GUEST_NAME" ]]; then
    cij::info "QEMU_GUESTS is unset using 'default-guest'"
    QEMU_GUEST_NAME="default-guest"
  fi

  if [[ -z "$QEMU_GUEST_PATH" ]]; then
    QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"
  fi

  QEMU_GUEST_MONITOR="$QEMU_GUEST_PATH/guest.monitor"
  QEMU_GUEST_PIDFILE="$QEMU_GUEST_PATH/guest.pid"

  if [[ -z "$QEMU_GUEST_SSH_FWD_PORT" ]]; then
    QEMU_GUEST_SSH_FWD_PORT="2022"
  fi

  if [[ -z "$QEMU_GUEST_CPU" ]]; then
    QEMU_GUEST_CPU="host"
  fi

  if [[ -z "$QEMU_GUEST_MEM" ]]; then
    QEMU_GUEST_MEM="2G"
  fi

  if [[ -z "$QEMU_GUEST_BOOT_IMG_FMT" ]]; then
    QEMU_GUEST_BOOT_IMG_FMT="qcow2"
  fi

  if [[ -z "$QEMU_GUEST_BOOT_IMG" ]]; then
    QEMU_GUEST_BOOT_IMG="$QEMU_GUEST_PATH/boot.img"
  fi

  if [[ -z "$QEMU_GUEST_KERNEL" && -f "$QEMU_GUEST_PATH/bzImage" ]]; then
    QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
  fi

  if [[ -z "$QEMU_GUEST_CONSOLE" ]]; then
    QEMU_GUEST_CONSOLE="file"
  fi

  if [[ "$QEMU_GUEST_CONSOLE" = "file" ]]; then
    QEMU_GUEST_CONSOLE_FILE="$QEMU_GUEST_PATH/console.out"
  fi

  if [[ -z "$QEMU_GUEST_MEM" ]]; then
    QEMU_GUEST_MEM="2G"
  fi

  if [[ -z "$QEMU_NVME_ID" ]]; then
    QEMU_NVME_ID="cij_nvme"
  fi
  if [[ -z "$QEMU_NVME_LINES" ]]; then
    QEMU_NVME_LINES=80
  fi
  if [[ -z "$QEMU_NVME_NUM_PU" ]]; then
    QEMU_NVME_NUM_PU=4
  fi
  if [[ -z "$QEMU_NVME_SECS_PER_CHK" ]]; then
    QEMU_NVME_SECS_PER_CHK=3072
  fi
  if [[ -z "$QEMU_NVME_META_SZ" ]]; then
    QEMU_NVME_META_SZ=16
  fi
  if [[ -z "$QEMU_NVME_WS_MIN" ]]; then
    QEMU_NVME_WS_MIN=12
  fi
  if [[ -z "$QEMU_NVME_WS_OPT" ]]; then
    QEMU_NVME_WS_OPT=24
  fi
  if [[ -z "$QEMU_NVME_CUNITS" ]]; then
    QEMU_NVME_CUNITS=192
  fi

  if [[ -n "$QEMU_NVME_CHUNKTABLE" && ! -f "$QEMU_NVME_CHUNKTABLE" ]]; then
    cij::err "qemu::env: QEMU_NVME_CHUNKTABLE is set but file does not exist"
    return 1
  fi
  if [[ -n "$QEMU_NVME_RESETFAIL" && ! -f "$QEMU_NVME_RESETFAIL" ]]; then
    cij::err "qemu::env: QEMU_NVME_RESETFAIL is set but file does not exist"
    return 1
  fi
  if [[ -n "$QEMU_NVME_WRITEFAIL" && ! -f "$QEMU_NVME_WRITEFAIL" ]]; then
    cij::err "qemu::env: QEMU_NVME_WRITEFAIL is set but file does not exist"
    return 1
  fi

  QEMU_NVME_IMAGE="$QEMU_NVME_ID"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_l$QEMU_NVME_LINES"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_pu$QEMU_NVME_NUM_PU"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_sc$QEMU_NVME_SECS_PER_CHK"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_mz$QEMU_NVME_META_SZ"

  return 0
}

qemu::hostcmd() {
  if ! qemu::env; then
    cij::err "qemu::hostcmd failed"
    return 1
  fi

  SSH_USER=$QEMU_HOST_USER SSH_HOST=$QEMU_HOST SSH_PORT=$QEMU_HOST_PORT ssh::cmd "$1"
}

qemu::hostcmd_output() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  SSH_USER=$QEMU_HOST_USER SSH_HOST=$QEMU_HOST SSH_PORT=$QEMU_HOST_PORT ssh::cmd_output "$1"
}

qemu::host_push() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  if ! SSH_USER=$QEMU_HOST_USER SSH_HOST=$QEMU_HOST SSH_PORT=$QEMU_HOST_PORT ssh::push "$1" "$2"; then
    cij::err "qemu::host_push failed"
    return 1
  fi

  return 0
}

qemu::provision_kernel() {
  if ! qemu::env; then
    cij::err "qemu::provision_kernel failed"
    return 1
  fi


  LOCAL_KERNEL=$1
  if [[ -z "$LOCAL_KERNEL" ]]; then
    cij::info "Local kernel path not supplied. Defaulting to: arch/x86/boot/bzImage"
    LOCAL_KERNEL="arch/x86/boot/bzImage"
  fi

  if [[ -z "$QEMU_GUEST_KERNEL" ]]; then
    cij::err "qemu::provision_kernel: !QEMU_GUEST_KERNEL: '$QEMU_GUEST_KERNEL'"
    return 1
  fi

  if ! qemu::host_push "$LOCAL_KERNEL" "$QEMU_GUEST_KERNEL"; then
    cij::err "qemu:provision_kernel failed"
    return 1
  fi
}

qemu::kill() {
  if ! qemu::env; then
    cij::err "qemu::kill failed"
    return 1
  fi

  if ! PID=$(qemu::hostcmd_output "cat \"$QEMU_GUEST_PIDFILE\""); then
    cij::err "qemu::kill: failed to get qemu pid"
    return 1
  fi

  if ! qemu::hostcmd "kill $PID"; then
    cij::err "qemu::kill: failed to kill qemu guest"
    return 1
  fi

  return 0
}

# Returns 0 if qemu is running, 1 if it fails to determine status or not running
qemu::is_running() {
  if ! qemu::env; then
    cij::err "qemu::is_running failed"
    return 1
  fi

  if ! qemu::hostcmd "[[ -f \"$QEMU_GUEST_PIDFILE\" ]]"; then
    cij::info "qemu::is_running: no pidfile, assuming it is not running"
    return 0
  fi

  PID=""
  if ! PID=$(qemu::hostcmd_output "cat \"$QEMU_GUEST_PIDFILE\""); then
    cij::err "qemu::is_running: failed getting pid from '$QEMU_GUEST_PIDFILE'"
    return 1
  fi

  if [[ -z "$PID" ]]; then
    cij::info "qemu::is_running: no qemu/pid($PID), probably not running"
    return 0
  fi

  if qemu::hostcmd "ps -p \"$PID\" > /dev/null"; then
    cij::info "qemu::is_running: qemu/pid($PID) seems to be running"
    return 1
  else
    cij::info "qemu::is_running: qemu/pid($PID) does not seem to be running"
    return 0
  fi
}

qemu::poweroff() {
  if ! qemu::env; then
    cij::err "qemu::poweroff: env failed"
    return 1
  fi

  qemu::hostcmd "echo system_powerdown | socat - UNIX-CONNECT:$QEMU_GUEST_MONITOR"
  return $?
}

qemu::guest_nvme_dev_del() {
  if ! qemu::env; then
    cij::err "qemu::guest_nvme_dev_del: env failed"
    return 1
  fi

  qemu::hostcmd "echo device_del lnvm | socat - UNIX-CONNECT:$QEMU_GUEST_MONITOR"
  return $?
}

qemu::reset() {
  if ! qemu::env; then
    cij::err "qemu::reset: env failed"
    return 1
  fi

  qemu::hostcmd "echo system_reset | socat - UNIX-CONNECT:$QEMU_GUEST_MONITOR"
  return $?
}

qemu::monitor() {
  if ! qemu::env; then
    cij::err "qemu::monitor: failed"
    return 1
  fi

  qemu::hostcmd "socat - UNIX-CONNECT:$QEMU_GUEST_MONITOR"
  return $?
}

# watch the console monitor output
# interactive usage
qemu::console() {
  if ! qemu::env; then
    cij::err "qemu::console: failed"
    return 1
  fi

  qemu::hostcmd "tail -n 1000 -f $QEMU_GUEST_PATH/console.out"
  return $?
}

qemu::guest_nvme_exists() {
  if ! qemu::env; then
    cij::err "qemu::guest_nvme_exists: failed"
    return 1
  fi

  qemu::hostcmd "[[ -f "$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.img" ]]"
  return $?
}

qemu::guest_nvme_create() {
  if ! qemu::env; then
    cij::err "qemu::guest_nvme_create: failed"
    return 1
  fi

  DRIVE_IMG="$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.data"
  DRIVE_META="$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.meta"

  DD_BS=$(( QEMU_NVME_SECS_PER_CHK * 4))"k"
  DD_COUNT=$(( QEMU_NVME_NUM_PU * QEMU_NVME_LINES + 1))

  cij::info "Creating drive: bs($DD_BS) count($DD_COUNT)"
  if ! qemu::hostcmd "dd if=/dev/zero of=$DRIVE_IMG bs=$DD_BS count=$DD_COUNT"; then
    cij::err "qemu::guest_nvme_create: failed"
    return 1
  fi

  DD_BS=$(( QEMU_NVME_SECS_PER_CHK * QEMU_NVME_META_SZ ))
  DD_COUNT=$(( QEMU_NVME_NUM_PU * QEMU_NVME_LINES + 1))

  cij::info "Creating drive meta: bs($DD_BS) count($DD_COUNT)"
  if ! qemu::hostcmd "dd if=/dev/zero of=$DRIVE_META bs=$DD_BS count=$DD_COUNT"; then
    cij::err "qemu::guest_nvme_create: failed"
    return 1
  fi

  if ! qemu::hostcmd "sync"; then
    cij::err "qemu::guest_nvme_create: failed"
    return 1
  fi

  return 0
}

# Configure a virtual OCSSD 2.0 device
qemu::guest_nvme_config() {
  if ! qemu::env; then
    cij::err "qemu::env: failed"
    return 1
  fi

  GUEST_NVME_DRIVE="$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.data"
  GUEST_NVME_DRIVE_META="$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.meta"

  QEMU_ARGS_NVME=""
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME -drive file=\"$GUEST_NVME_DRIVE\",if=none,id=\"drive_$QEMU_NVME_ID\",format=raw"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME -device nvme,drive=\"drive_$QEMU_NVME_ID\",serial=deadbeef,id=\"$QEMU_NVME_ID\""
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,namespaces=1"

  if [[ ! -z "$QEMU_NVME_MDTS" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,mdts=$QEMU_NVME_MDTS"
  fi
  if [[ ! -z "$QEMU_NVME_NLBAF" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,nlbaf=$QEMU_NVME_NLBAF"
  fi
  if [[ ! -z "$QEMU_NVME_MS" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,ms=$QEMU_NVME_MS"
  fi

  if [[ ! -z "$QEMU_NVME_DEBUG" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,ldebug=$QEMU_NVME_DEBUG"
  fi
  if [[ ! -z "$QEMU_NVME_NUM_GRP" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lnum_grp=$QEMU_NVME_NUM_GRP"
  fi
  if [[ ! -z "$QEMU_NVME_NUM_PU" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lnum_pu=$QEMU_NVME_NUM_PU"
  fi
  if [[ ! -z "$QEMU_NVME_NUM_SEC" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lnum_sec=$QEMU_NVME_NUM_SEC"
  fi
  if [[ ! -z "$QEMU_NVME_SEC_SIZE" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lsec_size=$QEMU_NVME_SEC_SIZE"
  fi

  if [[ ! -z "$QEMU_NVME_WS_MIN" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lws_min=$QEMU_NVME_WS_MIN"
  fi
  if [[ ! -z "$QEMU_NVME_WS_OPT" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lws_opt=$QEMU_NVME_WS_OPT"
  fi
  if [[ ! -z "$QEMU_NVME_WS_CUNITS" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lmw_cunits=$QEMU_NVME_MW_CUNITS"
  fi

  if [[ ! -z "$QEMU_NVME_CHUNKTABLE" ]]; then
    QEMU_GUEST_CHUNKTABLE="$QEMU_GUEST_PATH/chunktable.qemu"
    qemu::hostcmd "[[ -f \"$QEMU_GUEST_CHUNKTABLE\" ]] && rm \"$QEMU_GUEST_CHUNKTABLE\""
    if ! qemu::host_push "$QEMU_NVME_CHUNKTABLE" "$QEMU_GUEST_PATH/chunktable.qemu"; then
      cij::err "qemu::config_guest_nvme failed"
      return 1
    fi
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lchunktable_txt=$QEMU_GUEST_CHUNKTABLE"
  fi

  if [[ ! -z "$QEMU_NVME_RESETFAIL" ]]; then
    QEMU_GUEST_RESETFAIL="$QEMU_GUEST_PATH/resetfail.qemu"
    qemu::hostcmd "rm $QEMU_GUEST_RESETFAIL"
    if ! qemu::host_push "$QEMU_NVME_RESETFAIL" "$QEMU_GUEST_RESETFAIL"; then
      cij::err "qemu::config_guest_nvme failed"
      return 1
    fi
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lresetfail=$QEMU_GUEST_RESETFAIL"
  fi

  return 0;
}

qemu::run() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  if ! qemu::is_running; then
    cij::err "qemu::run: looks like qemu is already running"
    return 1
  fi

  cij::info "Guests: " $QEMU_GUESTS " Name: " $QEMU_GUEST_NAME " Path: " $QEMU_GUEST_PATH
  if ! qemu::hostcmd "[[ -f $QEMU_GUEST_BOOT_IMG ]]"; then
    cij::err "Cannot find guest boot image($QEMU_GUEST_BOOT_IMG)"
    return 1
  fi

  if [[ ! -z "$QEMU_NVME_ID" ]]; then
    if ! qemu::guest_nvme_config; then
      cij:err "qemu::run: failed: guest_nvme_config"
      return 1
    fi
    if ! qemu::guest_nvme_exists; then
      if ! qemu::guest_nvme_create; then
        cij:err "qemu::run: failed: guest_nvme_create"
        return 1;
      fi
    fi
  fi

  # Setup arguments, `qemu::env` provides sensible defaults for the
  # non-optional arguments
  QEMU_ARGS="--enable-kvm"
  QEMU_ARGS="$QEMU_ARGS -cpu $QEMU_GUEST_CPU"
  if [[ -n "$QEMU_GUEST_SMP" ]]; then
    QEMU_ARGS="$QEMU_ARGS -smp $QEMU_GUEST_SMP"
  fi
  QEMU_ARGS="$QEMU_ARGS -m $QEMU_GUEST_MEM"
  # shellcheck disable=2153
  if [[ -n "$QEMU_GUEST_BOOT_ISO" ]]; then
    QEMU_ARGS="$QEMU_ARGS -boot d -cdrom $QEMU_GUEST_BOOT_ISO"
  fi
  QEMU_ARGS="$QEMU_ARGS -drive file=${QEMU_GUEST_BOOT_IMG},id=bootdrive,format=${QEMU_GUEST_BOOT_IMG_FMT},if=none"
  QEMU_ARGS="$QEMU_ARGS -device virtio-blk-pci,drive=bootdrive,scsi=off,config-wce=off"
  QEMU_ARGS="$QEMU_ARGS -monitor unix:$QEMU_GUEST_MONITOR,server,nowait"
  QEMU_ARGS="$QEMU_ARGS -pidfile $QEMU_GUEST_PIDFILE"

  if [[ -n "$QEMU_GUEST_KERNEL" ]]; then
    QEMU_ARGS="$QEMU_ARGS -kernel \"$QEMU_GUEST_KERNEL\""
    QEMU_ARGS="$QEMU_ARGS -append \"root=/dev/vda1 vga=0 console=ttyS0,kgdboc=ttyS1,115200 $QEMU_GUEST_APPEND\""
  fi

  if [[ "$QEMU_GUEST_CONSOLE" = "file" ]]; then
    QEMU_ARGS="$QEMU_ARGS -display none -serial file:$QEMU_GUEST_CONSOLE_FILE"
    QEMU_ARGS="$QEMU_ARGS -daemonize"
  elif [[ "$QEMU_GUEST_CONSOLE" = "stdio" ]]; then
    QEMU_ARGS="$QEMU_ARGS -nographic -serial mon:stdio"
  fi

  QEMU_ARGS="$QEMU_ARGS -net user,hostfwd=tcp::$QEMU_GUEST_SSH_FWD_PORT-:22 -net nic"
  QEMU_ARGS="$QEMU_ARGS $QEMU_ARGS_NVME $QEMU_ARGS_EXTRA"

  QEMU_CMD="$QEMU_BIN $QEMU_ARGS"

  cij::info "Starting QEMU with commandline: $QEMU_CMD"
  if ! qemu::hostcmd "$QEMU_CMD"; then
    cij::err "qemu::run Failed to start qemu"
    return 1
  fi

  return 0
}
