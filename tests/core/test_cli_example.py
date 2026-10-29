import os
from pathlib import Path

from cijoe.cli.cli import SEARCH_PATHS, search_for_file


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


def test_emit_example_core(cijoe, tmp_path):
    err, _ = cijoe.run("cijoe --example core.default", cwd=tmp_path)
    assert not err


def test_cli_example_listing_with_a_task_in_the_cwd(cijoe, tmp_path):
    (tmp_path / "mine.yaml").write_text("doc: x\nsteps: []\n")

    err, state = cijoe.run("cijoe --example", cwd=tmp_path)
    assert not err
    assert "core.default" in state.output()


def test_emit_example_twice(cijoe, tmp_path):
    for _ in range(2):
        err, _ = cijoe.run("cijoe --example core.default", cwd=tmp_path)
        assert not err


def test_emit_example_that_does_not_exist(cijoe, tmp_path):
    err, _ = cijoe.run("cijoe --example core.nosuch", cwd=tmp_path)
    assert err

    err, _ = cijoe.run("cijoe --example nosuch", cwd=tmp_path)
    assert err


def test_cli_version(cijoe):
    err, _ = cijoe.run("cijoe --version")
    pass
    assert not err


def test_cli_resources(cijoe):
    err, _ = cijoe.run("cijoe --resources")
    assert not err


def test_cli_integration_check(cijoe, tmp_path):
    # Get a temporary path and change directory so it is possible
    # to rerun test and it wont pollute the test environment

    err, _ = cijoe.run("cijoe --example core.default", cwd=tmp_path)
    assert not err

    err, _ = cijoe.run(
        "cijoe --integrity-check ",
        cwd=tmp_path / "cijoe-example-core.default",
    )
    assert not err


def test_cli_environment_variables(cijoe):
    # This test needs to be run in a session since we set a environment
    # variable and it should not pollute.
    os.environ["HELLO_WORLD"] = "true"
    message = cijoe.getconf("hello.world", None)
    assert message

    os.environ["HELLO_WORLD"] = "1"
    message = cijoe.getconf("hello.world", None)

    os.environ["HELLO_WORLD"] = "0x1"
    message = cijoe.getconf("hello.world", None)
    assert message == 1

    os.environ["HELLO_WORLD"] = "Hello World!"
    message = cijoe.getconf("hello.world", None)
    assert message == "Hello World!"

    # This should fail since 0xg is not a valid hex value
    os.environ["HELLO_WORLD"] = "0xg"
    message = cijoe.getconf("hello.world", None)


def test_getconf_reads_a_dashed_key_from_underscores(cijoe, monkeypatch):
    monkeypatch.setenv("SYSTEM_IMAGING_IMAGES_FEDORA_43", "from-env")

    assert cijoe.getconf("system-imaging.images.fedora-43") == "from-env"


def test_cli_search_for_file_exists():
    filename = "tmpfile.txt"
    file = (SEARCH_PATHS[0] / filename).resolve()
    file.write_text("Hello World!")

    path = search_for_file(Path(filename))
    assert path

    file.unlink()


def test_cli_search_for_file_not_exists():
    filename = "tmpfile.txt"

    path = search_for_file(Path(filename))
    assert not path


def test_cli_search_for_file_absolute_exists():
    filename = "tmpfile.txt"
    file = (SEARCH_PATHS[0] / filename).resolve()
    file.write_text("Hello World!")

    path = search_for_file(file)
    assert path

    file.unlink()


def test_cli_search_for_file_absolute_not_exists():
    filename = "tmpfile.txt"
    file = SEARCH_PATHS[0] / filename

    path = search_for_file(file)
    assert not path
