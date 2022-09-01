from pathlib import Path

import cijoe.core
from cijoe.core.resources import Collector

CORE_RESOURCE_COUNTS = {
    "configs": 2,
    "templates": 1,
    "auxilary": 1,
    "worklets": 6,
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
        )


def test_collect_worklets_from_path():
    """Uses the core package, to have something to collect."""

    collector = Collector()
    collector.collect_from_path(Path(__file__).parent.parent.joinpath("worklets"))

    assert (
        len(collector.resources["worklets"]) == CORE_RESOURCE_COUNTS["worklets"]
    ), "Failed collecting from path"


def test_collect_worklets_from_packages():

    collector = Collector()
    collector.collect_from_packages(cijoe.core.__path__, cijoe.core.__name__ + ".")

    assert (
        len(collector.resources["worklets"]) == CORE_RESOURCE_COUNTS["worklets"]
    ), "Failed collecting from packages"


def test_compare_from_path_with_from_package():
    """This is just to give hint to whether it is 'from_path' or 'from_packages'"""

    collector_path = Collector()
    collector_path.collect_from_path(Path(__file__).parent.parent.joinpath("worklets"))

    collector_pkgs = Collector()
    collector_pkgs.collect_from_packages(cijoe.core.__path__, cijoe.core.__name__ + ".")

    assert len(collector_path.resources["worklets"]) == len(
        collector_pkgs.resources["worklets"]
    )


def test_collect_from_empty_path():
    """This should return an empty dictionary"""

    collector = Collector()
    collector.collect_from_path("/tmp")

    assert len(collector.resources["worklets"]) == 0, "Did not expect to find any"
