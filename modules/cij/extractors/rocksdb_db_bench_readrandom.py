#!/usr/bin/env python3
"""
Extract read metrics (iops, bwps, lat) from fio json data (fio-output* files)
"""

import os
from typing import Collection, List, Dict

from cij.runner import TestCase, trun_from_file
from cij.analyser import to_base_unit
from cij.extractors import rocksdb
from cij.extractors.util import dump_metrics_to_file, parse_args_load_trun

_MY_NAME = os.path.splitext(os.path.basename(__file__))[0]

def extract_metrics(tcase: TestCase) -> List[dict]:
    """
    Locate testcase db_bench files and parse them.
    Writes metrics to aux_root/metrics.yml and returns them.
    """

    metrics = []

    for fpath in rocksdb.get_db_bench_files(tcase):
        pmetric = rocksdb.parse_db_bench_file(fpath)
        if not pmetric:
            continue

        ctx = rocksdb.make_context(
            pmetric,
            extr_name=_MY_NAME,
            fname=os.path.basename(fpath),
            evars=tcase.evars,
        )

        metrics.append({
            "ctx": ctx,
            "iops": to_base_unit(pmetric["iops"], ""),
            # "bwps": to_base_unit(pmetric["mbps"], "MiB"),
            "lat": to_base_unit(pmetric["lat"], "msec"),
            "batch_size": to_base_unit(pmetric["batch_size"], ""),
        })

    if metrics:  # Only dump non-empty metrics
        dump_metrics_to_file(metrics, tcase.aux_root)

    return metrics


if __name__ == "__main__":
    """ Extract metrics if invoked directly """
    trun = parse_args_load_trun(_MY_NAME)
    for tplan in trun.testplans:
        for tsuite in tplan.testsuites:
            for tcase in tsuite.testcases:
                extract_metrics(tcase)
