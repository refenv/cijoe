#!/usr/bin/env bash
#
# qemu.sh - Script providing convenience functions for invoking qemu
#
# Tools required:
#
# * ssh, the SSH cli
# * cloud-localds, for provisioning cloud-images via 'qemu::img_from_url'
# * minicom, for interactive text-console
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
#
# qemu::hostcmd                 - Execute a command on the qemu-host
# qemu::hostcmd_output          - Retrieve output from command on qemu-host
# qemu::host_push               - Push to qemu-host
# qemu::provision_kernel        - Push kernel to qemu-host
# qemu::is_running              - Check whether the guest is running
# qemu::wait                    - Wait for QEMU to stop running
#
# qemu::img_from_url
#
# Guest configuration and QEMU arguments are managed via variables. Define them
# as exported environment variables or make sure they are in scope.
#
# Variables:
#
# QEMU_HOST                     - SSH_HOST of qemu-host
# QEMU_HOST_USER                - SSH_USER of qemu-host
# QEMU_HOST_PORT                - SSH_PORT of qemu-host
#
# QEMU_HOST_SYSTEM_BIN          - Path to qemu binary, default 'qemu'
# QEMU_HOST_IMG_BIN             - Path to qemu binary, default 'qemu-img'
#
# QEMU_ARGS_EXTRA               - Wildcard for options which aren't wrapped below.
#
# The "QEMU_GUESTS" is just a directory containing subdirectories,
# one subdirectory for each guests. Within each guest directory files such
# as "guest.pid", "guest.serial", "guest.monitor", "boot.img", "nvme00.img", and
# the like.
#
# QEMU_GUESTS                   - Path to qemu guests, default /tmp/guests.
#
# The "QEMU_GUEST_*"            - These define how a guest is started
#
# QEMU_GUEST_NAME               - Default "default-guest"
# QEMU_GUEST_PATH               - Default "QEMU_GUESTS/QEMU_GUEST_NAME"
# QEMU_GUEST_BOOT_ISO           - Boot from provided ISO instead of IMG
# QEMU_GUEST_BOOT_IMG           - Default "QEMU_GUEST_PATH/boot.img"
# QEMU_GUEST_BOOT_IMG_FMT       - Default "qcow2"
# QEMU_GUEST_CPU                - Adds "-cpu $QEMU_GUEST_CPU", DEFAULT: "host"
# QEMU_GUEST_MEM                - Adds "-m QEMU_GUEST_MEM", DEFAULT: "2G"
# QEMU_GUEST_SMP                - Adds "-smp $QEMU_GUEST_SMP", OPTIONAL, no DEFAULT
# QEMU_GUEST_IOMMU              - Adds "-device, 'intel-iommu,pt,intremap=on'"

# QEMU_GUEST_KERNEL             - Adds "-kernel $QEMU_GUEST_PATH/bzImage" and additional args
# QEMU_GUEST_APPEND             - Adds extra kernel parameters for -append
# QEMU_GUEST_SSH_FWD_PORT       - Port to forward port 22 to host. Default: 2022
# QEMU_GUEST_CONSOLE            - Default: "file"
#
#   "stdio":  Console mapped to stdio
#   "file": Console output piped to file "QEMU_GUEST_PATH/console.out"
#   "foo":  The SDL interface pops up.
#
# QEMU_GUEST_HOST_SHARE         - Set to an absolute path to share with guest
#
qemu::env() {
  if [[ ! -v QEMU_HOST ]]; then
    cij::err "qemu::env: QEMU_HOST not set"
    return 1
  fi
  if [[ ! -v QEMU_HOST_USER ]]; then
    cij::err "qemu::env: QEMU_HOST_USER not set"
    return 1
  fi
  # set host defaults
  : "${QEMU_HOST_PORT:=22}"

  if [[ ! -v QEMU_GUESTS ]]; then
    cij::info "QEMU_GUESTS is unset using '/tmp/guests'"
    : "${QEMU_GUESTS:=/tmp/guests}"
  fi

  if [[ ! -v QEMU_GUEST_NAME ]]; then
    cij::info "QEMU_GUESTS is unset using 'default-guest'"
    : "${QEMU_GUEST_NAME=default-guest}"
  fi

  # Set qemu defaults
  : "${QEMU_HOST_SYSTEM_BIN:=qemu}"
  : "${QEMU_HOST_IMG_BIN:=qemu-img}"

  # set guest defaults
  : "${QEMU_GUEST_BOOT_ISO:=}"
  : "${QEMU_GUEST_PATH:=${QEMU_GUESTS}/${QEMU_GUEST_NAME}}"

  case ${QEMU_GUEST_CONSOLE} in
  sock)
    : "${QEMU_GUEST_MONITOR:=${QEMU_GUEST_PATH}/monitor.sock}"
    : "${QEMU_GUEST_SERIAL:=${QEMU_GUEST_PATH}/serial.sock}"
    ;;
  file)
    : "${QEMU_GUEST_MONITOR:=${QEMU_GUEST_PATH}/monitor.sock}"
    : "${QEMU_GUEST_SERIAL:=${QEMU_GUEST_PATH}/serial.txt}"
    ;;
  esac

  : "${QEMU_GUEST_PIDFILE:=${QEMU_GUEST_PATH}/guest.pid}"
  : "${QEMU_GUEST_APPEND:=}"
  : "${QEMU_GUEST_SSH_FWD_PORT:=2022}"
  : "${QEMU_GUEST_MACHINE_TYPE:=q35}"
  : "${QEMU_GUEST_CPU:=host}"
  : "${QEMU_GUEST_MEM:=2G}"
  : "${QEMU_GUEST_IOMMU:=0}"
  : "${QEMU_GUEST_BOOT_IMG:=${QEMU_GUEST_PATH}/boot.img}"
  : "${QEMU_GUEST_BOOT_IMG_FMT:=qcow2}"

  : "${QEMU_GUEST_KERNEL:=0}"

  : "${QEMU_GUEST_CONSOLE:=file}"

  return 0
}

