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

Start the interactive **CIJOE** shell:

```bash
cijoe
```

Run a testplan:

```bash
cij_runner \
    --env $CIJ_ENVS/localhost.sh \
    --testplan $CIJ_TESTPLANS/EXTP_01_refenv.plan \
    --output /tmp/testrun
```

Create report of the test run:

```bash
cij_reporter --output /tmp/testrun
```

View the results:

```bash
xdg-open /tmp/testrun/report.html
```

## Test Packages

See `testcases/README.md` for info. on implementing testcases.

See `testfiles/README.md` for info. on providing input-files for testcases.

See `testsuites/README.md` for info. on running testsuites via `cij_runner`.

See `testplans/README.md` for info. on running testplans

## Reference Environments

See the [refenv](https://github.com/safl/cijoe) repository for information on
setting up reference environments.
