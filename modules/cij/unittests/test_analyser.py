import unittest
from unittest.mock import patch
from collections import namedtuple

from cij.runner import TestRun, TestPlan, TestSuite, TestCase, Status
from cij.analyser import (Range, InvalidRangeError, UnknownUnitError,
                          to_base_unit, analyse_prequirements)

RangeTest = namedtuple("RangeTest", ["rng", "n", "expected"])


class TestRange(unittest.TestCase):
    def test_range_valid_ranges_no_unit(self):
        """
        Validates that valid ranges without units are accepted, and that they
        are computed correctly.
        """

        tests = [
            # half open range with negative infinity
            RangeTest(rng="]-inf;5]", n=-9999999999999999, expected=True),
            RangeTest(rng="]-inf;5]", n=0, expected=True),
            RangeTest(rng="]-inf;5]", n=5, expected=True),
            RangeTest(rng="]-inf;5]", n=10, expected=False),
            RangeTest(rng="]-inf;5]", n=5.0001, expected=False),

            # half open range with positive infinity
            RangeTest(rng="[-10;inf[", n=9999999999999999, expected=True),
            RangeTest(rng="[-10;inf[", n=0, expected=True),
            RangeTest(rng="[-10;inf[", n=-10, expected=True),
            RangeTest(rng="[-10;inf[", n=-100, expected=False),
            RangeTest(rng="[-10;inf[", n=-99999999999999, expected=False),

            # closed range with absolute values
            RangeTest(rng="[-10;10]", n=-10, expected=True),
            RangeTest(rng="[-10;10]", n=0, expected=True),
            RangeTest(rng="[-10;10]", n=10, expected=True),
            RangeTest(rng="[-10;10]", n=-10.1, expected=False),
            RangeTest(rng="[-10;10]", n=10.1, expected=False),

            # open range with absolute values
            RangeTest(rng="]-10;10[", n=-9.99999999999999, expected=True),
            RangeTest(rng="]-10;10[", n=9.999999999999999, expected=True),
            RangeTest(rng="]-10;10[", n=5, expected=True),
            RangeTest(rng="]-10;10[", n=-10, expected=False),
            RangeTest(rng="]-10;10[", n=10, expected=False),

            # closed range, exact equality
            RangeTest(rng="[10;10]", n=10, expected=True),
            RangeTest(rng="[10;10]", n=10.00000000000001, expected=False),
            RangeTest(rng="[10;10]", n=9.999999999999999, expected=False),

            # open range, no matches possible
            RangeTest(rng="]10;10[", n=10, expected=False),

            # ranges with decimals
            RangeTest(rng="[10.0;10.1]", n=10.05, expected=True),
            RangeTest(rng="[10.;11.]", n=10, expected=True),
            RangeTest(rng="[10.0;10.1[", n=10.05, expected=True),
            RangeTest(rng="]10.0;10.1[", n=10.05, expected=True),
            RangeTest(rng="]10.0;10.1[", n=10.1, expected=False),
            RangeTest(rng="]10.0;10.1[", n=10.0, expected=False),

            # ranges with whitespace
            RangeTest(rng="[1; 10]", n=5, expected=True),
            RangeTest(rng="[1 ;10]", n=5, expected=True),
            RangeTest(rng="[1 ; 10]", n=5, expected=True),
            RangeTest(rng="[ 1 ; 10 ]", n=5, expected=True),
            RangeTest(rng="[   1     ;     10   ]", n=5, expected=True),
        ]

        for test in tests:
            rng = Range(test.rng)
            self.assertEqual(
                test.expected,
                rng.contains(test.n),
                f"Expected {test.expected} for {test.n} in '{test.rng}'"
            )

    def test_range_invalid_ranges(self):
        """
        Validates that invalid range declarations raise exceptions.
        """

        tests = [
            # non-increasing range requirements
            RangeTest(rng="]10;5]", n=0, expected=InvalidRangeError),
            RangeTest(rng="]inf;5]", n=0, expected=InvalidRangeError),
            RangeTest(rng="]1;-inf]", n=0, expected=InvalidRangeError),
            RangeTest(rng="]-5;-10]", n=0, expected=InvalidRangeError),

            # invalid range syntax
            RangeTest(rng="[1,10]", n=5, expected=InvalidRangeError),
            RangeTest(rng="[1:10]", n=5, expected=InvalidRangeError),
            RangeTest(rng="[a;10]", n=5, expected=InvalidRangeError),
            RangeTest(rng="[1;b]", n=5, expected=InvalidRangeError),
            RangeTest(rng="(1;10]", n=5, expected=InvalidRangeError),
            RangeTest(rng="[1;10)", n=5, expected=InvalidRangeError),
            RangeTest(rng="[;10]", n=5, expected=InvalidRangeError),
            RangeTest(rng="[1;]", n=5, expected=InvalidRangeError),
            RangeTest(rng="abc", n=5, expected=InvalidRangeError),

            # invalid units
            RangeTest(rng="[1;5]x", n=0, expected=InvalidRangeError),
            RangeTest(rng="[1;5]invalid", n=0, expected=InvalidRangeError),
            RangeTest(rng="[1;5]5", n=0, expected=InvalidRangeError),
            RangeTest(rng="[1ms;5ms]", n=0, expected=InvalidRangeError),
            RangeTest(rng="[1ms;5ms]ms", n=0, expected=InvalidRangeError),
        ]

        for test in tests:
            msg = f"Expected {test.rng} to be invalid"
            with self.assertRaises(test.expected, msg=msg):
                Range(test.rng)

    def test_range_valid_ranges_with_unit(self):
        """
        Validates that valid ranges units are accepted, and that they are
        computed correctly.
        """

        tests = [
            # general
            RangeTest(rng="[1;1]", n=1, expected=True),
            RangeTest(rng="[1;1]B", n=1, expected=True),
            RangeTest(rng="[1;1]k", n=1000, expected=True),
            RangeTest(rng="[1;1]M", n=1000**2, expected=True),
            RangeTest(rng="[1;1]G", n=1000**3, expected=True),

            # kilo
            RangeTest(rng="[1;1]kB", n=1000**1, expected=True),
            RangeTest(rng="[1;1]MB", n=1000**2, expected=True),
            RangeTest(rng="[1;1]GB", n=1000**3, expected=True),
            RangeTest(rng="[1;1]TB", n=1000**4, expected=True),

            # kibi
            RangeTest(rng="[1;1]KiB", n=1024**1, expected=True),
            RangeTest(rng="[1;1]MiB", n=1024**2, expected=True),
            RangeTest(rng="[1;1]GiB", n=1024**3, expected=True),
            RangeTest(rng="[1;1]TiB", n=1024**4, expected=True),

            # time
            RangeTest(rng="[1;1]nsec", n=1/1000**3, expected=True),
            RangeTest(rng="[1;1]usec", n=1/1000**2, expected=True),
            RangeTest(rng="[1;1]msec", n=1/1000**1, expected=True),
            RangeTest(rng="[1;1]sec", n=1, expected=True),
            RangeTest(rng="[1;1]min", n=60, expected=True),

            # ranges with whitespace
            RangeTest(rng="[1; 1]KiB", n=1024**1, expected=True),
            RangeTest(rng="[1;1] KiB", n=1024**1, expected=True),
            RangeTest(rng="[1; 1] KiB", n=1024**1, expected=True),
            RangeTest(rng="[1 ; 1]KiB", n=1024**1, expected=True),
            RangeTest(rng="[ 1 ; 1 ] KiB", n=1024**1, expected=True),
            RangeTest(rng="[  1  ;  1  ]  KiB", n=1024**1, expected=True),
        ]

        for test in tests:
            rng = Range(test.rng)
            self.assertEqual(
                test.expected,
                rng.contains(test.n),
                f"Expected {test.expected} for {test.n} in '{test.rng}'"
            )


