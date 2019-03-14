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

# shellcheck source=modules/bin.sh
source "$CIJ_MODULES/bin.sh"
# shellcheck source=modules/cij.sh
source "$CIJ_MODULES/cij.sh"
# shellcheck source=modules/qemu.sh
source "$CIJ_MODULES/qemu.sh"
# shellcheck source=modules/test.sh
source "$CIJ_MODULES/test.sh"
# shellcheck source=modules/ssh.sh
source "$CIJ_MODULES/ssh.sh"
# shellcheck source=modules/lock.sh
source "$CIJ_MODULES/lock.sh"
# shellcheck source=modules/ipmi.sh
source "$CIJ_MODULES/ipmi.sh"
# shellcheck source=modules/nvme.sh
source "$CIJ_MODULES/nvme.sh"
# shellcheck source=modules/block.sh
source "$CIJ_MODULES/block.sh"
# shellcheck source=modules/fio.sh
source "$CIJ_MODULES/fio.sh"
# shellcheck source=modules/pci.sh
source "$CIJ_MODULES/pci.sh"
# shellcheck source=modules/board.sh
source "$CIJ_MODULES/board.sh"
# shellcheck source=modules/lnvm.sh
source "$CIJ_MODULES/lnvm.sh"
# shellcheck source=modules/rbench.sh
source "$CIJ_MODULES/rbench.sh"
# shellcheck source=modules/fs.sh
source "$CIJ_MODULES/fs.sh"
# shellcheck source=modules/xfstests.sh
source "$CIJ_MODULES/xfstests.sh"
# shellcheck source=modules/vdbench.sh
source "$CIJ_MODULES/vdbench.sh"
# shellcheck source=modules/blktests.sh
source "$CIJ_MODULES/blktests.sh"
# shellcheck source=modules/pblk.sh
source "$CIJ_MODULES/pblk.sh"
# shellcheck source=modules/tftp.sh
source "$CIJ_MODULES/tftp.sh"

if [[ "$CIJ_TYPE" == "reposrun" ]]; then
  PATH=$PATH:$CIJ_ROOT/bin
  export PYTHONPATH=$PYTHONPATH:$CIJ_MODULES
fi
