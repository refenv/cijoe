def test_hello():
    assert True


def test_default(cijoe):
    err, state = cijoe.run("ls -lh")

    assert err == 0


def test_default_again(cijoe):
    err, state = cijoe.run("ls")

    assert err == 0


def test_run_local_passes_env(cijoe):
    err, state = cijoe.run_local("echo FOO=[$FOO]", env={"FOO": "given"})

    assert err == 0
    assert "FOO=[given]" in state.output()