ToBaseUnitTest = namedtuple("ToBaseUnitTest", ["val", "unit", "expected"])


class TestToBaseUnit(unittest.TestCase):
    def test_to_base_unit_valid(self):
        """ Validates that valid units are accepted and computed correctly.
        """

        tests = [
            # general
            ToBaseUnitTest(val=1, unit="", expected=1),
            ToBaseUnitTest(val=1, unit="B", expected=1),
            ToBaseUnitTest(val=1, unit="k", expected=1000),
            ToBaseUnitTest(val=1, unit="M", expected=1000**2),
            ToBaseUnitTest(val=1, unit="G", expected=1000**3),

            # kibi
            ToBaseUnitTest(val=1, unit="B", expected=1),
            ToBaseUnitTest(val=1, unit="KiB", expected=1024),
            ToBaseUnitTest(val=1, unit="MiB", expected=1024**2),
            ToBaseUnitTest(val=1, unit="GiB", expected=1024**3),
            ToBaseUnitTest(val=1, unit="TiB", expected=1024**4),

            # kilo
            ToBaseUnitTest(val=1, unit="B", expected=1),
            ToBaseUnitTest(val=1, unit="kB", expected=1000),
            ToBaseUnitTest(val=1, unit="MB", expected=1000**2),
            ToBaseUnitTest(val=1, unit="GB", expected=1000**3),
            ToBaseUnitTest(val=1, unit="TB", expected=1000**4),

            # time
            ToBaseUnitTest(val=1, unit="nsec", expected=1/1000**3),
            ToBaseUnitTest(val=1, unit="usec", expected=1/1000**2),
            ToBaseUnitTest(val=1, unit="msec", expected=1/1000**1),
            ToBaseUnitTest(val=1, unit="sec", expected=1),
            ToBaseUnitTest(val=1, unit="min", expected=60),
        ]

        for test in tests:
            got = to_base_unit(test.val, test.unit)
            self.assertEqual(
                test.expected,
                got,
                f"Expected {test.expected} for {test.val}, got '{got}'"
            )

    def test_to_base_unit_invalid(self):
        """ Validates that invalid units are not accepted and raise exceptions.
        """

        tests = [
            ToBaseUnitTest(val=1, unit="wrong unit", expected=UnknownUnitError),
            ToBaseUnitTest(val=1, unit=" k", expected=UnknownUnitError),
            ToBaseUnitTest(val=1, unit=" ", expected=UnknownUnitError),
            ToBaseUnitTest(val=1, unit="iops", expected=UnknownUnitError),
        ]

        for test in tests:
            msg = f"Expected {test.unit} to be invalid"
            with self.assertRaises(test.expected, msg=msg):
                to_base_unit(test.val, test.unit)


