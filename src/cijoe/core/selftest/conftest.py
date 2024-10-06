import pytest

from cijoe.core.resources import Collector


@pytest.fixture
def nvme(cijoe, capsys):
    nvme = cijoe.get_config(subject="nvme")
    if not nvme:
        return None

    for device in nvme.get("devices", []):
        return device


@pytest.fixture
def xnvme(cijoe, capsys):
    nvme = cijoe.get_config(subject="nvme")
    if not nvme:
        return None

    for device in nvme.get("devices", []):
        return device


@pytest.fixture(autouse=True)
def reset_collector():
    # This fixture runs automatically before each test
    collector = Collector()
    collector.reset()
