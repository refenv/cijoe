from cijoe.core.misc import deprecated


def test_deprecated_warns_once_on_stderr(capsys):
    deprecated("old_thing", "new_thing")
    deprecated("old_thing", "new_thing")
    deprecated("gone_thing")

    assert capsys.readouterr().err == (
        "WARNING: old_thing is deprecated; use new_thing\n"
        "WARNING: gone_thing is deprecated; it will be removed in v1.0\n"
    )
