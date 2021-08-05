#!/usr/bin/env bash
#
# This defines the transport to use for "cij.cmd"
#
# Here we are telling that commands will be run locally, that is, we will be running commands on
# the same machine which is invoking e.g. cij_runner. The default is to not do anything unless:
#
# * CIJ_TARGET_TRANSPORT, is set to "local"
# * SSH_HOST, is set
#
# This is to avoid running destructive tests on your *dev box*
#
export CIJ_TARGET_TRANSPORT="local"
