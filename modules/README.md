# Modules

This folder contains BASH SHELL packages/modules that wrap around various
commands and utilities. These scripts are all included when including CIJOE,
this means that the functions defined in the scripts are always available when
using CIJOE.

The modules use namespace prefix separated by `::`. The namespace is the same as
the filename. E.g. the CIJOE module is `cij.sh` and functions prefixed with
`cij::` e.g. `cij::emph`, the testing module is in `tst.sh` and functions
prefixed with `test::` e.g. `test::fail`.
