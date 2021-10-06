#!/usr/bin/env python3
"""
    Library functions for cij_extractor
"""
import os
import importlib.util
from typing import List, Optional, cast
import dataclasses

import cij.runner
from cij.runner import TestRun, TestCase
from cij.errors import CIJError, InitializationError
from cij.util import rehome

# pylint:disable=unsubscriptable-object


class Extractor:
    """ Type declaration for extractors. Used to help mypy. """

    # pylint: disable=too-few-public-methods

    def extract_metrics(self, tcase: TestCase) -> List[dict]:
        """
        Extracts metrics from relevant tcase logs in tcase.aux_root and dumps
        to tcase.analysis_log_fpath in yaml format.

        Returns the list of metrics.
        """
        raise NotImplementedError


def extract_metrics(trun: TestRun, extractors: List[Extractor]) -> int:
    """ Run the given extractors on all TestCases in the given trun. """
    if len(extractors) > 1:
        cij.warn(
            "NOTICE: "
            "multiple extractors requested. If any of your testcases contain "
            "measurements supported by multiple extractors, only extractions "
            "by the last extractor will be persisted to metrics.yml"
        )

    for tplan in trun.testplans:
        for tsuite in tplan.testsuites:
            for tcase in tsuite.testcases:
                for extractor in extractors:
                    extractor.extract_metrics(tcase)

    return 0


def _get_extractor(name: str) -> Optional[Extractor]:
    """
    Import an extractor by name or filepath
    """
    try:
        spec = importlib.util.find_spec("cij.extractors.%s" % name)
    except ModuleNotFoundError:
        spec = None

    name = cij.util.expand_path(name)
    if spec is None:
        spec = importlib.util.spec_from_file_location("", name)
    if spec is None:
        spec = importlib.util.spec_from_file_location("", "%s.py" % name)
    if not spec or not spec.loader:
        cij.err("Cannot find: %r" % name)
        return None

    assert isinstance(spec.loader, importlib.abc.Loader)  # help mypy

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except FileNotFoundError as ex:
        cij.err(f"Cannot find: {name}")
        raise InitializationError(f"extractor '{name}' not recognized") from ex

    if not getattr(module, 'extract_metrics', None):
        raise InitializationError(f"extractor '{name} doesn't have the "
                                  "required 'extract_metrics' method")

    return cast(Extractor, module)


@dataclasses.dataclass
class ExtractorMeta:
    """ Container for extractor name and docstring """
    name: str
    docs: str


def find_extractors() -> List[ExtractorMeta]:
    """ Search cij.extractors.* for available extractors and return
    a list of their names and docstrings.
    """

    try:
        spec = importlib.util.find_spec("cij.extractors")
    except ModuleNotFoundError:
        return []

    assert spec and spec.loader
    assert isinstance(spec.loader, importlib.abc.Loader)  # help mypy
    assert isinstance(spec.loader, importlib.abc.ResourceReader)  # help mypy

    extractor_fpaths = [
        spec.loader.resource_path(k)
        for k in spec.loader.contents() if not k.startswith('__')
    ]

    emeta = []
    for fpath in extractor_fpaths:
        name = os.path.splitext(os.path.basename(fpath))[0]
        try:
            extractor = _get_extractor(name)
        except InitializationError:
            continue

        emeta.append(ExtractorMeta(
            name=name,
            docs=getattr(extractor, "__doc__", "").strip(),
        ))

    return emeta


def main(args):
    """
    Run cij extractor.

    """

    trun = cij.runner.trun_from_file(args.trun_fpath)

    # pylint: disable=no-member
    rehome(trun.args.output, args.output, trun)

    err = 0
    try:
        extractors = [_get_extractor(ename) for ename in args.extractor]
        err += extract_metrics(trun, extractors)
        cij.info("Metrics extracted")
    except CIJError as ex:
        cij.err(f"main:FAILED to run data extraction: {ex}")
        err += 1

    return err
