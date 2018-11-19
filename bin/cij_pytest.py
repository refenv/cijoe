#!/usr/bin/env python
"""
 cij_runner - Turns sh-scripts into `unittest` compatible tests

 Traditional shell-based testing would only provide a single pass/fail
 for all tests, by enveloping them in Python and unittest framework then
 the test-runner can make result output available as junit/xunit,
 and individual tests can expose pass/fail instead of a single pass/fail
 for all tests.

 It uses the following environment variables:

 CIJ_SUITE  - Test suite
 CIJ_ENV    - Test environment

In addition to having a correctly setup CIJOE installation, specifically:

 CIJ_ENVS       - Path to environments definitions
 CIJ_TESTCASES      - This is what it is all about, scripts here are wrapped.
 CIJ_MODULES    - To locate 'cijoe.sh'

Usage:

 # Run test-suite "enum", in environment "localhost", produce XML output and
 # shorten error output
 export CIJ_TEST_RES_ROOT=/tmp
 export CIJ_SUITE="enum"
 export CIJ_ENV="localhost"
 py.test $CIJ_ROOT/bin/cij_runner.py \
    --junitxml /tmp/test_results.xml \
    -r f \
    --tb=line

A bunch of other `unittest` compatible frameworks can be used, py.test, however,
seems to provide both decent XML and console output.

TODO: log output should be configurable/parameterizable
"""
from __future__ import print_function
from subprocess import Popen, STDOUT
import unittest
import os
from cij_tests import tindex

CIJ_ENV = os.environ.get("CIJ_ENV")
CIJ_SUITE = os.environ.get("CIJ_SUITE")

CIJ_ROOT = os.environ.get("CIJ_ROOT")
CIJ_ENVS = os.environ.get("CIJ_ENVS")
CIJ_TESTCASES = os.environ.get("CIJ_TESTCASES")
CIJ_MODULES = os.environ.get("CIJ_MODULES")

# We inherit the large amount of public methods from unittest.TestCase,
# nothing we can do about that so we disable pylint checking.
# pylint: disable=r0904
class MetaTest(unittest.TestCase):
    """
    This is a meta-class used as the basis for dynamically
    creating unittest.TestCase classes based on .sh files.
    """

    def meta_test(self):
        """
        meta_test: executes sh-scripts, pipes out+err to file
        """

        # Make sure we have 'cijoe.sh' to setup default environment
        cijoe_path = os.sep.join([CIJ_MODULES, "cijoe.sh"])
        if not os.path.exists(cijoe_path):
            Exception("Cannot find cijoe(%s)" % cijoe_path)

        # Make sure we have an environment defined
        env_path = os.sep.join([CIJ_ENVS, "%s.sh" % CIJ_ENV])
        if not os.path.exists(env_path):
            raise Exception("Cannot find env(%s)" % env_path)

        # Use naming conventions of Class and Method to obtain path
        _, cname, mname = self.id().split(".")
        if not cname.startswith("Test"):
            raise Exception("Invalid cname(%s)" % cname)
        if not mname.startswith("test_"):
            raise Exception("Invalid mname(%s)" % mname)

        suite_name = cname[len("Test"):]

        test_name = "_".join(mname.split("_")[1:-1])
        test_lang = mname.split("_")[-1]
        test_ext = ".sh" if test_lang == "SHELL" else ".py"

        test_path = os.sep.join([CIJ_TESTCASES, "%s%s" % (test_name, test_ext)])
        assert os.path.exists(test_path), \
            "The script for %s/%s does not exist at test_path: %s" % (
                suite_name, test_name, test_path)

        # Run the actual test-script and pipe stdout+stderr to log
        log_path = '/tmp/test-%s-%s-%s.log' % (suite_name, test_name, CIJ_ENV)

        with open(log_path, 'a') as log_fd:

            if test_lang == "PYTHON":
                cmd = [
                    'bash', '-c',
                    'source %s && '
                    'source %s && '
                    'python %s' % (cijoe_path, env_path, test_path)
                ]
            else:
                cmd = [
                    'bash', '-c',
                    'source %s && '
                    'source %s && '
                    'source %s' % (cijoe_path, env_path, test_path)
                ]
            process = Popen(cmd, stdout=log_fd, stderr=STDOUT, cwd=CIJ_MODULES)
            process.wait()

            assert process.returncode == 0, "Ran: %s/%s, rcode: %d, see: %s" % (
                suite_name, test_name, process.returncode, log_path
            )

def cls_factory(cname):
    """
    Constructs a class named `cname` inheriting from `MetaTest`.
    """

    class Foo(MetaTest):
        """cls_factory product"""
        pass
    Foo.__name__ = cname

    return Foo

def produce_classes(search_path, suite_name):
    """Construct a class with a name picked up by test-collection"""

    classes = {}

    suite_fname = "%s.suite" % suite_name
    suite_path = os.sep.join([CIJ_ROOT, "suites", suite_fname])
    suite = open(suite_path).read().splitlines() if suite_name else []

    listing = tindex(search_path)
    if listing is None:
        return {}

    tests = suite if suite else listing
    if not tests:
        return {}

    cname = "Test"
    if suite:
        cname += suite_name.capitalize()

    cls = cls_factory(cname)
    for test in tests:              # Test method for each file
        tname = "test_%s" % test.replace(".sh", "_SHELL").replace(".py", "_PYTHON")
        setattr(cls, tname, cls.meta_test)
        classes[cname] = cls

    return classes

# Expose classes into scope for `unittest`, `py.test`, `nose`, `nose2`, or
# some other unittest framework to pick up the classes, instantiate
# them and run their test methods.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

CLASSES = produce_classes(CIJ_TESTCASES, CIJ_SUITE)    # Create test classes
for CNAME in CLASSES:                               # Expose them in local scope
    CLS = CLASSES[CNAME]
    locals()[CNAME] = CLS
    del CLS                 # Avoid dual def. due to Python scope-leak
    del CNAME

if __name__ == "__main__":
    print("# Fix this")
