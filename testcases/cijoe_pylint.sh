#!/bin/bash
#
# Run shellcheck on CIJOE executable
#
# shellcheck disable=SC2119
#
CIJ_TEST_NAME=$(basename "${BASH_SOURCE[0]}")
export CIJ_TEST_NAME
# shellcheck source=modules/cijoe.sh
source "$CIJ_ROOT/modules/cijoe.sh"
test::enter

: "${CIJ_REPOS:=./}"

pushd "$CIJ_REPOS" || test::fail

paths="$CIJ_REPOS/modules/cij"
paths="$paths $CIJ_REPOS/setup.py"
for path in {bin,hooks,testcases}/*; do
  if [[ -d "$path" ]]; then
    continue
  fi

  if grep "^#.*python" "$path" > /dev/null; then
    paths="$paths $path"
  fi
done

# shellcheck disable=SC2086
if ! pylint $paths ; then
  popd || true
  test::fail
fi

popd || true
test::pass
