from cijoe.core.resources import dict_substitute


def test_strings_are_substituted_in_any_list():
    topic = {
        "strings": ["{{ config.x }}", "b"],
        "mixed": ["--size", 4, "{{ config.x }}", True, {"v": "{{ config.x }}"}],
        "tables": [{"v": "{{ config.x }}"}],
    }

    assert dict_substitute(topic, {"config": {"x": "a"}}) == []
    assert topic == {
        "strings": ["a", "b"],
        "mixed": ["--size", 4, "a", True, {"v": "a"}],
        "tables": [{"v": "a"}],
    }
