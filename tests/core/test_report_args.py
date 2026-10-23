"""The --report-* options, and the deprecated spellings they replace"""

import errno
import logging
import sys

import pytest

from cijoe.cli.cli import parse_args


def parse(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["cijoe", "task.yaml", *argv])
    return parse_args()


def test_defaults(monkeypatch):
    err, args = parse(monkeypatch)
    assert not err
    assert not args.open_report
    assert not args.report_skip
    assert not args.report_only


def test_report_only_with_open(monkeypatch):
    err, args = parse(monkeypatch, "--report-only", "--report-open")
    assert not err
    assert args.report_only and args.open_report


def test_skip_and_only_conflict(monkeypatch):
    err, _ = parse(monkeypatch, "--report-skip", "--report-only")
    assert err == errno.EINVAL


@pytest.mark.parametrize(
    "old, attr",
    [
        ("-n", "report_skip"),
        ("--no-report", "report_skip"),
        ("-p", "report_only"),
        ("--produce-report", "report_only"),
    ],
)
def test_deprecated_maps_onto_new(monkeypatch, caplog, old, attr):
    with caplog.at_level(logging.WARNING):
        err, args = parse(monkeypatch, old)
    assert not err
    assert getattr(args, attr)
    assert "deprecated" in caplog.text
    assert not any(name.endswith("_deprecated") for name in vars(args))


@pytest.mark.parametrize("old", ["-s", "--skip-report"])
def test_deprecated_skip_report_is_accepted_and_ignored(monkeypatch, caplog, old):
    with caplog.at_level(logging.WARNING):
        err, args = parse(monkeypatch, old)
    assert not err
    assert not args.open_report
    assert "deprecated" in caplog.text
