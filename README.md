# cijoe - Tools for systems development and testing

**Status** [![Build Status](https://travis-ci.org/safl/cijoe.svg?branch=master)](https://travis-ci.org/safl/cijoe)

**CIJOE** provides a collection of SHELL commands, modules and a Python package.

# Installation and Usage

Install **CIJOE** via pip / The Python Package index / PyPi:

```bash
pip install cijoe
```

Or via repository:

```bash
CIJ_REPOS_URL=https://github.com/safl/cijoe.git

git clone $CIJ_REPOS_URL
cd cijoe
make install
```

## Usage

Run CIJOE interactively and define the target environment:

```bash
# Start cijoe
cijoe

# Use refence definitions as a template for defining your environment
cat $CIJ_ENVS/refenv-u1604.sh > target_env.sh

# Open up your favorite editor and modify accordingly
vim target_env.sh
```

Start the test-runner and view the report:

```bash
# Create directory to store results
RESULTS=$(mktemp -d trun.XXXXXX -p /tmp)

# Run the testplan example
cij_runner \
    $CIJ_TESTPLANS/example_01_usage.plan \
    target_env.sh \
    --output $RESULTS

# Create test report
cij_reporter $RESULTS

# Inspect the test-report
xdg-open $RESULTS/report.html
```

## Test Packages

See `testcases/README.md` for info. on implementing testcases.

See `testfiles/README.md` for info. on providing input-files for testcases.

See `testsuites/README.md` for info. on running testsuites via `cij_runner`.

See `testplans/README.md` for info. on running testplans

## Reference Environments

See the [refenv](https://github.com/safl/cijoe) repository for information on
setting up reference environments.
