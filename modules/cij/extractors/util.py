import os
import argparse
from typing import Sequence, List

import yaml

from cij.runner import TestRun
import cij


def parse_args_load_trun(name: str) -> TestRun:
    """
    Parse arguments, load TRUN from test output directory and return it.

    This function is a helper for extractors to easily and consistently
    implement direct CLI functionality without being invoked through the
    cij_extractor command.
    """

    prsr = argparse.ArgumentParser(
        description=name,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    prsr.add_argument(
        "--output",
        help="Path to test result output directory",
        required=True
    )

    args = prsr.parse_args()
    trun_fpath = cij.runner.yml_fpath(args.output)

    return cij.runner.trun_from_file(trun_fpath)


def dump_metrics_to_file(metrics: List[dict], aux_root: str):
    """
    Dump a list of measured metrics to metrics.yml at aux_root.
    """

    fpath = os.path.join(aux_root, "metrics.yml")
    with open(fpath, 'w') as yml_file:
        data = yaml.dump(
            metrics, explicit_start=True, default_flow_style=False
        )
        yml_file.write(data)