qemu::hostcmd() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  SSH_USER=${QEMU_HOST_USER} SSH_HOST=${QEMU_HOST} SSH_PORT=${QEMU_HOST_PORT} ssh::cmd "$1"
}

qemu::hostcmd_output() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  SSH_USER=${QEMU_HOST_USER} SSH_HOST=${QEMU_HOST} SSH_PORT=${QEMU_HOST_PORT} ssh::cmd_output "$1"
}

qemu::host_push() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  if ! SSH_USER=${QEMU_HOST_USER} SSH_HOST=${QEMU_HOST} SSH_PORT=${QEMU_HOST_PORT} ssh::push "$1" "$2"; then
    cij::err "qemu::host_push failed"
    return 1
  fi

  return 0
}

# Copy from path into guest, e.g.
# > qemu::provision_kernel "/path/to/kernel/bzImage"
qemu::provision_kernel() {
  if ! qemu::env; then
    cij::err "qemu::provision_kernel failed"
    return 1
  fi

  local bzi_src
  local bzi_dst

  bzi_src=$1
  bzi_dst="${QEMU_GUEST_PATH}/bzImage"

  if ! qemu::host_push "$bzi_src" "${bzi_dst}"; then
    cij::err "qemu:provision_kernel failed"
    return 1
  fi
}

qemu::kill() {
  if ! qemu::env; then
    cij::err "qemu::kill failed"
    return 1
  fi

  if ! qemu_pid=$(qemu::hostcmd_output "cat \"$QEMU_GUEST_PIDFILE\""); then
    cij::err "qemu::kill: failed to get qemu pid"
    return 1
  fi

  if ! qemu::hostcmd "kill $qemu_pid"; then
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

  if ! qemu::hostcmd "[[ -f \"${QEMU_GUEST_PIDFILE}\" ]]"; then
    cij::info "qemu::is_running: no pidfile, assuming it is not running"
    return 1
  fi

  PID=""
  if ! PID=$(qemu::hostcmd_output "cat \"${QEMU_GUEST_PIDFILE}\""); then
    cij::err "qemu::is_running: failed getting pid from '${QEMU_GUEST_PIDFILE}'"
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

  qemu::hostcmd "echo system_powerdown | socat - UNIX-CONNECT:${QEMU_GUEST_MONITOR}"
  return $?
}

qemu::reset() {
  if ! qemu::env; then
    cij::err "qemu::reset: env failed"
    return 1
  fi

  qemu::hostcmd "echo system_reset | socat - UNIX-CONNECT:${QEMU_GUEST_MONITOR}"
  return $?
}

qemu::monitor() {
  if ! qemu::env; then
    cij::err "qemu::monitor: failed"
    return 1
  fi

  qemu::hostcmd "socat - UNIX-CONNECT:${QEMU_GUEST_MONITOR}"
  return $?
}

