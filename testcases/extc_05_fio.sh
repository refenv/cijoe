#!/bin/bash
#
# Run fio controlled by environment variables, formal and json-formatted output stored in AUX
#
# Instrument the fio-wrapper script via the environment variables:
#
# FIO_BIN: set this to the fio binary to use. Def: "fio"
# FIO_ARGS: Assign this for auxilary arguments to fio. Def: ""
#
# FIO_NRUNS: Repeat the fio invocation this many times. Def: "1"
# FIO_BS_LIST: The "--bs" to run fio for, provide a string on the form "512 4k 32k". Def: "512"
# FIO_IODEPTH_LIST: The "--iodepth" to use; provide a string on the form "1 2 4 8". Def: "1"
#
# FIO_FILENAME: When set, adds argument "--filename=${FIO_FILENAME}"
# FIO_SCRIPT: When set, adds argument "--script=${FIO_SCRIPT}"
# FIO_SECTION: When set, adds argument "--section=${FIO_SCRIPT}"
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test.enter

: "${FIO_BIN:=fio}"

: "${FIO_ARGS:=}"

: "${FIO_NRUNS:=1}"
: "${FIO_BS_LIST:=512}"
: "${FIO_IODEPTH_LIST:=1}"

main() {
  local _target_fpath="/tmp/fio-output.txt"

  for FIO_IODEPTH in $FIO_IODEPTH_LIST; do
    for FIO_BS in $FIO_BS_LIST; do
      for i in $(seq "$FIO_NRUNS"); do
        local _output_fpath="${CIJ_TEST_AUX_ROOT}/fio-output-iodepth:${FIO_IODEPTH}-bs:${FIO_BS}-run:${i}.txt"
        local _args=""

        if [[ -v FIO_FILENAME ]]; then
          _args="${_args} --filename ${FIO_FILENAME}"
        fi
        if [[ -v FIO_SCRIPT ]]; then
          _args="${_args} --script ${FIO_SCRIPT}"
        fi
        if [[ -v FIO_SECTION ]]; then
          _args="${_args} --section ${FIO_SECTION}"
        fi

        _args="${_args} --output-format=normal,json --output=${_target_fpath}"

        cij.info "run: ${i}/${FIO_NRUNS}"
        if ! cij.cmd "${FIO_BIN} ${FIO_ARGS} ${_args}"; then
          return 1
        fi

        # Download the output
        if ! cij.pull "${_target_fpath}" "${_output_fpath}"; then
          cij.err "xnvme.fioe: failed pulling down fio output-file"
          return 1
        fi

        # Dump output files it to stdout for convenient inspection in the run-logs
        cat "${_output_fpath}"
      done
    done
  done

  return 0
}

if main; then
  test.pass "That went well; see aux-files for output."
else
  test.fail
fi
