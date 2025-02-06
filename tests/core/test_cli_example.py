import subprocess


def test_cli_example_emit_listing(cijoe):
    err, _ = cijoe.run("cijoe --example")
    assert not err


def test_cli_example_emit_specific(cijoe, tmp_path):
    err, state = cijoe.run("cijoe --example")
    assert not err

    examples = [line.strip() for line in state.output().splitlines()]
    for example in examples:
        err, state = cijoe.run(f"cijoe --example {example}", cwd=tmp_path)
        assert not err


def test_cli_example_emit_all_in_package(cijoe, tmp_path):
    err, state = cijoe.run("cijoe --example")
    assert not err

    examples = [line.strip() for line in state.output().splitlines()]
    for pkg_name in list(set([line.split(".")[0] for line in examples])):
        err, state = cijoe.run(f"cijoe --example {pkg_name}", cwd=tmp_path)
        assert not err


def test_cli_resource_script(tmp_path):
    config_path = (tmp_path / "test-config-empty.toml").resolve()
    config_path.write_text("")

    result = subprocess.run(
        [
            "cijoe",
            "core.example_script_default",
            "--config",
            str(config_path),
        ],
        cwd=str(tmp_path),
    )

    assert result.returncode == 0
