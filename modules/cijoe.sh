#!/usr/bin/env bash
#
# cijoe.sh - Entry point for CIJOE, setting up environment variables and
# sourcing in BASH modules
#
# Sets up defaults for environment variables:
#
# CIJ_ROOT              - Path to CIJOE
# CIJ_MODULES           - Path to CIJOE BASH and Python modules
# CIJ_HOOKS             - Path to CIJOE BASH and Python module hooks
# CIJ_TEMPLATES         - Path to various file template/skeleton files
#
# CIJ_PKG_ROOT          - Path to a CIJOE package root
# CIJ_ENVS              - Path to environment declarations
# CIJ_TESTFILES         - Path to files used by testcases e.g. fio jobfiles
# CIJ_TESTCASES         - Path to CIJOE test cases implemented in BASH or Python
# CIJ_TESTSUITES        - Path to CIJOE test suites
# CIJ_TESTPLANS         - Path to CIJOE test plans
#
# Sources in bash packages/modules from CIJ_MODULES/*
#

#
# Setup CIJOE core environment variables
#

: "${CIJ_ROOT:=$(pwd)}"
DLIST="hooks modules templates"
for DNAME in $DLIST; do
  if [[ ! -d "$CIJ_ROOT/$DNAME" ]]; then
    echo "# FAILED: CIJ_ROOT: '$CIJ_ROOT' must have all of '$DLIST'"
    return 1
  fi
done
export CIJ_ROOT

: "${CIJ_MODULES:="$CIJ_ROOT/modules"}"
export CIJ_MODULES

: "${CIJ_HOOKS:="$CIJ_ROOT/hooks"}"
export CIJ_HOOKS

: "${CIJ_TEMPLATES:="$CIJ_ROOT/templates"}"
export CIJ_TEMPLATES

#
# Setup CIJOE package environment variables
#
: "${CIJ_PKG_ROOT:=$CIJ_ROOT}"
DLIST="envs testcases testfiles testsuites testplans"
for DNAME in $DLIST; do
  if [[ ! -d "$CIJ_PKG_ROOT/$DNAME" ]]; then
    echo "# FAILED: CIJ_PKG_ROOT: '$CIJ_PKG_ROOT' must have all of '$DLIST'"
    return 1
  fi
done
export CIJ_PKG_ROOT

: "${CIJ_ENVS:="$CIJ_PKG_ROOT/envs"}"
export CIJ_ENVS

: "${CIJ_TESTCASES:="$CIJ_PKG_ROOT/testcases"}"
export CIJ_TESTCASES

: "${CIJ_TESTFILES:="$CIJ_PKG_ROOT/testfiles"}"
export CIJ_TESTFILES

: "${CIJ_TESTSUITES:="$CIJ_PKG_ROOT/testsuites"}"
export CIJ_TESTSUITES

: "${CIJ_TESTPLANS:="$CIJ_PKG_ROOT/testplans"}"
export CIJ_TESTPLANS

# Source in all the CIJOE Modules; except "cijoe.sh" itself
for MOD_PATH in "$CIJ_MODULES"/*; do
  if [[ "$MOD_PATH" == *"cijoe.sh" ]]; then
    continue;
  fi

  # shellcheck disable=SC1090
  source "${MOD_PATH}"
done

if [[ -v CIJ_TYPE ]] && [[ "$CIJ_TYPE" == "reposrun" ]]; then
  PATH=$PATH:$CIJ_ROOT/bin
  export PYTHONPATH=$PYTHONPATH:$CIJ_MODULES
fi
