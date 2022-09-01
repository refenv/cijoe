from cijoe.core.resources import get_resources


def test_workflow_load():

    resources = get_resources()

    config = resources["configs"]["core.default"]
    assert config

    errors = config.load()
    assert not errors

    workflow = resources["workflows"]["core.example"]
    assert workflow

    errors = workflow.load(config, [])
    assert not errors
