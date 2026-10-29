from pathlib import Path

import cijoe.core
from cijoe.core.resources import Collector

CORE_RESOURCE_COUNTS = {
    "configs": 5,
    "templates": 2,
    "auxiliary": 2,
    "scripts": 12,
}


def test_resource_collection():
    """Check that the expected amount of resources are collected"""

    collector = Collector()
    collector.collect()

    for category, count in CORE_RESOURCE_COUNTS.items():
        assert (
            len(
                [
                    r
                    for r in collector.resources[category].keys()
                    if r.startswith("core")
                ]
            )
            == count
        ), f"Invalid count({count}) for category({category})"


def test_collect_scripts_from_path():
    """Uses the core package, to have something to collect."""

    collector = Collector()
    collector.collect_from_path(
        Path(__file__)
        .parent.parent.parent.joinpath("src", "cijoe", "core", "scripts")
        .resolve()
    )

    assert (
        len(collector.resources["scripts"]) == CORE_RESOURCE_COUNTS["scripts"]
    ), "Failed collecting from path"


def test_collect_scripts_from_packages():
    collector = Collector()
    collector.collect_from_packages(cijoe.core.__path__, cijoe.core.__name__ + ".")

    assert (
        len(collector.resources["scripts"]) == CORE_RESOURCE_COUNTS["scripts"]
    ), "Failed collecting from packages"


def test_compare_from_path_with_from_package():
    """This is just to give hint to whether it is 'from_path' or 'from_packages'"""

    collector_path = Collector()
    collector_path.collect_from_path(Path(__file__).parent.parent.joinpath("scripts"))

    collector_pkgs = Collector()
    collector_pkgs.collect_from_packages(cijoe.core.__path__, cijoe.core.__name__ + ".")

    assert len(collector_path.resources["scripts"]) == len(
        collector_pkgs.resources["scripts"]
    )


def test_collect_from_empty_path():
    """This should return an empty dictionary"""

    collector = Collector()
    collector.collect_from_path("/tmp")

    assert len(collector.resources["scripts"]) == 0, "Did not expect to find any"


def test_collect_from_packages_skips_other_suffixes(tmp_path, monkeypatch):
    """A file in a category directory is only collected with that category's suffix"""

    for sub in ["cijoe_fake", "cijoe_fake/demo", "cijoe_fake/demo/tasks"]:
        (tmp_path / sub).mkdir()
        (tmp_path / sub / "__init__.py").write_text("")
    (tmp_path / "cijoe_fake/demo/tasks/README.md").write_text("not a task")
    (tmp_path / "cijoe_fake/demo/tasks/.keep").write_text("")
    (tmp_path / "cijoe_fake/demo/tasks/real.yaml").write_text("doc: x\nsteps: []\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delattr(Collector, "instance", raising=False)

    import cijoe_fake

    collector = Collector()
    collector.collect_from_packages(cijoe_fake.__path__, "cijoe_fake.")

    assert list(collector.resources["tasks"]) == ["demo.real"]
