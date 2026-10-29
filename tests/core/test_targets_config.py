"""
Targets as the config describes them, '[cijoe.targets.<name>.ssh]', and as the
deprecated '[cijoe.transport.<name>]' still does
"""

from cijoe.core.command import Cijoe
from cijoe.core.resources import Config


def load(tmp_path, text):
    path = tmp_path / "config.toml"
    path.write_text(text)
    config = Config(path)
    return config, config.load()


def test_targets(tmp_path, capsys):
    config, errors = load(
        tmp_path,
        '[cijoe.targets.guest.ssh]\nhostname = "localhost"\n'
        '[cijoe.targets.other.ssh]\nhostname = "other"\n',
    )
    assert errors == []
    assert "deprecated" not in capsys.readouterr().err

    cijoe = Cijoe(config, tmp_path / "output", False)
    assert list(cijoe.targets) == ["guest", "other", "initiator"]
    assert cijoe.targets["other"].ssh_params == {"hostname": "other"}
    assert cijoe.default_target == "guest"


def test_transport_is_a_deprecated_target(tmp_path, capsys):
    config, errors = load(tmp_path, '[cijoe.transport.guest]\nhostname = "localhost"\n')
    assert errors == []
    assert capsys.readouterr().err == (
        "WARNING: [cijoe.transport.guest] is deprecated;"
        " use [cijoe.targets.guest.ssh]\n"
    )
    assert config.options["cijoe"]["targets"] == {
        "guest": {"ssh": {"hostname": "localhost"}}
    }
    assert config.options["cijoe"]["transport"] == {"guest": {"hostname": "localhost"}}


def test_a_target_in_both_tables(tmp_path):
    _, errors = load(
        tmp_path,
        '[cijoe.targets.guest.ssh]\nhostname = "a"\n'
        '[cijoe.transport.guest]\nhostname = "b"\n',
    )
    assert errors == ["The target guest is in both cijoe.targets and cijoe.transport."]


def test_initiator_is_reserved(tmp_path):
    _, errors = load(tmp_path, '[cijoe.targets.initiator.ssh]\nhostname = "a"\n')
    assert errors == ["The key cijoe.targets.initiator is reserved."]


def test_a_target_says_how_it_is_reached(tmp_path):
    _, errors = load(tmp_path, '[cijoe.targets.guest]\nhostname = "a"\n')
    assert errors == ["The target guest has no [cijoe.targets.guest.ssh]."]


def test_default_target(tmp_path):
    config, errors = load(
        tmp_path,
        'cijoe.default_target = "other"\n'
        '[cijoe.targets.guest.ssh]\nhostname = "a"\n'
        '[cijoe.targets.other.ssh]\nhostname = "b"\n',
    )
    assert errors == []
    assert Cijoe(config, tmp_path / "a", False).default_target == "other"

    config, errors = load(tmp_path, 'cijoe.default_target = "initiator"\n')
    assert errors == []
    assert Cijoe(config, tmp_path / "b", False).default_target == "initiator"


def test_default_target_must_be_a_target(tmp_path):
    _, errors = load(
        tmp_path,
        'cijoe.default_target = "nope"\n[cijoe.targets.guest.ssh]\nhostname = "a"\n',
    )
    assert errors == [
        "The cijoe.default_target (nope) is not a target; known: guest, initiator"
    ]


def test_ssh_by_name_is_deprecated(tmp_path, capsys):
    """transport.SSH() given a target's name, as it once took a transport's"""

    from cijoe.core import transport

    config, errors = load(tmp_path, '[cijoe.targets.guest.ssh]\nhostname = "a"\n')
    assert errors == []
    ssh = transport.SSH(config, tmp_path, "guest")
    assert ssh.ssh_params == {"hostname": "a"}
    assert "transport.SSH(config, output_path, <name>) is deprecated" in (
        capsys.readouterr().err
    )


def test_targets_is_a_table(tmp_path):
    _, errors = load(tmp_path, 'cijoe.targets = "guest"\n')
    assert errors == ["The key cijoe.targets must be a table, of one table per target."]
