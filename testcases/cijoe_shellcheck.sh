#!/bin/bash
#
# Run shellcheck on shell scripts found in $CIJ_PKG_REPOS
#
# This testcase runs the 'shellcheck' tool on all shell script it can find in
# $CIJ_PKG_REPOS. The intent is to use this on CIJOE as well as CIJOE packages.
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

cij::info "CIJ_PKG_REPOS: 'CIJ_PKG_REPOS'"
cij::info "SHELLCHECK_OPTS: 'SHELLCHECK_OPTS'"

if [[ -z "$CIJ_PKG_REPOS" ]]; then
  test::fail "Please set 'CIJ_PKG_REPOS'"
fi
pushd "$CIJ_PKG_REPOS" || test::fail "Invalid 'CIJ_PKG_REPOS'"

paths=""
for path in {bin,envs,hooks,testcases,modules}/*; do
  if [[ -d "$path" ]]; then
    continue
  fi

  if grep "^#.*bash" "$path" > /dev/null; then
    paths="$paths $path"
  fi
done

if [[ -z "$paths" ]]; then
  cij::warn "No SHELL source code to check"
  popd || true
  test::pass
fi

# shellcheck disable=SC2086
if ! shellcheck $paths ; then
  popd || true
  test::fail
fi

popd || true
test::pass
