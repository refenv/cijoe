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
# qemu::is_wait                 - Wait for QEMU to stop running
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
# QEMU_IMG_BIN          - Path to qemu-img binary, no default, MUST be set.
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
# QEMU_GUEST_APPEND     - Adds extra kernel parameters for -append
# QEMU_GUEST_SSH_FWD_PORT - Port to forward port 22 to host. Default: 2022
# QEMU_GUEST_CONSOLE    - Default: "file"
#
#   "stdio":  Console mapped to stdio
#   "file": Console output piped to file "QEMU_GUEST_PATH/console.out"
#   "foo":  The SDL interface pops up.
#
# The QEMU_NVME_* environment variables defines the Open-Channel SSD device to
# emulate. The drive will be backed by files storing data, various
# error-injection files, and monitor.
#
# QEMU_NVME_ID          - Name of drive to simulate
#                         Defaults to nvme0
# QEMU_NVME_IMAGE_FPATH - Absolute path to the NVMe drive image
# QEMU_NVME_MDTS        - Maximum Data Transfer Size. In units of the minimum
#                         memory page size. Specified as 2**n.
#                         DEFAULT: 7
# QEMU_NVME_NUM_GRP     - Number of groups
#                         DEFAULT: 2
# QEMU_NVME_NUM_PU      - Number of parallel units per group
#                         DEFAULT: 4
# QEMU_NVME_NUM_CHK     - Number of chunks per parallel unit
#                         DEFAULT: 60
# QEMU_NVME_NUM_SEC     - Number of sectors per chunk
#                         DEFAULT: 4096
# QEMU_NVME_LBADS       - LBA data size (LBADS)
#                         DEFAULT: 4096
# QEMU_NVME_MS          - Meta-data size (MS)
#                       - DEFAULT: 16
# QEMU_NVME_WS_MIN      - Minimum write size, in sectors
#                         DEFAULT: 4
# QEMU_NVME_WS_OPT      - Optimal write size
#                         DEFAULT: 8
# QEMU_NVME_MW_CUNITS   - Cache minimum write size units
#                         DEFAULT: 24
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

  # set host defaults
  : "${QEMU_HOST_PORT:=22}"

  if [[ -z "$QEMU_GUESTS" ]]; then
    cij::info "QEMU_GUESTS is unset using '/tmp/guests'"
    QEMU_GUESTS="/tmp/guests"
  fi

  if [[ -z "$QEMU_GUEST_NAME" ]]; then
    cij::info "QEMU_GUESTS is unset using 'default-guest'"
    QEMU_GUEST_NAME="default-guest"
  fi

  # set guest defaults
  : "${QEMU_GUEST_BOOT_ISO:=}"
  : "${QEMU_GUEST_PATH:=$QEMU_GUESTS/$QEMU_GUEST_NAME}"
  QEMU_GUEST_MONITOR="$QEMU_GUEST_PATH/guest.monitor"
  QEMU_GUEST_PIDFILE="$QEMU_GUEST_PATH/guest.pid"
  : "${QEMU_GUEST_APPEND:=}"
  : "${QEMU_GUEST_SSH_FWD_PORT:=2022}"
  : "${QEMU_GUEST_MACHINE_TYPE:=q35}"
  : "${QEMU_GUEST_CPU:=host}"
  : "${QEMU_GUEST_MEM:=2G}"
  : "${QEMU_GUEST_BOOT_IMG:=$QEMU_GUEST_PATH/boot.img}"
  : "${QEMU_GUEST_BOOT_IMG_FMT:=qcow2}"

  if [[ -z "$QEMU_GUEST_KERNEL" && -f "$QEMU_GUEST_PATH/bzImage" ]]; then
    QEMU_GUEST_KERNEL="$QEMU_GUEST_PATH/bzImage"
  fi

  : "${QEMU_GUEST_CONSOLE:=file}"
  if [[ "$QEMU_GUEST_CONSOLE" = "file" ]]; then
    QEMU_GUEST_CONSOLE_FILE="$QEMU_GUEST_PATH/console.out"
  fi

  # set nvme defaults
  : "${QEMU_NVME_ID:=cij_nvme}"
  : "${QEMU_NVME_NUM_GRP:=2}"
  : "${QEMU_NVME_NUM_CHK:=60}"
  : "${QEMU_NVME_NUM_PU:=4}"
  : "${QEMU_NVME_NUM_SEC:=4096}"
  : "${QEMU_NVME_LBADS:=4096}"
  : "${QEMU_NVME_MS:=16}"
  : "${QEMU_NVME_WS_MIN:=4}"
  : "${QEMU_NVME_WS_OPT:=8}"
  : "${QEMU_NVME_CUNITS:=24}"

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
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_grp$QEMU_NVME_NUM_GRP"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_pu$QEMU_NVME_NUM_PU"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_chk$QEMU_NVME_NUM_CHK"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_sec$QEMU_NVME_NUM_SEC"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_lbads$QEMU_NVME_LBADS"
  QEMU_NVME_IMAGE="$QEMU_NVME_IMAGE""_ms$QEMU_NVME_MS"

  QEMU_NVME_IMAGE_FPATH="$QEMU_GUEST_PATH/$QEMU_NVME_IMAGE.img"
  export QEMU_NVME_IMAGE_FPATH

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
    return 1
  fi

  PID=""
  if ! PID=$(qemu::hostcmd_output "cat \"$QEMU_GUEST_PIDFILE\""); then
    cij::err "qemu::is_running: failed getting pid from '$QEMU_GUEST_PIDFILE'"
    return 1
  fi

  if [[ -z "$PID" ]]; then
    cij::info "qemu::is_running: no qemu/pid($PID), probably not running"
    return 1
  fi

  if qemu::hostcmd "ps -p \"$PID\" > /dev/null"; then
    cij::info "qemu::is_running: qemu/pid($PID) seems to be running"
    return 0
  else
    cij::info "qemu::is_running: qemu/pid($PID) does not seem to be running"
    return 1
  fi
}

