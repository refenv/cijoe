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