# watch the console monitor output
# interactive usage
qemu::console() {
  if ! qemu::env; then
    cij::err "qemu::console: qemu::env failed"
    return 1
  fi

  case ${QEMU_GUEST_CONSOLE} in
  sock)
    SSH_EXTRA_ARGS="-t" qemu::hostcmd "minicom -D unix#${QEMU_GUEST_PATH}/serial.sock"
    ;;
  file)
    qemu::hostcmd "tail -n 1000 -f ${QEMU_GUEST_PATH}/serial.txt"
    ;;
  esac

  return $?
}

qemu::img() {
  if ! qemu::env; then
    cij::err "qemu::img: qemu::env failed"
    return 1
  fi

  local _cmd

  _cmd="${QEMU_HOST_IMG_BIN} $*"

  qemu::hostcmd "${_cmd}"
  return $?
}

qemu::guest_dev_exists() {
  if ! qemu::env; then
    cij::err "qemu::guest_dev_exists: qemu::env failed"
    return 1
  fi

  qemu::hostcmd "[[ -f ${QEMU_DEV_IMAGE_FPATH} ]]"
  return $?
}

qemu::img_create() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  : "${1?missing: ident}"
  : "${2?missing: fmt}"
  : "${3?missing: size}"

  local _ident="$1"
  local _fmt="$2"
  local _size="$3"

  local _img="${QEMU_GUEST_PATH}/${_ident}.img"

  if qemu::hostcmd "[[ -f ${_img} ]]"; then
    return 0
  fi

  qemu::img "create -f ${_fmt} ${_img} ${_size}"
  return $?
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
  cij::info "Guests: ${QEMU_GUESTS} Name: ${QEMU_GUEST_NAME} Path: ${QEMU_GUEST_PATH}"
  if ! qemu::hostcmd "[[ -f ${QEMU_GUEST_BOOT_IMG} ]]"; then
    cij::err "qemu::run: missing: ${QEMU_GUEST_BOOT_IMG}"
    return 1
  fi

  # Setup arguments, `qemu::env` provides sensible defaults for the
  # non-optional arguments
  local _args=""
  local _cmd=""

  # cpu/memory
  _args="$_args -machine type=$QEMU_GUEST_MACHINE_TYPE,kernel_irqchip=split,accel=kvm"
  _args="$_args -cpu ${QEMU_GUEST_CPU}"

  if [[ -v QEMU_GUEST_SMP ]]; then
    _args="$_args -smp ${QEMU_GUEST_SMP}"
  fi

  # NOTE: how does this behave when cpu=host and the host is e.g. a Ryzen?
  if [[ -v QEMU_GUEST_IOMMU && "$QEMU_GUEST_IOMMU" != "0" ]]; then
    _args="$_args -device intel-iommu,pt=on,intremap=on"
  fi

  _args="$_args -m ${QEMU_GUEST_MEM}"

  # optionally boot from iso
  if [[ -n "${QEMU_GUEST_BOOT_ISO}" ]]; then
    _args="$_args -boot d -cdrom ${QEMU_GUEST_BOOT_ISO}"
  fi

  # boot drive
  _args="$_args -blockdev ${QEMU_GUEST_BOOT_IMG_FMT},node-name=boot,file.driver=file,file.filename=${QEMU_GUEST_BOOT_IMG}"
  _args="$_args -device virtio-blk-pci,drive=boot"

  # network interface with a single port-forward
  _args="$_args -netdev user,id=n1,ipv6=off,hostfwd=tcp::${QEMU_GUEST_SSH_FWD_PORT}-:22"
  _args="$_args -device virtio-net-pci,netdev=n1"

  # pidfile
  _args="$_args -pidfile ${QEMU_GUEST_PIDFILE}"

  # optionally boot specific kernel
  if [[ -v QEMU_GUEST_KERNEL && "${QEMU_GUEST_KERNEL}" == "1" ]]; then
    _args="$_args -kernel \"${QEMU_GUEST_PATH}/bzImage\""
    _args="$_args -append \"root=/dev/vda1 vga=0 console=ttyS0,kgdboc=ttyS1,115200 ${QEMU_GUEST_APPEND}\""
  fi

  # qemu monitor
  _args="$_args -monitor unix:${QEMU_GUEST_PATH}/monitor.sock,server,nowait"

  case ${QEMU_GUEST_CONSOLE} in
  sock)
    _args="$_args -display none"
    _args="$_args -serial unix:${QEMU_GUEST_PATH}/serial.sock,server,nowait"
    _args="$_args -daemonize"
    ;;

  file)
    _args="$_args -display none"
    _args="$_args -serial file:${QEMU_GUEST_PATH}/serial.txt"
    _args="$_args -daemonize"
    ;;

  stdio)
    _args="$_args -nographic"
    _args="$_args -serial mon:stdio"
    ;;
  esac

  if [[ -v QEMU_GUEST_HOST_SHARE ]]; then
    _args="$_args -virtfs fsdriver=local,id=fsdev0,security_model=mapped,mount_tag=hostshare,path=${QEMU_GUEST_HOST_SHARE}"
  fi

  _cmd="$_args -D ${QEMU_GUEST_PATH}/stderr.log"

  _cmd="${QEMU_HOST_SYSTEM_BIN} $_args"
  if [[ -v QEMU_ARGS_EXTRA ]]; then
    _cmd="${_cmd} ${QEMU_ARGS_EXTRA}"
  fi

  cij::info "Starting QEMU with commandline: $_cmd"
  if ! qemu::hostcmd "$_cmd"; then
    cij::err "qemu::run Failed to start qemu"
    return 1
  fi

  return 0
}

