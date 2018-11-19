"""
    Utilities for writing Python tests with CIJOE
"""
import sys
import os
import yaml
import cij.board
import cij.block
import cij.nvme
import cij.lnvm
import cij.util
import cij.nvm
import cij.ssh
import cij


PASS = 0
FAIL = 1
SKIP = 2
REQS = []


def tindex(spath=None):
    """
    Lists tindex in CIJ_TESTCASES

    @Returns On success, a list of filenames is returned. On error, None is
    returned
    """

    spath = spath if spath else os.environ.get("CIJ_TESTCASES", None)
    if spath is None:
        return None

    tests = []                          # Look for .sh files
    for root, _, files in os.walk(spath):
        if root != spath:
            continue

        tests += [f for f in files if f[-3:] in [".sh", ".py"]]

    return tests


def envs():
    """
    Return variables defined by modules required by test
    """

    variables = {}

    for req in REQS:
        prefix = req.upper()
        variables[prefix] = cij.env_to_dict(
            prefix, getattr(cij, req).REQUIRED + getattr(cij, req).EXPORTED
        )

    return variables


def require(req):
    """Add test requirement"""

    REQS.append(req)


def enter():
    """Enter the test, check requirements and setup aux. environment"""

    if cij.ssh.env():
        tfail("cij.test: invalid SSH environment")

    for req in REQS:
        if getattr(cij, req).env():
            tfail()

    cij.emph("cij.test: entering test")


def texit(msg=None, rcode=1):
    """Exit the test"""

    msg = ", msg: %r" % msg if msg else ""

    if rcode:
        cij.err("cij.test: FAILED%s" % msg)
    else:
        cij.good("cij.test: PASSED%s" % msg)

    sys.exit(rcode)


def tpass(msg=None):
    """Testing: Exit test indicating test passed"""

    texit(msg, 0)


def tfail(msg=None):
    """Testing: Exit test indicating test failed"""

    texit(msg, 1)


def command(cmd, ssh=True, shell=True, echo=True):
    """
    Execute the given 'cmd'

    @returns (rcode, stdout, stderr)
    """

    if ssh:
        return cij.ssh.command(cmd, shell, echo)
    else:
        return cij.util.execute(cmd, shell, echo)


def command_to_struct(cmd):
    """
    Same as `command` except it tries to convert stdout to struct

    @returns (rcode, struct, stderr, struct)
    """

    struct = None

    rcode, stdout, stderr = command(cmd)

    try:
        lines = stdout.splitlines()

        for line_number, line in enumerate(lines):
            if line.strip().startswith("#"):
                break
        struct = yaml.load("\n".join(lines[line_number:]))
    except Exception as exc:
        cij.err("could not parse stdout as yaml, exc: %r" % exc)

    return rcode, stdout, stderr, struct
