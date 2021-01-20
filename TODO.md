# TODO

* `cij_runner`
  - Add support for running multiple testplans in a single testrun
  - Add a file-lock replacing the lock-hook [DONE]
  - Encapsulate the testrun, testplan, testsuites, testcase and hooks using dataclasses
  - Add a runtime threshold, terminate the testcase/hook when threshold is exceeded
* Performance Evaluation possibly named `cij analyse ...`
  - Add a new tool processing testrun-output
  - Should be possible to provide adhoc transformations, plotting, criteria-checking
* Command-line interface
  - Provide a single binary, named `cij` with subcommands and bash-completion e.g.
    - cij run ...
    - cij report ...
    - cij analyse
  - Rename  `cijoe` bin to `cijoe_shell` or check if can be started by e.g. `cijoe shell`
* Python library
  - Replace shebangs with Python3 [DONE]
  - Remove Python testcase support and all that stuff Python mod for ssh etc. [DONE]
* BASH-modules
  - Change the "namespace" delimiter-convention from "::" to "."
  - Add ``cij::cmd`` replacing the use of ssh::cmd and support not using SSH but running locally
  - Remove some of those slightly over-engineered bash-modules
  - Remove the test-auto-magic-env-checking e.g. auto-testing whether devices exists etc. [DONE]
* CI
  - Switch CI from Travis to GitHUB Actions
    - Run CIJOE selftest [done]
    - Deployment tags to PyPI
    - Deploy CIJOE docker image
