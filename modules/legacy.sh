#!/usr/bin/env bash
#
# legacy.sh - Legacy support for the old "::" module separator
#
# It is added here in its own file to rid the modules themselves, one can then add/remove this
# module to check whether a package supports it.
#
cij::info() {
  cij.info "$@"
}
cij::good() {
  cij.good "$@"
}
cij::warn() {
  cij.warn "$@"
}
cij::err() {
  cij.err "$@"
}
cij::emph() {
  cij.emph "$@"
}
cij::throttle() {
  cij.throttle "$@"
}
cij::watchf() {
  cij.watchf "$@"
}
cij::watchf_for() {
  cij.watchf_for "$@"
}
cij::repeat() {
  cij.repeat "$@"
}
cij::isint() {
  cij.isint "$@"
}
cij::push() {
  cij.push "$@"
}
cij::pull() {
  cij.pull "$@"
}
cij::cmd() {
  cij.cmd "$@"
}

test::usage() {
  test.usage "$@"
}
test::enter() {
  test.enter "$@"
}
test::exit() {
  test.exit "$@"
}
test::skip() {
  test.skip "$@"
}
test::fail() {
  test.fail "$@"
}
test::pass() {
  test.pass "$@"
}
test::info() {
  test.info "$@"
}

ssh::cmd() {
  ssh.cmd "$@"
}
ssh::cmd_output() {
  ssh.cmd_output "$@"
}
ssh::cmd_t() {
  ssh.cmd_t "$@"
}
ssh::shell() {
  ssh.shell "$@"
}
ssh::push() {
  ssh.push "$@"
}
ssh::pull() {
  ssh.pull "$@"
}
ssh::check() {
  ssh.check "$@"
}

