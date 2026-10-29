# Changelog

The repository is tagged using semantic versioning, e.g. `v0.0.3`. The `master`
branch consist of the latest state of CIJOE with possible hot-fixes since
the last version tag, consider `master` as a preview of the next version.

Changes are described in this file in a section named matching the version tag.
Sections with "(Upcoming)" describe changes on the roadmap for CIJOE.

Changes on the `master` branch, from the latest version tag up to and including
HEAD can be subject to a git rebase.

## 0.9.68

`system_imaging.diskimage_from_oras` stages an image pinned by tag, such as
`oras://ghcr.io/xnvme/xnvme-devenv/guest-ubuntu-2610:v0.10.0`, once: the tag is
resolved to the digest it names, which is stamped next to the qcow2, so the image
is pulled again only when the tag moves, as a digest-pinned one is only when the
digest is bumped. A staged tag whose registry cannot be reached is used as it is.

## 0.9.67

Gathering facts is part of `cijoe.core.facts`: a script gathers the common facts
about a target with `cijoe.core.facts.gather()`, the sections being
`cijoe.core.facts.SECTIONS`, rather than importing them from the
`core.facts_gather` script.

## 0.9.66

A machine is described as a target, `[cijoe.targets.<name>.ssh]`, with
`cijoe.default_target` naming the one used when nothing else does, instead of
the first table. A task step names the target it runs on with `target:`,
beside `uses:` or `run:`, and its commands, transfers, tool checks and `{{
target.* }}` references are all about that target. `cijoe.run()`,
`cijoe.put()`, `cijoe.get()` and `cijoe.close()` take `target=`, and
`core.wait_for_target` waits on the step's target.

The old spellings still work, and each warns on stderr, naming its replacement:

* `[cijoe.transport.<name>]`, now `[cijoe.targets.<name>.ssh]`
* `transport_name=` on `run()`, `put()`, `get()`, `close()` and
  `set_output_ident()`, and `Cijoe.transports`, now `target=` and
  `Cijoe.targets`
* `core.wait_for_transport` and its `transport_name`, now `core.wait_for_target`
  with the step's `target`
* `transport` for `core.cmdrunner`, `core.put` and `core.get`, and
  `target_name` for `core.facts_gather` and `core.tools_check`, now the step's
  `target`
* `transport.SSH(config, output_path, <name>)`, now given the target's
  `[cijoe.targets.<name>.ssh]` table

## 0.9.65

The `linux` package is deprecated, and will be removed at v1.0. `linux.null_blk`,
`linux.build_kdebs` and `linux.sysinfo` warn when they run; for
`linux.sysinfo`, use `core.facts_gather`, which records the target's OS,
kernel, CPUs, memory, PCI functions and NVMe controllers as facts.

Building QEMU from source is deprecated, and will be removed at v1.0: `qemu.build`
and `qemu.install` warn when they run. Install QEMU as your distribution or
upstream provides it, and name its binaries in `qemu.systems` and
`qemu.img_bin`; `qemu.qemu_version` records which versions a run used.

The package declares its license as the SPDX expression `BSD-3-Clause`, rather
than by a license classifier, and the project is REUSE compliant.

## 0.9.64

`core.facts_gather` also records a target's GPUs and NICs, as `gpu` and `nic`:
the PCI functions of class display or accelerator, and network, each with what
the target made of it, its DRM render nodes, network interfaces and RDMA
devices on Linux, and its network interface on FreeBSD. A FreeBSD PCI function
now has the `name` its driver gave it, such as `vtnet0`. Before each section it
checks the tools that section runs on the target's OS family and records them
as facts, leaving out a section whose tools are lacking, and `skip` leaves out
sections by name.

Every run gathers the initiator's `os`, `kernel` and `system` facts before its
first step, its commands' output under `initiator/` and the facts shown in the
report as written by `(start of run)`; `[cijoe.facts] initiator` names other
sections, or none, `[]`.