#
# Downloads a cloud-image and executes first-boot
#
# qemu::img_from_url "https://cloud.cdimage.com/.../debian-generic.qcow2"
#
qemu::img_from_url() {
  if ! qemu::env; then
    cij::err "qemu::img_from_url failed"
    return 1
  fi

  local data_file="${QEMU_GUEST_PATH}/user-data"
  local meta_file="${QEMU_GUEST_PATH}/meta-data"
  local seed_img="${QEMU_GUEST_PATH}/seed.img"
  local boot_img_bck="${QEMU_GUEST_PATH}/boot-bck.img"
  local boot_img="${QEMU_GUEST_PATH}/boot.img"

  boot_img_url="$1"

  # Check that files for cloud-image seeding are available on qemu-host
  if ! qemu::hostcmd "[[ -f \"${data_file}\" ]]"; then
    cij::err "qemu::img_from_url: missing: ${data_file}"
    return 1
  fi
  if ! qemu::hostcmd "[[ -f \"${meta_file}\" ]]"; then
    cij::err "qemu::img_from_url: missing: ${meta_file}"
    return 1
  fi

  # Create seed-image on qemu-host
  if ! qemu::hostcmd "cloud-localds -v ${seed_img} ${data_file} ${meta_file}"; then
    cij::err "qemu::img_from_url: failed producing ${seed_img}"
    return 1
  fi

  # Download the seed image on qemu-host
  if ! qemu::hostcmd "[[ -f ${boot_img_bck} ]]"; then
    if ! qemu::hostcmd "wget -O ${boot_img_bck} ${boot_img_url}"; then
      cij::err "qemu::img_from_url: failed downloading: ${boot_img_url}"
      return 1
    fi
  fi

  # Copy from backup
  if ! qemu::hostcmd "cp ${boot_img_bck} ${boot_img}"; then
    cij::err "qemu::img_from_url: failed copying"
    return 1
  fi

  # Spin it up for first-boot
  : "${QEMU_ARGS_EXTRA:=-drive file=${seed_img},if=virtio,format=raw}"
  if ! qemu::run; then
    cij::err "qemu:img_from_url: failed starting qemu"
    return 1
  fi

  # TODO: wait for it spin up, init, configure and then then shut it down
  qemu::wait 600

  return 0
}

#
# Helper function, creating a "-drive" args loving in QEMU_GUEST_PATH
#
qemu::args_drive() {
  if ! qemu::env; then
    cij::err "qemu::env failed"
    return 1
  fi

  : "${1?missing: id}"
  : "${2?missing: format}"

  local _ident="$1"
  local _fmt="$2"
  local _args

  _args="-drive "
  _args="${_args}id=${_ident}"
  _args="${_args},file=${QEMU_GUEST_PATH}/${_ident}.img"
  _args="${_args},format=${_fmt}"
  _args="${_args},if=none"
  _args="${_args},discard=on"
  _args="${_args},detect-zeroes=unmap"
#  if [[ -n "$3" ]]; then
#    _args="${_args},$3"
#  fi

  echo "$_args"
}

