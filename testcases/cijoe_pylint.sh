#!/bin/bash
#
# Run pylint on Python source code found in $CIJ_PKG_REPOS
#
# This testcase runs the Python language integrity on all the Python code it can
# find it $CIJ_PKG_REPOS. The intent is to use this on CIJOE as well as CIJOE
# packages.
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

cij::info "CIJ_PKG_REPOS: 'CIJ_PKG_REPOS'"

if [[ -z "$CIJ_PKG_REPOS" ]]; then
  test::fail "Please set 'CIJ_PKG_REPOS'"
fi
pushd "$CIJ_PKG_REPOS" || test::fail "Invalid 'CIJ_PKG_REPOS'"

paths=""
for path in {bin,hooks,testcases}/* "$CIJ_PKG_REPOS/modules/cij" "$CIJ_PKG_REPOS/setup.py"; do
  if [[ -d "$path" ]]; then
    continue
  fi

  if grep "^#.*python" "$path" > /dev/null; then
    paths="$paths $path"
  fi
done

if [[ -z "$paths" ]]; then
  cij::warn "No Python source to check"
  popd || true
  test::pass
fi

# shellcheck disable=SC2086
if ! pylint $paths ; then
  popd || true
  test::fail
fi

popd || true
test::pass
