#!/usr/bin/env bash
#
# selftest: running tests of CIJOE and CIJOE packages using CIJOE
#
# * Sources in CIJOE
# * Creates local environment definition $res_dpath/selftest_env.sh
# * Invokes the cij_runner
# * Generates report(s) using cij_reporter and cij_testcases
#

# shellcheck source=modules/cijoe.sh
cij_setup() {
  CIJ_ROOT=$(cij_root)
  export CIJ_ROOT

  pushd "$CIJ_ROOT" || exit 1
  source modules/cijoe.sh
  if ! source "$CIJ_ROOT/modules/cijoe.sh"; then
    echo "Bad mojo"
    exit
  fi
  popd || exit 1
}

main() {
  local res=0

  cij_setup

  pkg_selftest="$1"
  open_reports="$2"
  res_dpath="$3"

  # Create directory to store results
  : "${res_dpath:=$(mktemp -d trun.XXXXXX -p /tmp)}"
  : "${env_fpath:=$res_dpath/selftest_env.sh}"
  : "${tplan_fpath:=$CIJ_TESTPLANS/cijoe.plan}"
  rmdir "$res_dpath" || echo "Cannot remove => That is OK"
  mkdir "$res_dpath"

  cij::info "# pkg_selftest: '$pkg_selftest'"
  cij::info "# open_reports: '$open_reports'"
  cij::info "# res_dpath: '$res_dpath'"

  cij::info "# res_dpath: '$res_dpath'"
  cij::info "# tplan_fpath: '$tplan_fpath'"
  cij::info "# env_fpath: '$env_fpath'"

  # Create the environment
  cat "$CIJ_ENVS/localhost.sh" > "$env_fpath"
  echo "export CIJ_PKG_REPOS=\"$PWD\"" >> "$env_fpath"
  if [[ $pkg_selftest -gt 0 ]]; then
    echo "export SHELLCHECK_OPTS='--exclude=SC1091'" >> "$env_fpath"
  fi

  # Start the runner
  if ! cij_runner --testplan "$tplan_fpath" --env "$env_fpath" --output "$res_dpath" -vvv; then
    cij::err "cij_runner encountered an error"
    res=$(( res + 1 ))
  fi

  # Extract metrics
  if ! cij_extractor --extractor fio_json_read --output "$res_dpath"; then
    cij::err "cij_extractor encountered an error"
    res=$(( res + 1 ))
  fi

  # Analyse metrics
  if ! cij_analyser --preqs "${CIJ_TESTFILES}/example.preqs" --output "$res_dpath"; then
    cij::err "cij_analyser encountered an error"
    res=$(( res + 1 ))
  fi

  # Create test report
  if ! cij_reporter --output "$res_dpath"; then
    cij::err "cij_reporter encountered an error"
    res=$(( res + 1 ))
  fi

  # Create testcases report
  if ! cij_testcases --output "$res_dpath"; then
    cij::err "cij_testcases encountered an error"
    res=$(( res + 1 ))
  fi

  if [[ $open_reports -gt 0 ]]; then
    (xdg-open "$res_dpath/report.html" || open "$res_dpath/report.html") &
  elif [[ $open_reports -gt 1 ]]; then
    (xdg-open "$res_dpath/testcases.html" || open "$res_dpath/testcases.html") &
    (xdg-open "$res_dpath/report.html" || open "$res_dpath/report.html") &
  fi

  cij::info "res: '$res'"

  exit $res
}

main "$@"
