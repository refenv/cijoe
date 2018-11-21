#!/usr/bin/env bash
#
# rbench::env - Checks environment for needed variables
#
# Variables REQUIRED by module
#/
# RBENCH_BIN    - Path to db_bench binary, no default, MUST be set
#
# All db_bench arguments uppercased and prefixed with RBENCH_ e.g.
# $RBENCH_NUM
#

rbench::env() {
  if ! ssh::env; then
    cij::err "rbench::env - Invalid SSH ENV."
    return 1
  fi

  # Mandatory ENV. VAR> definitions
  if [[ -z "$RBENCH_BIN" ]]; then
    cij::err "rbench::env: RBENCH_BIN is not defined"
    return 1
  fi

  return 0
}

rbench::run() {
  if ! rbench::env; then
    cij::err "rbench::run - Invalid SSH ENV."
    return 1
  fi

  ARGS=""
  if [[ -n "$RBENCH_BENCHMARKS" ]]; then
    ARGS="$ARGS --benchmarks=$RBENCH_BENCHMARKS"
  fi
  if [[ -n "$RBENCH_USE_EXISTING_DB" ]]; then
    ARGS="$ARGS --use_existing_db=$RBENCH_USE_EXISTING_DB"
  fi
  if [[ -n "$RBENCH_USE_DIRECT_READS" ]]; then
    ARGS="$ARGS --use_direct_reads=$RBENCH_USE_DIRECT_READS"
  fi

  #if [[ -n "$RBENCH_USE_DIRECT_WRITES" ]]; then
  #     ARGS="$ARGS --use_direct_writes=$RBENCH_USE_DIRECT_WRITES"
  #fi

  if [[ -n "$RBENCH_USE_DIRECT_IO_FOR_FLUSH_AND_COMPACTION" ]]; then
    ARGS="$ARGS --use_direct_io_for_flush_and_compaction=$RBENCH_USE_DIRECT_IO_FOR_FLUSH_AND_COMPACTION"
  fi
  if [[ -n "$RBENCH_ENV_URI" ]]; then
    ARGS="$ARGS --env_uri=$RBENCH_ENV_URI"
  fi
  if [[ -n "$RBENCH_DB" ]]; then
    ARGS="$ARGS --db=$RBENCH_DB"
  fi
  if [[ -n "$RBENCH_NUM" ]]; then
    ARGS="$ARGS --num=$RBENCH_NUM"
  fi
  if [[ -n "$RBENCH_VALUE_SIZE" ]]; then
    ARGS="$ARGS --value_size=$RBENCH_VALUE_SIZE"
  fi
  if [[ -n "$RBENCH_VERIFY_CHECKSUM" ]]; then
    ARGS="$ARGS --verify_checksum=$RBENCH_VERIFY_CHECKSUM"
  fi
  if [[ -n "$RBENCH_SYNC" ]]; then
    ARGS="$ARGS --sync=$RBENCH_SYNC"
  fi
  if [[ -n "$RBENCH_DISABLE_WAL" ]]; then
    ARGS="$ARGS --disable_wal=$RBENCH_DISABLE_WAL"
  fi
  if [[ -n "$RBENCH_COMPRESSION_TYPE" ]]; then
    ARGS="$ARGS --compression_type=$RBENCH_COMPRESSION_TYPE"
  fi
  if [[ -n "$RBENCH_COMPRESSION_RATIO" ]]; then
    ARGS="$ARGS --compression_ratio=$RBENCH_COMPRESSION_RATIO"
  fi
  if [[ -n "$RBENCH_MMAP_READ" ]]; then
    ARGS="$ARGS --mmap_read=$RBENCH_MMAP_READ"
  fi
  if [[ -n "$RBENCH_STATS_INTERVAL" ]]; then
    ARGS="$ARGS --stats_interval=$RBENCH_STATS_INTERVAL"
  fi
  if [[ -n "$RBENCH_STATS_PER_INTERVAL" ]]; then
    ARGS="$ARGS --stats_per_interval=$RBENCH_STATS_PER_INTERVAL"
  fi
  if [[ -n "$RBENCH_DISABLE_SEEK_COMPACTION" ]]; then
    ARGS="$ARGS --disable_seek_compaction=$RBENCH_DISABLE_SEEK_COMPACTION"
  fi
  if [[ -n "$RBENCH_STATISTICS" ]]; then
    ARGS="$ARGS --statistics=$RBENCH_STATISTICS"
  fi
  if [[ -n "$RBENCH_HISTOGRAM" ]]; then
    ARGS="$ARGS --histogram=$RBENCH_HISTOGRAM"
  fi
  if [[ -n "$RBENCH_THREADS" ]]; then
    ARGS="$ARGS --threads=$RBENCH_THREADS"
  fi
  if [[ -n "$RBENCH_OPEN_FILES" ]]; then
    ARGS="$ARGS --open_files=$RBENCH_OPEN_FILES"
  fi
  if [[ -n "$RBENCH_BLOCK_SIZE" ]]; then
    ARGS="$ARGS --block_size=$RBENCH_BLOCK_SIZE"
  fi
  if [[ -n "$RBENCH_CACHE_SIZE" ]]; then
    ARGS="$ARGS --cache_size=$RBENCH_CACHE_SIZE"
  fi
  if [[ -n "$RBENCH_BLOOM_BITS" ]]; then
    ARGS="$ARGS --bloom_bits=$RBENCH_BLOOM_BITS"
  fi
  if [[ -n "$RBENCH_CACHE_NUMSHARDBITS" ]]; then
    ARGS="$ARGS --cache_numshardbits=$RBENCH_CACHE_NUMSHARDBITS"
  fi
  if [[ -n "$RBENCH_WRITE_BUFFER_SIZE" ]]; then
    ARGS="$ARGS --write_buffer_size=$RBENCH_WRITE_BUFFER_SIZE"
  fi
  if [[ -n "$RBENCH_MAX_WRITE_BUFFER_NUMBER" ]]; then
    ARGS="$ARGS --max_write_buffer_number=$RBENCH_MAX_WRITE_BUFFER_NUMBER"
  fi
  if [[ -n "$RBENCH_MIN_WRITE_BUFFER_NUMBER_TO_MERGE" ]]; then
    ARGS="$ARGS --min_write_buffer_number_to_merge=$RBENCH_MIN_WRITE_BUFFER_NUMBER_TO_MERGE"
  fi
  if [[ -n "$RBENCH_TARGET_FILE_SIZE_BASE" ]]; then
    ARGS="$ARGS --target_file_size_base=$RBENCH_TARGET_FILE_SIZE_BASE"
  fi
  if [[ -n "$RBENCH_TARGET_FILE_SIZE_MULTIPLIER" ]]; then
    ARGS="$ARGS --target_file_size_multiplier=$RBENCH_TARGET_FILE_SIZE_MULTIPLIER"
  fi
  if [[ -n "$RBENCH_MAX_BACKGROUND_COMPACTIONS" ]]; then
    ARGS="$ARGS --max_background_compactions=$RBENCH_MAX_BACKGROUND_COMPACTIONS"
  fi
  if [[ -n "$RBENCH_MAX_GRANDPARENT_OVERLAP_FACTOR" ]]; then
    ARGS="$ARGS --max_grandparent_overlap_factor=$RBENCH_MAX_GRANDPARENT_OVERLAP_FACTOR"
  fi
  if [[ -n "$RBENCH_MAX_BYTES_FOR_LEVEL_BASE" ]]; then
    ARGS="$ARGS --max_bytes_for_level_base=$RBENCH_MAX_BYTES_FOR_LEVEL_BASE"
  fi
  if [[ -n "$RBENCH_MAX_BYTES_FOR_LEVEL_MULTIPLIER" ]]; then
    ARGS="$ARGS --max_bytes_for_level_multiplier=$RBENCH_MAX_BYTES_FOR_LEVEL_MULTIPLIER"
  fi
  if [[ -n "$RBENCH_MIN_LEVEL_TO_COMPRESS" ]]; then
    ARGS="$ARGS --min_level_to_compress=$RBENCH_MIN_LEVEL_TO_COMPRESS"
  fi
  if [[ -n "$RBENCH_NUM_LEVELS" ]]; then
    ARGS="$ARGS --num_levels=$RBENCH_NUM_LEVELS"
  fi
  if [[ -n "$RBENCH_LEVEL0_FILE_NUM_COMPACTION_TRIGGER" ]]; then
    ARGS="$ARGS --level0_file_num_compaction_trigger=$RBENCH_LEVEL0_FILE_NUM_COMPACTION_TRIGGER"
  fi
  if [[ -n "$RBENCH_LEVEL0_SLOWDOWN_WRITES_TRIGGER" ]]; then
    ARGS="$ARGS --level0_slowdown_writes_trigger=$RBENCH_LEVEL0_SLOWDOWN_WRITES_TRIGGER"
  fi
  if [[ -n "$RBENCH_LEVEL0_STOP_WRITES_TRIGGER" ]]; then
    ARGS="$ARGS --level0_stop_writes_trigger=$RBENCH_LEVEL0_STOP_WRITES_TRIGGER"
  fi
  if [[ -n "$RBENCH_DELETE_OBSOLETE_FILES_PERIOD_MICROS" ]]; then
    ARGS="$ARGS --delete_obsolete_files_period_micros=$RBENCH_DELETE_OBSOLETE_FILES_PERIOD_MICROS"
  fi
  if [[ -n "$RBENCH_RANDOM_ACCESS_MAX_BUFFER_SIZE" ]]; then
    ARGS="$ARGS --random_access_max_buffer_size=$RBENCH_RANDOM_ACCESS_MAX_BUFFER_SIZE"
  fi
  if [[ -n "$RBENCH_WRITABLE_FILE_MAX_BUFFER_SIZE" ]]; then
    ARGS="$ARGS --writable_file_max_buffer_size=$RBENCH_WRITABLE_FILE_MAX_BUFFER_SIZE"
  fi
  if [[ -n "$RBENCH_DISABLE_AUTO_COMPACTIONS" ]]; then
    ARGS="$ARGS --disable_auto_compactions=$RBENCH_DISABLE_AUTO_COMPACTIONS"
  fi

  RBENCH_CMD="$RBENCH_BIN $ARGS"
  if [[ -n "$RBENCH_CMD_PREFIX" ]]; then
    RBENCH_CMD="$RBENCH_CMD_PREFIX $RBENCH_CMD"
  fi

  if [[ -n "$RBENCH_CMD_POSTFIX" ]]; then
    RBENCH_CMD="$RBENCH_CMD $RBENCH_CMD_POSTFIX"
  fi

  if ! ssh::cmd "ulimit -n 100000"; then
    cij::err "rbench::run setting ulimit failed"
    return 1
  fi

  cij::emph "Running: $RBENCH_CMD"
  if ! ssh::cmd "$RBENCH_CMD"; then
    cij::err "rbench::run db_bench returned with an error"
    return 1
  fi
}
