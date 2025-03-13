import subprocess
from pathlib import Path


def run_loglevel_script(tmp_path, loglevel) -> subprocess.CompletedProcess[str]:
    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    script_file = Path(__file__).absolute().parent / "aux_loglevel.py"

    command = [
        "cijoe",
        str(script_file),
        "--config",
        str(config_path),
        "--no-report",
    ]

    if loglevel:
        command += [f"-{loglevel*'l'}"]

    return subprocess.run(
        command,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )


def test_no_loglevel_parameter(tmp_path):
    result = run_loglevel_script(tmp_path, 0)

    assert result.returncode == 0
    assert "critical" in result.stderr
    assert "error" in result.stderr
    assert "warning" not in result.stderr
    assert "info" not in result.stderr
    assert "debug" not in result.stderr


def test_one_loglevel_parameter(tmp_path):
    result = run_loglevel_script(tmp_path, 1)

    assert result.returncode == 0
    assert "warning" in result.stderr
    assert "info" in result.stderr
    assert "debug" not in result.stderr


def test_two_loglevel_parameter(tmp_path):
    result = run_loglevel_script(tmp_path, 2)

    assert result.returncode == 0
    assert "debug" in result.stderr


def test_more_loglevel_parameter(tmp_path):
    result = run_loglevel_script(tmp_path, 5)

    assert result.returncode == 0
    assert "debug" in result.stderr
