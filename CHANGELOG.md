# Changelog

The repository is tagged using semantic versioning, e.g. `v0.0.3`. The `master`
branch consist of the latest state of CIJOE with possible hot-fixes since
the last version tag, consider `master` as a preview of the next version.

Changes are described in this file in a section named matching the version tag.
Sections with "(Upcoming)" describe changes on the roadmap for CIJOE.

Changes on the `master` branch, from the latest version tag up to and including
HEAD can be subject to a git rebase.

## v0.0.6 (Upcoming)

* Expand usage example
* Style and logic fixes

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
