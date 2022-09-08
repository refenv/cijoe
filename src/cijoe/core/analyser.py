#!/usr/bin/env python3
"""
    Library functions for performance requirements and normalization of metrics
"""
import copy
import dataclasses
import os
import re
from typing import List, Tuple

import yaml

from cijoe.core.errors import InvalidRangeError, UnknownUnitError

UNITS = {
    # general
    "": 1,  # no unit
    "B": 1,  # bytes
    "k": 1000,  # kilo
    "M": 1000**2,  # mega
    "G": 1000**3,  # giga
    # kibi
    "KiB": 1024**1,  # kibibytes
    "MiB": 1024**2,  # mibibytes
    "GiB": 1024**3,  # gibibytes
    "TiB": 1024**4,  # tibibytes
    # kilo
    "kB": 1000**1,  # kilobytes
    "MB": 1000**2,  # megabytes
    "GB": 1000**3,  # gigabytes
    "TB": 1000**4,  # gigabytes
    # time
    "nsec": 1 / 1000**3,  # nanoseconds
    "usec": 1 / 1000**2,  # microseconds
    "msec": 1 / 1000**1,  # milliseconds
    "sec": 1,  # seconds
    "min": 60,  # minutes
}


class Range:
    """
    Range implements parsing and validation of mathematical range notation,
    e.g. `[-5;100[` which translates to "must be >= -5 and < 100".
    """

    # pylint: disable=no-self-use
    # pylint: disable=too-few-public-methods

    _rng_re = re.compile(
        r"^(?P<elower>\[|\])\s*(?P<rstart>-inf|-?\d+(\.\d*)?)\s*;"  # [1.0;
        r"\s*(?P<rend>inf|-?\d+(\.\d*)?)\s*(?P<eupper>\[|\])"  # 1.0]
        rf"\s*(?P<unit>({'|'.join(UNITS)}))$"  # ms
    )

    def __init__(self, rng: str):
        match = self._rng_re.match(rng)
        if not match:
            raise InvalidRangeError(f'invalid syntax or unit for "{rng}"')

        rng_start = float(match["rstart"])
        rng_end = float(match["rend"])
        if rng_start > rng_end:
            raise InvalidRangeError(
                "expected lower bound <= upper bound, " f"{rng_start} <= {rng_end}"
            )

        # NOTE: _rng_re enforces that match["unit"] exists in UNITS.
        unit_val = UNITS[match["unit"]]

        self._rng_start = rng_start
        self._rng_end = rng_end
        self._elower = match["elower"]
        self._eupper = match["eupper"]
        self._unit = match["unit"]

        self._check_lower = self._make_check_lower(
            match["elower"], rng_start * unit_val
        )
        self._check_upper = self._make_check_upper(match["eupper"], rng_end * unit_val)

    def contains(self, val: float) -> bool:
        """Check whether n is contained in range.

        val must be given in the base unit of the measurement, e.g. seconds for
        time and bytes for storage.
        """
        return self._check_lower(val) and self._check_upper(val)

    def _make_check_lower(self, edge_lower: str, rng_start: float):
        if edge_lower == "[":
            return lambda n: n >= rng_start
        if edge_lower == "]":
            return lambda n: n > rng_start
        raise InvalidRangeError("invalid input _make_check_lower")

    def _make_check_upper(self, edge_upper: str, rng_end: float):
        if edge_upper == "[":
            return lambda n: n < rng_end
        if edge_upper == "]":
            return lambda n: n <= rng_end
        raise InvalidRangeError("invalid input _make_check_upper")

    def format_val(self, val: float) -> str:
        """Formats and returns val using the unit of the range.

        Example:
            range: "[250; 750]usec"
            val: 0.0005
            output: "500 usec"
        """

        val_conv = val / UNITS[self._unit]
        return f"{val_conv:.3f} {self._unit}"

    def __str__(self):
        return (
            f"{self._elower}{self._rng_start};"
            f"{self._rng_end}{self._eupper} {self._unit}"
        )


def to_base_unit(val: float, unit: str = "") -> float:
    """Converts val in the given unit to its base unit.
    Example:
        val: 100, unit: 'KiB'
        output: 102400 (bytes)

        val: 500, unit: 'msec'
        output: 0.5 (seconds)
    """
    unit_scalar = UNITS.get(unit, None)
    if not unit_scalar:
        raise UnknownUnitError(f"Unit '{unit}' is not supported")

    return val * unit_scalar