AnalysePrequirementsTest = namedtuple("AnalysePrequirementsTest",
                                      ["metrics",
                                      "status_trun", "status_tplan",
                                      "status_tsuite", "status_tcase"])


class TestAnalysePrequirements(unittest.TestCase):

    @patch("builtins.open")
    def test_analyse_prequirements_global_preq_single_testcase(self, _):
        """
        Verifies that analyse_prequirements uses global metrics for testcases
        and sets the expected status_preq at all levels in the TestRun struct.
        """
        preqs = {"global": {"metrics": {"bwps": "[100; 500]"}}}

        tests = {
            "within range": AnalysePrequirementsTest(
                metrics=[{"bwps": 250}],
                status_trun=Status.Pass,
                status_tplan=Status.Pass,
                status_tsuite=Status.Pass,
                status_tcase=Status.Pass,
            ),
            "outside range": AnalysePrequirementsTest(
                metrics=[{"bwps": 501}],
                status_trun=Status.Fail,
                status_tplan=Status.Fail,
                status_tsuite=Status.Fail,
                status_tcase=Status.Fail,
            ),
            "no metrics": AnalysePrequirementsTest(
                metrics=[],
                status_trun=Status.Pass,
                status_tplan=Status.Pass,
                status_tsuite=Status.Pass,
                status_tcase=Status.Unkn,
            ),
        }

        for tname, test in tests.items():
            tcase = TestCase(name="tcase")
            tsuite = TestSuite(name="tsuite", testcases=[tcase])
            tplan = TestPlan(name="tplan", testsuites=[tsuite])
            trun = TestRun(name="trun", testplans=[tplan])

            with patch('cij.analyser._get_metrics', lambda _: test.metrics):
                msg = f"test '{tname}' failed"
                err = analyse_prequirements(trun, preqs)
                self.assertFalse(err, msg)

                self.assertEqual(test.status_trun, trun.status_preq, msg)
                self.assertEqual(test.status_tplan, tplan.status_preq, msg)
                self.assertEqual(test.status_tsuite, tsuite.status_preq, msg)
                self.assertEqual(test.status_tcase, tcase.status_preq, msg)
