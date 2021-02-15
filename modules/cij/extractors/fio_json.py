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

from cij.runner import TestCase
import cij


def make_context(fio_obj: dict, extr_name: str, fname: str, job_id: int,
                 evars: dict) -> dict:
    """ Make a context dict for fio json output files. """
    opt = fio_obj["global options"]
    opt.update(fio_obj["jobs"][job_id]["job options"])  # override job-specific opts

    return {
        "timestamp": fio_obj["timestamp"],
        "ioengine": opt["ioengine"],
        "bs": opt["bs"],
        "rw": opt["rw"],
        "size": opt["size"],
        "iodepth": opt["iodepth"],
        "fname": fname,
        "job_id": job_id,
        "extractor_name": extr_name,
        "evars": evars,
    }


def get_fio_output_files(tcase: TestCase) -> List[str]:
    """ Return a list of fio-output files from the TestCase aux directory """
    return list(glob.glob(os.path.join(tcase.aux_root, "fio-output*")))


def parse_fio_output_file(fpath: str) -> dict:
    """ Read and parse json from fio json outputs """
    lines = []

    with open(fpath, 'r') as fiof:
        do_append = False
        for l in fiof:
            if l.startswith('{'):
                do_append = True

            if do_append:
                lines.append(l)

            if l.startswith('}'):
                break

    try:
        return json.loads(''.join(lines))
    except json.decoder.JSONDecodeError:
        return {}
