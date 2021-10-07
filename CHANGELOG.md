# Changelog

The repository is tagged using semantic versioning, e.g. `v0.0.3`. The `master`
branch consist of the latest state of CIJOE with possible hot-fixes since
the last version tag, consider `master` as a preview of the next version.

Changes are described in this file in a section named matching the version tag.
Sections with "(Upcoming)" describe changes on the roadmap for CIJOE.

Changes on the `master` branch, from the latest version tag up to and including
HEAD can be subject to a git rebase.

## UPCOMING

* Remove all Linux-specifics, and provide **cijoe-pkg-linux** package replacing it
  - hooks: ``dmesg_{enter,exit}.sh``, ``sysinf.sh``
  - modules: ``xfstests.sh``, ``blktests.sh``, ``ipmi.sh``, ``fs.sh``, ``kmemleak.sh``, ``pci.sh``
  - testcases: ``extc_02_fs.sh``, ``extc_03_blktests.sh``, ``extc_04_xfstests.sh``

* Remove fio-specifics and provide a **cijoe-pkg-fio** package
  - testcases: ``extc_05_fio.sh``

* Remove qemu-specifics and provide **cijoe-pkg-qemu** package replacing it
  - envs: ``localhost-qemu.sh``
  - hooks: ``qemu_{enter,exit}.sh``
  - modules: ``qemu.sh``

* Remove RocksDB specific, and consider providing a **cijoe-pkg-rocksdb** package
  - modules: ``rbench.sh``

## 0.2.1

* Replaced the ``::`` module-separator with ``.`` in hooks and modules.

* Fix to quick-start documentation

## 0.2.0

* Replaced the ``::`` module-seperator with ``.``

* Removed all examples and provided them in an example package 'cijoe-pkg-example'

* Removed deprecated Bash-module named ``board``

* Removed deprecated reference environment ``refenv-u1604``

* A complete overhaul of the documentation

* ``extractor:fio_json_read``: add 'name' and 'stddev' to metric-context

* ``bin:cij_metric_dump``: tool to collect all metrics and dump them to stdout

## 0.1.42

* Add tool ``cij_plotter`` capable of producing plots based of metrics extraced from testcases

* Add tools for testcase metric extraction and analysis

* Support for using the Python tools without entering the CIJOE shell

* Support for multiple testplans per test-run
  - Arguments to ``cij_runner`` has changed
    Use: ``--testplan`` to provide one or more testplans (this replaces positional arg)
    Use: ``--env`` to provide invironment file (this replaces positional arg)
  - Structure of ``cij_runner`` output has changed
    Before: ``<OUTPUT>/testsuite_ident/...``
    Now: ``<OUTPUT>/testplan_ident/testsuite_ident/...``
    In other words, testsuites and nested beneath testplans in the test-result output.

## 0.0.35

* Added option tot disable colors in bash-output-helpers
* Added option to initialize qemu-boot image from cloud-image
* Cleanup SSH module

## 0.0.34

* Fixed typo in sysinf hook
* Removed use of dmesg-hook in `example_01_usage.plan`
* Added `example_02_usage.plan` using the dmesg-hook

## 0.0.33

* Added Dockerfile for interactive use of CIJOE
* Fixed junit-representation

## 0.0.32

* The lock-hook will no longer create lock-files on the test-target, the
  lock-hook will as such only protect one-self against one-self, e.g. abort when
  the same environment is being used. When using shared resources your resource
  manager or CI system should provide mutual exclusion to the test-target.

* The Makefile now defaults to doing user-mode uninstall + install.

* Reporter: CSS and JavaScript are now embedded to avoid requiring
  network-access to external resources when reading the reports.

## 0.0.28

* Fixes...

## 0.0.27

* mod/qemu: added EARLY RESET and examples of device state and error-injection

## 0.0.26

* fixes...

## 0.0.25

* mod/qemu: re-done to align with the NVMe/OCSSD support in `refenv/qemu`

## 0.0.24

* hooks/sysinf: added collection of kernel config

## v0.0.23

* `bin/cij_runner`: added primitive interrupt handler
* hooks: fixed invalid error-messaging
* testcases/tlint: fixed description

## v0.0.22

* mod/fio: fixed showcmd for remote fio
* hooks/pblk: added comment on requirements
* docs: added placeholder for descr. of packages
* selftest: changed messaging on error to reduce confusion
* build: changed messaging on error to reduce confusion
* `bin/cij_tlint`: fixed missing use-of-nonexistant check

## v0.0.21

* selftest: fixed warning-message
* mod/qemu: fixed return of 'qemu::is_running' and added 'qemu::wait'
* mod/qemu: exported path to NVMe/OCSSD device via QEMU_NVME_IMAGE_FPATH

## v0.0.20

* Selftest fix

## v0.0.19

* Refined selftesting for reuse by cijoe packages

## v0.0.18

* Nothing but the version number

## v0.0.17

* Yet another bunch of fixes
* Changed license from BSD-2 to Apache

## v0.0.16

* CI fixes for automatic deployment

## v0.0.15

* Bunch of Python 3 and style fixes
* Deprecated pblk-hooks for specific params

## v0.0.14

* `cij_reporter`: fixed rendering of elapsed wall-clock
* Updated qemu module to match new 'qemu' with OCSSD support in 'qemu-img'

## v0.0.13

* A myriad of cleanup and fixes

* Deprecated Python Libraries
  - nvm.py incomplete Python interface for liblightnvm using CLI
  - spdk.py testcases implemented for liblightnvm in Python, this is handled
    better by the liblightnvm testcases themselves, hence deprecated

## v0.0.12

* Bumped version number
* Added 'clean' to release-script

## v0.0.11

* Added option to define testcases "inline" in testplan
  - It used to rely on a specific testsuite file
  - It now uses inline, when it is defined, testsuite otherwise
* Added testplan/testsuite alias
  - To be used for briefly describing how a set of testcases relates to the
    testplan
* Expanded usage examples
* Fixes to environment sourcing and lnvm module
* Fixed prefix to interactive shell

## v0.0.5

## Test-Runner

* Changed `cij_runner` arguments to positional

## Example environment definitions

* Expanded declarations of reference environment

## v0.0.4

Added this CHANGELOG, a bunch of style fixes and a couple of logic fixes, and
some functionality changes.

# Shell Modules

* Renamed `get_fib_range` to `cij::get_fib_range`
* `get_exp_2_range` to `cij::get_exp_2_range`
* vdbench: prefixed vars with `VDBENCH_`

# Tools

Changed `cij_reporter` it now takes the output path as positional argument
instead of optional named argument. E.g.:

```bash
# How it was
cij_reporter --output /path/to/output

# How it is now
cij_reporter /path/to/output
```
