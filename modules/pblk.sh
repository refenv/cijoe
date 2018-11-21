#!/usr/bin/env bash
#
# pblk.sh - Script providing convenience functions for pblk
#
# Functions:
#
# pblk::watch           - Displays a dashboard of pblk sysfs stats
# pblk::trace_enable    - Enables a pblk trace event
# pblk::trace_disable   - Disables a pblk trace event
# pblk::trace_watch     - Watches the kernel trace buffer
#

pblk::watch() {
  ssh::cmd_t "watch -n.5 \" \
  echo Line stats && \
  cat /sys/class/block/$BLOCK_DEV_NAME/pblk/lines \
  && echo
  && echo Rate limiter stats \
  && cat /sys/class/block/$BLOCK_DEV_NAME/pblk/rate_limiter \
  && echo
  && echo Write amplification trip \
  && cat /sys/class/block/$BLOCK_DEV_NAME/pblk/write_amp_trip \
  && echo
  && echo Write amplification mileage \
  && cat /sys/class/block/$BLOCK_DEV_NAME/pblk/write_amp_mileage \
  && echo
  && echo Padding distribution \
  && cat /sys/class/block/$BLOCK_DEV_NAME/pblk/padding_dist \""
}

pblk::trace_enable() {
  ssh::cmd "echo 1 > /sys/kernel/debug/tracing/events/pblk/pblk_$1/enable"
}

pblk::trace_disable() {
  ssh::cmd "echo 0 > /sys/kernel/debug/tracing/events/pblk/pblk_$1/enable"
}

pblk::trace_watch() {
  ssh::cmd_t "watch -n.5 \" tail -n \$(( \$(tput lines) - 2 )) /sys/kernel/debug/tracing/trace\""
}

pblk::trace_all() {
  pblk::trace_enable "state"
  pblk::trace_enable "line_state"
  pblk::trace_enable "chunk_state"
  pblk::trace_enable "chunk_reset"
}

pblk::trace_get() {
  ssh::cmd_output "cat /sys/kernel/debug/tracing/trace" > "$1"
}

