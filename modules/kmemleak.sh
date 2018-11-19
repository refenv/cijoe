#!/usr/bin/env bash
#
# TODO:
# Document this module
# Implement it using the SSH module
#

function kmemleak::cat
{
  cat /sys/kernel/debug/kmemleak
}

function kmemleak::clear
{
  echo clear > /sys/kernel/debug/kmemleak
}

function kmemleak::scan
{
  echo scan > /sys/kernel/debug/kmemleak
}
