#!/usr/bin/env python3

"""
This file provides basic functionality to make it easier to implement custom
extractors. It is not itself an extractor.
"""

from __future__ import annotations
import os
import json
import glob
import dataclasses
from typing import List
import re

from cij.runner import TestCase
import cij


def make_context(db_bench_obj: dict, extr_name: str, fname: str,
                 evars: dict) -> dict:
    """ Make a context dict for db_bench output files. """

    return {
        "rocks_ver": db_bench_obj["rocks_ver"],
        "date": db_bench_obj["date"],
        "memtable_rep": db_bench_obj["memtable_rep"],
        "compression": db_bench_obj["compression"],
        "entries": db_bench_obj["entries"],
        "keys_bytes": db_bench_obj["keys_bytes"],
        "values_bytes": db_bench_obj["values_bytes"],
        "fname": fname,
        "extractor_name": extr_name,
        "evars": evars,
    }


def get_db_bench_files(tcase: TestCase) -> List[str]:
    """ Return a list of db_bench files from the TestCase aux directory """
    return list(glob.glob(os.path.join(tcase.aux_root, "db_bench*")))


def parse_db_bench_file(fpath: str) -> dict:
    """ Read and parse json from db_bench outputs """

    # Each matcher matches a line in a db_bench output and extracts relevant
    # values from it
    matchers = [
        # example: `RocksDB: version 1.2`
        re.compile(
            r"^RocksDB:\s+version\s+(?P<rocks_ver>\d(\.\d*)?)$"
        ),

        # example: `Entries: 1337`
        re.compile(
            r"^Entries:\s+(?P<entries>\d+)$"
        ),

        # example: `Date: Wed Mar 3 15:40:16 2021`
        re.compile(
            r"^Date:\s+(?P<date>.*?\d{4})$"
        ),

        # example: `Compression: Snappy`
        re.compile(
            r"^Compression:\s+(?P<compression>\w+)$"
        ),

        # example: `Values: 123 bytes each (0 bytes after compression)`
        re.compile(
            r"^Values:\s+(?P<values_bytes>\d+) bytes each\s+"
            r"\(\d+ bytes after compression\)$"
        ),

        # example: `Keys: 5 bytes each (+ 0 bytes user-defined timestamp)`
        re.compile(
            r"^Keys:\s+(?P<keys_bytes>\d+) bytes each\s+"
            r"\(\+ \d+ bytes user-defined timestamp\)$"
        ),

        # example: `Memtablerep: skip_list`
        re.compile(
            r"^Memtablerep:\s+(?P<memtable_rep>\w+)$"
        ),

        # example: `CPU: 12 * AMD Ryzen 5 5600X 6-Core Processor`
        re.compile(
            r"^CPU:\s+(?P<cpu>.*)$"
        ),

        # example: `CPUCache: 512 KB`
        re.compile(
            r"^CPUCache:\s+(?P<cpu_cache>.* KB)$"
        ),

        # example: `DB path: [/tmp/rocksdbtest-1000/dbbench]`
        re.compile(
            r"^DB path: \[(?P<db_path>.*?)\]$"
        ),

        # example: `fillseq: 123.2 micros/op 321 ops/sec 12.3 MB/s`
        re.compile(
            r"^fillseq\s+:\s+"
            r"(?P<lat>\d+(\.\d*)?) micros/op\s+"
            r"(?P<iops>\d+) ops/sec;\s+"
            r"(?P<mbps>\d+(\.\d*)?) MB/s\s*$"
        ),

        # example: `multireadrandom: 1.2 micros/op 2 ops/sec; (1 of 1 found)`
        re.compile(
            r"^multireadrandom\s+:\s+"
            r"(?P<lat>\d+(\.\d*)?) micros/op\s+"
            r"(?P<iops>\d+) ops/sec;\s+"
            r"\(\d+ of \d+\s+found\)$"
        ),

        # example: `entries_per_batch = 2`
        re.compile(
            r"^entries_per_batch = (?P<batch_size>\d+)$"
        )
    ]

    conversions = {
        'lat': float,
        'iops': float,
        'mbps': float,
        'values_bytes': float,
        'keys_bytes': float,
        'entries': float,
        'batch_size': float,
    }

    output = {}
    with open(fpath, 'r') as db_benchf:
        for l in db_benchf:
            for matcher in matchers:
                match = matcher.match(l)
                if not match:
                    continue

                for key, value in match.groupdict().items():
                    converter = conversions.get(key, lambda v: v)
                    output[key] = converter(value)

    return output


__EXAMPLE_DB_BENCH_OUTPUT = """
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
RocksDB:    version 6.18
Date:       Wed Mar  3 15:40:16 2021
CPU:        16 * AMD Ryzen 7 PRO 4750U with Radeon Graphics
CPUCache:   512 KB
Keys:       16 bytes each (+ 0 bytes user-defined timestamp)
Values:     100 bytes each (50 bytes after compression)
Entries:    1000000
Prefix:    0 bytes
Keys per prefix:    0
RawSize:    110.6 MB (estimated)
FileSize:   62.9 MB (estimated)
Write rate: 0 bytes/second
Read rate: 0 ops/second
Compression: Snappy
Compression sampling rate: 0
Memtablerep: skip_list
Perf Level: 1
------------------------------------------------
Initializing RocksDB Options from the specified file
Initializing RocksDB Options from command-line flags
DB path: [/tmp/rocksdbtest-1000/dbbench]
fillseq      :       1.789 micros/op 559021 ops/sec;   61.8 MB/s
Please disable_auto_compactions in FillDeterministic benchmark
"""