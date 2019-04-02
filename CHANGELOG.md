# Changelog

The repository is tagged using semantic versioning, e.g. `v0.0.3`. The `master`
branch consist of the latest state of CIJOE with possible hot-fixes since
the last version tag, consider `master` as a preview of the next version.

Changes are described in this file in a section named matching the version tag.
Sections with "(Upcoming)" describe changes on the roadmap for CIJOE.

Changes on the `master` branch, from the latest version tag up to and including
HEAD can be subject to a git rebase.


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
