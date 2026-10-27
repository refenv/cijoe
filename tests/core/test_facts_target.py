from cijoe.core.command import Cijoe
from cijoe.core.facts import Facts
from cijoe.core.resources import (
    FACTS_REFERENCE,
    Config,
    dict_substitute,
    facts_templates,
    substitute_templates,
)


def test_target_facts_are_under_targets(tmp_path):
    facts = Facts(tmp_path / "facts.toml")
    facts.default_target = "qemu_guest"

    facts.target().set("os", {"id": "debian"})
    facts.target("machineB").set("os.id", "freebsd")
    assert facts.target().get("os.id") == "debian"
    assert facts.target().get() == {"os": {"id": "debian"}}
    assert facts.get("targets.machineB.os.id") == "freebsd"
    assert facts.changed == {"targets.qemu_guest.os", "targets.machineB.os.id"}

    facts.target().delete("os")
    assert facts.target().get(default="none") == {}


def test_the_default_target_is_the_first_transport(tmp_path):
    (tmp_path / "none.toml").write_text("")
    cijoe = Cijoe(Config.from_path(tmp_path / "none.toml"), tmp_path / "a", False)
    assert cijoe.default_target == "initiator"
    assert cijoe.facts.default_target == "initiator"

    (tmp_path / "two.toml").write_text(
        '[cijoe.transport.guest]\nhostname = "localhost"\n'
        '[cijoe.transport.other]\nhostname = "localhost"\n'
    )
    cijoe = Cijoe(Config.from_path(tmp_path / "two.toml"), tmp_path / "b", False)
    assert cijoe.default_target == "guest"
    assert cijoe.facts.target().prefix == "targets.guest"


def test_target_is_left_to_the_step_and_config_target_is_not():
    assert FACTS_REFERENCE.search("{{ target.os.id }}")
    assert FACTS_REFERENCE.search("{%if target.gpu %}")
    assert not FACTS_REFERENCE.search("{{ config.deploy.target }}")
    assert not FACTS_REFERENCE.search("{{ config.x.facts }}")

    step = {"commands": ["echo {{ target.os.id }} {{ config.x }}"]}
    templates = facts_templates(step)
    assert dict_substitute(step, {"config": {"x": "a"}}, defer_facts=True) == []
    context = {"config": {"x": "a"}, "facts": {}, "target": {"os": {"id": "debian"}}}
    assert substitute_templates(step, templates, context) == []
    assert step["commands"] == ["echo debian a"]