A script's `TOOLS` may be declared per OS family, `{"*": {...}, "linux":
{...}}`, and a `[tools.<tool>]` may say on which families it is needed, `os =
["freebsd"]`; the target's family is taken from its facts, or asked of it once,
and a target whose family cannot be found is checked for every tool.

## 0.9.63

Facts about a machine are kept under `targets.<name>`, the name the
configuration gives it as `[cijoe.transport.<name>]`, or `initiator`, whether it
is a QEMU guest or hardware. `cijoe.default_target` names the target `run()`
reaches when given no transport, `cijoe.facts.target()` reads and writes a
target's facts, by default the default target's, and a task reads them as
`{{ target.* }}`, short for `{{ facts.targets.<default target>.* }}`.

The new `core.facts_gather` records a target's OS, kernel, CPUs and memory, PCI
functions and NVMe controllers under its name, in one layout on Linux, FreeBSD,
macOS and Windows, finding the OS by asking the target and leaving out what it
cannot gather there. The `core.facts` example uses it in place of its own
script.

Which tools a target has, and at which versions, are facts, as
`targets.<name>.tools.<tool>`, and what a run needs of them is configuration,
as `[tools.<tool>]` with the command that prints its version and the least
version needed. The new `core.tools_check` checks the tools a step names, or
all the configuration describes, records what the target has, and fails naming
every tool missing or too old. A script declares the tools it needs as
`TOOLS = {"fio": "3.38", "nvme": None}`, and cijoe checks them just before the
step that uses it, failing the step without running the script when any is
lacking; `cijoe -i` lists what each step declares. A tool the facts already
show to be good enough is not asked about again. A least version is a string
of dotted numbers, with a pre-release such as `rc1` before its release.

A reference to `facts` or `target` that is part of a longer name, such as
`{{ config.deploy.target }}`, is no longer taken for a reference to facts, and
is substituted when the task is loaded.

`cijoe -i` substitutes a task with the context a run does, `local` and
`resources` as well as `config`, so a task that refers to `{{ local.env.* }}`
passes the integrity check when it would pass a run.

## 0.9.62

Facts are what the steps of a run observe, kept apart from the configuration,
which says what is wanted and is never changed by a run. A script writes them
with `cijoe.facts.set()`, `update()` and `delete()` on dotted keys and reads
them with `cijoe.facts.get()`; the steps after it read them as
`{{ facts.<key> }}` in their `with`, substituted when the step starts rather
than when the task is loaded. Every write saves the whole set to `facts.toml` in
the output directory, and the report has a Facts tab, with the step that last
wrote each fact, and a facts button on each step that wrote any. Tests run by
`core.testrunner` start with the run's facts, and what they change is merged
back. `--facts <file>` starts a run from the facts an earlier run saved, with a
warning when that run's configuration differs. A configuration file with a
`facts` table is refused. The documentation has a page on facts, and
`cijoe --example core.facts` emits an example task.

Strings in a list are substituted whatever else the list holds. A list mixing
strings with numbers or booleans, such as `args = ["--size", 4,
"{{ config.x }}"]` in a configuration or a step's `with`, or with tables, in a
configuration, was left as it was; its references now take effect, and a
literal `{{` or `{%` in such a string is an error.

## 0.9.61

The SSH transport keeps one connection for its run()/get()/put() instead of
connecting and disconnecting around each, which cost a key exchange, about 0.4 s,
per command. The connection has a 30 second keepalive, is made again
on next use when it has dropped, e.g. as the remote rebooted, and is closed by
the new `Cijoe.close()`, at the end of a pytest session, or as Python exits.

The qemu guest's boot image is by default a qcow2 overlay backed by the staged
system image, instead of a copy of it, so a boot no longer starts with a
multi-GB copy and guests from one image share it. `qemu.guest_initialize`
takes `--overlay false` to copy as before; `diskimage_from_cloudimage` does so,
since it must write the image it produces.

The report options are now `--report-open` to also open the report in a
browser, which is no longer done by default, `--report-skip` to not write it,
and `--report-only` to write it for an existing output and exit.
`-n/--no-report` and `-p/--produce-report` remain as deprecated spellings of
`--report-skip` and `--report-only`, and `-s/--skip-report` is accepted and
ignored, each with a warning.

The example configs and tasks moved from Debian 12 and Fedora 43 to Debian 13
and Fedora 44. The `core.get_put` example task now creates its disk image with
`system_imaging.diskimage_from_cloudimage` before `qemu.guest_initialize`, as
its config no longer carries a `disk.url`.

Fixed the environment example in the configuration documentation, which was not
valid TOML.

## 0.9.59

Renamed the "workflow" concept to "task" across the codebase, docs, and example
files. The on-disk layout moves from `workflows/` directories to `tasks/`, and
the CLI/test references follow. The change is mechanical and user-visible; task
files retain the same YAML shape.

Documented that `run:` in a task is sugar for `core.cmdrunner` and that a
sibling `with:` block can pass any cmdrunner argument, most usefully
`transport:` to retarget inline commands.

Added oras:// support to system-imaging via the diskimage_from_oras script: it
resolves the artifact reference with withcache, pulls and decompresses the blob,
and writes a qcow2 to disk.path, skipping the pull when the pinned image is
already staged.

Added a `recursive` argument to the `repository_prep` script for cloning
submodules in one step.

Fixed `core/command` to replace dashes in environment variable keys so they
remain valid identifiers, and fixed a styling regression in the HTML report
template.

CI dropped Python 3.9 from the test matrix; minimum supported Python is now
3.10. The argparse-driven CLI was refactored, and the autogenerated rst pages
under `docs/source/packages/` now reflect each script's actual options.

## 0.9.2

Added a naive path-sanitizer, switched to using git to "clean", fixed a style-issue.

## 0.9.1

Fixed doc generation via read-the-docs

## 0.9.0

A complete re-implementation and a switch of license.


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
