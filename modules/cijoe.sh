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
CIJ_ROOT=$CIJ_ROOT
if [[ -z "$CIJ_ROOT" ]]; then
  CIJ_ROOT=$(pwd)
fi
DLIST="hooks modules templates"
for DNAME in $DLIST; do
  if [[ ! -d "$CIJ_ROOT/$DNAME" ]]; then
    echo "# FAILED: CIJ_ROOT: '$CIJ_ROOT' must have all of '$DLIST'"
    return 1
  fi
done
export CIJ_ROOT

if [[ -z "$CIJ_MODULES" ]]; then
  CIJ_MODULES="$CIJ_ROOT/modules"
fi
export CIJ_MODULES

if [[ -z "$CIJ_HOOKS" ]]; then
  CIJ_HOOKS="$CIJ_ROOT/hooks"
fi
export CIJ_HOOKS

if [[ -z "$CIJ_TEMPLATES" ]]; then
  CIJ_TEMPLATES="$CIJ_ROOT/templates"
fi
export CIJ_TEMPLATES

#
# Setup CIJOE package environment variables
#
CIJ_PKG_ROOT=$CIJ_PKG_ROOT
if [[ -z "$CIJ_PKG_ROOT" ]]; then
  CIJ_PKG_ROOT=$CIJ_ROOT
fi
DLIST="envs testcases testfiles testsuites testplans"
for DNAME in $DLIST; do
  if [[ ! -d "$CIJ_PKG_ROOT/$DNAME" ]]; then
    echo "# FAILED: CIJ_PKG_ROOT: '$CIJ_PKG_ROOT' must have all of '$DLIST'"
    return 1
  fi
done
export CIJ_PKG_ROOT

if [[ -z "$CIJ_ENVS" ]]; then
  CIJ_ENVS="$CIJ_PKG_ROOT/envs"
fi
export CIJ_ENVS

if [[ -z "$CIJ_TESTCASES" ]]; then
  CIJ_TESTCASES="$CIJ_PKG_ROOT/testcases"
fi
export CIJ_TESTCASES

if [[ -z "$CIJ_TESTFILES" ]]; then
  CIJ_TESTFILES="$CIJ_PKG_ROOT/testfiles"
fi
export CIJ_TESTFILES

if [[ -z "$CIJ_TESTSUITES" ]]; then
  CIJ_TESTSUITES="$CIJ_PKG_ROOT/testsuites"
fi
export CIJ_TESTSUITES

if [[ -z "$CIJ_TESTPLANS" ]]; then
  CIJ_TESTPLANS="$CIJ_PKG_ROOT/testplans"
fi
export CIJ_TESTPLANS

source $CIJ_MODULES/bin.sh
source $CIJ_MODULES/cij.sh
source $CIJ_MODULES/qemu.sh
source $CIJ_MODULES/test.sh
source $CIJ_MODULES/ssh.sh
source $CIJ_MODULES/lock.sh
source $CIJ_MODULES/ipmi.sh
source $CIJ_MODULES/grub.sh
source $CIJ_MODULES/nvme.sh
source $CIJ_MODULES/block.sh
source $CIJ_MODULES/fio.sh
source $CIJ_MODULES/pci.sh
source $CIJ_MODULES/board.sh
source $CIJ_MODULES/lnvm.sh
source $CIJ_MODULES/rbench.sh
source $CIJ_MODULES/fs.sh
source $CIJ_MODULES/xfstests.sh
source $CIJ_MODULES/vdbench.sh
source $CIJ_MODULES/blktests.sh
source $CIJ_MODULES/pblk.sh
source $CIJ_MODULES/tftp.sh

if [[ "$CIJ_TYPE" == "reposrun" ]]; then
  PATH=$PATH:$CIJ_ROOT/bin
  export PYTHONPATH=$PYTHONPATH:$CIJ_MODULES
fi
