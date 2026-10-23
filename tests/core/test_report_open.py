"""The report is written after a run, but only opened when asked for"""

import sys
import webbrowser

import pytest

from cijoe.cli import cli

TASK = """\
---
doc: A single step, that runs anywhere
steps:
- name: noop
  run: "true"
"""


@pytest.mark.parametrize(
    "extra, written, opened",
    [
        ([], True, 0),
        (["--report-open"], True, 1),
        (["--report-skip"], False, 0),
        (["-s"], True, 0),
    ],
)
def test_report_open(tmp_path, monkeypatch, extra, written, opened):
    calls = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: calls.append(url))
    monkeypatch.chdir(tmp_path)

    config = tmp_path / "cijoe-config.toml"
    config.write_text("[cijoe.task]\nfail_fast = true\n")
    task = tmp_path / "cijoe-task.yaml"
    task.write_text(TASK)

    argv = ["cijoe", "-c", str(config), str(task), "-o", str(tmp_path / "out")]
    monkeypatch.setattr(sys, "argv", argv + extra)
    assert cli.main() == 0

    assert (tmp_path / "out" / "report.html").exists() == written
    assert len(calls) == opened


@pytest.mark.parametrize("step_with", ["", "  with:\n    report_open: false\n"])
def test_reporter_as_a_task_step(tmp_path, monkeypatch, step_with):
    """core.reporter keeps working as a task step, with and without its argument"""

    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: None)
    monkeypatch.chdir(tmp_path)

    config = tmp_path / "cijoe-config.toml"
    config.write_text("[cijoe.task]\nfail_fast = true\n")
    task = tmp_path / "cijoe-task.yaml"
    task.write_text(TASK + "- name: report\n  uses: core.reporter\n" + step_with)

    argv = ["cijoe", "-c", str(config), str(task), "-o", str(tmp_path / "out")]
    monkeypatch.setattr(sys, "argv", argv)
    assert cli.main() == 0
    assert (tmp_path / "out" / "report.html").exists()
