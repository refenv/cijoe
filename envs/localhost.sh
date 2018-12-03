#!/usr/bin/env bash
#
# This is minimal configuration for CTRL <-> TRGT setup
#
# SSH key-based auth will be used to access "localhost" as the user "root"
#
export CIJ_TRGT=localhost
export SSH_HOST=$CIJ_TRGT
export SSH_USER=root
