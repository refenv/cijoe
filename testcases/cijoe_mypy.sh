#!/usr/bin/env bash
#
# Run mypy on Python source code found in $CIJ_PKG_REPOS
#
# This testcase runs mypy to check for possible issues in the cijoe data structures, specifically
# the representation of testrun, testcases, testsuites, and hooks.
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test.enter

cij.info "CIJ_PKG_REPOS: '${CIJ_PKG_REPOS}'"

if [[ -z "$CIJ_PKG_REPOS" ]]; then
  test.fail "Please set 'CIJ_PKG_REPOS'"
fi

if [[ ! -d "${CIJ_PKG_REPOS}/modules/cij" ]]; then
  cij.warn "No Python source to check"
  test.pass
fi

# shellcheck disable=SC2086
if ! mypy "${CIJ_PKG_REPOS}/modules/cij" ; then
  popd || true
  test.fail
fi

test.pass
