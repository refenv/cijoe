# Testcases

This folder contains testcases, written as scripts, implemented as BASH/SHELL or
Python scripts.

The absolute path to this directory is defined as environment variable:

```bash
CIJ_TESTCASES=$CIJ_PKG_ROOT/testcases
```

## Bash SHELL scripts

The testing scripts must comply with the shell style guide found here:

* https://google.github.io/styleguide/shell.xml

In addition to the style guide, the test scripts must comply with the test
contract. The contract is described in the following.

1. All expressions are remote, that is, they must execute commands over SSH,
   ensure that the SSH-utility is satisfied.

2. Whenever possible, testcases must use framework modules, e.g. utilize
   "test::pass" to exit a test upon success and use "test::fail" to exit a test
   indicating failure. When implementing a test, inspect the available modules
   to see what functionality can be re-used/expanded.

3. stdout and stderr, should never be redirected. Additionally, when a test
   produces output it should produce it *annotated* via the `cij::emph`,
   `cij::info`, `cij::err`, `cij::warn` module functions. This allows for
   post-processing to distinguish between output from the testcase itself in
   contrast to the output produce by the commands executed by the testcase.

When a testcase produces output in the form of files, these must be placed in
the `$CIJ_TEST_AUX_ROOT`.

Always check the return values of executed commands, even the simplest
expressions can lead to unexpected behavior when not succeeding. Additionally,
when checking return values, provide a meaningful informational message via
`cij::err`. Checking and providing meaningful annotated error-messages makes
reading log-files from testcases a lot easier and accelerates troubleshooting.

## Python scripts

Tests implemented in Python must comply with the Python PEP8 style guide found
here:

 * https://www.python.org/dev/peps/pep-0008/

In addition, they should use the `CIJOE` Python package `cij` and its containing
modules under the same guidelines are the Bash SHELL scripts.