# Wait for qemu to stop running, or fail trying...
qemu::wait() {
  if ! qemu::env; then
    cij::err "qemu::wait: env failed"
    return 1
  fi

  local timeout=$1
  local count=0

  while qemu::is_running; do
    sleep 1
    count=$(( count + 1))
    if [[ -n "$timeout" && "$count" -gt "$timeout" ]]; then
      break
    fi
  done

  return 0
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

  qemu::hostcmd "[[ -f $QEMU_NVME_IMAGE_FPATH ]]"
  return $?
}

qemu::guest_nvme_create() {
  if ! qemu::env; then
    cij::err "qemu::guest_nvme_create: failed"
    return 1
  fi

  local opts="num_ns=1"
  opts="$opts,num_grp=$QEMU_NVME_NUM_GRP"
  opts="$opts,num_pu=$QEMU_NVME_NUM_PU"
  opts="$opts,num_chk=$QEMU_NVME_NUM_CHK"
  opts="$opts,num_sec=$QEMU_NVME_NUM_SEC"
  opts="$opts,sec_size=$QEMU_NVME_LBADS"
  opts="$opts,md_size=$QEMU_NVME_MS"
  opts="$opts,ws_min=$QEMU_NVME_WS_MIN"
  opts="$opts,ws_opt=$QEMU_NVME_WS_OPT"
  opts="$opts,mw_cunits=$QEMU_NVME_MW_CUNITS"

  cij::info "Creating ocssd backing file"
  if ! qemu::hostcmd "$QEMU_IMG_BIN create -f ocssd -o $opts $QEMU_NVME_IMAGE_FPATH"; then
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

  QEMU_ARGS_NVME=""
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME -blockdev ocssd"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,node-name=drive_$QEMU_NVME_ID"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,discard=unmap"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,detect-zeroes=unmap"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,file.driver=file"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,file.filename=$QEMU_NVME_IMAGE_FPATH"

  QEMU_ARGS_NVME="$QEMU_ARGS_NVME -device nvme"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,drive=drive_$QEMU_NVME_ID"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,serial=deadbeef"
  QEMU_ARGS_NVME="$QEMU_ARGS_NVME,id=$QEMU_NVME_ID"

  : "${QEMU_NVME_MDTS:=}"
  : "${QEMU_NVME_MS:=}"

  if [[ -n "$QEMU_NVME_MDTS" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,mdts=$QEMU_NVME_MDTS"
  fi

  if [[ -n "$QEMU_NVME_DEBUG" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,ldebug=$QEMU_NVME_DEBUG"
  fi

  if [[ -n "$QEMU_NVME_WS_MIN" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lws_min=$QEMU_NVME_WS_MIN"
  fi

  if [[ -n "$QEMU_NVME_WS_OPT" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lws_opt=$QEMU_NVME_WS_OPT"
  fi

  if [[ -n "$QEMU_NVME_WS_CUNITS" ]]; then
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lmw_cunits=$QEMU_NVME_MW_CUNITS"
  fi

  if [[ -n "$QEMU_NVME_CHUNKTABLE" ]]; then
    QEMU_GUEST_CHUNKTABLE="$QEMU_GUEST_PATH/chunktable.txt"
    qemu::hostcmd "[[ -f \"$QEMU_GUEST_CHUNKTABLE\" ]] && rm \"$QEMU_GUEST_CHUNKTABLE\""
    if ! qemu::host_push "$QEMU_NVME_CHUNKTABLE" "$QEMU_GUEST_PATH/chunktable.txt"; then
      cij::err "qemu::config_guest_nvme failed"
      return 1
    fi
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lchunkstate=$QEMU_GUEST_CHUNKTABLE"
  fi

  if [[ -n "$QEMU_NVME_RESETFAIL" ]]; then
    QEMU_GUEST_RESETFAIL="$QEMU_GUEST_PATH/resetfail.txt"
    qemu::hostcmd "rm $QEMU_GUEST_RESETFAIL"
    if ! qemu::host_push "$QEMU_NVME_RESETFAIL" "$QEMU_GUEST_RESETFAIL"; then
      cij::err "qemu::config_guest_nvme failed"
      return 1
    fi
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lresetfail=$QEMU_GUEST_RESETFAIL"
  fi

  if [[ -n "$QEMU_NVME_WRITEFAIL" ]]; then
    QEMU_GUEST_RESETFAIL="$QEMU_GUEST_PATH/writefail.txt"
    qemu::hostcmd "rm $QEMU_GUEST_WRITEFAIL"
    if ! qemu::host_push "$QEMU_NVME_WRITEFAIL" "$QEMU_GUEST_WRITEFAIL"; then
      cij::err "qemu::config_guest_nvme failed"
      return 1
    fi
    QEMU_ARGS_NVME="$QEMU_ARGS_NVME,lwritefail=$QEMU_GUEST_WRITEFAIL"
  fi

  return 0;
}

qemu::run() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  if qemu::is_running; then
    cij::err "qemu::run: looks like qemu is already running"
    return 1
  fi

  cij::info "Guests: " $QEMU_GUESTS " Name: " $QEMU_GUEST_NAME " Path: " $QEMU_GUEST_PATH
  if ! qemu::hostcmd "[[ -f $QEMU_GUEST_BOOT_IMG ]]"; then
    cij::err "Cannot find guest boot image ($QEMU_GUEST_BOOT_IMG)"
    return 1
  fi

  if [[ -n "$QEMU_NVME_ID" ]]; then
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

  # cpu/memory
  QEMU_ARGS=
  QEMU_ARGS="$QEMU_ARGS -machine type=$QEMU_GUEST_MACHINE_TYPE,kernel_irqchip=split,accel=kvm"
  QEMU_ARGS="$QEMU_ARGS -cpu $QEMU_GUEST_CPU"

  if [[ -n "${QEMU_GUEST_SMP}" ]]; then
    QEMU_ARGS="$QEMU_ARGS -smp $QEMU_GUEST_SMP"
  fi

  QEMU_ARGS="$QEMU_ARGS -m $QEMU_GUEST_MEM"

  # optionally boot from iso
  if [[ -n "${QEMU_GUEST_BOOT_ISO}" ]]; then
    QEMU_ARGS="$QEMU_ARGS -boot d -cdrom $QEMU_GUEST_BOOT_ISO"
  fi

  # boot drive
  QEMU_ARGS="$QEMU_ARGS -blockdev ${QEMU_GUEST_BOOT_IMG_FMT},node-name=boot,file.driver=file,file.filename=${QEMU_GUEST_BOOT_IMG}"
  QEMU_ARGS="$QEMU_ARGS -device virtio-blk-pci,drive=boot"

  # nic
  QEMU_ARGS="$QEMU_ARGS -netdev user,id=n1,ipv6=off,hostfwd=tcp::$QEMU_GUEST_SSH_FWD_PORT-:22"
  QEMU_ARGS="$QEMU_ARGS -device virtio-net-pci,netdev=n1"

  # qemu monitor
  QEMU_ARGS="$QEMU_ARGS -monitor unix:$QEMU_GUEST_MONITOR,server,nowait"

  # pidfile
  QEMU_ARGS="$QEMU_ARGS -pidfile $QEMU_GUEST_PIDFILE"

  # optionally boot specific kernel
  if [[ -n "$QEMU_GUEST_KERNEL" ]]; then
    QEMU_ARGS="$QEMU_ARGS -kernel \"${QEMU_GUEST_KERNEL}\""
    QEMU_ARGS="$QEMU_ARGS -append \"root=/dev/vda1 vga=0 console=ttyS0,kgdboc=ttyS1,115200 $QEMU_GUEST_APPEND\""
  fi

  case $QEMU_GUEST_CONSOLE in
    file )
      QEMU_ARGS="$QEMU_ARGS -display none -serial file:$QEMU_GUEST_CONSOLE_FILE"
      QEMU_ARGS="$QEMU_ARGS -daemonize"
      ;;

    stdio )
      QEMU_ARGS="$QEMU_ARGS -nographic"
      QEMU_ARGS="$QEMU_ARGS -serial mon:stdio"
      ;;
  esac

  QEMU_ARGS="$QEMU_ARGS $QEMU_ARGS_NVME $QEMU_ARGS_EXTRA"

  QEMU_CMD="$QEMU_BIN $QEMU_ARGS"

  cij::info "Starting QEMU with commandline: $QEMU_CMD"
  if ! qemu::hostcmd "$QEMU_CMD"; then
    cij::err "qemu::run Failed to start qemu"
    return 1
  fi

  return 0
}
